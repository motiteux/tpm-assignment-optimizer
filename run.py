#!/usr/bin/env python3
"""
Wrapper script to run the TPM optimizer locally without installation.
"""
import sys
import os

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from tpm_optimizer.cli import create_parser, run_optimization


def main():
    parser = create_parser()
    args = parser.parse_args()

    run_optimization(
        method=args.method,
        tpms_file=args.tpms_file,
        programs_file=args.programs_file,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()