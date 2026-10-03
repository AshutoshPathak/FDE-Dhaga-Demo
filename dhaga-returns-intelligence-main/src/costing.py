import os

CASE_ORDERS_PER_WEEK = 48_000
CASE_RETURN_RATE = 0.31
CASE_OTHER_SHARE = 0.44
EST_OTHER_RETURNS_PER_WEEK = CASE_ORDERS_PER_WEEK * CASE_RETURN_RATE * CASE_OTHER_SHARE

def _f(name):
    v = os.getenv(name, "").strip()
    return float(v) if v else None

def cost_summary(usage, records_processed: int):
    prices = {
        "fast_in": _f("MODEL_FAST_INPUT_USD_PER_1M"),
        "fast_out": _f("MODEL_FAST_OUTPUT_USD_PER_1M"),
        "strong_in": _f("MODEL_STRONG_INPUT_USD_PER_1M"),
        "strong_out": _f("MODEL_STRONG_OUTPUT_USD_PER_1M"),
    }
    tokens = {"fast_input":usage.fast_input,"fast_output":usage.fast_output,"strong_input":usage.strong_input,"strong_output":usage.strong_output}
    base = {
        "tokens": tokens,
        "records_processed": records_processed,
        "derived_weekly_other_return_volume": round(EST_OTHER_RETURNS_PER_WEEK),
        "volume_note": "Derived from case figures: 48,000 orders/week × 31% returns × 44% tagged Other.",
    }
    if any(v is None for v in prices.values()):
        return {**base,"run_cost_usd":None,"cost_per_1000_usd":None,"estimated_weekly_other_cost_usd":None,"note":"Token usage captured. Add current official per-1M-token prices in environment variables to calculate cost."}
    total = (usage.fast_input*prices["fast_in"] + usage.fast_output*prices["fast_out"] + usage.strong_input*prices["strong_in"] + usage.strong_output*prices["strong_out"]) / 1_000_000
    per_record = total / records_processed if records_processed else 0
    return {**base,"run_cost_usd":round(total,6),"cost_per_1000_usd":round(per_record*1000,6),"estimated_weekly_other_cost_usd":round(per_record*EST_OTHER_RETURNS_PER_WEEK,6),"note":"Uses configured per-1M-token prices; weekly volume is a derived estimate from the case study."}
