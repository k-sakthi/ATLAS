import pytest
from stage3.watch import StudyWatch
import os
import pandas as pd

def test_correction_reversal(tmp_path):
    watch = StudyWatch(str(tmp_path))
    
    # We will mock the reference ranges manually since we are using tmp_path without full data
    from app.data_loader import DATASETS
    DATASETS["reference_ranges.csv"] = pd.DataFrame([
        {'LBTESTCD': 'ALT', 'LAB': 'CENTRAL', 'HIGH': 50.0},
        {'LBTESTCD': 'AST', 'LAB': 'CENTRAL', 'HIGH': 40.0},
        {'LBTESTCD': 'BILI', 'LAB': 'CENTRAL', 'HIGH': 1.0}
    ])
    
    # CUT 2: Inject data that triggers Hy's Law
    # AST/ALT > 3x ULN, BILI > 2x ULN
    watch.state.ingest_record("DM", {"USUBJID": "SUBJ_X", "SITEID": "S01", "AGE": 45, "RFSTDTC": "2026-01-01", "ARM": "DRUG", "SCR_HBA1C": 5.0}, 2, "DM.csv")
    watch.state.ingest_record("LB", {"USUBJID": "SUBJ_X", "LBSEQ": 1, "LBTESTCD": "ALT", "LBORRES_NUM": 200.0, "LBDTC": "2026-01-01", "VISIT": "SCREENING"}, 2, "LB.csv")
    watch.state.ingest_record("LB", {"USUBJID": "SUBJ_X", "LBSEQ": 2, "LBTESTCD": "BILI", "LBORRES_NUM": 3.0, "LBDTC": "2026-01-01", "VISIT": "SCREENING"}, 2, "LB.csv")
    
    from stage3.adapter import Stage3Adapter
    adapter = Stage3Adapter(watch.state)
    print("DM DF:\n", adapter.domain_dataframe("DM", "SUBJ_X"))
    print("LB DF:\n", adapter.domain_dataframe("LB", "SUBJ_X"))
    import app.analysis as ana
    original = ana.apply_cuts_and_corrections
    ana.apply_cuts_and_corrections = lambda df, fn, cut: adapter.domain_dataframe(fn.replace('.csv', ''), "SUBJ_X")
    print("HYS_LAW:", ana.detect_hys_law(2))
    ana.apply_cuts_and_corrections = original

    # Recompute triggers detection
    findings_cut2 = watch.recompute_invalidated_nodes()
    print("FINDINGS CUT 2:", findings_cut2)
    # It should have found HYS_LAW
    assert any(f.finding_type == "CLINICAL_HYS_LAW" for f in findings_cut2)
    
    # Manually trace it for testing
    hys_finding = next(f for f in findings_cut2 if f.finding_type == "CLINICAL_HYS_LAW")
    dec_id = watch.trace.add_decision(2, hys_finding.finding_type, "REVIEW", "SCOPE", [{"data": 200.0}], "test", "test")
    
    # CUT 3: Unrelated data
    watch.state.ingest_record("DM", {"USUBJID": "SUBJ_Y", "SITEID": "S01", "AGE": 50, "RFSTDTC": "2026-01-01", "ARM": "PLACEBO", "SCR_HBA1C": 5.0}, 3, "DM.csv")
    findings_cut3 = watch.recompute_invalidated_nodes()
    
    # CUT 5: Correction removes condition
    # ALT corrected to 40.0 (below 3x ULN)
    watch.state.apply_correction(5, "LB", "SUBJ_X", "LBORRES_NUM", 40.0, 1)
    
    # Recompute
    findings_cut5 = watch.recompute_invalidated_nodes()
    
    # The condition should no longer exist in the new findings set
    current_clinical = watch.state.current_clinical_findings.get("SUBJ_X", [])
    assert not any(f['type'] == 'HYS_LAW' for f in current_clinical)
    
    # BUT trace remains unchanged!
    expl = watch.explain(dec_id)
    assert expl.evidence_snapshot[0]["data"] == 200.0
