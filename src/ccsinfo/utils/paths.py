"""Claude Code path discovery utilities."""

from __future__ import annotations

from pathlib import Path


def get_claude_base_dir() -> Path:
    """Get the base Claude Code directory (~/.claude)."""
    return Path.home() / ".claude"


def get_projects_dir() -> Path:
    """Get the projects directory (~/.claude/projects)."""
    return get_claude_base_dir() / "projects"


def get_tasks_dir() -> Path:
    """Get the tasks directory (~/.claude/tasks)."""
    return get_claude_base_dir() / "tasks"


def encode_project_path(project_path: str) -> str:
    """Encode a project path to Claude Code's directory name format.

    Claude Code replaces:
    - '/' with '-'
    - '.' with '-'

    Example: '/home/user/project' -> '-home-user-project'
    """
    return project_path.replace("/", "-").replace(".", "-")


def decode_project_path(encoded_path: str) -> str:
    """Decode a Claude Code directory name back to the original path.

    Note: This is lossy - we cannot distinguish between original '-' and encoded '/' or '.'.
    The path returned should be treated as approximate.
    """
    # Handle the pattern where /. becomes --
    result = encoded_path.replace("--", "/.")
    result = result.replace("-", "/")
    return result


def get_project_dir(project_path: str) -> Path:
    """Get the Claude data directory for a project path."""
    encoded = encode_project_path(project_path)
    return get_projects_dir() / encoded


def list_all_projects() -> list[Path]:
    """List all project directories in ~/.claude/projects."""
    projects_dir = get_projects_dir()
    if not projects_dir.exists():
        return []
    return [p for p in projects_dir.iterdir() if p.is_dir()]


def list_session_files(project_dir: Path) -> list[Path]:
    """List all session JSONL files in a project directory."""
    return list(project_dir.glob("*.jsonl"))


def get_history_file(project_dir: Path) -> Path | None:
    """Get the history file for a project if it exists."""
    history_file = project_dir / ".history.jsonl"
    return history_file if history_file.exists() else None


def list_task_dirs() -> list[Path]:
    """List all task directories (one per session)."""
    tasks_dir = get_tasks_dir()
    if not tasks_dir.exists():
        return []
    return [p for p in tasks_dir.iterdir() if p.is_dir()]


def list_task_files(session_task_dir: Path) -> list[Path]:
    """List all task JSON files in a session's task directory."""
    return list(session_task_dir.glob("*.json"))
