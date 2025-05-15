
import pytest
from CPACqc.ui.cli import get_args

import sys
import argparse
import pytest
from unittest.mock import patch


def test_get_args_required_only():
    test_args = ["prog", "-d", "/path/to/bids"]
    with patch.object(sys, 'argv', test_args):
        args = get_args()
        assert args.bids_dir == "/path/to/bids"
        assert args.qc_dir is None
        assert args.config is None
        assert args.sub is None
        assert args.n_procs == 8

def test_get_args_all_options():
    test_args = [
        "prog", "-d", "/bids", "-o", "/qc", "-c", "config.csv", 
        "-s", "sub-01", "sub-02", "-n", "4"
    ]
    with patch.object(sys, 'argv', test_args):
        args = get_args()
        assert args.bids_dir == "/bids"
        assert args.qc_dir == "/qc"
        assert args.config == "config.csv"
        assert args.sub == ["sub-01", "sub-02"]
        assert args.n_procs == 4

