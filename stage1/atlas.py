import math
from typing import Optional, Dict, Any, List
from app.analysis import (
    find_subjects,
    search_labs,
    detect_saes,
    detect_hys_law,
    detect_dosing_errors,
    detect_visit_deviations,
    detect_prohibited_meds,
    detect_teae,
    detect_exclusion_violations
)
from app.repository import get_subject_data, get_labs, get_adverse_events, get_exposure

def sanitize_nans(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: sanitize_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_nans(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj):
            return None
    return obj

class Atlas:
    """Thin compatibility adapter around the existing Stage 1 API/functionality."""
    
    def get_subject(self, usubjid: str, cut: int) -> Dict[str, Any]:
        data, evidence = get_subject_data(usubjid, cut)
        return sanitize_nans({"data": data, "evidence": evidence})
        
    def get_subject_labs(self, usubjid: str, cut: int) -> Dict[str, Any]:
        data, evidence = get_labs(usubjid, cut)
        return sanitize_nans({"data": data, "evidence": evidence})

    def get_subject_ae(self, usubjid: str, cut: int) -> Dict[str, Any]:
        data, evidence = get_adverse_events(usubjid, cut)
        return sanitize_nans({"data": data, "evidence": evidence})

    def get_subject_ex(self, usubjid: str, cut: int) -> Dict[str, Any]:
        data, evidence = get_exposure(usubjid, cut)
        return sanitize_nans({"data": data, "evidence": evidence})

    def detect_saes(self, cut: int) -> Dict[str, Any]:
        res = detect_saes(cut)
        return sanitize_nans(res)

    def detect_hys_law(self, cut: int) -> Dict[str, Any]:
        res = detect_hys_law(cut)
        return sanitize_nans(res)

    def detect_dosing_errors(self, cut: int) -> Dict[str, Any]:
        res = detect_dosing_errors(cut)
        return sanitize_nans(res)

    def detect_visit_deviations(self, cut: int) -> Dict[str, Any]:
        res = detect_visit_deviations(cut)
        return sanitize_nans(res)

    def detect_prohibited_meds(self, cut: int) -> Dict[str, Any]:
        res = detect_prohibited_meds(cut)
        return sanitize_nans(res)

    def detect_teae(self, cut: int) -> Dict[str, Any]:
        res = detect_teae(cut)
        return sanitize_nans(res)

    def detect_exclusion_violations(self, cut: int) -> Dict[str, Any]:
        res = detect_exclusion_violations(cut)
        return sanitize_nans(res)

