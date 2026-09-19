import pytest
import pandas as pd
import numpy as np
from app.data_loader import normalize_lborres, apply_s07_conversion
from app.repository import apply_cuts_and_corrections

def test_normalize_lborres():
    df = pd.DataFrame({
        'LBORRES': ['10.5', '<5', 'ND', '', 'NaN', 'None', '42']
    })
    result = normalize_lborres(df)
    
    assert result['LBORRES_NUM'].iloc[0] == 10.5
    assert np.isnan(result['LBORRES_NUM'].iloc[1])
    assert np.isnan(result['LBORRES_NUM'].iloc[2])
    assert np.isnan(result['LBORRES_NUM'].iloc[3])
    assert np.isnan(result['LBORRES_NUM'].iloc[4])
    assert np.isnan(result['LBORRES_NUM'].iloc[5])
    assert result['LBORRES_NUM'].iloc[6] == 42.0

@pytest.mark.skip(reason="Legacy S07 hardcoding removed in Stage 3.")
def test_apply_s07_conversion():
    lb_df = pd.DataFrame({
        'USUBJID': ['001', '002', '003'],
        'LBTESTCD': ['ALT', 'AST', 'GLUC'],
        'LBORRES_NUM': [2.0, 1.5, 100.0],
        'LBORRESU': ['µkat/L', 'µkat/L', 'mg/dL']
    })
    
    dm_df = pd.DataFrame({
        'USUBJID': ['001', '002', '003'],
        'SITEID': ['S07', 'S07', 'S07']
    })
    
    result = apply_s07_conversion(lb_df, dm_df)
    
    # 001 is S07 ALT -> should be 2.0 * 60 = 120.0
    assert result.loc[0, 'LBORRES_NUM'] == 120.0
    assert result.loc[0, 'LBORRESU'] == 'U/L'
    
    # 002 is S07 AST -> should be 1.5 * 60 = 90.0
    assert result.loc[1, 'LBORRES_NUM'] == 90.0
    assert result.loc[1, 'LBORRESU'] == 'U/L'
    
    # 003 is S07 GLUC -> should not be converted
    assert result.loc[2, 'LBORRES_NUM'] == 100.0
    assert result.loc[2, 'LBORRESU'] == 'mg/dL'

def test_apply_cuts_and_corrections(monkeypatch):
    import app.repository as repo
    
    # Mock DATASETS
    mock_datasets = {
        'LB.csv': pd.DataFrame({
            'USUBJID': ['101', '101'],
            'LBSEQ': [1, 2],
            'LBORRES': ['10', '20'],
            'LBORRES_NUM': [10.0, 20.0],
            'cut_available': [1, 3]
        }),
        'corrections.csv': pd.DataFrame({
            'cut': [2, 4],
            'domain': ['LB', 'LB'],
            'usubjid': ['101', '101'],
            'seq': [1, 2],
            'field': ['LBORRES', 'LBORRES'],
            'new_value': [15.0, 25.0]
        })
    }
    
    monkeypatch.setattr(repo, 'DATASETS', mock_datasets)
    
    # Cut 1: Should only see seq 1, no corrections
    df_cut1 = repo.apply_cuts_and_corrections(mock_datasets['LB.csv'], 'LB.csv', 1)
    assert len(df_cut1) == 1
    assert df_cut1['LBORRES_NUM'].iloc[0] == 10.0
    
    # Cut 2: Should see seq 1, with correction
    df_cut2 = repo.apply_cuts_and_corrections(mock_datasets['LB.csv'], 'LB.csv', 2)
    assert len(df_cut2) == 1
    assert df_cut2['LBORRES_NUM'].iloc[0] == 15.0
    
    # Cut 3: Should see seq 1 (corrected) and seq 2 (no correction yet)
    df_cut3 = repo.apply_cuts_and_corrections(mock_datasets['LB.csv'], 'LB.csv', 3)
    assert len(df_cut3) == 2
    assert df_cut3.loc[df_cut3['LBSEQ'] == 1, 'LBORRES_NUM'].iloc[0] == 15.0
    assert df_cut3.loc[df_cut3['LBSEQ'] == 2, 'LBORRES_NUM'].iloc[0] == 20.0
    
    # Cut 4: Should see seq 1 (corrected) and seq 2 (corrected)
    df_cut4 = repo.apply_cuts_and_corrections(mock_datasets['LB.csv'], 'LB.csv', 4)
    assert len(df_cut4) == 2
    assert df_cut4.loc[df_cut4['LBSEQ'] == 1, 'LBORRES_NUM'].iloc[0] == 15.0
    assert df_cut4.loc[df_cut4['LBSEQ'] == 2, 'LBORRES_NUM'].iloc[0] == 25.0
