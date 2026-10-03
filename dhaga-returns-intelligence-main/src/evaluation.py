import pandas as pd

def evaluate(predicted: pd.DataFrame, labeled_path: str) -> dict:
    gold = pd.read_csv(labeled_path)
    merged = predicted.merge(gold[["return_id","gold_primary_reason","gold_sub_reason","expected_route"]], on="return_id", how="inner")
    if merged.empty:
        return {}
    primary = (merged["ai_primary_reason"] == merged["gold_primary_reason"]).mean()
    sub = (merged["ai_sub_reason"] == merged["gold_sub_reason"]).mean()
    review = merged["review_status"].eq("Needs Review")
    return {"rows_compared":len(merged),"primary_accuracy":round(float(primary)*100,1),"sub_reason_accuracy":round(float(sub)*100,1),"human_review_pct":round(float(review.mean())*100,1)}
