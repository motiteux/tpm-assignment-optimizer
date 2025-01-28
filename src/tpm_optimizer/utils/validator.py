from ..models import TPM, Program


class DataValidator:
    @staticmethod
    def validate_tpm(tpm: TPM):
        """Validate TPM data"""
        assert isinstance(tpm.id, str), "TPM ID must be a string"
        assert 0 <= tpm.available_time <= 1, "Available time must be between 0 and 1"
        assert 1 <= tpm.level <= 5, "TPM level must be between 1 and 5"
        assert isinstance(tpm.timezone, str), "Timezone must be a string"
        if tpm.available_time > 1:
            print(f"Warning: TPM {tpm.id} ({tpm.name}) has capacity > 1: {tpm.available_time}")

    @staticmethod
    def validate_program(program: Program):
        """Validate Program data"""
        assert isinstance(program.id, str), "Program ID must be a string"
        assert 0 < program.required_time <= 1, "Required time must be between 0 and 1"
        assert 1 <= program.required_level <= 5, "Required level must be between 1 and 5"
        assert isinstance(program.timezone, str), "Timezone must be a string"
        assert 1 <= program.complexity_score <= 5, "Complexity score must be between 1 and 5"