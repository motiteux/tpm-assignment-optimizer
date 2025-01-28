from typing import Dict
from ..models import TPM, Program, TPMConstraints
from ..utils.timezone import calculate_timezone_score, timezone_difference


class BaseOptimizer:
    def __init__(self, tpms: Dict[str, TPM], programs: Dict[str, Program]):
        self.tpms = tpms
        self.programs = programs
        self.assignments = {}
        # Validate and store fixed assignments
        self.fixed_assignments = {
            prog_id: program.fixed_tpm
            for prog_id, program in programs.items()
            if program.fixed_tpm and program.fixed_tpm.strip()
        }

    def validate_assignment(self, prog_id: str, tpm_id: str) -> bool:
        """Validate if a program can be assigned to a TPM"""
        program = self.programs[prog_id]
        tpm = self.tpms[tpm_id]

        if tpm.level < program.required_level:
            return False

        if prog_id in tpm.conflicts:
            return False

        current_load = sum(self.programs[p].required_time
                          for p in self.assignments
                          if self.assignments[p] == tpm_id and p != prog_id)

        if not tpm.allow_overload and (current_load + program.required_time > tpm.available_time):
            return False

        assigned_portfolios = set(self.programs[p].portfolio
                                for p in self.assignments
                                if self.assignments[p] == tpm_id)
        if program.portfolio not in assigned_portfolios and len(assigned_portfolios) >= TPMConstraints.MAX_PORTFOLIOS:
            return False

        return True

    def validate_fixed_assignments_solution(self, solution: Dict[str, str]) -> bool:
        """Verify all fixed assignments are respected in a solution"""
        for prog_id, fixed_tpm in self.fixed_assignments.items():
            if prog_id not in solution or solution[prog_id] != fixed_tpm:
                return False
        return True

    def calculate_assignment_score(self, prog_id: str, tpm_id: str) -> float:
        """Calculate score for assigning a program to a TPM"""
        program = self.programs[prog_id]
        tpm = self.tpms[tpm_id]

        if not self.validate_assignment(prog_id, tpm_id):
            return -float('inf')

        timezone_score = calculate_timezone_score(tpm.timezone, program)
        skill_score = len(tpm.skills.intersection(program.required_skills)) / len(program.required_skills)
        level_score = self._calculate_level_score(tpm.level, program.required_level)
        preference_score = 0.2 if prog_id in tpm.desired_programs else 0.0

        assigned_portfolios = set(self.programs[p].portfolio
                                for p in self.assignments
                                if self.assignments[p] == tpm_id)
        portfolio_score = 1.0 if program.portfolio in assigned_portfolios else 0.5

        return (0.3 * timezone_score +
                0.25 * skill_score +
                0.2 * level_score +
                0.15 * portfolio_score +
                0.1 * preference_score)

    def _calculate_level_score(self, tpm_level: int, required_level: int) -> float:
        if tpm_level == required_level:
            return 1.0
        elif tpm_level == required_level + 1:
            return 0.7
        elif tpm_level > required_level + 1:
            return 0.4
        else:
            return 0.0

    def optimize(self) -> Dict[str, str]:
        """Abstract method to be implemented by specific optimizers"""
        raise NotImplementedError