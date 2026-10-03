from typing import Literal
from pydantic import BaseModel, Field

PrimaryReason = Literal[
    "Fit", "Fabric/Material", "Quality", "Colour",
    "Expectation Mismatch", "Damaged", "Wrong Item",
    "Delivery Related", "Other"
]

# Canonical labels keep analytics comparable across batches. Body area preserves the
# extra specificity instead of allowing variants such as "Chest tight".
SubReason = Literal[
    "Too tight", "Too loose", "Too small", "Too short", "Too long",
    "Sleeves too narrow", "Sleeves too short",
    "Fabric feels rough", "Fabric too sheer", "Fabric too thin", "Too thin",
    "Loose stitching", "Poor stitching", "Print peeling", "Shape changed after wash", "Zip issue",
    "Colour mismatch", "Looks different from image", "Damaged on arrival",
    "Wrong product received", "Late delivery", "Changed mind", "Unclear",
]

class Classification(BaseModel):
    return_id: str
    primary_reason: PrimaryReason
    sub_reason: SubReason
    body_area: str
    confidence: float = Field(ge=0.0, le=1.0)
    short_explanation: str

class BatchClassification(BaseModel):
    items: list[Classification]

class Insight(BaseModel):
    headline: str
    recommended_action: str
    evidence: str
