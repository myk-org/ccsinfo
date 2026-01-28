"""Shared fixtures for ccsinfo tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def temp_claude_dir(tmp_path: Path) -> Path:
    """Create a temporary .claude directory structure."""
    claude_dir = tmp_path / ".claude"
    projects_dir = claude_dir / "projects"
    tasks_dir = claude_dir / "tasks"

    projects_dir.mkdir(parents=True)
    tasks_dir.mkdir(parents=True)

    return claude_dir


@pytest.fixture
def sample_session_data() -> list[dict[str, Any]]:
    """Sample session JSONL data."""
    return [
        {
            "type": "user",
            "uuid": "msg-001",
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": "Hello"}],
            },
            "timestamp": "2024-01-15T10:00:00Z",
        },
        {
            "type": "assistant",
            "uuid": "msg-002",
            "parentMessageUuid": "msg-001",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "Hi there!"}],
            },
            "timestamp": "2024-01-15T10:00:01Z",
        },
    ]


@pytest.fixture
def sample_task_data() -> dict[str, Any]:
    """Sample task JSON data."""
    return {
        "id": "1",
        "subject": "Test task",
        "description": "A test task",
        "status": "pending",
        "owner": None,
        "blockedBy": [],
        "blocks": [],
    }


@pytest.fixture
def sample_session_file(tmp_path: Path, sample_session_data: list[dict[str, Any]]) -> Path:
    """Create a sample session JSONL file."""
    session_file = tmp_path / "test-session.jsonl"
    with session_file.open("w") as f:
        for entry in sample_session_data:
            f.write(json.dumps(entry) + "\n")
    return session_file


@pytest.fixture
def sample_task_file(tmp_path: Path, sample_task_data: dict[str, Any]) -> Path:
    """Create a sample task JSON file."""
    task_file = tmp_path / "1.json"
    with task_file.open("w") as f:
        json.dump(sample_task_data, f)
    return task_file


@pytest.fixture
def mock_claude_dir(
    tmp_path: Path, sample_session_data: list[dict[str, Any]], sample_task_data: dict[str, Any]
) -> Path:
    """Create a fully populated mock .claude directory."""
    claude_dir = tmp_path / ".claude"

    # Create projects directory with a sample project
    projects_dir = claude_dir / "projects"
    project_dir = projects_dir / "-home-user-test-project"
    project_dir.mkdir(parents=True)

    # Create a session file in the project
    session_file = project_dir / "abc-123-def-456.jsonl"
    with session_file.open("w") as f:
        for entry in sample_session_data:
            f.write(json.dumps(entry) + "\n")

    # Create tasks directory with a session's tasks
    tasks_dir = claude_dir / "tasks"
    session_tasks_dir = tasks_dir / "abc-123-def-456"
    session_tasks_dir.mkdir(parents=True)

    # Create a task file
    task_file = session_tasks_dir / "1.json"
    with task_file.open("w") as f:
        json.dump(sample_task_data, f)

    return claude_dir
