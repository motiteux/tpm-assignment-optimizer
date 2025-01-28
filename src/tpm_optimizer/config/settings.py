# src/tpm_optimizer/config/settings.py
from dataclasses import dataclass
from typing import Dict


@dataclass
class OptimizationSettings:
    # Simulated Annealing parameters
    INITIAL_TEMPERATURE: float = 1.0
    COOLING_RATE: float = 0.995
    MIN_TEMPERATURE: float = 0.001
    MAX_ITERATIONS: int = 10000

    # Hybrid optimizer parameters
    MAX_RUNTIME: int = 300  # 5 minutes
    NO_IMPROVEMENT_LIMIT: int = 1000

    # Scoring weights
    WEIGHTS: Dict[str, float] = {
        'timezone': 0.3,
        'skill': 0.25,
        'level': 0.2,
        'portfolio': 0.15,
        'preference': 0.1
    }

    # Load targets
    TARGET_UTILIZATION: float = 0.85
    MIN_UTILIZATION: float = 0.7
    MAX_UTILIZATION: float = 1.0