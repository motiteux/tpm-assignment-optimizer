#!/usr/bin/env python3
"""
TPM Assignment Optimizer main entry point.
"""

from .cli import create_parser, run_optimization


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