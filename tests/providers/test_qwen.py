"""Unit tests for the QwenProvider."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from providers.qwen import DEFAULT_BASE_URL, DEFAULT_MODEL, QwenProvider


def _make_choice(
    content: str | None = "Hello!",
    tool_calls=None,
    finish_reason: str = "stop",
):
    """Build a minimal mock choice object matching the OpenAI SDK shape."""
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls or []
    message.model_extra = {}

    choice = MagicMock()
    choice.message = message
    choice.finish_reason = finish_reason
    return choice


def _make_usage(prompt=10, completion=5):
    usage = MagicMock()
    usage.prompt_tokens = prompt
    usage.completion_tokens = completion
    usage.total_tokens = prompt + completion
    return usage


def _make_response(choice, usage=None):
    response = MagicMock()
    response.choices = [choice]
    response.usage = usage or _make_usage()
    return response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def provider():
    """Return a QwenProvider with a dummy API key (no real HTTP calls)."""
    return QwenProvider(api_key="sk-test")


# ---------------------------------------------------------------------------
# Initialisation tests
# ---------------------------------------------------------------------------


class TestQwenProviderInit:
    def test_default_base_url(self, provider):
        assert provider.base_url == DEFAULT_BASE_URL

    def test_custom_base_url(self):
        p = QwenProvider(api_key="sk-test", base_url="https://custom.example.com/v1")
        assert p.base_url == "https://custom.example.com/v1"

    def test_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("QWEN_API_KEY", "sk-env-key")
        p = QwenProvider()
        assert p.api_key == "sk-env-key"

    def test_explicit_key_overrides_env(self, monkeypatch):
        monkeypatch.setenv("QWEN_API_KEY", "sk-env-key")
        p = QwenProvider(api_key="sk-explicit")
        assert p.api_key == "sk-explicit"


# ---------------------------------------------------------------------------
# get_default_model
# ---------------------------------------------------------------------------


class TestGetDefaultModel:
    def test_returns_qwen_plus(self, provider):
        assert provider.get_default_model() == DEFAULT_MODEL

    def test_default_model_constant(self):
        assert DEFAULT_MODEL == "qwen-plus"


# ---------------------------------------------------------------------------
# chat – basic text response
# ---------------------------------------------------------------------------


class TestChat:
    @pytest.fixture(autouse=True)
    def mock_openai(self, provider):
        choice = _make_choice(content="Hi there!")
        response = _make_response(choice)
        provider._client.chat.completions.create = AsyncMock(return_value=response)

    async def test_returns_llm_response(self, provider):
        result = await provider.chat(messages=[{"role": "user", "content": "Hello"}])
        assert result.content == "Hi there!"

    async def test_finish_reason(self, provider):
        result = await provider.chat(messages=[{"role": "user", "content": "Hello"}])
        assert result.finish_reason == "stop"

    async def test_usage_populated(self, provider):
        result = await provider.chat(messages=[{"role": "user", "content": "Hello"}])
        assert result.usage["prompt_tokens"] == 10
        assert result.usage["completion_tokens"] == 5
        assert result.usage["total_tokens"] == 15

    async def test_no_tool_calls_by_default(self, provider):
        result = await provider.chat(messages=[{"role": "user", "content": "Hello"}])
        assert result.tool_calls == []
        assert not result.has_tool_calls

    async def test_uses_default_model(self, provider):
        await provider.chat(messages=[{"role": "user", "content": "Hello"}])
        call_kwargs = provider._client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == DEFAULT_MODEL

    async def test_custom_model_passed_through(self, provider):
        await provider.chat(messages=[{"role": "user", "content": "Hello"}], model="qwen-max")
        call_kwargs = provider._client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "qwen-max"

    async def test_max_tokens_and_temperature_forwarded(self, provider):
        await provider.chat(messages=[{"role": "user", "content": "Hi"}], max_tokens=512, temperature=0.1)
        call_kwargs = provider._client.chat.completions.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 512
        assert call_kwargs["temperature"] == 0.1


# ---------------------------------------------------------------------------
# chat – tool calls
# ---------------------------------------------------------------------------


class TestChatToolCalls:
    def _make_tc(self, tc_id, name, arguments: dict):
        tc = MagicMock()
        tc.id = tc_id
        tc.function.name = name
        tc.function.arguments = json.dumps(arguments)
        return tc

    async def test_tool_calls_parsed(self, provider):
        tc = self._make_tc("call_1", "get_weather", {"location": "Beijing"})
        choice = _make_choice(content=None, tool_calls=[tc], finish_reason="tool_calls")
        response = _make_response(choice)
        provider._client.chat.completions.create = AsyncMock(return_value=response)

        result = await provider.chat(
            messages=[{"role": "user", "content": "Weather?"}],
            tools=[{"type": "function", "function": {"name": "get_weather", "description": "...", "parameters": {}}}],
        )

        assert result.has_tool_calls
        assert len(result.tool_calls) == 1
        tc_req = result.tool_calls[0]
        assert tc_req.id == "call_1"
        assert tc_req.name == "get_weather"
        assert tc_req.arguments == {"location": "Beijing"}

    async def test_tools_forwarded_to_api(self, provider):
        choice = _make_choice()
        provider._client.chat.completions.create = AsyncMock(return_value=_make_response(choice))
        tools = [{"type": "function", "function": {"name": "noop", "description": "", "parameters": {}}}]

        await provider.chat(messages=[{"role": "user", "content": "Hi"}], tools=tools)
        call_kwargs = provider._client.chat.completions.create.call_args.kwargs
        assert call_kwargs["tools"] == tools

    async def test_tools_not_sent_when_none(self, provider):
        choice = _make_choice()
        provider._client.chat.completions.create = AsyncMock(return_value=_make_response(choice))
        await provider.chat(messages=[{"role": "user", "content": "Hi"}])
        call_kwargs = provider._client.chat.completions.create.call_args.kwargs
        assert "tools" not in call_kwargs

    async def test_invalid_json_arguments_become_empty_dict(self, provider):
        tc = MagicMock()
        tc.id = "call_bad"
        tc.function.name = "broken"
        tc.function.arguments = "NOT JSON"
        choice = _make_choice(content=None, tool_calls=[tc], finish_reason="tool_calls")
        provider._client.chat.completions.create = AsyncMock(return_value=_make_response(choice))
        result = await provider.chat(messages=[{"role": "user", "content": "Hi"}])
        assert result.tool_calls[0].arguments == {}


# ---------------------------------------------------------------------------
# chat – reasoning effort
# ---------------------------------------------------------------------------


class TestChatReasoningEffort:
    async def test_reasoning_effort_enables_thinking(self, provider):
        choice = _make_choice()
        provider._client.chat.completions.create = AsyncMock(return_value=_make_response(choice))

        await provider.chat(messages=[{"role": "user", "content": "Think"}], reasoning_effort="high")
        call_kwargs = provider._client.chat.completions.create.call_args.kwargs
        assert call_kwargs.get("extra_body") == {"enable_thinking": True}

    async def test_no_extra_body_without_reasoning_effort(self, provider):
        choice = _make_choice()
        provider._client.chat.completions.create = AsyncMock(return_value=_make_response(choice))
        await provider.chat(messages=[{"role": "user", "content": "Hi"}])
        call_kwargs = provider._client.chat.completions.create.call_args.kwargs
        assert "extra_body" not in call_kwargs


# ---------------------------------------------------------------------------
# chat – reasoning_content
# ---------------------------------------------------------------------------


class TestChatReasoningContent:
    async def test_reasoning_content_extracted(self, provider):
        choice = _make_choice(content="Final answer")
        choice.message.model_extra = {"reasoning_content": "<think>step by step</think>"}
        provider._client.chat.completions.create = AsyncMock(return_value=_make_response(choice))

        result = await provider.chat(messages=[{"role": "user", "content": "Reason"}])
        assert result.reasoning_content == "<think>step by step</think>"

    async def test_no_reasoning_content_by_default(self, provider):
        choice = _make_choice()
        provider._client.chat.completions.create = AsyncMock(return_value=_make_response(choice))
        result = await provider.chat(messages=[{"role": "user", "content": "Hi"}])
        assert result.reasoning_content is None
