import pytest
from stage3.state import generate_record_id, StudyState
from stage3.dependency import DependencyGraph

def test_dynamic_identity_fallback():
    # USUBJID | PARAM | VALUE
    row1 = {"USUBJID": "001", "PARAM": "A", "VALUE": 10}
    row2 = {"USUBJID": "001", "PARAM": "B", "VALUE": 20}
    
    id1 = generate_record_id("XYZ", row1)
    id2 = generate_record_id("XYZ", row2)
    
    # Must remain distinct records
    assert id1 != id2
    assert "PARAM-A" in id1
    assert "PARAM-B" in id2

def test_dynamic_identity_hash_fallback():
    # If no PARAM/VISIT/SEQ exists
    row1 = {"USUBJID": "001", "STABLE_FIELD": "FOO", "VALUE": 10}
    row2 = {"USUBJID": "001", "STABLE_FIELD": "BAR", "VALUE": 20}
    
    id1 = generate_record_id("XYZ", row1)
    id2 = generate_record_id("XYZ", row2)
    
    assert id1 != id2
    assert "HASH" in id1
    assert "HASH" in id2

def test_correction_semantics_historical_state():
    state = StudyState()
    row = {"USUBJID": "123", "LBSEQ": 1, "LBORRES": "10"}
    state.ingest_record("LB", row, 1, "LB.csv")
    
    rec_id = generate_record_id("LB", row)
    
    # Simulate a decision based on version 1
    # In practice this would be stored in the Trace log, we'll store a mock version here
    historical_evidence = state.records[rec_id].data.copy()
    
    # Correction in cut 10
    state.apply_correction(10, "LB", "123", "LBORRES", "20", seq=1)
    
    # Current state is Y (20)
    assert state.records[rec_id].data["LBORRES"] == "20"
    
    # Historical D1 evidence remains X (10)
    assert historical_evidence["LBORRES"] == "10"
    
    # The record provenance must show it's version 2 from cut 10
    assert state.records[rec_id].provenance.version == 2
    assert state.records[rec_id].provenance.cut == 10

def test_cyclic_dependency_protection():
    dag = DependencyGraph()
    dag.add_edge("raw", "A")
    dag.add_edge("A", "B")
    dag.add_edge("B", "A") # Cycle
    
    # Should not infinite loop
    dag.invalidate("raw")
    
    assert not dag.is_valid("raw")
    assert not dag.is_valid("A")
    assert not dag.is_valid("B")

def test_out_of_order_data():
    state = StudyState()
    
    # Arrives in cut 3, but is conceptually older
    row = {"USUBJID": "123", "LBDTC": "2026-01-01"}
    
    # The system must ingest it
    state.ingest_record("LB", row, 3, "LB.csv")
    rec_id = generate_record_id("LB", row)
    
    rec = state.records[rec_id]
    
    # Preserve actual event metadata
    assert rec.data["LBDTC"] == "2026-01-01"
    
    # Associate ingestion provenance with cut 3
    assert rec.provenance.cut == 3
    
    # Not pretend it arrived in Cut 1
    assert rec.provenance.cut != 1

def test_unknown_domain_safely_stored():
    state = StudyState()
    row = {"USUBJID": "999", "PKVAL": 42}
    
    state.ingest_record("PK", row, 2, "PK.csv")
    
    rec_id = generate_record_id("PK", row)
    assert "PK" in state.domains
    assert rec_id in state.records
    assert state.records[rec_id].data["PKVAL"] == 42
