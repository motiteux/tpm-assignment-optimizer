import pytest
from src.tpm_optimizer.models import Program

def test_program_creation():
    """Test Program creation with valid data"""
    program = Program(
        id="PROG001",
        name="Test Program",
        timezone="America/Los_Angeles",
        required_skills={"project-management"},
        required_time=0.5,
        required_level=3
    )
    assert program.id == "PROG001"
    assert program.required_time == 0.5
    assert program.fixed_tpm is None

def test_program_validation():
    """Test Program validation"""
    with pytest.raises(ValueError):
        Program(
            id="PROG001",
            name="Test Program",
            timezone="America/Los_Angeles",
            required_skills={"project-management"},
            required_time=1.5,  # Invalid
            required_level=3
        )

    with pytest.raises(ValueError):
        Program(
            id="PROG001",
            name="Test Program",
            timezone="America/Los_Angeles",
            required_skills={"project-management"},
            required_time=0.5,
            required_level=6  # Invalid
        )