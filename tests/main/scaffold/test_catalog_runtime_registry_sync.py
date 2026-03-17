from __future__ import annotations

import importlib

from src.strategy.runtime.registry import CAPABILITY_REGISTRY
import src.main.scaffold.catalog as catalog_module
import src.strategy.runtime.registry as registry_module


def test_scaffold_catalog_service_activation_keys_follow_runtime_registry() -> None:
    reversed_registry = dict(reversed(tuple(CAPABILITY_REGISTRY.items())))

    registry_module.CAPABILITY_REGISTRY = reversed_registry
    registry_module.CAPABILITY_KEYS = tuple(reversed_registry.keys())
    try:
        reloaded_catalog = importlib.reload(catalog_module)
        assert reloaded_catalog.SERVICE_ACTIVATION_KEYS == tuple(reversed_registry.keys())
    finally:
        registry_module.CAPABILITY_REGISTRY = CAPABILITY_REGISTRY
        registry_module.CAPABILITY_KEYS = tuple(CAPABILITY_REGISTRY.keys())
        importlib.reload(catalog_module)
