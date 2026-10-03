# Step 8 Technical Spec

## Goal
Turn messy return comments into structured reasons, route uncertain cases for stronger review, aggregate patterns deterministically, and surface evidence-backed product actions.

## Input
`return_id, order_id, sku, product_name, category, vendor_id, size_ordered, payment_mode, city_tier, return_reason_selected, other_comment`

## Taxonomy
Primary: Fit; Fabric/Material; Quality; Colour; Expectation Mismatch; Damaged; Wrong Item; Delivery Related; Other.

Per-row structured output: `return_id, primary_reason, sub_reason, body_area, confidence, short_explanation`.

## Models
- Fast/bulk: `gemini-2.5-flash-lite`, temperature 0.1.
- Strong/review: `gemini-2.5-flash`, temperature 0.1.
- Strong/insight: `gemini-2.5-flash`, temperature 0.3.

## Patterns
1. Parallelization: classify independent batches concurrently.
2. Routing: confidence < 0.80 goes to the stronger model.

## Deterministic code
CSV/schema validation, threshold checks, grouping, counts, percentages, exports, cost arithmetic.

## Model work
Messy-language interpretation, taxonomy mapping, ambiguous-case judgment, final concise insight.

## Failures
Missing data, invalid schema, model/API errors, low confidence and disagreement must be visible. Never silently guess.
