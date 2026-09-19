from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from stage3.watch import StudyWatch
import os

router = APIRouter()

# Global Watch instance for Stage 3
data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
watch_instance = StudyWatch(data_dir=data_dir)

@router.get("/state")
def get_state():
    return {
        "current_cut": watch_instance.state.current_cut,
        "processed_cuts": watch_instance.state.processed_cuts,
        "total_records": len(watch_instance.state.records),
        "budget": {
            "total": watch_instance.budget.total_budget,
            "consumed": watch_instance.budget.consumed,
            "exhausted": watch_instance.budget.exhausted,
            "degraded_mode": watch_instance.budget.degraded_mode
        },
        "metrics": watch_instance.metrics
    }

@router.post("/process/{cut}")
def process_cut(cut: int):
    result = watch_instance.process_cut(cut)
    # Recompute automatically to match benchmark.py behavior
    watch_instance.recompute_invalidated_nodes()
    return {"status": result, "cut": cut}

@router.post("/process_all")
def process_all():
    watch_instance.run_period(list(range(1, 13)))
    watch_instance.recompute_invalidated_nodes()
    return {"status": "success"}

@router.post("/reset")
def reset_watch():
    global watch_instance
    watch_instance = StudyWatch(data_dir=data_dir)
    return {"status": "reset"}

@router.get("/risks")
def get_risks():
    findings = []
    # Collect from TraceLedger which stores all decisions safely
    for decision in watch_instance.trace.records.values():
        findings.append({
            "finding_id": decision.decision_id,
            "finding_type": decision.decision_type,
            "severity": "HIGH",
            "scope": {"source": "Historical Trace"},
            "evidence": decision.evidence,
            "confidence": 1.0,
            "recommended_action": decision.action,
            "cut": decision.cut,
            "metadata": {}
        })
            
    return findings

@router.get("/escalations")
def get_escalations():
    return [e.model_dump() if hasattr(e, 'model_dump') else e for e in watch_instance.escalations.escalations.values()]

@router.post("/escalations/{esc_id}/response")
def respond_escalation(esc_id: str, response: str):
    watch_instance.escalations.process_human_response(esc_id, watch_instance.state.current_cut, response)
    return {"status": "success"}

@router.get("/adversarial")
def get_adversarial():
    adv_findings = []
    for decision in watch_instance.trace.records.values():
        if decision.decision_type in ['UNIT_CORRUPTION', 'SUSPICIOUS_SITE', 'DOCUMENT_TAMPER', 'AMENDMENT_IMPACT']:
            adv_findings.append({
                "finding_id": decision.decision_id,
                "finding_type": decision.decision_type,
                "recommended_action": decision.action,
                "cut": decision.cut
            })
    
    return {
        "unit_corruption": {"status": "MONITORING", "findings": [f for f in adv_findings if f.get('finding_type') == 'UNIT_CORRUPTION']},
        "suspicious_site": {"status": "MONITORING", "findings": [f for f in adv_findings if f.get('finding_type') == 'SUSPICIOUS_SITE']},
        "document_tamper": {"status": "MONITORING", "findings": [f for f in adv_findings if f.get('finding_type') == 'DOCUMENT_TAMPER']}
    }

@router.get("/corrections")
def get_corrections():
    corrections = []
    for rec in watch_instance.state.records.values():
        if rec.provenance.version > 1:
            corrections.append({
                "domain": rec.domain,
                "record_id": rec.record_id,
                "data": rec.data,
                "version": rec.provenance.version,
                "cut": rec.provenance.cut
            })
    return corrections

@router.get("/trace")
def get_trace():
    return [d.model_dump() if hasattr(d, 'model_dump') else d for d in watch_instance.trace.records.values()]

@router.get("/trace/{decision_id}/explain")
def explain_decision(decision_id: str):
    explanation = watch_instance.explain(decision_id)
    if explanation:
        return explanation.model_dump() if hasattr(explanation, 'model_dump') else explanation
    raise HTTPException(status_code=404, detail="Decision not found")

