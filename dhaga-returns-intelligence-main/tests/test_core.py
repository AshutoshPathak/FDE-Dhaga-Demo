import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from src.data import validate_input, clean_input, merge_predictions, overview_metrics, reason_breakdown, product_summary
from src.demo_classifier import classify_dataframe

SAMPLE = ROOT / "data" / "dhaga_returns_sample_300.csv"

def test_sample_valid():
    df = pd.read_csv(SAMPLE)
    ok, msg = validate_input(df)
    assert ok, msg
    assert len(df) == 300
    assert (df["return_reason_selected"] == "Other").sum() == 132

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
