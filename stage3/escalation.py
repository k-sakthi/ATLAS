import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class EscalationHistoryEntry(BaseModel):
    cut: int
    state: str
    note: str

class Escalation(BaseModel):
    escalation_id: str
    created_cut: int
    current_state: str = "PENDING"
    unanswered_cuts: int = 0
    required_approval: bool = True
    last_checked_cut: int = 0
    response_metadata: Optional[Dict] = None
    history: List[EscalationHistoryEntry] = Field(default_factory=list)

class EscalationManager:
    def __init__(self):
        self.escalations: Dict[str, Escalation] = {}
        
    def create_escalation(self, cut: int, required_approval: bool = True, note: str = "") -> Escalation:
        esc_id = f"ESC-{cut}-{uuid.uuid4().hex[:8]}"
        esc = Escalation(
            escalation_id=esc_id,
            created_cut=cut,
            required_approval=required_approval,
            last_checked_cut=cut,
            history=[EscalationHistoryEntry(cut=cut, state="PENDING", note=note)]
        )
        self.escalations[esc_id] = esc
        return esc
        
    def process_human_response(self, esc_id: str, cut: int, response: str, note: str = ""):
        if esc_id not in self.escalations:
            return
        esc = self.escalations[esc_id]
        esc.last_checked_cut = cut
        esc.current_state = response
        esc.history.append(EscalationHistoryEntry(cut=cut, state=response, note=note))
        
    def tick(self, cut: int):
        for esc in self.escalations.values():
            if esc.current_state in ["PENDING", "STANDING_LIMITS", "CLARIFY"]:
                if esc.last_checked_cut < cut:
                    esc.unanswered_cuts += 1
                    esc.last_checked_cut = cut
                    
                    if esc.unanswered_cuts >= 4 and esc.current_state != "STANDING_LIMITS":
                        esc.current_state = "STANDING_LIMITS"
                        esc.history.append(EscalationHistoryEntry(
                            cut=cut, 
                            state="STANDING_LIMITS", 
                            note="Approval not received; action remains approval-gated."
                        ))
            
            # End of study handling
            if cut == 12 and esc.current_state in ["PENDING", "STANDING_LIMITS", "CLARIFY"]:
                esc.current_state = "EXPIRED_UNANSWERED"
                esc.history.append(EscalationHistoryEntry(cut=cut, state="EXPIRED_UNANSWERED", note="Study ended without resolution."))
