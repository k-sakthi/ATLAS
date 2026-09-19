from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Set

class Provenance(BaseModel):
    cut: int
    source_file: str
    version: int
    timestamp: str

class Record(BaseModel):
    domain: str
    record_id: str
    data: Dict[str, Any]
    provenance: Provenance
    is_trusted: bool = True

class Correction(BaseModel):
    cut: int
    domain: str
    usubjid: str
    seq: Optional[float] = None
    field: str
    new_value: Any
    reason: Optional[str] = None

class DependencyNode(BaseModel):
    node_id: str
    type: str # 'raw', 'metric', 'finding', etc.
    valid: bool = True
    data: Optional[Any] = None

class Evidence(BaseModel):
    source_file: str
    record_id: Optional[str] = None
    field: Optional[str] = None
    value: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None

class Finding(BaseModel):
    finding_id: str
    finding_type: str
    severity: str
    scope: Dict[str, str]
    evidence: List[Evidence]
    confidence: float
    recommended_action: str
    metadata: Dict[str, Any]

