"""
SupportSense AI — Phase 2: Basic Working Agent (Baseline)
===========================================================
E-commerce Customer Support Resolution Agent — Phase 2 deliverable.

This is a DELIBERATELY simple, rule/template-based agent with NO LLM and
NO retrieval. It routes user queries to a canned response using keyword
matching. Its purpose is to establish a documented baseline so later
phases (LLM integration, RAG, tools, memory) can be evaluated against it.

Run modes:
  1. Interactive:   python phase2_baseline_agent.py
  2. Batch/testing:  python phase2_baseline_agent.py --batch test_queries.txt
     (or just run with no args and it will also execute the built-in
      demo test set and write logs/interaction_log.jsonl)

Every turn (query, matched intent, confidence signal, response) is logged
to logs/interaction_log.jsonl for the Phase 2 evidence package.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "interaction_log.jsonl"

# ---------------------------------------------------------------------------
# Intent → (keywords, template response)
# Keyword matching is intentionally naive: simple substring checks on a
# lower-cased query. This is the mechanism whose limitations Phase 2 is
# meant to expose.
# ---------------------------------------------------------------------------
INTENT_RULES = [
    {
        "intent": "delivery_timeline",
        "keywords": ["delivery", "deliver", "how long", "arrive", "shipping time"],
        "response": (
            "Standard delivery typically takes 5-7 business days, and express "
            "delivery takes 2-3 business days, depending on your location."
        ),
    },
    {
        "intent": "shipping_charges",
        "keywords": ["shipping cost", "shipping charge", "shipping fee", "delivery charge"],
        "response": (
            "Shipping is free on orders above the promotional threshold; "
            "otherwise a flat shipping fee applies at checkout."
        ),
    },
    {
        "intent": "return_policy",
        "keywords": ["return", "send back", "send it back"],
        "response": (
            "Most items can be returned within 15 days of delivery, provided "
            "they are unused and in original packaging."
        ),
    },
    {
        "intent": "refund_timeline",
        "keywords": ["refund", "money back", "get my money"],
        "response": (
            "Refunds are typically processed within 5-7 business days after "
            "the returned item is received and inspected."
        ),
    },
    {
        "intent": "refund_eligibility",
        "keywords": ["eligible", "eligibility", "can i get a refund", "qualify for a refund"],
        "response": (
            "Refund eligibility generally depends on the return window and "
            "item condition. Please check the return policy for details."
        ),
    },
    {
        "intent": "damaged_product",
        "keywords": ["damaged", "broken", "defective"],
        "response": (
            "We're sorry to hear that. Please share your order details so we "
            "can arrange a replacement or refund for the damaged item."
        ),
    },
    {
        "intent": "cancellation",
        "keywords": ["cancel"],
        "response": (
            "Orders can usually be cancelled before they are shipped. Once "
            "shipped, you may need to use the return process instead."
        ),
    },
]

FALLBACK_RESPONSE = (
    "I'm not sure how to help with that yet. Let me connect you with a "
    "human support representative who can assist further."
)


def match_intent(query: str):
    """Naive keyword matcher. Returns (intent_name, response, matched)."""
    q = query.lower()
    for rule in INTENT_RULES:
        for kw in rule["keywords"]:
            if kw in q:
                return rule["intent"], rule["response"], True
    return "unmatched_fallback", FALLBACK_RESPONSE, False


def log_interaction(query: str, intent: str, matched: bool, response: str):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "matched_intent": intent,
        "keyword_match_found": matched,
        "response": response,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record


def handle_query(query: str, verbose: bool = True):
    intent, response, matched = match_intent(query)
    record = log_interaction(query, intent, matched, response)
    if verbose:
        print(f"\nUser: {query}")
        print(f"[intent: {intent} | keyword_match: {matched}]")
        print(f"Agent: {response}")
    return record


# ---------------------------------------------------------------------------
# Demo / evidence test set — includes normal cases AND the two deliberate
# failure cases used to demonstrate baseline limitations (see phase2_notes.md)
# ---------------------------------------------------------------------------
DEMO_QUERIES = [
    "How long does standard delivery take?",
    "What are the shipping charges?",
    "Can I return an item after 15 days?",
    "How long does it take to receive a refund?",
    "Can I cancel my order after it has been shipped?",
    "My product arrived damaged. What should I do?",
    # --- Limitation 1: paraphrase / no language understanding ---
    "my order hasn't shown up yet, its been a week",
    # --- Limitation 2: no nuance / no real reasoning over specifics ---
    "I bought this 20 days ago and only just opened it, is it still returnable?",
]


def run_demo():
    print("=== SupportSense AI — Phase 2 Baseline Agent Demo ===")
    for q in DEMO_QUERIES:
        handle_query(q)
    print(f"\nLogged {len(DEMO_QUERIES)} interactions to {LOG_FILE}")


def run_interactive():
    print("SupportSense AI (Phase 2 baseline). Type 'exit' to quit.\n")
    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not query:
            continue
        if query.lower() in {"exit", "quit"}:
            break
        intent, response, matched = match_intent(query)
        print(f"Agent: {response}\n")
        log_interaction(query, intent, matched, response)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        run_interactive()
    else:
        run_demo()
