# Build Note — draft

## Code vs model
| Step | Code or model | Why |
|---|---|---|
| CSV/schema checks | Deterministic code | Validation/lookup does not need language judgment |
| Cleaning | Deterministic code | Repeatable transformations |
| Bulk comment classification | Gemini 2.5 Flash-Lite | Messy English/Hinglish language mapping |
| Confidence routing | Deterministic code | Simple threshold comparison |
| Ambiguous-case review | Gemini 2.5 Flash | Higher-quality judgment only where needed |
| Counts/percentages/grouping | Deterministic code | Arithmetic should be deterministic |
| Final operational insight | Gemini 2.5 Flash | Concise language/judgment over supplied aggregate facts |

## Why the patterns exist
**Parallelization:** return comments are independent; processing batches sequentially adds avoidable latency.  
**Routing:** using the stronger model for every row wastes cost; using only the cheaper model risks lower-quality handling of ambiguous comments.

## Failure handling
Invalid files fail visibly. Structured-output failures are retried once; unresolved rows are marked Needs Review. Low-confidence second-pass results are never silently accepted.

## Cost line
Token usage is captured per model. Current official token prices are environment variables, then the app reports run cost, cost/1,000 rows, and an estimated weekly cost for the derived "Other" return volume. Final numbers must be filled after a live run.

## Unexpected breakage
**TBD after live Gemini integration. Do not fabricate this section.** Record the first meaningful thing that actually breaks during API/deployment testing, what caused it, and what changed.
