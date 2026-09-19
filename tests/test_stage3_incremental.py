import pytest
from stage3.watch import StudyWatch
import os

def test_incremental_isolation(tmp_path):
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    watch = StudyWatch(data_dir)
    
    # Run Cut 1
    watch.process_cut(1)
    watch.recompute_invalidated_nodes()
    
    # Grab initial metrics
    initial_recomputed = watch.metrics["recomputed_nodes"]
    
    # Now we inject a correction for a SPECIFIC subject
    dm_df = watch.state.records
    # Just find any valid LB record
    lb_records = [r for r in watch.state.records.values() if r.domain == "LB"]
    if not lb_records:
        pytest.skip("No LB records found in public data")
        
    target_record = lb_records[0]
    subject = target_record.data["USUBJID"]
    seq = target_record.data.get("LBSEQ")
    
    # Assert DAG is fully valid before
    assert all(watch.state.dependency_graph.validity.values())
    
    # Apply correction
    watch.state.apply_correction(2, "LB", subject, "LBORRES", 999.9, seq)
    
    # Assert DAG is partially invalid
    assert not all(watch.state.dependency_graph.validity.values())
    
    # Recompute
    watch.recompute_invalidated_nodes()
    
    # Assert isolation
    # Only the nodes tied to this subject's LB record should have been invalidated and recomputed
    delta_recomputed = watch.metrics["recomputed_nodes"] - initial_recomputed
    assert delta_recomputed > 0
    # If it was O(N), delta would be thousands. Since it's O(delta), it should be very small (e.g., 1-10)
    assert delta_recomputed < 100 
    
    # Assert the DAG is valid again
    assert all(watch.state.dependency_graph.validity.values())
