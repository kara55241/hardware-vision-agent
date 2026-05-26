from pydantic import BaseModel
from typing import List

class ComponentBase(BaseModel):
    id: str
    type: str

class DetectedComponent(ComponentBase):
    bbox: List[float]
    confidence: float
    confirmed: bool = False

class Relation(BaseModel):
    subject: str
    relation: str
    object: str

class TripleOutput(BaseModel):
    components: List[DetectedComponent]
    relations: List[Relation]

class DiagnosisResult(BaseModel):
    status: str
    warnings: List[str]
    explanation: str
