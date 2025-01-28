from typing import Dict, Optional
import sys
from ..models import TPM, Program
from ..utils import load_data, DataValidator
from ..optimizers import (
    MILPOptimizer,
    SimulatedAnnealingOptimizer,
    HybridOptimizer,
    TwoPhaseOptimizer
)
from ..reporting import generate_assignment_report, print_assignment_report


def run_optimization(
        method: str,
        tpms_file: str = 'tpms.csv',
        programs_file: str = 'programs.csv',
        verbose: bool = False
) -> Optional[Dict[str, str]]:
    """Run the optimization process"""
    try:
        # Load data
        if verbose:
            print("Loading data...")
        tpms, programs = load_data(tpms_file, programs_file)

        # Validate data
        if verbose:
            print("Validating data...")
        validator = DataValidator()
        for tpm in tpms.values():
            validator.validate_tpm(tpm)
        for program in programs.values():
            validator.validate_program(program)

        # Select optimizer
        optimizer_class = {
            'milp': MILPOptimizer,
            'sa': SimulatedAnnealingOptimizer,
            'hybrid': HybridOptimizer,
            'two-phase': TwoPhaseOptimizer
        }[method]

        optimizer = optimizer_class(tpms, programs)

        # Run optimization
        if verbose:
            print(f"\nRunning optimization using {method.upper()} method...")
        assignments = optimizer.optimize()

        if assignments is None:
            if verbose:
                print(f"No valid solution found using {method} method")
            return None

        # Generate reports
        assignments_df, unassigned_df, utilization_df, metrics = \
            generate_assignment_report(optimizer)
        print_assignment_report(
            assignments_df,
            unassigned_df,
            utilization_df,
            metrics,
            total_programs=len(programs),
            total_assignments=len(assignments)
        )

        return assignments

    except Exception as e:
        print(f"Error: {str(e)}")
        # Re-raise the exception if it's a test
        if 'pytest' in sys.modules:
            raise
        return None