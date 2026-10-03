from __future__ import annotations
import json, tempfile
from pathlib import Path
import pandas as pd
import gradio as gr

from src.config import SETTINGS
from src.data import (
    validate_input,
    clean_input,
    merge_predictions,
    overview_metrics,
    reason_breakdown,
    product_summary
)
from src.demo_classifier import classify_dataframe
from src.costing import cost_summary
from src.ui.components import (
    render_header,
    render_hero_section,
    render_file_summary,
    render_default_file_summary,
    render_metrics,
    render_default_metrics,
    render_reason_bars,
    render_release_cards,
    render_default_release_cards,
    render_executive_insight,
    render_default_insight,
    render_tab_banner
)

BASE = Path(__file__).parents[2]
SAMPLE = BASE / "data" / "dhaga_returns_sample_300.csv"
CSS_PATH = Path(__file__).parent / "styles.css"

def get_css() -> str:
    if CSS_PATH.exists():
        return CSS_PATH.read_text(encoding="utf-8")
    return ""

def load_dataset(file_path: str | None) -> tuple[pd.DataFrame, str]:
    path = file_path if file_path else str(SAMPLE)
    df = pd.read_csv(path)
    ok, msg = validate_input(df)
    if not ok:
        raise gr.Error(msg)
    df = clean_input(df)
    summary_html = render_file_summary(path, df, msg)
    return df, summary_html

def generate_demo_insight(result: pd.DataFrame) -> dict:
    ps = product_summary(result)
    if ps.empty:
        return {
            "headline": "No clear pattern yet",
            "recommended_action": "Review the rows marked Needs Review.",
            "evidence": "Insufficient confidently classified records."
        }
    top = ps.iloc[0]
    subset = result[(result['sku'] == top['sku']) & (result['review_status'] != 'Needs Review')]
    issue = subset['ai_sub_reason'].value_counts().head(2)
    evidence = ", ".join([f"{k}: {v}" for k, v in issue.items()])
    return {
        "headline": f"{top['sku']} shows the strongest fit concentration in this run.",
        "recommended_action": f"Review the size chart and vendor measurements for {top['sku']} before the next restock.",
        "evidence": evidence or f"{len(subset)} classified returns."
    }

def execute_analysis(df: pd.DataFrame, confidence_threshold: float = SETTINGS.confidence_threshold, progress=gr.Progress()):
    if df is None or len(df) == 0:
        raise gr.Error("Upload a valid returns CSV or load the sample dataset first.")
    
    ok, msg = validate_input(df)
    if not ok:
        raise gr.Error(msg)
    
    confidence_threshold = float(confidence_threshold)
    if not 0.50 <= confidence_threshold <= 0.99:
        raise gr.Error("Choose a confidence threshold between 50% and 99%.")

    df = clean_input(df)
    progress(0.05, desc="Validating dataset integrity")
    
    live = bool(SETTINGS.api_key)
    usage = None
    
    if live:
        try:
            from src.gemini_client import GeminiWorkflow
            wf = GeminiWorkflow(confidence_threshold=confidence_threshold)
            preds = wf.classify(df, progress=progress)
            usage = wf.usage
        except Exception as e:
            raise gr.Error(f"Gemini workflow failed: {type(e).__name__}: {e}")
    else:
        progress(0.35, desc="Classifying comments via heuristic engine")
        preds = classify_dataframe(df, threshold=confidence_threshold)
        
    result = merge_predictions(df, preds)
    progress(0.80, desc="Aggregating SKU and category patterns")
    
    metrics = overview_metrics(result)
    reasons = reason_breakdown(result)
    ps = product_summary(result)
    
    review_cols = ["return_id", "sku", "other_comment", "ai_primary_reason", "ai_sub_reason", "ai_confidence", "ai_explanation", "model_used"]
    review = result[result['review_status'] == 'Needs Review'][review_cols].copy()
    
    display_cols = ["return_id", "sku", "product_name", "size_ordered", "other_comment", "ai_primary_reason", "ai_sub_reason", "ai_body_area", "ai_confidence", "review_status", "routing_stage", "model_used"]
    display = result[display_cols].copy()
    
    if live:
        summary_payload = {
            "top_products": ps.head(5).to_dict('records'),
            "reason_breakdown": reasons.head(8).to_dict('records')
        }
        try:
            progress(0.90, desc="Generating the operational insight (safely paced for Gemini)")
            insight = wf.insight(summary_payload)
        except Exception:
            insight = generate_demo_insight(result)
        costs = cost_summary(usage, len(df))
        tech = {
            "mode": "Live Gemini",
            "fast_model": SETTINGS.model_fast,
            "strong_model": SETTINGS.model_strong,
            "confidence_threshold": confidence_threshold,
            "request_pacing": {
                "fast_rpm_limit": SETTINGS.fast_requests_per_minute,
                "strong_rpm_limit": SETTINGS.strong_requests_per_minute,
                "safety_margin": "10%",
            },
            "usage_and_cost": costs
        }
    else:
        insight = generate_demo_insight(result)
        tech = {
            "mode": "Demo preview - heuristic classifier (set GEMINI_API_KEY for live LLM routing)",
            "fast_model": SETTINGS.model_fast,
            "strong_model": SETTINGS.model_strong,
            "confidence_threshold": confidence_threshold,
            "request_pacing": {
                "fast_rpm_limit": SETTINGS.fast_requests_per_minute,
                "strong_rpm_limit": SETTINGS.strong_requests_per_minute,
                "safety_margin": "10%",
            },
            "usage_and_cost": "Unavailable in demo mode"
        }
        
    insight_html = render_executive_insight(insight)
    reason_bars_html = render_reason_bars(reasons)
    release_cards_html = render_release_cards(ps, result_df=result)
    metrics_html = render_metrics(metrics, threshold=confidence_threshold)
    
    fd = tempfile.NamedTemporaryFile(prefix="dhaga_classified_", suffix=".csv", delete=False)
    result.to_csv(fd.name, index=False)
    fd.close()
    
    progress(1.0, desc="Analysis complete")
    return (
        result,
        metrics_html,
        release_cards_html,
        reason_bars_html,
        reasons,
        display,
        review,
        ps,
        insight_html,
        json.dumps(tech, indent=2),
        fd.name
    )

def create_dhaga_app() -> tuple[gr.Blocks, str, gr.Theme]:
    css = get_css()
    theme = gr.themes.Soft(
        primary_hue=gr.themes.colors.indigo,
        secondary_hue=gr.themes.colors.purple,
        neutral_hue=gr.themes.colors.slate,
        font=[gr.themes.GoogleFont("Plus Jakarta Sans"), "system-ui", "sans-serif"]
    )
    
    with gr.Blocks(title="Dhaga Returns Intelligence") as demo:
        # 1. Top Navbar (Salesforce Debugger Style)
        header = gr.HTML(render_header(
            api_key=SETTINGS.api_key,
            fast_model=SETTINGS.model_fast,
            strong_model=SETTINGS.model_strong,
            threshold=SETTINGS.confidence_threshold
        ))
        
        # 2. Hero Section (Updates & Release Notes Style)
        gr.HTML(render_hero_section(SETTINGS.model_fast, SETTINGS.model_strong))
        
        state_input = gr.State()
        state_result = gr.State()

        # 3. Control Hub & Dataset Ingestion
        with gr.Group(elem_classes=["control-hub-dark"]):
            gr.HTML('<div class="hub-header-title"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg> Dataset Ingestion &amp; Pipeline Control Hub</div>')
            with gr.Row():
                with gr.Column(scale=5):
                    upload = gr.File(label="Upload Returns Dataset (.csv)", file_types=[".csv"], type="filepath")
                with gr.Column(scale=3):
                    sample_btn = gr.Button("📂 Load Sample Dataset (300 rows)", variant="secondary", elem_classes=["btn-secondary-dark"])
                    run_btn = gr.Button("⚡ Run Returns Analysis", variant="primary", elem_classes=["btn-primary-gradient"])
            threshold_control = gr.Slider(
                minimum=0.50,
                maximum=0.99,
                value=SETTINGS.confidence_threshold,
                step=0.01,
                label="Review confidence threshold",
                info="Rows below this score are reviewed by the STRONG model; unresolved rows remain in Needs Review.",
            )
            file_summary = gr.HTML(render_default_file_summary())

        # 4. Main Navigation Tabs (High Contrast Dark Segmented Tabs)
        with gr.Tabs(elem_classes=["tabs"]):
            # Tab 1: Updates & Intelligence Overview
            with gr.Tab("Updates & Overview"):
                metrics_html = gr.HTML(render_default_metrics())
                gr.Markdown("### 🚀 Critical Defect & Release Intelligence")
                release_cards_display = gr.HTML(render_default_release_cards())
                
                with gr.Row():
                    with gr.Column(scale=5):
                        reason_bars_display = gr.HTML("")
                    with gr.Column(scale=5):
                        reasons_table = gr.Dataframe(headers=["Reason", "Returns", "Percent"], interactive=False, wrap=True)

            # Tab 2: Returns Explorer
            with gr.Tab("Returns Explorer"):
                gr.HTML(render_tab_banner("🔍", "Enriched Returns Feedback Table", "Per-return classifications with assigned taxonomy, body area localization, confidence score, and model attribution."))
                analysis_table = gr.Dataframe(interactive=False, wrap=True, max_height=520)

            # Tab 3: Review Queue
            with gr.Tab("Review Queue"):
                gr.HTML(render_tab_banner("⚠️", "Ambiguous &amp; Low-Confidence Comments", "These comments were flagged for human category review. Check ai_explanation for the reason: a Gemini 503 means temporary high demand, while a Gemini 429 means a request or token limit was reached.", extra_class="review-banner"))
                review_table = gr.Dataframe(interactive=False, wrap=True, max_height=500)

            # Tab 4: Category & Product Insights
            with gr.Tab("Category Insights"):
                with gr.Row():
                    with gr.Column(scale=5):
                        gr.Markdown("### 📊 SKU Returns Breakdown")
                        product_table = gr.Dataframe(interactive=False, wrap=True)
                    with gr.Column(scale=5):
                        gr.Markdown("### 🎯 Executive Recommendation")
                        insight_box = gr.HTML(render_default_insight())

            # Tab 5: Telemetry & Cost
            with gr.Tab("Telemetry & Cost"):
                gr.HTML(render_tab_banner("⚙️", "Pipeline Architecture &amp; Cost Telemetry", "Two-stage routing architecture: bulk classification via fast model + fallback routing for ambiguous cases. Real-time token usage and cost accounting."))
                with gr.Row():
                    with gr.Column(scale=3):
                        tech = gr.Code(language="json", label="Pipeline Configuration & Telemetry")
                    with gr.Column(scale=2):
                        gr.Markdown("### 📥 Export Enriched Dataset")
                        gr.Markdown("Download full classified returns data with assigned primary reasons, sub-reasons, confidence scores, and review status.")
                        export = gr.File(label="Classified Returns CSV", interactive=False)

        # 5. Wiring Callbacks
        upload.upload(
            load_dataset,
            inputs=upload,
            outputs=[state_input, file_summary]
        )
        
        sample_btn.click(
            lambda: (str(SAMPLE), *load_dataset(str(SAMPLE))),
            outputs=[upload, state_input, file_summary]
        )

        threshold_control.change(
            lambda value: render_header(
                api_key=SETTINGS.api_key,
                fast_model=SETTINGS.model_fast,
                strong_model=SETTINGS.model_strong,
                threshold=float(value),
            ),
            inputs=threshold_control,
            outputs=header,
        )
        
        run_btn.click(
            execute_analysis,
            inputs=[state_input, threshold_control],
            outputs=[
                state_result,
                metrics_html,
                release_cards_display,
                reason_bars_display,
                reasons_table,
                analysis_table,
                review_table,
                product_table,
                insight_box,
                tech,
                export
            ]
        )

    return demo, css, theme
