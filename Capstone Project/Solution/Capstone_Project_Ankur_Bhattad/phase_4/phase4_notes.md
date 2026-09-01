# Phase 4 Notes — Knowledge & Retrieval (SupportSense AI)

## What was built
`phase4_rag_agent.py` replaces Phase 3's hardcoded "4 policies typed into the system prompt"
with real document grounding:

- **Knowledge base** (`knowledge_base/*.md`): 5 short markdown documents — `shipping_policy.md`,
  `returns_policy.md`, `refunds_policy.md`, `cancellations_policy.md`, `faq.md` — authored to keep
  the same core numbers Phase 3 used (15-day returns, 5-7 day standard delivery, etc.) but with
  real added detail Phase 3 never had: shipping charge thresholds, international shipping, a
  48-hour damaged/defective reporting process distinct from the standard return window, refund
  method options, and partial-order cancellation rules. `faq.md` deliberately does **not** mention
  gift wrapping, so a gift-wrapping question has no matching content anywhere in the knowledge
  base — this is the deliberate "missing information" test case.
- **Chunking**: `langchain_text_splitters.RecursiveCharacterTextSplitter`, chunk_size=500,
  chunk_overlap=50, applied per source file with the filename kept as chunk metadata for
  traceability.
- **Embeddings**: `langchain_openai.OpenAIEmbeddings` (`text-embedding-3-small`), pointed at the
  same Vocareum OpenAI-compatible endpoint `utils.py` configures for chat completions.
- **Vector store**: `langchain_community.vectorstores.Chroma`, built in-memory from
  `knowledge_base/` fresh on every run (no persisted DB directory — only the markdown source files
  need to be committed, keeping the phase reproducible).
- **Retrieval**: top-`k=3` similarity search per query, chunks injected into a RAG system prompt
  that explicitly instructs the model to answer only from the retrieved excerpts and to say so —
  not guess — when the excerpts don't actually answer the question.
- **Comparison**: every one of the 12 test queries (the same 10 used in Phase 3, plus 2 new
  queries — see below) is run twice per query: once against Phase 3's unmodified default prompt
  (`v2_policy_grounded`, no retrieval) and once with retrieval, logged side by side.

Two queries were added to the Phase 3 test set specifically to probe retrieval:
- *"What's the shipping charge if my order is only Rs 300?"* — answerable only from the knowledge
  base; Phase 3's prompt never stated a shipping-charge threshold at all.
- *"Do you offer gift wrapping on orders?"* — deliberately unanswerable from any document in the
  knowledge base, to test graceful missing-information handling.

## Running it
Requires network access to the Vocareum endpoint (same constraint as Phase 3):
```bash
python phase4_rag_agent.py
```
Writes:
- `logs/phase4_interaction_log.jsonl` — every (mode, query, retrieved chunks + scores, response)
- `logs/retrieval_comparison_table.csv` — Query → Retrieved sources → No-retrieval response →
  With-retrieval response → What improved (a copy is kept at `Solution/retrieval_comparison_table.csv`
  for the submission package)

## Results — actual observed behavior (from the real run, 24 logged responses)

**Retrieval fixed a genuine correctness bug, not just a style difference.** On *"My product
arrived damaged. What should I do?"*, the no-retrieval baseline (Phase 3's own chosen default
prompt) told the customer to return the item under the standard 15-day/unused/original-packaging
policy — the wrong policy. It had no damaged-product policy to draw on, so it silently reused the
closest thing it knew. With retrieval, the agent correctly cited the real 48-hour damaged/defective
reporting window and free replacement/refund choice, sourced from `returns_policy.md`. This is the
clearest root-cause fix in this phase: a policy-application error, not a hallucinated fact, and it
was invisible in Phase 3 because Phase 3 had no ground truth to be wrong about.

**Retrieval closed the "I don't know" gap left by Phase 3's stated policies.** On *"What are the
shipping charges?"* and *"What's the shipping charge if my order is only Rs 300?"*, the no-retrieval
baseline correctly refused to guess (a good outcome, but unhelpful — the information simply wasn't
in its prompt). With retrieval, the agent gave the exact ₹499 threshold and ₹49/₹99 charges from
`shipping_policy.md`, and correctly applied the threshold to the user's specific ₹300 order to
conclude a ₹49 charge applies — proving retrieval supports both fact recall *and* applying a
retrieved rule to case-specific numbers, the same reasoning gap Phase 2's baseline was originally
built to expose.

**The missing-information case behaved as intended.** For *"Do you offer gift wrapping on
orders?"*, the retriever still returned its top-3 chunks (`faq.md`, `shipping_policy.md`,
`faq.md`) as it always does — none of them mention gift wrapping. The agent's response was: *"I
don't have that information in the policy documents. Would you like me to escalate your question
to a human support representative?"* — it recognized the retrieved context didn't answer the
question and said so explicitly, rather than repurposing an unrelated chunk into a fabricated
answer. This is a meaningfully different (and better) failure mode than the no-retrieval baseline's
answer, which declined by claiming the topic was categorically out of scope — true by coincidence
here, but not actually grounded in anything retrieved.

**Where retrieval made no difference.** For facts Phase 3's hardcoded prompt already had right
(delivery windows, the 15-day return window, cancel-before-ship), both responses were correct and
nearly identical — retrieval mainly added sourced phrasing rather than changing the answer. This is
expected: retrieval's value shows up specifically where the old hardcoded prompt had gaps or wrong
defaults, not universally.

## Failure modes observed
- **Baseline policy misapplication (fixed by retrieval)** — the damaged-product case above: not a
  hallucinated number, but confidently applying the wrong policy in the absence of the right one.
- **Retriever always returns k results, even when nothing is relevant** — for the gift-wrapping
  query, none of the 3 retrieved chunks were actually relevant. The fix here is prompt-level (told
  explicitly to check whether the excerpts answer the question before using them), not
  retrieval-level; a similarity-score threshold could reject irrelevant chunks outright, but was
  intentionally left out of this phase so the "recognize irrelevant context" behavior — which will
  still be needed even with a threshold, since borderline-relevant chunks would still pass one — is
  the one actually being tested and evidenced here.
- **No eligibility reasoning/tools yet** — the agent can now correctly *state* the 48-hour damage
  window or the 15-day return rule, but still cannot look up an actual order's purchase date or
  invoke a real eligibility check; it depends on the user supplying dates in the query, same as
  Phase 3. That gap is what Phase 5 (tools) is for.

## Carried-forward limitation (motivates Phase 5)
The agent now answers from real, sourced documents instead of hardcoded prompt text or model
guesswork — but it still has no way to act on a specific customer's data (order date, order
status) or perform an eligibility calculation itself; it only reasons over whatever the user types
into the query. Phase 5 (tool usage) adds a refund-eligibility tool and similar business-rule tools
so the agent can compute an eligible/not-eligible decision rather than just stating the policy text.
