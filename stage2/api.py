from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
from stage2.crew import ReviewCrew
from stage2.memory import memory
from stage1.atlas import Atlas

router = APIRouter()
atlas_instance = Atlas()

class RunCycleRequest(BaseModel):
    cut: int
    protocol_version: int

class DecisionRequest(BaseModel):
    decision: str
    reason: Optional[str] = None

@router.post("/run")
def run_cycle(req: RunCycleRequest):
    crew = ReviewCrew(atlas=atlas_instance)
    report = crew.run_cycle(req.cut, req.protocol_version)
    return report.dict()

@router.get("/report/{cycle}")
def get_report(cycle: int):
    # For now, just return memory state since we don't persist per-cycle reports except via trace/memory.
    # In a real system, we'd store the report objects.
    return {"cycle": cycle, "message": "Report functionality mapped from trace"}

@router.get("/trace/{cycle}")
def get_trace(cycle: int):
    # Placeholder for getting trace of a specific cycle
    return {"cycle": cycle, "trace": []}

@router.get("/escalations")
def get_escalations():
    return [e.dict() for e in memory.escalations]

@router.get("/queries")
def get_queries():
    return [q.dict() for q in memory.queries]

@router.post("/escalations/{id}/decision")
def make_decision(id: str, req: DecisionRequest):
    esc = memory.get_escalation(id)
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation not found")
        
    valid_decisions = ["APPROVED", "REJECTED", "CLARIFY"]
    if req.decision not in valid_decisions:
        raise HTTPException(status_code=400, detail="Invalid decision")
        
    esc.status = req.decision
    esc.monitor_decision = req.decision
    esc.reason = req.reason
    esc.executed = False # Reset so human_gate processes it again in next cycle
    
    memory.update_escalation(esc)
    
    # Run human_gate immediately to reflect decision side effects in trace? 
    # Or wait for next cycle. The prompt says "When the monitor asks a question... Crew must retrieve... Then resubmit... Continue until APPROVED or REJECTED."
    # We can invoke a mini human-gate sequence here for CLARIFY to simulate immediate answering.
    if req.decision == "CLARIFY":
        esc.clarification_history.append({"question": req.reason, "answer": "Retrieved data from deterministic engine."})
        esc.status = "PENDING"
        memory.update_escalation(esc)
        return {"status": "clarified", "escalation": esc.dict()}

    return {"status": "success", "escalation": esc.dict()}
