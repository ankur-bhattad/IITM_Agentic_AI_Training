# Phase 2 Notes — Baseline Agent Limitations (SupportSense AI)

## What was built
A keyword/template-based agent (`phase2_baseline_agent.py`) with no LLM and
no retrieval. It lower-cases the incoming query, checks it against a fixed
list of substring keywords per intent, and returns a static canned response.
Eight sample interactions (six "normal" + two deliberately adversarial) were
run and logged to `logs/interaction_log.jsonl`.

## Demonstrated limitations

### 1. No language understanding — only literal keyword matching
Query: *"my order hasn't shown up yet, its been a week"*
Result: `unmatched_fallback` — the agent has no "delivery" or "how long"
substring to latch onto, even though a human reads this instantly as a
delivery-timeline / delayed-order question. The agent can only recognize
phrasing it was explicitly coded for.

### 2. No reasoning over the specifics in the query
Query: *"I bought this 20 days ago and only just opened it, is it still
returnable?"*
Result: matched `return_policy` and returned the generic 15-day-window
template — despite the query stating a 20-day gap, which by the agent's
own stated policy should be **outside** the return window. The agent
cannot extract or reason about dates; it just pattern-matches to the
nearest intent and recites boilerplate, so it gives a misleadingly
reassuring answer here rather than the correct "no longer eligible"
response.

### 3. (Discovered while testing) Keyword collisions and rule-order fragility
Two additional real failures surfaced during the demo run, worth keeping
as evidence since they reinforce the same root cause:
- *"How long does it take to receive a refund?"* matched `delivery_timeline`
  instead of `refund_timeline`, because `"how long"` is a delivery keyword
  that gets checked before the refund rule, and substring matching doesn't
  care which intent the phrase "actually" belongs to.
- *"My product arrived damaged. What should I do?"* also matched
  `delivery_timeline`, because `"arrived"` contains the substring
  `"arrive"`, which is registered as a delivery keyword — a completely
  unintended collision that sent a damaged-product report into the wrong
  handler.

These aren't edge cases the design failed to anticipate — they're the
predictable consequence of matching on raw substrings with no notion of
intent priority, word boundaries, or meaning.

## Why this is insufficient for real users
- **Brittle to phrasing**: any paraphrase, typo, or indirect phrasing that
  doesn't contain the exact registered keyword falls through to a generic
  "let me escalate you" response, which doesn't scale to real customer
  language.
- **No grounding in actual policy documents**: responses are static text
  baked into the code, not retrieved from the shipping/return/refund
  policy documents referenced in the Phase 1 framing doc — so answers
  can't reflect real, current, or product-specific policy.
- **No reasoning or eligibility logic**: it cannot evaluate the
  specifics of a case (purchase date, item condition) against a policy,
  so it risks giving customers wrong or misleading eligibility answers.
- **Ordering-dependent and collision-prone**: correctness depends on the
  order rules are checked and on keywords never overlapping across
  intents — this doesn't scale as more intents are added.
- **No memory**: each query is handled in isolation with no conversation
  context.

## What this motivates for later phases
- **Phase 3 (LLM integration)**: replaces brittle keyword matching with
  actual language understanding, fixing limitations 1 and 3.
- **Phase 4 (Retrieval/RAG)**: grounds responses in the real shipping/
  return/refund policy documents instead of hardcoded templates,
  addressing the "no grounding" gap.
- **Phase 5 (Tools)**: a real refund-eligibility tool can evaluate purchase
  date vs. policy window instead of reciting a generic template,
  directly fixing limitation 2.
- **Phase 6 (Memory)**: adds conversation context across turns.

This baseline and its logged failures become the "before" evidence for
the before/after comparisons required in later phases and the Evaluation
Report.
