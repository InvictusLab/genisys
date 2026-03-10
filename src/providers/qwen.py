"""Qwen LLM provider using Alibaba Bailian's OpenAI-compatible API."""

import json
import os
from typing import Any

from openai import AsyncOpenAI

from providers.base import LLMProvider, LLMResponse, ToolCallRequest

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"


class QwenProvider(LLMProvider):
    """
    LLM provider for Alibaba's Qianwen (Qwen) models via the Bailian platform.

    Uses the OpenAI-compatible API endpoint. Requires a DashScope API key,
    which can be set via the ``QWEN_API_KEY`` environment variable.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        """
        Args:
            api_key: DashScope API key. Falls back to ``QWEN_API_KEY`` env var.
            base_url: Override the default Bailian endpoint.
        """
        resolved_key = api_key or os.environ.get("QWEN_API_KEY", "")
        resolved_url = base_url or DEFAULT_BASE_URL
        super().__init__(base_url=resolved_url, api_key=resolved_key)
        self._client = AsyncOpenAI(api_key=resolved_key, base_url=resolved_url)

    def get_default_model(self) -> str:
        """Return the default Qwen model identifier."""
        return DEFAULT_MODEL

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        reasoning_effort: str | None = None,
    ) -> LLMResponse:
        """
        Send a chat completion request to Qwen via the OpenAI-compatible endpoint.

        Args:
            messages: Conversation history as role/content dicts.
            tools: Optional tool definitions in OpenAI function-calling format.
            model: Model identifier; defaults to ``qwen-plus``.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature in [0, 2).
            reasoning_effort: When set, enables the model's internal thinking/reasoning
                mode (supported by QwQ and Qwen3 thinking variants).

        Returns:
            LLMResponse containing the assistant reply and any tool call requests.
        """
        sanitized = self._sanitize_empty_content(messages)
        kwargs: dict[str, Any] = {
            "model": model or self.get_default_model(),
            "messages": sanitized,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if tools:
            kwargs["tools"] = tools

        if reasoning_effort is not None:
            # Qwen thinking models accept enable_thinking via extra_body.
            kwargs["extra_body"] = {"enable_thinking": True}

        response = await self._client.chat.completions.create(**kwargs)

        choice = response.choices[0]
        message = choice.message
        finish_reason = choice.finish_reason or "stop"

        # Parse tool calls
        tool_calls: list[ToolCallRequest] = []
        if message.tool_calls:
            for tc in message.tool_calls:
                try:
                    arguments = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    arguments = {}
                tool_calls.append(
                    ToolCallRequest(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=arguments,
                    )
                )

        # Usage statistics
        usage: dict[str, int] = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        # Thinking content (QwQ / Qwen3-thinking models expose reasoning_content)
        reasoning_content: str | None = None
        raw_message = message.model_extra or {}
        if "reasoning_content" in raw_message:
            reasoning_content = raw_message["reasoning_content"]

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage,
            reasoning_content=reasoning_content,
        )
