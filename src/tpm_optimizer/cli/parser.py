import argparse


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(description='TPM Assignment Optimizer')

    parser.add_argument(
        '--method',
        choices=['milp', 'sa', 'hybrid', 'two-phase'],
        default='milp',
        help='Optimization method: milp, sa (Simulated Annealing), hybrid, or two-phase'
    )

    parser.add_argument(
        '--tpms-file',
        default='tpms.csv',
        help='Path to TPMs CSV file'
    )

    parser.add_argument(
        '--programs-file',
        default='programs.csv',
        help='Path to Programs CSV file'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )

    return parser