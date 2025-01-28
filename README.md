# TPM Assignment Optimizer

## Overview

Python-based tool for optimizing Technical Program Manager (TPM) assignments using multiple optimization strategies:
- Mixed Integer Linear Programming (MILP) for exact solutions
- Simulated Annealing (SA) for meta-heuristic optimization
- Hybrid Multi-Objective optimization for Pareto-optimal solutions
- Two-Phase optimization for rule-based assignment

The system matches TPMs to programs while respecting various constraints including timezone alignment, skill requirements, and capacity limits.

## Features
- Timezone-aware matching with stakeholder consideration
- Skill and level requirements validation
- Portfolio diversity management
- Fixed assignment handling
- Capacity and utilization optimization
- Comprehensive reporting

## Requirements

### Python Dependencies

    pandas>=2.1.0
    numpy>=1.24.0 
    pytz>=2023.3
    pulp>=2.7.0

### Input Files

#### tpms.csv

    id,name,timezone,skills,available_time,level,conflicts,fixed_program,desired_programs

Field descriptions:
- id: Unique TPM identifier (string)
- name: TPM name (string)
- timezone: IANA timezone format (e.g., "America/New_York")
- skills: Comma-separated list of skills
- available_time: Capacity (float 0-1)
- level: TPM level (integer 1-5)
- conflicts: Comma-separated list of program IDs to avoid
- fixed_program: Program ID if pre-assigned
- desired_programs: Comma-separated list of preferred programs

#### programs.csv

    id,name,timezone,required_skills,required_time,required_level,fixed_tpm,stakeholder_timezones,complexity_score,portfolio

Field descriptions:
- id: Unique program identifier (string)
- name: Program name (string)
- timezone: Primary IANA timezone
- required_skills: Comma-separated list of required skills
- required_time: Required capacity (float 0-1)
- required_level: Required TPM level (integer 1-5)
- fixed_tpm: TPM ID if pre-assigned
- stakeholder_timezones: Comma-separated list of stakeholder timezones
- complexity_score: Program complexity (integer 1-5)
- portfolio: Portfolio identifier (string)

## Installation

Clone repository

    git clone https://github.com/yourusername/tpm-optimizer.git
    cd tpm-optimizer

Create virtual environment (recommended)

    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate

Install dependencies

    pip install -r requirements.txt

## Usage

Prepare input files according to schema above. Then run the optimizer using any of these methods:

    # As a Python module (recommended)
    python -m tpm_optimizer --method sa

    # With specific input files
    python -m tpm_optimizer --tpms-file path/to/tpms.csv --programs-file path/to/programs.csv

    # With verbose output
    python -m tpm_optimizer --method hybrid --verbose

Run optimizer with different methods:

    # Default (MILP)
    python -m tpm_optimizer --method milp

    # Simulated Annealing
    python -m tpm_optimizer --method sa

    # Hybrid Multi-Objective
    python -m tpm_optimizer --method hybrid

    # Two-Phase Rule-Based
    python -m tpm_optimizer --method two-phase

Additional options:
    --tpms-file PATH      Custom path to TPMs CSV file
    --programs-file PATH  Custom path to Programs CSV file
    --verbose            Enable detailed output

## Method Selection Guide

Choose the appropriate method based on your needs:

MILP (--method milp):
- Best for exact solutions
- Smaller datasets
- When optimality is critical

Simulated Annealing (--method sa):
- Good for larger datasets
- When approximate solutions are acceptable
- Better handling of complex constraints

Hybrid (--method hybrid):
- Best for multi-objective optimization
- When balancing multiple competing goals
- More flexible solution space

Two-Phase (--method two-phase):
- Best for very large datasets
- When quick solutions are needed
- Rule-based approach prioritizing capacity

## Constraints

### Hard Constraints

- TPM capacity cannot be exceeded
- TPM level must meet/exceed program requirement
- Fixed assignments must be respected
- Conflicts must be avoided
- Maximum 2 portfolios per TPM
- TPM III+: max 3 programs
- TPM I-II: max 2 programs

### Optimization Weights

- Timezone alignment: 40%
- Skill matching: 25%
- Level matching: 20%
- TPM preferences: 10%
- Random factor: 5%

## Output Reports

### TPM Assignments

- Program ID
- Program Name
- Required Time
- Timezone
- TPM Name
- TPM Timezone
- Timezone Match
- Time Allocation

### Unassigned Programs

- Program ID
- Program Name
- Required Time
- Timezone

### TPM Utilization

- TPM ID
- TPM Name
- Total Capacity
- Used Capacity
- Remaining Capacity
- Utilization %
- Program Count
- Timezone
- Portfolio Diversity

### Summary Metrics

- Assignment Coverage
- Average Timezone Spread
- Average Portfolio Diversity
- Average TPM Utilization
- Timezone Respect Percentage

## Known Limitations

- Performance may degrade with large datasets (>100 programs)
- Fixed assignments must be feasible within constraints
- Timezone matching uses discrete scoring rather than continuous optimization

## Troubleshooting

### Common Issues

Missing dependencies

    pip install -r requirements.txt

Input file format errors

Verify CSV formatting

Check column names match exactly

Ensure no extra whitespace in fields

Timezone errors

Verify all timezones use IANA format

Check for typos in timezone names

No solution found

Verify constraints are not overconstrained

Check fixed assignments are feasible

Review capacity requirements

## Performance Considerations

Recommended maximum size: 60 TPMs × 150 programs

Expected runtime: < 1 minute for recommended size

Memory usage: ~500MB for recommended size

## Project Structure

    tpm-assignment-optimizer/
    ├── src/
    │   └── tpm_optimizer/
    │       ├── models/          # Data classes (TPM, Program)
    │       ├── optimizers/      # Optimization algorithms
    │       │   ├── milp.py     # MILP optimizer
    │       │   ├── simulated_annealing.py
    │       │   ├── hybrid.py
    │       │   └── two_phase.py
    │       ├── utils/           # Utility functions
    │       ├── reporting/       # Report generation
    │       └── cli/            # Command-line interface
    ├── tests/                  # Test suite
    ├── test_data/             # Test data files
    ├── requirements.txt       # Dependencies
    └── README.md             # This file

## Performance Considerations

Performance varies by optimization method:

MILP:
- Recommended maximum: 60 TPMs × 150 programs
- Expected runtime: < 1 minute
- Provides exact solution

Simulated Annealing:
- Can handle larger datasets
- Expected runtime: 1-2 minutes
- Approximate solution

Hybrid:
- Recommended maximum: 80 TPMs × 200 programs
- Expected runtime: 2-3 minutes
- Multi-objective optimization

Two-Phase:
- Can handle largest datasets
- Expected runtime: < 30 seconds
- Rule-based solution

Memory usage: ~500MB for recommended size

## License
MIT License. See LICENSE file for details.