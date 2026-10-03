from typing import Literal
from pydantic import BaseModel, Field

PrimaryReason = Literal[
    "Fit", "Fabric/Material", "Quality", "Colour",
    "Expectation Mismatch", "Damaged", "Wrong Item",
    "Delivery Related", "Other"
]

class Classification(BaseModel):
    return_id: str
    primary_reason: PrimaryReason
    sub_reason: str
    body_area: str
    confidence: float = Field(ge=0.0, le=1.0)
    short_explanation: str

class BatchClassification(BaseModel):
    items: list[Classification]

class Insight(BaseModel):
    headline: str
    recommended_action: str
    evidence: str
