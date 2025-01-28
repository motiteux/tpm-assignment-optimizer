from dataclasses import dataclass, field
from typing import Set, List


@dataclass
class TPM:
    id: str
    name: str
    timezone: str
    skills: Set[str]
    available_time: float
    level: int
    conflicts: Set[str]
    allow_overload: bool = False
    fixed_program: str = None
    desired_programs: Set[str] = field(default_factory=set)
    assigned_programs: List[str] = field(default_factory=list)
    portfolios: Set[str] = field(default_factory=set)

    def __post_init__(self):
        """Validate TPM data after initialization"""
        if not 0 <= self.available_time <= 1:
            raise ValueError(f"Available time must be between 0 and 1, got {self.available_time}")
        if not 1 <= self.level <= 5:
            raise ValueError(f"Level must be between 1 and 5, got {self.level}")