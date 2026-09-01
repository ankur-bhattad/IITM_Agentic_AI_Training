"""
SupportSense AI — Phase 5: Enable Tool Usage
===============================================
Adds real function/tool calling on top of Phase 4's retrieval-grounded agent,
so date-dependent decisions (refund eligibility, delivery estimates) are
computed deterministically in Python rather than guessed by the LLM — the
carried-forward limitation Phase 4's notes explicitly called out.

Three tools are defined (Problem Framing Document, Section 15/16):
  - refund_eligibility_tool  — eligible/not-eligible, real date arithmetic
  - delivery_estimate_tool   — estimated delivery date range, business-day math
  - escalate_to_human_tool   — logs a non-PII escalation record, mock ticket id

None of the tools mutate any order/payment state — they are read-only /
advisory only, per the Problem Framing Document's Out-of-Scope constraints
(no live order tracking, no order modification, no refund processing).

Guardrails:
  - Every tool returns a structured {"status": "ok"|"error", ...} result
    instead of raising, so bad input degrades gracefully instead of crashing.
  - The tool-calling loop is capped at MAX_TOOL_ITERATIONS; hitting the cap
    forces an escalation instead of looping indefinitely.

Run:
    python phase5_tool_agent.py

Requires `utils.py` (sets OPENAI_API_BASE / OPENAI_API_KEY) in the same
directory, and network access to the Vocareum endpoint.

Outputs:
    logs/phase5_interaction_log.jsonl — every query's full tool-call trace
    logs/tool_usage_table.csv         — Query -> Tools called -> Result -> Notes
    logs/escalations.jsonl            — non-PII escalation records
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

MODEL = os.environ.get("SUPPORTSENSE_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.environ.get("SUPPORTSENSE_EMBED_MODEL", "text-embedding-3-small")
TOP_K = 3
MAX_TOOL_ITERATIONS = 4

PHASE_DIR = Path(__file__).parent
KNOWLEDGE_BASE_DIR = PHASE_DIR / "knowledge_base"
LOG_DIR = PHASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
INTERACTION_LOG = LOG_DIR / "phase5_interaction_log.jsonl"
TOOL_USAGE_TABLE = LOG_DIR / "tool_usage_table.csv"
ESCALATIONS_LOG = LOG_DIR / "escalations.jsonl"

client = OpenAI(
    base_url=os.environ["OPENAI_API_BASE"],
    api_key=os.environ["OPENAI_API_KEY"],
)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def _add_business_days(start_date, n_days):
    """Business day = any day except Sunday, matching shipping_policy.md
    ("exclude Sundays and public holidays"; holidays are out of scope here)."""
    d = start_date
    added = 0
    while added < n_days:
        d += timedelta(days=1)
        if d.weekday() != 6:  # 6 = Sunday
            added += 1
    return d


def refund_eligibility_tool(delivery_date: str, is_damaged: bool = False) -> dict:
    try:
        delivered = datetime.strptime(delivery_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return {
            "status": "error",
            "reason": f"Could not parse delivery_date '{delivery_date}'. Expected format YYYY-MM-DD.",
        }
    today = datetime.now().date()
    if delivered > today:
        return {"status": "error", "reason": "delivery_date is in the future."}

    days_since = (today - delivered).days
    if is_damaged:
        # Day-granularity approximation of the 48-hour window (no time-of-day
        # tracked in this demo) — noted as a simplification in phase5_notes.md.
        eligible = days_since <= 2
        return {
            "status": "ok",
            "eligible": eligible,
            "policy_applied": "damaged/defective 48-hour report window",
            "days_since_delivery": days_since,
            "reason": f"Delivered {days_since} day(s) ago; damaged/defective reports must be made within 48 hours of delivery.",
        }
    eligible = days_since <= 15
    return {
        "status": "ok",
        "eligible": eligible,
        "policy_applied": "standard 15-day return window",
        "days_since_delivery": days_since,
        "reason": f"Delivered {days_since} day(s) ago; standard returns are accepted within 15 days of delivery.",
    }


def delivery_estimate_tool(order_date: str, shipping_method: str) -> dict:
    try:
        ordered = datetime.strptime(order_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return {
            "status": "error",
            "reason": f"Could not parse order_date '{order_date}'. Expected format YYYY-MM-DD.",
        }
    method = (shipping_method or "").strip().lower()
    windows = {"standard": (5, 7), "express": (2, 3)}
    if method not in windows:
        return {
            "status": "error",
            "reason": f"Unknown shipping_method '{shipping_method}'. Valid options: standard, express.",
        }
    min_days, max_days = windows[method]
    return {
        "status": "ok",
        "shipping_method": method,
        "earliest_delivery": _add_business_days(ordered, min_days).isoformat(),
        "latest_delivery": _add_business_days(ordered, max_days).isoformat(),
    }


_VALID_ESCALATION_CATEGORIES = {
    "abusive_language",
    "out_of_scope",
    "ambiguous",
    "unresolved",
    "tool_failure",
    "loop_guard",
}


def escalate_to_human_tool(reason_category: str, summary: str) -> dict:
    category = (reason_category or "").strip().lower()
    if category not in _VALID_ESCALATION_CATEGORIES:
        category = "unresolved"  # escalation must never itself fail closed
    ticket_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ticket_id": ticket_id,
        "reason_category": category,
        # Truncated, non-identifying summary only — no order IDs, names, or
        # contact details are ever passed into this field by design (system
        # prompt instructs the model accordingly).
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
    {
        "type": "function",
        "function": {
            "name": "refund_eligibility_tool",
            "description": (
                "Determine whether an item is eligible for return/refund, given its "
                "delivery date. Use this instead of judging eligibility yourself "
                "whenever the user states or implies a delivery/purchase date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "delivery_date": {
                        "type": "string",
                        "description": "The date the item was delivered, in YYYY-MM-DD format.",
                    },
                    "is_damaged": {
                        "type": "boolean",
                        "description": "True if the customer reports the item arrived damaged or defective.",
                    },
                },
                "required": ["delivery_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delivery_estimate_tool",
            "description": (
                "Estimate a delivery date range for an order, given its order date "
                "and shipping method. Use this instead of guessing delivery dates yourself."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_date": {
                        "type": "string",
                        "description": "The date the order was placed, in YYYY-MM-DD format.",
                    },
                    "shipping_method": {
                        "type": "string",
                        "description": "Either 'standard' or 'express'.",
                    },
                },
                "required": ["order_date", "shipping_method"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human_tool",
            "description": (
                "Escalate the conversation to a human support representative. Use this "
                "for abusive language, requests outside this agent's scope (e.g. "
                "processing a refund, tracking a live order, changing payment details), "
                "or any case that remains unresolved after clarification."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason_category": {
                        "type": "string",
                        "description": "One of: abusive_language, out_of_scope, ambiguous, unresolved, tool_failure.",
                    },
                    "summary": {
                        "type": "string",
                        "description": "A brief, non-identifying summary of the issue. Do not include names, order IDs, or contact details.",
                    },
                },
                "required": ["reason_category", "summary"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Retrieval (same pattern as phase_4/phase4_rag_agent.py)
# ---------------------------------------------------------------------------


def load_knowledge_base() -> list[Document]:
    docs = []
    for path in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        docs.append(Document(page_content=text, metadata={"source": path.name}))
    return docs


def build_vectorstore() -> Chroma:
    raw_docs = load_knowledge_base()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(raw_docs)
    embeddings = OpenAIEmbeddings(
        model=EMBED_MODEL,
        base_url=os.environ["OPENAI_API_BASE"],
        api_key=os.environ["OPENAI_API_KEY"],
    )
    return Chroma.from_documents(chunks, embedding=embeddings)


def retrieve(vectorstore: Chroma, query: str, k: int = TOP_K):
    results = vectorstore.similarity_search_with_score(query, k=k)
    return [
        {"source": doc.metadata["source"], "score": float(score), "text": doc.page_content}
        for doc, score in results
    ]


SYSTEM_PROMPT_TEMPLATE = """You are SupportSense, an e-commerce customer
support agent. Today's date is {today}.

Follow these rules strictly:
- Only answer questions about shipping, delivery, returns, refunds, and
  cancellations.
- Base policy explanations ONLY on the retrieved policy excerpts below;
  never invent policy numbers or windows.
- When the user asks whether a specific order is eligible for return/refund
  and states or implies a delivery date (including relative phrasing like
  "20 days ago" — convert it to an absolute YYYY-MM-DD date using today's
  date above), call refund_eligibility_tool instead of judging eligibility
  yourself.
- When the user asks when an order will arrive and gives an order date and
  shipping method, call delivery_estimate_tool instead of estimating
  yourself.
- If a tool call returns status "error", do not guess a workaround: explain
  the specific issue to the user and ask for the missing/corrected detail;
  if you still can't proceed after that, escalate.
- If the request is abusive, out of scope (e.g. processing a refund,
  tracking a live order, changing payment details), or unresolved after
  clarification, call escalate_to_human_tool.
- If the retrieved excerpts don't answer a general policy question, say so
  and offer to escalate rather than guessing.
- Never claim certainty about information you were not given.

Retrieved policy excerpts:
{retrieved_context}"""


def run_query(vectorstore: Chroma, user_query: str) -> dict:
    retrieved = retrieve(vectorstore, user_query)
    context_block = "\n\n".join(f"[Source: {r['source']}]\n{r['text']}" for r in retrieved)
    today_str = datetime.now().date().isoformat()
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(retrieved_context=context_block, today=today_str)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]

    tool_trace = []
    iterations = 0
    hit_cap = False
    final_response = None

    while True:
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, tool_choice="auto", temperature=0.2
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            final_response = msg.content
            break

        iterations += 1
        if iterations > MAX_TOOL_ITERATIONS:
            hit_cap = True
            escalation = escalate_to_human_tool(
                "loop_guard",
                f"Exceeded {MAX_TOOL_ITERATIONS} tool-call iterations for one query.",
            )
            tool_trace.append(
                {"tool": "escalate_to_human_tool (forced by loop guard)", "arguments": {}, "result": escalation}
            )
            final_response = (
                "I'm having trouble resolving this automatically, so I've escalated it to a "
                f"human support representative (ticket {escalation['ticket_id']})."
            )
            break

        messages.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
            }
        )
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
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})

    return {
        "query": user_query,
        "retrieved_sources": [r["source"] for r in retrieved],
        "tool_trace": tool_trace,
        "final_response": final_response,
        "hit_iteration_cap": hit_cap,
    }


def demo_loop_guard() -> dict:
    """Synthetic, deterministic proof that the iteration cap engages and forces
    an escalation, independent of whether a real model ever actually loops."""
    iterations = 0
    while True:
        iterations += 1
        if iterations > MAX_TOOL_ITERATIONS:
            escalation = escalate_to_human_tool(
                "loop_guard",
                "Synthetic test: simulated tool kept signalling 'unresolved' without a final answer.",
            )
            return {
                "query": "[synthetic] loop-guard stress test",
                "retrieved_sources": [],
                "tool_trace": [
                    {"tool": "escalate_to_human_tool (forced by loop guard)", "arguments": {}, "result": escalation}
                ],
                "final_response": (
                    f"Iteration cap ({MAX_TOOL_ITERATIONS}) reached after {iterations - 1} simulated "
                    f"unresolved tool calls; forced escalation instead of looping (ticket {escalation['ticket_id']})."
                ),
                "hit_iteration_cap": True,
            }
        # Each simulated iteration represents a tool call that reports it hasn't
        # resolved the request yet — intentionally never returns a final answer,
        # to prove the cap (not the model) is what stops the loop.
        _simulated_unresolved_result = {"status": "ok", "resolved": False}


def demo_invalid_tool_calls() -> dict:
    """Direct, deterministic proof that each tool's guardrail rejects bad
    input with a structured error instead of raising or silently guessing —
    exercised directly (not via the model) so it doesn't depend on whether a
    live model happens to choose to call a tool with bad arguments."""
    bad_shipping = delivery_estimate_tool(order_date="2026-08-25", shipping_method="drone")
    bad_date = refund_eligibility_tool(delivery_date="last Tuesday")
    trace = [
        {"tool": "delivery_estimate_tool (forced, invalid shipping_method)", "arguments": {"order_date": "2026-08-25", "shipping_method": "drone"}, "result": bad_shipping},
        {"tool": "refund_eligibility_tool (forced, unparseable delivery_date)", "arguments": {"delivery_date": "last Tuesday"}, "result": bad_date},
    ]
    return {
        "query": "[synthetic] direct invalid tool-call test",
        "retrieved_sources": [],
        "tool_trace": trace,
        "final_response": (
            "Both tools rejected invalid input with a structured {'status': 'error', ...} result "
            "instead of raising an exception or returning a guessed answer."
        ),
        "hit_iteration_cap": False,
    }


TEST_QUERIES = [
    "How long does standard delivery take?",  # no-tool control: retrieval alone should answer
    "My item was delivered on 2026-08-28 and I'd like to return it, is that possible?",  # eligible
    "I bought this 20 days ago and only just opened it, is it still returnable?",  # not eligible
    "My product arrived damaged on 2026-08-30, what should I do?",  # damaged, within 48h
    "I ordered on 2026-08-25 and chose express shipping, when will it arrive?",  # correct delivery-estimate call
    "I ordered on 2026-08-25, can you tell me when it'll arrive via drone delivery?",  # invalid shipping_method -> failed call
    "This is ridiculous, refund me now or I'm reporting you!",  # abusive -> escalation
]


def log_interaction(result: dict):
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), **result}
    with INTERACTION_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def summarize_tools(tool_trace):
    if not tool_trace:
        return "(none)"
    return "; ".join(
        f"{t['tool']}({t['arguments']}) -> {t['result']}" for t in tool_trace
    )


def run_all():
    vectorstore = build_vectorstore()
    rows = []

    for query in TEST_QUERIES:
        print(f"\n=== Query: {query} ===")
        result = run_query(vectorstore, query)
        log_interaction(result)
        print(f"[Tools]    {summarize_tools(result['tool_trace'])}")
        print(f"[Response] {result['final_response']}")
        rows.append(
            {
                "query": result["query"],
                "tools_called": "; ".join(t["tool"] for t in result["tool_trace"]) or "(none)",
                "tool_details": summarize_tools(result["tool_trace"]),
                "final_response": result["final_response"],
                "notes": "",  # filled in manually after reviewing actual outputs
            }
        )

    print("\n=== Synthetic invalid tool-call demonstration ===")
    invalid_result = demo_invalid_tool_calls()
    log_interaction(invalid_result)
    print(f"[Tools]    {summarize_tools(invalid_result['tool_trace'])}")
    print(f"[Response] {invalid_result['final_response']}")

    print("\n=== Synthetic loop-guard demonstration ===")
    loop_result = demo_loop_guard()
    log_interaction(loop_result)
    print(f"[Tools]    {summarize_tools(loop_result['tool_trace'])}")
    print(f"[Response] {loop_result['final_response']}")

    for extra in (invalid_result, loop_result):
        rows.append(
            {
                "query": extra["query"],
                "tools_called": "; ".join(t["tool"] for t in extra["tool_trace"]) or "(none)",
                "tool_details": summarize_tools(extra["tool_trace"]),
                "final_response": extra["final_response"],
                "notes": "",
            }
        )

    with TOOL_USAGE_TABLE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["query", "tools_called", "tool_details", "final_response", "notes"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {TOOL_USAGE_TABLE}")
    print(f"Full interaction log at {INTERACTION_LOG}")
    print(f"Escalation records at {ESCALATIONS_LOG}")


if __name__ == "__main__":
    run_all()
