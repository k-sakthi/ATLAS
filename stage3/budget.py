class BudgetGovernor:
    def __init__(self, total_budget: int = 100000):
        self.total_budget = total_budget
        self.consumed = 0
        self.llm_calls = 0
        self.skipped_calls = 0
        self.per_cut_usage = {}
        
    @property
    def remaining(self) -> int:
        return max(0, self.total_budget - self.consumed)
        
    @property
    def percentage_used(self) -> float:
        if self.total_budget == 0:
            return 100.0
        return (self.consumed / self.total_budget) * 100.0
        
    @property
    def degraded_mode(self) -> bool:
        return self.percentage_used >= 80.0
        
    @property
    def exhausted(self) -> bool:
        return self.consumed >= self.total_budget

    def consume(self, cut: int, amount: int):
        self.consumed += amount
        self.per_cut_usage[cut] = self.per_cut_usage.get(cut, 0) + amount
        
    def can_make_optional_call(self) -> bool:
        if self.degraded_mode:
            self.skipped_calls += 1
            return False
        return True
        
    def record_call(self, cut: int, estimated_tokens: int):
        self.llm_calls += 1
        self.consume(cut, estimated_tokens)
