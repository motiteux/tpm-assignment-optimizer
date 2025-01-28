# tests/test_utils/test_loader.py
import pytest
from src.tpm_optimizer.models import TPM, Program
from src.tpm_optimizer.utils import load_data


def test_load_data(test_csv_files):
    """Test data loading from CSV files"""
    tpms, programs = load_data(test_csv_files['tpms'], test_csv_files['programs'])

    assert len(tpms) == 2
    assert isinstance(tpms['TPM001'], TPM)
    assert tpms['TPM001'].name == "Test Lead"
    assert tpms['TPM001'].skills == {"project-management", "agile", "mlops"}

    assert len(programs) == 2
    assert isinstance(programs['PROG001'], Program)
    assert programs['PROG001'].name == "ML Pipeline"
    assert programs['PROG001'].required_skills == {"project-management", "mlops"}