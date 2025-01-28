def calculate_level_score(tpm_level: int, required_level: int) -> float:
    if tpm_level == required_level:
        return 1.0
    elif tpm_level == required_level + 1:
        return 0.7
    elif tpm_level > required_level + 1:
        return 0.4
    else:
        return 0.0