"""Models for conversation messages."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import Field

from ccsinfo.core.models.base import BaseORJSONModel


class TextContent(BaseORJSONModel):
    """Text content block."""

    type: Literal["text"] = "text"
    text: str


class ToolUseContent(BaseORJSONModel):
    """Tool use content block."""

    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: dict[str, Any] = Field(default_factory=dict)


class ToolResultContent(BaseORJSONModel):
    """Tool result content block."""

    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str = Field(alias="tool_use_id")
    content: str | list[dict[str, Any]] = ""
    is_error: bool = False


ContentBlock = Annotated[
    TextContent | ToolUseContent | ToolResultContent,
    Field(discriminator="type"),
]


class ToolCall(BaseORJSONModel):
    """Represents a tool call made by the assistant."""

    id: str
    name: str
    input: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseORJSONModel):
    """Represents a tool result returned to the assistant."""

    tool_use_id: str
    content: str | list[dict[str, Any]] = ""
    is_error: bool = False


class MessageContent(BaseORJSONModel):
    """The inner message content with role and content blocks."""

    role: Literal["user", "assistant"]
    content: list[ContentBlock] = Field(default_factory=list)


class Message(BaseORJSONModel):
    """A conversation message in a Claude Code session."""

    uuid: str
    parent_message_uuid: str | None = Field(default=None, alias="parentMessageUuid")
    timestamp: datetime | None = None
    type: Literal["user", "assistant", "summary"]
    message: MessageContent | None = None

    @property
    def text_content(self) -> str:
        """Extract all text content from the message."""
        if not self.message:
            return ""
        texts: list[str] = []
        for block in self.message.content:
            if isinstance(block, TextContent):
                texts.append(block.text)
        return "\n".join(texts)

    @property
    def tool_calls(self) -> list[ToolCall]:
        """Extract all tool calls from the message."""
        if not self.message:
            return []
        calls: list[ToolCall] = []
        for block in self.message.content:
            if isinstance(block, ToolUseContent):
                calls.append(ToolCall(id=block.id, name=block.name, input=block.input))
        return calls

    @property
    def tool_results(self) -> list[ToolResult]:
        """Extract all tool results from the message."""
        if not self.message:
            return []
        results: list[ToolResult] = []
        for block in self.message.content:
            if isinstance(block, ToolResultContent):
                results.append(
                    ToolResult(
                        tool_use_id=block.tool_use_id,
                        content=block.content,
                        is_error=block.is_error,
                    )
                )
        return results
