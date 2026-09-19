from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class TraceEntry(BaseModel):
    node: str
    decision: str
    evidence: List[Dict[str, Any]] = []

class Escalation(BaseModel):
    id: str
    code: str
    usubjid: str
    severity: str
    summary: str
    evidence: List[Dict[str, Any]] = []
    alternatives: List[str] = []
    status: str = "PENDING"
    monitor_decision: Optional[str] = None
    reason: Optional[str] = None
    cycle: int
    siteid: Optional[str] = None
    executed: bool = False
    # For keeping track of clarifications
    clarification_history: List[Dict[str, str]] = []

class Query(BaseModel):
    id: str
    usubjid: str
    text: str
    evidence: List[Dict[str, Any]] = []
    status: str = "OPEN"
    cycle: int
    siteid: Optional[str] = None

class SiteFlag(BaseModel):
    siteid: str
    reason: str
    cycle: int

class ReviewReport(BaseModel):
    cycle: int
    cut: int
    protocol_version: int
    findings: int
    escalations: int
    queries: int
    deviations: int
    site_flags: int
    monitor_decisions: int
    trace: Dict[str, Any]
    memory_state: Dict[str, Any]

