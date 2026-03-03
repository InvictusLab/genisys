"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCallRequest:
    """
    A tool call request from the LLM.
    """

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """
    Response from an LLM provider.
    """

    content: str | None
    tool_calls: list[ToolCallRequest] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: dict[str, int] = field(default_factory=dict)
    reasoning_content: str | None = None  # Kimi, DeepSeek-R1 etc.
    thinking_blocks: list[dict] | None = None  # Anthropic extended thinking

    @property
    def has_tool_calls(self) -> bool:
        """
        Check if response contains tool calls.

        Returns:
            if response contains tool calls, return true. otherwise, return false.
        """
        return len(self.tool_calls) > 0


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    Implementations should handle the specifics of each provider's API while maintaining a consistent interface.
    """

    def __init__(self, api_base_url: str | None = None, api_key: str | None = None) -> None:
        """
        Args:
            api_base_url: LLM API base endpoint.
            api_key: secret key for accessing the LLM API.
        """
        self.api_base_url = api_base_url
        self.api_key = api_key

    @abstractmethod
    def get_default_model(self) -> str:
        """
        Return the default model for this provider.

        Returns:
            default model for this provider.
        """
        pass

    @abstractmethod
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
        Send a chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            tools: Optional list of tool definitions.
            model: Model identifier (provider-specific).
            max_tokens:
            temperature: Sampling temperature.
            reasoning_effort:

        Returns:
            LLMResponse with content and/or tool calls.
        """
        pass

    @staticmethod
    def _sanitize_empty_content(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Sanitize messages by removing empty content to avoid provider 400 errors.
        Empty content often results from MCP tools yielding no data.
        Most providers invalidate requests containing empty strings or text blocks.

        Args:
            messages: List of message dicts with 'role' and 'content'.

        Returns:
            List of message dicts with 'role' and 'content'(the value of content is not empty).
        """
        result: list[dict[str, Any]] = []
        for msg in messages:
            content = msg.get("content")

            if isinstance(content, str) and not content:
                clean = dict(msg)
                clean["content"] = None if (msg.get("role") == "assistant" and msg.get("tool_calls")) else "(empty)"
                result.append(clean)
                continue

            if isinstance(content, list):
                filtered = [
                    item
                    for item in content
                    if not (
                        isinstance(item, dict)
                        and item.get("type") in ("text", "input_text", "output_text")
                        and not item.get("text")
                    )
                ]
                if len(filtered) != len(content):
                    clean = dict(msg)
                    if filtered:
                        clean["content"] = filtered
                    elif msg.get("role") == "assistant" and msg.get("tool_calls"):
                        clean["content"] = None
                    else:
                        clean["content"] = "(empty)"
                    result.append(clean)
                    continue

            result.append(msg)
        return result
