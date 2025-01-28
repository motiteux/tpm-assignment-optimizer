from typing import Dict
from ..models import TPM, Program, ConstraintType, TPMConstraints
from ..utils import timezone_difference

class Objective:
    def __init__(self, name: str, constraint_type: ConstraintType):
        self.name = name
        self.constraint_type = constraint_type

    def evaluate(self, solution: Dict[str, str], tpms: Dict[str, TPM],
                 programs: Dict[str, Program]) -> float:
        raise NotImplementedError


class CapacityObjective(Objective):
    def evaluate(self, solution: Dict[str, str], tpms: Dict[str, TPM],
                 programs: Dict[str, Program]) -> float:
        tpm_loads = {tpm_id: 0.0 for tpm_id in tpms}
        for prog_id, tpm_id in solution.items():
            tpm_loads[tpm_id] += programs[prog_id].required_time

        violations = 0
        for tpm_id, load in tpm_loads.items():
            if not tpms[tpm_id].allow_overload and load > tpms[tpm_id].available_time:
                violations += (load - tpms[tpm_id].available_time) * 100
        return -violations


class UtilizationObjective(Objective):
    def evaluate(self, solution: Dict[str, str], tpms: Dict[str, TPM],
                 programs: Dict[str, Program]) -> float:
        tpm_loads = {tpm_id: 0.0 for tpm_id in tpms}
        for prog_id, tpm_id in solution.items():
            tpm_loads[tpm_id] += programs[prog_id].required_time

        score = 0
        for tpm_id, load in tpm_loads.items():
            if load > 0:  # Only consider utilized TPMs
                utilization = load / tpms[tpm_id].available_time
                if utilization < TPMConstraints.MIN_UTILIZATION:
                    score -= (TPMConstraints.MIN_UTILIZATION - utilization) * 5
        return score


class TimezoneObjective(Objective):
    def evaluate(self, solution: Dict[str, str], tpms: Dict[str, TPM],
                 programs: Dict[str, Program]) -> float:
        score = 0
        for prog_id, tpm_id in solution.items():
            tz_diff = timezone_difference(tpms[tpm_id].timezone,
                                      programs[prog_id].timezone)
            if tz_diff <= TPMConstraints.PREFERRED_TIMEZONE_SPREAD:
                score += 1
            elif tz_diff <= TPMConstraints.MAX_TIMEZONE_SPREAD:
                score += 0.5
            else:
                score -= 1
        return score


class PortfolioObjective(Objective):
    def evaluate(self, solution: Dict[str, str], tpms: Dict[str, TPM],
                 programs: Dict[str, Program]) -> float:
        tpm_portfolios = {}
        for prog_id, tpm_id in solution.items():
            if tpm_id not in tpm_portfolios:
                tpm_portfolios[tpm_id] = set()
            tpm_portfolios[tpm_id].add(programs[prog_id].portfolio)

        score = 0
        for portfolios in tpm_portfolios.values():
            if len(portfolios) > TPMConstraints.MAX_PORTFOLIOS:
                score -= (len(portfolios) - TPMConstraints.MAX_PORTFOLIOS) * 2
            elif len(portfolios) == TPMConstraints.TARGET_PORTFOLIO_DIVERSITY:
                score += 1
        return score