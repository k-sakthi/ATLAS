from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

class EvidenceDetail(BaseModel):
    file: str
    row_id: Dict[str, Any]
    values: Dict[str, Any]

class EvidenceTrail(BaseModel):
    records: List[EvidenceDetail]

class ApiResponse(BaseModel):
    data: Union[List[Dict[str, Any]], Dict[str, Any]]
    evidence: EvidenceTrail
    metadata: Optional[Dict[str, Any]] = None
