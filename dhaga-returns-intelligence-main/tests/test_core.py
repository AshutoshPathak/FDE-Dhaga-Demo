import sys
import math
from pathlib import Path
import pandas as pd
from pydantic import ValidationError

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from src.data import validate_input, clean_input, merge_predictions, overview_metrics, reason_breakdown, product_summary
from src.demo_classifier import classify_dataframe
from src.evaluation import evaluate
from src.gemini_client import GeminiWorkflow, RequestPacer, _is_retryable, model_failure_message
from src.schemas import Classification
from src.ui.components import render_header, render_hero_section

SAMPLE = ROOT / "data" / "dhaga_returns_sample_300.csv"
SMOKE_SAMPLE = ROOT / "data" / "dhaga_returns_smoke_10.csv"

def test_sample_valid():
    df = pd.read_csv(SAMPLE)
    ok, msg = validate_input(df)
    assert ok, msg
    assert len(df) == 300
    assert (df["return_reason_selected"] == "Other").sum() == 132

def test_smoke_sample_is_valid_and_small():
    df = pd.read_csv(SMOKE_SAMPLE)
    ok, msg = validate_input(df)
    assert ok, msg
    assert len(df) == 10

def test_demo_end_to_end():
    df = clean_input(pd.read_csv(SAMPLE).head(50))
    preds = classify_dataframe(df)
    assert len(preds) == 50
    result = merge_predictions(df, preds)
    m = overview_metrics(result)
    assert m["total"] == 50
    assert 0 <= m["auto_pct"] <= 100
    assert not reason_breakdown(result).empty
    assert not product_summary(result).empty

def test_evaluation_reports_accuracy_and_routing_metrics():
    df = clean_input(pd.read_csv(SAMPLE).head(10))
    result = merge_predictions(df, classify_dataframe(df))
    metrics = evaluate(result, str(SAMPLE.with_name("dhaga_returns_sample_300_labeled.csv")))

    assert metrics["rows_compared"] == 10
    assert {"primary_accuracy_pct", "sub_reason_accuracy_pct", "escalation_attempt_pct", "human_review_pct"}.issubset(metrics)

def test_demo_mode_uses_the_selected_threshold():
    df = pd.DataFrame([{"return_id": "R-001", "other_comment": "color mismatch"}])
    assert classify_dataframe(df, threshold=0.80)[0]["review_status"] == "Accepted"
    assert classify_dataframe(df, threshold=0.99)[0]["review_status"] == "Needs Review"

def test_live_schema_requires_a_canonical_sub_reason():
    record = {
        "return_id": "R-001", "primary_reason": "Fit", "sub_reason": "Too tight",
        "body_area": "Chest", "confidence": 0.95, "short_explanation": "Chest is tight.",
    }
    assert Classification.model_validate(record).sub_reason == "Too tight"
    record["sub_reason"] = "Chest tight"
    try:
        Classification.model_validate(record)
    except ValidationError:
        pass
    else:
        raise AssertionError("Free-form sub-reason should not pass the live schema")

class _ApiError(Exception):
    def __init__(self, code: int):
        self.code = code
        super().__init__(f"HTTP {code}")

def test_temporary_gemini_errors_are_retryable_and_visible():
    error = _ApiError(503)
    assert _is_retryable(error)
    message = model_failure_message("STRONG review", error)
    assert "Gemini 503" in message
    assert "Needs Review" in message

def test_auth_errors_are_not_retried():
    assert not _is_retryable(_ApiError(401))
    assert not _is_retryable(_ApiError(429))

def test_request_pacer_leaves_headroom_below_model_rpm_limit():
    now = [100.0]
    delays = []
    pacer = RequestPacer(5, clock=lambda: now[0], sleep=delays.append)

    pacer.wait_for_slot()
    pacer.wait_for_slot()

    assert len(delays) == 1
    assert math.isclose(delays[0], 60.0 / (5 * 0.90))

def test_failed_fast_batch_does_not_cascade_into_strong_requests():
    workflow = object.__new__(GeminiWorkflow)
    failed_message = model_failure_message("FAST classification", _ApiError(503))
    workflow._fast_batch = lambda records: [
        {
            "return_id": str(record["return_id"]),
            "primary_reason": "Other",
            "sub_reason": "Classification failed",
            "body_area": "NA",
            "confidence": 0.0,
            "short_explanation": failed_message,
            "model_error": True,
        }
        for record in records
    ]
    workflow._strong_one = lambda *_: (_ for _ in ()).throw(AssertionError("STRONG should not run"))
    df = pd.DataFrame([{
        "return_id": "R-001", "sku": "SKU-001", "product_name": "Test Kurta",
        "category": "Kurtas", "size_ordered": "M", "other_comment": "Too tight",
    }])

    result = workflow.classify(df)

    assert result[0]["review_status"] == "Needs Review"
    assert result[0]["short_explanation"] == failed_message

def test_header_and_hero_show_current_model_configuration_without_fake_actions():
    header = render_header("key-present", "gemini-3.5-flash-lite", "gemini-3.5-flash", 0.8)
    hero = render_hero_section("gemini-3.5-flash-lite", "gemini-3.5-flash")

    assert "Back to Operations" not in hero
    assert "v2.5 Flash-Lite" not in hero
    assert "gemini-3.5-flash-lite → gemini-3.5-flash" in hero
    assert "Review threshold 80%" in header
