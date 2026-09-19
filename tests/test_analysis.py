import pytest
import pandas as pd
import numpy as np
from app.analysis import (
    exclude_safety_sites, PROTOCOL_WINDOWS, detect_hys_law, detect_saes,
    detect_dosing_errors, detect_visit_deviations, detect_prohibited_meds,
    detect_teae, detect_exclusion_violations
)
import app.repository as repo
from app.data_loader import normalize_lborres, apply_s07_conversion

def get_mock_datasets():
    return {
        'cuts.csv': pd.DataFrame([
            {'cut': 1, 'protocol_version': 1},
            {'cut': 2, 'protocol_version': 2},
            {'cut': 3, 'protocol_version': 3}
        ]),
        'DM.csv': pd.DataFrame([
            {'USUBJID': '001', 'SITEID': 'S01', 'ARM': 'DRUG', 'RFSTDTC': '2026-01-01', 'AGE': 50, 'SCR_HBA1C': 8.0, 'cut_available': 1},
            {'USUBJID': '002', 'SITEID': 'S03', 'ARM': 'DRUG', 'RFSTDTC': '2026-01-01', 'AGE': 50, 'SCR_HBA1C': 8.0, 'cut_available': 1}, # Safety exclusion
            {'USUBJID': '003', 'SITEID': 'S07', 'ARM': 'PLACEBO', 'RFSTDTC': '2026-01-01', 'AGE': 50, 'SCR_HBA1C': 8.0, 'cut_available': 1}, # Safety exclusion
            {'USUBJID': '004', 'SITEID': 'S01', 'ARM': 'PLACEBO', 'RFSTDTC': '2026-01-01', 'AGE': 50, 'SCR_HBA1C': 8.0, 'cut_available': 1},
        ]),
        'reference_ranges.csv': pd.DataFrame([
            {'LBTESTCD': 'ALT', 'LAB': 'CENTRAL', 'HIGH': 50},
            {'LBTESTCD': 'AST', 'LAB': 'CENTRAL', 'HIGH': 40},
            {'LBTESTCD': 'BILI', 'LAB': 'CENTRAL', 'HIGH': 1.0},
            {'LBTESTCD': 'CREAT', 'LAB': 'CENTRAL', 'HIGH': 1.2}
        ]),
        'LB.csv': pd.DataFrame([
            # Hy's law exactly 3x/2x (should not trigger)
            {'USUBJID': '001', 'LBSEQ': 1, 'LBTESTCD': 'ALT', 'LBDTC': '2026-02-01', 'LBORRES_NUM': 150, 'VISIT': 'WEEK4', 'cut_available': 1},
            {'USUBJID': '001', 'LBSEQ': 2, 'LBTESTCD': 'BILI', 'LBDTC': '2026-02-01', 'LBORRES_NUM': 2.0, 'VISIT': 'WEEK4', 'cut_available': 1},
            # Hy's law AST strict > (121 > 120), BILI strict > (2.1 > 2.0) within 14 days
            {'USUBJID': '001', 'LBSEQ': 3, 'LBTESTCD': 'AST', 'LBDTC': '2026-03-01', 'LBORRES_NUM': 121, 'VISIT': 'WEEK8', 'cut_available': 1},
            {'USUBJID': '001', 'LBSEQ': 4, 'LBTESTCD': 'BILI', 'LBDTC': '2026-03-15', 'LBORRES_NUM': 2.1, 'VISIT': 'WEEK12', 'cut_available': 1}, # exactly 14 days
            # Hy's law ALT 15 days apart (should not trigger)
            {'USUBJID': '001', 'LBSEQ': 5, 'LBTESTCD': 'ALT', 'LBDTC': '2026-04-01', 'LBORRES_NUM': 151, 'VISIT': 'WEEK12', 'cut_available': 1},
            {'USUBJID': '001', 'LBSEQ': 6, 'LBTESTCD': 'BILI', 'LBDTC': '2026-04-16', 'LBORRES_NUM': 2.1, 'VISIT': 'WEEK16', 'cut_available': 1},
            # S03 and S07 are excluded, so even if they have Hy's law, it's ignored
            {'USUBJID': '002', 'LBSEQ': 7, 'LBTESTCD': 'ALT', 'LBDTC': '2026-02-01', 'LBORRES_NUM': 151, 'VISIT': 'WEEK4', 'cut_available': 1},
            {'USUBJID': '002', 'LBSEQ': 8, 'LBTESTCD': 'BILI', 'LBDTC': '2026-02-01', 'LBORRES_NUM': 2.1, 'VISIT': 'WEEK4', 'cut_available': 1},
            # Exclusion criteria testing
            {'USUBJID': '004', 'LBSEQ': 9, 'LBTESTCD': 'CREAT', 'LBDTC': '2025-12-15', 'LBORRES_NUM': 1.6, 'VISIT': 'SCREENING', 'cut_available': 1},
            {'USUBJID': '001', 'LBSEQ': 10, 'LBTESTCD': 'ALT', 'LBDTC': '2025-12-15', 'LBORRES_NUM': 101, 'VISIT': 'SCREENING', 'cut_available': 1}, # ALT > 2x ULN
        ]),
        'AE.csv': pd.DataFrame([
            # SAE by AESER=Y
            {'USUBJID': '001', 'AESEQ': 1, 'AESER': 'Y', 'AESHOSP': 'N', 'AESTDTC': '2025-12-01', 'cut_available': 1},
            # SAE by AESHOSP=Y
            {'USUBJID': '001', 'AESEQ': 2, 'AESER': 'N', 'AESHOSP': 'Y', 'AESTDTC': '2026-01-05', 'cut_available': 1},
            # TEAE (onset >= first dose)
            {'USUBJID': '004', 'AESEQ': 3, 'AESER': 'N', 'AESHOSP': 'N', 'AESTDTC': '2026-01-01', 'cut_available': 1} # Onset == First dose (TEAE)
        ]),
        'EX.csv': pd.DataFrame([
            {'USUBJID': '001', 'EXSEQ': 1, 'EXDOSE': 10, 'cut_available': 1}, # DRUG correct
            {'USUBJID': '002', 'EXSEQ': 2, 'EXDOSE': 20, 'cut_available': 1}, # DRUG incorrect
            {'USUBJID': '004', 'EXSEQ': 3, 'EXDOSE': 0, 'cut_available': 1}, # PLACEBO correct
            {'USUBJID': '003', 'EXSEQ': 4, 'EXDOSE': 10, 'cut_available': 1}, # PLACEBO incorrect
        ]),
        'VS.csv': pd.DataFrame([
            {'USUBJID': '001', 'VSSEQ': 1, 'VISIT': 'WEEK2', 'VSDTC': '2026-01-22', 'cut_available': 1}, # 21 days diff (target 14). Deviation for all protocols (7 > window)
            {'USUBJID': '004', 'VSSEQ': 2, 'VISIT': 'WEEK4', 'VSDTC': '2026-02-03', 'cut_available': 1}, # 33 days diff (target 28). Diff = 5.
        ]),
        'CM.csv': pd.DataFrame([
            {'USUBJID': '001', 'CMSEQ': 1, 'CMCLAS': 'SYSTEMIC_GLUCOCORTICOID', 'cut_available': 1},
            {'USUBJID': '004', 'CMSEQ': 2, 'CMCLAS': 'SULFONYLUREA', 'cut_available': 1},
        ])
    }

def test_s03_s07_safety_exclusion(monkeypatch):
    
    import app.analysis as ana
    monkeypatch.setattr(ana, 'DATASETS', get_mock_datasets())
    monkeypatch.setattr(repo, 'DATASETS', get_mock_datasets())
    # 002 (S03) has Hy's Law but should be excluded
    res = detect_hys_law(1)
    assert len(res['data']) == 1 # Only 001 AST+BILI
    assert res['data'][0]['USUBJID'] == '001'
    
    saes = detect_saes(1)
    # 001 has 2 SAEs
    assert len(saes['data']) == 2
    for s in saes['data']:
        assert s['USUBJID'] == '001'

def test_s07_unit_conversion():
    lb_df = pd.DataFrame({'USUBJID': ['001'], 'LBTESTCD': ['ALT'], 'LBORRES_NUM': [1.0], 'LBORRESU': ['ukat/L']})
    dm_df = pd.DataFrame({'USUBJID': ['001'], 'SITEID': ['S07']})
    conv = apply_s07_conversion(lb_df, dm_df)
    assert conv['LBORRES_NUM'].iloc[0] == 60.0
    assert conv['LBORRESU'].iloc[0] == 'U/L'

def test_non_numeric_handling():
    df = pd.DataFrame({'LBORRES': ['<5', 'ND', '', '10']})
    res = normalize_lborres(df)
    assert pd.isna(res['LBORRES_NUM'].iloc[0])
    assert pd.isna(res['LBORRES_NUM'].iloc[1])
    assert pd.isna(res['LBORRES_NUM'].iloc[2])
    assert res['LBORRES_NUM'].iloc[3] == 10.0

def test_hys_law_logic(monkeypatch):
    import app.analysis as ana
    monkeypatch.setattr(ana, 'DATASETS', get_mock_datasets())
    monkeypatch.setattr(repo, 'DATASETS', get_mock_datasets())
    res = detect_hys_law(1)
    data = res['data']
    assert len(data) == 1
    # Check it's the AST case
    assert data[0]['LBTESTCD_HEP'] == 'AST'
    assert data[0]['LBORRES_NUM_HEP'] == 121
    assert data[0]['LBORRES_NUM_BILI'] == 2.1
    # Check 14-day window logic (days_diff is 14)
    assert data[0]['days_diff'] == 14
    
    # Check signal label
    assert res['metadata']['label'] == 'protocol-defined screening signal'

def test_sae_definitions(monkeypatch):
    import app.analysis as ana
    monkeypatch.setattr(ana, 'DATASETS', get_mock_datasets())
    monkeypatch.setattr(repo, 'DATASETS', get_mock_datasets())
    res = detect_saes(1)
    data = res['data']
    assert len(data) == 2
    assert any(x['AESER'] == 'Y' for x in data)
    assert any(x['AESHOSP'] == 'Y' for x in data)

def test_dosing_rules(monkeypatch):
    import app.analysis as ana
    monkeypatch.setattr(ana, 'DATASETS', get_mock_datasets())
    monkeypatch.setattr(repo, 'DATASETS', get_mock_datasets())
    res = detect_dosing_errors(1)
    data = res['data']
    # 002 (DRUG=20), 003 (PLACEBO=10)
    assert len(data) == 2
    assert set([x['USUBJID'] for x in data]) == {'002', '003'}

def test_visit_windows(monkeypatch):
    import app.analysis as ana
    monkeypatch.setattr(ana, 'DATASETS', get_mock_datasets())
    monkeypatch.setattr(repo, 'DATASETS', get_mock_datasets())
    # Cut 1 -> v1 -> window 7
    # 001: 21 days (diff 7, not > 7. wait. 21 - 14 = 7. 7 is NOT > 7. So it shouldn't be flagged in v1?)
    # Wait, 22 Jan - 1 Jan = 21 days. Target 14. 21 - 14 = 7.
    # If window is +/- 7, then 7 is within window. (abs(actual - target) > window). 7 > 7 is False.
    res_v1 = detect_visit_deviations(1)
    # 004 is 33 days, target 28. Diff 5. <= 7, so not flagged in v1.
    assert len(res_v1['data']) == 0
    
    # Cut 2 -> v2 -> window 3
    # 001 diff 7 > 3 => flagged
    # 004 diff 5 > 3 => flagged
    res_v2 = detect_visit_deviations(2)
    assert len(res_v2['data']) == 2

def test_prohibited_meds(monkeypatch):
    import app.analysis as ana
    monkeypatch.setattr(ana, 'DATASETS', get_mock_datasets())
    monkeypatch.setattr(repo, 'DATASETS', get_mock_datasets())
    # Cut 1 -> v1 -> only GLUCOCORTICOID
    res_v1 = detect_prohibited_meds(1)
    assert len(res_v1['data']) == 1
    assert res_v1['data'][0]['CMCLAS'] == 'SYSTEMIC_GLUCOCORTICOID'
    
    # Cut 3 -> v3 -> GLUC and SULF
    res_v3 = detect_prohibited_meds(3)
    assert len(res_v3['data']) == 2
    assert set([x['CMCLAS'] for x in res_v3['data']]) == {'SYSTEMIC_GLUCOCORTICOID', 'SULFONYLUREA'}

def test_teae(monkeypatch):
    import app.analysis as ana
    monkeypatch.setattr(ana, 'DATASETS', get_mock_datasets())
    monkeypatch.setattr(repo, 'DATASETS', get_mock_datasets())
    res = detect_teae(1)
    data = res['data']
    # 001 has AE on 2025-12-01 (before 2026-01-01) -> not TEAE
    # 001 has AE on 2026-01-05 (after 2026-01-01) -> TEAE
    # 004 has AE on 2026-01-01 (equal) -> TEAE
    assert len(data) == 2
    assert set(x['USUBJID'] for x in data) == {'001', '004'}

def test_exclusion_criteria(monkeypatch):
    import app.analysis as ana
    monkeypatch.setattr(ana, 'DATASETS', get_mock_datasets())
    monkeypatch.setattr(repo, 'DATASETS', get_mock_datasets())
    # v1 cut 1
    res_v1 = detect_exclusion_violations(1)
    data_v1 = res_v1['data']
    # 001 has ALT > 2x ULN at SCREENING (101 > 100) -> flagged
    # 004 has CREAT = 1.6, but v1 doesn't care -> not flagged
    assert len(data_v1) == 1
    assert data_v1[0]['USUBJID'] == '001'
    assert 'ALT_EXCLUSION' in data_v1[0]['reasons']
    
    # v2 cut 2
    res_v2 = detect_exclusion_violations(2)
    data_v2 = res_v2['data']
    # 001 flagged for ALT. 004 flagged for CREAT (v2 cares)
    assert len(data_v2) == 2
    creats = [x for x in data_v2 if 'CREAT_EXCLUSION' in x['reasons']]
    assert len(creats) == 1
    assert creats[0]['USUBJID'] == '004'

def test_real_correction_across_cuts(monkeypatch):
    from app.repository import apply_cuts_and_corrections
    
    # Setup dataset with real correction simulated
    ds = {
        'cuts.csv': pd.DataFrame([{'cut': 4, 'protocol_version': 1}, {'cut': 5, 'protocol_version': 2}]),
        'corrections.csv': pd.DataFrame([{
            'cut': 5, 'domain': 'LB', 'usubjid': '008', 'seq': 8, 'field': 'LBORRES_NUM', 'new_value': 25.92
        }]),
        'LB.csv': pd.DataFrame([{
            'USUBJID': '008', 'LBSEQ': 8, 'LBORRES_NUM': 26.5, 'cut_available': 4
        }])
    }
    monkeypatch.setattr(repo, 'DATASETS', ds)
    
    # At cut 4, value should be 26.5
    lb_cut4 = apply_cuts_and_corrections(ds['LB.csv'], 'LB.csv', 4)
    assert lb_cut4['LBORRES_NUM'].iloc[0] == 26.5
    
    # At cut 5, correction applies, value should be 25.92
    lb_cut5 = apply_cuts_and_corrections(ds['LB.csv'], 'LB.csv', 5)
    assert lb_cut5['LBORRES_NUM'].iloc[0] == 25.92
