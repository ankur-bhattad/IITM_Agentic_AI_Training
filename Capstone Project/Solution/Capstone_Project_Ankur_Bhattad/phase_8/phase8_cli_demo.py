"""
SupportSense AI — Phase 8: Deployment Readiness (offline evidence script)
=============================================================================
Generates real evidence for Phase 8 without needing the FastAPI server
running: real conversations through `phase8_agent_core.run_turn` (capturing
real latency numbers from the live Vocareum endpoint), plus two forced
failure-injection demos proving graceful failure handling -- same
synthetic/forced-demonstration pattern used in Phases 5-7
(demo_invalid_tool_calls, demo_loop_guard, demo_short_term_trimming),
clearly labeled [synthetic] wherever the failure was deliberately induced
rather than occurring organically.

Run:
    python phase8_cli_demo.py

Outputs:
    logs/phase8_interaction_log.jsonl   -- full per-turn transcripts + timing
    logs/trace_log.jsonl                -- latency records (shared w/ app_api.py)
    logs/error_log.jsonl                -- captured errors (shared w/ app_api.py)
    logs/deployment_readiness_table.csv -- scenario -> request -> status -> latency -> notes
"""

import csv
import json
from datetime import datetime, timezone

import phase8_agent_core as core

INTERACTION_LOG = core.LOG_DIR / "phase8_interaction_log.jsonl"
TABLE = core.LOG_DIR / "deployment_readiness_table.csv"

# ---------------------------------------------------------------------------
# Real conversations (live Vocareum calls) -- exercised for real latency data
# ---------------------------------------------------------------------------

CONVERSATIONS = {
    "normal_A": [
        "My item was delivered on 2026-08-28, is it eligible for return?",
        "What if it had arrived damaged instead?",
    ],
    "normal_B": [
        "I ordered on 2026-08-25 and chose express shipping, when will it arrive?",
        "This is ridiculous, refund me now or I'm reporting you!",
    ],
}


def log_interaction(record: dict):
    with INTERACTION_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), **record}) + "\n")


def summarize_tools(tool_trace):
    if not tool_trace:
        return "(none)"
    return "; ".join(f"{t['tool']}({t['arguments']}) -> {t['result']}" for t in tool_trace)


def run_normal_conversations(vectorstore, rows):
    for convo_name, turns in CONVERSATIONS.items():
        print(f"\n########## Conversation: {convo_name} ##########")
        conversation = core.Conversation(convo_name)
        for user_message in turns:
            print(f"\n--- Turn {conversation.turn_index + 1} (user): {user_message}")
            result = core.run_turn(conversation, vectorstore, user_message)
            log_interaction(result)
            print(f"[Status]   {result['status']}")
            print(f"[Timing]   {result['timing']}")
            print(f"[Tools]    {summarize_tools(result['tool_trace'])}")
            print(f"[Response] {result['response']}")
            rows.append({
                "scenario": convo_name, "request": user_message, "status": result["status"],
                "latency_ms": result["timing"]["total_ms"], "error_handled": "no",
                "notes": f"tools={summarize_tools(result['tool_trace'])}",
            })


# ---------------------------------------------------------------------------
# [synthetic] Forced failure demos
# ---------------------------------------------------------------------------


class _BrokenVectorstore:
    """Stands in for a vectorstore whose backing service is unreachable."""
    def similarity_search_with_score(self, query, k=3):
        raise ConnectionError("simulated: vector database unreachable")


def demo_forced_retrieval_failure(rows):
    print("\n########## [synthetic] Forced retrieval failure ##########")
    conversation = core.Conversation("synthetic_retrieval_failure")
    user_message = "What is your standard return window?"
    result = core.run_turn(conversation, _BrokenVectorstore(), user_message)
    log_interaction({**result, "synthetic": True, "injected_failure": "retrieval"})
    print(f"[Status]   {result['status']}")
    print(f"[Response] {result['response']}")
    assert result["status"] == "degraded_ok", "expected retrieval failure to degrade gracefully, not crash"
    assert "escalat" in result["response"].lower(), "expected fallback response to mention escalation"
    rows.append({
        "scenario": "synthetic_retrieval_failure", "request": user_message, "status": result["status"],
        "latency_ms": result["timing"]["total_ms"], "error_handled": "yes",
        "notes": "[synthetic] vectorstore forced to raise ConnectionError -> retry -> AgentUnavailableError -> forced escalation + safe fallback response, no crash",
    })


def demo_forced_llm_failure(vectorstore, rows):
    print("\n########## [synthetic] Forced LLM-call failure ##########")
    conversation = core.Conversation("synthetic_llm_failure")
    user_message = "How long does standard delivery take?"

    original_create = core.client.chat.completions.create

    def _always_fail(*args, **kwargs):
        raise TimeoutError("simulated: Vocareum endpoint timed out")

    core.client.chat.completions.create = _always_fail
    try:
        result = core.run_turn(conversation, vectorstore, user_message)
    finally:
        core.client.chat.completions.create = original_create  # restore real client regardless of outcome

    log_interaction({**result, "synthetic": True, "injected_failure": "llm_call"})
    print(f"[Status]   {result['status']}")
    print(f"[Response] {result['response']}")
    assert result["status"] == "degraded_ok", "expected LLM failure to degrade gracefully, not crash"
    assert "escalat" in result["response"].lower(), "expected fallback response to mention escalation"
    rows.append({
        "scenario": "synthetic_llm_failure", "request": user_message, "status": result["status"],
        "latency_ms": result["timing"]["total_ms"], "error_handled": "yes",
        "notes": "[synthetic] LLM client forced to raise TimeoutError on every call -> retry -> AgentUnavailableError -> forced escalation + safe fallback response, no crash",
    })

    # Prove the client actually works again post-restore (real live call).
    followup = core.run_turn(conversation, vectorstore, "Never mind, thanks.")
    log_interaction(followup)
    assert followup["status"] == "ok", "expected the client to recover after restoring the real completions.create"
    rows.append({
        "scenario": "synthetic_llm_failure_recovery", "request": "Never mind, thanks.", "status": followup["status"],
        "latency_ms": followup["timing"]["total_ms"], "error_handled": "no",
        "notes": "real client restored after the forced-failure demo; confirms the failure was isolated to the injected call, not a lingering broken state",
    })


def main():
    vectorstore = core.build_vectorstore()
    rows = []

    run_normal_conversations(vectorstore, rows)
    demo_forced_retrieval_failure(rows)
    demo_forced_llm_failure(vectorstore, rows)

    with TABLE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["scenario", "request", "status", "latency_ms", "error_handled", "notes"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {TABLE}")
    print(f"Full interaction log at {INTERACTION_LOG}")
    print(f"Trace log at {core.TRACE_LOG}")
    print(f"Error log at {core.ERROR_LOG}")


if __name__ == "__main__":
    main()
