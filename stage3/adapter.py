import pandas as pd
from typing import Dict, List, Any, Optional
import numpy as np

class Stage3Adapter:
    def __init__(self, state):
        """
        Initializes the adapter with the active StudyState and pre-indexes records by USUBJID for O(1) lookups.
        """
        self.state = state
        self._subject_index = {}
        for rec in self.state.records.values():
            if not rec.is_trusted: continue
            subj = rec.data.get("USUBJID")
            if subj:
                if subj not in self._subject_index:
                    self._subject_index[subj] = []
                self._subject_index[subj].append(rec)

    def dataframe_for_subject(self, domain: str, usubjid: str) -> pd.DataFrame:
        """
        Materializes a single subject's domain records into a pandas DataFrame.
        """
        records = [
            rec.data for rec in self._subject_index.get(usubjid, [])
            if rec.domain == domain
        ]
        
        df = pd.DataFrame(records)
        
        from app.data_loader import normalize_dates, normalize_lborres
        if not df.empty:
            df = normalize_dates(df)
            if domain == "LB":
                df = normalize_lborres(df)
                
        return df

    def domain_dataframe(self, domain: str, usubjid: Optional[str] = None) -> pd.DataFrame:
        """
        Materializes a domain DataFrame. 
        If usubjid is provided, isolates to that subject.
        """
        if usubjid:
            return self.dataframe_for_subject(domain, usubjid)
            
        records = []
        for rec in self.state.records.values():
            if rec.domain == domain and rec.is_trusted:
                records.append(rec.data)
        
        df = pd.DataFrame(records)
        
        from app.data_loader import normalize_dates, normalize_lborres
        if not df.empty:
            df = normalize_dates(df)
            if domain == "LB":
                df = normalize_lborres(df)
                
        return df

    def get_reference_ranges(self) -> pd.DataFrame:
        """Returns the reference ranges directly from DATASETS for analysis."""
        from app.data_loader import DATASETS
        return DATASETS.get("reference_ranges.csv", pd.DataFrame())

    def get_protocol_version(self, cut: int) -> int:
        from app.analysis import get_protocol_version
        return get_protocol_version(cut)
