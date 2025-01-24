# TPM Assignment Optimizer

## Overview

Python-based tool for optimizing Technical Program Manager (TPM) assignments using Mixed Integer Linear Programming (MILP). The system matches TPMs to programs while respecting various constraints including timezone alignment, skill requirements, and capacity limits.

## Features

    Timezone-aware matching with stakeholder consideration
    Skill and level requirements validation
    Portfolio diversity management
    Fixed assignment handling
    Capacity and utilization optimization
    Comprehensive reporting

## Requirements

### Python Dependencies

shell

pandas>=2.1.0
numpy>=1.24.0 
pytz>=2023.3
pulp>=2.7.0

### Input Files

#### tpms.csv

python

id,name,timezone,skills,available_time,level,conflicts,fixed_program,desired_programs

Field descriptions:

    id: Unique TPM identifier (string)
    name: TPM name (string)
    timezone: IANA timezone format (e.g., "America/New_York")
    skills: Comma-separated list of skills
    available_time: Capacity (float 0-1)
    level: TPM level (integer 1-5)
    conflicts: Comma-separated list of program IDs to avoid
    fixed_program: Program ID if pre-assigned
    desired_programs: Comma-separated list of preferred programs

#### programs.csv

python

id,name,timezone,required_skills,required_time,required_level,fixed_tpm,stakeholder_timezones,complexity_score,portfolio

Field descriptions:

    id: Unique program identifier (string)
    name: Program name (string)
    timezone: Primary IANA timezone
    required_skills: Comma-separated list of required skills
    required_time: Required capacity (float 0-1)
    required_level: Required TPM level (integer 1-5)
    fixed_tpm: TPM ID if pre-assigned
    stakeholder_timezones: Comma-separated list of stakeholder timezones
    complexity_score: Program complexity (integer 1-5)
    portfolio: Portfolio identifier (string)

## Installation

    Clone repository

bash

git clone https://github.com/yourusername/tpm-optimizer.git
cd tpm-optimizer

    Create virtual environment (recommended)

bash

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

    Install dependencies

bash

pip install -r requirements.txt

## Usage

    Prepare input files according to schema above
    Place input files in same directory as script
    Run optimizer:

bash

python tpm_optimizer.py

## Constraints

### Hard Constraints

    TPM capacity cannot be exceeded
    TPM level must meet/exceed program requirement
    Fixed assignments must be respected
    Conflicts must be avoided
    Maximum 2 portfolios per TPM
    TPM III+: max 3 programs
    TPM I-II: max 2 programs

### Optimization Weights

    Timezone alignment: 40%
    Skill matching: 25%
    Level matching: 20%
    TPM preferences: 10%
    Random factor: 5%

## Output Reports

### TPM Assignments

    Program ID
    Program Name
    Required Time
    Timezone
    TPM Name
    TPM Timezone
    Timezone Match
    Time Allocation

### Unassigned Programs

    Program ID
    Program Name
    Required Time
    Timezone

### TPM Utilization

    TPM ID
    TPM Name
    Total Capacity
    Used Capacity
    Remaining Capacity
    Utilization %
    Program Count
    Timezone
    Portfolio Diversity

### Summary Metrics

    Assignment Coverage
    Average Timezone Spread
    Average Portfolio Diversity
    Average TPM Utilization
    Timezone Respect Percentage

## Known Limitations

    Performance may degrade with large datasets (>100 programs)
    Fixed assignments must be feasible within constraints
    Timezone matching uses discrete scoring rather than continuous optimization

## Troubleshooting

### Common Issues

    Missing dependencies

bash

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

## License
MIT License. See LICENSE file for details.