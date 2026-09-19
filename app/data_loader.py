import pandas as pd
import numpy as np
import os
import glob
from typing import Dict

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if col.endswith('DTC'):
            # Convert to standard ISO date YYYY-MM-DD
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
            except Exception:
                pass # Ignore if not a valid date format entirely
    return df

def normalize_lborres(df: pd.DataFrame) -> pd.DataFrame:
    if 'LBORRES' not in df.columns:
        return df
    
    # Handle <5, ND, blank as missing (NaN)
    def parse_lborres(val):
        if pd.isna(val):
            return np.nan
        val_str = str(val).strip().upper()
        if val_str in ('<5', 'ND', '', 'NAN', 'NONE'):
            return np.nan
        try:
            return float(val_str)
        except ValueError:
            return np.nan
            
    df['LBORRES_NUM'] = df['LBORRES'].apply(parse_lborres)
    return df

def apply_s07_conversion(lb_df: pd.DataFrame, dm_df: pd.DataFrame) -> pd.DataFrame:
    """
    S07 ALT/AST conversion from µkat/L to U/L.
    Wait, LB doesn't have SITEID. We need to merge with DM to find SITEID.
    """
    if lb_df.empty or dm_df.empty:
        return lb_df

    # Merge to get SITEID
    merged = lb_df.merge(dm_df[['USUBJID', 'SITEID']], on='USUBJID', how='left')
    
    # Condition: SITEID == 'S07', LBTESTCD in ('ALT', 'AST'), and Unit might be µkat/L
    # But even if unit is missing, the requirement says "S07 ALT/AST conversion from µkat/L to U/L."
    # We will assume S07 reports ALT/AST in µkat/L and needs * 60 conversion.
    mask = (merged['SITEID'] == 'S07') & (merged['LBTESTCD'].isin(['ALT', 'AST']))
    
    # Apply conversion
    merged.loc[mask, 'LBORRES_NUM'] = merged.loc[mask, 'LBORRES_NUM'] * 60.0
    merged.loc[mask, 'LBORRESU'] = 'U/L'
    
    # Drop SITEID as it belongs to DM
    merged = merged.drop(columns=['SITEID'])
    return merged

def load_data() -> Dict[str, pd.DataFrame]:
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    datasets = {}
    
    # First pass: read all dataframes and normalize dates
    for f in files:
        fname = os.path.basename(f)
        df = pd.read_csv(f)
        df = normalize_dates(df)
        datasets[fname] = df
        
    # Second pass: normalize LBORRES and S07 conversions
    if 'LB.csv' in datasets:
        lb_df = datasets['LB.csv']
        lb_df = normalize_lborres(lb_df)
        if 'DM.csv' in datasets:
            lb_df = apply_s07_conversion(lb_df, datasets['DM.csv'])
        datasets['LB.csv'] = lb_df
        
    return datasets

# Pre-load data in memory
DATASETS = load_data()
