"""Search service for searching across Claude Code data."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pendulum

from ccsinfo.core.models.sessions import SessionSummary
from ccsinfo.core.parsers.history import search_all_history
from ccsinfo.core.parsers.sessions import get_all_sessions

logger = logging.getLogger(__name__)


class SearchService:
    """Service for searching across Claude Code sessions, messages, and history."""

    def search_sessions(self, query: str, limit: int = 50) -> list[SessionSummary]:
        """Full-text search across sessions.

        Searches session slugs, working directories, and git branches.

        Args:
            query: The search query string.
            limit: Maximum number of results to return.

        Returns:
            List of matching session summaries.
        """
        query_lower = query.lower()
        results: list[SessionSummary] = []

        for project_path, session in get_all_sessions():
            # Search in various session fields
            searchable_fields = [
                session.session_id,
                session.slug or "",
                session.cwd or "",
                session.git_branch or "",
                project_path,
            ]

            # Check if query matches any field
            if any(query_lower in field.lower() for field in searchable_fields if field):
                summary = SessionSummary(
                    id=session.session_id,
                    project_path=project_path,
                    project_name=Path(project_path).name if project_path else "Unknown",
                    created_at=pendulum.instance(session.first_timestamp) if session.first_timestamp else None,
                    updated_at=pendulum.instance(session.last_timestamp) if session.last_timestamp else None,
                    message_count=session.message_count,
                    is_active=session.is_active(),
                )
                results.append(summary)

            if len(results) >= limit:
                break

        # Sort by relevance (sessions with query in ID first, then by date)
        results.sort(
            key=lambda s: (
                query_lower not in s.id.lower(),  # Exact ID matches first
                -(s.updated_at.timestamp() if s.updated_at else 0),  # Then by date
            )
        )

        return results[:limit]

    def search_messages(self, query: str, limit: int = 100) -> list[dict[str, Any]]:
        """Search message content across all sessions.

        Args:
            query: The search query string.
            limit: Maximum number of results to return.

        Returns:
            List of dictionaries containing session_id, message info, and matched text.
        """
        query_lower = query.lower()
        results: list[dict[str, Any]] = []

        for project_path, session in get_all_sessions():
            for entry in session.entries:
                if entry.type not in ("user", "assistant"):
                    continue

                # Extract text content to search
                text_content = ""
                if entry.message and entry.message.content:
                    if isinstance(entry.message.content, str):
                        text_content = entry.message.content
                    elif isinstance(entry.message.content, list):
                        texts = []
                        for content in entry.message.content:
                            if content.type == "text" and content.text:
                                texts.append(content.text)
                        text_content = "\n".join(texts)

                if query_lower in text_content.lower():
                    # Find the matching snippet
                    idx = text_content.lower().find(query_lower)
                    start = max(0, idx - 50)
                    end = min(len(text_content), idx + len(query) + 50)
                    snippet = text_content[start:end]
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(text_content):
                        snippet = snippet + "..."

                    entry_ts = entry.get_timestamp()
                    results.append({
                        "session_id": session.session_id,
                        "project_path": project_path,
                        "message_uuid": entry.uuid,
                        "message_type": entry.type,
                        "timestamp": entry_ts.isoformat() if entry_ts else None,
                        "snippet": snippet,
                    })

                if len(results) >= limit:
                    break

            if len(results) >= limit:
                break

        return results[:limit]

    def search_history(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """Search prompt history across all projects.

        Args:
            query: The search query string.
            limit: Maximum number of results to return.

        Returns:
            List of dictionaries containing project_path, prompt, session_id, and timestamp.
        """
        matches = search_all_history(query, case_sensitive=False)

        results: list[dict[str, Any]] = []
        for project_path, entry in matches[:limit]:
            entry_ts = entry.get_timestamp()
            results.append({
                "project_path": project_path,
                "prompt": entry.prompt,
                "session_id": entry.session_id,
                "timestamp": entry_ts.isoformat() if entry_ts else None,
            })

        return results


# Singleton instance
search_service = SearchService()
