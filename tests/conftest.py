import pytest
import pandas as pd
import os
import tempfile
from src.tpm_optimizer.models import TPM, Program


@pytest.fixture
def sample_tpms():
    return {
        "TPM001": TPM(
            id="TPM001",
            name="Test Lead",
            timezone="America/Los_Angeles",
            skills={"project-management", "agile", "mlops"},
            available_time=0.8,
            level=3,
            conflicts={"PROG004"},
            fixed_program="PROG001",
            desired_programs={"PROG002", "PROG003"},
            allow_overload=False
        ),
        "TPM002": TPM(
            id="TPM002",
            name="Senior TPM",
            timezone="Europe/London",
            skills={"project-management", "agile"},
            available_time=1.0,
            level=4,
            conflicts=set(),
            allow_overload=True
        )
    }


@pytest.fixture
def sample_programs():
    return {
        "PROG001": Program(
            id="PROG001",
            name="ML Pipeline",
            timezone="America/Los_Angeles",
            required_skills={"project-management", "mlops"},
            required_time=0.3,
            required_level=3,
            fixed_tpm="TPM001",
            stakeholder_timezones={"America/Los_Angeles", "Europe/London"},
            complexity_score=4,
            portfolio="platform"
        ),
        "PROG002": Program(
            id="PROG002",
            name="Data Platform",
            timezone="Europe/London",
            required_skills={"project-management", "agile"},
            required_time=0.4,
            required_level=3,
            portfolio="platform"
        )
    }


@pytest.fixture
def test_csv_files():
    """Create temporary test CSV files"""
    tpms_data = pd.DataFrame({
        'id': ['TPM001', 'TPM002'],
        'name': ['Test Lead', 'Senior TPM'],
        'timezone': ['America/Los_Angeles', 'Europe/London'],  # Valid timezones
        'skills': ['project-management,agile,mlops', 'project-management,agile'],
        'available_time': [0.8, 1.0],
        'level': [3, 4],
        'conflicts': ['PROG004', ''],
        'fixed_program': ['PROG001', ''],
        'desired_programs': ['PROG002,PROG003', ''],
        'allow_overload': [False, True]
    })

    programs_data = pd.DataFrame({
        'id': ['PROG001', 'PROG002'],
        'name': ['ML Pipeline', 'Data Platform'],
        'timezone': ['America/Los_Angeles', 'Europe/London'],  # Valid timezones
        'required_skills': ['project-management,mlops', 'project-management,agile'],
        'required_time': [0.3, 0.4],
        'required_level': [3, 3],
        'fixed_tpm': ['TPM001', ''],
        'stakeholder_timezones': ['America/Los_Angeles,Europe/London', ''],
        'complexity_score': [4, 3],
        'portfolio': ['platform', 'platform']
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        tpms_path = os.path.join(tmpdir, 'test_tpms.csv')
        programs_path = os.path.join(tmpdir, 'test_programs.csv')

        tpms_data.to_csv(tpms_path, index=False)
        programs_data.to_csv(programs_path, index=False)

        yield {'tpms': tpms_path, 'programs': programs_path}