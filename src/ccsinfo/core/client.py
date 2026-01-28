"""HTTP client for remote server mode."""

from __future__ import annotations

from typing import Any, cast

import httpx


class CCSInfoClient:
    """Client for ccsinfo REST API."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=30.0)

    def _get_list(self, path: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        response = self._client.get(path, params=params)
        response.raise_for_status()
        return cast("list[dict[str, Any]]", response.json())

    def _get_dict(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self._client.get(path, params=params)
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    # Sessions
    def list_sessions(
        self,
        project_id: str | None = None,
        active_only: bool = False,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit, "active_only": active_only}
        if project_id:
            params["project_id"] = project_id
        return self._get_list("/sessions", params)

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self._get_dict(f"/sessions/{session_id}")

    def get_session_messages(
        self,
        session_id: str,
        role: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if role:
            params["role"] = role
        return self._get_list(f"/sessions/{session_id}/messages", params)

    def get_session_tools(self, session_id: str) -> list[dict[str, Any]]:
        return self._get_list(f"/sessions/{session_id}/tools")

    def get_active_sessions(self) -> list[dict[str, Any]]:
        return self._get_list("/sessions/active")

    # Projects
    def list_projects(self) -> list[dict[str, Any]]:
        return self._get_list("/projects")

    def get_project(self, project_id: str) -> dict[str, Any]:
        return self._get_dict(f"/projects/{project_id}")

    def get_project_stats(self, project_id: str) -> dict[str, Any]:
        return self._get_dict(f"/projects/{project_id}/stats")

    # Tasks
    def list_tasks(
        self,
        session_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if session_id:
            params["session_id"] = session_id
        if status:
            params["status"] = status
        return self._get_list("/tasks", params)

    def get_task(self, task_id: str, session_id: str) -> dict[str, Any]:
        return self._get_dict(f"/tasks/{task_id}", {"session_id": session_id})

    def get_pending_tasks(self) -> list[dict[str, Any]]:
        return self._get_list("/tasks/pending")

    # Stats
    def get_global_stats(self) -> dict[str, Any]:
        return self._get_dict("/stats")

    def get_daily_stats(self, days: int = 30) -> list[dict[str, Any]]:
        return self._get_list("/stats/daily", {"days": days})

    def get_trends(self) -> dict[str, Any]:
        return self._get_dict("/stats/trends")

    # Search
    def search_sessions(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        return self._get_list("/search", {"q": query, "limit": limit})

    def search_messages(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        return self._get_list("/search/messages", {"q": query, "limit": limit})

    def search_history(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        return self._get_list("/search/history", {"q": query, "limit": limit})

    # Health
    def health(self) -> dict[str, Any]:
        return self._get_dict("/health")

    def info(self) -> dict[str, Any]:
        return self._get_dict("/info")


def get_client(server_url: str | None) -> CCSInfoClient | None:
    """Get client if server URL is set."""
    if server_url:
        return CCSInfoClient(server_url)
    return None
