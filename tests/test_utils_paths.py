"""Tests for path utilities."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from ccsinfo.utils.paths import (
    decode_project_path,
    encode_project_path,
    get_claude_base_dir,
    get_history_file,
    get_project_dir,
    get_projects_dir,
    get_tasks_dir,
    list_all_projects,
    list_session_files,
    list_task_dirs,
    list_task_files,
)


class TestEncodeProjectPath:
    """Tests for encode_project_path function."""

    def test_encode_simple_path(self) -> None:
        """Test encoding a simple project path."""
        path = "/home/user/project"
        encoded = encode_project_path(path)
        assert "/" not in encoded
        assert encoded == "-home-user-project"

    def test_encode_path_with_dots(self) -> None:
        """Test encoding a path with dots."""
        path = "/home/user/.config/project"
        encoded = encode_project_path(path)
        assert "/" not in encoded
        assert "." not in encoded
        assert encoded == "-home-user--config-project"

    def test_encode_path_with_multiple_slashes(self) -> None:
        """Test encoding a deeply nested path."""
        path = "/home/user/projects/python/myapp"
        encoded = encode_project_path(path)
        assert "/" not in encoded
        assert encoded == "-home-user-projects-python-myapp"

    def test_encode_empty_path(self) -> None:
        """Test encoding an empty path."""
        path = ""
        encoded = encode_project_path(path)
        assert encoded == ""


class TestDecodeProjectPath:
    """Tests for decode_project_path function."""

    def test_decode_simple_path(self) -> None:
        """Test decoding a simple encoded path."""
        encoded = "-home-user-project"
        decoded = decode_project_path(encoded)
        assert decoded == "/home/user/project"

    def test_decode_path_with_dots(self) -> None:
        """Test decoding a path that had dots (-- pattern)."""
        encoded = "-home-user--config-project"
        decoded = decode_project_path(encoded)
        # The -- becomes /. to restore dot-prefixed directories
        assert decoded == "/home/user/.config/project"

    def test_decode_empty_path(self) -> None:
        """Test decoding an empty string."""
        encoded = ""
        decoded = decode_project_path(encoded)
        assert decoded == ""


class TestEncodeDecode:
    """Tests for encode/decode roundtrip behavior."""

    def test_simple_roundtrip(self) -> None:
        """Test that simple paths can roundtrip (within limitations)."""
        path = "/home/user/project"
        encoded = encode_project_path(path)
        decoded = decode_project_path(encoded)
        # Simple paths without dots or dashes should roundtrip
        assert decoded == path

    def test_dotted_path_roundtrip(self) -> None:
        """Test roundtrip of paths with dots."""
        path = "/home/user/.config"
        encoded = encode_project_path(path)
        decoded = decode_project_path(encoded)
        # Paths with dots should roundtrip through the -- pattern
        assert decoded == path


class TestGetClaudeBaseDir:
    """Tests for get_claude_base_dir function."""

    def test_returns_claude_dir(self) -> None:
        """Test that it returns a path ending with .claude."""
        base_dir = get_claude_base_dir()
        assert base_dir.name == ".claude"

    def test_returns_path_in_home(self) -> None:
        """Test that it returns a path in user's home directory."""
        base_dir = get_claude_base_dir()
        assert base_dir.parent == Path.home()


class TestGetProjectsDir:
    """Tests for get_projects_dir function."""

    def test_returns_projects_dir(self) -> None:
        """Test that it returns a path ending with projects."""
        projects_dir = get_projects_dir()
        assert projects_dir.name == "projects"
        assert projects_dir.parent.name == ".claude"


class TestGetTasksDir:
    """Tests for get_tasks_dir function."""

    def test_returns_tasks_dir(self) -> None:
        """Test that it returns a path ending with tasks."""
        tasks_dir = get_tasks_dir()
        assert tasks_dir.name == "tasks"
        assert tasks_dir.parent.name == ".claude"


class TestGetProjectDir:
    """Tests for get_project_dir function."""

    def test_returns_encoded_project_path(self) -> None:
        """Test that it returns a path with encoded project name."""
        project_path = "/home/user/myproject"
        project_dir = get_project_dir(project_path)
        assert project_dir.name == "-home-user-myproject"
        assert project_dir.parent.name == "projects"


class TestListAllProjects:
    """Tests for list_all_projects function."""

    def test_empty_when_no_projects_dir(self, tmp_path: Path) -> None:
        """Test that it returns empty list when projects dir doesn't exist."""
        with patch("ccsinfo.utils.paths.get_projects_dir", return_value=tmp_path / "nonexistent"):
            projects = list_all_projects()
            assert projects == []

    def test_returns_project_directories(self, tmp_path: Path) -> None:
        """Test that it returns project directories."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Create some project directories
        (projects_dir / "project1").mkdir()
        (projects_dir / "project2").mkdir()
        # Create a file (should be ignored)
        (projects_dir / "somefile.txt").touch()

        with patch("ccsinfo.utils.paths.get_projects_dir", return_value=projects_dir):
            projects = list_all_projects()
            assert len(projects) == 2
            names = {p.name for p in projects}
            assert names == {"project1", "project2"}


class TestListSessionFiles:
    """Tests for list_session_files function."""

    def test_returns_jsonl_files(self, tmp_path: Path) -> None:
        """Test that it returns JSONL files."""
        (tmp_path / "session1.jsonl").touch()
        (tmp_path / "session2.jsonl").touch()
        (tmp_path / "other.json").touch()

        files = list_session_files(tmp_path)
        assert len(files) == 2
        names = {f.name for f in files}
        assert names == {"session1.jsonl", "session2.jsonl"}

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Test with empty directory."""
        files = list_session_files(tmp_path)
        assert files == []


class TestGetHistoryFile:
    """Tests for get_history_file function."""

    def test_returns_none_when_not_exists(self, tmp_path: Path) -> None:
        """Test that it returns None when history file doesn't exist."""
        result = get_history_file(tmp_path)
        assert result is None

    def test_returns_path_when_exists(self, tmp_path: Path) -> None:
        """Test that it returns path when history file exists."""
        history_file = tmp_path / ".history.jsonl"
        history_file.touch()

        result = get_history_file(tmp_path)
        assert result == history_file


class TestListTaskDirs:
    """Tests for list_task_dirs function."""

    def test_empty_when_no_tasks_dir(self, tmp_path: Path) -> None:
        """Test that it returns empty list when tasks dir doesn't exist."""
        with patch("ccsinfo.utils.paths.get_tasks_dir", return_value=tmp_path / "nonexistent"):
            dirs = list_task_dirs()
            assert dirs == []

    def test_returns_task_directories(self, tmp_path: Path) -> None:
        """Test that it returns task session directories."""
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()

        (tasks_dir / "session-1").mkdir()
        (tasks_dir / "session-2").mkdir()

        with patch("ccsinfo.utils.paths.get_tasks_dir", return_value=tasks_dir):
            dirs = list_task_dirs()
            assert len(dirs) == 2


class TestListTaskFiles:
    """Tests for list_task_files function."""

    def test_returns_json_files(self, tmp_path: Path) -> None:
        """Test that it returns JSON files."""
        (tmp_path / "1.json").touch()
        (tmp_path / "2.json").touch()
        (tmp_path / "other.txt").touch()

        files = list_task_files(tmp_path)
        assert len(files) == 2
        names = {f.name for f in files}
        assert names == {"1.json", "2.json"}

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Test with empty directory."""
        files = list_task_files(tmp_path)
        assert files == []
