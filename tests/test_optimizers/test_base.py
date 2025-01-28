import pytest
from src.tpm_optimizer.optimizers import BaseOptimizer


def test_base_optimizer(sample_tpms, sample_programs):
    """Test BaseOptimizer functionality"""
    optimizer = BaseOptimizer(sample_tpms, sample_programs)

    # Test assignment validation
    assert optimizer.validate_assignment("PROG001", "TPM001")

    # Test fixed assignment validation
    solution = {"PROG001": "TPM001"}
    assert optimizer.validate_fixed_assignments_solution(solution)