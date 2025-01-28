from dataclasses import dataclass, field
from typing import Set


@dataclass
class Program:
    id: str
    name: str
    timezone: str
    required_skills: Set[str]
    required_time: float
    required_level: int
    fixed_tpm: str = None
    stakeholder_timezones: Set[str] = field(default_factory=set)
    complexity_score: int = 1
    portfolio: str = ''
    assigned_tpm: str = None

    def __post_init__(self):
        """Validate Program data after initialization"""
        if not 0 < self.required_time <= 1:
            raise ValueError(f"Required time must be between 0 and 1, got {self.required_time}")
        if not 1 <= self.required_level <= 5:
            raise ValueError(f"Required level must be between 1 and 5, got {self.required_level}")
        if not 1 <= self.complexity_score <= 5:
            raise ValueError(f"Complexity score must be between 1 and 5, got {self.complexity_score}")