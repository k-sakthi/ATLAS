import pytest
import os
import pandas as pd
from stage3.watch import StudyWatch
from stage3.state import StudyState, generate_record_id
from stage3.dependency import DependencyGraph

def test_empty_state():
    state = StudyState()
    assert len(state.records) == 0
    assert len(state.processed_cuts) == 0

def test_duplicate_record():
    state = StudyState()
    row = {"USUBJID": "123", "DMSEQ": 1, "AGE": 50}
    # Ingest twice
    added1 = state.ingest_record("DM", row, 1, "DM.csv")
    added2 = state.ingest_record("DM", row, 1, "DM.csv")
    
    assert added1 is True
    assert added2 is False
    assert len(state.records) == 1

def test_conflicting_record_version():
    state = StudyState()
    row1 = {"USUBJID": "123", "DMSEQ": 1, "AGE": 50}
    row2 = {"USUBJID": "123", "DMSEQ": 1, "AGE": 51} # Conflict
    
    state.ingest_record("DM", row1, 1, "DM.csv")
    rec_id = generate_record_id("DM", row1)
    assert state.records[rec_id].provenance.version == 1
    
    added2 = state.ingest_record("DM", row2, 2, "DM.csv")
    assert added2 is True
    assert state.records[rec_id].data["AGE"] == 51
    assert state.records[rec_id].provenance.version == 2
    assert state.records[rec_id].provenance.cut == 2

def test_new_site_and_domain():
    state = StudyState()
    row = {"USUBJID": "S99-001", "SITEID": "S99", "VAL": 10}
    state.ingest_record("NEWDOM", row, 1, "NEWDOM.csv")
    
    assert "S99" in state.sites
    assert "NEWDOM" in state.domains

def test_correction_updates_record():
    state = StudyState()
    row = {"USUBJID": "123", "LBSEQ": 1, "LBORRES": "10"}
    state.ingest_record("LB", row, 1, "LB.csv")
    rec_id = generate_record_id("LB", row)
    
    updated = state.apply_correction(cut=2, domain="LB", usubjid="123", seq=1, field="LBORRES", new_value="20")
    
    assert updated is True
    assert state.records[rec_id].data["LBORRES"] == "20"
    assert state.records[rec_id].provenance.version == 2
    assert state.records[rec_id].data["CORRECTION_CUT"] == 2

def test_recursive_invalidation():
    dag = DependencyGraph()
    dag.add_edge("raw:1", "derived:1")
    dag.add_edge("derived:1", "finding:1")
    
    assert dag.is_valid("finding:1")
    dag.invalidate("raw:1")
    
    assert not dag.is_valid("raw:1")
    assert not dag.is_valid("derived:1")
    assert not dag.is_valid("finding:1")

def test_invalidation_idempotent():
    dag = DependencyGraph()
    dag.add_edge("raw:1", "derived:1")
    
    dag.invalidate("raw:1")
    assert not dag.is_valid("raw:1")
    
    # Should not crash or infinite loop
    dag.invalidate("raw:1")
    assert not dag.is_valid("raw:1")

def test_correction_invalidates_dependents():
    state = StudyState()
    row = {"USUBJID": "123", "LBSEQ": 1, "LBORRES": "10"}
    state.ingest_record("LB", row, 1, "LB.csv")
    rec_id = generate_record_id("LB", row)
    
    state.dependency_graph.add_edge(rec_id, "derived_hys_law")
    
    state.apply_correction(cut=2, domain="LB", usubjid="123", seq=1, field="LBORRES", new_value="20")
    assert not state.dependency_graph.is_valid("derived_hys_law")

def test_provenance():
    state = StudyState()
    row = {"USUBJID": "123"}
    state.ingest_record("DM", row, 3, "DM.csv")
    
    rec_id = generate_record_id("DM", row)
    prov = state.records[rec_id].provenance
    assert prov.cut == 3
    assert prov.source_file == "DM.csv"
    assert prov.version == 1
    assert prov.timestamp is not None

def test_out_of_order_record():
    state = StudyState()
    row = {"USUBJID": "123"}
    # Arrives in cut 3, but is conceptually older, handled gracefully
    state.ingest_record("DM", row, 3, "DM.csv")
    rec_id = generate_record_id("DM", row)
    assert rec_id in state.records

