from typing import Dict, List, Tuple
from pulp import *
import math
from .base import BaseOptimizer
from ..models import TPM, Program
from .solution import Solution

class MILPOptimizer(BaseOptimizer):
    def __init__(self, tpms: Dict[str, TPM], programs: Dict[str, Program]):
        super().__init__(tpms, programs)
        self.fixed_assignment_overloads = {}

    def analyze_tpm_capacities(self):
        """Analyze TPM capacities and fixed assignments"""
        print("\nAnalyzing TPM capacities:")
        for tpm_id, tpm in self.tpms.items():
            fixed_load = sum(
                program.required_time
                for program in self.programs.values()
                if program.fixed_tpm == tpm_id
            )
            print(f"TPM {tpm_id} ({tpm.name}): ")
            print(f"  Base capacity: {tpm.available_time: .2f}")
            print(f"  Fixed assignments load: {fixed_load: .2f}")
            print(f"  Total after fixed: {(tpm.available_time + fixed_load): .2f}")

    def analyze_fixed_assignments(self) -> Tuple[bool, List[str]]:
        """Analyze and validate fixed assignments"""
        print("\nTPM Overload Settings:")
        for tpm_id, tpm in self.tpms.items():
            print(f"TPM {tpm_id} ({tpm.name}): allow_overload = {tpm.allow_overload}")

        print("\nAnalyzing fixed assignments:")
        issues = []
        tpm_loads = {tpm_id: 0.0 for tpm_id in self.tpms}

        for prog_id, program in self.programs.items():
            if program.fixed_tpm:
                if program.fixed_tpm not in self.tpms:
                    issues.append(f"Program {prog_id}: Fixed TPM {program.fixed_tpm} does not exist")
                    continue

                tpm = self.tpms[program.fixed_tpm]
                tpm_loads[program.fixed_tpm] += program.required_time

                print(f"\nProgram {prog_id}:")
                print(f"  Required time: {program.required_time}")
                print(f"  Fixed TPM {program.fixed_tpm} ({tpm.name}):")
                print(f"    Available time: {tpm.available_time}")
                print(f"    Current load: {tpm_loads[program.fixed_tpm]}")
                print(f"    Required level: {program.required_level}")
                print(f"    TPM level: {tpm.level}")
                print(f"    Allow overload: {tpm.allow_overload}")

                if not self.validate_assignment(prog_id, program.fixed_tpm):
                    issues.append(f"Program {prog_id}: Invalid fixed assignment to TPM {program.fixed_tpm}")

        # Record overloaded TPMs
        for tpm_id, load in tpm_loads.items():
            if load > self.tpms[tpm_id].available_time:
                self.fixed_assignment_overloads[tpm_id] = load
                if not self.tpms[tpm_id].allow_overload:
                    issues.append(
                        f"TPM {tpm_id} ({self.tpms[tpm_id].name}) is overloaded: "
                        f"Fixed assignments require {load:.2f} FTE, but capacity is {self.tpms[tpm_id].available_time:.2f} FTE "
                        f"and overload is not allowed"
                    )
                else:
                    print(f"Note: TPM {tpm_id} ({self.tpms[tpm_id].name}) will be overloaded: "
                          f"{load:.2f} FTE > {self.tpms[tpm_id].available_time:.2f} FTE "
                          f"but overload is allowed")

        return len(issues) == 0, issues

    def analyze_level_requirements(self) -> Tuple[bool, List[str]]:
        """Analyze level requirements by bandwidth"""
        print("\nAnalyzing level requirements by bandwidth:")
        issues = []

        for level in range(1, 6):
            program_time_at_level = sum(p.required_time for p in self.programs.values()
                                        if p.required_level == level)
            tpm_capacity_at_or_above = sum(t.available_time for t in self.tpms.values()
                                           if t.level >= level)
            fixed_assignments_at_level = sum(
                p.required_time for p in self.programs.values()
                if p.required_level == level and p.fixed_tpm is not None
            )

            remaining_program_time = program_time_at_level - fixed_assignments_at_level
            remaining_tpm_capacity = tpm_capacity_at_or_above - fixed_assignments_at_level

            print(f"\nLevel {level}:")
            print(f"  Total program time requiring this level: {program_time_at_level:.2f}")
            print(f"  Fixed assignments at this level: {fixed_assignments_at_level:.2f}")
            print(f"  Remaining program time to assign: {remaining_program_time:.2f}")
            print(f"  TPM capacity at or above this level: {tpm_capacity_at_or_above:.2f}")
            print(f"  Remaining TPM capacity: {remaining_tpm_capacity:.2f}")

            if remaining_program_time > remaining_tpm_capacity:
                issues.append(
                    f"Insufficient capacity at level {level}: "
                    f"Required={remaining_program_time:.2f}, "
                    f"Available={remaining_tpm_capacity:.2f}"
                )

        return len(issues) == 0, issues

    def optimize(self) -> Dict[str, str]:
        """Run the MILP optimization with detailed feasibility checking"""
        print("\nPerforming pre-optimization analysis...")

        self.analyze_tpm_capacities()

        # Process fixed assignments first
        fixed_assignments = {
            prog_id: program.fixed_tpm
            for prog_id, program in self.programs.items()
            if program.fixed_tpm
        }

        print(f"\nProcessing {len(fixed_assignments)} fixed assignments...")
        for prog_id, tpm_id in fixed_assignments.items():
            if tpm_id in self.tpms:
                self.assignments[prog_id] = tpm_id
                print(f"Pre-assigned Program {prog_id} to TPM {tpm_id}")

        # Get remaining programs
        remaining_programs = {
            prog_id: program
            for prog_id, program in self.programs.items()
            if prog_id not in self.assignments
        }

        # Create MILP model
        model = LpProblem("TPM_Assignment", LpMaximize)

        # Decision variables
        x = LpVariable.dicts("assign",
                             ((i, j) for i in self.tpms for j in remaining_programs),
                             cat='Binary')

        # Modified objective function handling
        objective_terms = []
        for i in self.tpms:
            for j in remaining_programs:
                score = self.calculate_assignment_score(j, i)
                if score != -float('inf'):
                    objective_terms.append(score * x[i, j])
                else:
                    # If assignment is invalid, force variable to 0
                    model += x[i, j] == 0

        model += lpSum(objective_terms)

        # Constraints
        for j in remaining_programs:
            model += lpSum(x[i, j] for i in self.tpms) == 1

        for i in self.tpms:
            current_load = sum(self.programs[p].required_time
                             for p in self.assignments if self.assignments[p] == i)
            if not self.tpms[i].allow_overload:
                model += (lpSum(remaining_programs[j].required_time * x[i, j]
                             for j in remaining_programs) <=
                        self.tpms[i].available_time - current_load)

        # Add validation constraints
        for i in self.tpms:
            for j in remaining_programs:
                if not self.validate_assignment(j, i):
                    model += x[i, j] == 0

        # Solve
        status = model.solve()

        if status == 1:  # Optimal solution found
            for i in self.tpms:
                for j in remaining_programs:
                    if value(x[i, j]) > 0.5:
                        self.assignments[j] = i

        return self.assignments