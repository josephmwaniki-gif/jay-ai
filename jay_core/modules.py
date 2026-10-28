"""Module contract and registry.

Rules enforced here (from the Jay AI spec):
- A module never claims an action was performed unless it really was:
  results are tagged VERIFIED (tool actually did it), GENERATED (text/instructions only)
  or ERROR (nothing was done).
- Unavailable or unhealthy modules are reported as such, never silently skipped.
- Sensitive actions require explicit confirmation; the registry refuses otherwise.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol, runtime_checkable


class ModuleState(str, Enum):
    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ResultKind(str, Enum):
    VERIFIED = "verified"    # a real tool/service performed the action
    GENERATED = "generated"  # text or instructions only; nothing was executed
    ERROR = "error"          # nothing was done


@dataclass(frozen=True)
class ModuleStatus:
    state: ModuleState
    detail: str = ""


@dataclass(frozen=True)
class ActionRequest:
    module: str
    action: str
    args: Mapping[str, Any] = field(default_factory=dict)
    confirmed: bool = False  # user explicitly confirmed a sensitive action


@dataclass(frozen=True)
class ActionResult:
    kind: ResultKind
    message: str
    data: Mapping[str, Any] = field(default_factory=dict)
    error_code: str | None = None

    @staticmethod
    def error(code: str, message: str) -> "ActionResult":
        return ActionResult(ResultKind.ERROR, message, error_code=code)


@runtime_checkable
class JayModule(Protocol):
    name: str
    version: str
    sensitive_actions: frozenset[str]  # actions needing explicit confirmation

    def status(self) -> ModuleStatus: ...
    def actions(self) -> frozenset[str]: ...
    def execute(self, request: ActionRequest) -> ActionResult: ...


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, JayModule] = {}

    def register(self, module: JayModule) -> None:
        if not isinstance(module, JayModule):
            raise TypeError("object does not implement the JayModule contract")
        if module.name in self._modules:
            raise ValueError(f"module already registered: {module.name}")
        self._modules[module.name] = module

    def names(self) -> list[str]:
        return sorted(self._modules)

    def statuses(self) -> dict[str, ModuleStatus]:
        out: dict[str, ModuleStatus] = {}
        for name, module in self._modules.items():
            try:
                out[name] = module.status()
            except Exception as exc:  # a broken module must not break the registry
                out[name] = ModuleStatus(ModuleState.UNAVAILABLE, f"status check failed: {type(exc).__name__}")
        return out

    def dispatch(self, request: ActionRequest) -> ActionResult:
        module = self._modules.get(request.module)
        if module is None:
            return ActionResult.error("module_not_found", f"No module named '{request.module}'.")
        if request.action not in module.actions():
            return ActionResult.error("action_not_found", f"'{request.module}' has no action '{request.action}'.")
        status = self.statuses()[request.module]
        if status.state is ModuleState.UNAVAILABLE:
            return ActionResult.error("module_unavailable", f"'{request.module}' is unavailable: {status.detail}")
        if request.action in module.sensitive_actions and not request.confirmed:
            return ActionResult.error("confirmation_required", f"'{request.action}' needs explicit user confirmation.")
        try:
            return module.execute(request)
        except Exception as exc:
            return ActionResult.error("module_error", f"'{request.module}' failed: {type(exc).__name__}")
