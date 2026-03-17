from __future__ import annotations

import pytest

from src.main.config.config_loader import ConfigLoader
from src.strategy.runtime.registry import CAPABILITY_REGISTRY


def test_load_service_activation_manifest_rejects_non_bool_values() -> None:
    manifest = {key: False for key in CAPABILITY_REGISTRY}
    manifest["option_chain"] = "yes"

    with pytest.raises(ValueError, match="must be boolean"):
        ConfigLoader.load_service_activation_manifest(
            {"service_activation": manifest}
        )


def test_load_service_activation_manifest_requires_complete_registry_keys() -> None:
    with pytest.raises(ValueError, match="exactly match runtime registry"):
        ConfigLoader.load_service_activation_manifest(
            {"service_activation": {"option_chain": True}}
        )
