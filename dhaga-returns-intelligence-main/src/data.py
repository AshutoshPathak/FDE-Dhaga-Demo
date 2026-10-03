from __future__ import annotations
import pandas as pd

REQUIRED_COLUMNS = [
    "return_id", "order_id", "sku", "product_name", "category",
    "size_ordered", "return_reason_selected", "other_comment"
]

def validate_input(df: pd.DataFrame) -> tuple[bool, str]:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return False, "Missing required columns: " + ", ".join(missing)
    if df.empty:
        return False, "The uploaded CSV has no rows."
    if len(df) > 5000:
        return False, "For this MVP, upload at most 5,000 rows per run."
    return True, "File looks valid"

def clean_input(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["other_comment"] = out["other_comment"].fillna("").astype(str).str.strip()
    for c in ["sku", "category", "size_ordered", "return_reason_selected"]:
        out[c] = out[c].fillna("Unknown").astype(str).str.strip()
    return out

def merge_predictions(df: pd.DataFrame, predictions: list[dict]) -> pd.DataFrame:
    pred = pd.DataFrame(predictions)
    if pred.empty:
        return df.copy()
    pred = pred.rename(columns={
        "primary_reason":"ai_primary_reason", "sub_reason":"ai_sub_reason",
        "body_area":"ai_body_area", "confidence":"ai_confidence",
        "short_explanation":"ai_explanation"
    })
    cols = ["return_id","ai_primary_reason","ai_sub_reason","ai_body_area","ai_confidence","ai_explanation","review_status","model_used"]
    return df.merge(pred[cols], on="return_id", how="left")

def overview_metrics(result: pd.DataFrame) -> dict:
    total = len(result)
    originally_other = int((result["return_reason_selected"] == "Other").sum()) if total else 0
    needs_review = int((result["review_status"] == "Needs Review").sum()) if total else 0
    return {"total": total, "originally_other": originally_other,
            "auto_pct": round(((total-needs_review)/total*100),1) if total else 0,
            "needs_review": needs_review}

def reason_breakdown(result: pd.DataFrame) -> pd.DataFrame:
    valid = result[result["ai_primary_reason"].notna()]
    if valid.empty:
        return pd.DataFrame(columns=["Reason","Returns","Percent"])
    s = valid["ai_primary_reason"].value_counts().rename_axis("Reason").reset_index(name="Returns")
    s["Percent"] = (s["Returns"] / len(valid) * 100).round(1)
    return s

def product_summary(result: pd.DataFrame) -> pd.DataFrame:
    valid = result[result["review_status"] != "Needs Review"].copy()
    if valid.empty:
        return pd.DataFrame(columns=["sku","product_name","returns","fit_pct","top_issue"])
    valid["is_fit"] = valid["ai_primary_reason"].eq("Fit")
    rows=[]
    for (sku,name), g in valid.groupby(["sku","product_name"], dropna=False):
        top = g["ai_sub_reason"].value_counts().index[0] if g["ai_sub_reason"].notna().any() else "Unknown"
        rows.append({"sku":sku,"product_name":name,"returns":len(g),"fit_pct":round(g["is_fit"].mean()*100,1),"top_issue":top})
    return pd.DataFrame(rows).sort_values(["fit_pct","returns"], ascending=False)
