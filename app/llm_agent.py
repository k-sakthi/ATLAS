import os
from google import genai
from google.genai import types
from typing import Dict, Any, Optional
import json

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
from app.repository import (
    get_subject_data,
    get_latest_cut
)

def _sanitize(res):
    def clean(x):
        if isinstance(x, dict):
            return {k: clean(v) for k, v in x.items()}
        if isinstance(x, list):
            return [clean(v) for v in x]
        if isinstance(x, float) and x != x:
            return None
        return x
    
    data = clean(res.get("data"))
    evidence = res.get("evidence")
    if hasattr(evidence, "model_dump"):
        evidence = evidence.model_dump()
    return {"data": data, "evidence": clean(evidence), "metadata": res.get("metadata")}

def tool_find_subjects(siteid: str = None, arm: str = None, disposition: str = None, cut: int = None) -> Dict[str, Any]:
    """Finds subjects by site, arm, or disposition at a given cut."""
    return _sanitize(find_subjects(siteid, arm, disposition, cut if cut is not None else get_latest_cut()))

def tool_search_labs(testcd: str = None, min_val: float = None, max_val: float = None, cut: int = None) -> Dict[str, Any]:
    """Searches laboratory records."""
    return _sanitize(search_labs(testcd, min_val, max_val, cut if cut is not None else get_latest_cut()))

def tool_detect_saes(cut: int = None) -> Dict[str, Any]:
    """Detects serious adverse events (SAEs)."""
    return _sanitize(detect_saes(cut if cut is not None else get_latest_cut()))

def tool_detect_hys_law(cut: int = None) -> Dict[str, Any]:
    """Detects potential Hy's Law cases."""
    return _sanitize(detect_hys_law(cut if cut is not None else get_latest_cut()))

def tool_detect_dosing_errors(cut: int = None) -> Dict[str, Any]:
    """Detects dosing errors in exposure data."""
    return _sanitize(detect_dosing_errors(cut if cut is not None else get_latest_cut()))

def tool_detect_visit_deviations(cut: int = None) -> Dict[str, Any]:
    """Detects visit window deviations."""
    return _sanitize(detect_visit_deviations(cut if cut is not None else get_latest_cut()))

def tool_detect_prohibited_meds(cut: int = None) -> Dict[str, Any]:
    """Detects use of prohibited medications."""
    return _sanitize(detect_prohibited_meds(cut if cut is not None else get_latest_cut()))

def tool_detect_teae(cut: int = None) -> Dict[str, Any]:
    """Detects treatment-emergent adverse events (TEAE)."""
    return _sanitize(detect_teae(cut if cut is not None else get_latest_cut()))

def tool_detect_exclusion_violations(cut: int = None) -> Dict[str, Any]:
    """Detects exclusion criteria violations at screening."""
    return _sanitize(detect_exclusion_violations(cut if cut is not None else get_latest_cut()))

def tool_get_subject_data(usubjid: str, cut: int = None) -> Dict[str, Any]:
    """Gets demographics data for a single subject."""
    res, ev = get_subject_data(usubjid, cut if cut is not None else get_latest_cut())
    return _sanitize({"data": res, "evidence": {"records": ev}})

def tool_get_labs(usubjid: str, cut: int = None) -> Dict[str, Any]:
    """Gets lab records for a single subject."""
    from app.repository import get_labs
    res, ev = get_labs(usubjid, cut if cut is not None else get_latest_cut())
    return _sanitize({"data": res, "evidence": {"records": ev}})

def tool_get_adverse_events(usubjid: str, cut: int = None) -> Dict[str, Any]:
    """Gets adverse events for a single subject."""
    from app.repository import get_adverse_events
    res, ev = get_adverse_events(usubjid, cut if cut is not None else get_latest_cut())
    return _sanitize({"data": res, "evidence": {"records": ev}})

def tool_get_exposure(usubjid: str, cut: int = None) -> Dict[str, Any]:
    """Gets exposure/dosing records for a single subject."""
    from app.repository import get_exposure
    res, ev = get_exposure(usubjid, cut if cut is not None else get_latest_cut())
    return _sanitize({"data": res, "evidence": {"records": ev}})

def ask_gemini(question: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return "Gemini is not configured. Set GEMINI_API_KEY in the backend environment."
        
    try:
        model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
        client = genai.Client(api_key=api_key)
        
        tools = [
            tool_find_subjects, tool_search_labs, tool_detect_saes, tool_detect_hys_law,
            tool_detect_dosing_errors, tool_detect_visit_deviations, tool_detect_prohibited_meds,
            tool_detect_teae, tool_detect_exclusion_violations, tool_get_subject_data,
            tool_get_labs, tool_get_adverse_events, tool_get_exposure
        ]
        
        chat = client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction='''You are a clinical data analysis assistant. 
You must NEVER perform calculations, threshold comparisons, or safety exclusions yourself.
Python is the sole source of truth for all deterministic decisions.
Your role is to:
1. Explain deterministic results.
2. Answer questions using the returned structured evidence.
3. Call the provided tools to get data.
4. Summarize findings.
5. Clearly state when medical-monitor adjudication is required.

DO NOT invent clinical information. If a finding is empty, say "No matching deterministic findings were returned for the requested criteria."
If an API/tool fails, say "The deterministic analysis service could not be reached."

For Hy's Law, preserve the exact label "protocol-defined screening signal". Do not describe it as a confirmed diagnosis.
Ground your answers with explicit evidence from the tools (include values, dates, ULN, source files).
S03 and S07 findings excluded by the analysis engine must remain excluded. Do not override the API.
''',
                tools=tools,
            )
        )
        
        response = chat.send_message(question)
        return response.text
    except Exception as e:
        import traceback
        with open("debug_error_agent.txt", "w") as f:
            f.write(f"Exception: {type(e).__name__}\n{str(e)}\n{traceback.format_exc()}")
        return "The deterministic analysis service could not be reached."
