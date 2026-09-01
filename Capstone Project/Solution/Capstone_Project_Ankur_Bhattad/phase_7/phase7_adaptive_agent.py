"""
SupportSense AI — Phase 7: Adaptive Behaviour
=================================================
Extends Phase 6's memory-carrying, tool-calling, retrieval-grounded agent
with a feedback mechanism: explicit thumbs-up/down + a fixed reason code
(modeled the way a real product UI would send it — not free text the model
has to interpret) drives small, explicit, explainable behaviour-adjustment
rules for THIS session.

Safety boundary (see phase7_notes.md for the full rationale): feedback may
change HOW the agent communicates (verbosity) and WHEN it proactively
escalates, but never WHAT it states as policy. A "you got the policy wrong"
signal (reason="incorrect_info") only adds a transparent "flagged for human
review" note to future related answers — the retrieved policy content itself
is never altered based on a customer's claim, per the Problem Framing
Document's "never fabricate policies" / "base responses only on retrieved
knowledge" safety requirements.

Feedback storage:
  - Behavioural state (`Conversation.preferences`) is session-scoped only,
    same privacy rationale as Phase 6's memory (no cross-session customer
    data).
  - `logs/feedback_log.jsonl` is a separate, explicitly non-PII, cross-run
    log (rating + reason + conversation/turn id only — no message content)
    for product-analytics purposes; it does not feed back into any live
    session's behaviour.

Run:
    python phase7_adaptive_agent.py

Requires `utils.py` (sets OPENAI_API_BASE / OPENAI_API_KEY) in the same
directory, and network access to the Vocareum endpoint.

Outputs:
    logs/phase7_interaction_log.jsonl   — full per-turn transcripts + preferences state
    logs/adaptive_behavior_table.csv    — Conversation -> Turn/event -> Response -> Notes
    logs/feedback_log.jsonl             — non-PII feedback records
"""

import csv
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import utils  # noqa: F401  (sets OPENAI_API_BASE / OPENAI_API_KEY as a side effect)
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, trim_messages

MODEL = os.environ.get("SUPPORTSENSE_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.environ.get("SUPPORTSENSE_EMBED_MODEL", "text-embedding-3-small")
TOP_K = 3
MAX_TOOL_ITERATIONS = 4
MAX_SHORT_TERM_MESSAGES = 12

PHASE_DIR = Path(__file__).parent
KNOWLEDGE_BASE_DIR = PHASE_DIR / "knowledge_base"
LOG_DIR = PHASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
INTERACTION_LOG = LOG_DIR / "phase7_interaction_log.jsonl"
ADAPTIVE_TABLE = LOG_DIR / "adaptive_behavior_table.csv"
ESCALATIONS_LOG = LOG_DIR / "escalations.jsonl"
FEEDBACK_LOG = LOG_DIR / "feedback_log.jsonl"

client = OpenAI(
    base_url=os.environ["OPENAI_API_BASE"],
    api_key=os.environ["OPENAI_API_KEY"],
)

# ---------------------------------------------------------------------------
# Tools — unchanged from phase_5/phase_6
# ---------------------------------------------------------------------------


def _add_business_days(start_date, n_days):
    d = start_date
    added = 0
    while added < n_days:
        d += timedelta(days=1)
        if d.weekday() != 6:  # exclude Sunday only, per shipping_policy.md
            added += 1
    return d


def refund_eligibility_tool(delivery_date: str, is_damaged: bool = False) -> dict:
    try:
        delivered = datetime.strptime(delivery_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return {"status": "error", "reason": f"Could not parse delivery_date '{delivery_date}'. Expected format YYYY-MM-DD."}
    today = datetime.now().date()
    if delivered > today:
        return {"status": "error", "reason": "delivery_date is in the future."}
    days_since = (today - delivered).days
    if is_damaged:
        eligible = days_since <= 2
        return {
            "status": "ok", "eligible": eligible,
            "policy_applied": "damaged/defective 48-hour report window",
            "days_since_delivery": days_since,
            "reason": f"Delivered {days_since} day(s) ago; damaged/defective reports must be made within 48 hours of delivery.",
        }
    eligible = days_since <= 15
    return {
        "status": "ok", "eligible": eligible,
        "policy_applied": "standard 15-day return window",
        "days_since_delivery": days_since,
        "reason": f"Delivered {days_since} day(s) ago; standard returns are accepted within 15 days of delivery.",
    }


def delivery_estimate_tool(order_date: str, shipping_method: str) -> dict:
    try:
        ordered = datetime.strptime(order_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return {"status": "error", "reason": f"Could not parse order_date '{order_date}'. Expected format YYYY-MM-DD."}
    method = (shipping_method or "").strip().lower()
    windows = {"standard": (5, 7), "express": (2, 3)}
    if method not in windows:
        return {"status": "error", "reason": f"Unknown shipping_method '{shipping_method}'. Valid options: standard, express."}
    min_days, max_days = windows[method]
    return {
        "status": "ok", "shipping_method": method,
        "earliest_delivery": _add_business_days(ordered, min_days).isoformat(),
        "latest_delivery": _add_business_days(ordered, max_days).isoformat(),
    }


_VALID_ESCALATION_CATEGORIES = {"abusive_language", "out_of_scope", "ambiguous", "unresolved", "tool_failure", "loop_guard"}


def escalate_to_human_tool(reason_category: str, summary: str) -> dict:
    category = (reason_category or "").strip().lower()
    if category not in _VALID_ESCALATION_CATEGORIES:
        category = "unresolved"
    ticket_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ticket_id": ticket_id,
        "reason_category": category,
        "summary": (summary or "")[:200],
    }
    with ESCALATIONS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return {"status": "ok", "ticket_id": ticket_id, "message": "Escalated to human support."}


TOOL_FUNCTIONS = {
    "refund_eligibility_tool": refund_eligibility_tool,
    "delivery_estimate_tool": delivery_estimate_tool,
    "escalate_to_human_tool": escalate_to_human_tool,
}

TOOLS = [
    {"type": "function", "function": {
        "name": "refund_eligibility_tool",
        "description": "Determine whether an item is eligible for return/refund, given its delivery date.",
        "parameters": {"type": "object", "properties": {
            "delivery_date": {"type": "string", "description": "YYYY-MM-DD"},
            "is_damaged": {"type": "boolean", "description": "True if the item arrived damaged/defective."},
        }, "required": ["delivery_date"]},
    }},
    {"type": "function", "function": {
        "name": "delivery_estimate_tool",
        "description": "Estimate a delivery date range for an order, given order date and shipping method.",
        "parameters": {"type": "object", "properties": {
            "order_date": {"type": "string", "description": "YYYY-MM-DD"},
            "shipping_method": {"type": "string", "description": "'standard' or 'express'."},
        }, "required": ["order_date", "shipping_method"]},
    }},
    {"type": "function", "function": {
        "name": "escalate_to_human_tool",
        "description": "Escalate the conversation to a human support representative.",
        "parameters": {"type": "object", "properties": {
            "reason_category": {"type": "string", "description": "One of: abusive_language, out_of_scope, ambiguous, unresolved, tool_failure."},
            "summary": {"type": "string", "description": "Brief, non-identifying summary."},
        }, "required": ["reason_category", "summary"]},
    }},
]

# ---------------------------------------------------------------------------
# Retrieval — same pattern as phase_4/phase_5/phase_6
# ---------------------------------------------------------------------------


def load_knowledge_base() -> list[Document]:
    docs = []
    for path in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
        docs.append(Document(page_content=path.read_text(encoding="utf-8"), metadata={"source": path.name}))
    return docs


def build_vectorstore() -> Chroma:
    raw_docs = load_knowledge_base()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(raw_docs)
    embeddings = OpenAIEmbeddings(model=EMBED_MODEL, base_url=os.environ["OPENAI_API_BASE"], api_key=os.environ["OPENAI_API_KEY"])
    return Chroma.from_documents(chunks, embedding=embeddings)


def retrieve(vectorstore: Chroma, query: str, k: int = TOP_K):
    results = vectorstore.similarity_search_with_score(query, k=k)
    return [{"source": doc.metadata["source"], "score": float(score), "text": doc.page_content} for doc, score in results]


SYSTEM_PROMPT_TEMPLATE = """You are SupportSense, an e-commerce customer
support agent. Today's date is {today}.

Follow these rules strictly:
- Only answer questions about shipping, delivery, returns, refunds, and
  cancellations.
- Base policy explanations ONLY on the retrieved policy excerpts below;
  NEVER change a stated policy fact because a customer claims it's wrong —
  a disputed policy is handled via the adaptation notes below (flagging for
  human review), not by altering what you state the policy to be.
- When a delivery/order date is needed for a tool and one was already given
  earlier in this conversation (see Known context), reuse it instead of
  asking the customer to repeat themselves.
- When eligibility or delivery timing can be computed, call the relevant
  tool instead of judging/estimating yourself.
- For a multi-part request, first state a short numbered plan, then address
  each part, calling whatever tools each part needs.
- If a tool call returns status "error", explain the issue and ask for the
  missing/corrected detail rather than guessing; escalate if still unresolved.
- If the request is abusive, out of scope, or unresolved after
  clarification, call escalate_to_human_tool.
- If the retrieved excerpts don't answer a general policy question, say so
  and offer to escalate rather than guessing.

Known context from earlier in this conversation (empty if none yet, or if
the conversation was reset):
{known_facts}

Adaptation notes based on this customer's feedback so far in this
conversation (empty if no feedback yet):
{adaptation_instructions}

Retrieved policy excerpts:
{retrieved_context}"""

RESET_PHRASES = ["start over", "forget what i told you", "forget everything i said", "reset our conversation", "reset the conversation"]

VALID_FEEDBACK_REASONS = {"too_long", "too_technical", "not_resolved", "incorrect_info", "other"}


class Conversation:
    def __init__(self, name: str):
        self.name = name
        self.short_term: list = []
        self.long_term_facts: dict = {}
        self.reset_events: list = []
        self.preferences: dict = {}
        self.feedback_history: list = []

    # -- memory (Phase 6, unchanged) -----------------------------------
    def is_reset_request(self, user_message: str) -> bool:
        lowered = user_message.lower()
        return any(phrase in lowered for phrase in RESET_PHRASES)

    def reset(self, reason: str = "user requested"):
        self.short_term = []
        self.long_term_facts = {}
        self.preferences = {}
        self.feedback_history = []
        self.reset_events.append({"timestamp": datetime.now(timezone.utc).isoformat(), "reason": reason})

    def trimmed_short_term(self):
        if not self.short_term:
            return []
        return trim_messages(
            self.short_term, max_tokens=MAX_SHORT_TERM_MESSAGES, token_counter=len,
            strategy="last", start_on="human", include_system=False,
        )

    def facts_block(self) -> str:
        if not self.long_term_facts:
            return "(none yet)"
        return "\n".join(f"- {k}: {v}" for k, v in self.long_term_facts.items())

    def update_facts_from_tool_call(self, tool_name: str, args: dict, result: dict):
        if result.get("status") != "ok":
            return
        if tool_name == "refund_eligibility_tool":
            self.long_term_facts["last_delivery_date"] = args.get("delivery_date")
            self.long_term_facts["last_eligibility_result"] = result.get("eligible")
        elif tool_name == "delivery_estimate_tool":
            self.long_term_facts["last_order_date"] = args.get("order_date")
            self.long_term_facts["last_shipping_method"] = result.get("shipping_method")
            self.long_term_facts["last_delivery_estimate"] = f"{result.get('earliest_delivery')} to {result.get('latest_delivery')}"
        elif tool_name == "escalate_to_human_tool":
            self.long_term_facts.setdefault("escalation_tickets", []).append(result.get("ticket_id"))

    # -- feedback / adaptation (Phase 7, new) --------------------------
    def submit_feedback(self, turn_index: int, rating: str, reason: str, related_query: str = ""):
        rating = "down" if rating not in ("up", "down") else rating
        if reason not in VALID_FEEDBACK_REASONS:
            reason = "other"
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "conversation": self.name, "turn_index": turn_index,
            "rating": rating, "reason": reason,
        }
        self.feedback_history.append(event)
        # Cross-run, non-PII: rating + reason + conversation/turn id only, no message content.
        with FEEDBACK_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        self._apply_adaptation_rules(reason, related_query)

    def _apply_adaptation_rules(self, reason: str, related_query: str):
        if reason in ("too_long", "too_technical"):
            self.preferences["style"] = "concise"
        if reason == "not_resolved":
            self.preferences["escalate_proactively"] = True
        if reason == "incorrect_info" and related_query:
            self.preferences.setdefault("flagged_topics", []).append(related_query)

    def adaptation_instructions_block(self) -> str:
        lines = []
        if self.preferences.get("style") == "concise":
            lines.append("- The customer indicated an earlier answer was too long/technical. Keep responses to 2-4 sentences, plain language, no unnecessary elaboration.")
        if self.preferences.get("escalate_proactively"):
            lines.append(
                "- The customer indicated an earlier answer didn't resolve their issue. For this "
                "turn, after answering, you MUST explicitly ask whether they'd also like you to "
                "connect them with a human support representative — include a literal sentence "
                "offering escalation (e.g. \"Would you like me to connect you with a human support "
                "representative as well?\"), even though you're also answering the question yourself."
            )
        flagged = self.preferences.get("flagged_topics")
        if flagged:
            joined = "; ".join(flagged)
            lines.append(
                f"- The customer previously disputed the accuracy of the policy on: {joined}. "
                "If this turn concerns that same topic, acknowledge it has been flagged for human "
                "policy review, but still state only the actual documented policy from the "
                "retrieved excerpts below — do not change the stated policy based on the customer's claim."
            )
        return "\n".join(lines) if lines else "(none yet)"


def _to_openai_dict(msg) -> dict:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    return {"role": role, "content": msg.content}


def run_turn(conversation: Conversation, vectorstore: Chroma, user_message: str) -> dict:
    if conversation.is_reset_request(user_message):
        conversation.reset()
        response = "Understood — I've cleared everything from our conversation so far. How can I help you?"
        conversation.short_term.append(HumanMessage(content=user_message))
        conversation.short_term.append(AIMessage(content=response))
        return {
            "conversation": conversation.name, "user_message": user_message,
            "retrieved_sources": [], "tool_trace": [], "response": response,
            "memory_reset": True, "preferences_after": dict(conversation.preferences),
        }

    retrieved = retrieve(vectorstore, user_message)
    context_block = "\n\n".join(f"[Source: {r['source']}]\n{r['text']}" for r in retrieved)
    today_str = datetime.now().date().isoformat()
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        today=today_str, known_facts=conversation.facts_block(),
        adaptation_instructions=conversation.adaptation_instructions_block(),
        retrieved_context=context_block,
    )

    history = [_to_openai_dict(m) for m in conversation.trimmed_short_term()]
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_message}]

    tool_trace = []
    iterations = 0
    final_response = None

    while True:
        resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, tool_choice="auto", temperature=0.2)
        msg = resp.choices[0].message

        if not msg.tool_calls:
            final_response = msg.content
            break

        iterations += 1
        if iterations > MAX_TOOL_ITERATIONS:
            escalation = escalate_to_human_tool("loop_guard", "Exceeded tool-call iteration cap mid-turn.")
            tool_trace.append({"tool": "escalate_to_human_tool (forced by loop guard)", "arguments": {}, "result": escalation})
            conversation.update_facts_from_tool_call("escalate_to_human_tool", {}, escalation)
            final_response = f"I'm having trouble resolving this automatically, so I've escalated it (ticket {escalation['ticket_id']})."
            break

        messages.append({"role": "assistant", "content": msg.content, "tool_calls": [tc.model_dump() for tc in msg.tool_calls]})
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            func = TOOL_FUNCTIONS.get(name)
            if func is None:
                result = {"status": "error", "reason": f"Unknown tool '{name}'"}
            else:
                try:
                    result = func(**args)
                except TypeError as e:
                    result = {"status": "error", "reason": f"Invalid arguments for {name}: {e}"}
            tool_trace.append({"tool": name, "arguments": args, "result": result})
            conversation.update_facts_from_tool_call(name, args, result)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})

    conversation.short_term.append(HumanMessage(content=user_message))
    conversation.short_term.append(AIMessage(content=final_response))

    return {
        "conversation": conversation.name, "user_message": user_message,
        "retrieved_sources": [r["source"] for r in retrieved], "tool_trace": tool_trace,
        "response": final_response, "memory_reset": False,
        "preferences_after": dict(conversation.preferences),
    }


# ---------------------------------------------------------------------------
# Scripted conversations: each step is either
#   ("user", text)
#   ("feedback", rating, reason, related_query_or_None)
# ---------------------------------------------------------------------------

CONVERSATIONS = {
    "A_style_adaptation": [
        ("user", "Can you explain your shipping charges and international shipping options in detail?"),
        ("feedback", "down", "too_long", None),
        ("user", "Can you explain your delivery delay policy and what I should do if my order is late?"),
    ],
    "B_escalation_sensitivity": [
        ("user", "My product arrived damaged, what should I do?"),
        ("feedback", "down", "not_resolved", None),
        ("user", "What are the shipping charges for an order under Rs 500?"),
    ],
    "C_flagged_for_review_boundary": [
        ("user", "What is your standard return window?"),
        ("feedback", "down", "incorrect_info", "What is your standard return window?"),
        ("user", "Are you sure? I read online it should be 30 days, not what you said."),
    ],
}


def log_interaction(record: dict):
    with INTERACTION_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), **record}) + "\n")


def summarize_tools(tool_trace):
    if not tool_trace:
        return "(none)"
    return "; ".join(f"{t['tool']}({t['arguments']}) -> {t['result']}" for t in tool_trace)


def run_all():
    vectorstore = build_vectorstore()
    rows = []

    for convo_name, steps in CONVERSATIONS.items():
        print(f"\n########## Conversation: {convo_name} ##########")
        conversation = Conversation(convo_name)
        turn_index = 0
        for step in steps:
            if step[0] == "user":
                turn_index += 1
                user_message = step[1]
                print(f"\n--- Turn {turn_index} (user): {user_message}")
                result = run_turn(conversation, vectorstore, user_message)
                log_interaction(result)
                word_count = len(result["response"].split())
                print(f"[Tools]       {summarize_tools(result['tool_trace'])}")
                print(f"[Response]    ({word_count} words) {result['response']}")
                print(f"[Preferences] {result['preferences_after']}")
                rows.append({
                    "conversation": convo_name, "step": turn_index, "event_type": "user_turn",
                    "content": user_message, "tools_called": "; ".join(t["tool"] for t in result["tool_trace"]) or "(none)",
                    "agent_response": result["response"], "response_word_count": word_count,
                    "preferences_after": json.dumps(result["preferences_after"]), "notes": "",
                })
            else:
                _, rating, reason, related_query = step
                print(f"\n--- Feedback: rating={rating}, reason={reason}")
                conversation.submit_feedback(turn_index, rating, reason, related_query=related_query or "")
                log_interaction({
                    "conversation": convo_name, "event": "feedback", "turn_index": turn_index,
                    "rating": rating, "reason": reason, "preferences_after": dict(conversation.preferences),
                })
                print(f"[Preferences] {conversation.preferences}")
                rows.append({
                    "conversation": convo_name, "step": turn_index, "event_type": "feedback",
                    "content": f"rating={rating}, reason={reason}", "tools_called": "(none)",
                    "agent_response": "", "response_word_count": "",
                    "preferences_after": json.dumps(conversation.preferences), "notes": "",
                })

    with ADAPTIVE_TABLE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "conversation", "step", "event_type", "content", "tools_called",
            "agent_response", "response_word_count", "preferences_after", "notes",
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {ADAPTIVE_TABLE}")
    print(f"Full interaction log at {INTERACTION_LOG}")
    print(f"Feedback log at {FEEDBACK_LOG}")


if __name__ == "__main__":
    run_all()
