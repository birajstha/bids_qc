import pytest
from unittest.mock import patch, MagicMock
from CPACqc.services.multiprocessing_service import MultiprocessingPort
from CPACqc.utils.logging.log import FileLogger as logger

from CPACqc.utils.multiprocessing.multiprocessing_utils import ProcessPoolMultiprocessing

def dummy_func(x):
    return x * 2

def dummy_func_error(x):
    raise ValueError("Test error")

def test_run_success(monkeypatch):
    # Patch logger to avoid actual logging
    monkeypatch.setattr(logger, "info", lambda msg: None)
    monkeypatch.setattr(logger, "error", lambda msg: None)

    runner = ProcessPoolMultiprocessing()
    args = [1, 2, 3]
    not_plotted = runner.run(dummy_func, args, n_procs=2)
    assert not not_plotted  # Should be empty if all succeed

def test_run_with_error(monkeypatch):
    monkeypatch.setattr(logger, "info", lambda msg: None)
    monkeypatch.setattr(logger, "error", lambda msg: None)

    runner = ProcessPoolMultiprocessing()
    args = [1, 2]
    not_plotted = runner.run(dummy_func_error, args, n_procs=2)
    assert set(not_plotted) == set(args)