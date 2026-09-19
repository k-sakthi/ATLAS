import pytest
from stage2.crew import ReviewCrew
from stage2.memory import memory, Memory
from stage1.atlas import Atlas

@pytest.fixture(autouse=True)
def reset_memory():
    memory.queries = []
    memory.escalations = []
    memory.site_flags = []
    memory.subject_flags_history = {}
    memory.cycle_count = 0
    yield

class BaseMockAtlas(Atlas):
    def detect_saes(self, cut): return {"data": [], "evidence": []}
    def detect_hys_law(self, cut): return {"data": [], "evidence": []}
    def detect_dosing_errors(self, cut): return {"data": [], "evidence": []}
    def detect_visit_deviations(self, cut): return {"data": [], "evidence": []}
    def detect_prohibited_meds(self, cut): return {"data": [], "evidence": []}
    def detect_teae(self, cut): return {"data": [], "evidence": []}
    def detect_exclusion_violations(self, cut): return {"data": [], "evidence": []}
    def get_subject_labs(self, usubjid, cut): return {"data": [], "evidence": []}

def test_empty_cycle():
    crew = ReviewCrew()
    crew.atlas = BaseMockAtlas()
    report = crew.run_cycle(1, 1)
    
    assert report.findings == 0
    assert report.escalations == 0
    assert report.queries == 0
    assert len(report.trace["entries"]) >= 6 # 6 nodes

def test_clarify_graph_lookup():
    crew = ReviewCrew()
    class MockAtlas(BaseMockAtlas):
        def detect_saes(self, cut): 
            return {"data": [{"USUBJID": "001", "AESEQ": 1, "AETERM": "X", "AESER": "Y"}], "evidence": []}
        def get_subject_labs(self, usubjid, cut):
            if usubjid == "001":
                return {"data": [{"USUBJID": "001", "LBTESTCD": "ALT", "VISIT": "SCREENING", "LBSTRESN": 50}], "evidence": []}
            return {"data": [], "evidence": []}
            
    crew.atlas = MockAtlas()
    crew.run_cycle(1, 1) # Detects SAE, escalates
    esc = memory.escalations[0]
    
    # Request Clarify
    esc.status = "CLARIFY"
    esc.reason = "What is the screening ALT?"
    esc.executed = False
    memory.update_escalation(esc)
    
    crew.run_cycle(1, 1)
    # Check if answer contains 50
    assert memory.escalations[0].status == "PENDING"
    ans = memory.escalations[0].clarification_history[-1]["answer"]
    assert "50" in ans

def test_clarify_missing_info():
    crew = ReviewCrew()
    class MockAtlas(BaseMockAtlas):
        def detect_saes(self, cut): 
            return {"data": [{"USUBJID": "001", "AESEQ": 1, "AETERM": "X", "AESER": "Y"}], "evidence": []}
            
    crew.atlas = MockAtlas()
    crew.run_cycle(1, 1) # Detects SAE, escalates
    esc = memory.escalations[0]
    
    # Request Clarify with something unanswerable
    esc.status = "CLARIFY"
    esc.reason = "What is the random weird value?"
    esc.executed = False
    memory.update_escalation(esc)
    
    crew.run_cycle(1, 1)
    ans = memory.escalations[0].clarification_history[-1]["answer"]
    assert "does not contain sufficient evidence" in ans

def test_recurring_subject_across_two_cycles():
    crew = ReviewCrew()
    class MockAtlas(BaseMockAtlas):
        def detect_teae(self, cut):
            return {"data": [{"USUBJID": "REC-001"}], "evidence": []}
            
    crew.atlas = MockAtlas()
    crew.run_cycle(1, 1) # Cycle 1: Subject flagged, but not an escalation by itself
    assert len(memory.escalations) == 0
    
    crew.run_cycle(1, 1) # Cycle 2: Same subject flagged again
    assert len(memory.escalations) == 1
    assert memory.escalations[0].code == "SUBJECT_RECURRING_FINDINGS"

def test_site_level_dosing_escalation():
    crew = ReviewCrew()
    class MockAtlas(BaseMockAtlas):
        def detect_dosing_errors(self, cut): return {"data": [
            {"USUBJID": "042-S01-001", "VISIT": "V1", "EXDOSE": 10},
            {"USUBJID": "042-S01-002", "VISIT": "V1", "EXDOSE": 10}
        ], "evidence": []}
        
    crew.atlas = MockAtlas()
    crew.run_cycle(1, 1)
    
    # Expect 1 site flag and 1 site escalation
    assert len(memory.site_flags) == 1
    site_escs = [e for e in memory.escalations if e.code == "SITE_RECURRING_DOSING"]
    assert len(site_escs) == 1
    
    # Next cycle should not duplicate
    crew.run_cycle(1, 1)
    site_escs_after = [e for e in memory.escalations if e.code == "SITE_RECURRING_DOSING"]
    assert len(site_escs_after) == 1

def test_rejected_escalation_not_repeated():
    crew = ReviewCrew()
    class MockAtlas(BaseMockAtlas):
        def detect_saes(self, cut): 
            return {"data": [{"USUBJID": "001", "AESEQ": 1, "AETERM": "X", "AESER": "Y"}], "evidence": []}
            
    crew.atlas = MockAtlas()
    crew.run_cycle(1, 1) # Cycle 1
    
    esc = memory.escalations[0]
    esc.status = "REJECTED"
    memory.update_escalation(esc)
    
    crew.run_cycle(1, 1) # Cycle 2
    
    sae_escs = [e for e in memory.escalations if e.code == "SAE_DETECTED"]
    assert len(sae_escs) == 1
    assert sae_escs[0].status == "REJECTED"

def test_trace_order_and_evidence():
    crew = ReviewCrew()
    class MockAtlas(BaseMockAtlas):
        def detect_dosing_errors(self, cut): return {"data": [
            {"USUBJID": "042-S01-001", "VISIT": "V1", "EXDOSE": 10},
            {"USUBJID": "042-S01-002", "VISIT": "V1", "EXDOSE": 10}
        ], "evidence": []}
        
    crew.atlas = MockAtlas()
    report = crew.run_cycle(1, 1)
    entries = report.trace["entries"]
    
    nodes = [e["node"] for e in entries]
    # Check sequence
    expected_sequence = ["detect", "medical_review", "data_manager", "compliance", "human_gate", "execute"]
    
    # We might have multiple traces for the same node, but the overall progression should be ordered
    node_indices = {n: [i for i, v in enumerate(nodes) if v == n] for n in expected_sequence}
    
    assert min(node_indices["detect"]) < min(node_indices["medical_review"])
    assert min(node_indices["medical_review"]) < min(node_indices["data_manager"])
    assert min(node_indices["data_manager"]) < min(node_indices["compliance"])
    assert min(node_indices["compliance"]) < min(node_indices["human_gate"])
    assert min(node_indices["human_gate"]) < min(node_indices["execute"])
    
    # Look for site escalation trace in data manager
    data_manager_traces = [e["decision"] for e in entries if e["node"] == "data_manager"]
    assert any("site escalation created for S01" in t for t in data_manager_traces)
