import pytest
from src.tpm_optimizer.utils import DataValidator


def test_data_validator(sample_tpms, sample_programs):
    """Test data validation"""
    validator = DataValidator()

    # Test TPM validation
    for tpm in sample_tpms.values():
        validator.validate_tpm(tpm)

    # Test Program validation
    for program in sample_programs.values():
        validator.validate_program(program)