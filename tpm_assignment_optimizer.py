import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Set, List
import pytz
from datetime import datetime
import random
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

class MILPOptimizer:
    def __init__(self, tpms: Dict[str, TPM], programs: Dict[str, Program]):
        self.tpms = tpms
        self.programs = programs
        self.assignments = {}

    def optimize(self):
        model = LpProblem("TPM_Assignment", LpMaximize)

        # Decision variables
        x = LpVariable.dicts("assign", 
                             ((i, j) for i in self.tpms for j in self.programs), 
                             cat='Binary')

        # Objective function
        model += lpSum(self.calculate_match_score(self.tpms[i], self.programs[j]) * x[i,j] 
                       for i in self.tpms for j in self.programs)

        # Constraints
        for j in self.programs:
            model += lpSum(x[i,j] for i in self.tpms) == 1  # Each program assigned once

        for i in self.tpms:
            model += lpSum(self.programs[j].required_time * x[i,j] for j in self.programs) <= self.tpms[i].available_time
            model += lpSum(x[i,j] for j in self.programs) <= (3 if self.tpms[i].level >= 3 else 2)

        for i in self.tpms:
            for j in self.programs:
                model += self.tpms[i].level * x[i,j] >= self.programs[j].required_level * x[i,j]

        portfolios = set(self.programs[j].portfolio for j in self.programs)
        for i in self.tpms:
            for p in portfolios:
                model += lpSum(x[i,j] for j in self.programs if self.programs[j].portfolio == p) <= 2

        for i in self.tpms:
            for j in self.tpms[i].conflicts:
                if j in self.programs:
                    model += x[i,j] == 0

        for j in self.programs:
            if self.programs[j].fixed_tpm:
                i = self.programs[j].fixed_tpm
                model += x[i,j] == 1

        # Solve the model
        model.solve()

        # Extract results
        for i in self.tpms:
            for j in self.programs:
                if x[i,j].value() == 1:
                    self.assignments[j] = i

        return self.assignments

    def calculate_match_score(self, tpm: TPM, program: Program) -> float:
        timezone_score = self._calculate_timezone_score(tpm.timezone, program)
        skill_score = len(tpm.skills.intersection(program.required_skills)) / len(program.required_skills)
        level_score = self._calculate_level_score(tpm.level, program.required_level)
        preference_score = 0.2 if program.id in tpm.desired_programs else 0.0
        
        return round(
            0.40 * timezone_score +
            0.25 * skill_score +
            0.20 * level_score +
            0.10 * preference_score,
            2
        )

    def _calculate_timezone_score(self, tpm_timezone: str, program: Program) -> float:
        program_timezones = [program.timezone] + list(program.stakeholder_timezones)
        time_diffs = [timezone_difference(tpm_timezone, tz) for tz in program_timezones]
        min_diff = min(time_diffs)
        
        if min_diff <= 2:
            return 1.0
        elif min_diff <= 4:
            return 0.5
        else:
            return 0.0

    def _calculate_level_score(self, tpm_level: int, required_level: int) -> float:
        if tpm_level == required_level:
            return 1.0
        elif tpm_level == required_level + 1:
            return 0.7
        elif tpm_level > required_level + 1:
            return 0.4
        else:
            return 0.0

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
        tpms[str(row['id'])] = TPM(
            id=str(row['id']),
            name=safe_get(row, 'name', ''),
            timezone=safe_get(row, 'timezone', 'UTC'),
            skills=split_if_string(safe_get(row, 'skills', '')),
            available_time=float(safe_get(row, 'available_time', 0)),
            level=int(safe_get(row, 'level', 1)),
            conflicts=split_if_string(safe_get(row, 'conflicts', '')),
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
            fixed_tpm=safe_get(row, 'fixed_tpm'),
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
                'Timezone': program.timezone,
                'TPM Name': tpm.name,
                'TPM Timezone': tpm.timezone,
                'Timezone Match': tz_diff <= 3.0,
                'Time Allocation': f"{round_float(program.required_time)}/{round_float(tpm.available_time + program.required_time)}"
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
        total_capacity = tpm.available_time + total_allocated
        portfolio_diversity[tpm_id] = len(set(optimizer.programs[p].portfolio for p in assigned_programs))
        utilization_data.append({
            'TPM ID': tpm_id,
            'TPM Name': tpm.name,
            'Total Capacity': round_float(total_capacity),
            'Used Capacity': round_float(total_allocated),
            'Remaining Capacity': round_float(tpm.available_time),
            'Utilization %': round_float((total_allocated / total_capacity) * 100) if total_capacity > 0 else 0,
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
    timezone_matches = assignments_df['Timezone Match'].value_counts(normalize=True) * 100
    print(f"Percentage of Exact Timezone Matches: {timezone_matches.get(True, 0):.2f}%")
    print(f"Percentage of Non-Exact Timezone Matches: {timezone_matches.get(False, 0):.2f}%")

    print("\nTop 5 Most Utilized TPMs:")
    top_utilized_tpms = utilization_df.nlargest(5, 'Utilization %')
    for _, row in top_utilized_tpms.iterrows():
        print(f"{row['TPM Name']}: {row['Utilization %']:.2f}% utilized")

    print("\nTop 5 Least Utilized TPMs:")
    least_utilized_tpms = utilization_df.nsmallest(5, 'Utilization %')
    for _, row in least_utilized_tpms.iterrows():
        print(f"{row['TPM Name']}: {row['Utilization %']:.2f}% utilized")

if __name__ == "__main__":
    main()