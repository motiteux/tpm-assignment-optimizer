import pytest
from src.tpm_optimizer.utils import (
    timezone_difference,
    calculate_timezone_score,
    DataValidator
)
from src.tpm_optimizer.models import TPM, Program


def test_timezone_difference():
    """Test timezone difference calculations"""
    assert timezone_difference("America/Los_Angeles", "America/Los_Angeles") == 0
    diff = timezone_difference("America/Los_Angeles", "Europe/London")
    assert 8 <= diff <= 9  # Account for daylight savings


def test_timezone_score():
    """Test timezone score calculation"""
    program = Program(
        id="TEST1",
        name="Test Program",
        timezone="America/Los_Angeles",
        required_skills=set(),
        required_time=0.5,
        required_level=3,
        stakeholder_timezones={"America/Los_Angeles"}  # Same timezone region
    )

    # Same timezone
    score = calculate_timezone_score("America/Los_Angeles", program)
    assert score == 1.0

    # Moderate timezone difference
    score = calculate_timezone_score("America/New_York", program)
    assert score == 1.0  # Within 3 hours

    # Large timezone difference
    score = calculate_timezone_score("Asia/Singapore", program)
    assert score == 0.0  # More than 6 hours


def test_data_validator():
    """Test data validation"""
    validator = DataValidator()

    # Test TPM validation
    tpm = TPM(
        id="TPM001",
        name="Test TPM",
        timezone="UTC",
        skills={"project-management"},
        available_time=0.8,
        level=3,
        conflicts=set()
    )
    validator.validate_tpm(tpm)

    # Test Program validation
    program = Program(
        id="PROG001",
        name="Test Program",
        timezone="UTC",
        required_skills={"project-management"},
        required_time=0.5,
        required_level=3
    )
    validator.validate_program(program)


def test_timezone_handling_edge_cases():
    """Test timezone handling with edge cases"""
    # Empty timezone handling
    assert timezone_difference("", "") == 0  # Empty to Empty = 0 (both UTC)
    assert timezone_difference("", "UTC") == 0  # Empty to UTC = 0
    assert timezone_difference("UTC", "") == 0  # UTC to Empty = 0

    # When one timezone is empty (treated as UTC)
    assert timezone_difference("America/Los_Angeles", "") == timezone_difference("America/Los_Angeles", "UTC")
    assert timezone_difference("", "America/Los_Angeles") == timezone_difference("UTC", "America/Los_Angeles")

    # Invalid timezone handling
    assert timezone_difference("Invalid/Zone", "UTC") == 0
    assert timezone_difference("Invalid/Zone", "Invalid/Zone") == 0

    # Test timezone score with empty stakeholder timezones
    program = Program(
        id="TEST1",
        name="Test Program",
        timezone="",  # Empty timezone
        required_skills=set(),
        required_time=0.5,
        required_level=3,
        stakeholder_timezones=set()  # Empty set
    )

    # All these should return 1.0 as there are no timezone requirements
    assert calculate_timezone_score("", program) == 1.0
    assert calculate_timezone_score("UTC", program) == 1.0
    assert calculate_timezone_score("America/Los_Angeles", program) == 1.0

    # Test with valid program timezone but empty TPM timezone
    program.timezone = "America/Los_Angeles"
    score = calculate_timezone_score("", program)
    # Should be equivalent to comparing with UTC
    assert score == calculate_timezone_score("UTC", program)
