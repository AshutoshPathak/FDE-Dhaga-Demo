from __future__ import annotations
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from google import genai
from google.genai import types
from .config import SETTINGS
from .schemas import BatchClassification, Classification, Insight

TAXONOMY = """
Primary reasons: Fit, Fabric/Material, Quality, Colour, Expectation Mismatch, Damaged, Wrong Item, Delivery Related, Other.
Use concise sub-reasons. Body area should be one of Chest, Waist, Shoulders, Arms, Length, Overall, Seam, Back, NA when possible.
"""

@dataclass
class Usage:
    fast_input: int = 0
    fast_output: int = 0
    strong_input: int = 0
    strong_output: int = 0

    def add(self, response, strong=False):
        u = getattr(response, "usage_metadata", None)
        if not u:
            return
        inp = int(getattr(u, "prompt_token_count", 0) or 0)
        out = int(getattr(u, "candidates_token_count", 0) or 0)
        if strong:
            self.strong_input += inp
            self.strong_output += out
        else:
            self.fast_input += inp
            self.fast_output += out

class GeminiWorkflow:
    def __init__(self):
        if not SETTINGS.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        self.client = genai.Client(api_key=SETTINGS.api_key)
        self.usage = Usage()

    def _fast_batch(self, records: list[dict]) -> list[dict]:
        prompt = f"""You classify e-commerce fashion return comments.
{TAXONOMY}
Return exactly one classification per input return_id. Do not invent facts. Hinglish is normal. Confidence is your certainty in the taxonomy mapping.
INPUT:
{json.dumps(records, ensure_ascii=False)}"""
        last_error = None
        for _attempt in range(2):
            try:
                response = self.client.models.generate_content(
                    model=SETTINGS.model_fast,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json",
                        response_schema=BatchClassification,
                    ),
                )
                self.usage.add(response, strong=False)
                parsed = response.parsed or BatchClassification.model_validate_json(response.text)
                by_id = {str(x.return_id): x for x in parsed.items}
                if any(str(r["return_id"]) not in by_id for r in records):
                    raise ValueError("Model omitted one or more return_id values")
                return [by_id[str(r["return_id"])].model_dump() for r in records]
            except Exception as e:
                last_error = e
        return [
            {"return_id":str(r["return_id"]),"primary_reason":"Other","sub_reason":"Classification failed","body_area":"NA","confidence":0.0,"short_explanation":f"Structured classification failed after retry: {type(last_error).__name__}"}
            for r in records
        ]

    def _strong_one(self, record: dict, first: dict) -> dict:
        prompt = f"""Review an ambiguous fashion-return classification.
{TAXONOMY}
Use only the supplied customer comment and metadata. If it remains genuinely ambiguous, keep confidence below {SETTINGS.confidence_threshold}.
RECORD: {json.dumps(record, ensure_ascii=False)}
FIRST PASS: {json.dumps(first, ensure_ascii=False)}"""
        response = self.client.models.generate_content(
            model=SETTINGS.model_strong,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=Classification,
            ),
        )
        self.usage.add(response, strong=True)
        obj = response.parsed or Classification.model_validate_json(response.text)
        return obj.model_dump()

    def classify(self, df, progress=None):
        records = df[["return_id","sku","product_name","category","size_ordered","other_comment"]].to_dict("records")
        batches = [records[i:i+SETTINGS.batch_size] for i in range(0, len(records), SETTINGS.batch_size)]
        first = []
        with ThreadPoolExecutor(max_workers=SETTINGS.max_workers) as ex:
            futures = {ex.submit(self._fast_batch, b): i for i,b in enumerate(batches)}
            done = 0
            for fut in as_completed(futures):
                first.extend(fut.result())
                done += 1
                if progress:
                    progress(0.15 + 0.45*(done/max(1,len(batches))), desc="Classifying return comments")
        by_id = {str(x["return_id"]): x for x in first}
        outputs, low = [], []
        for r in records:
            p = by_id.get(str(r["return_id"]))
            if not p:
                outputs.append({"return_id":str(r["return_id"]),"primary_reason":"Other","sub_reason":"Model response missing","body_area":"NA","confidence":0.0,"short_explanation":"No classification returned.","review_status":"Needs Review","model_used":SETTINGS.model_fast})
            elif float(p["confidence"]) < SETTINGS.confidence_threshold:
                low.append((r,p))
            else:
                p.update({"review_status":"Accepted","model_used":SETTINGS.model_fast})
                outputs.append(p)
        for idx,(r,p) in enumerate(low):
            try:
                q = self._strong_one(r,p)
                q["review_status"] = "Accepted" if q["confidence"] >= SETTINGS.confidence_threshold else "Needs Review"
                q["model_used"] = SETTINGS.model_strong
                outputs.append(q)
            except Exception as e:
                p.update({"review_status":"Needs Review","model_used":SETTINGS.model_fast,"short_explanation":f"Second-pass review failed: {type(e).__name__}"})
                outputs.append(p)
            if progress:
                progress(0.60 + 0.20*((idx+1)/max(1,len(low))), desc="Reviewing uncertain cases")
        return outputs

    def insight(self, summary: dict) -> dict:
        prompt = f"""You are assisting a fashion category head. Based only on the supplied aggregate facts, produce one concise operational insight. Do not claim causality. Do not invent data.
SUMMARY: {json.dumps(summary, ensure_ascii=False)}"""
        response = self.client.models.generate_content(
            model=SETTINGS.model_strong,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json",
                response_schema=Insight,
            ),
        )
        self.usage.add(response, strong=True)
        obj = response.parsed or Insight.model_validate_json(response.text)
        return obj.model_dump()
