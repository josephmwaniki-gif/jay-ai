"""Provider-agnostic chat layer.

- Providers are replaceable: anything with `name` and `complete(messages, timeout)`.
- Credentials come from environment variables only; they are never logged, put in
  error messages, or stored in memory/history.
- Model text is returned as GENERATED, never VERIFIED: it is an answer, not proof
  that any action was carried out.
- If no provider is configured or all fail, a clear ERROR result is returned.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable, Mapping, Protocol, Sequence

from .modules import ActionResult, ResultKind

SYSTEM_PROMPT = (
    "You are Jay, a friendly, confident personal AI assistant. Address the user as 'Sir'. "
    "Reply in the language the user writes in (English, Kiswahili, or Sheng). "
    "You can only answer in text. Never claim you opened an app, sent a message, "
    "changed a file, or performed any action on the user's device."
)
DEFAULT_TIMEOUT = 30.0
MAX_HISTORY = 20  # messages kept in memory per session

Transport = Callable[[str, Mapping[str, str], Mapping[str, Any], float], Mapping[str, Any]]


class ProviderError(Exception):
    """A provider failed. `code` is safe to show; it never contains credentials."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class ChatProvider(Protocol):
    name: str

    def complete(self, messages: Sequence[Mapping[str, str]], timeout: float) -> str: ...


def http_post_json(url: str, headers: Mapping[str, str], body: Mapping[str, Any], timeout: float) -> Mapping[str, Any]:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # https enforced by callers' URLs
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        code = "rate_limited" if exc.code == 429 else "auth_failed" if exc.code in (401, 403) else "http_error"
        raise ProviderError(code, f"provider returned HTTP {exc.code}") from None
    except TimeoutError:
        raise ProviderError("timeout", "provider timed out") from None
    except (urllib.error.URLError, OSError):
        raise ProviderError("unreachable", "provider could not be reached") from None
    except ValueError:
        raise ProviderError("bad_response", "provider returned invalid JSON") from None


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str, transport: Transport = http_post_json,
                 url: str = "https://api.anthropic.com/v1/messages") -> None:
        self._key, self._model, self._transport, self._url = api_key, model, transport, url

    def complete(self, messages: Sequence[Mapping[str, str]], timeout: float) -> str:
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        convo = [dict(m) for m in messages if m["role"] != "system"]
        data = self._transport(
            self._url,
            {"x-api-key": self._key, "anthropic-version": "2023-06-01"},
            {"model": self._model, "max_tokens": 1024, "system": system, "messages": convo},
            timeout,
        )
        try:
            text = "".join(b["text"] for b in data["content"] if b.get("type") == "text")
        except (KeyError, TypeError):
            raise ProviderError("bad_response", "unexpected response shape") from None
        if not text.strip():
            raise ProviderError("bad_response", "empty response")
        return text


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1",
                 transport: Transport = http_post_json) -> None:
        self._key, self._model, self._transport = api_key, model, transport
        self._url = base_url.rstrip("/") + "/chat/completions"

    def complete(self, messages: Sequence[Mapping[str, str]], timeout: float) -> str:
        data = self._transport(
            self._url, {"Authorization": f"Bearer {self._key}"},
            {"model": self._model, "messages": [dict(m) for m in messages]}, timeout,
        )
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise ProviderError("bad_response", "unexpected response shape") from None
        if not text or not text.strip():
            raise ProviderError("bad_response", "empty response")
        return text


class ChatRouter:
    """Tries providers in priority order; falls back on failure."""

    def __init__(self, providers: Sequence[ChatProvider], timeout: float = DEFAULT_TIMEOUT) -> None:
        self._providers = list(providers)
        self._timeout = timeout
        self._history: list[dict[str, str]] = []

    @property
    def provider_names(self) -> list[str]:
        return [p.name for p in self._providers]

    def clear_history(self) -> None:
        self._history.clear()

    def chat(self, user_text: str) -> ActionResult:
        user_text = user_text.strip()
        if not user_text:
            return ActionResult.error("empty_message", "Message is empty.")
        if not self._providers:
            return ActionResult.error("no_provider", "No AI provider is configured.")
        turn = self._history + [{"role": "user", "content": user_text}]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + turn
        failures: list[str] = []
        for provider in self._providers:
            try:
                text = provider.complete(messages, self._timeout)
            except ProviderError as exc:
                failures.append(f"{provider.name}: {exc.code}")
                continue
            except Exception as exc:  # unknown provider bug; never leak details
                failures.append(f"{provider.name}: {type(exc).__name__}")
                continue
            self._history = (turn + [{"role": "assistant", "content": text}])[-MAX_HISTORY:]
            return ActionResult(ResultKind.GENERATED, text, {"provider": provider.name})
        return ActionResult.error("all_providers_failed", "AI is unavailable (" + "; ".join(failures) + ").")


def build_router_from_env(environ: Mapping[str, str] | None = None) -> ChatRouter:
    """JAY_ANTHROPIC_API_KEY [+ JAY_ANTHROPIC_MODEL]; JAY_OPENAI_API_KEY + JAY_OPENAI_MODEL [+ JAY_OPENAI_BASE_URL]."""
    env = os.environ if environ is None else environ
    providers: list[ChatProvider] = []
    if env.get("JAY_ANTHROPIC_API_KEY"):
        providers.append(AnthropicProvider(env["JAY_ANTHROPIC_API_KEY"], env.get("JAY_ANTHROPIC_MODEL") or "claude-sonnet-5-5"))
    if env.get("JAY_OPENAI_API_KEY") and env.get("JAY_OPENAI_MODEL"):
        providers.append(OpenAICompatibleProvider(
            env["JAY_OPENAI_API_KEY"], env["JAY_OPENAI_MODEL"], env.get("JAY_OPENAI_BASE_URL") or "https://api.openai.com/v1"))
    return ChatRouter(providers)
