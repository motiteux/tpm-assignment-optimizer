from typing import Dict, Set
import pandas as pd


def calculate_summary_metrics(
        total_programs: int,
        assigned_count: int,
        total_timezone_spread: float,
        respected_timezones: int,
        portfolio_diversity: Dict[str, int],
        utilization_df: pd.DataFrame
) -> Dict[str, float]:
    """Calculate summary metrics for the assignment solution"""

    assignment_coverage = assigned_count / total_programs if total_programs > 0 else 0
    avg_timezone_spread = total_timezone_spread / assigned_count if assigned_count > 0 else 0
    avg_portfolio_diversity = (sum(portfolio_diversity.values()) /
                               len(portfolio_diversity) if portfolio_diversity else 0)
    avg_tpm_utilization = utilization_df['Utilization %'].mean() if not utilization_df.empty else 0
    timezone_respect_percentage = (respected_timezones / assigned_count * 100
                                   if assigned_count > 0 else 0)

    return {
        'Assignment Coverage': round(assignment_coverage * 100, 1),
        'Average Timezone Spread': round(avg_timezone_spread, 1),
        'Average Portfolio Diversity': round(avg_portfolio_diversity, 1),
        'Average TPM Utilization': round(avg_tpm_utilization, 1),
        'Timezone Respect Percentage': round(timezone_respect_percentage, 1)
    }