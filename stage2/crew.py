import uuid
from typing import Dict, Any, List
from stage1.atlas import Atlas
from stage2.models import ReviewReport, TraceEntry, Escalation, Query, SiteFlag
from stage2.memory import memory
import datetime

class ReviewCrew:
    def __init__(self, hub_url: str = "", gateway_url: str = "", team_key: str = "", atlas: Atlas = None):
        self.atlas = atlas or Atlas()
        self.trace: List[TraceEntry] = []
        self.findings = {}
        self.current_cut = 0
        self.protocol_version = 0

    def add_trace(self, node: str, decision: str, evidence: List[Dict[str, Any]] = None):
        self.trace.append(TraceEntry(
            node=node,
            decision=decision,
            evidence=evidence or []
        ))

    def detect(self):
        # Gather deterministic findings
        saes = self.atlas.detect_saes(self.current_cut)["data"]
        hys = self.atlas.detect_hys_law(self.current_cut)["data"]
        dosing = self.atlas.detect_dosing_errors(self.current_cut)["data"]
        devs = self.atlas.detect_visit_deviations(self.current_cut)["data"]
        meds = self.atlas.detect_prohibited_meds(self.current_cut)["data"]
        teae = self.atlas.detect_teae(self.current_cut)["data"]
        exclusions = self.atlas.detect_exclusion_violations(self.current_cut)["data"]
        
        self.findings = {
            "saes": saes,
            "hys_law": hys,
            "dosing_errors": dosing,
            "visit_deviations": devs,
            "prohibited_meds": meds,
            "teae": teae,
            "exclusion_violations": exclusions
        }
        
        total_findings = sum(len(v) for v in self.findings.values())
        self.add_trace("detect", f"{total_findings} findings under protocol v{self.protocol_version}")

    def medical_review(self):
        # Classify findings (ESCALATE, MONITOR, QUERY)
        saes = self.findings.get("saes", [])
        hys_law = self.findings.get("hys_law", [])
        
        # Track subjects flagged in this cycle
        current_cycle_subjects = set()
        for v in self.findings.values():
            for item in v:
                if "USUBJID" in item:
                    current_cycle_subjects.add(item["USUBJID"])
                    
        # Update memory
        memory.subject_flags_history[str(memory.cycle_count)] = list(current_cycle_subjects)
        memory.save()
        
        escalated_count = 0
        
        # Check recurring subjects
        for usubjid in current_cycle_subjects:
            past_cycles = []
            for cyc_str, subjects in memory.subject_flags_history.items():
                if int(cyc_str) != memory.cycle_count and usubjid in subjects:
                    past_cycles.append(int(cyc_str))
            if past_cycles:
                escalation_id = f"RECURRING_SUBJ_{usubjid}"
                if not memory.has_escalation(escalation_id):
                    esc = Escalation(
                        id=escalation_id,
                        code="SUBJECT_RECURRING_FINDINGS",
                        usubjid=usubjid,
                        severity="HIGH",
                        summary=f"Subject flagged in multiple cycles: past {past_cycles}, current {memory.cycle_count}.",
                        evidence=[{"past_cycles": past_cycles, "current_cycle": memory.cycle_count}],
                        alternatives=["Review subject broadly"],
                        cycle=memory.cycle_count
                    )
                    memory.add_escalation(esc)
                    self.add_trace("medical_review", f"recurring subject detected -> escalation created for {usubjid}")
                    escalated_count += 1
                    
        for sae in saes:
            is_miscoded = sae.get('AESHOSP') == 'Y' and sae.get('AESER') == 'N'
            reason = "AESHOSP=Y and AESER=N indicates miscoded SAE requiring escalation." if is_miscoded else "SAE requires same-cycle escalation."
            
            # Check memory for duplicate
            escalation_id = f"SAE_{sae['USUBJID']}_{sae.get('AESEQ', '')}"
            if not memory.has_escalation(escalation_id):
                esc = Escalation(
                    id=escalation_id,
                    code="SAE_MISCODED" if is_miscoded else "SAE_DETECTED",
                    usubjid=sae['USUBJID'],
                    severity="CRITICAL",
                    summary=f"Serious Adverse Event: {sae.get('AETERM')}. {reason}",
                    evidence=[sae],
                    alternatives=["Downgrade to MONITOR if reviewed"],
                    cycle=memory.cycle_count
                )
                memory.add_escalation(esc)
                self.add_trace("medical_review", f"Escalated {esc.code} for {esc.usubjid}")
                escalated_count += 1

        for hy in hys_law:
            usubjid = hy['USUBJID']
            is_baseline_elevated = False # Could check evidence if available
            if "baseline_elevated" in hy or (hy.get("screening_alt", 0) > 40): # approximation if needed
                is_baseline_elevated = True
            
            escalation_id = f"HYS_{usubjid}"
            if is_baseline_elevated:
                self.add_trace("medical_review", f"Hy's Law candidate {usubjid} remains monitoring as screening value was already high.")
            elif not memory.has_escalation(escalation_id):
                esc = Escalation(
                    id=escalation_id,
                    code="HYS_LAW_SIGNAL",
                    usubjid=usubjid,
                    severity="CRITICAL",
                    summary="Potential Hy's Law signal detected. Medical monitor adjudication required.",
                    evidence=[hy],
                    alternatives=["Downgrade if baseline elevated or alternative etiology"],
                    cycle=memory.cycle_count
                )
                memory.add_escalation(esc)
                self.add_trace("medical_review", f"Escalated HYS_LAW_SIGNAL for {usubjid}")
                escalated_count += 1
                
        if escalated_count == 0 and len(saes) == 0 and len(hys_law) == 0:
            self.add_trace("medical_review", "No new findings requiring medical review escalation.")

    def data_manager(self):
        # Convert genuine data problems to queries
        dosing_errors = self.findings.get("dosing_errors", [])
        
        # Track errors per site
        site_errors = {}
        queries_raised = 0
        for err in dosing_errors:
            # Assuming err has SITEID, if not we fall back to string parsing or None
            siteid = err.get('SITEID', err.get('USUBJID', '').split('-')[1] if '-' in err.get('USUBJID', '') else 'UNKNOWN')
            site_errors[siteid] = site_errors.get(siteid, 0) + 1
            
            query_id = f"DOSE_{err['USUBJID']}_{err.get('VISIT', '')}"
            if not memory.has_query(query_id):
                q = Query(
                    id=query_id,
                    usubjid=err['USUBJID'],
                    text=f"Dosing error at {err.get('VISIT')}. Administered dose {err.get('EXDOSE')} deviates from expected. Please verify against source.",
                    evidence=[err],
                    cycle=memory.cycle_count,
                    siteid=siteid
                )
                memory.add_query(q)
                self.add_trace("data_manager", f"Raised query for dosing error {q.usubjid} at {err.get('VISIT')}")
                queries_raised += 1
                
        for site, count in site_errors.items():
            if count > 1: # Arbitrary threshold for recurring site issue
                flag = SiteFlag(siteid=site, reason=f"Recurring dosing errors ({count})", cycle=memory.cycle_count)
                memory.add_site_flag(flag)
                
                escalation_id = f"SITE_DOSING_{site}"
                if not memory.has_escalation(escalation_id):
                    esc = Escalation(
                        id=escalation_id,
                        code="SITE_RECURRING_DOSING",
                        usubjid=f"SITE-{site}",
                        severity="HIGH",
                        summary=f"Multiple subjects at site {site} have wrong dose.",
                        evidence=[e for e in dosing_errors if e.get('SITEID', e.get('USUBJID', '').split('-')[1] if '-' in e.get('USUBJID', '') else 'UNKNOWN') == site],
                        alternatives=["Site retraining"],
                        cycle=memory.cycle_count,
                        siteid=site
                    )
                    memory.add_escalation(esc)
                    self.add_trace("data_manager", f"multiple subjects at site -> site escalation created for {site}")
                else:
                    self.add_trace("data_manager", f"Site-level flag generated for {site}: {flag.reason}")
                
        if queries_raised == 0 and len(dosing_errors) == 0:
            self.add_trace("data_manager", "No new data quality issues detected.")
                
    def compliance(self):
        # Check compliance against cut/protocol version
        devs = self.findings.get("visit_deviations", [])
        meds = self.findings.get("prohibited_meds", [])
        excl = self.findings.get("exclusion_violations", [])
        
        total_devs = len(devs) + len(meds) + len(excl)
        self.add_trace("compliance", f"Detected {total_devs} protocol compliance findings at cut {self.current_cut}")
        
    def human_gate(self):
        # Process monitor decisions
        escalations = memory.escalations
        acted_count = 0
        for esc in escalations:
            # We only act on pending ones that just got a decision or need clarification
            if esc.status == "APPROVED" and not esc.executed:
                self.add_trace("human_gate", f"{esc.code} {esc.usubjid} -> APPROVED: {esc.reason or 'actioned'}")
                esc.executed = True
                memory.update_escalation(esc)
                acted_count += 1
            elif esc.status == "REJECTED" and not esc.executed:
                self.add_trace("human_gate", f"{esc.code} {esc.usubjid} -> REJECTED: downgraded to monitoring")
                esc.executed = True
                memory.update_escalation(esc)
                acted_count += 1
            elif esc.status == "CLARIFY" and not esc.executed:
                question = esc.reason.lower() if esc.reason else ""
                answer_parts = []
                
                # Retrieve from graph dynamically
                if "alt" in question or "ast" in question or "lab" in question or "screening" in question:
                    labs = self.atlas.get_subject_labs(esc.usubjid, self.current_cut).get("data", [])
                    relevant_labs = [l for l in labs if l.get('LBTESTCD') in ['ALT', 'AST'] and l.get('VISIT') == 'SCREENING']
                    if relevant_labs:
                        answer_parts.append(f"Screening Labs: {relevant_labs}")
                        
                if "medicine" in question or "medication" in question or "cm" in question:
                    meds = self.atlas.detect_prohibited_meds(self.current_cut).get("data", [])
                    subj_meds = [m for m in meds if m.get('USUBJID') == esc.usubjid]
                    if subj_meds:
                        answer_parts.append(f"Relevant Medications: {subj_meds}")
                        
                final_answer = " | ".join(answer_parts) if answer_parts else "The available deterministic dataset does not contain sufficient evidence to answer this question."
                
                self.add_trace("human_gate", f"CLARIFY -> graph lookup -> evidence retrieved -> answer constructed -> resubmitted")
                esc.status = "PENDING"
                esc.clarification_history.append({"question": esc.reason, "answer": final_answer})
                memory.update_escalation(esc)
                acted_count += 1
                
        if acted_count == 0:
            self.add_trace("human_gate", "No human gate actions processed this cycle.")
                
    def execute(self) -> ReviewReport:
        findings_count = sum(len(v) for v in self.findings.values())
        new_escalations = len([e for e in memory.escalations if e.cycle == memory.cycle_count])
        new_queries = len([q for q in memory.queries if q.cycle == memory.cycle_count])
        total_devs = len(self.findings.get("visit_deviations", [])) + len(self.findings.get("prohibited_meds", [])) + len(self.findings.get("exclusion_violations", []))
        
        self.add_trace("execute", f"cycle complete: {findings_count} findings, {new_escalations} escalations, {new_queries} queries, {total_devs} deviations")
        
        return ReviewReport(
            cycle=memory.cycle_count,
            cut=self.current_cut,
            protocol_version=self.protocol_version,
            findings=findings_count,
            escalations=len(memory.escalations),
            queries=len(memory.queries),
            deviations=total_devs,
            site_flags=len(memory.site_flags),
            monitor_decisions=len([e for e in memory.escalations if e.monitor_decision is not None]),
            trace={"entries": [t.dict() for t in self.trace]},
            memory_state={
                "escalations": [e.dict() for e in memory.escalations],
                "queries": [q.dict() for q in memory.queries]
            }
        )

    def run_cycle(self, cut: int, protocol_version: int) -> ReviewReport:
        self.trace = []
        self.current_cut = cut
        self.protocol_version = protocol_version
        
        # Advance cycle counter
        memory.next_cycle()

        self.detect()
        self.medical_review()
        self.data_manager()
        self.compliance()
        self.human_gate()
        
        return self.execute()
