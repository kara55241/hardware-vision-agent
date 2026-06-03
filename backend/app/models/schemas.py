from pydantic import BaseModel
from typing import List

class ComponentBase(BaseModel):
    id: str
    type: str

class DetectedComponent(ComponentBase):
    bbox: List[float]
    confidence: float
    confirmed: bool = False
    value: str = ""
    unit: str = ""

class Relation(BaseModel):
    subject: str
    relation: str
    object: str

class Connection(BaseModel):
    from_node: str
    to_node: str

class CircuitData(BaseModel):
    image_id: str
    components: List[DetectedComponent]
    connections: List[Connection]
    power_type: str

class QualityCheckResult(BaseModel):
    passed: bool
    feedback: str

class ColorBandResult(BaseModel):
    resistor_id: str
    value: str
    unit: str

class DiagnosisResult(BaseModel):
    status: str
    warnings: List[str]
    explanation: str
