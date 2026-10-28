"""Jay AI core: platform-independent contracts shared by Windows, Android and backend."""
from .modules import (
    ActionRequest, ActionResult, JayModule, ModuleRegistry, ModuleState, ModuleStatus, ResultKind,
)
from .health import health_report

__version__ = "0.1.0"
API_VERSION = "v1"

__all__ = [
    "ActionRequest", "ActionResult", "JayModule", "ModuleRegistry", "ModuleState",
    "ModuleStatus", "ResultKind", "health_report", "__version__", "API_VERSION",
]
