import pytest
from stage3.watch import StudyWatch
import os

def test_stage3_adapter_parity(tmp_path):
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    watch = StudyWatch(data_dir)
    watch.process_cut(1)
    
    from stage3.adapter import Stage3Adapter
    adapter = Stage3Adapter(watch.state)
    
    # 1. Check a subject isolation
    # Find a known subject from public data
    # Assuming "10001" exists if we load data
    dm_df = adapter.domain_dataframe("DM")
    if not dm_df.empty:
        subject = dm_df.iloc[0]["USUBJID"]
        
        # Test full domain vs isolated
        lb_full = adapter.domain_dataframe("LB")
        lb_isolated = adapter.domain_dataframe("LB", subject)
        
        # Isolated should only have records for subject
        assert len(lb_isolated) > 0
        assert all(lb_isolated["USUBJID"] == subject)
        
        # Columns should match expected structure
        assert "USUBJID" in lb_isolated.columns
        assert "LBTESTCD" in lb_isolated.columns
        
        # Make sure empty domains return empty df safely
        xyz_df = adapter.domain_dataframe("XYZ", subject)
        assert xyz_df.empty
        assert isinstance(xyz_df, type(lb_full))
