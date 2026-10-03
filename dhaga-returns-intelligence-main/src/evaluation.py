import pandas as pd

def evaluate(predicted: pd.DataFrame, labeled_path: str) -> dict:
    gold = pd.read_csv(labeled_path)
    merged = predicted.merge(gold[["return_id","gold_primary_reason","gold_sub_reason","expected_route"]], on="return_id", how="inner")
    if merged.empty:
        return {}
    required = {"ai_primary_reason", "ai_sub_reason", "review_status", "routing_stage"}
    missing = required.difference(merged.columns)
    if missing:
        raise ValueError("Prediction CSV is missing required columns: " + ", ".join(sorted(missing)))
    primary = (merged["ai_primary_reason"] == merged["gold_primary_reason"]).mean()
    sub = (merged["ai_sub_reason"] == merged["gold_sub_reason"]).mean()
    review = merged["review_status"].eq("Needs Review")
    route = merged["routing_stage"].fillna("")
    escalated = route.isin(["STRONG reviewed", "STRONG unavailable"])
    strong_reviewed = route.eq("STRONG reviewed")
    expected_escalation = merged["expected_route"].eq("strong_model_or_review")
    return {
        "rows_compared": len(merged),
        "primary_accuracy_pct": round(float(primary) * 100, 1),
        "sub_reason_accuracy_pct": round(float(sub) * 100, 1),
        "escalation_attempt_pct": round(float(escalated.mean()) * 100, 1),
        "strong_review_completed_pct": round(float(strong_reviewed.mean()) * 100, 1),
        "human_review_pct": round(float(review.mean()) * 100, 1),
        "expected_escalation_pct": round(float(expected_escalation.mean()) * 100, 1),
    }
