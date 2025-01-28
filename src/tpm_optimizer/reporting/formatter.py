import pandas as pd
from typing import Dict, Tuple, Set
from ..models import TPM, Program
from ..optimizers import BaseOptimizer
from ..utils.timezone import timezone_difference
from .metrics import calculate_summary_metrics


def shorten_name(name: str, max_length: int = 30) -> str:
    """Shorten a name intelligently while keeping it recognizable"""
    if len(name) <= max_length:
        return name

    # Common abbreviations
    abbreviations = {
        'Machine Learning': 'ML',
        'Lifecycle': 'LC',
        'Authentication': 'Auth',
        'Authorization': 'Auth',
        'Private Label Solutions': 'PLS',
        'Technical Program Manager': 'TPM',
        'Recommendations': 'Recs',
        'Management': 'Mgmt',
        'Platform': 'Plat',
        'Generation': 'Gen',
        'Intelligence': 'Intel',
        'Integration': 'Int',
        'Development': 'Dev'
    }

    # Apply abbreviations
    shortened = name
    for full, abbr in abbreviations.items():
        shortened = shortened.replace(full, abbr)

    # If still too long, truncate with ellipsis
    if len(shortened) > max_length:
        shortened = shortened[:max_length - 3] + "..."

    return shortened


def generate_assignment_report(
        optimizer: BaseOptimizer
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, float]]:
    """Generate detailed tabular reports of assignments and TPM utilization"""
    assignment_data = []
    unassigned_data = []
    utilization_data = []

    total_programs = len(optimizer.programs)
    assigned_programs_count = len(optimizer.assignments)
    total_timezone_spread = 0
    respected_timezones = 0

    # Process assignments
    for prog_id, program in optimizer.programs.items():
        tpm_id = optimizer.assignments.get(prog_id)
        if tpm_id:
            tpm = optimizer.tpms[tpm_id]
            tz_diff = timezone_difference(tpm.timezone, program.timezone)
            total_timezone_spread += tz_diff
            if tz_diff <= 3:
                respected_timezones += 1

            is_fixed = prog_id in optimizer.fixed_assignments
            assignment_data.append({
                'Program ID': prog_id,
                'Program Name': shorten_name(program.name),
                'Required Time': f"{program.required_time:.1f}",
                'TPM Name': tpm.name,
                'Fixed': 'Yes' if is_fixed else 'No',
                'Timezone Match': 'Yes' if tz_diff <= 3.0 else 'No',
                'Time Allocation': f"{program.required_time:.1f}/{tpm.available_time:.1f}"
            })
        else:
            unassigned_data.append({
                'Program ID': prog_id,
                'Program Name': shorten_name(program.name),
                'Required Time': f"{program.required_time:.1f}",
                'Timezone': program.timezone
            })

    # Calculate TPM utilization
    portfolio_diversity = {}
    for tpm_id, tpm in optimizer.tpms.items():
        assigned_programs = [p for p in optimizer.assignments if optimizer.assignments[p] == tpm_id]
        total_allocated = sum(optimizer.programs[p].required_time for p in assigned_programs)
        portfolio_diversity[tpm_id] = len(set(optimizer.programs[p].portfolio for p in assigned_programs))

        utilization_data.append({
            'TPM ID': tpm_id,
            'TPM Name': tpm.name,
            'Total Capacity': round(tpm.available_time, 1),
            'Used Capacity': round(total_allocated, 1),
            'Remaining Capacity': round(max(0, tpm.available_time - total_allocated), 1),
            'Utilization %': round((total_allocated / tpm.available_time * 100) if tpm.available_time > 0 else 0, 1),
            'Program Count': len(assigned_programs),
            'Timezone': tpm.timezone,
            'Portfolio Diversity': portfolio_diversity[tpm_id]
        })

    # Create DataFrames
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

    # Calculate metrics
    metrics = calculate_summary_metrics(
        total_programs=total_programs,
        assigned_count=assigned_programs_count,
        total_timezone_spread=total_timezone_spread,
        respected_timezones=respected_timezones,
        portfolio_diversity=portfolio_diversity,
        utilization_df=utilization_df
    )

    return assignments_df, unassigned_df, utilization_df, metrics