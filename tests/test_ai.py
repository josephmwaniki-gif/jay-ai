"""All provider calls here are MOCKS. They do not prove a live provider integration."""
import unittest

from jay_core.ai import (
    AnthropicProvider, ChatRouter, OpenAICompatibleProvider, ProviderError, build_router_from_env,
)
from jay_core.modules import ResultKind

SECRET = "sk-test-SECRET-123"


class FakeProvider:
    def __init__(self, name, reply=None, error=None):
        self.name, self.reply, self.error, self.seen = name, reply, error, []

    def complete(self, messages, timeout):
        self.seen.append(list(messages))
        if self.error:
            raise self.error
        return self.reply


class RouterTests(unittest.TestCase):
    def test_no_provider(self):
        r = ChatRouter([]).chat("hi")
        self.assertEqual(r.error_code, "no_provider")

    def test_empty_message(self):
        self.assertEqual(ChatRouter([FakeProvider("a", "x")]).chat("  ").error_code, "empty_message")

    def test_success_is_generated_not_verified(self):
        r = ChatRouter([FakeProvider("a", "hello Sir")]).chat("hi")
        self.assertEqual(r.kind, ResultKind.GENERATED)
        self.assertEqual(r.data["provider"], "a")

    def test_fallback_to_second_provider(self):
        a = FakeProvider("a", error=ProviderError("timeout", "t"))
        b = FakeProvider("b", "from b")
        r = ChatRouter([a, b]).chat("hi")
        self.assertEqual(r.message, "from b")
        self.assertEqual(len(a.seen), 1)

    def test_all_fail_reports_error(self):
        r = ChatRouter([FakeProvider("a", error=ProviderError("timeout", "t")),
                        FakeProvider("b", error=RuntimeError("boom"))]).chat("hi")
        self.assertEqual(r.error_code, "all_providers_failed")
        self.assertIn("a: timeout", r.message)
        self.assertIn("b: RuntimeError", r.message)

    def test_history_kept_and_bounded_and_not_stored_on_failure(self):
        p = FakeProvider("a", "ok")
        router = ChatRouter([p])
        for i in range(30):
            router.chat(f"m{i}")
        self.assertLessEqual(len(router._history), 20)
        self.assertEqual(p.seen[-1][0]["role"], "system")
        bad = ChatRouter([FakeProvider("a", error=ProviderError("timeout", "t"))])
        bad.chat("hi")
        self.assertEqual(bad._history, [])


class ProviderTests(unittest.TestCase):
    def test_anthropic_request_and_parse(self):
        calls = []
        def transport(url, headers, body, timeout):
            calls.append((url, headers, body))
            return {"content": [{"type": "text", "text": "Habari Sir"}]}
        p = AnthropicProvider(SECRET, "m1", transport)
        out = p.complete([{"role": "system", "content": "S"}, {"role": "user", "content": "hi"}], 5)
        self.assertEqual(out, "Habari Sir")
        url, headers, body = calls[0]
        self.assertTrue(url.startswith("https://"))
        self.assertEqual(body["system"], "S")
        self.assertEqual(body["messages"], [{"role": "user", "content": "hi"}])

    def test_openai_parse_and_bad_shape(self):
        ok = OpenAICompatibleProvider(SECRET, "m", transport=lambda *a: {"choices": [{"message": {"content": "yo"}}]})
        self.assertEqual(ok.complete([{"role": "user", "content": "hi"}], 5), "yo")
        bad = OpenAICompatibleProvider(SECRET, "m", transport=lambda *a: {"nope": 1})
        with self.assertRaises(ProviderError) as ctx:
            bad.complete([{"role": "user", "content": "hi"}], 5)
        self.assertEqual(ctx.exception.code, "bad_response")

    def test_secret_never_in_router_errors(self):
        def transport(*a):
            raise ProviderError("auth_failed", "provider returned HTTP 401")
        r = ChatRouter([AnthropicProvider(SECRET, "m", transport)]).chat("hi")
        self.assertNotIn(SECRET, r.message)


class EnvTests(unittest.TestCase):
    def test_no_keys_means_no_providers(self):
        self.assertEqual(build_router_from_env({}).provider_names, [])

    def test_keys_build_providers_in_order(self):
        env = {"JAY_ANTHROPIC_API_KEY": "k", "JAY_OPENAI_API_KEY": "k2", "JAY_OPENAI_MODEL": "m"}
        self.assertEqual(build_router_from_env(env).provider_names, ["anthropic", "openai-compatible"])

    def test_openai_needs_model(self):
        self.assertEqual(build_router_from_env({"JAY_OPENAI_API_KEY": "k"}).provider_names, [])


if __name__ == "__main__":
    unittest.main()
