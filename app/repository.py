import pandas as pd
import math
from typing import Dict, Any, List, Tuple
from app.data_loader import DATASETS
from app.schemas import EvidenceDetail, EvidenceTrail, ApiResponse

def get_latest_cut() -> int:
    if 'cuts.csv' in DATASETS:
        return int(DATASETS['cuts.csv']['cut'].max())
    return 0

def apply_cuts_and_corrections(domain_df: pd.DataFrame, domain_name: str, target_cut: int) -> pd.DataFrame:
    if domain_df.empty:
        return domain_df
        
    df = domain_df.copy()
    
    # Filter by cut_available (only rows available up to the target_cut)
    if 'cut_available' in df.columns:
        df = df[df['cut_available'] <= target_cut]
        
    # Apply corrections
    if 'corrections.csv' in DATASETS:
        corrections = DATASETS['corrections.csv']
        # Filter corrections up to the target_cut
        # Correction domain must match the domain_name (without .csv)
        domain_str = domain_name.replace('.csv', '')
        relevant_corrections = corrections[
            (corrections['cut'] <= target_cut) & 
            (corrections['domain'] == domain_str)
        ]
        
        # Apply corrections sequentially (in case multiple corrections apply to the same field across cuts)
        relevant_corrections = relevant_corrections.sort_values(by='cut')
        
        # Create an index for faster lookup if seq is available
        # Wait, not all domains have a sequence number matching 'seq'. DM doesn't have DMSEQ, it just has USUBJID.
        # But corrections.csv has 'seq'. For DM, seq might be NaN or ignored. Let's check if seq is used.
        # The prompt says corrections are based on domain, usubjid, seq, field.
        
        # Determine the sequence column name (e.g., LBSEQ for LB)
        seq_col = f"{domain_str}SEQ"
        
        for _, row in relevant_corrections.iterrows():
            subj = row['usubjid']
            seq = row['seq']
            field = row['field']
            new_val = row['new_value']
            
            mask = (df['USUBJID'] == subj)
            if seq_col in df.columns and pd.notna(seq):
                mask = mask & (df[seq_col] == seq)
                
            if field in df.columns:
                df.loc[mask, field] = new_val
                df.loc[mask, 'CORRECTION_CUT'] = row['cut']
                
                if field == 'LBORRES' and 'LBORRES_NUM' in df.columns:
                    num_val = float(new_val)
                    if domain_str == 'LB':
                        if 'DM.csv' in DATASETS:
                            dm_df = DATASETS['DM.csv']
                            if (dm_df['USUBJID'] == subj).any() and dm_df[dm_df['USUBJID'] == subj]['SITEID'].iloc[0] == 'S07':
                                row_data = df[mask]
                                if not row_data.empty and row_data.iloc[0]['LBTESTCD'] in ['ALT', 'AST']:
                                    num_val = num_val * 60.0
                                    df.loc[mask, 'S07_CONVERSION_APPLIED'] = 'YES'
                    df.loc[mask, 'LBORRES_NUM'] = num_val
                    
    return df

def generate_evidence(file: str, records: List[Dict[str, Any]], primary_keys: List[str]) -> List[EvidenceDetail]:
    evidence_list = []
    for rec in records:
        row_id = {k: rec[k] for k in primary_keys if k in rec}
        # Filter out NaN/None values from values
        values = {k: v for k, v in rec.items() if pd.notna(v)}
        evidence_list.append(EvidenceDetail(
            file=file,
            row_id=row_id,
            values=values
        ))
    return evidence_list

def get_subject_data(usubjid: str, cut: int) -> Tuple[Dict[str, Any], List[EvidenceDetail]]:
    df = apply_cuts_and_corrections(DATASETS.get('DM.csv', pd.DataFrame()), 'DM.csv', cut)
    if df.empty:
        return {}, []
    
    subj_df = df[df['USUBJID'] == usubjid]
    if subj_df.empty:
        return {}, []
        
    records = subj_df.to_dict('records')
    evidence = generate_evidence('DM.csv', records, ['USUBJID'])
    return records[0], evidence

def _get_domain_data(usubjid: str, domain: str, cut: int, pk_cols: List[str]) -> Tuple[List[Dict[str, Any]], List[EvidenceDetail]]:
    file_name = f"{domain}.csv"
    df = apply_cuts_and_corrections(DATASETS.get(file_name, pd.DataFrame()), file_name, cut)
    if df.empty:
        return [], []
        
    subj_df = df[df['USUBJID'] == usubjid]
    if subj_df.empty:
        return [], []
        
    records = subj_df.to_dict('records')
    evidence = generate_evidence(file_name, records, pk_cols)
    return records, evidence

def get_labs(usubjid: str, cut: int) -> Tuple[List[Dict[str, Any]], List[EvidenceDetail]]:
    return _get_domain_data(usubjid, 'LB', cut, ['USUBJID', 'LBSEQ'])

def get_adverse_events(usubjid: str, cut: int) -> Tuple[List[Dict[str, Any]], List[EvidenceDetail]]:
    return _get_domain_data(usubjid, 'AE', cut, ['USUBJID', 'AESEQ'])

def get_exposure(usubjid: str, cut: int) -> Tuple[List[Dict[str, Any]], List[EvidenceDetail]]:
    return _get_domain_data(usubjid, 'EX', cut, ['USUBJID', 'EXSEQ'])
