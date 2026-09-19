import json
import os
from typing import List, Dict, Any, Optional
from stage2.models import Escalation, Query, SiteFlag

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "stage2_memory.json")

class Memory:
    def __init__(self):
        self.queries: List[Query] = []
        self.escalations: List[Escalation] = []
        self.site_flags: List[SiteFlag] = []
        self.subject_flags_history: Dict[str, List[str]] = {} # cycle_count -> list of usubjids
        self.cycle_count = 0
        self.load()

    def load(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r") as f:
                    data = json.load(f)
                    self.queries = [Query(**q) for q in data.get("queries", [])]
                    self.escalations = [Escalation(**e) for e in data.get("escalations", [])]
                    self.site_flags = [SiteFlag(**sf) for sf in data.get("site_flags", [])]
                    self.subject_flags_history = data.get("subject_flags_history", {})
                    self.cycle_count = data.get("cycle_count", 0)
            except Exception:
                pass

    def save(self):
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        data = {
            "queries": [q.model_dump() for q in self.queries],
            "escalations": [e.model_dump() for e in self.escalations],
            "site_flags": [sf.model_dump() for sf in self.site_flags],
            "subject_flags_history": self.subject_flags_history,
            "cycle_count": self.cycle_count
        }
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def next_cycle(self) -> int:
        self.cycle_count += 1
        self.save()
        return self.cycle_count

    def get_query(self, query_id: str) -> Optional[Query]:
        for q in self.queries:
            if q.id == query_id:
                return q
        return None

    def has_query(self, query_id: str) -> bool:
        return self.get_query(query_id) is not None

    def add_query(self, query: Query):
        if not self.has_query(query.id):
            self.queries.append(query)
            self.save()

    def get_escalation(self, escalation_id: str) -> Optional[Escalation]:
        for e in self.escalations:
            if e.id == escalation_id:
                return e
        return None

    def has_escalation(self, escalation_id: str) -> bool:
        return self.get_escalation(escalation_id) is not None

    def add_escalation(self, escalation: Escalation):
        if not self.has_escalation(escalation.id):
            self.escalations.append(escalation)
            self.save()
            
    def update_escalation(self, escalation: Escalation):
        for i, e in enumerate(self.escalations):
            if e.id == escalation.id:
                self.escalations[i] = escalation
                self.save()
                return

    def get_site_flags(self) -> List[SiteFlag]:
        return self.site_flags

    def add_site_flag(self, flag: SiteFlag):
        # Avoid exact duplicates
        for sf in self.site_flags:
            if sf.siteid == flag.siteid and sf.reason == flag.reason:
                return
        self.site_flags.append(flag)
        self.save()

# Global memory instance
memory = Memory()

