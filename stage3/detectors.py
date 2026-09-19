import hashlib
import os
import datetime
from typing import List, Dict, Any, Tuple
from stage3.models import Finding, Evidence
from stage3.state import StudyState

KNOWN_FACTORS = [18.0, 60.0, 2.5, 0.055, 0.016, 0.4]

ANALYTE_CORROBORATION = {
    'GLUC': ['hypoglycemia', 'hyperglycemia', 'diabetes', 'glucose'],
    'ALT': ['liver', 'hepatic', 'jaundice', 'hepatitis', 'hys law'],
    'AST': ['liver', 'hepatic', 'jaundice', 'hepatitis', 'hys law'],
    'BILI': ['jaundice', 'liver', 'hepatic', 'gallbladder'],
    'CREAT': ['renal', 'kidney']
}

class SuspiciousSiteConfig:
    def __init__(self, minimum_records: int = 10, variance_threshold: float = 0.01, duplicate_ratio_threshold: float = 0.8, weekday_concentration_threshold: float = 0.8, timestamp_concentration_threshold: float = 0.8):
        self.minimum_records = minimum_records
        self.variance_threshold = variance_threshold
        self.duplicate_ratio_threshold = duplicate_ratio_threshold
        self.weekday_concentration_threshold = weekday_concentration_threshold
        self.timestamp_concentration_threshold = timestamp_concentration_threshold

class UnitCorruptionDetector:
    def detect(self, state: StudyState, cut: int) -> List[Finding]:
        findings = []
        lb_records = [r for r in state.records.values() if r.domain == 'LB' and r.is_trusted]
        
        # historical and current
        history = [r for r in lb_records if r.provenance.cut < cut]
        current = [r for r in lb_records if r.provenance.cut == cut]
        
        def get_vals(recs):
            groups = {}
            for r in recs:
                site = r.data.get('SITEID')
                test = r.data.get('LBTESTCD')
                val = r.data.get('LBORRES_NUM', r.data.get('LBSTRESN'))
                try:
                    v = float(val)
                except (ValueError, TypeError):
                    continue
                if site and test and v == v:
                    groups.setdefault((site, test), []).append((r.record_id, v))
            return groups
            
        hist_g = get_vals(history)
        curr_g = get_vals(current)
        
        for (site, test), curr_vals_with_id in curr_g.items():
            hist_vals_with_id = hist_g.get((site, test), [])
            hist_vals = [v for _, v in hist_vals_with_id]
            curr_vals = [v for _, v in curr_vals_with_id]
            
            if len(hist_vals) >= 2 and len(curr_vals) >= 2:
                hist_med = sorted(hist_vals)[len(hist_vals)//2]
                curr_med = sorted(curr_vals)[len(curr_vals)//2]
                
                if hist_med == 0 or curr_med == 0:
                    continue
                    
                ratio = hist_med / curr_med if hist_med > curr_med else curr_med / hist_med
                
                # Check conversion matches
                is_conversion = False
                for f in KNOWN_FACTORS:
                    if abs(ratio - f) / f < 0.1:
                        is_conversion = True
                        break
                        
                abrupt_shift = ratio > 2.0
                
                # Check relevant clinical corroboration
                has_corroboration = False
                keywords = ANALYTE_CORROBORATION.get(test.upper(), [])
                if keywords:
                    ae_curr = [r for r in state.records.values() if r.domain == 'AE' and r.provenance.cut <= cut and r.data.get('SITEID') == site]
                    for ae in ae_curr:
                        term = str(ae.data.get('AETERM', '')).lower()
                        if any(kw in term for kw in keywords):
                            has_corroboration = True
                            break
                            
                ev = Evidence(
                    source_file="LB.csv",
                    metadata={"site": site, "test": test, "historical_median": hist_med, "current_median": curr_med, "ratio": ratio}
                )
                
                if is_conversion and abrupt_shift:
                    conf = 0.5 if has_corroboration else 0.95
                    finding = Finding(
                        finding_id=f"UNIT-CORRUPT-{site}-{test}-{cut}",
                        finding_type="DATA_INTEGRITY_UNIT_CORRUPTION",
                        severity="HIGH",
                        scope={"site_id": site, "test_cd": test},
                        evidence=[ev],
                        confidence=conf,
                        recommended_action="QUARANTINE",
                        metadata={"ratio": ratio, "corroboration": has_corroboration, "conversion_match": True, "abrupt_shift": True}
                    )
                    findings.append(finding)
                elif abrupt_shift and not is_conversion:
                    # Persistent drift check across whole period, not a unit step change
                    finding = Finding(
                        finding_id=f"DRIFT-{site}-{test}-{cut}",
                        finding_type="PERSISTENT_LAB_DISTRIBUTION_DRIFT",
                        severity="MEDIUM",
                        scope={"site_id": site, "test_cd": test},
                        evidence=[ev],
                        confidence=0.7 if not has_corroboration else 0.4,
                        recommended_action="MONITOR",
                        metadata={"ratio": ratio, "corroboration": has_corroboration}
                    )
                    findings.append(finding)
                    
        return findings

class SuspiciousSiteDetector:
    def __init__(self, config: SuspiciousSiteConfig = None):
        self.config = config or SuspiciousSiteConfig()
        
    def detect(self, state: StudyState, cut: int) -> List[Finding]:
        findings = []
        vs_records = [r for r in state.records.values() if r.domain == 'VS' and r.is_trusted]
        
        site_vals = {}
        site_weekdays = {}
        for r in vs_records:
            site = r.data.get('SITEID')
            val = r.data.get('VSSTRESN', r.data.get('VSORRES_NUM', r.data.get('VSORRES')))
            dtc = r.data.get('VSDTC')
            try:
                v = float(val)
                if site and v == v:
                    site_vals.setdefault(site, []).append((r.record_id, v))
            except (ValueError, TypeError):
                pass
                
            if site and dtc:
                try:
                    wd = datetime.datetime.fromisoformat(str(dtc).replace("Z", "+00:00")).weekday()
                    site_weekdays.setdefault(site, []).append(wd)
                except ValueError:
                    pass
                
        for site, vals_with_ids in site_vals.items():
            if len(vals_with_ids) >= self.config.minimum_records:
                vals = [v for _, v in vals_with_ids]
                mean = sum(vals)/len(vals)
                variance = sum((x - mean)**2 for x in vals) / len(vals)
                
                # Duplicate value rate
                most_common_val_count = max([vals.count(v) for v in set(vals)])
                dup_rate = most_common_val_count / len(vals)
                
                # Weekday concentration
                wds = site_weekdays.get(site, [])
                wd_concentration = max([wds.count(w) for w in set(wds)]) / len(wds) if wds else 0.0
                
                signals_matched = 0
                if variance < self.config.variance_threshold: signals_matched += 1
                if dup_rate >= self.config.duplicate_ratio_threshold: signals_matched += 1
                if wd_concentration >= self.config.weekday_concentration_threshold: signals_matched += 1
                
                if signals_matched >= 2:
                    ev = Evidence(source_file="VS.csv", metadata={"site": site, "variance": variance, "n": len(vals), "duplicate_rate": dup_rate, "weekday_concentration": wd_concentration})
                    finding = Finding(
                        finding_id=f"SUSP-SITE-{site}-{cut}",
                        finding_type="SUSPICIOUS_SITE_REGULARITY",
                        severity="HIGH",
                        scope={"site_id": site},
                        evidence=[ev],
                        confidence=0.94,
                        recommended_action="QUARANTINE",
                        metadata={"variance": variance, "duplicate_ratio": dup_rate, "weekday_entropy": 1.0 - wd_concentration}
                    )
                    findings.append(finding)
        return findings

class DocumentTamperDetector:
    def __init__(self):
        self.trusted_hashes = {}
        
    def initialize(self, protocol_dir: str):
        if not os.path.exists(protocol_dir):
            return
        for fname in os.listdir(protocol_dir):
            if fname.endswith('.md'):
                fpath = os.path.join(protocol_dir, fname)
                with open(fpath, 'rb') as f:
                    self.trusted_hashes[fname] = hashlib.sha256(f.read()).hexdigest()
                    
    def detect(self, protocol_dir: str, cut: int) -> List[Finding]:
        findings = []
        if not os.path.exists(protocol_dir):
            return findings
            
        for fname in os.listdir(protocol_dir):
            if fname.endswith('.md'):
                fpath = os.path.join(protocol_dir, fname)
                with open(fpath, 'rb') as f:
                    curr_hash = hashlib.sha256(f.read()).hexdigest()
                    
                if fname in self.trusted_hashes:
                    if curr_hash != self.trusted_hashes[fname]:
                        ev = Evidence(
                            source_file=fpath,
                            metadata={"original_hash": self.trusted_hashes[fname], "current_hash": curr_hash}
                        )
                        fnd = Finding(
                            finding_id=f"TAMPER-{fname}-{cut}",
                            finding_type="DOCUMENT_TAMPERED",
                            severity="CRITICAL",
                            scope={"file": fname},
                            evidence=[ev],
                            confidence=1.0,
                            recommended_action="REJECT_INSTRUCTION",
                            metadata={"cut": cut}
                        )
                        findings.append(fnd)
                else:
                    # New document
                    self.trusted_hashes[fname] = curr_hash
        return findings

class AmendmentImpactDetector:
    def detect(self, state: StudyState, cut: int, amendment_detected: bool, affected_nodes: List[str]) -> List[Finding]:
        findings = []
        if amendment_detected:
            for node in affected_nodes:
                state.dependency_graph.invalidate(node)
                
            ev = Evidence(source_file="amendment.json", metadata={"affected_nodes": affected_nodes})
            fnd = Finding(
                finding_id=f"AMEND-IMPACT-{cut}",
                finding_type="AMENDMENT_IMPACT",
                severity="INFO",
                scope={"nodes": "multiple"},
                evidence=[ev],
                confidence=1.0,
                recommended_action="RECOMPUTE_AFFECTED",
                metadata={"invalidated_count": len(affected_nodes)}
            )
            findings.append(fnd)
        return findings
