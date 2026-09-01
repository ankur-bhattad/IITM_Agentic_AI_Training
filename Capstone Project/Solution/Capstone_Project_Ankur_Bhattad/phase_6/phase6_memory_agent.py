"""
SupportSense AI — Phase 6: Planning, Memory & Context
=========================================================
Extends Phase 5's tool-calling + retrieval agent into a multi-turn
`Conversation`: the agent now carries facts across turns instead of treating
every query independently (Phase 5's carried-forward limitation), and states
a short plan before acting on compound, multi-part requests.

Memory design:
  - Short-term memory: the running (HumanMessage, AIMessage) turn history for
    one Conversation, windowed with langchain_core.messages.trim_messages so
    the history sent to the model each turn is capped instead of growing
    unbounded. Only the user's text and the final assistant answer for each
    turn are kept here — NOT the intermediate tool-call/tool-result messages,
    so trimming can never split a tool call from its result.
  - Long-term (session) memory: a small structured facts dict, updated from
    successful tool calls as they happen (e.g. the delivery date used in a
    refund_eligibility_tool call), and re-injected into the system prompt
    every turn regardless of short-term trimming.
  - Retention rule: both stores live only inside one Conversation object /
    process — never written to disk — matching the Problem Framing
    Document's "customer information should only be used during the active
    session" constraint.
  - Reset rule: a user phrase like "start over" / "forget what I told you"
    clears both stores immediately, logged as a memory_reset event.

The framing doc's declared "LangChain Conversation Memory" refers to
langchain.memory.ConversationBufferMemory, which no longer exists in the
installed langchain_core (1.6.0) — trim_messages is the current LangChain
primitive for this and is used here instead.

Run:
    python phase6_memory_agent.py

Requires `utils.py` (sets OPENAI_API_BASE / OPENAI_API_KEY) in the same
directory, and network access to the Vocareum endpoint.

Outputs:
    logs/phase6_interaction_log.jsonl       — full per-turn transcripts + memory snapshots
    logs/multi_turn_conversation_table.csv  — Conversation -> Turn -> User -> Response -> Notes
"""

import csv
import json
import os
import sys
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
MAX_SHORT_TERM_MESSAGES = 12  # ~6 (user, assistant) turn pairs

PHASE_DIR = Path(__file__).parent
KNOWLEDGE_BASE_DIR = PHASE_DIR / "knowledge_base"
LOG_DIR = PHASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
INTERACTION_LOG = LOG_DIR / "phase6_interaction_log.jsonl"
CONVERSATION_TABLE = LOG_DIR / "multi_turn_conversation_table.csv"
ESCALATIONS_LOG = LOG_DIR / "escalations.jsonl"

client = OpenAI(
    base_url=os.environ["OPENAI_API_BASE"],
    api_key=os.environ["OPENAI_API_KEY"],
)

# ---------------------------------------------------------------------------
# Tools — unchanged from phase_5/phase5_tool_agent.py
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
        eligible = days_since <= 2  # day-granularity approximation of the 48-hour window
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
    import uuid
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
        "description": "Determine whether an item is eligible for return/refund, given its delivery date. Use this instead of judging eligibility yourself whenever a delivery/purchase date is known (from this message or earlier in the conversation).",
        "parameters": {"type": "object", "properties": {
            "delivery_date": {"type": "string", "description": "The date the item was delivered, in YYYY-MM-DD format."},
            "is_damaged": {"type": "boolean", "description": "True if the customer reports (or is asking about) the item arriving damaged or defective."},
        }, "required": ["delivery_date"]},
    }},
    {"type": "function", "function": {
        "name": "delivery_estimate_tool",
        "description": "Estimate a delivery date range for an order, given its order date and shipping method.",
        "parameters": {"type": "object", "properties": {
            "order_date": {"type": "string", "description": "The date the order was placed, in YYYY-MM-DD format."},
            "shipping_method": {"type": "string", "description": "Either 'standard' or 'express'."},
        }, "required": ["order_date", "shipping_method"]},
    }},
    {"type": "function", "function": {
        "name": "escalate_to_human_tool",
        "description": "Escalate the conversation to a human support representative.",
        "parameters": {"type": "object", "properties": {
            "reason_category": {"type": "string", "description": "One of: abusive_language, out_of_scope, ambiguous, unresolved, tool_failure."},
            "summary": {"type": "string", "description": "A brief, non-identifying summary. No names, order IDs, or contact details."},
        }, "required": ["reason_category", "summary"]},
    }},
]

# ---------------------------------------------------------------------------
# Retrieval — same pattern as phase_4/phase_5
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
  never invent policy numbers or windows.
- When a delivery/order date is needed for a tool and one was already given
  earlier in this conversation (see "Known context" below), reuse it instead
  of asking the customer to repeat themselves — unless the conversation has
  been reset, in which case no earlier context applies.
- When the user asks whether a specific order is eligible for return/refund
  and a delivery date is known (from this message or Known context), call
  refund_eligibility_tool instead of judging eligibility yourself.
- When the user asks when an order will arrive and an order date + shipping
  method are known, call delivery_estimate_tool instead of estimating
  yourself.
- For a request with more than one distinct part (e.g. an eligibility
  question AND a delivery estimate in the same message), first state a short
  numbered plan of the sub-tasks, then address each one — calling whatever
  tools each part needs — before giving a combined final answer.
- If a tool call returns status "error", explain the issue and ask for the
  missing/corrected detail rather than guessing; escalate if still unresolved.
- If the request is abusive, out of scope, or unresolved after
  clarification, call escalate_to_human_tool.
- If the retrieved excerpts don't answer a general policy question, say so
  and offer to escalate rather than guessing.

Known context from earlier in this conversation (empty if none yet, or if
the conversation was just reset):
{known_facts}

Retrieved policy excerpts:
{retrieved_context}"""

RESET_PHRASES = ["start over", "forget what i told you", "forget everything i said", "reset our conversation", "reset the conversation"]


class Conversation:
    def __init__(self, name: str):
        self.name = name
        self.short_term: list = []  # list of HumanMessage/AIMessage — this session only
        self.long_term_facts: dict = {}  # this session only, never persisted to disk
        self.reset_events: list = []

    def is_reset_request(self, user_message: str) -> bool:
        lowered = user_message.lower()
        return any(phrase in lowered for phrase in RESET_PHRASES)

    def reset(self, reason: str = "user requested"):
        self.short_term = []
        self.long_term_facts = {}
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
            "memory_reset": True, "facts_after": dict(conversation.long_term_facts),
        }

    retrieved = retrieve(vectorstore, user_message)
    context_block = "\n\n".join(f"[Source: {r['source']}]\n{r['text']}" for r in retrieved)
    today_str = datetime.now().date().isoformat()
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        today=today_str, known_facts=conversation.facts_block(), retrieved_context=context_block
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
        "response": final_response, "memory_reset": False, "facts_after": dict(conversation.long_term_facts),
    }


def demo_short_term_trimming() -> dict:
    """Direct, deterministic proof that trim_messages actually caps the
    short-term window, independent of whether any of the 3 demo conversations
    happen to run long enough to trigger it organically."""
    convo = Conversation("synthetic_trim_test")
    for i in range(10):  # 10 turns = 20 messages, well over MAX_SHORT_TERM_MESSAGES
        convo.short_term.append(HumanMessage(content=f"filler user turn {i}"))
        convo.short_term.append(AIMessage(content=f"filler agent reply {i}"))
    trimmed = convo.trimmed_short_term()
    return {
        "conversation": "[synthetic] short-term trimming test",
        "user_message": "(n/a — direct trim_messages() call)",
        "retrieved_sources": [], "tool_trace": [],
        "response": (
            f"Before trimming: {len(convo.short_term)} messages. After trim_messages(max_tokens="
            f"{MAX_SHORT_TERM_MESSAGES}, strategy='last'): {len(trimmed)} messages retained, "
            f"starting with: '{trimmed[0].content}' (oldest turns correctly dropped)."
        ),
        "memory_reset": False, "facts_after": {},
    }


CONVERSATIONS = {
    "A_recall_and_followup": [
        "Is my order delivered on 2026-08-28 eligible for return?",
        "What if it had arrived damaged instead?",
    ],
    "B_planning_decomposition": [
        "Can you tell me if my item delivered on 2026-08-10 is returnable, and also estimate delivery for a new order I placed on 2026-09-01 via express shipping?",
    ],
    "C_reset": [
        "Is my order delivered on 2026-08-28 eligible for return?",
        "Actually, please forget what I told you and start over.",
        "Is my item still returnable?",
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

    for convo_name, turns in CONVERSATIONS.items():
        print(f"\n########## Conversation: {convo_name} ##########")
        conversation = Conversation(convo_name)
        for turn_num, user_message in enumerate(turns, start=1):
            print(f"\n--- Turn {turn_num}: {user_message}")
            result = run_turn(conversation, vectorstore, user_message)
            log_interaction(result)
            print(f"[Tools]    {summarize_tools(result['tool_trace'])}")
            print(f"[Response] {result['response']}")
            print(f"[Facts]    {result['facts_after']}")
            rows.append({
                "conversation": convo_name, "turn": turn_num, "user_message": user_message,
                "tools_called": "; ".join(t["tool"] for t in result["tool_trace"]) or "(none)",
                "agent_response": result["response"],
                "memory_reset": result["memory_reset"],
                "facts_after_turn": json.dumps(result["facts_after"]),
                "notes": "",
            })

    print("\n########## Synthetic short-term trimming demonstration ##########")
    trim_result = demo_short_term_trimming()
    log_interaction(trim_result)
    print(f"[Response] {trim_result['response']}")
    rows.append({
        "conversation": trim_result["conversation"], "turn": 1, "user_message": trim_result["user_message"],
        "tools_called": "(none)", "agent_response": trim_result["response"],
        "memory_reset": False, "facts_after_turn": "{}", "notes": "",
    })

    with CONVERSATION_TABLE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "conversation", "turn", "user_message", "tools_called", "agent_response",
            "memory_reset", "facts_after_turn", "notes",
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {CONVERSATION_TABLE}")
    print(f"Full interaction log at {INTERACTION_LOG}")


if __name__ == "__main__":
    run_all()
