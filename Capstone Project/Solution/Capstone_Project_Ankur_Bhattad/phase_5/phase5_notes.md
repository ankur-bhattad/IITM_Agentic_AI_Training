# Phase 5 Notes — Tool Usage (SupportSense AI)

## What was built
`phase5_tool_agent.py` adds real OpenAI-style function/tool calling on top of Phase 4's
retrieval-grounded agent, so date-dependent decisions are computed deterministically in Python
instead of guessed by the LLM — the exact gap Phase 4's notes flagged as motivating this phase.

Three tools are defined, matching the Problem Framing Document's Section 15/16 architecture:
- **`refund_eligibility_tool(delivery_date, is_damaged)`** — computes eligible/not-eligible using
  `datetime.now()` for "today" (never trusted from the model) against the 15-day standard window
  or the 48-hour damaged-product window from `returns_policy.md`. The model's only job is to
  extract/convert the delivery date (including relative phrasing like "20 days ago") into
  `YYYY-MM-DD`; the actual day-count and eligibility decision is Python arithmetic, not an LLM
  guess.
- **`delivery_estimate_tool(order_date, shipping_method)`** — computes an estimated delivery date
  range using real business-day arithmetic (Sundays excluded, per `shipping_policy.md`), and
  rejects any `shipping_method` other than `standard`/`express`.
- **`escalate_to_human_tool(reason_category, summary)`** — the only tool that "acts": it writes a
  non-PII escalation record (`logs/escalations.jsonl` — category + truncated, non-identifying
  summary only) and returns a mock ticket id. No tool in this phase modifies an order, processes a
  payment, or looks up live order status — consistent with the Problem Framing Document's
  Out-of-Scope list.

Every tool returns a structured `{"status": "ok"|"error", ...}` result rather than raising, so bad
input is a normal, recoverable tool result the model can react to. The agent loop retrieves policy
context exactly as in Phase 4, then calls the model with `tools=` and iterates on any tool calls
(executing them, feeding results back) up to `MAX_TOOL_ITERATIONS = 4` before forcing an
escalation — the loop-prevention guardrail.

## Running it
Requires network access to the Vocareum endpoint (same constraint as Phases 3-4):
```bash
python phase5_tool_agent.py
```
Writes:
- `logs/phase5_interaction_log.jsonl` — every query's full tool-call trace
- `logs/tool_usage_table.csv` — Query → Tools called → Tool details → Final response → Notes
  (a copy is kept at `Solution/tool_usage_table.csv` for the submission package)
- `logs/escalations.jsonl` — non-PII escalation records

## Results — actual observed behavior (from the real run, 9 logged rows)

**Correct tool selection, demonstrated three ways.** *"My item was delivered on 2026-08-28... is
that possible?"* correctly triggered `refund_eligibility_tool` → `eligible: True` (4 days since
delivery). *"I bought this 20 days ago and only just opened it, is it still returnable?"* — the
original Phase 2 baseline's signature failure case — now correctly converts the relative "20 days
ago" phrasing into an absolute date (2026-08-12) using the current date stated in the system
prompt, calls the tool, and gets the deterministic and correct `eligible: False` (20 > 15 days).
*"I ordered on 2026-08-25 and chose express shipping, when will it arrive?"* correctly triggered
`delivery_estimate_tool` and returned an exact date range (2026-08-27 to 2026-08-28) computed by
real business-day arithmetic, not LLM estimation. *"This is ridiculous, refund me now or I'm
reporting you!"* correctly triggered `escalate_to_human_tool` with a non-identifying summary — no
refund was processed, honoring the out-of-scope constraint.

**Correct tool *non*-selection was just as important to verify.** *"How long does standard
delivery take?"* (a general policy question) and *"My product arrived damaged... what should I
do?"* (a procedural question, not an eligibility determination) were both answered directly from
retrieved policy context with no tool call — proving the model isn't reaching for a tool
reflexively when retrieval alone already answers the question correctly.

**The "failed tool call" requirement needed a forced demonstration.** The organic query designed
to trigger an invalid `delivery_estimate_tool` call — *"...can you tell me when it'll arrive via
drone delivery?"* — didn't actually produce a failed tool call: the model noticed from the
retrieved shipping-policy excerpts that only standard/express are valid methods and asked for
clarification *without* calling the tool at all. That's a reasonable model behavior, but it means
the tool's own error-handling path was never exercised by a live call. To get real evidence of the
required "failed or incorrect tool call," `demo_invalid_tool_calls()` invokes
`delivery_estimate_tool(order_date="2026-08-25", shipping_method="drone")` and
`refund_eligibility_tool(delivery_date="last Tuesday")` directly. Both returned a clean
`{"status": "error", "reason": "..."}` instead of raising an exception or returning a guessed
result — proving the guardrail holds at the tool layer regardless of whether the model chooses to
call it with bad input.

**Loop-prevention was verified the same way, for the same reason.** Coaxing gpt-4o-mini into an
organic infinite tool-calling loop isn't reliably reproducible test-to-test. `demo_loop_guard()`
instead directly drives the iteration-counting logic with a simulated tool that always reports
"unresolved": it runs to `MAX_TOOL_ITERATIONS + 1` (5) attempts, at which point the cap engages and
forces `escalate_to_human_tool(reason_category="loop_guard", ...)` — logged with its own ticket id
— instead of continuing indefinitely.

## Failure modes / limitations observed
- **Day-granularity approximation of the 48-hour damaged-product window** — `refund_eligibility_tool`
  compares whole days, not hours, so an item reported on day 3 at 1am (which might still be within
  48 hours) would incorrectly read as ineligible. Acceptable for this phase's demo scope; a
  production version would track delivery timestamp, not just date.
- **No public-holiday calendar** — `delivery_estimate_tool` only excludes Sundays (per
  `shipping_policy.md`'s stated rule), not public holidays, since no holiday calendar was defined
  for this project. Documented as a known simplification, not a hidden bug.
- **The model can route around a tool's guardrail by simply not calling it** — as seen with the
  drone-delivery query. This is not unsafe here (the model's own answer was correct), but it means
  tool-level input validation alone isn't sufficient evidence of guardrail coverage; the direct
  `demo_invalid_tool_calls()` test exists specifically to close that gap.

## Carried-forward limitation (motivates Phase 6)
Every query in this phase is still handled independently — there is no conversation memory, so a
follow-up like "what about if it's damaged instead?" after an eligibility answer would require the
user to restate the delivery date from scratch. Phase 6 (planning, memory & context) adds
short/long-term memory so the agent can carry details (dates, prior tool results) across turns of
the same conversation instead of re-deriving them every time.
