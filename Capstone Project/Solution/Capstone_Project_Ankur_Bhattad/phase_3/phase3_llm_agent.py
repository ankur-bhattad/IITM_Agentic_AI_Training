"""
SupportSense AI — Phase 3: Make the Agent Smarter (LLM Integration)
=====================================================================
Replaces the Phase 2 keyword/template router with an actual LLM call
(via the Vocareum-hosted OpenAI-compatible endpoint configured in
utils.py), and evaluates 3 prompt strategies against the SAME test set
used in Phase 2 — including the two queries that broke the baseline.

No retrieval / tools / memory yet (those are Phases 4-6). The agent
answers from the LLM's own knowledge plus the system prompt's stated
policies — this is intentional: it lets Phase 4's retrieval-grounding
be evaluated as a clear improvement later.

Run:
    python phase3_llm_agent.py

Requires `utils.py` (sets OPENAI_API_BASE / OPENAI_API_KEY) to be in
the same directory or on PYTHONPATH. Needs network access to the
Vocareum endpoint — run this inside your Vocareum notebook/environment,
not in an offline sandbox.

Outputs:
    logs/phase3_interaction_log.jsonl   — every (variant, query, response)
    logs/prompt_comparison_table.csv    — Prompt -> Query -> Output -> Notes
"""

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import utils  # noqa: F401  (sets OPENAI_API_BASE / OPENAI_API_KEY as a side effect)
from openai import OpenAI

MODEL = os.environ.get("SUPPORTSENSE_MODEL", "gpt-4o-mini")

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
INTERACTION_LOG = LOG_DIR / "phase3_interaction_log.jsonl"
COMPARISON_TABLE = LOG_DIR / "prompt_comparison_table.csv"

client = OpenAI(
    base_url=os.environ["OPENAI_API_BASE"],
    api_key=os.environ["OPENAI_API_KEY"],
)

# ---------------------------------------------------------------------------
# Prompt variants
# ---------------------------------------------------------------------------

PROMPT_V1_NAIVE = """You are a customer support assistant for an e-commerce
company. Answer the user's question."""

PROMPT_V2_POLICY_GROUNDED = """You are SupportSense, an e-commerce customer
support agent. Follow these rules strictly:

- Only answer questions about shipping, delivery, returns, refunds, and
  cancellations.
- Base your answers on these general policies unless the user gives
  specifics that change the answer:
  * Standard delivery: 5-7 business days. Express: 2-3 business days.
  * Returns: accepted within 15 days of delivery, unused, original packaging.
  * Refunds: processed within 5-7 business days after the returned item
    is received and inspected.
  * Cancellations: allowed before an order ships; after shipping, use the
    return process instead.
- If the user's question is ambiguous or you are not confident in the
  answer, ask a clarifying question instead of guessing.
- If the request is outside this scope (e.g. processing a refund, tracking
  a live order, changing payment details, or anything abusive/unsafe),
  politely decline and say you'll escalate to a human support
  representative.
- Never invent a policy that isn't listed above."""

PROMPT_V3_POLICY_GROUNDED_STRICT_FORMAT = PROMPT_V2_POLICY_GROUNDED + """

Additionally:
- When a user gives specific details (e.g. a number of days since
  purchase), explicitly apply the relevant policy to those details and
  state the conclusion (eligible / not eligible / cannot determine) rather
  than repeating the general policy text alone.
- Keep responses to 2-4 sentences.
- If you are escalating or declining, say so in the first sentence.
- Never claim certainty about information you were not given (e.g. do not
  claim to know the user's actual order or purchase date if they didn't
  state one)."""

PROMPT_VARIANTS = {
    "v1_naive": PROMPT_V1_NAIVE,
    "v2_policy_grounded": PROMPT_V2_POLICY_GROUNDED,
    "v3_policy_grounded_strict_format": PROMPT_V3_POLICY_GROUNDED_STRICT_FORMAT,
}

# ---------------------------------------------------------------------------
# Test set — same core set as Phase 2, plus 2 safety-probing queries to
# test refusal/escalation behaviour that Phase 2 couldn't demonstrate at all.
# ---------------------------------------------------------------------------

TEST_QUERIES = [
    "How long does standard delivery take?",
    "What are the shipping charges?",
    "Can I return an item after 15 days?",
    "How long does it take to receive a refund?",
    "Can I cancel my order after it has been shipped?",
    "My product arrived damaged. What should I do?",
    "my order hasn't shown up yet, its been a week",
    "I bought this 20 days ago and only just opened it, is it still returnable?",
    "Can you just process a refund for me right now?",         # out-of-scope / transactional
    "This is ridiculous, refund me now or I'm reporting you!",  # abusive / needs graceful handling
]


def call_llm(system_prompt: str, user_query: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


def log_interaction(variant: str, query: str, response: str):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_variant": variant,
        "query": query,
        "response": response,
    }
    with INTERACTION_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def run_comparison():
    rows = []
    for variant_name, system_prompt in PROMPT_VARIANTS.items():
        print(f"\n=== Variant: {variant_name} ===")
        for query in TEST_QUERIES:
            try:
                response = call_llm(system_prompt, query)
            except Exception as e:  # noqa: BLE001 — surface API errors into the table
                response = f"[ERROR calling LLM: {e}]"
            log_interaction(variant_name, query, response)
            print(f"\nQ: {query}\nA: {response}")
            rows.append(
                {
                    "prompt_variant": variant_name,
                    "query": query,
                    "response": response,
                    "what_improved_or_worsened": "",  # fill in manually after review
                }
            )

    with COMPARISON_TABLE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["prompt_variant", "query", "response", "what_improved_or_worsened"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {COMPARISON_TABLE}")
    print(f"Full interaction log at {INTERACTION_LOG}")


if __name__ == "__main__":
    run_comparison()
