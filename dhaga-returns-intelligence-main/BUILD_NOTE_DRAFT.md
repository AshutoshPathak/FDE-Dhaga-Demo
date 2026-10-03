# Build Note — Dhaga Returns Intelligence

## What the MVP does

The app turns English/Hinglish fashion-return comments into a controlled reason, sub-reason, body area, confidence score, and review status. It aggregates the results by SKU and category, flags uncertain rows for human review, and exports the enriched CSV.

## Code versus model

| Step | Implementation | Why |
|---|---|---|
| CSV validation and cleaning | Deterministic Python | Required columns, empty values, and row limits are predictable rules. |
| Bulk classification | Gemini 3.5 Flash-Lite, temperature 0.1 | Interprets unstructured English/Hinglish return feedback at low cost. |
| Confidence routing and request pacing | Deterministic Python | Threshold comparison and provider-limit handling should be repeatable. |
| Ambiguous-case review | Gemini 3.5 Flash, temperature 0.1 | A distinct, stronger second pass is used only when FAST confidence is below the chosen threshold. |
| Aggregation, review queue, and export | Deterministic Python | Counts, percentages, filters, and files must be auditable. |
| Executive recommendation | Gemini 3.5 Flash, temperature 0.3 | Turns supplied aggregate facts into concise category-language guidance. |

The model receives a Pydantic structured-output schema. `sub_reason` is a controlled vocabulary and `body_area` stores the specific location; for example, `Too tight` plus `Chest`, rather than free-form variants such as “Chest tight.”

## Purposeful patterns

**Controlled batching and pacing.** The 300-row input is split into 50-row FAST batches, processed sequentially, and paced below the configured per-model request-per-minute limits. This avoids free-tier request bursts.

**Confidence routing.** FAST accepts high-confidence rows. Rows below the user-controlled threshold go to the distinct STRONG model. If either model is unavailable or the second pass remains below threshold, the row is visibly sent to `Needs Review` rather than being silently accepted.

## Live evaluation

The 300-row input was evaluated against the held-back labeled CSV. The first live run established a baseline; it showed that free-form sub-reason wording hurt exact-match scoring. The second run constrained sub-reasons to the controlled vocabulary.

| Run | Primary accuracy | Sub-reason accuracy | STRONG review completed | Human review |
|---|---:|---:|---:|---:|
| V1 baseline | 83.3% | 20.3% | 0.7% | 0.7% |
| V2 controlled vocabulary | 92.3% | 86.0% | 2.7% | 2.7% |

V2 is a post-tuning validation on the same labeled set, not an untouched blind holdout. The evaluation also records a 26.3% label-based expected-escalation rate; this is a comparison reference, not routing accuracy.

## Genuine unexpected breakage and fix

Early live runs reached Gemini free-tier limits and intermittent service pressure: Google AI Studio showed FAST at 16/15 RPM and the original STRONG model at 7/5 RPM, producing Gemini 429 responses; a separate STRONG request also received a 503 high-demand response. This was not an invalid API key.

The fix was to pace requests with a 10% safety margin, share pacing across separate UI runs, stop automatic retries after a 429, make 429/503 states explicit in the Review Queue, and use the validated `gemini-3.5-flash` STRONG model. Successful second-stage routing was then verified in the UI with `model_used: gemini-3.5-flash`.

## Cost and scope

The successful 300-row V2 run used 22,852 FAST input tokens, 23,013 FAST output tokens, 3,623 STRONG input tokens, and 903 STRONG output tokens. Using the current [Gemini Standard paid-tier prices](https://ai.google.dev/gemini-api/docs/pricing)—$0.30/$2.50 per million FAST input/output tokens and $1.50/$9.00 for STRONG—the projected cost is **$0.077950 per 300-row run**, or **$0.259832 per 1,000 rows**.

For a clearly labelled Dhaga-scale estimate, the case implies 6,547 “Other” returns per week (48,000 orders/week × 31% returns × 44% Other). At the observed token mix, that projects to **$1.701120 per week**. This is a paid-tier Standard projection; the observed run used the Free Tier and therefore incurred no token charge.

This is a decision-support MVP. It does not issue refunds, alter product data, or replace category review.
