from __future__ import annotations

import importlib
from typing import Any

from .models import CapabilityContribution, RuntimeKernel, StrategyRuntime
from .registry import CAPABILITY_KEYS, CAPABILITY_REGISTRY


class StrategyRuntimeBuilder:
    def build(self, entry: Any, full_config: dict[str, Any]) -> StrategyRuntime:
        manifest = self._validate_manifest(full_config.get("service_activation"))
        enabled = tuple(key for key, active in manifest.items() if active)
        kernel = RuntimeKernel(entry=entry, logger=getattr(entry, "logger", None))
        contributions = self._load_enabled_contributions(enabled, entry, full_config, kernel)
        return self._merge_contributions(enabled, contributions, kernel)

    def _validate_manifest(self, raw_manifest: Any) -> dict[str, bool]:
        if not isinstance(raw_manifest, dict):
            raise ValueError("service_activation manifest must be a table")

        unknown = sorted(set(raw_manifest) - set(CAPABILITY_REGISTRY))
        if unknown:
            joined = ", ".join(unknown)
            raise ValueError(f"unknown capability keys: {joined}")

        missing = [key for key in CAPABILITY_KEYS if key not in raw_manifest]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"missing capability keys: {joined}")

        manifest: dict[str, bool] = {}
        for key in CAPABILITY_KEYS:
            value = raw_manifest[key]
            if not isinstance(value, bool):
                raise ValueError(f"capability '{key}' must be boolean")
            manifest[key] = value

        enabled = {key for key, active in manifest.items() if active}
        for key in enabled:
            spec = CAPABILITY_REGISTRY[key]
            missing_requires = tuple(requirement for requirement in spec.requires if requirement not in enabled)
            if missing_requires:
                joined = ", ".join(missing_requires)
                raise ValueError(f"capability '{key}' requires: {joined}")

            present_conflicts = tuple(conflict for conflict in spec.conflicts if conflict in enabled)
            if present_conflicts:
                joined = ", ".join(present_conflicts)
                raise ValueError(f"capability '{key}' conflicts with: {joined}")

        return manifest

    def _load_enabled_contributions(
        self,
        enabled: tuple[str, ...],
        entry: Any,
        full_config: dict[str, Any],
        kernel: RuntimeKernel,
    ) -> dict[str, CapabilityContribution]:
        contributions: dict[str, CapabilityContribution] = {}
        for key in enabled:
            provider_path = CAPABILITY_REGISTRY[key].provider_import_path
            module = importlib.import_module(provider_path)
            provider = getattr(module, "PROVIDER")
            contribution = provider.build(entry, full_config, kernel)
            contributions[key] = contribution
        return contributions

    def _merge_contributions(
        self,
        enabled: tuple[str, ...],
        contributions: dict[str, CapabilityContribution],
        kernel: RuntimeKernel,
    ) -> StrategyRuntime:
        runtime = StrategyRuntime(enabled_capabilities=enabled, kernel=kernel)

        for key in enabled:
            spec = CAPABILITY_REGISTRY[key]
            contribution = contributions[key]
            for role_path in spec.single_roles:
                value = self._get_role_value(contribution, role_path)
                if value is None:
                    continue
                if self._get_role_value(runtime, role_path) is not None:
                    raise ValueError(f"runtime role collision: {role_path}")
                self._set_role_value(runtime, role_path, value)

            for role_path in spec.multi_roles:
                existing = tuple(self._get_role_value(runtime, role_path))
                extra = tuple(self._get_role_value(contribution, role_path))
                if extra:
                    self._set_role_value(runtime, role_path, existing + extra)

        return runtime

    def _get_role_value(self, container: Any, role_path: str) -> Any:
        current = container
        for attr in role_path.split("."):
            current = getattr(current, attr)
        return current

    def _set_role_value(self, container: Any, role_path: str, value: Any) -> None:
        *parents, attr = role_path.split(".")
        current = container
        for parent in parents:
            current = getattr(current, parent)
        setattr(current, attr, value)
