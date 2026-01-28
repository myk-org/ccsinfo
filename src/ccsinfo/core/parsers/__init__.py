"""Parser modules for Claude Code session data.

This module provides parsers for:
- JSONL/JSON files (generic utilities)
- Session files (conversation history)
- Task files (task management)
- History files (prompt history)
"""

from ccsinfo.core.parsers.history import (
    HistoryEntry,
    PromptHistory,
    get_all_history,
    get_history_file,
    get_history_summary,
    get_project_history,
    parse_history_file,
    search_all_history,
)
from ccsinfo.core.parsers.jsonl import (
    iter_json_files,
    iter_jsonl_files,
    parse_json,
    parse_jsonl,
)
from ccsinfo.core.parsers.sessions import (
    Message,
    MessageContent,
    Session,
    SessionEntry,
    get_all_projects,
    get_all_sessions,
    get_project_sessions,
    get_projects_directory,
    get_session_by_id,
    get_session_summary,
    is_session_active,
    parse_session_file,
)
from ccsinfo.core.parsers.tasks import (
    Task,
    TaskCollection,
    get_session_ids_with_tasks,
    get_tasks_directory,
    iter_all_session_tasks,
    parse_session_tasks,
    parse_task_file,
)
from ccsinfo.utils.paths import decode_project_path, encode_project_path

__all__ = [
    # History parser
    "HistoryEntry",
    # Session parser
    "Message",
    "MessageContent",
    "PromptHistory",
    "Session",
    "SessionEntry",
    # Task parser
    "Task",
    "TaskCollection",
    "decode_project_path",
    "encode_project_path",
    "get_all_history",
    "get_all_projects",
    "get_all_sessions",
    "get_history_file",
    "get_history_summary",
    "get_project_history",
    "get_project_sessions",
    "get_projects_directory",
    "get_session_by_id",
    "get_session_ids_with_tasks",
    "get_session_summary",
    "get_tasks_directory",
    "is_session_active",
    "iter_all_session_tasks",
    # JSONL/JSON utilities
    "iter_json_files",
    "iter_jsonl_files",
    "parse_history_file",
    "parse_json",
    "parse_jsonl",
    "parse_session_file",
    "parse_session_tasks",
    "parse_task_file",
    "search_all_history",
]
