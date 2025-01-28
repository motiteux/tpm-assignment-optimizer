from typing import Dict, List
from .base import BaseOptimizer
from ..models import TPM, Program
from ..utils.timezone import timezone_difference


class TwoPhaseOptimizer(BaseOptimizer):
    def optimize(self) -> Dict[str, str]:
        """Run two-phase optimization"""
        # Phase 1: Initial feasible solution
        solution = self._create_feasible_solution()

        # Phase 2: Load balancing
        balanced_solution = self._balance_workload(solution)

        self.assignments = balanced_solution
        return self.assignments

    def _create_feasible_solution(self) -> Dict[str, str]:
        """Create initial solution prioritizing optimal load distribution"""
        solution = self.fixed_assignments.copy()
        loads = self._calculate_tpm_loads(solution)

        # Sort programs by complexity and size
        unassigned = [(prog_id, self.programs[prog_id])
                      for prog_id in self.programs
                      if prog_id not in solution]
        unassigned.sort(key=lambda x: (x[1].complexity_score, x[1].required_time),
                        reverse=True)

        for prog_id, program in unassigned:
            # Rank all TPMs for this program
            tpm_rankings = []
            for tpm_id in self.tpms:
                rank = self._rank_tpm_for_program(prog_id, tpm_id, loads)
                if rank > -float('inf'):
                    tpm_rankings.append((rank, tpm_id))

            if tpm_rankings:
                # Choose highest ranked TPM
                best_tpm = max(tpm_rankings, key=lambda x: x[0])[1]
                solution[prog_id] = best_tpm
                loads[best_tpm] = loads.get(best_tpm, 0) + program.required_time

        return solution

    def _balance_workload(self, initial_solution: Dict[str, str]) -> Dict[str, str]:
        """Balance workload with clear priorities"""
        current = initial_solution.copy()
        current = self._fix_overloads(current)
        current = self._reach_minimum_loads(current)
        current = self._optimize_distribution(current)
        return current

    def _calculate_program_constraints(self, prog_id: str) -> int:
        """Calculate how constrained a program is"""
        program = self.programs[prog_id]
        score = 0
        score += program.required_time * 10  # Higher time requirement = more constrained
        score += len(program.stakeholder_timezones)
        score += program.required_level
        return score

    def _find_feasible_tpms(self, prog_id: str, current_solution: Dict[str, str]) -> List[str]:
        """Find all TPMs that can feasibly take this program"""
        return [tpm_id for tpm_id in self.tpms.keys()
                if self._can_assign(prog_id, tpm_id, current_solution)]

    def _can_assign(self, prog_id: str, tpm_id: str, solution: Dict[str, str]) -> bool:
        """Check if assignment is feasible"""
        if not self.validate_assignment(prog_id, tpm_id):
            return False

        # Check timezone spread
        tz_diff = timezone_difference(self.tpms[tpm_id].timezone,
                                      self.programs[prog_id].timezone)
        if tz_diff > 6:
            return False

        # Check portfolio limit
        portfolios = set(self.programs[p].portfolio for p, t in solution.items()
                         if t == tpm_id)
        if (self.programs[prog_id].portfolio not in portfolios and
                len(portfolios) >= 2):
            return False

        return True

    def _calculate_tpm_loads(self, solution: Dict[str, str]) -> Dict[str, float]:
        """Calculate loads for all TPMs"""
        loads = {tpm_id: 0.0 for tpm_id in self.tpms}
        for prog_id, tpm_id in solution.items():
            loads[tpm_id] += self.programs[prog_id].required_time
        return loads

    def _can_move_program(self, prog_id: str, target_tpm: str,
                          solution: Dict[str, str]) -> bool:
        """Check if program can be moved to target TPM"""
        if prog_id in self.fixed_assignments:
            return False

        # Create temporary solution with the move
        temp_solution = solution.copy()
        temp_solution[prog_id] = target_tpm

        # Check if move maintains feasibility
        if not self._can_assign(prog_id, target_tpm, temp_solution):
            return False

        # Check if move would overload target
        new_load = self._calculate_tpm_load(target_tpm, temp_solution)
        if (not self.tpms[target_tpm].allow_overload and
                new_load > self.tpms[target_tpm].available_time):
            return False

        return True

    def _fix_overloads(self, solution: Dict[str, str]) -> Dict[str, str]:
        """Fix any overloaded TPMs"""
        current = solution.copy()
        loads = self._calculate_tpm_loads(current)

        overloaded = [(tid, load) for tid, load in loads.items()
                      if load > 1.0 and not self.tpms[tid].allow_overload]
        overloaded.sort(key=lambda x: x[1], reverse=True)

        for over_tpm, _ in overloaded:
            self._redistribute_load(current, over_tpm, loads)

        return current

    def _reach_minimum_loads(self, solution: Dict[str, str]) -> Dict[str, str]:
        """Try to get all TPMs to minimum load"""
        return solution  # Simplified for now

    def _optimize_distribution(self, solution: Dict[str, str]) -> Dict[str, str]:
        """Optimize load distribution within acceptable range"""
        return solution  # Simplified for now

    def _redistribute_load(self, solution: Dict[str, str],
                           from_tpm: str, loads: Dict[str, float]) -> None:
        """Helper method to redistribute load from overloaded TPM"""
        programs_to_move = [(p, self.programs[p].required_time)
                            for p, t in solution.items()
                            if t == from_tpm and p not in self.fixed_assignments]
        programs_to_move.sort(key=lambda x: x[1])

        other_tpms = [(tid, load) for tid, load in loads.items()
                      if tid != from_tpm and
                      (self.tpms[tid].allow_overload or load < 1.0)]
        other_tpms.sort(key=lambda x: x[1])

        for prog_id, _ in programs_to_move:
            for target_tpm, _ in other_tpms:
                if self.validate_assignment(prog_id, target_tpm):
                    solution[prog_id] = target_tpm
                    loads[from_tpm] -= self.programs[prog_id].required_time
                    loads[target_tpm] += self.programs[prog_id].required_time
                    if loads[from_tpm] <= 1.0:
                        return

    def _rank_tpm_for_program(self, prog_id: str, tpm_id: str,
                             current_loads: Dict[str, float]) -> float:
        """Rank how suitable a TPM is for a program"""
        if not self.validate_assignment(prog_id, tpm_id):
            return -float('inf')

        program = self.programs[prog_id]
        tpm = self.tpms[tpm_id]
        score = 0

        # Capacity fit
        current_load = current_loads.get(tpm_id, 0)
        new_load = current_load + program.required_time
        if new_load <= tpm.available_time:
            # Prefer assignments that get TPM closer to optimal load
            if 0.8 <= new_load <= 0.9:
                score += 100
            elif 0.7 <= new_load < 0.8:
                score += 80
            elif 0.9 < new_load <= 1.0:
                score += 60
        elif not tpm.allow_overload:
            return -float('inf')

        # Timezone match
        tz_diff = timezone_difference(tpm.timezone, program.timezone)
        if tz_diff <= 3:
            score += 50
        elif tz_diff <= 6:
            score += 20

        # Portfolio match
        if program.portfolio in tpm.portfolios:
            score += 30

        return score