import pandas as pd
from typing import Dict, Any, List, Optional
from app.data_loader import DATASETS
from app.repository import apply_cuts_and_corrections, generate_evidence, get_latest_cut
from app.schemas import EvidenceTrail, EvidenceDetail

TARGET_DAYS = {
    'SCREENING': -14, 'BASELINE': 0, 'WEEK2': 14, 'WEEK4': 28, 'WEEK8': 56,
    'WEEK12': 84, 'WEEK16': 112, 'WEEK20': 140, 'WEEK24': 168, 'EOS': 182
}

PROTOCOL_WINDOWS = {1: 7, 2: 3, 3: 3}

def get_protocol_version(cut: int) -> int:
    cuts_df = DATASETS.get('cuts.csv', pd.DataFrame())
    if cuts_df.empty:
        return 1
    row = cuts_df[cuts_df['cut'] == cut]
    if not row.empty:
        return int(row.iloc[0]['protocol_version'])
    return 1

def exclude_safety_sites(df: pd.DataFrame, dm_df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or dm_df.empty:
        return df
    dm_filtered = dm_df[~dm_df['SITEID'].isin(['S03', 'S07'])]
    return df[df['USUBJID'].isin(dm_filtered['USUBJID'])]

def find_subjects(siteid: Optional[str], arm: Optional[str], disposition: Optional[str], cut: int) -> Dict[str, Any]:
    dm_df = apply_cuts_and_corrections(DATASETS.get('DM.csv', pd.DataFrame()), 'DM.csv', cut)
    if dm_df.empty: return {"data": [], "evidence": EvidenceTrail(records=[])}

    filtered = dm_df.copy()
    if siteid: filtered = filtered[filtered['SITEID'] == siteid]
    if arm: filtered = filtered[filtered['ARM'] == arm]
    if disposition:
        ds_df = apply_cuts_and_corrections(DATASETS.get('DS.csv', pd.DataFrame()), 'DS.csv', cut)
        if not ds_df.empty:
            ds_filtered = ds_df[ds_df['DSDECOD'] == disposition]
            filtered = filtered[filtered['USUBJID'].isin(ds_filtered['USUBJID'])]
        else: filtered = filtered.iloc[0:0]

    records = filtered.to_dict('records')
    evidence = generate_evidence('DM.csv', records, ['USUBJID'])
    return {"data": records, "evidence": EvidenceTrail(records=evidence)}

def search_labs(testcd: Optional[str], min_val: Optional[float], max_val: Optional[float], cut: int) -> Dict[str, Any]:
    lb_df = apply_cuts_and_corrections(DATASETS.get('LB.csv', pd.DataFrame()), 'LB.csv', cut)
    if lb_df.empty: return {"data": [], "evidence": EvidenceTrail(records=[])}

    filtered = lb_df.copy()
    if testcd: filtered = filtered[filtered['LBTESTCD'] == testcd]
    if min_val is not None: filtered = filtered[filtered['LBORRES_NUM'] >= min_val]
    if max_val is not None: filtered = filtered[filtered['LBORRES_NUM'] <= max_val]

    records = filtered.to_dict('records')
    evidence = generate_evidence('LB.csv', records, ['USUBJID', 'LBSEQ'])
    return {"data": records, "evidence": EvidenceTrail(records=evidence)}

def detect_saes(cut: int) -> Dict[str, Any]:
    ae_df = apply_cuts_and_corrections(DATASETS.get('AE.csv', pd.DataFrame()), 'AE.csv', cut)
    dm_df = apply_cuts_and_corrections(DATASETS.get('DM.csv', pd.DataFrame()), 'DM.csv', cut)
    
    if ae_df.empty: return {"data": [], "evidence": EvidenceTrail(records=[])}

    ae_filtered = exclude_safety_sites(ae_df, dm_df)
    sae_df = ae_filtered[(ae_filtered['AESER'] == 'Y') | (ae_filtered['AESHOSP'] == 'Y')]
    
    records = sae_df.to_dict('records')
    evidence = generate_evidence('AE.csv', records, ['USUBJID', 'AESEQ'])
    return {"data": records, "evidence": EvidenceTrail(records=evidence)}

def detect_hys_law(cut: int) -> Dict[str, Any]:
    lb_df = apply_cuts_and_corrections(DATASETS.get('LB.csv', pd.DataFrame()), 'LB.csv', cut)
    dm_df = apply_cuts_and_corrections(DATASETS.get('DM.csv', pd.DataFrame()), 'DM.csv', cut)
    ref_df = DATASETS.get('reference_ranges.csv', pd.DataFrame())
    
    if lb_df.empty or ref_df.empty: return {"data": [], "evidence": EvidenceTrail(records=[])}

    lb_safe = exclude_safety_sites(lb_df, dm_df)
    
    # Needs ALT, AST, BILI
    alt_df = lb_safe[lb_safe['LBTESTCD'] == 'ALT'].copy()
    ast_df = lb_safe[lb_safe['LBTESTCD'] == 'AST'].copy()
    bili_df = lb_safe[lb_safe['LBTESTCD'] == 'BILI'].copy()
    
    alt_ref = ref_df[(ref_df['LBTESTCD'] == 'ALT') & (ref_df['LAB'] == 'CENTRAL')]
    ast_ref = ref_df[(ref_df['LBTESTCD'] == 'AST') & (ref_df['LAB'] == 'CENTRAL')]
    bili_ref = ref_df[(ref_df['LBTESTCD'] == 'BILI') & (ref_df['LAB'] == 'CENTRAL')]
    
    if alt_ref.empty or ast_ref.empty or bili_ref.empty: return {"data": [], "evidence": EvidenceTrail(records=[])}
        
    alt_uln = alt_ref.iloc[0]['HIGH']
    ast_uln = ast_ref.iloc[0]['HIGH']
    bili_uln = bili_ref.iloc[0]['HIGH']
    
    # Strict > criteria
    alt_elevated = alt_df[alt_df['LBORRES_NUM'] > 3 * alt_uln]
    ast_elevated = ast_df[ast_df['LBORRES_NUM'] > 3 * ast_uln]
    bili_elevated = bili_df[bili_df['LBORRES_NUM'] > 2 * bili_uln].copy()
    
    # Combine ALT and AST
    hep_elevated = pd.concat([alt_elevated, ast_elevated]).drop_duplicates(subset=['USUBJID', 'LBSEQ'])
    hep_elevated['LBDTC_DATE'] = pd.to_datetime(hep_elevated['LBDTC'], errors='coerce')
    bili_elevated['LBDTC_DATE'] = pd.to_datetime(bili_elevated['LBDTC'], errors='coerce')
    
    hys_cases = pd.merge(
        hep_elevated, 
        bili_elevated, 
        on='USUBJID',
        suffixes=('_HEP', '_BILI')
    )
    
    # Check within 14 days
    hys_cases['days_diff'] = (hys_cases['LBDTC_DATE_HEP'] - hys_cases['LBDTC_DATE_BILI']).dt.days.abs()
    valid_cases = hys_cases[hys_cases['days_diff'] <= 14].copy()
    
    # Format output dates back to strings
    valid_cases['LBDTC_DATE_HEP'] = valid_cases['LBDTC_DATE_HEP'].dt.strftime('%Y-%m-%d')
    valid_cases['LBDTC_DATE_BILI'] = valid_cases['LBDTC_DATE_BILI'].dt.strftime('%Y-%m-%d')
    
    # Convert to dict and add evidence
    # Group by USUBJID to only return one finding per patient if multiple exist, or just return all matches
    records = valid_cases.to_dict('records')
    evidence_list = []
    
    for row in records:
        hep_keys = {'LBTESTCD', 'LBORRES_NUM_HEP', 'LBDTC_HEP', 'LBORRES_HEP', 'CORRECTION_CUT_HEP', 'S07_CONVERSION_APPLIED_HEP'}
        bili_keys = {'LBORRES_NUM_BILI', 'LBDTC_BILI', 'LBORRES_BILI', 'CORRECTION_CUT_BILI', 'S07_CONVERSION_APPLIED_BILI'}
        
        hep_vals = {'LBTESTCD': row['LBTESTCD_HEP'], 'REFERENCE_RANGE_HIGH': alt_uln if row['LBTESTCD_HEP']=='ALT' else ast_uln}
        for k in hep_keys:
            if k in row and pd.notna(row[k]):
                clean_k = k.replace('_HEP', '')
                hep_vals[clean_k] = row[k]
                
        bili_vals = {'LBTESTCD': 'BILI', 'REFERENCE_RANGE_HIGH': bili_uln}
        for k in bili_keys:
            if k in row and pd.notna(row[k]):
                clean_k = k.replace('_BILI', '')
                bili_vals[clean_k] = row[k]
                
        evidence_list.append(EvidenceDetail(
            file='LB.csv', 
            row_id={'USUBJID': row['USUBJID'], 'LBSEQ': row['LBSEQ_HEP']}, 
            values=hep_vals
        ))
        evidence_list.append(EvidenceDetail(
            file='LB.csv', 
            row_id={'USUBJID': row['USUBJID'], 'LBSEQ': row['LBSEQ_BILI']}, 
            values=bili_vals
        ))
        
    return {
        "data": records, 
        "evidence": EvidenceTrail(records=evidence_list),
        "metadata": {"label": "protocol-defined screening signal"}
    }

def detect_dosing_errors(cut: int) -> Dict[str, Any]:
    ex_df = apply_cuts_and_corrections(DATASETS.get('EX.csv', pd.DataFrame()), 'EX.csv', cut)
    dm_df = apply_cuts_and_corrections(DATASETS.get('DM.csv', pd.DataFrame()), 'DM.csv', cut)
    
    if ex_df.empty or dm_df.empty: return {"data": [], "evidence": EvidenceTrail(records=[])}
        
    merged = pd.merge(ex_df, dm_df[['USUBJID', 'ARM']], on='USUBJID', how='left')
    errors = merged[
        ((merged['ARM'] == 'DRUG') & (merged['EXDOSE'] != 10)) |
        ((merged['ARM'] == 'PLACEBO') & (merged['EXDOSE'] != 0))
    ]
    
    records = errors.to_dict('records')
    evidence = generate_evidence('EX.csv', records, ['USUBJID', 'EXSEQ'])
    return {"data": records, "evidence": EvidenceTrail(records=evidence)}

def detect_visit_deviations(cut: int) -> Dict[str, Any]:
    vs_df = apply_cuts_and_corrections(DATASETS.get('VS.csv', pd.DataFrame()), 'VS.csv', cut)
    dm_df = apply_cuts_and_corrections(DATASETS.get('DM.csv', pd.DataFrame()), 'DM.csv', cut)
    
    if vs_df.empty or dm_df.empty: return {"data": [], "evidence": EvidenceTrail(records=[])}
        
    protocol_version = get_protocol_version(cut)
    window = PROTOCOL_WINDOWS.get(protocol_version, 7)
    
    merged = pd.merge(vs_df, dm_df[['USUBJID', 'RFSTDTC']], on='USUBJID', how='inner')
    merged['VSDTC_DATE'] = pd.to_datetime(merged['VSDTC'], errors='coerce')
    merged['RFSTDTC_DATE'] = pd.to_datetime(merged['RFSTDTC'], errors='coerce')
    merged['days'] = (merged['VSDTC_DATE'] - merged['RFSTDTC_DATE']).dt.days
    
    deviations = []
    
    for idx, row in merged.iterrows():
        visit = row['VISIT']
        if visit in TARGET_DAYS:
            target = TARGET_DAYS[visit]
            actual = row['days']
            if pd.notna(actual):
                if abs(actual - target) > window:
                    dev_record = row.to_dict()
                    dev_record['VSDTC_DATE'] = dev_record['VSDTC_DATE'].strftime('%Y-%m-%d') if pd.notna(dev_record['VSDTC_DATE']) else None
                    dev_record['RFSTDTC_DATE'] = dev_record['RFSTDTC_DATE'].strftime('%Y-%m-%d') if pd.notna(dev_record['RFSTDTC_DATE']) else None
                    deviations.append(dev_record)
                    
    dedup = {}
    for d in deviations:
        key = (d['USUBJID'], d['VISIT'])
        if key not in dedup: dedup[key] = d
            
    final_deviations = list(dedup.values())
    evidence = generate_evidence('VS.csv', final_deviations, ['USUBJID', 'VSSEQ'])
    return {"data": final_deviations, "evidence": EvidenceTrail(records=evidence)}

def detect_prohibited_meds(cut: int) -> Dict[str, Any]:
    cm_df = apply_cuts_and_corrections(DATASETS.get('CM.csv', pd.DataFrame()), 'CM.csv', cut)
    if cm_df.empty: return {"data": [], "evidence": EvidenceTrail(records=[])}
    
    pv = get_protocol_version(cut)
    
    prohibited = cm_df[cm_df['CMCLAS'] == 'SYSTEMIC_GLUCOCORTICOID'].copy()
    
    if pv >= 3:
        sulf = cm_df[cm_df['CMCLAS'] == 'SULFONYLUREA']
        prohibited = pd.concat([prohibited, sulf])
        
    records = prohibited.to_dict('records')
    evidence = generate_evidence('CM.csv', records, ['USUBJID', 'CMSEQ'])
    return {"data": records, "evidence": EvidenceTrail(records=evidence)}

def detect_teae(cut: int) -> Dict[str, Any]:
    ae_df = apply_cuts_and_corrections(DATASETS.get('AE.csv', pd.DataFrame()), 'AE.csv', cut)
    dm_df = apply_cuts_and_corrections(DATASETS.get('DM.csv', pd.DataFrame()), 'DM.csv', cut)
    if ae_df.empty or dm_df.empty: return {"data": [], "evidence": EvidenceTrail(records=[])}
    
    merged = pd.merge(ae_df, dm_df[['USUBJID', 'RFSTDTC']], on='USUBJID', how='inner')
    merged['AESTDTC_DATE'] = pd.to_datetime(merged['AESTDTC'], errors='coerce')
    merged['RFSTDTC_DATE'] = pd.to_datetime(merged['RFSTDTC'], errors='coerce')
    
    # TEAE: onset on or after first dose (RFSTDTC)
    teae = merged[merged['AESTDTC_DATE'] >= merged['RFSTDTC_DATE']]
    
    records = teae.drop(columns=['AESTDTC_DATE', 'RFSTDTC_DATE']).to_dict('records')
    
    evidence_list = []
    for row in records:
        evidence_list.append(EvidenceDetail(
            file='AE.csv',
            row_id={'USUBJID': row['USUBJID'], 'AESEQ': row['AESEQ']},
            values={'AESTDTC': row['AESTDTC']}
        ))
        evidence_list.append(EvidenceDetail(
            file='DM.csv',
            row_id={'USUBJID': row['USUBJID']},
            values={'RFSTDTC': row['RFSTDTC']}
        ))
        
    return {"data": records, "evidence": EvidenceTrail(records=evidence_list)}

def detect_exclusion_violations(cut: int) -> Dict[str, Any]:
    dm_df = apply_cuts_and_corrections(DATASETS.get('DM.csv', pd.DataFrame()), 'DM.csv', cut)
    lb_df = apply_cuts_and_corrections(DATASETS.get('LB.csv', pd.DataFrame()), 'LB.csv', cut)
    ref_df = DATASETS.get('reference_ranges.csv', pd.DataFrame())
    
    if dm_df.empty: return {"data": [], "evidence": EvidenceTrail(records=[])}
    
    violations = []
    evidence_list = []
    pv = get_protocol_version(cut)
    
    for _, subj in dm_df.iterrows():
        usubjid = subj['USUBJID']
        age = subj['AGE']
        hba1c = subj['SCR_HBA1C']
        
        reasons = []
        if pd.notna(age) and (age < 18 or age > 75):
            reasons.append('AGE')
        if pd.notna(hba1c) and (hba1c < 7.0 or hba1c > 10.5):
            reasons.append('HBA1C')
            
        # Add DM evidence if violations found
        if reasons:
            violations.append({"USUBJID": usubjid, "reasons": reasons})
            evidence_list.append(EvidenceDetail(file='DM.csv', row_id={'USUBJID': usubjid}, values={'AGE': age, 'SCR_HBA1C': hba1c}))
            
    # Liver/Renal from LB
    if not lb_df.empty and not ref_df.empty:
        lb_scr = lb_df[lb_df['VISIT'] == 'SCREENING']
        
        alt_uln = ref_df[(ref_df['LBTESTCD'] == 'ALT') & (ref_df['LAB'] == 'CENTRAL')]['HIGH'].iloc[0] if not ref_df[(ref_df['LBTESTCD'] == 'ALT') & (ref_df['LAB'] == 'CENTRAL')].empty else None
        ast_uln = ref_df[(ref_df['LBTESTCD'] == 'AST') & (ref_df['LAB'] == 'CENTRAL')]['HIGH'].iloc[0] if not ref_df[(ref_df['LBTESTCD'] == 'AST') & (ref_df['LAB'] == 'CENTRAL')].empty else None
        
        for _, lab in lb_scr.iterrows():
            test = lab['LBTESTCD']
            val = lab['LBORRES_NUM']
            
            if pd.notna(val):
                if test == 'ALT' and alt_uln and val > 2 * alt_uln:
                    violations.append({"USUBJID": lab['USUBJID'], "reasons": ["ALT_EXCLUSION"]})
                    vals = {k: v for k, v in lab.items() if pd.notna(v) and k not in ['USUBJID', 'LBSEQ']}
                    evidence_list.append(EvidenceDetail(file='LB.csv', row_id={'USUBJID': lab['USUBJID'], 'LBSEQ': lab['LBSEQ']}, values=vals))
                elif test == 'AST' and ast_uln and val > 2 * ast_uln:
                    violations.append({"USUBJID": lab['USUBJID'], "reasons": ["AST_EXCLUSION"]})
                    vals = {k: v for k, v in lab.items() if pd.notna(v) and k not in ['USUBJID', 'LBSEQ']}
                    evidence_list.append(EvidenceDetail(file='LB.csv', row_id={'USUBJID': lab['USUBJID'], 'LBSEQ': lab['LBSEQ']}, values=vals))
                elif pv >= 2 and test == 'CREAT' and val > 1.5:
                    violations.append({"USUBJID": lab['USUBJID'], "reasons": ["CREAT_EXCLUSION"]})
                    vals = {k: v for k, v in lab.items() if pd.notna(v) and k not in ['USUBJID', 'LBSEQ']}
                    evidence_list.append(EvidenceDetail(file='LB.csv', row_id={'USUBJID': lab['USUBJID'], 'LBSEQ': lab['LBSEQ']}, values=vals))
                    
    return {"data": violations, "evidence": EvidenceTrail(records=evidence_list)}
