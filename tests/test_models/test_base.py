import pytest
from src.tpm_optimizer.models import TPM, Program

def test_tpm_creation(sample_tpms):
    tpm = sample_tpms['TPM001']
    assert isinstance(tpm, TPM)
    assert tpm.id == "TPM001"
    assert tpm.name == "Test Lead"
    assert tpm.skills == {"project-management", "agile", "mlops"}

def test_program_creation(sample_programs):
    program = sample_programs['PROG001']
    assert isinstance(program, Program)
    assert program.id == "PROG001"
    assert program.name == "ML Pipeline"
    assert program.required_skills == {"project-management", "mlops"}