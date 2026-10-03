from __future__ import annotations

def _out(row, primary, sub, area, confidence, explanation):
    return {"return_id":str(row["return_id"]),"primary_reason":primary,"sub_reason":sub,
            "body_area":area,"confidence":confidence,"short_explanation":explanation,
            "review_status":"Needs Review" if confidence < 0.80 else "Accepted",
            "model_used":"Demo heuristic (no API key)"}

def classify_row(row):
    t = str(row.get("other_comment", "")).lower()
    if not t.strip(): return _out(row,"Other","Blank comment","NA",0.20,"No usable customer comment was provided.")
    if any(x in t for x in ["wrong item","galat item","mera order wala item nahi"]): return _out(row,"Wrong Item","Wrong product received","NA",0.96,"Customer says a different item was received.")
    if any(x in t for x in ["damaged","torn","hole"]): return _out(row,"Damaged","Damaged on arrival","NA",0.95,"Customer reports physical damage.")
    if any(x in t for x in ["late delivery","late hui","occasion ke baad","expected date"]): return _out(row,"Delivery Related","Late delivery","NA",0.92,"Customer refers to late delivery.")
    if any(x in t for x in ["zip","stitch","thread","button","print","wash ke baad","one wash"]):
        sub = "Zip issue" if "zip" in t else "Button issue" if "button" in t else "Print peeling" if "print" in t else "Shape changed after wash" if "wash" in t else "Poor stitching"
        return _out(row,"Quality",sub,"NA",0.90,"Customer describes a product-quality defect.")
    if any(x in t for x in ["fabric","kapda","material","transparent","sheer","itchy"]):
        sub = "Too sheer" if any(x in t for x in ["transparent","sheer"]) else "Too thin" if ("thin" in t or "patla" in t) else "Fabric feels rough"
        return _out(row,"Fabric/Material",sub,"NA",0.88,"Customer describes a fabric or material issue.")
    if any(x in t for x in ["colour","color","shade"]): return _out(row,"Colour","Colour mismatch","NA",0.92,"Customer says the colour differs from expectation.")
    if any(x in t for x in ["photo jaisa","image mein","listing","actual different","photo and actual"]): return _out(row,"Expectation Mismatch","Looks different from image","NA",0.86,"Customer compares the received item with listing imagery.")
    fit_words=["tight","loose","small","short","long","fit","fitting","chota","lamba","kamar","chest","shoulder","sleeve","bazu","wrist"]
    if any(x in t for x in fit_words):
        area="Chest" if "chest" in t else "Waist" if any(x in t for x in ["waist","kamar"]) else "Shoulders" if "shoulder" in t else "Arms" if any(x in t for x in ["sleeve","bazu","wrist","arms"]) else "Length" if any(x in t for x in ["short","long","length","lamba"]) else "Overall"
        sub="Too tight" if "tight" in t else "Too loose" if ("loose" in t or "baggy" in t) else "Too short" if ("short" in t or "choti" in t) else "Too long" if ("long" in t or "lamba" in t) else "Too small overall" if ("small" in t or "chota" in t) else "Unclear fit issue"
        conf=0.84 if sub != "Unclear fit issue" else 0.61
        return _out(row,"Fit",sub,area,conf,"Customer language indicates a fit or size issue.")
    return _out(row,"Other","Unclear","NA",0.48,"The comment is too vague for a confident classification.")

def classify_dataframe(df):
    return [classify_row(row) for _, row in df.iterrows()]
