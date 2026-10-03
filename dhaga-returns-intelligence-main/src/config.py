from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_FAST = os.getenv("GEMINI_MODEL_FAST", "gemini-3.5-flash-lite")
GEMINI_MODEL_STRONG = os.getenv("GEMINI_MODEL_STRONG", "gemini-3.5-flash")

@dataclass(frozen=True)
class Settings:
    model_fast: str = GEMINI_MODEL_FAST
    model_strong: str = GEMINI_MODEL_STRONG
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.80"))
    # Six 50-row calls for the 300-row sample stay well below the burst created by
    # thirty 10-row calls, while remaining comfortably within the model context.
    batch_size: int = int(os.getenv("BATCH_SIZE", "50"))
    # Keep request bursts modest on shared Gemini capacity. This remains configurable.
    max_workers: int = int(os.getenv("MAX_WORKERS", "1"))
    # Defaults match the free-tier limits currently shown for this project's models.
    # The client uses a small safety margin rather than aiming exactly at the cap.
    fast_requests_per_minute: int = int(os.getenv("GEMINI_FAST_RPM", "15"))
    strong_requests_per_minute: int = int(os.getenv("GEMINI_STRONG_RPM", "5"))
    api_key: str | None = GEMINI_API_KEY

SETTINGS = Settings()
