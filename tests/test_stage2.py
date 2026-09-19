import pytest
from stage2.crew import ReviewCrew
from stage2.memory import memory, Escalation
from stage1.atlas import Atlas

@pytest.fixture(autouse=True)
def reset_memory():
    memory.queries = []
    memory.escalations = []
    memory.site_flags = []
    memory.subject_flags_history = {}
    memory.cycle_count = 0
    yield

def test_empty_cycle():
    crew = ReviewCrew()
    # Mock atlas to return nothing
    class EmptyAtlas(Atlas):
        def detect_saes(self, cut): return {"data": [], "evidence": []}
        def detect_hys_law(self, cut): return {"data": [], "evidence": []}
        def detect_dosing_errors(self, cut): return {"data": [], "evidence": []}
        def detect_visit_deviations(self, cut): return {"data": [], "evidence": []}
        def detect_prohibited_meds(self, cut): return {"data": [], "evidence": []}
        def detect_teae(self, cut): return {"data": [], "evidence": []}
        def detect_exclusion_violations(self, cut): return {"data": [], "evidence": []}
    
    crew.atlas = EmptyAtlas()
    report = crew.run_cycle(1, 1)
    
    assert report.findings == 0
    assert report.escalations == 0
    assert report.queries == 0
    assert len(report.trace["entries"]) >= 6 # 6 nodes

def test_detect_runs_first():
    crew = ReviewCrew()
    report = crew.run_cycle(1, 1)
    assert len(report.trace["entries"]) >= 6
    assert report.trace["entries"][0]["node"] == "detect"

def test_sae_escalates_same_cycle():
    crew = ReviewCrew()
    class MockAtlas(Atlas):
        def detect_saes(self, cut): 
            return {"data": [{"USUBJID": "001", "AESEQ": 1, "AETERM": "X", "AESER": "Y"}], "evidence": []}
        def detect_hys_law(self, cut): return {"data": [], "evidence": []}
        def detect_dosing_errors(self, cut): return {"data": [], "evidence": []}
        def detect_visit_deviations(self, cut): return {"data": [], "evidence": []}
        def detect_prohibited_meds(self, cut): return {"data": [], "evidence": []}
        def detect_teae(self, cut): return {"data": [], "evidence": []}
        def detect_exclusion_violations(self, cut): return {"data": [], "evidence": []}
    
    crew.atlas = MockAtlas()
    report = crew.run_cycle(1, 1)
    assert report.findings == 1
    assert report.escalations == 1
    
    report2 = crew.run_cycle(1, 1)
    
    sae_escs = [e for e in memory.escalations if e.code == "SAE_DETECTED"]
    assert len(sae_escs) == 1

def test_aeshosp_aeser_miscoded():
    crew = ReviewCrew()
    class MockAtlas(Atlas):
        def detect_saes(self, cut): 
            return {"data": [{"USUBJID": "002", "AESEQ": 2, "AETERM": "Y", "AESER": "N", "AESHOSP": "Y"}], "evidence": []}
        def detect_hys_law(self, cut): return {"data": [], "evidence": []}
        def detect_dosing_errors(self, cut): return {"data": [], "evidence": []}
        def detect_visit_deviations(self, cut): return {"data": [], "evidence": []}
        def detect_prohibited_meds(self, cut): return {"data": [], "evidence": []}
        def detect_teae(self, cut): return {"data": [], "evidence": []}
        def detect_exclusion_violations(self, cut): return {"data": [], "evidence": []}
    
    crew.atlas = MockAtlas()
    crew.run_cycle(1, 1)
    assert memory.escalations[0].code == "SAE_MISCODED"

def test_liver_candidate_monitoring():
    crew = ReviewCrew()
    class MockAtlas(Atlas):
        def detect_saes(self, cut): return {"data": [], "evidence": []}
        def detect_hys_law(self, cut): return {"data": [{"USUBJID": "003", "screening_alt": 50, "baseline_elevated": True}], "evidence": []}
        def detect_dosing_errors(self, cut): return {"data": [], "evidence": []}
        def detect_visit_deviations(self, cut): return {"data": [], "evidence": []}
        def detect_prohibited_meds(self, cut): return {"data": [], "evidence": []}
        def detect_teae(self, cut): return {"data": [], "evidence": []}
        def detect_exclusion_violations(self, cut): return {"data": [], "evidence": []}
    
    crew.atlas = MockAtlas()
    crew.run_cycle(1, 1)
    assert len(memory.escalations) == 0 # Remained monitoring

def test_data_quality_query():
    crew = ReviewCrew()
    class MockAtlas(Atlas):
        def detect_saes(self, cut): return {"data": [], "evidence": []}
        def detect_hys_law(self, cut): return {"data": [], "evidence": []}
        def detect_dosing_errors(self, cut): return {"data": [{"USUBJID": "004", "VISIT": "V1", "EXDOSE": 10}], "evidence": []}
        def detect_visit_deviations(self, cut): return {"data": [], "evidence": []}
        def detect_prohibited_meds(self, cut): return {"data": [], "evidence": []}
        def detect_teae(self, cut): return {"data": [], "evidence": []}
        def detect_exclusion_violations(self, cut): return {"data": [], "evidence": []}
    
    crew.atlas = MockAtlas()
    crew.run_cycle(1, 1)
    assert len(memory.queries) == 1
    assert "004" in memory.queries[0].usubjid
    
    # Run same cycle again, duplicate query prevented
    crew.run_cycle(1, 1)
    assert len(memory.queries) == 1

def test_human_gate_approve_reject_clarify():
    crew = ReviewCrew()
    class MockAtlas(Atlas):
        def detect_saes(self, cut): return {"data": [{"USUBJID": "001", "AESEQ": 1, "AETERM": "X", "AESER": "Y"}], "evidence": []}
        def detect_hys_law(self, cut): return {"data": [], "evidence": []}
        def detect_dosing_errors(self, cut): return {"data": [], "evidence": []}
        def detect_visit_deviations(self, cut): return {"data": [], "evidence": []}
        def detect_prohibited_meds(self, cut): return {"data": [], "evidence": []}
        def detect_teae(self, cut): return {"data": [], "evidence": []}
        def detect_exclusion_violations(self, cut): return {"data": [], "evidence": []}
    
    crew.atlas = MockAtlas()
    crew.run_cycle(1, 1)
    assert len(memory.escalations) == 1
    
    esc = memory.escalations[0]
    
    # Reject
    esc.status = "REJECTED"
    esc.monitor_decision = "REJECTED"
    memory.update_escalation(esc)
    
    crew.run_cycle(1, 1)
    # Should not re-escalate next cycle (status already REJECTED, executed flag set by human_gate)
    
    sae_escs = [e for e in memory.escalations if e.code == "SAE_DETECTED"]
    assert len(sae_escs) == 1
    assert sae_escs[0].status == "REJECTED"
    assert sae_escs[0].executed
    
    # Clarify
    esc = sae_escs[0]
    esc.status = "CLARIFY"
    esc.monitor_decision = "CLARIFY"
    esc.executed = False
    memory.update_escalation(esc)
    
    crew.run_cycle(1, 1)
    
    sae_escs_after = [e for e in memory.escalations if e.code == "SAE_DETECTED"]
    assert sae_escs_after[0].status == "PENDING"
    assert len(sae_escs_after[0].clarification_history) == 1

def test_site_level_flag():
    crew = ReviewCrew()
    class MockAtlas(Atlas):
        def detect_saes(self, cut): return {"data": [], "evidence": []}
        def detect_hys_law(self, cut): return {"data": [], "evidence": []}
        def detect_dosing_errors(self, cut): return {"data": [
            {"USUBJID": "042-S01-001", "VISIT": "V1", "EXDOSE": 10},
            {"USUBJID": "042-S01-002", "VISIT": "V1", "EXDOSE": 10}
        ], "evidence": []}
        def detect_visit_deviations(self, cut): return {"data": [], "evidence": []}
        def detect_prohibited_meds(self, cut): return {"data": [], "evidence": []}
        def detect_teae(self, cut): return {"data": [], "evidence": []}
        def detect_exclusion_violations(self, cut): return {"data": [], "evidence": []}
    
    crew.atlas = MockAtlas()
    crew.run_cycle(1, 1)
    assert len(memory.site_flags) == 1
    assert memory.site_flags[0].siteid == "S01"

