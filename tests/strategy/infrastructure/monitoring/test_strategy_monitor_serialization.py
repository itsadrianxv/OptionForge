"""StrategyMonitor payload serialization tests."""

import json
from datetime import date, datetime

import pytest

pd = pytest.importorskip("pandas")

from src.strategy.infrastructure.monitoring.strategy_monitor import StrategyMonitor


def test_serialize_payload_handles_special_types_without_schema_version():
    """Monitor payload should support special types and skip schema_version injection."""
    monitor = StrategyMonitor(
        variant_name="15m",
        monitor_instance_id="default",
        monitor_db_config={},
    )

    payload = {
        "timestamp": datetime(2026, 3, 6, 10, 30, 0),
        "trading_day": date(2026, 3, 6),
        "symbols": {"rb2501.SHFE", "i2505.DCE"},
        "bars": pd.DataFrame([{"open": 100.0, "close": 101.5, "volume": 10}]),
    }

    payload_text = monitor._serialize_payload(payload)
    parsed = json.loads(payload_text)

    assert "schema_version" not in parsed
    assert parsed["timestamp"] == {"__datetime__": "2026-03-06T10:30:00"}
    assert parsed["trading_day"] == {"__date__": "2026-03-06"}
    assert parsed["symbols"] == {
        "__set__": True,
        "values": ["i2505.DCE", "rb2501.SHFE"],
    }
    assert parsed["bars"] == {
        "__dataframe__": True,
        "records": [{"open": 100.0, "close": 101.5, "volume": 10}],
    }
