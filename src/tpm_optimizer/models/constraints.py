from dataclasses import dataclass


@dataclass
class LoadTargets:
    """Target load ranges for TPM assignments"""
    MIN_LOAD = 0.7    # Minimum acceptable utilization
    TARGET_LOAD = 0.9 # Ideal utilization target
    MAX_LOAD = 1.0    # Maximum load unless overload allowed


class ConstraintType:
    """Types of constraints for optimization"""
    HARD = "hard"
    SOFT = "soft"


@dataclass
class TPMConstraints:
    """TPM-specific constraints"""
    # Hard constraints
    MAX_CAPACITY: float = 1.0
    MAX_PORTFOLIOS: int = 2
    MAX_TIMEZONE_SPREAD: int = 6
    MAX_ASSIGNMENTS: int = 3

    # Soft constraints
    MIN_UTILIZATION: float = 0.7
    TARGET_PORTFOLIO_DIVERSITY: int = 2
    PREFERRED_TIMEZONE_SPREAD: int = 3