from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.main.process.child_process import ChildProcess
from src.main.process.recorder_process import RecorderProcess


def test_child_process_waits_for_trading_readiness() -> None:
    process = ChildProcess.__new__(ChildProcess)
    process.logger = MagicMock()
    process.gateway_manager = MagicMock()

    process._wait_for_connection(timeout=12.5)

    process.gateway_manager.wait_for_ready.assert_called_once_with("trading", 12.5)


def test_recorder_process_waits_for_recording_readiness() -> None:
    process = RecorderProcess.__new__(RecorderProcess)
    process.logger = MagicMock()
    process.gateway_manager = MagicMock()

    process._wait_for_connection(timeout=8.0)

    process.gateway_manager.wait_for_ready.assert_called_once_with("recording", 8.0)


def test_child_process_init_strategies_does_not_sleep_when_all_are_ready() -> None:
    process = ChildProcess.__new__(ChildProcess)
    process.logger = MagicMock()

    strategies = {
        "alpha": SimpleNamespace(inited=False),
        "beta": SimpleNamespace(inited=False),
    }

    def init_strategy(strategy_name: str) -> None:
        strategies[strategy_name].inited = True

    process.strategy_engine = SimpleNamespace(
        strategies=strategies,
        init_strategy=MagicMock(side_effect=init_strategy),
    )

    with patch("src.main.process.child_process.time.sleep") as sleep_mock:
        process._init_strategies()

    sleep_mock.assert_not_called()
    assert process.strategy_engine.init_strategy.call_count == 2


def test_child_process_wait_for_strategies_initialized_reports_names() -> None:
    process = ChildProcess.__new__(ChildProcess)
    process.logger = MagicMock()
    process.strategy_engine = SimpleNamespace(
        strategies={
            "alpha": SimpleNamespace(inited=False),
            "beta": SimpleNamespace(inited=True),
        }
    )

    with patch("src.main.process.child_process.time.sleep", return_value=None):
        with pytest.raises(TimeoutError, match="alpha"):
            process._wait_for_strategies_initialized(timeout=0.01, check_interval=0.01)
