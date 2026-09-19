import uuid
import copy
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime

class TraceRecord(BaseModel):
    decision_id: str
    cut: int
    timestamp: str
    decision_type: str
    action: str
    what: str
    evidence: List[Any]
    evidence_lines: List[str]
    alternatives: List[str]
    why: str
    policy: str
    status: str
    trace_version: int = 1

class TraceLedger:
    def __init__(self):
        self.records: Dict[str, TraceRecord] = {}
        
    def add_decision(self, cut: int, decision_type: str, action: str, what: str, evidence: List[Any], why: str, policy: str) -> str:
        dec_id = f"DEC-CUT{cut:02d}-{uuid.uuid4().hex[:8]}"
        
        # Deep copy evidence to make it immutable snapshot
        imm_evidence = copy.deepcopy(evidence)
        
        record = TraceRecord(
            decision_id=dec_id,
            cut=cut,
            timestamp=datetime.utcnow().isoformat(),
            decision_type=decision_type,
            action=action,
            what=what,
            evidence=imm_evidence,
            evidence_lines=[f"{type(e).__name__}: {str(e)}" for e in imm_evidence],
            alternatives=[],
            why=why,
            policy=policy,
            status="COMMITTED"
        )
        self.records[dec_id] = record
        return dec_id
        
    def get_decision(self, decision_id: str) -> TraceRecord:
        if decision_id not in self.records:
            raise ValueError(f"Decision {decision_id} not found in trace.")
        return self.records[decision_id]

class Explanation(BaseModel):
    decision_id: str
    historical_cut: int
    action: str
    what: str
    why: str
    policy: str
    evidence_snapshot: List[Any]
