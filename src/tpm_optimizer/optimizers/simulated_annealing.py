from typing import Dict
import random
import math
from .base import BaseOptimizer
from ..models import TPM, Program
from ..utils.timezone import timezone_difference


class SimulatedAnnealingOptimizer(BaseOptimizer):
    def __init__(self, tpms: Dict[str, TPM], programs: Dict[str, Program]):
        super().__init__(tpms, programs)
        # SA parameters
        self.temperature = 1.0
        self.cooling_rate = 0.995
        self.min_temperature = 0.001
        self.max_iterations = 10000

    def calculate_solution_score(self, solution: Dict[str, str]) -> float:
        """Calculate comprehensive score for a solution"""
        total_score = 0.0
        portfolio_violations = 0
        timezone_violations = 0
        capacity_violations = 0
        underutilization_penalties = 0

        # Track TPM loads and usage
        tpm_loads = {tpm_id: 0.0 for tpm_id in self.tpms}
        tpm_used = {tpm_id: False for tpm_id in self.tpms}

        MIN_UTILIZATION = 0.7  # Minimum desired utilization

        for prog_id, tpm_id in solution.items():
            program = self.programs[prog_id]
            tpm = self.tpms[tpm_id]

            # Update TPM load and usage
            tpm_loads[tpm_id] += program.required_time
            tpm_used[tpm_id] = True

            # Check capacity violation
            if not tpm.allow_overload and tpm_loads[tpm_id] > tpm.available_time:
                capacity_violations += (tpm_loads[tpm_id] - tpm.available_time) * 100

            # Assignment score
            assignment_score = self.calculate_assignment_score(prog_id, tpm_id)
            if assignment_score == -float('inf'):
                return -float('inf')

            total_score += assignment_score

            # Portfolio diversity check
            assigned_portfolios = set(self.programs[p].portfolio
                                      for p, t in solution.items()
                                      if t == tpm_id)
            if len(assigned_portfolios) > 2:
                portfolio_violations += 1

            # Timezone check
            tz_diff = timezone_difference(tpm.timezone, program.timezone)
            if tz_diff > 6:
                timezone_violations += 1

        # Add stronger utilization penalty
        severe_underutilization = 0
        for tpm_id, load in tpm_loads.items():
            if tpm_used[tpm_id]:  # Only penalize TPMs that are being used
                utilization = load / self.tpms[tpm_id].available_time
                if utilization < MIN_UTILIZATION:
                    underutilization_penalties += (MIN_UTILIZATION - utilization) * 5.0
                    if utilization < 0.5:  # Severe underutilization
                        severe_underutilization += (0.5 - utilization) * 10.0

        # Penalize unused TPMs when they could take work
        unused_tpms = sum(1 for used in tpm_used.values() if not used)
        overloaded_tpms = sum(1 for tpm_id, load in tpm_loads.items()
                              if load > self.tpms[tpm_id].available_time and
                              not self.tpms[tpm_id].allow_overload)

        if unused_tpms > 0 and overloaded_tpms > 0:
            total_score -= (unused_tpms * overloaded_tpms * 5.0)

        # Apply all penalties
        total_score -= (portfolio_violations * 2.0 +
                        timezone_violations * 1.5 +
                        capacity_violations * 10.0 +
                        underutilization_penalties +
                        severe_underutilization)

        return total_score

    def get_neighbor_solution(self, current_solution: Dict[str, str]) -> Dict[str, str]:
        """Generate a neighbor solution with small modifications"""
        neighbor = current_solution.copy()

        # Get only non-fixed assignments
        movable_programs = [prog_id for prog_id in current_solution.keys()
                            if prog_id not in self.fixed_assignments]

        if len(movable_programs) < 1:
            return neighbor

        if random.random() < 0.5 and len(movable_programs) >= 2:
            # Swap two non-fixed assignments
            prog1, prog2 = random.sample(movable_programs, 2)
            neighbor[prog1], neighbor[prog2] = neighbor[prog2], neighbor[prog1]
        else:
            # Change single non-fixed assignment
            prog = random.choice(movable_programs)
            available_tpms = [tpm_id for tpm_id in self.tpms.keys()
                              if self.validate_assignment(prog, tpm_id)]
            if available_tpms:
                neighbor[prog] = random.choice(available_tpms)

        return neighbor

    def optimize(self) -> Dict[str, str]:
        """Run simulated annealing optimization"""
        # Start with fixed assignments
        current_solution = self.fixed_assignments.copy()

        # Random initial assignment for remaining programs
        unassigned = [prog_id for prog_id in self.programs
                      if prog_id not in current_solution]

        for prog_id in unassigned:
            available_tpms = [tpm_id for tpm_id in self.tpms.keys()
                              if self.validate_assignment(prog_id, tpm_id)]
            if available_tpms:
                current_solution[prog_id] = random.choice(available_tpms)

        current_score = self.calculate_solution_score(current_solution)
        best_solution = current_solution.copy()
        best_score = current_score

        temperature = self.temperature
        iteration = 0

        while temperature > self.min_temperature and iteration < self.max_iterations:
            neighbor = self.get_neighbor_solution(current_solution)

            # Skip invalid solutions
            if not self.validate_fixed_assignments_solution(neighbor):
                continue

            neighbor_score = self.calculate_solution_score(neighbor)

            # Accept better solutions
            if neighbor_score > current_score:
                current_solution = neighbor
                current_score = neighbor_score
                if current_score > best_score:
                    best_solution = current_solution.copy()
                    best_score = current_score
            else:
                # Accept worse solutions with probability based on temperature
                delta = neighbor_score - current_score
                probability = math.exp(delta / temperature)
                if random.random() < probability:
                    current_solution = neighbor
                    current_score = neighbor_score

            temperature *= self.cooling_rate
            iteration += 1

            # Optional progress reporting
            if iteration % 1000 == 0:
                print(f"Iteration {iteration}, Temperature: {temperature:.4f}, "
                      f"Current Score: {current_score:.2f}, Best Score: {best_score:.2f}")

        # Final validation
        if not self.validate_fixed_assignments_solution(best_solution):
            raise ValueError("Optimization failed to respect fixed assignments")

        self.assignments = best_solution
        return self.assignments

    def set_parameters(self, temperature: float = 1.0, cooling_rate: float = 0.995,
                       min_temperature: float = 0.001, max_iterations: int = 10000):
        """Allow customization of SA parameters"""
        self.temperature = temperature
        self.cooling_rate = cooling_rate
        self.min_temperature = min_temperature
        self.max_iterations = max_iterations