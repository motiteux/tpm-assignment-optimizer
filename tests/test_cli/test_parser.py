import pytest  # Add this import
from src.tpm_optimizer.cli.parser import create_parser


def test_parser_creation():
    """Test argument parser creation and defaults"""
    parser = create_parser()
    args = parser.parse_args([])  # Test with no arguments

    assert args.method == 'milp'  # Default method
    assert args.tpms_file == 'tpms.csv'  # Default TPMs file
    assert args.programs_file == 'programs.csv'  # Default programs file
    assert not args.verbose  # Default verbose setting


def test_parser_method_choices():
    """Test method argument choices"""
    parser = create_parser()

    # Test valid methods
    for method in ['milp', 'sa', 'hybrid', 'two-phase']:
        args = parser.parse_args(['--method', method])
        assert args.method == method

    # Test invalid method (should raise error)
    with pytest.raises(SystemExit):
        parser.parse_args(['--method', 'invalid'])