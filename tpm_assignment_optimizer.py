import pandas as pd
from dataclasses import dataclass, field
from typing import Set
import pytz
from datetime import datetime
from pulp import *


@dataclass
class TPM:
    id: str
    name: str
    timezone: str
    skills: Set[str]
    available_time: float
    level: int
    conflicts: Set[str]
    allow_overload: bool = False
    fixed_program: str = None
    desired_programs: Set[str] = field(default_factory=set)
    assigned_programs: List[str] = field(default_factory=list)
    portfolios: Set[str] = field(default_factory=set)


@dataclass
class Program:
    id: str
    name: str
    timezone: str
    required_skills: Set[str]
    required_time: float
    required_level: int
    fixed_tpm: str = None
    stakeholder_timezones: Set[str] = field(default_factory=set)
    complexity_score: int = 1
    portfolio: str = ''
    assigned_tpm: str = None


def tz_to_utc_offset(tz_str):
    tz = pytz.timezone(tz_str)
    naive_dt = datetime.now().replace(tzinfo=None)
    offset = tz.utcoffset(naive_dt).total_seconds() / 3600
    return offset


def timezone_difference(tz1: str, tz2: str) -> float:
    offset1 = tz_to_utc_offset(tz1)
    offset2 = tz_to_utc_offset(tz2)
    return abs(offset1 - offset2)


def calculate_timezone_score(tpm_timezone: str, program: Program) -> float:
    program_timezones = [program.timezone] + list(program.stakeholder_timezones)
    time_diffs = [timezone_difference(tpm_timezone, tz) for tz in program_timezones]
    min_diff = min(time_diffs)

    if min_diff <= 2:
        return 1.0
    elif min_diff <= 4:
        return 0.5
    else:
        return 0.0


def calculate_level_score(tpm_level: int, required_level: int) -> float:
    if tpm_level == required_level:
        return 1.0
    elif tpm_level == required_level + 1:
        return 0.7
    elif tpm_level > required_level + 1:
        return 0.4
    else:
        return 0.0


class MILPOptimizer:
    def __init__(self, tpms: Dict[str, TPM], programs: Dict[str, Program]):
        self.tpms = tpms
        self.programs = programs
        self.assignments = {}
        self.fixed_assignment_overloads = {}

    def analyze_tpm_capacities(self):
        print("\nAnalyzing TPM capacities:")
        for tpm_id, tpm in self.tpms.items():
            fixed_load = sum(
                program.required_time
                for program in self.programs.values()
                if program.fixed_tpm == tpm_id
            )
            print(f"TPM {tpm_id} ({tpm.name}):")
            print(f"  Base capacity: {tpm.available_time:.2f}")
            print(f"  Fixed assignments load: {fixed_load:.2f}")
            print(f"  Total after fixed: {(tpm.available_time + fixed_load):.2f}")

    def analyze_fixed_assignments(self) -> Tuple[bool, List[str]]:
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

                if tpm.level < program.required_level:
                    issues.append(
                        f"Program {prog_id}: Fixed TPM {program.fixed_tpm} level ({tpm.level}) "
                        f"< required level ({program.required_level})"
                    )

                if prog_id in tpm.conflicts:
                    issues.append(
                        f"Program {prog_id}: Fixed to TPM {program.fixed_tpm} but listed in TPM's conflicts"
                    )

        # Record overloaded TPMs, but only as issues if overload is not allowed
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

    def analyze_utilization(self):
        print("\nAnalyzing TPM utilization:")
        for tpm_id, tpm in self.tpms.items():
            current_load = sum(
                self.programs[p].required_time
                for p in self.assignments
                if self.assignments[p] == tpm_id
            )
            utilization = current_load / tpm.available_time if tpm.available_time > 0 else 0
            print(f"TPM {tpm_id} ({tpm.name}):")
            print(f"  Current utilization: {utilization:.2%}")
            if utilization < 0.4:
                print(f"  WARNING: Under-utilized TPM")

    def optimize(self):
        """Run the MILP optimization with detailed feasibility checking"""
        print("\nPerforming pre-optimization analysis...")

        self.analyze_tpm_capacities()

        # Get unused TPMs
        unused_tpms = [tpm_id for tpm_id, tpm in self.tpms.items()
                       if not any(self.assignments.get(p) == tpm_id for p in self.programs)]
        print(f"\nUnused TPMs: {len(unused_tpms)}")
        for tpm_id in unused_tpms:
            print(f"  {tpm_id} ({self.tpms[tpm_id].name})")

        # First, process fixed assignments
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

        print(f"\nOptimizing {len(remaining_programs)} remaining programs...")
        if not remaining_programs:
            print("No remaining programs to optimize")
            return self.assignments

        # Sort remaining programs by size
        sorted_program_ids = sorted(
            remaining_programs.keys(),
            key=lambda p: remaining_programs[p].required_time,
            reverse=True  # Largest programs first
        )

        model = LpProblem("TPM_Assignment", LpMaximize)

        # Decision variables
        x = LpVariable.dicts("assign",
                             ((i, j) for i in self.tpms for j in sorted_program_ids),
                             cat='Binary')

        # Objective function with strong preference for unused TPMs
        objective = (
                lpSum(self._calculate_match_score(self.tpms[i], remaining_programs[j]) * x[i, j]
                      for i in self.tpms for j in sorted_program_ids) +
                # Heavy bonus for using unused TPMs
                lpSum(2.0 * x[i, j] for i in unused_tpms for j in sorted_program_ids)
        )
        model += objective

        # Constraints
        print("\nAdding constraints...")

        # 1. Each program must be assigned to exactly one TPM
        for j in sorted_program_ids:
            model += lpSum(x[i, j] for i in self.tpms) == 1, f"One_TPM_Per_Program_{j}"

        # 2. Capacity constraints with minimum assignments for unused TPMs
        for i in self.tpms:
            current_load = sum(
                self.programs[p].required_time
                for p in self.assignments
                if self.assignments[p] == i
            )

            if not self.tpms[i].allow_overload:
                remaining_capacity = self.tpms[i].available_time - current_load
                model += lpSum(remaining_programs[j].required_time * x[i, j]
                               for j in sorted_program_ids) <= remaining_capacity, f"Capacity_{i}"

            # Force minimum assignments for unused TPMs
            if i in unused_tpms:
                model += lpSum(x[i, j] for j in sorted_program_ids) >= 1, f"Min_Assignment_{i}"
                # Try to assign at least 40% capacity to unused TPMs
                model += lpSum(remaining_programs[j].required_time * x[i, j]
                               for j in sorted_program_ids) >= 0.4 * self.tpms[i].available_time, f"Min_Load_{i}"

        # 3. Level requirements
        for i in self.tpms:
            for j in sorted_program_ids:
                if self.tpms[i].level < remaining_programs[j].required_level:
                    model += x[i, j] == 0, f"Level_{i}_{j}"

        # 4. Conflicts
        for i in self.tpms:
            for j in self.tpms[i].conflicts:
                if j in sorted_program_ids:
                    model += x[i, j] == 0, f"Conflict_{i}_{j}"

        # 5. Portfolio diversity
        portfolios = set(remaining_programs[j].portfolio for j in sorted_program_ids)
        for i in self.tpms:
            existing_portfolios = set(
                self.programs[p].portfolio
                for p in self.assignments
                if self.assignments[p] == i
            )
            # Allow more portfolios for unused TPMs
            max_portfolios = 3 if i in unused_tpms else 2
            for p in portfolios:
                if len(existing_portfolios) < max_portfolios or p in existing_portfolios:
                    model += lpSum(x[i, j] for j in sorted_program_ids
                                   if remaining_programs[j].portfolio == p) <= max_portfolios

        # Solve
        print("\nSolving optimization model...")
        status = model.solve()
        print(f"Optimization status: {LpStatus[status]}")

        if status != LpStatusOptimal:
            print("\nAnalyzing infeasibility...")
            for j in sorted_program_ids:
                prog = remaining_programs[j]
                eligible_tpms = [
                    i for i in self.tpms
                    if (self.tpms[i].level >= prog.required_level and
                        j not in self.tpms[i].conflicts)
                ]
                if not eligible_tpms:
                    print(f"Program {j} has no eligible TPMs due to level/conflict constraints")
                else:
                    available_tpms = [
                        i for i in eligible_tpms
                        if self.tpms[i].available_time >= prog.required_time or self.tpms[i].allow_overload
                    ]
                    if not available_tpms:
                        print(f"Program {j} has no TPMs with sufficient capacity")
            return self.assignments

        # Extract results
        print("\nExtracting results...")
        for i in self.tpms:
            for j in sorted_program_ids:
                if value(x[i, j]) > 0.5:
                    self.assignments[j] = i
                    print(f"Assigned Program {j} to TPM {i}")

        return self.assignments

    def _calculate_match_score(self, tpm: TPM, program: Program) -> float:
        # Calculate current utilization for this TPM
        current_load = sum(
            self.programs[p].required_time
            for p in self.assignments
            if self.assignments[p] == tpm.id
        )
        utilization = current_load / tpm.available_time if tpm.available_time > 0 else 1.0

        # If TPM would be overloaded and doesn't allow it, return -1
        if not tpm.allow_overload and (current_load + program.required_time > tpm.available_time):
            return -1

        # Calculate base scores
        timezone_score = calculate_timezone_score(tpm.timezone, program)
        skill_score = len(tpm.skills.intersection(program.required_skills)) / len(program.required_skills)
        level_score = calculate_level_score(tpm.level, program.required_level)
        preference_score = 0.2 if program.id in tpm.desired_programs else 0.0

        # Strong incentive for unused and under-utilized TPMs
        utilization_bonus = 0
        if utilization == 0:  # Completely unused TPM
            utilization_bonus = 0.5  # Very high bonus for unused TPMs
        elif utilization < 0.4:  # Under 40% utilization
            utilization_bonus = 0.3  # Significant bonus for under-utilized TPMs

        # Increased weight for utilization factor
        utilization_factor = 1 - (utilization * 0.7)  # Stronger penalty for high utilization

        base_score = (
                             0.30 * timezone_score +
                             0.20 * skill_score +
                             0.15 * level_score +
                             0.10 * preference_score +
                             0.25 * utilization_factor  # Increased weight for utilization
                     ) + utilization_bonus

        # Timezone penalty for large differences
        tz_diff = timezone_difference(tpm.timezone, program.timezone)
        if tz_diff > 6:
            base_score *= 0.5  # Significant penalty for large timezone differences

        return round(base_score, 2)


class DataValidator:
    @staticmethod
    def validate_tpm(tpm: TPM):
        assert isinstance(tpm.id, str), "TPM ID must be a string"
        assert 0 <= tpm.available_time <= 1, "Available time must be between 0 and 1"
        assert 1 <= tpm.level <= 5, "TPM level must be between 1 and 5"
        assert isinstance(tpm.timezone, str), "Timezone must be a string"

    @staticmethod
    def validate_program(program: Program):
        assert isinstance(program.id, str), "Program ID must be a string"
        assert 0 < program.required_time <= 1, "Required time must be between 0 and 1"
        assert 1 <= program.required_level <= 5, "Required level must be between 1 and 5"
        assert isinstance(program.timezone, str), "Timezone must be a string"
        assert 1 <= program.complexity_score <= 5, "Complexity score must be between 1 and 5"

    @staticmethod
    def validate_tpm(tpm: TPM):
        assert isinstance(tpm.id, str), "TPM ID must be a string"
        assert 0 <= tpm.available_time <= 1, "Available time must be between 0 and 1"
        assert 1 <= tpm.level <= 5, "TPM level must be between 1 and 5"
        assert isinstance(tpm.timezone, str), "Timezone must be a string"
        # Add debug output for suspicious capacity
        if tpm.available_time > 1:
            print(f"Warning: TPM {tpm.id} ({tpm.name}) has capacity > 1: {tpm.available_time}")


def load_data(tpms_file: str, programs_file: str) -> tuple:
    tpms_df = pd.read_csv(tpms_file)
    programs_df = pd.read_csv(programs_file)

    def split_if_string(value):
        return set(value.split(',')) if isinstance(value, str) else set()

    def safe_get(row, key, default=None):
        value = row[key] if key in row and pd.notna(row[key]) else default
        return value if value != '' else default

    tpms = {}
    for _, row in tpms_df.iterrows():
        # Get allow_overload value, treating null/empty as False
        allow_overload_value = str(safe_get(row, 'allow_overload', '')).lower()
        allow_overload = allow_overload_value in ['true', '1', 'yes', 't', 'y']

        tpms[str(row['id'])] = TPM(
            id=str(row['id']),
            name=safe_get(row, 'name', ''),
            timezone=safe_get(row, 'timezone', 'UTC'),
            skills=split_if_string(safe_get(row, 'skills', '')),
            available_time=float(safe_get(row, 'available_time', 0)),
            level=int(safe_get(row, 'level', 1)),
            conflicts=split_if_string(safe_get(row, 'conflicts', '')),
            allow_overload=allow_overload,
            fixed_program=safe_get(row, 'fixed_program'),
            desired_programs=split_if_string(safe_get(row, 'desired_programs', ''))
        )

    programs = {}
    for _, row in programs_df.iterrows():
        programs[str(row['id'])] = Program(
            id=str(row['id']),
            name=safe_get(row, 'name', ''),
            timezone=safe_get(row, 'timezone', 'UTC'),
            required_skills=split_if_string(safe_get(row, 'required_skills', '')),
            required_time=float(safe_get(row, 'required_time', 0)),
            required_level=int(safe_get(row, 'required_level', 1)),
            fixed_tpm=str(safe_get(row, 'fixed_tpm')) if pd.notna(row.get('fixed_tpm')) else None,
            stakeholder_timezones=split_if_string(safe_get(row, 'stakeholder_timezones', '')),
            complexity_score=int(safe_get(row, 'complexity_score', 1)),
            portfolio=safe_get(row, 'portfolio', '')
        )

    return tpms, programs

def generate_assignment_report(optimizer: MILPOptimizer) -> tuple:
    """Generate detailed tabular reports of assignments and TPM utilization"""
    assignment_data = []
    unassigned_data = []
    utilization_data = []
    total_programs = len(optimizer.programs)
    assigned_programs_count = len(optimizer.assignments)
    total_timezone_spread = 0
    respected_timezones = 0

    def round_float(value, decimals=2):
        return round(float(value), decimals)

    # Process assignments
    for prog_id, program in optimizer.programs.items():
        tpm_id = optimizer.assignments.get(prog_id)
        if tpm_id:
            tpm = optimizer.tpms[tpm_id]
            tz_diff = timezone_difference(tpm.timezone, program.timezone)
            total_timezone_spread += tz_diff
            if tz_diff <= 3:
                respected_timezones += 1
            assignment_data.append({
                'Program ID': prog_id,
                'Program Name': program.name,
                'Required Time': round_float(program.required_time),
                'Program Timezone': program.timezone,
                'TPM Name': tpm.name,
                'TPM Timezone': tpm.timezone,
                'Timezone Match': 'Yes' if tz_diff <= 3.0 else 'No',  # Changed to string format
                # 'Time Allocation': f"{round_float(program.required_time)}/{round_float(tpm.available_time + program.required_time)}"
            })
        else:
            unassigned_data.append({
                'Program ID': prog_id,
                'Program Name': program.name,
                'Required Time': round_float(program.required_time),
                'Timezone': program.timezone
            })

    portfolio_diversity = {}
    for tpm_id, tpm in optimizer.tpms.items():
        assigned_programs = [p for p in optimizer.assignments if optimizer.assignments[p] == tpm_id]
        total_allocated = sum(optimizer.programs[p].required_time for p in assigned_programs)
        portfolio_diversity[tpm_id] = len(set(optimizer.programs[p].portfolio for p in assigned_programs))

        # Fixed capacity calculation
        total_capacity = tpm.available_time  # Should be ≤ 1.0
        used_capacity = total_allocated
        remaining_capacity = max(0, total_capacity - used_capacity)
        utilization_percentage = (used_capacity / total_capacity * 100) if total_capacity > 0 else 0

        utilization_data.append({
            'TPM ID': tpm_id,
            'TPM Name': tpm.name,
            'Total Capacity': round(total_capacity, 2),
            'Used Capacity': round(used_capacity, 2),
            'Remaining Capacity': round(remaining_capacity, 2),
            'Utilization %': round(utilization_percentage, 2),
            'Program Count': len(assigned_programs),
            'Timezone': tpm.timezone,
            'Portfolio Diversity': portfolio_diversity[tpm_id]
        })

    assignments_df = pd.DataFrame(assignment_data)
    if not assignments_df.empty:
        assignments_df = assignments_df.sort_values(['TPM Name', 'Program ID'])

    unassigned_df = pd.DataFrame(unassigned_data)
    if not unassigned_df.empty:
        unassigned_df = unassigned_df.sort_values('Program ID')
    else:
        unassigned_df = pd.DataFrame(columns=['Program ID', 'Program Name', 'Required Time', 'Timezone'])

    utilization_df = pd.DataFrame(utilization_data)
    if not utilization_df.empty:
        utilization_df = utilization_df.sort_values('TPM Name')

    # Calculate overall metrics
    assignment_coverage = assigned_programs_count / total_programs if total_programs > 0 else 0
    avg_timezone_spread = total_timezone_spread / assigned_programs_count if assigned_programs_count > 0 else 0
    avg_portfolio_diversity = sum(portfolio_diversity.values()) / len(portfolio_diversity) if portfolio_diversity else 0
    avg_tpm_utilization = utilization_df['Utilization %'].mean() if not utilization_df.empty else 0
    timezone_respect_percentage = (respected_timezones / assigned_programs_count) * 100 if assigned_programs_count > 0 else 0

    return assignments_df, unassigned_df, utilization_df, {
        'Assignment Coverage': round_float(assignment_coverage * 100),
        'Average Timezone Spread': round_float(avg_timezone_spread),
        'Average Portfolio Diversity': round_float(avg_portfolio_diversity),
        'Average TPM Utilization': round_float(avg_tpm_utilization),
        'Timezone Respect Percentage': round_float(timezone_respect_percentage)
    }


def main():
    tpms, programs = load_data('tpms.csv', 'programs.csv')

    validator = DataValidator()
    for tpm in tpms.values():
        validator.validate_tpm(tpm)
    for program in programs.values():
        validator.validate_program(program)

    optimizer = MILPOptimizer(tpms, programs)
    assignments = optimizer.optimize()

    assignments_df, unassigned_df, utilization_df, metrics = generate_assignment_report(optimizer)

    print("\n=== TPM Assignments ===")
    if not assignments_df.empty:
        print(assignments_df.to_string(index=False))
    else:
        print("No assignments made.")

    print("\n=== Unassigned Programs ===")
    if not unassigned_df.empty:
        print(unassigned_df.to_string(index=False))
    else:
        print("No unassigned programs!")

    print("\n=== TPM Utilization ===")
    if not utilization_df.empty:
        print(utilization_df.to_string(index=False))
    else:
        print("No TPM utilization data available.")

    # Print summary and metrics
    print(f"\nSummary:")
    print(f"Total programs: {len(programs)}")
    print(f"Total programs assigned: {len(assignments)}")
    print(f"Total programs unassigned: {len(programs) - len(assignments)}")
    print(f"Assignment Coverage: {metrics['Assignment Coverage']:.2f}%")
    print(f"Average Timezone Spread: {metrics['Average Timezone Spread']:.2f} hours")
    print(f"Average Portfolio Diversity: {metrics['Average Portfolio Diversity']:.2f}")
    print(f"Average TPM Utilization: {metrics['Average TPM Utilization']:.2f}%")
    print(f"Timezone Respect Percentage: {metrics['Timezone Respect Percentage']:.2f}%")

    print("\nTimezone Match Breakdown:")
    if not assignments_df.empty:
        timezone_matches = assignments_df['Timezone Match'].value_counts()
        total_assignments = len(assignments_df)
        print(f"Exact Timezone Matches: {timezone_matches.get('Yes', 0)} ({(timezone_matches.get('Yes', 0) / total_assignments * 100):.2f}%)")
        print(f"Non-Exact Timezone Matches: {timezone_matches.get('No', 0)} ({(timezone_matches.get('No', 0) / total_assignments * 100):.2f}%)")
    else:
        print("No assignments to analyze")

    print("\nTop 5 Most Utilized TPMs:")
    if not utilization_df.empty:
        top_utilized_tpms = utilization_df.nlargest(5, 'Utilization %')
        for _, row in top_utilized_tpms.iterrows():
            print(f"{row['TPM Name']}: {row['Utilization %']:.2f}% utilized")
    else:
        print("No utilization data available")

    print("\nTop 5 Least Utilized TPMs:")
    if not utilization_df.empty:
        least_utilized_tpms = utilization_df.nsmallest(5, 'Utilization %')
        for _, row in least_utilized_tpms.iterrows():
            print(f"{row['TPM Name']}: {row['Utilization %']:.2f}% utilized")
    else:
        print("No utilization data available")

if __name__ == "__main__":
    main()