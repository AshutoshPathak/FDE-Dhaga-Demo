---
title: Dhaga Returns Intelligence
emoji: ⚡
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 6.29.1
python_version: "3.12"
app_file: app.py
pinned: false
short_description: Classify fashion return feedback.
---

# Dhaga Returns Intelligence

A small FDE-style MVP that converts messy fashion return comments into structured return reasons and product-level actions for Dhaga & Co.'s Category team.

## What it does

1. Uploads return data shaped like Dhaga's existing data.
2. Validates and cleans the CSV in deterministic Python.
3. Uses Gemini 3.5 Flash-Lite for bulk structured classification.
4. Routes low-confidence rows to Gemini 3.5 Flash.
5. Aggregates counts and percentages in Python, not in the model.
6. Uses the stronger model to turn aggregate facts into one concise operational insight.
7. Shows uncertain rows explicitly in **Needs Review** and exports the classified CSV.

Sub-reasons use a controlled vocabulary; body area retains location detail. This prevents equivalent phrases such as “tight chest” and “too tight” from fragmenting downstream analysis.

## Workflow patterns

- **Controlled batching**: independent batches are sent sequentially and paced below the configured per-model RPM limits.
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

The included `data/dhaga_returns_sample_300.csv` is the full app input. Use `data/dhaga_returns_smoke_10.csv` for a low-cost live smoke test before running all 300 rows. Use `data/dhaga_returns_strong_smoke_1.csv` only with `CONFIDENCE_THRESHOLD=0.99` to deliberately verify the STRONG route. The labeled file is only for evaluation and must not be passed to the model.

## Failure behaviour

- Missing required columns: visible error.
- Empty dataset: visible error.
- Invalid structured model output: schema validation fails visibly rather than being silently parsed.
- Low confidence after second pass: row is placed in **Needs Review**.
- Model/API failure: the affected row is visibly routed to **Needs Review**; the app never accepts a failed classification automatically.

## Models and temperatures

- Bulk classifier: `gemini-3.5-flash-lite`, temperature `0.1`.
- Ambiguous-case review: `gemini-3.5-flash`, temperature `0.1`.
- Aggregate business insight: `gemini-3.5-flash`, temperature `0.3`.

The model IDs and RPM limits are environment-configurable. By default, the app keeps below this project's observed free-tier limits of 15 FAST and 5 STRONG requests per minute.

## Evaluation

After a live run, download the app's **Classified Returns CSV** and compare it with the held-back labels:

```bash
python scripts/evaluate_demo.py /absolute/path/to/dhaga_classified_....csv
```

The report records primary-reason accuracy, sub-reason accuracy, STRONG escalation attempts, completed STRONG reviews, and human-review rate. Never upload `data/dhaga_returns_sample_300_labeled.csv` to the app; it is evaluation-only.

## Cost

Token usage is captured from Gemini responses. The supplied `.env.example` lists the current Standard paid-tier per-million-token prices for the configured models; confirm them against the official Gemini pricing page before the presentation. The app then calculates a paid-tier projection. A Free Tier run has no token charge, so present that separately from the production-cost projection.

## Hugging Face Spaces

Create a **Gradio** Space and upload the contents of this folder as the Space repository root: `app.py`, `requirements.txt`, `README.md`, `src/`, and the three app-input files in `data/` (`dhaga_returns_sample_300.csv`, `dhaga_returns_smoke_10.csv`, and `dhaga_returns_strong_smoke_1.csv`). The README front matter pins the tested Python 3.12 and Gradio 6.29.1 environment.

In the Space's **Settings → Variables and secrets**, add:

- Secret: `GEMINI_API_KEY` (never upload `.env`).
- Variables: `MODEL_FAST_INPUT_USD_PER_1M=0.30`, `MODEL_FAST_OUTPUT_USD_PER_1M=2.50`, `MODEL_STRONG_INPUT_USD_PER_1M=1.50`, and `MODEL_STRONG_OUTPUT_USD_PER_1M=9.00` for paid-tier cost projection.

Do not upload `.venv/`, `.env`, `data/dhaga_returns_sample_300_labeled.csv`, or generated `dhaga_classified_*.csv` files. After the Space builds, cold-test it in a browser/profile that did not build the app.

## Scope

This is deliberately an MVP. It does not issue refunds, modify size charts, update vendor systems, integrate with live Dhaga systems, or claim to predict future return rates. It demonstrates that unstructured return comments can be converted into actionable category-level evidence.
