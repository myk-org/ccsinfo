"""Session service for managing Claude Code sessions."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pendulum

from ccsinfo.core.models.messages import Message as MessageModel
from ccsinfo.core.models.messages import MessageContent, TextContent, ToolUseContent
from ccsinfo.core.models.sessions import Session, SessionDetail, SessionSummary
from ccsinfo.core.parsers.sessions import (
    Session as ParsedSession,
)
from ccsinfo.core.parsers.sessions import (
    get_all_sessions,
    get_session_by_id,
)
from ccsinfo.utils.paths import decode_project_path

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing Claude Code sessions."""

    def list_sessions(
        self,
        project_id: str | None = None,
        active_only: bool = False,
        limit: int | None = None,
    ) -> list[SessionSummary]:
        """List sessions with optional filters.

        Args:
            project_id: Optional project ID (base64-encoded path) to filter by.
            active_only: If True, only return active sessions.
            limit: Maximum number of sessions to return.

        Returns:
            List of session summaries.
        """
        summaries: list[SessionSummary] = []

        for project_path, session in get_all_sessions():
            # Filter by project if specified
            if project_id is not None:
                try:
                    decoded = decode_project_path(project_id)
                    if project_path != decoded:
                        continue
                except Exception:
                    continue

            # Convert to summary
            summary = self._session_to_summary(session, project_path)

            # Filter active only
            if active_only and not summary.is_active:
                continue

            summaries.append(summary)

        # Sort by updated_at descending (most recent first)
        summaries.sort(
            key=lambda s: s.updated_at or pendulum.datetime(1970, 1, 1),
            reverse=True,
        )

        # Apply limit
        if limit is not None:
            summaries = summaries[:limit]

        return summaries

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID.

        Args:
            session_id: The session UUID.

        Returns:
            Session object if found, None otherwise.
        """
        parsed = get_session_by_id(session_id)
        if parsed is None:
            return None

        # Get project path from file path
        project_path = self._get_project_path_from_file(parsed.file_path)

        return Session(
            id=parsed.session_id,
            project_path=project_path,
            project_name=Path(project_path).name if project_path else "Unknown",
            created_at=parsed.first_timestamp,
            updated_at=parsed.last_timestamp,
            message_count=parsed.message_count,
            is_active=parsed.is_active(),
            file_path=parsed.file_path,
        )

    def get_session_detail(self, session_id: str) -> SessionDetail | None:
        """Get full session with messages.

        Args:
            session_id: The session UUID.

        Returns:
            SessionDetail with all messages if found, None otherwise.
        """
        parsed = get_session_by_id(session_id)
        if parsed is None:
            return None

        project_path = self._get_project_path_from_file(parsed.file_path)
        messages = self._extract_messages(parsed)

        return SessionDetail(
            id=parsed.session_id,
            project_path=project_path,
            project_name=Path(project_path).name if project_path else "Unknown",
            created_at=parsed.first_timestamp,
            updated_at=parsed.last_timestamp,
            message_count=parsed.message_count,
            is_active=parsed.is_active(),
            file_path=parsed.file_path,
            messages=messages,
        )

    def get_session_messages(
        self,
        session_id: str,
        role: str | None = None,
        limit: int | None = None,
    ) -> list[MessageModel]:
        """Get messages from a session.

        Args:
            session_id: The session UUID.
            role: Optional role filter ('user', 'assistant').
            limit: Maximum number of messages to return.

        Returns:
            List of messages from the session.
        """
        detail = self.get_session_detail(session_id)
        if detail is None:
            return []

        messages = detail.messages

        # Filter by role
        if role is not None:
            messages = [m for m in messages if m.type == role]

        # Apply limit
        if limit is not None:
            messages = messages[:limit]

        return messages

    def get_active_sessions(self) -> list[SessionSummary]:
        """Get currently active sessions.

        Returns:
            List of active session summaries.
        """
        return self.list_sessions(active_only=True)

    def get_session_tools(self, session_id: str) -> list[dict[str, Any]]:
        """Get tool calls from a session.

        Args:
            session_id: The session UUID.

        Returns:
            List of tool call dictionaries with name, id, and input.
        """
        detail = self.get_session_detail(session_id)
        if detail is None:
            return []

        tools: list[dict[str, Any]] = []
        for message in detail.messages:
            for tool_call in message.tool_calls:
                tools.append({
                    "id": tool_call.id,
                    "name": tool_call.name,
                    "input": tool_call.input,
                })

        return tools

    def _session_to_summary(
        self,
        parsed: ParsedSession,
        project_path: str,
    ) -> SessionSummary:
        """Convert a parsed session to a summary.

        Args:
            parsed: The parsed session.
            project_path: The decoded project path.

        Returns:
            SessionSummary object.
        """
        return SessionSummary(
            id=parsed.session_id,
            project_path=project_path,
            project_name=Path(project_path).name if project_path else "Unknown",
            created_at=parsed.first_timestamp,
            updated_at=parsed.last_timestamp,
            message_count=parsed.message_count,
            is_active=parsed.is_active(),
        )

    def _get_project_path_from_file(self, file_path: Path) -> str:
        """Get the project path from a session file path.

        Args:
            file_path: Path to the session file.

        Returns:
            Decoded project path.
        """
        # The parent directory name is the encoded project path
        encoded = file_path.parent.name
        try:
            return decode_project_path(encoded)
        except Exception:
            return encoded

    def _extract_messages(self, parsed: ParsedSession) -> list[MessageModel]:
        """Extract messages from a parsed session.

        Args:
            parsed: The parsed session.

        Returns:
            List of Message models.
        """
        messages: list[MessageModel] = []

        for entry in parsed.entries:
            if entry.type not in ("user", "assistant"):
                continue

            # Build content blocks
            content_blocks = []
            if entry.message and entry.message.content:
                if isinstance(entry.message.content, str):
                    content_blocks.append(TextContent(text=entry.message.content))
                elif isinstance(entry.message.content, list):
                    for content in entry.message.content:
                        if content.type == "text" and content.text:
                            content_blocks.append(TextContent(text=content.text))
                        elif content.type == "tool_use" and content.name:
                            content_blocks.append(
                                ToolUseContent(
                                    id=content.tool_use_id or "",
                                    name=content.name,
                                    input=content.input or {},
                                )
                            )

            msg = MessageModel(
                uuid=entry.uuid or "",
                parent_message_uuid=entry.parent_uuid,
                timestamp=entry.get_timestamp(),
                type=entry.type,
                message=MessageContent(
                    role=entry.type,
                    content=content_blocks,
                )
                if content_blocks
                else None,
            )
            messages.append(msg)

        return messages


# Singleton instance
session_service = SessionService()
