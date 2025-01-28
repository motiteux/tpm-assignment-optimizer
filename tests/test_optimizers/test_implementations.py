import pytest
from src.tpm_optimizer.optimizers import (
    MILPOptimizer,
    SimulatedAnnealingOptimizer,
    HybridOptimizer,
    TwoPhaseOptimizer
)


def test_milp_optimizer(sample_tpms, sample_programs):
    """Test MILP optimizer"""
    optimizer = MILPOptimizer(sample_tpms, sample_programs)
    solution = optimizer.optimize()

    assert isinstance(solution, dict)
    if solution:
        assert all(prog_id in sample_programs for prog_id in solution.keys())
        assert all(tpm_id in sample_tpms for tpm_id in solution.values())


def test_simulated_annealing_optimizer(sample_tpms, sample_programs):
    """Test Simulated Annealing optimizer"""
    optimizer = SimulatedAnnealingOptimizer(sample_tpms, sample_programs)
    solution = optimizer.optimize()

    assert isinstance(solution, dict)
    if solution:
        assert all(prog_id in sample_programs for prog_id in solution.keys())
        assert all(tpm_id in sample_tpms for tpm_id in solution.values())


def test_hybrid_optimizer(sample_tpms, sample_programs):
    """Test Hybrid optimizer"""
    optimizer = HybridOptimizer(sample_tpms, sample_programs)
    solution = optimizer.optimize()

    assert isinstance(solution, dict)
    if solution:
        assert all(prog_id in sample_programs for prog_id in solution.keys())
        assert all(tpm_id in sample_tpms for tpm_id in solution.values())


def test_two_phase_optimizer(sample_tpms, sample_programs):
    """Test Two Phase optimizer"""
    optimizer = TwoPhaseOptimizer(sample_tpms, sample_programs)
    solution = optimizer.optimize()

    assert isinstance(solution, dict)
    if solution:
        assert all(prog_id in sample_programs for prog_id in solution.keys())
        assert all(tpm_id in sample_tpms for tpm_id in solution.values())