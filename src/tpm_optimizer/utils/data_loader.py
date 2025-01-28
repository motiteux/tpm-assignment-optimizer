import pandas as pd
from typing import Dict, Tuple, Set
from ..models import TPM, Program


def load_data(tpms_file: str, programs_file: str) -> Tuple[Dict[str, TPM], Dict[str, Program]]:
    """Load TPM and Program data from CSV files"""
    tpms_df = pd.read_csv(tpms_file)
    programs_df = pd.read_csv(programs_file)

    def split_if_string(value) -> Set[str]:
        return set(value.split(',')) if isinstance(value, str) else set()

    def safe_get(row, key, default=None):
        value = row[key] if key in row and pd.notna(row[key]) else default
        return value if value != '' else default

    tpms = {}
    for _, row in tpms_df.iterrows():
        allow_overload_value = str(safe_get(row, 'allow_overload', '')).lower()
        allow_overload = allow_overload_value in ['true', '1', 'yes', 't', 'y']

        tpm = TPM(
            id=str(row['id']),
            name=safe_get(row, 'name', ''),
            timezone=safe_get(row, 'timezone', 'UTC'),
            skills=split_if_string(safe_get(row, 'skills', '')),
            available_time=float(safe_get(row, 'available_time', 0)),
            level=int(safe_get(row, 'level', 1)),
            conflicts=split_if_string(safe_get(row, 'conflicts', '')),
            allow_overload=allow_overload,
            fixed_program=safe_get(row, 'fixed_program'),
            desired_programs=split_if_string(safe_get(row, 'desired_programs', ''))
        )
        tpms[str(row['id'])] = tpm

    programs = {}
    for _, row in programs_df.iterrows():
        programs[str(row['id'])] = Program(
            id=str(row['id']),
            name=safe_get(row, 'name', ''),
            timezone=safe_get(row, 'timezone', 'UTC'),
            required_skills=split_if_string(safe_get(row, 'required_skills', '')),
            required_time=float(safe_get(row, 'required_time', 0)),
            required_level=int(safe_get(row, 'required_level', 1)),
            fixed_tpm=str(safe_get(row, 'fixed_tpm')) if pd.notna(row.get('fixed_tpm')) else None,
            stakeholder_timezones=split_if_string(safe_get(row, 'stakeholder_timezones', '')),
            complexity_score=int(safe_get(row, 'complexity_score', 1)),
            portfolio=safe_get(row, 'portfolio', '')
        )

    return tpms, programs
