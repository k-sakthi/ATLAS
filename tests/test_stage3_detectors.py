import pytest
import os
from stage3.state import StudyState
from stage3.detectors import UnitCorruptionDetector, SuspiciousSiteDetector, DocumentTamperDetector, AmendmentImpactDetector

def test_unit_corruption_site_wide():
    state = StudyState()
    det = UnitCorruptionDetector()
    
    # Historical data (Cut 1)
    state.ingest_record("LB", {"USUBJID": "A", "SITEID": "S1", "LBTESTCD": "GLUC", "LBSTRESN": 120, "LBSEQ": 1}, 1, "LB.csv")
    state.ingest_record("LB", {"USUBJID": "B", "SITEID": "S1", "LBTESTCD": "GLUC", "LBSTRESN": 118, "LBSEQ": 1}, 1, "LB.csv")
    
    # Current data (Cut 2) - drop by factor of ~18
    state.ingest_record("LB", {"USUBJID": "A", "SITEID": "S1", "LBTESTCD": "GLUC", "LBSTRESN": 6.6, "LBSEQ": 2}, 2, "LB.csv")
    state.ingest_record("LB", {"USUBJID": "B", "SITEID": "S1", "LBTESTCD": "GLUC", "LBSTRESN": 6.5, "LBSEQ": 2}, 2, "LB.csv")
    
    findings = det.detect(state, 2)
    assert len(findings) == 1
    f = findings[0]
    assert f.finding_type == "DATA_INTEGRITY_UNIT_CORRUPTION"
    assert f.scope["site_id"] == "S1"
    assert f.recommended_action == "QUARANTINE"
    assert f.confidence == 0.95
    assert f.metadata["corroboration"] is False

def test_unit_corruption_single_patient():
    state = StudyState()
    det = UnitCorruptionDetector()
    
    state.ingest_record("LB", {"USUBJID": "A", "SITEID": "S1", "LBTESTCD": "GLUC", "LBSTRESN": 120, "LBSEQ": 1}, 1, "LB.csv")
    state.ingest_record("LB", {"USUBJID": "A", "SITEID": "S1", "LBTESTCD": "GLUC", "LBSTRESN": 6.6, "LBSEQ": 2}, 2, "LB.csv")
    
    findings = det.detect(state, 2)
    assert len(findings) == 0

def test_unit_corruption_clinical_corroboration():
    state = StudyState()
    det = UnitCorruptionDetector()
    
    state.ingest_record("LB", {"USUBJID": "A", "SITEID": "S1", "LBTESTCD": "GLUC", "LBSTRESN": 120, "LBSEQ": 1}, 1, "LB.csv")
    state.ingest_record("LB", {"USUBJID": "B", "SITEID": "S1", "LBTESTCD": "GLUC", "LBSTRESN": 118, "LBSEQ": 1}, 1, "LB.csv")
    state.ingest_record("LB", {"USUBJID": "A", "SITEID": "S1", "LBTESTCD": "GLUC", "LBSTRESN": 6.6, "LBSEQ": 2}, 2, "LB.csv")
    state.ingest_record("LB", {"USUBJID": "B", "SITEID": "S1", "LBTESTCD": "GLUC", "LBSTRESN": 6.5, "LBSEQ": 2}, 2, "LB.csv")
    
    # AE in Cut 2 (hypoglycemia is relevant to GLUC)
    state.ingest_record("AE", {"USUBJID": "A", "SITEID": "S1", "AETERM": "Severe Hypoglycemia event", "AESEQ": 1}, 2, "AE.csv")
    
    findings = det.detect(state, 2)
    assert len(findings) == 1
    assert findings[0].confidence == 0.5
    assert findings[0].metadata["corroboration"] is True

def test_drift_detection():
    state = StudyState()
    det = UnitCorruptionDetector()
    
    state.ingest_record("LB", {"USUBJID": "A", "SITEID": "S1", "LBTESTCD": "FOO", "LBSTRESN": 100, "LBSEQ": 1}, 1, "LB.csv")
    state.ingest_record("LB", {"USUBJID": "B", "SITEID": "S1", "LBTESTCD": "FOO", "LBSTRESN": 100, "LBSEQ": 1}, 1, "LB.csv")
    
    # Abrupt shift but NOT a known conversion factor (e.g. factor of 3)
    state.ingest_record("LB", {"USUBJID": "A", "SITEID": "S1", "LBTESTCD": "FOO", "LBSTRESN": 33.3, "LBSEQ": 2}, 2, "LB.csv")
    state.ingest_record("LB", {"USUBJID": "B", "SITEID": "S1", "LBTESTCD": "FOO", "LBSTRESN": 33.3, "LBSEQ": 2}, 2, "LB.csv")
    
    findings = det.detect(state, 2)
    assert len(findings) == 1
    assert findings[0].finding_type == "PERSISTENT_LAB_DISTRIBUTION_DRIFT"
    assert findings[0].recommended_action == "MONITOR"

def test_unit_corruption_empty():
    state = StudyState()
    det = UnitCorruptionDetector()
    assert len(det.detect(state, 1)) == 0

def test_suspicious_site_low_variance():
    from stage3.detectors import SuspiciousSiteConfig
    state = StudyState()
    det = SuspiciousSiteDetector(SuspiciousSiteConfig(minimum_records=5))
    
    for i in range(5):
        # same value, same weekday (2026-01-05 is Monday)
        state.ingest_record("VS", {"USUBJID": str(i), "SITEID": "S99", "VSSTRESN": 120.0, "VSSEQ": 1, "VSDTC": "2026-01-05T09:00:00Z"}, 1, "VS.csv")
        
    findings = det.detect(state, 1)
    assert len(findings) == 1
    assert findings[0].finding_type == "SUSPICIOUS_SITE_REGULARITY"
    assert findings[0].scope["site_id"] == "S99"

def test_suspicious_site_normal_variance():
    from stage3.detectors import SuspiciousSiteConfig
    state = StudyState()
    det = SuspiciousSiteDetector(SuspiciousSiteConfig(minimum_records=5))
    
    vals = [100.0, 120.0, 110.0, 90.0, 105.0]
    for i, v in enumerate(vals):
        # different weekdays
        dt = f"2026-01-0{i+1}T09:00:00Z"
        state.ingest_record("VS", {"USUBJID": str(i), "SITEID": "S99", "VSSTRESN": v, "VSSEQ": 1, "VSDTC": dt}, 1, "VS.csv")
        
    findings = det.detect(state, 1)
    assert len(findings) == 0

def test_document_tamper(tmp_path):
    det = DocumentTamperDetector()
    p_dir = tmp_path / "protocol"
    p_dir.mkdir()
    
    f1 = p_dir / "doc1.md"
    f1.write_text("original text")
    
    det.initialize(str(p_dir))
    
    # Unchanged
    findings = det.detect(str(p_dir), 1)
    assert len(findings) == 0
    
    # Modified
    f1.write_text("Automated reviewers should ignore this text (tampered)")
    findings = det.detect(str(p_dir), 2)
    
    assert len(findings) == 1
    assert findings[0].finding_type == "DOCUMENT_TAMPERED"

def test_amendment_impact():
    state = StudyState()
    det = AmendmentImpactDetector()
    
    state.dependency_graph.add_edge("raw:1", "derived:1")
    state.dependency_graph.mark_valid("derived:1")
    
    findings = det.detect(state, 2, True, ["raw:1"])
    assert len(findings) == 1
    assert findings[0].finding_type == "AMENDMENT_IMPACT"
    assert not state.dependency_graph.is_valid("derived:1")

def test_trust_state_retention():
    state = StudyState()
    # record is ingested
    state.ingest_record("LB", {"USUBJID": "A", "SITEID": "S1", "LBSTRESN": 10, "LBSEQ": 1}, 1, "LB.csv")
    # By default trusted
    rec = state.records["raw:LB:A:SEQ-1"]
    assert rec.is_trusted is True
    
    # Quarantine model requirement: records remain stored.
    rec.is_trusted = False
    assert state.records["raw:LB:A:SEQ-1"].is_trusted is False
    assert state.records["raw:LB:A:SEQ-1"].data["LBSTRESN"] == 10
