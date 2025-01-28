import pytest
from src.tpm_optimizer.cli.commands import run_optimization


def test_run_optimization(test_csv_files):
    """Test running optimization with different methods"""
    methods = ['milp', 'sa', 'hybrid', 'two-phase']

    for method in methods:
        try:
            assignments = run_optimization(
                method=method,
                tpms_file=test_csv_files['tpms'],
                programs_file=test_csv_files['programs'],
                verbose=True
            )

            # Check if assignments is not None (some methods might not find a solution)
            if assignments is not None:
                assert isinstance(assignments, dict)
                # Additional checks for valid assignments
                assert all(isinstance(k, str) and isinstance(v, str)
                           for k, v in assignments.items())
            else:
                print(f"Note: {method} optimizer returned None (no solution found)")

        except Exception as e:
            pytest.fail(f"Method {method} failed with error: {str(e)}")