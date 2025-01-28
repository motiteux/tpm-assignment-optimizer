import pandas as pd
from typing import Dict


def print_assignment_report(
        assignments_df: pd.DataFrame,
        unassigned_df: pd.DataFrame,
        utilization_df: pd.DataFrame,
        metrics: Dict[str, float],
        total_programs: int,
        total_assignments: int
) -> None:
    """Print formatted assignment report to console"""

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

    print(f"\nSummary:")
    print(f"Total programs: {total_programs}")
    print(f"Total programs assigned: {total_assignments}")
    print(f"Total programs unassigned: {total_programs - total_assignments}")
    print(f"Assignment Coverage: {metrics['Assignment Coverage']:.1f}%")
    print(f"Average Timezone Spread: {metrics['Average Timezone Spread']:.1f} hours")
    print(f"Average Portfolio Diversity: {metrics['Average Portfolio Diversity']:.1f}")
    print(f"Average TPM Utilization: {metrics['Average TPM Utilization']:.1f}%")
    print(f"Timezone Respect Percentage: {metrics['Timezone Respect Percentage']:.1f}%")