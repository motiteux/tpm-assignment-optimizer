from typing import Dict, List
import random
import math
from time import time
from .base import BaseOptimizer
from ..models import TPM, Program, ConstraintType
from .solution import Solution

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
        MIN_UTILIZATION = 0.7
        for tpm_id, load in tpm_loads.items():
            if load > 0:  # Only consider utilized TPMs
                utilization = load / tpms[tpm_id].available_time
                if utilization < MIN_UTILIZATION:
                    score -= (MIN_UTILIZATION - utilization) * 5
        return score

class TimezoneObjective(Objective):
    def evaluate(self, solution: Dict[str, str], tpms: Dict[str, TPM],
                 programs: Dict[str, Program]) -> float:
        from ..utils.timezone import timezone_difference
        score = 0
        for prog_id, tpm_id in solution.items():
            tz_diff = timezone_difference(tpms[tpm_id].timezone,
                                       programs[prog_id].timezone)
            if tz_diff <= 3:  # Preferred timezone spread
                score += 1
            elif tz_diff <= 6:  # Maximum timezone spread
                score += 0.5
            else:
                score -= 1
        return score

class PortfolioObjective(Objective):
    def evaluate(self, solution: Dict[str, str], tpms: Dict[str, TPM],
                 programs: Dict[str, Program]) -> float:
        tpm_portfolios = {}
        TARGET_PORTFOLIO_DIVERSITY = 2
        for prog_id, tpm_id in solution.items():
            if tpm_id not in tpm_portfolios:
                tpm_portfolios[tpm_id] = set()
            tpm_portfolios[tpm_id].add(programs[prog_id].portfolio)

        score = 0
        for portfolios in tpm_portfolios.values():
            if len(portfolios) > 2:  # Max portfolios
                score -= (len(portfolios) - 2) * 2
            elif len(portfolios) == TARGET_PORTFOLIO_DIVERSITY:
                score += 1
        return score

class HybridOptimizer(BaseOptimizer):
    def __init__(self, tpms: Dict[str, TPM], programs: Dict[str, Program]):
        super().__init__(tpms, programs)
        self.objectives = [
            CapacityObjective("capacity", ConstraintType.HARD),
            UtilizationObjective("utilization", ConstraintType.SOFT),
            TimezoneObjective("timezone", ConstraintType.SOFT),
            PortfolioObjective("portfolio", ConstraintType.SOFT)
        ]

    def evaluate_solution(self, solution: Dict[str, str]) -> Dict[str, float]:
        """Evaluate all objectives for a solution"""
        scores = {}
        for obj in self.objectives:
            scores[obj.name] = obj.evaluate(solution, self.tpms, self.programs)
        return scores

    def is_feasible(self, solution: Dict[str, str]) -> bool:
        """Check if solution meets all hard constraints"""
        if not self.validate_fixed_assignments_solution(solution):
            return False

        for obj in self.objectives:
            if (obj.constraint_type == ConstraintType.HARD and
                obj.evaluate(solution, self.tpms, self.programs) < 0):
                return False
        return True

    def get_neighbor(self, solution: Dict[str, str]) -> Dict[str, str]:
        """Generate a neighbor solution maintaining feasibility"""
        neighbor = solution.copy()
        attempts = 0
        max_attempts = 50

        while attempts < max_attempts:
            movable_programs = [prog_id for prog_id in solution.keys()
                              if prog_id not in self.fixed_assignments]

            if len(movable_programs) < 1:
                return neighbor

            if random.random() < 0.5 and len(movable_programs) >= 2:
                # Try swapping
                prog1, prog2 = random.sample(movable_programs, 2)
                temp_neighbor = neighbor.copy()
                temp_neighbor[prog1], temp_neighbor[prog2] = temp_neighbor[prog2], temp_neighbor[prog1]
                if self.is_feasible(temp_neighbor):
                    return temp_neighbor
            else:
                # Try reassignment
                prog = random.choice(movable_programs)
                available_tpms = [tpm_id for tpm_id in self.tpms.keys()
                                if self.validate_assignment(prog, tpm_id)]
                if available_tpms:
                    temp_neighbor = neighbor.copy()
                    temp_neighbor[prog] = random.choice(available_tpms)
                    if self.is_feasible(temp_neighbor):
                        return temp_neighbor

            attempts += 1

        return solution

    def optimize(self) -> Dict[str, str]:
        """Run hybrid optimization with Pareto dominance"""
        start_time = time()
        MAX_RUNTIME = 300  # 5 minutes maximum

        print("Creating initial solution...")
        # Start with fixed assignments
        current_solution = Solution(self.fixed_assignments.copy(), self.tpms, self.programs)

        # Initial assignment
        unassigned = [prog_id for prog_id in self.programs
                     if prog_id not in current_solution.assignments]

        # Sort unassigned by complexity and time required
        unassigned.sort(key=lambda x: (self.programs[x].complexity_score,
                                     self.programs[x].required_time),
                       reverse=True)

        print(f"Assigning {len(unassigned)} programs...")
        assignments = current_solution.assignments.copy()
        for prog_id in unassigned:
            available_tpms = [tpm_id for tpm_id in self.tpms.keys()
                            if self.validate_assignment(prog_id, tpm_id)]
            if available_tpms:
                best_tpm = None
                best_metrics = None
                for tpm_id in available_tpms:
                    temp_assignments = assignments.copy()
                    temp_assignments[prog_id] = tpm_id
                    temp_solution = Solution(temp_assignments, self.tpms, self.programs)
                    if best_metrics is None or temp_solution.dominates(best_metrics):
                        best_tpm = tpm_id
                        best_metrics = temp_solution

                if best_tpm:
                    assignments[prog_id] = best_tpm

        current_solution = Solution(assignments, self.tpms, self.programs)
        best_solution = current_solution

        # Simulated annealing with Pareto dominance
        temperature = 1.0
        cooling_rate = 0.99
        min_temperature = 0.001
        iteration = 0
        max_iterations = 5000
        no_improvement_limit = 1000
        no_improvement_count = 0

        print("\nStarting optimization:")
        while (temperature > min_temperature and
               iteration < max_iterations and
               time() - start_time < MAX_RUNTIME and
               no_improvement_count < no_improvement_limit):

            if iteration % 100 == 0:
                print(f"Iteration {iteration}, Temperature: {temperature:.3f}")
                print(f"Current metrics: {current_solution.metrics}")

            # Generate neighbor
            neighbor = self.get_neighbor(current_solution.assignments)
            if not neighbor:  # No valid neighbor found
                no_improvement_count += 1
                continue

            neighbor_solution = Solution(neighbor, self.tpms, self.programs)

            # Accept if neighbor dominates current
            if neighbor_solution.dominates(current_solution):
                current_solution = neighbor_solution
                if neighbor_solution.dominates(best_solution):
                    best_solution = neighbor_solution
                    no_improvement_count = 0
                    print(f"New best solution found: {best_solution.metrics}")
            else:
                # Accept with probability based on number of improved metrics
                improved_metrics = sum(1 for m, v in neighbor_solution.metrics.items()
                                    if v < current_solution.metrics[m])
                probability = math.exp(improved_metrics / temperature)
                if random.random() < probability:
                    current_solution = neighbor_solution

            temperature *= cooling_rate
            iteration += 1
            no_improvement_count += 1

        runtime = time() - start_time
        print(f"\nOptimization completed:")
        print(f"Runtime: {runtime:.1f} seconds")
        print(f"Iterations: {iteration}")
        print(f"Final metrics: {best_solution.metrics}")

        self.assignments = best_solution.assignments
        return self.assignments