from __future__ import annotations
import json
import random
import re
import time
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from google import genai
from google.genai import types
from .config import SETTINGS
from .schemas import BatchClassification, Classification, Insight

TAXONOMY = """
Primary reasons: Fit, Fabric/Material, Quality, Colour, Expectation Mismatch, Damaged, Wrong Item, Delivery Related, Other.
Select sub_reason exactly from this controlled vocabulary; never invent wording or change capitalization.
- Fit: Too tight, Too loose, Too small, Too short, Too long, Sleeves too narrow, Sleeves too short.
- Fabric/Material: Fabric feels rough, Fabric too sheer, Fabric too thin, Too thin.
- Quality: Loose stitching, Poor stitching, Print peeling, Shape changed after wash, Zip issue.
- Colour: Colour mismatch. Expectation Mismatch: Looks different from image. Damaged: Damaged on arrival.
- Wrong Item: Wrong product received. Delivery Related: Late delivery. Other: Changed mind or Unclear.
Use body_area for the location (Chest, Waist, Shoulders, Arms, Length, Overall, Seam, Back, or NA), not a custom sub-reason. For example, a tight chest is sub_reason Too tight and body_area Chest.
"""

# A 429 is potentially retryable after the provider's reset window, but an automatic
# retry here would spend more of the limited request budget. Surface it immediately.
RETRYABLE_STATUS_CODES = {408, 500, 502, 503, 504}
MAX_MODEL_ATTEMPTS = 3
RATE_LIMIT_SAFETY_FACTOR = 0.90
_MODEL_PACERS: dict[tuple[str, int], "RequestPacer"] = {}
_MODEL_PACERS_LOCK = Lock()


def _status_code(error: Exception) -> int | None:
    """Extract an HTTP-like status code from Gemini SDK errors without exposing secrets."""
    code = getattr(error, "code", None)
    if isinstance(code, int):
        return code
    match = re.search(r"\b([45]\d{2})\b", str(error))
    return int(match.group(1)) if match else None


def _is_retryable(error: Exception) -> bool:
    return _status_code(error) in RETRYABLE_STATUS_CODES


def model_failure_message(stage: str, error: Exception) -> str:
    """Give the category user a safe, actionable explanation of a model failure."""
    status = _status_code(error)
    if status == 503:
        detail = "Gemini 503: temporary high demand"
    elif status == 429:
        detail = "Gemini 429: request or token rate limit reached; wait before retrying"
    elif status == 401:
        detail = "Gemini 401: API key is missing, invalid, or expired"
    elif status == 403:
        detail = "Gemini 403: API key does not have access to this model"
    elif status:
        detail = f"Gemini {status}: {type(error).__name__}"
    else:
        detail = f"Gemini request failed: {type(error).__name__}"
    return f"{stage} unavailable ({detail}). Sent to Needs Review rather than accepted automatically."


class RequestPacer:
    """Spaces requests for one model so a batch stays below its RPM quota."""

    def __init__(self, requests_per_minute: int, *, clock=time.monotonic, sleep=time.sleep):
        if requests_per_minute < 1:
            raise ValueError("requests_per_minute must be at least 1")
        # Leave headroom for the provider's rolling time window and other small calls.
        self.interval = 60.0 / (requests_per_minute * RATE_LIMIT_SAFETY_FACTOR)
        self._next_slot = 0.0
        self._lock = Lock()
        self._clock = clock
        self._sleep = sleep

    def wait_for_slot(self) -> None:
        """Reserve the next slot before waiting, including when workers are enabled."""
        with self._lock:
            slot = max(self._clock(), self._next_slot)
            self._next_slot = slot + self.interval
        delay = slot - self._clock()
        if delay > 0:
            self._sleep(delay)


def model_pacer(model: str, requests_per_minute: int) -> RequestPacer:
    """Reuse a model's pace across analyses clicked in the same running app."""
    key = (model, requests_per_minute)
    with _MODEL_PACERS_LOCK:
        if key not in _MODEL_PACERS:
            _MODEL_PACERS[key] = RequestPacer(requests_per_minute)
        return _MODEL_PACERS[key]


def _generate_with_retry(call, pacer: RequestPacer | None = None):
    """Retry only temporary provider failures with bounded exponential backoff and jitter."""
    for attempt in range(MAX_MODEL_ATTEMPTS):
        try:
            if pacer:
                pacer.wait_for_slot()
            return call()
        except Exception as error:
            if not _is_retryable(error) or attempt == MAX_MODEL_ATTEMPTS - 1:
                raise
            delay = min(8.0, 2**attempt) + random.uniform(0.0, 0.25)
            time.sleep(delay)


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
    def __init__(self, confidence_threshold: float | None = None):
        if not SETTINGS.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        self.client = genai.Client(api_key=SETTINGS.api_key)
        self.usage = Usage()
        self.confidence_threshold = (
            SETTINGS.confidence_threshold if confidence_threshold is None else float(confidence_threshold)
        )
        self.fast_pacer = model_pacer(SETTINGS.model_fast, SETTINGS.fast_requests_per_minute)
        self.strong_pacer = model_pacer(SETTINGS.model_strong, SETTINGS.strong_requests_per_minute)

    def _fast_batch(self, records: list[dict]) -> list[dict]:
        prompt = f"""You classify e-commerce fashion return comments.
{TAXONOMY}
Return exactly one classification per input return_id. Do not invent facts. Hinglish is normal. Confidence is your certainty in the taxonomy mapping.
INPUT:
{json.dumps(records, ensure_ascii=False)}"""
        try:
            response = _generate_with_retry(
                lambda: self.client.models.generate_content(
                    model=SETTINGS.model_fast,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json",
                        response_schema=BatchClassification,
                    ),
                ),
                pacer=self.fast_pacer,
            )
            self.usage.add(response, strong=False)
            parsed = response.parsed or BatchClassification.model_validate_json(response.text)
            by_id = {str(x.return_id): x for x in parsed.items}
            if any(str(r["return_id"]) not in by_id for r in records):
                raise ValueError("Model omitted one or more return_id values")
            return [by_id[str(r["return_id"])].model_dump() for r in records]
        except Exception as error:
            message = model_failure_message("FAST classification", error)
        return [
            {
                "return_id": str(r["return_id"]),
                "primary_reason": "Other",
                "sub_reason": "Classification failed",
                "body_area": "NA",
                "confidence": 0.0,
                "short_explanation": message,
                "model_error": True,
            }
            for r in records
        ]

    def _strong_one(self, record: dict, first: dict) -> dict:
        prompt = f"""Review an ambiguous fashion-return classification.
{TAXONOMY}
Use only the supplied customer comment and metadata. If it remains genuinely ambiguous, keep confidence below {self.confidence_threshold}.
RECORD: {json.dumps(record, ensure_ascii=False)}
FIRST PASS: {json.dumps(first, ensure_ascii=False)}"""
        response = _generate_with_retry(
            lambda: self.client.models.generate_content(
                model=SETTINGS.model_strong,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                    response_schema=Classification,
                ),
            ),
            pacer=self.strong_pacer,
        )
        self.usage.add(response, strong=True)
        obj = response.parsed or Classification.model_validate_json(response.text)
        return obj.model_dump()

    def classify(self, df, progress=None):
        records = df[["return_id","sku","product_name","category","size_ordered","other_comment"]].to_dict("records")
        batches = [records[i:i+SETTINGS.batch_size] for i in range(0, len(records), SETTINGS.batch_size)]
        first = []
        if progress:
            progress(
                0.15,
                desc=f"Submitting {len(batches)} FAST batch(es); waiting for Gemini responses",
            )
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
                outputs.append({"return_id":str(r["return_id"]),"primary_reason":"Other","sub_reason":"Model response missing","body_area":"NA","confidence":0.0,"short_explanation":"No classification returned.","review_status":"Needs Review","model_used":SETTINGS.model_fast,"routing_stage":"FAST unavailable"})
            elif p.get("model_error"):
                p.update({"review_status": "Needs Review", "model_used": SETTINGS.model_fast, "routing_stage": "FAST unavailable"})
                outputs.append(p)
            elif float(p["confidence"]) < self.confidence_threshold:
                low.append((r,p))
            else:
                p.update({"review_status":"Accepted","model_used":SETTINGS.model_fast,"routing_stage":"FAST accepted"})
                outputs.append(p)
        if progress:
            if low:
                progress(0.60, desc=f"Reviewing {len(low)} uncertain return(s) with the STRONG model")
            else:
                progress(0.80, desc="FAST classification complete; preparing results")
        for idx,(r,p) in enumerate(low):
            if progress:
                progress(
                    0.60 + 0.20*(idx/max(1, len(low))),
                    desc=f"Reviewing uncertain case {idx + 1} of {len(low)} (safely paced for Gemini)",
                )
            try:
                q = self._strong_one(r,p)
                q["review_status"] = "Accepted" if q["confidence"] >= self.confidence_threshold else "Needs Review"
                q["model_used"] = SETTINGS.model_strong
                q["routing_stage"] = "STRONG reviewed"
                outputs.append(q)
            except Exception as e:
                p.update({
                    "review_status": "Needs Review",
                    "model_used": SETTINGS.model_fast,
                    "routing_stage": "STRONG unavailable",
                    "short_explanation": model_failure_message("STRONG review", e),
                })
                outputs.append(p)
            if progress:
                progress(0.60 + 0.20*((idx+1)/max(1,len(low))), desc="Reviewing uncertain cases")
        return outputs

    def insight(self, summary: dict) -> dict:
        prompt = f"""You are assisting a fashion category head. Based only on the supplied aggregate facts, produce one concise operational insight. Do not claim causality. Do not invent data.
SUMMARY: {json.dumps(summary, ensure_ascii=False)}"""
        response = _generate_with_retry(
            lambda: self.client.models.generate_content(
                model=SETTINGS.model_strong,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json",
                    response_schema=Insight,
                ),
            ),
            pacer=self.strong_pacer,
        )
        self.usage.add(response, strong=True)
        obj = response.parsed or Insight.model_validate_json(response.text)
        return obj.model_dump()
