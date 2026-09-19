from typing import Dict, List, Any, Optional
from stage3.models import Record, Provenance
from stage3.dependency import DependencyGraph
import datetime
import hashlib
import json

def generate_record_id(domain: str, row: Dict[str, Any]) -> str:
    """Generate a stable identity for a record."""
    usubjid = str(row.get("USUBJID", "UNKNOWN")).strip()
    seq_key = f"{domain}SEQ"
    
    parts = [f"raw:{domain}:{usubjid}"]
    
    # 1. Use SEQ if available
    if seq_key in row and row[seq_key] == row[seq_key] and row[seq_key] is not None and str(row[seq_key]).strip():
        parts.append(f"SEQ-{row[seq_key]}")
        return ":".join(parts)
        
    # 2. Try identifying keys
    identifying_keys = []
    for k in ["VISIT", f"{domain}TESTCD", f"{domain}PARAMCD", "PARAM", "PARAMCD", "TESTCD"]:
        if k in row and row[k] == row[k] and row[k] is not None and str(row[k]).strip():
            identifying_keys.append(f"{k}-{row[k]}")
            
    if identifying_keys:
        parts.extend(identifying_keys)
        return ":".join(parts)
        
    # 3. Fallback: hash stable fields
    exclude_suffixes = ('RES', 'RESN', 'ORRES', 'ORRESU', 'VALUE', 'VAL', 'DTC', 'CUT', 'TIMESTAMP')
    exclude_exact = ('SITEID', 'USUBJID', 'CUT_AVAILABLE', 'CORRECTION_CUT')
    
    stable_pairs = []
    for k, v in sorted(row.items()):
        k_up = k.upper()
        if k_up in exclude_exact or any(k_up.endswith(s) for s in exclude_suffixes):
            continue
        if v == v and v is not None and str(v).strip():
            stable_pairs.append(f"{k}={v}")
            
    if stable_pairs:
        stable_str = "|".join(stable_pairs)
        hash_val = hashlib.md5(stable_str.encode('utf-8')).hexdigest()[:8]
        parts.append(f"HASH-{hash_val}")
    else:
        parts.append("UNKNOWN_ID")
        
    return ":".join(parts)

class StudyState:
    def __init__(self):
        self.processed_cuts: List[int] = []
        self.current_cut: int = 0
        
        # Identity to Record
        self.records: Dict[str, Record] = {}
        
        self.sites: set = set()
        self.domains: set = set()
        
        self.dependency_graph = DependencyGraph()
        
    def ingest_record(self, domain: str, row: Dict[str, Any], cut: int, source_file: str) -> bool:
        """
        Ingest a single record. 
        Returns True if newly added or updated (version conflict/correction), False if exact duplicate.
        """
        rec_id = generate_record_id(domain, row)
        self.domains.add(domain)
        
        if "SITEID" in row and row["SITEID"]:
            self.sites.add(row["SITEID"])
            
        # Deduplication
        if rec_id in self.records:
            existing = self.records[rec_id]
            # Compare content excluding volatile keys if needed, but for now exact match:
            # We must ignore NaNs when comparing, or use a stable hash
            # A simple approach: compare dicts
            def clean_dict(d):
                return {k: v for k, v in d.items() if v == v and v is not None} # Handles NaN check for floats
                
            if clean_dict(existing.data) == clean_dict(row):
                return False # Exact duplicate, ignore
                
            # Content differs, treat as correction/version update
            new_version = existing.provenance.version + 1
            prov = Provenance(cut=cut, source_file=source_file, version=new_version, timestamp=datetime.datetime.utcnow().isoformat())
            self.records[rec_id] = Record(domain=domain, record_id=rec_id, data=row, provenance=prov)
            
            # Invalidate downstream
            self.dependency_graph.invalidate(rec_id)
            return True
            
        # New record
        prov = Provenance(cut=cut, source_file=source_file, version=1, timestamp=datetime.datetime.utcnow().isoformat())
        self.records[rec_id] = Record(domain=domain, record_id=rec_id, data=row, provenance=prov)
        self.dependency_graph.add_node(rec_id)
        # Mark invalid so it triggers initial computation
        self.dependency_graph.validity[rec_id] = False
        return True

    def apply_correction(self, cut: int, domain: str, usubjid: str, field: str, new_value: Any, seq: Optional[float] = None) -> bool:
        """Apply a correction explicitly to an existing record."""
        # Find the record id
        row_mock = {"USUBJID": usubjid}
        if seq is not None and not (isinstance(seq, float) and seq != seq):
            row_mock[f"{domain}SEQ"] = seq
            
        rec_id = generate_record_id(domain, row_mock)
        
        if rec_id in self.records:
            record = self.records[rec_id]
            
            # Don't duplicate if same value
            if record.data.get(field) == new_value:
                return False
                
            # Update data
            record.data[field] = new_value
            record.data["CORRECTION_CUT"] = cut
            if field == "LBORRES":
                try:
                    record.data["LBORRES_NUM"] = float(new_value)
                except ValueError:
                    pass
            
            # Update provenance
            record.provenance.version += 1
            record.provenance.cut = cut
            record.provenance.timestamp = datetime.datetime.utcnow().isoformat()
            
            # Invalidate dependents
            self.dependency_graph.invalidate(rec_id)
            return True
            
        return False
