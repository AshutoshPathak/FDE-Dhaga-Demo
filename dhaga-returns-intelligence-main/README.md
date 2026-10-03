# Dhaga Returns Intelligence

A small FDE-style MVP that converts messy fashion return comments into structured return reasons and product-level actions for Dhaga & Co.'s Category team.

## What it does

1. Uploads return data shaped like Dhaga's existing data.
2. Validates and cleans the CSV in deterministic Python.
3. Uses Gemini 2.5 Flash-Lite for bulk structured classification.
4. Routes low-confidence rows to Gemini 2.5 Flash.
5. Aggregates counts and percentages in Python, not in the model.
6. Uses the stronger model to turn aggregate facts into one concise operational insight.
7. Shows uncertain rows explicitly in **Needs Review** and exports the classified CSV.

## Workflow patterns

- **Parallelization**: independent batches are classified concurrently to reduce latency.
- **Routing**: only low-confidence cases are sent to the stronger model, reducing unnecessary cost.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add GEMINI_API_KEY to .env
python app.py
```

Open `http://localhost:7860`.

Without `GEMINI_API_KEY`, the UI opens in a clearly marked demo-preview mode using deterministic heuristics. This is only for frontend testing. The final project demo should use the Gemini workflow.

## Input columns

Required: `return_id`, `order_id`, `sku`, `product_name`, `category`, `size_ordered`, `return_reason_selected`, `other_comment`.

The included `data/dhaga_returns_sample_300.csv` is the app input. The labeled file is only for evaluation and must not be passed to the model.

## Failure behaviour

- Missing required columns: visible error.
- Empty dataset: visible error.
- Invalid structured model output: schema validation fails visibly rather than being silently parsed.
- Low confidence after second pass: row is placed in **Needs Review**.
- Model/API failure: visible error; no silent fallback in live mode.

## Models and temperatures

- Bulk classifier: `gemini-2.5-flash-lite`, temperature `0.1`.
- Ambiguous-case review: `gemini-2.5-flash`, temperature `0.1`.
- Aggregate business insight: `gemini-2.5-flash`, temperature `0.3`.

The model IDs are environment-configurable.

## Cost

Token usage is captured from Gemini responses. Fill the four pricing variables in `.env` from the current official Gemini pricing page before the presentation. The app will then calculate run cost. Pricing is deliberately not hard-coded so it cannot silently go stale.

## Hugging Face Spaces

Create a Gradio Space, upload this repository, and add `GEMINI_API_KEY` as a Space Secret.

## Scope

This is deliberately an MVP. It does not issue refunds, modify size charts, update vendor systems, integrate with live Dhaga systems, or claim to predict future return rates. It demonstrates that unstructured return comments can be converted into actionable category-level evidence.
