"""
SupportSense AI — Phase 8: Deployment Readiness (agent core)
=================================================================
Factors Phase 7's agent logic (tools, retrieval, memory + adaptation) out of
a single script into an importable module shared by `app_api.py` (the
FastAPI deployment) and `phase8_cli_demo.py` (the offline evidence script).

New in this phase, on top of Phase 7's unchanged tools/retrieval/Conversation
logic:
  - Latency instrumentation: every LLM call, tool call, and retrieval call is
    timed; `run_turn()` returns a `timing` block alongside the response.
  - Graceful failure handling: `_call_llm()` and `_retrieve_with_fallback()`
    each retry once on exception, then raise a narrow `AgentUnavailableError`
    instead of letting the raw SDK exception propagate. `run_turn()` catches
    that, logs a non-PII error record, forces an escalation, and returns a
    safe fallback response — a turn ALWAYS completes with a normal response
    object, never an unhandled exception.

Non-PII logging (same rule as Phases 5-7's escalations.jsonl/feedback_log.jsonl):
error/trace logs record conversation id, turn index, latency, error type/
truncated message — never raw user message content.
"""

import json
import os
import sys
import time
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
LLM_MAX_ATTEMPTS = 2
LLM_RETRY_BACKOFF_SECONDS = 0.5

PHASE_DIR = Path(__file__).parent
KNOWLEDGE_BASE_DIR = PHASE_DIR / "knowledge_base"
LOG_DIR = PHASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
ESCALATIONS_LOG = LOG_DIR / "escalations.jsonl"
ERROR_LOG = LOG_DIR / "error_log.jsonl"
TRACE_LOG = LOG_DIR / "trace_log.jsonl"

client = OpenAI(
    base_url=os.environ["OPENAI_API_BASE"],
    api_key=os.environ["OPENAI_API_KEY"],
)


class AgentUnavailableError(Exception):
    """Raised when a dependency (LLM or retrieval) fails after retrying."""


def log_error(conversation_id: str, turn_index: int, error_type: str, error_message: str, recovered: bool, action_taken: str, trace_id: str = ""):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "conversation_id": conversation_id,
        "turn_index": turn_index,
        "error_type": error_type,
        "error_message": (error_message or "")[:200],
        "recovered": recovered,
        "action_taken": action_taken,
    }
    with ERROR_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record


def log_trace(record: dict):
    with TRACE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), **record}) + "\n")


# ---------------------------------------------------------------------------
# Tools — unchanged from phase_5/phase_6/phase_7
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
# Retrieval — same pattern as phase_4-7, wrapped with a graceful fallback
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


def _retrieve_with_fallback(vectorstore, query: str, conversation_id: str, turn_index: int, trace_id: str, k: int = TOP_K):
    """Retrieval wrapped with one retry; raises AgentUnavailableError (never a raw SDK/Chroma
    exception) if the vectorstore is unusable, so the caller can fail safely instead of
    fabricating an ungrounded policy answer."""
    last_exc = None
    for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
        started = time.perf_counter()
        try:
            results = vectorstore.similarity_search_with_score(query, k=k)
            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
            return [{"source": doc.metadata["source"], "score": float(score), "text": doc.page_content} for doc, score in results], elapsed_ms
        except Exception as exc:  # noqa: BLE001 - deliberately broad: any retrieval failure must degrade safely
            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
            last_exc = exc
            log_error(conversation_id, turn_index, type(exc).__name__, str(exc), recovered=(attempt < LLM_MAX_ATTEMPTS), action_taken=f"retrieval attempt {attempt}/{LLM_MAX_ATTEMPTS}", trace_id=trace_id)
            if attempt < LLM_MAX_ATTEMPTS:
                time.sleep(LLM_RETRY_BACKOFF_SECONDS)
    raise AgentUnavailableError(f"retrieval failed after {LLM_MAX_ATTEMPTS} attempts: {last_exc}")


# ---------------------------------------------------------------------------
# LLM call — wrapped with one retry, same fail-safe shape as retrieval
# ---------------------------------------------------------------------------


def _call_llm(messages, conversation_id: str, turn_index: int, trace_id: str):
    last_exc = None
    for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
        started = time.perf_counter()
        try:
            resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, tool_choice="auto", temperature=0.2)
            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
            return resp, elapsed_ms
        except Exception as exc:  # noqa: BLE001 - deliberately broad: any LLM-call failure must degrade safely
            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
            last_exc = exc
            log_error(conversation_id, turn_index, type(exc).__name__, str(exc), recovered=(attempt < LLM_MAX_ATTEMPTS), action_taken=f"llm_call attempt {attempt}/{LLM_MAX_ATTEMPTS}", trace_id=trace_id)
            if attempt < LLM_MAX_ATTEMPTS:
                time.sleep(LLM_RETRY_BACKOFF_SECONDS)
    raise AgentUnavailableError(f"LLM call failed after {LLM_MAX_ATTEMPTS} attempts: {last_exc}")


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
- When eligibility or delivery timing can be computed, ALWAYS call the
  relevant tool instead of judging/estimating yourself — this includes
  damaged/defective-item eligibility (the 48-hour window), not only standard
  returns. Do this even when the retrieved policy excerpts already describe
  the window in words: the tool performs the actual date arithmetic against
  today's date, which you must never compute yourself, for either window.
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
        self.turn_index = 0

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

    # -- feedback / adaptation (Phase 7, unchanged) --------------------
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
        feedback_log = LOG_DIR / "feedback_log.jsonl"
        with feedback_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        self._apply_adaptation_rules(reason, related_query)
        return dict(self.preferences)

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


def run_turn(conversation: Conversation, vectorstore, user_message: str) -> dict:
    """Runs one turn end-to-end. ALWAYS returns a normal response dict — retrieval or LLM
    failures are caught internally and converted into a graceful fallback + forced escalation,
    never an unhandled exception."""
    trace_id = uuid.uuid4().hex[:12]
    turn_started = time.perf_counter()
    conversation.turn_index += 1
    turn_index = conversation.turn_index

    if conversation.is_reset_request(user_message):
        conversation.reset()
        response = "Understood — I've cleared everything from our conversation so far. How can I help you?"
        conversation.short_term.append(HumanMessage(content=user_message))
        conversation.short_term.append(AIMessage(content=response))
        timing = {"retrieval_ms": None, "llm_call_ms": [], "tool_call_ms": [], "total_ms": round((time.perf_counter() - turn_started) * 1000, 1)}
        log_trace({"trace_id": trace_id, "conversation_id": conversation.name, "turn_index": turn_index, "scenario": "reset", "status": "ok", **timing})
        return {
            "trace_id": trace_id, "conversation": conversation.name, "turn_index": turn_index,
            "user_message": user_message, "retrieved_sources": [], "tool_trace": [], "response": response,
            "memory_reset": True, "preferences_after": dict(conversation.preferences),
            "timing": timing, "status": "ok",
        }

    tool_call_ms = []
    llm_call_ms = []

    try:
        retrieved, retrieval_ms = _retrieve_with_fallback(vectorstore, user_message, conversation.name, turn_index, trace_id)
    except AgentUnavailableError as exc:
        escalation = escalate_to_human_tool("tool_failure", "Retrieval unavailable; cannot safely ground a policy answer.")
        conversation.update_facts_from_tool_call("escalate_to_human_tool", {}, escalation)
        response = f"I'm having trouble accessing our policy information right now, so I don't want to guess. I've escalated this to a human agent (ticket {escalation['ticket_id']})."
        conversation.short_term.append(HumanMessage(content=user_message))
        conversation.short_term.append(AIMessage(content=response))
        timing = {"retrieval_ms": None, "llm_call_ms": [], "tool_call_ms": [], "total_ms": round((time.perf_counter() - turn_started) * 1000, 1)}
        log_trace({"trace_id": trace_id, "conversation_id": conversation.name, "turn_index": turn_index, "scenario": "retrieval_failure", "status": "degraded_ok", **timing})
        return {
            "trace_id": trace_id, "conversation": conversation.name, "turn_index": turn_index,
            "user_message": user_message, "retrieved_sources": [], "tool_trace": [{"tool": "escalate_to_human_tool (forced by retrieval failure)", "arguments": {}, "result": escalation}],
            "response": response, "memory_reset": False, "preferences_after": dict(conversation.preferences),
            "timing": timing, "status": "degraded_ok", "error": str(exc),
        }

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

    try:
        while True:
            resp, call_ms = _call_llm(messages, conversation.name, turn_index, trace_id)
            llm_call_ms.append(call_ms)
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
                tool_started = time.perf_counter()
                if func is None:
                    result = {"status": "error", "reason": f"Unknown tool '{name}'"}
                else:
                    try:
                        result = func(**args)
                    except TypeError as e:
                        result = {"status": "error", "reason": f"Invalid arguments for {name}: {e}"}
                tool_call_ms.append(round((time.perf_counter() - tool_started) * 1000, 1))
                tool_trace.append({"tool": name, "arguments": args, "result": result})
                conversation.update_facts_from_tool_call(name, args, result)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})
        status = "ok"
        error_str = None
    except AgentUnavailableError as exc:
        escalation = escalate_to_human_tool("tool_failure", "LLM service unavailable after retry.")
        tool_trace.append({"tool": "escalate_to_human_tool (forced by LLM failure)", "arguments": {}, "result": escalation})
        conversation.update_facts_from_tool_call("escalate_to_human_tool", {}, escalation)
        final_response = f"I'm having trouble processing this right now — I've escalated it to a human agent (ticket {escalation['ticket_id']})."
        status = "degraded_ok"
        error_str = str(exc)

    conversation.short_term.append(HumanMessage(content=user_message))
    conversation.short_term.append(AIMessage(content=final_response))

    timing = {
        "retrieval_ms": retrieval_ms, "llm_call_ms": llm_call_ms, "tool_call_ms": tool_call_ms,
        "total_ms": round((time.perf_counter() - turn_started) * 1000, 1),
    }
    log_trace({"trace_id": trace_id, "conversation_id": conversation.name, "turn_index": turn_index, "scenario": "chat", "status": status, **timing})

    return {
        "trace_id": trace_id, "conversation": conversation.name, "turn_index": turn_index,
        "user_message": user_message, "retrieved_sources": [r["source"] for r in retrieved], "tool_trace": tool_trace,
        "response": final_response, "memory_reset": False,
        "preferences_after": dict(conversation.preferences),
        "timing": timing, "status": status, "error": error_str,
    }
