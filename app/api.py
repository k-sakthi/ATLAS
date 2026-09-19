from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Any
from app.repository import (
    get_subject_data, get_labs, get_adverse_events, get_exposure, get_latest_cut
)
from app.analysis import (
    find_subjects, search_labs, detect_saes, detect_hys_law, detect_dosing_errors, detect_visit_deviations
)
from app.schemas import ApiResponse, EvidenceTrail
import math

router = APIRouter()

def sanitize_nans(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: sanitize_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_nans(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj):
            return None
    return obj

def add_dosing_context(records: Any) -> Any:
    if not isinstance(records, list):
        return records

    enriched = []
    for rec in records:
        if not isinstance(rec, dict):
            enriched.append(rec)
            continue

        row = dict(rec)
        arm = row.get("ARM")
        if arm == "DRUG":
            row["expected_dose"] = 10
        elif arm == "PLACEBO":
            row["expected_dose"] = 0

        if "expected_dose" in row:
            row["expected_dose_unit"] = row.get("EXDOSU") or "mg"
            row["reason"] = (
                f"{arm} arm expected dose is {row['expected_dose']} {row['expected_dose_unit']}; "
                f"administered dose was {row.get('EXDOSE')} {row.get('EXDOSU') or row['expected_dose_unit']}."
            )

        if row.get("USUBJID") and not row.get("SITEID"):
            parts = str(row["USUBJID"]).split("-")
            if len(parts) >= 2:
                row["SITEID"] = parts[1]

        enriched.append(row)

    return enriched

@router.get("/subjects/{usubjid}", response_model=ApiResponse)
def get_subject(usubjid: str, cut: Optional[int] = Query(None)):
    target_cut = cut if cut is not None else get_latest_cut()
    data, evidence = get_subject_data(usubjid, target_cut)
    
    if not data:
        raise HTTPException(status_code=404, detail="Subject not found")
        
    return ApiResponse(
        data=sanitize_nans(data),
        evidence=EvidenceTrail(records=sanitize_nans(evidence))
    )

@router.get("/subjects/{usubjid}/labs", response_model=ApiResponse)
def get_subject_labs(usubjid: str, cut: Optional[int] = Query(None)):
    target_cut = cut if cut is not None else get_latest_cut()
    data, evidence = get_labs(usubjid, target_cut)
    return ApiResponse(
        data=sanitize_nans(data),
        evidence=EvidenceTrail(records=sanitize_nans(evidence))
    )

@router.get("/subjects/{usubjid}/adverse_events", response_model=ApiResponse)
def get_subject_ae(usubjid: str, cut: Optional[int] = Query(None)):
    target_cut = cut if cut is not None else get_latest_cut()
    data, evidence = get_adverse_events(usubjid, target_cut)
    return ApiResponse(
        data=sanitize_nans(data),
        evidence=EvidenceTrail(records=sanitize_nans(evidence))
    )

@router.get("/subjects/{usubjid}/exposure", response_model=ApiResponse)
def get_subject_ex(usubjid: str, cut: Optional[int] = Query(None)):
    target_cut = cut if cut is not None else get_latest_cut()
    data, evidence = get_exposure(usubjid, target_cut)
    return ApiResponse(
        data=sanitize_nans(data),
        evidence=EvidenceTrail(records=sanitize_nans(evidence))
    )

@router.get("/analysis/subjects", response_model=ApiResponse)
def get_analysis_subjects(siteid: Optional[str] = None, arm: Optional[str] = None, disposition: Optional[str] = None, cut: Optional[int] = Query(None)):
    target_cut = cut if cut is not None else get_latest_cut()
    result = find_subjects(siteid, arm, disposition, target_cut)
    return ApiResponse(
        data=sanitize_nans(result["data"]),
        evidence=result["evidence"]
    )

@router.get("/analysis/labs", response_model=ApiResponse)
def get_analysis_labs(testcd: Optional[str] = None, min_val: Optional[float] = None, max_val: Optional[float] = None, cut: Optional[int] = Query(None)):
    target_cut = cut if cut is not None else get_latest_cut()
    result = search_labs(testcd, min_val, max_val, target_cut)
    return ApiResponse(
        data=sanitize_nans(result["data"]),
        evidence=result["evidence"]
    )

@router.get("/analysis/sae", response_model=ApiResponse)
def get_analysis_sae(cut: Optional[int] = Query(None)):
    target_cut = cut if cut is not None else get_latest_cut()
    result = detect_saes(target_cut)
    return ApiResponse(
        data=sanitize_nans(result["data"]),
        evidence=result["evidence"]
    )

@router.get("/analysis/hys_law", response_model=ApiResponse)
def get_analysis_hys_law(cut: Optional[int] = Query(None)):
    target_cut = cut if cut is not None else get_latest_cut()
    result = detect_hys_law(target_cut)
    return ApiResponse(
        data=sanitize_nans(result["data"]),
        evidence=result["evidence"],
        metadata=result.get("metadata")
    )

@router.get("/analysis/dosing_errors", response_model=ApiResponse)
def get_analysis_dosing_errors(cut: Optional[int] = Query(None)):
    target_cut = cut if cut is not None else get_latest_cut()
    result = detect_dosing_errors(target_cut)
    records = add_dosing_context(sanitize_nans(result["data"]))
    evidence_records = add_dosing_context([
        {
            "file": e.file,
            "row_id": e.row_id,
            "values": add_dosing_context([e.values])[0]
        }
        for e in result["evidence"].records
    ])
    return ApiResponse(
        data=records,
        evidence=EvidenceTrail(records=sanitize_nans(evidence_records))
    )

@router.get("/analysis/visit_deviations", response_model=ApiResponse)
def get_analysis_visit_deviations(cut: Optional[int] = Query(None)):
    target_cut = cut if cut is not None else get_latest_cut()
    result = detect_visit_deviations(target_cut)
    return ApiResponse(
        data=sanitize_nans(result["data"]),
        evidence=result["evidence"]
    )

from app.analysis import detect_prohibited_meds, detect_teae, detect_exclusion_violations

@router.get("/analysis/prohibited_meds", response_model=ApiResponse)
def api_prohibited_meds(cut: Optional[int] = Query(None)):
    target_cut = cut if cut is not None else get_latest_cut()
    result = detect_prohibited_meds(target_cut)
    return ApiResponse(
        data=sanitize_nans(result["data"]),
        evidence=result["evidence"]
    )

@router.get("/analysis/teae", response_model=ApiResponse)
def api_teae(cut: Optional[int] = Query(None)):
    target_cut = cut if cut is not None else get_latest_cut()
    result = detect_teae(target_cut)
    return ApiResponse(
        data=sanitize_nans(result["data"]),
        evidence=result["evidence"]
    )

@router.get("/analysis/exclusion_violations", response_model=ApiResponse)
def get_analysis_exclusion_violations(cut: Optional[int] = Query(None)):
    target_cut = cut if cut is not None else get_latest_cut()
    result = detect_exclusion_violations(target_cut)
    return ApiResponse(
        data=sanitize_nans(result["data"]),
        evidence=result["evidence"]
    )

from pydantic import BaseModel
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str

@router.post("/chat", response_model=ChatResponse)
def chat_with_agent(req: ChatRequest):
    from app.llm_agent import ask_gemini
    try:
        answer = ask_gemini(req.question)
        return ChatResponse(answer=answer)
    except Exception as e:
        import traceback
        with open("debug_error.txt", "w") as f:
            f.write(f"Exception: {type(e).__name__}\n{str(e)}\n{traceback.format_exc()}")
        return ChatResponse(answer="The deterministic analysis service could not be reached.")
