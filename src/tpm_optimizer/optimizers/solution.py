from dataclasses import dataclass
from typing import Dict
from ..models import TPM, Program
from ..utils.timezone import timezone_difference

class Solution:
    def __init__(self, assignments: Dict[str, str], tpms: Dict[str, TPM], programs: Dict[str, Program]):
        self.assignments = assignments
        self.tpms = tpms
        self.programs = programs
        self.metrics = self._calculate_metrics()

    def _count_unused_tpms(self) -> int:
        used_tpms = set(self.assignments.values())
        return len(self.tpms) - len(used_tpms)

    def _count_overloaded_tpms(self) -> int:
        tpm_loads = {tpm_id: 0.0 for tpm_id in self.tpms}
        for prog_id, tpm_id in self.assignments.items():
            tpm_loads[tpm_id] += self.programs[prog_id].required_time

        return sum(1 for tpm_id, load in tpm_loads.items()
                   if not self.tpms[tpm_id].allow_overload
                   and load > self.tpms[tpm_id].available_time)

    def _count_timezone_violations(self) -> int:
        violations = 0
        for prog_id, tpm_id in self.assignments.items():
            tz_diff = timezone_difference(self.tpms[tpm_id].timezone,
                                      self.programs[prog_id].timezone)
            if tz_diff > 6:
                violations += 1
        return violations

    def _count_portfolio_violations(self) -> int:
        tpm_portfolios = {}
        for prog_id, tpm_id in self.assignments.items():
            if tpm_id not in tpm_portfolios:
                tpm_portfolios[tpm_id] = set()
            tpm_portfolios[tpm_id].add(self.programs[prog_id].portfolio)

        return sum(1 for portfolios in tpm_portfolios.values()
                   if len(portfolios) > 2)

    def _calculate_metrics(self) -> Dict[str, float]:
        return {
            'unused_tpms': self._count_unused_tpms(),
            'overloaded_tpms': self._count_overloaded_tpms(),
            'timezone_violations': self._count_timezone_violations(),
            'portfolio_violations': self._count_portfolio_violations()
        }

    def dominates(self, other: 'Solution') -> bool:
        """Returns True if this solution Pareto-dominates the other"""
        at_least_one_better = False
        for metric, value in self.metrics.items():
            if value > other.metrics[metric]:  # Higher values are worse
                return False
            if value < other.metrics[metric]:
                at_least_one_better = True
        return at_least_one_better

    def is_feasible(self) -> bool:
        """Check if solution satisfies hard constraints"""
        # Check fixed assignments
        for prog_id, program in self.programs.items():
            if program.fixed_tpm:
                if prog_id not in self.assignments or self.assignments[prog_id] != program.fixed_tpm:
                    return False

        # No overloaded TPMs unless allowed
        if self._count_overloaded_tpms() > 0:
            return False

        return True
