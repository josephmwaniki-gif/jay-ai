"""Versioned health report, the basis of the future /v1/health and /v1/version API."""
from __future__ import annotations

from .modules import ModuleRegistry, ModuleState


def health_report(registry: ModuleRegistry, app_version: str, api_version: str) -> dict:
    statuses = registry.statuses()
    states = {s.state for s in statuses.values()}
    if ModuleState.UNAVAILABLE in states:
        overall = "degraded"
    elif ModuleState.DEGRADED in states:
        overall = "degraded"
    else:
        overall = "ok"
    return {
        "api_version": api_version,
        "app_version": app_version,
        "status": overall,
        "modules": {n: {"state": s.state.value, "detail": s.detail} for n, s in sorted(statuses.items())},
    }
