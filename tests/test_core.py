import unittest

from jay_core import (
    API_VERSION, ActionRequest, ModuleRegistry, ModuleState, ModuleStatus,
    ActionResult, ResultKind, __version__, health_report,
)


class FakeModule:
    """Mock module for tests only; results here are NOT proof of a live integration."""
    version = "0.0.1"

    def __init__(self, name="fake", state=ModuleState.READY, boom=False):
        self.name = name
        self._state = state
        self._boom = boom
        self.sensitive_actions = frozenset({"delete"})
        self.calls = []

    def status(self):
        if self._boom:
            raise RuntimeError("status exploded")
        return ModuleStatus(self._state, "mock")

    def actions(self):
        return frozenset({"echo", "delete"})

    def execute(self, request):
        self.calls.append(request.action)
        if self._boom:
            raise RuntimeError("exec exploded")
        return ActionResult(ResultKind.VERIFIED, "done", {"action": request.action})


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.reg = ModuleRegistry()
        self.mod = FakeModule()
        self.reg.register(self.mod)

    def test_dispatch_success_is_verified(self):
        r = self.reg.dispatch(ActionRequest("fake", "echo"))
        self.assertEqual(r.kind, ResultKind.VERIFIED)

    def test_unknown_module_and_action(self):
        self.assertEqual(self.reg.dispatch(ActionRequest("nope", "echo")).error_code, "module_not_found")
        self.assertEqual(self.reg.dispatch(ActionRequest("fake", "nope")).error_code, "action_not_found")

    def test_unavailable_module_reports_error_and_is_not_executed(self):
        reg = ModuleRegistry()
        m = FakeModule(state=ModuleState.UNAVAILABLE)
        reg.register(m)
        r = reg.dispatch(ActionRequest("fake", "echo"))
        self.assertEqual(r.kind, ResultKind.ERROR)
        self.assertEqual(r.error_code, "module_unavailable")
        self.assertEqual(m.calls, [])

    def test_sensitive_action_needs_confirmation(self):
        r = self.reg.dispatch(ActionRequest("fake", "delete"))
        self.assertEqual(r.error_code, "confirmation_required")
        self.assertEqual(self.mod.calls, [])
        ok = self.reg.dispatch(ActionRequest("fake", "delete", confirmed=True))
        self.assertEqual(ok.kind, ResultKind.VERIFIED)

    def test_module_exception_becomes_error_result(self):
        reg = ModuleRegistry()
        reg.register(FakeModule(boom=True))
        self.assertEqual(reg.statuses()["fake"].state, ModuleState.UNAVAILABLE)
        self.assertEqual(reg.dispatch(ActionRequest("fake", "echo")).kind, ResultKind.ERROR)

    def test_duplicate_and_invalid_registration(self):
        with self.assertRaises(ValueError):
            self.reg.register(FakeModule())
        with self.assertRaises(TypeError):
            self.reg.register(object())

    def test_health_report(self):
        rep = health_report(self.reg, __version__, API_VERSION)
        self.assertEqual(rep["status"], "ok")
        self.assertEqual(rep["api_version"], "v1")
        reg = ModuleRegistry()
        reg.register(FakeModule(state=ModuleState.UNAVAILABLE))
        self.assertEqual(health_report(reg, __version__, API_VERSION)["status"], "degraded")


if __name__ == "__main__":
    unittest.main()
