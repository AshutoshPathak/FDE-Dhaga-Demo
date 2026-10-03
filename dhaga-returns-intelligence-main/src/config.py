from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_FAST = os.getenv("GEMINI_MODEL_FAST", "gemini-3.5-flash-lite")
GEMINI_MODEL_STRONG = os.getenv("GEMINI_MODEL_STRONG", "gemini-3.8-flash")

@dataclass(frozen=True)
class Settings:
    model_fast: str = GEMINI_MODEL_FAST
    model_strong: str = GEMINI_MODEL_STRONG
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.80"))
    batch_size: int = int(os.getenv("BATCH_SIZE", "10"))
    max_workers: int = int(os.getenv("MAX_WORKERS", "4"))
    api_key: str | None = GEMINI_API_KEY

SETTINGS = Settings()
