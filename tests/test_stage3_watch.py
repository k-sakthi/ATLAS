import pytest
import os
import pandas as pd
from stage3.watch import StudyWatch

@pytest.fixture
def mock_data_dir(tmp_path):
    df_dm = pd.DataFrame([
        {"USUBJID": "123", "SITEID": "S01", "cut_available": 1},
        {"USUBJID": "124", "SITEID": "S01", "cut_available": 2}
    ])
    df_dm.to_csv(tmp_path / "DM.csv", index=False)
    
    df_corr = pd.DataFrame([
        {"cut": 2, "domain": "DM", "usubjid": "123", "seq": None, "field": "SITEID", "new_value": "S02", "reason": "test"}
    ])
    df_corr.to_csv(tmp_path / "corrections.csv", index=False)
    
    return str(tmp_path)

def test_cut_ingestion(mock_data_dir):
    watch = StudyWatch(mock_data_dir)
    res = watch.process_cut(1)
    
    assert res == "SUCCESS"
    assert "DM" in watch.state.domains
    
    # Check that a record for USUBJID 123 was created
    assert any(k.startswith("raw:DM:123") for k in watch.state.records)
    assert not any(k.startswith("raw:DM:124") for k in watch.state.records)

def test_multiple_cuts(mock_data_dir):
    watch = StudyWatch(mock_data_dir)
    watch.process_cut(1)
    watch.process_cut(2)
    
    assert any(k.startswith("raw:DM:123") for k in watch.state.records)
    assert any(k.startswith("raw:DM:124") for k in watch.state.records)
    
    # Check correction was applied
    rec_id = next(k for k in watch.state.records if k.startswith("raw:DM:123"))
    rec = watch.state.records[rec_id]
    assert rec.data["SITEID"] == "S02"
    assert rec.provenance.version == 2

def test_duplicate_cut(mock_data_dir):
    watch = StudyWatch(mock_data_dir)
    res1 = watch.process_cut(1)
    res2 = watch.process_cut(1)
    
    assert res1 == "SUCCESS"
    assert res2 == "ALREADY_PROCESSED"
