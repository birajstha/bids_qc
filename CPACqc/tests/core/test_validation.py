
import pytest
import os
from unittest.mock import MagicMock, patch
from CPACqc.core.validation import validate_args

@patch("os.path.exists")
@patch("os.makedirs")
def test_validate_args_valid(mock_makedirs, mock_exists):
    # Setup mocks
    mock_exists.side_effect = lambda path: path in ["/bids", "config.csv"]
    args = MagicMock()
    args.bids_dir = "/bids"
    args.qc_dir = "/qc"
    args.config = "config.csv"
    args.sub = ["sub-01", "sub-02"]
    args.n_procs = 2
    args.version = False

    result = validate_args(args)
    assert result == args
    mock_makedirs.assert_called_with("/qc", exist_ok=True)

@patch("os.path.exists")
def test_validate_args_missing_bids(mock_exists):
    mock_exists.return_value = False
    args = MagicMock()
    args.bids_dir = "/missing"
    args.qc_dir = None
    args.config = None
    args.sub = None
    args.n_procs = 1
    args.version = False

    with pytest.raises(ValueError, match="BIDS directory '/missing' does not exist."):
        validate_args(args)

@patch("os.path.exists")
def test_validate_args_invalid_config(mock_exists):
    def exists_side_effect(path):
        return path == "/bids"
    mock_exists.side_effect = exists_side_effect
    args = MagicMock()
    args.bids_dir = "/bids"
    args.qc_dir = None
    args.config = "missing.csv"
    args.sub = None
    args.n_procs = 1
    args.version = False

    with pytest.raises(ValueError, match="Config file 'missing.csv' does not exist."):
        validate_args(args)

@patch("os.path.exists", return_value=True)
def test_validate_args_invalid_subject_label(mock_exists):
    args = MagicMock()
    args.bids_dir = "/bids"
    args.qc_dir = None
    args.config = None
    args.sub = ["01"]
    args.n_procs = 1
    args.version = False

    with pytest.raises(ValueError, match="Invalid subject label format: 01. It should start with 'sub-'"):
        validate_args(args)

@patch("os.path.exists", return_value=True)
def test_validate_args_invalid_n_procs(mock_exists):
    args = MagicMock()
    args.bids_dir = "/bids"
    args.qc_dir = None
    args.config = None
    args.sub = None
    args.n_procs = 0
    args.version = False

    with pytest.raises(ValueError, match="Number of processes '0' should be a positive integer."):
        validate_args(args)

@patch("os.path.exists", return_value=True)
def test_validate_args_version_flag(mock_exists, capsys):
    args = MagicMock()
    args.bids_dir = "/bids"
    args.qc_dir = None
    args.config = None
    args.sub = None
    args.n_procs = 1
    args.version = True

    from CPACqc import __version__
    validate_args(args)
    captured = capsys.readouterr()
    assert f"CPACqc version : {__version__}" in captured.out