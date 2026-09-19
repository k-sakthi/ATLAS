import pandas as pd
import os
import glob
import json
import logging
from typing import List, Dict, Any, Optional

from stage3.state import StudyState
from stage3.detectors import (
    UnitCorruptionDetector, SuspiciousSiteDetector, DocumentTamperDetector, AmendmentImpactDetector
)
from stage3.escalation import EscalationManager
from stage3.budget import BudgetGovernor
from stage3.trace import TraceLedger, Explanation
from stage3.policy import PolicyEngine

logger = logging.getLogger(__name__)

class StudyWatch:
    def __init__(self, data_dir: str, budget: int = 100000):
        self.data_dir = data_dir
        self.state = StudyState()
        
        self.budget = BudgetGovernor(total_budget=budget)
        self.escalations = EscalationManager()
        self.trace = TraceLedger()
        self.policy = PolicyEngine()
        
        self.unit_detector = UnitCorruptionDetector()
        self.site_detector = SuspiciousSiteDetector()
        self.doc_detector = DocumentTamperDetector()
        self.amend_detector = AmendmentImpactDetector()
        
        # Initialize doc security
        self.doc_detector.initialize(os.path.join(self.data_dir, "protocol"))
        
        self.metrics = {
            "recomputed_nodes": 0,
            "invalidated_nodes": 0,
            "reused_nodes": 0
        }
        
    def process_cut(self, cut: int) -> str:
        """
        Process a specific cut idempotently.
        """
        if cut in self.state.processed_cuts:
            return "ALREADY_PROCESSED"
            
        self.state.current_cut = cut
        
        # 1. Ingest Records
        self._ingest_records(cut)
        
        # 2. Apply Corrections up to this cut
        self._ingest_corrections(cut)
        
        # 3. Mark affected nodes invalid (Done in state methods automatically)
        
        # 5. Mark complete
        self.state.processed_cuts.append(cut)
        return "SUCCESS"
        
    def _ingest_records(self, cut: int):
        files = glob.glob(os.path.join(self.data_dir, "*.csv"))
        for f in files:
            fname = os.path.basename(f)
            if fname in ['cuts.csv', 'corrections.csv', 'reference_ranges.csv']:
                continue
                
            domain = fname.replace('.csv', '')
            try:
                df = pd.read_csv(f)
                        
                if 'cut_available' in df.columns:
                    # Only ingest records available exactly in this cut
                    new_records = df[df['cut_available'] == cut]
                else:
                    # If no cut_available, assume all available at cut 1
                    if cut == 1:
                        new_records = df
                    else:
                        new_records = pd.DataFrame()
                        
                for _, row in new_records.iterrows():
                    # Handle NaNs in dict
                    row_dict = {k: v for k, v in row.to_dict().items() if pd.notna(v)}
                    self.state.ingest_record(domain, row_dict, cut, fname)
                    
            except Exception:
                pass # Gracefully handle unknown or unparseable domain
                
    def _ingest_corrections(self, cut: int):
        corr_file = os.path.join(self.data_dir, "corrections.csv")
        if not os.path.exists(corr_file):
            return
            
        df = pd.read_csv(corr_file)
        new_corrs = df[df['cut'] == cut]
        
        for _, row in new_corrs.iterrows():
            seq = row['seq'] if pd.notna(row['seq']) else None
            self.state.apply_correction(
                cut=cut,
                domain=row['domain'],
                usubjid=row['usubjid'],
                field=row['field'],
                new_value=row['new_value'],
                seq=seq
            )
            
    def recompute_invalidated_nodes(self) -> List[Any]:
        new_findings = []
        invalid = [nid for nid, is_v in self.state.dependency_graph.validity.items() if not is_v]
        if not invalid:
            valid_count = len([nid for nid, is_v in self.state.dependency_graph.validity.items() if is_v])
            self.metrics["reused_nodes"] = valid_count
            return new_findings
            
        self.metrics["invalidated_nodes"] += len(invalid)
        
        # 1. Identify affected USUBJIDs
        affected_subjects = set()
        for node in invalid:
            parts = node.split(":")
            if len(parts) >= 3 and parts[0] == "raw":
                usubjid = parts[2]
                if usubjid != "UNKNOWN":
                    affected_subjects.add(usubjid)
        
        # 2. Materialize through Adapter & Patch Analysis
        import app.analysis as ana
        from stage3.adapter import Stage3Adapter
        from stage3.models import Finding
        adapter = Stage3Adapter(self.state)
        
        original_apply = getattr(ana, "apply_cuts_and_corrections", None)
        
        if not hasattr(self.state, "current_clinical_findings"):
            self.state.current_clinical_findings = {}
            self.state.clinical_finding_hashes = set()
            
        try:
            for usubjid in affected_subjects:
                # Patch for this subject
                def mock_apply(df_in, file_name, cut_val):
                    domain = file_name.replace('.csv', '')
                    return adapter.domain_dataframe(domain, usubjid)
                    
                ana.apply_cuts_and_corrections = mock_apply
                
                # Execute deterministic rules
                raw_findings = []
                # Each function returns {"data": records, "evidence": EvidenceTrail, "metadata": ...}
                for f_name, f_func in [
                    ("SAE", ana.detect_saes),
                    ("HYS_LAW", ana.detect_hys_law),
                    ("DOSING_ERROR", ana.detect_dosing_errors),
                    ("VISIT_DEVIATION", ana.detect_visit_deviations),
                    ("PROHIBITED_MED", ana.detect_prohibited_meds),
                    ("TEAE", ana.detect_teae),
                    ("EXCLUSION", ana.detect_exclusion_violations)
                ]:
                    res = f_func(self.state.current_cut)
                    for data_row in res.get("data", []):
                        raw_findings.append({
                            "type": f_name,
                            "data": data_row,
                            "evidence": res.get("evidence")
                        })
                
                self.state.current_clinical_findings[usubjid] = raw_findings
                
                # Check for new findings to return for Tracing
                for rf in raw_findings:
                    # Simple hash for uniqueness across time
                    import hashlib
                    # Include usubjid and type and stable keys
                    content = f"{usubjid}-{rf['type']}-{rf['data'].get('VISIT', '')}-{rf['data'].get('LBSEQ', '')}"
                    f_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    if f_hash not in self.state.clinical_finding_hashes:
                        self.state.clinical_finding_hashes.add(f_hash)
                        
                        f_model = Finding(
                            finding_id=f"CLIN-{f_hash}",
                            finding_type=f"CLINICAL_{rf['type']}",
                            severity="HIGH",
                            scope={"usubjid": usubjid},
                            evidence=[], # We could translate EvidenceTrail to Evidence models here
                            confidence=1.0,
                            recommended_action="REVIEW",
                            metadata=rf['data']
                        )
                        new_findings.append(f_model)
                        
        finally:
            if original_apply:
                ana.apply_cuts_and_corrections = original_apply
                
        # 3. Mark Valid
        for node in invalid:
            self.state.dependency_graph.mark_valid(node)
            self.metrics["recomputed_nodes"] += 1
            
        valid_count = len([nid for nid, is_v in self.state.dependency_graph.validity.items() if is_v])
        self.metrics["reused_nodes"] = valid_count
        
        return new_findings

    def explain(self, decision_id: str) -> Explanation:
        rec = self.trace.get_decision(decision_id)
        return Explanation(
            decision_id=rec.decision_id,
            historical_cut=rec.cut,
            action=rec.action,
            what=rec.what,
            why=rec.why,
            policy=rec.policy,
            evidence_snapshot=rec.evidence
        )
        
    def run_period(self, cuts: range = range(1, 13)) -> Dict[str, Any]:
        report = {
            "period": "1-12",
            "cuts_processed": 0,
            "signals": [],
            "critical_signals": [],
            "site_risk": [],
            "adversarial_events": [],
            "deviations": [],
            "quarantined_records": [],
            "escalations": [],
            "unresolved_items": [],
            "corrections": [],
            "amendments": [],
            "budget_used": 0,
            "degraded_mode": False,
            "recomputation_metrics": {},
            "decisions": [],
            "audit_summary": ""
        }
        
        for cut in cuts:
            # 1. Ingest, deduplicate, process corrections
            self.process_cut(cut)
            
            # 2. Verify protocol hashes
            protocol_dir = os.path.join(self.data_dir, "protocol")
            doc_findings = self.doc_detector.detect(protocol_dir, cut)
            
            # 3. Process amendments (mock via amendment_detector for now)
            amend_findings = self.amend_detector.detect(self.state, cut, False, [])
            
            # 4. Invalidate & Recompute
            clin_findings = self.recompute_invalidated_nodes()
            
            # 5. Run adversarial detectors
            unit_f = self.unit_detector.detect(self.state, cut)
            site_f = self.site_detector.detect(self.state, cut)
            
            findings = doc_findings + amend_findings + unit_f + site_f + clin_findings
            
            # 6. Quarantine & Policy & Trace
            for f in findings:
                dec = self.policy.evaluate(f)
                
                if "QUARANTINE" in dec.action:
                    for ev in f.evidence:
                        if ev.record_id and ev.record_id in self.state.records:
                            self.state.records[ev.record_id].is_trusted = False
                            report["quarantined_records"].append(ev.record_id)
                
                if "ESCALATE" in dec.action or "QUERY" in dec.action:
                    esc = self.escalations.create_escalation(cut, note=f"Escalated due to {f.finding_type}")
                    report["escalations"].append(esc.escalation_id)
                    
                dec_id = self.trace.add_decision(
                    cut=cut,
                    decision_type=f.finding_type,
                    action=dec.action,
                    what=str(f.scope),
                    evidence=f.evidence,
                    why=dec.why,
                    policy=dec.policy
                )
                report["decisions"].append(dec_id)
                report["adversarial_events"].append(f.finding_type)
                
            # 7. Tick escalations
            self.escalations.tick(cut)
            
            # 8. Budget
            self.budget.record_call(cut, 500)
            if self.budget.degraded_mode:
                report["degraded_mode"] = True
                
            report["cuts_processed"] += 1
            
        report["budget_used"] = self.budget.consumed
        report["recomputation_metrics"] = self.metrics
        
        for esc in self.escalations.escalations.values():
            if esc.current_state in ["PENDING", "STANDING_LIMITS", "CLARIFY", "EXPIRED_UNANSWERED"]:
                report["unresolved_items"].append(esc.escalation_id)
                
        return report
