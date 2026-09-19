import pytest
import pandas as pd
from app.repository import apply_cuts_and_corrections
import app.repository as repo
from app.analysis import detect_hys_law, detect_exclusion_violations
import app.analysis as ana
from app.data_loader import normalize_lborres, apply_s07_conversion

def get_s07_mock_datasets():
    # Setup test scenarios
    # 001 = S07 subject, ALT test
    # 002 = non-S07 subject (S01), ALT test
    # 003 = S07 subject, CREAT test
    dm_data = [
        {'USUBJID': '001', 'SITEID': 'S07', 'AGE': 50, 'SCR_HBA1C': 8.0, 'cut_available': 1},
        {'USUBJID': '002', 'SITEID': 'S01', 'AGE': 50, 'SCR_HBA1C': 8.0, 'cut_available': 1},
        {'USUBJID': '003', 'SITEID': 'S07', 'AGE': 50, 'SCR_HBA1C': 8.0, 'cut_available': 1}
    ]
    lb_data = [
        # S07 ALT: original raw 0.5 (converted to 30)
        {'USUBJID': '001', 'LBSEQ': 1, 'LBTESTCD': 'ALT', 'LBORRES': '0.5', 'LBORRES_NUM': 30.0, 'LBORRESU': 'U/L', 'cut_available': 1, 'LBDTC': '2026-01-01', 'VISIT': 'SCREENING'},
        # non-S07 ALT: original 40
        {'USUBJID': '002', 'LBSEQ': 2, 'LBTESTCD': 'ALT', 'LBORRES': '40', 'LBORRES_NUM': 40.0, 'LBORRESU': 'U/L', 'cut_available': 1, 'LBDTC': '2026-01-01', 'VISIT': 'SCREENING'},
        # S07 CREAT: original 1.0 (not multiplied)
        {'USUBJID': '003', 'LBSEQ': 3, 'LBTESTCD': 'CREAT', 'LBORRES': '1.0', 'LBORRES_NUM': 1.0, 'LBORRESU': 'mg/dL', 'cut_available': 1, 'LBDTC': '2026-01-01', 'VISIT': 'SCREENING'},
        
        # BILI for 001 for Hy's Law test
        {'USUBJID': '001', 'LBSEQ': 4, 'LBTESTCD': 'BILI', 'LBORRES': '3.0', 'LBORRES_NUM': 3.0, 'LBORRESU': 'mg/dL', 'cut_available': 1, 'LBDTC': '2026-01-01', 'VISIT': 'SCREENING'}
    ]
    corr_data = [
        # S07 ALT correction cut 2: 0.61 -> should become 36.6
        {'cut': 2, 'domain': 'LB', 'usubjid': '001', 'seq': 1, 'field': 'LBORRES', 'new_value': '0.61', 'reason': 'test A'},
        # S07 ALT correction cut 3: 2.6 (hy's law range) -> should become 156
        {'cut': 3, 'domain': 'LB', 'usubjid': '001', 'seq': 1, 'field': 'LBORRES', 'new_value': '2.6', 'reason': 'test D'},
        # non-S07 ALT correction cut 2: 45 -> should stay 45 (not * 60)
        {'cut': 2, 'domain': 'LB', 'usubjid': '002', 'seq': 2, 'field': 'LBORRES', 'new_value': '45', 'reason': 'test F'},
        # S07 CREAT correction cut 2: 1.1 -> should stay 1.1
        {'cut': 2, 'domain': 'LB', 'usubjid': '003', 'seq': 3, 'field': 'LBORRES', 'new_value': '1.1', 'reason': 'test G'},
    ]
    ref_ranges = [
        {'LBTESTCD': 'ALT', 'LAB': 'CENTRAL', 'HIGH': 50.0},
        {'LBTESTCD': 'AST', 'LAB': 'CENTRAL', 'HIGH': 40.0},
        {'LBTESTCD': 'BILI', 'LAB': 'CENTRAL', 'HIGH': 1.0},
        {'LBTESTCD': 'CREAT', 'LAB': 'CENTRAL', 'HIGH': 1.2}
    ]
    return {
        'DM.csv': pd.DataFrame(dm_data),
        'LB.csv': pd.DataFrame(lb_data),
        'corrections.csv': pd.DataFrame(corr_data),
        'cuts.csv': pd.DataFrame([{'cut': 1, 'protocol_version': 1}, {'cut': 2, 'protocol_version': 1}, {'cut': 3, 'protocol_version': 1}]),
        'reference_ranges.csv': pd.DataFrame(ref_ranges)
    }

def test_s07_correction_conversion(monkeypatch):
    ds = get_s07_mock_datasets()
    monkeypatch.setattr(repo, 'DATASETS', ds)
    
    # Requirement C: Verify correction is NOT applied before its cut (cut 1)
    df_cut1 = apply_cuts_and_corrections(ds['LB.csv'], 'LB.csv', 1)
    assert df_cut1[df_cut1['USUBJID'] == '001']['LBORRES_NUM'].iloc[0] == 30.0
    
    # Requirement A: S07 corrected ALT at cut 2 becomes 36.6
    # Requirement B: Value used from applicable cut
    # Requirement E: Conversion happens exactly once (0.61 * 60 = 36.6)
    df_cut2 = apply_cuts_and_corrections(ds['LB.csv'], 'LB.csv', 2)
    s07_alt_cut2 = df_cut2[df_cut2['USUBJID'] == '001']
    assert s07_alt_cut2['LBORRES_NUM'].iloc[0] == 36.6
    assert s07_alt_cut2['LBORRES'].iloc[0] == '0.61'
    assert s07_alt_cut2['CORRECTION_CUT'].iloc[0] == 2
    assert s07_alt_cut2['S07_CONVERSION_APPLIED'].iloc[0] == 'YES'
    
    # Requirement D: Multiple corrections resolve to latest
    df_cut3 = apply_cuts_and_corrections(ds['LB.csv'], 'LB.csv', 3)
    s07_alt_cut3 = df_cut3[df_cut3['USUBJID'] == '001']
    assert s07_alt_cut3['LBORRES_NUM'].iloc[0] == 156.0 # 2.6 * 60
    assert s07_alt_cut3['CORRECTION_CUT'].iloc[0] == 3
    
    # Requirement F: Non-S07 ALT is NOT multiplied by 60
    s01_alt_cut2 = df_cut2[df_cut2['USUBJID'] == '002']
    assert s01_alt_cut2['LBORRES_NUM'].iloc[0] == 45.0
    if 'S07_CONVERSION_APPLIED' in s01_alt_cut2.columns:
        assert pd.isna(s01_alt_cut2['S07_CONVERSION_APPLIED'].iloc[0])
    
    # Requirement G: S07 non-ALT/AST is NOT multiplied by 60
    s07_creat_cut2 = df_cut2[df_cut2['USUBJID'] == '003']
    assert s07_creat_cut2['LBORRES_NUM'].iloc[0] == 1.1

def test_hys_law_and_exclusion_uses_corrected(monkeypatch):
    ds = get_s07_mock_datasets()
    monkeypatch.setattr(repo, 'DATASETS', ds)
    monkeypatch.setattr(ana, 'DATASETS', ds)
    
    # Requirement H: Exclusions use corrected converted value
    # At cut 1, ALT is 30 (not > 2x ULN which is 100). No exclusion.
    exc_cut1 = detect_exclusion_violations(1)
    # Wait, 001 is S07. S07 is excluded from safety assessments (Hy's law). But what about exclusion violations?
    # exclusion_violations does not call `exclude_safety_sites`. 
    # Let's check: 30 is not > 100.
    assert len(exc_cut1['data']) == 0
    
    # At cut 3, ALT is 156 (> 100). Should be excluded.
    exc_cut3 = detect_exclusion_violations(3)
    assert len(exc_cut3['data']) == 1
    assert exc_cut3['data'][0]['USUBJID'] == '001'
    assert 'ALT_EXCLUSION' in exc_cut3['data'][0]['reasons']
    
    # Requirement I: Evidence contains necessary fields
    evidence = exc_cut3['evidence'].records
    assert len(evidence) > 0
    alt_ev = [e for e in evidence if e.file == 'LB.csv' and e.values.get('LBORRES_NUM') == 156.0][0]
    
    assert alt_ev.row_id['USUBJID'] == '001'
    assert alt_ev.row_id['LBSEQ'] == 1
    assert alt_ev.values['LBORRES'] == '2.6' # Corrected raw value
    assert alt_ev.values['CORRECTION_CUT'] == 3
    assert alt_ev.values['S07_CONVERSION_APPLIED'] == 'YES'
