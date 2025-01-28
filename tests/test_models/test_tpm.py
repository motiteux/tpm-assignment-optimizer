import pytest
from src.tpm_optimizer.models import TPM

def test_tpm_creation():
    """Test TPM creation with valid data"""
    tpm = TPM(
        id="TPM001",
        name="Test TPM",
        timezone="America/Los_Angeles",
        skills={"project-management", "agile"},
        available_time=0.8,
        level=3,
        conflicts=set()
    )
    assert tpm.id == "TPM001"
    assert tpm.available_time == 0.8
    assert not tpm.allow_overload

def test_tpm_validation():
    """Test TPM validation"""
    with pytest.raises(ValueError):
        TPM(
            id="TPM001",
            name="Test TPM",
            timezone="America/Los_Angeles",
            skills={"project-management"},
            available_time=1.5,  # Invalid
            level=3,
            conflicts=set()
        )

    with pytest.raises(ValueError):
        TPM(
            id="TPM001",
            name="Test TPM",
            timezone="America/Los_Angeles",
            skills={"project-management"},
            available_time=0.8,
            level=6,  # Invalid
            conflicts=set()
        )