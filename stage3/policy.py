from typing import List, Tuple
from stage3.models import Finding

class Decision(object):
    def __init__(self, action: str, why: str, policy: str):
        self.action = action
        self.why = why
        self.policy = policy

class PolicyEngine:
    def __init__(self):
        # Map finding type to action & policy justification
        self.policies = {
            "DATA_INTEGRITY_UNIT_CORRUPTION": ("QUARANTINE + QUERY", "Standard operating procedure for extreme uncorroborated laboratory shifts."),
            "SUSPICIOUS_SITE_REGULARITY": ("QUARANTINE_SITE + AUDIT", "Protocol mandates site quarantine upon statistically impossible variance."),
            "PERSISTENT_LAB_DISTRIBUTION_DRIFT": ("MONITOR", "Gradual drifts require monitoring before escalation."),
            "DOCUMENT_TAMPERED": ("REJECT_INSTRUCTION + AUDIT", "Security policy strictly rejects unverified document modifications."),
            "AMENDMENT_IMPACT": ("RECOMPUTE_AFFECTED", "Protocol amendments necessitate targeted dependency invalidation."),
            "SERIOUS_CLINICAL_EVENT": ("ESCALATE", "Immediate clinical emergency detected.")
        }
        
    def evaluate(self, finding: Finding) -> Decision:
        action, policy_justification = self.policies.get(finding.finding_type, ("MONITOR", "Default fallback for unknown findings."))
        
        # We can dynamically alter based on confidence or other criteria
        why = f"Finding {finding.finding_type} with confidence {finding.confidence} triggered standard action."
        
        return Decision(action=action, why=why, policy=policy_justification)
