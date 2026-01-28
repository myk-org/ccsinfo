"""Tests for parsers."""

from __future__ import annotations

import json
from pathlib import Path

import orjson
import pytest

from ccsinfo.core.models.tasks import Task
from ccsinfo.core.parsers.jsonl import (
    iter_json_files,
    iter_jsonl_files,
    parse_json,
    parse_jsonl,
)


class TestParseJson:
    """Tests for parse_json function."""

    def test_parse_simple_json(self, tmp_path: Path) -> None:
        """Test parsing a simple JSON file."""
        data = {"key": "value", "number": 42}
        file_path = tmp_path / "test.json"
        file_path.write_text(json.dumps(data))

        result = parse_json(file_path)
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_parse_nested_json(self, tmp_path: Path) -> None:
        """Test parsing nested JSON."""
        data = {
            "outer": {
                "inner": {"value": "nested"},
                "list": [1, 2, 3],
            }
        }
        file_path = tmp_path / "nested.json"
        file_path.write_text(json.dumps(data))

        result = parse_json(file_path)
        assert result["outer"]["inner"]["value"] == "nested"
        assert result["outer"]["list"] == [1, 2, 3]

    def test_parse_json_file_not_found(self, tmp_path: Path) -> None:
        """Test that FileNotFoundError is raised for missing files."""
        file_path = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError) as exc_info:
            parse_json(file_path)
        assert "JSON file not found" in str(exc_info.value)

    def test_parse_json_with_model(self, tmp_path: Path) -> None:
        """Test parsing JSON with Pydantic model validation."""
        data = {
            "id": "1",
            "subject": "Test task",
            "description": "A test task",
            "status": "pending",
            "blockedBy": [],
            "blocks": [],
        }
        file_path = tmp_path / "task.json"
        file_path.write_text(json.dumps(data))

        result = parse_json(file_path, Task)
        assert isinstance(result, Task)
        assert result.id == "1"
        assert result.subject == "Test task"

    def test_parse_empty_json_object(self, tmp_path: Path) -> None:
        """Test parsing an empty JSON object."""
        file_path = tmp_path / "empty.json"
        file_path.write_text("{}")

        result = parse_json(file_path)
        assert result == {}

    def test_parse_json_array(self, tmp_path: Path) -> None:
        """Test parsing a JSON array (returns list)."""
        data = [1, 2, 3, "four"]
        file_path = tmp_path / "array.json"
        file_path.write_text(json.dumps(data))

        result = parse_json(file_path)
        assert result == [1, 2, 3, "four"]


class TestParseJsonl:
    """Tests for parse_jsonl function."""

    def test_parse_simple_jsonl(self, tmp_path: Path) -> None:
        """Test parsing a simple JSONL file."""
        lines = [
            {"id": 1, "name": "first"},
            {"id": 2, "name": "second"},
        ]
        file_path = tmp_path / "test.jsonl"
        file_path.write_text("\n".join(json.dumps(line) for line in lines))

        results = list(parse_jsonl(file_path))
        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[1]["name"] == "second"

    def test_parse_jsonl_skips_empty_lines(self, tmp_path: Path) -> None:
        """Test that empty lines are skipped."""
        content = '{"a": 1}\n\n{"b": 2}\n'
        file_path = tmp_path / "test.jsonl"
        file_path.write_text(content)

        results = list(parse_jsonl(file_path))
        assert len(results) == 2

    def test_parse_jsonl_skips_whitespace_lines(self, tmp_path: Path) -> None:
        """Test that whitespace-only lines are skipped."""
        content = '{"a": 1}\n   \n\t\n{"b": 2}'
        file_path = tmp_path / "test.jsonl"
        file_path.write_text(content)

        results = list(parse_jsonl(file_path))
        assert len(results) == 2

    def test_parse_jsonl_file_not_found(self, tmp_path: Path) -> None:
        """Test that FileNotFoundError is raised for missing files."""
        file_path = tmp_path / "nonexistent.jsonl"

        with pytest.raises(FileNotFoundError) as exc_info:
            list(parse_jsonl(file_path))
        assert "JSONL file not found" in str(exc_info.value)

    def test_parse_jsonl_skip_malformed_default(self, tmp_path: Path) -> None:
        """Test that malformed lines are skipped by default."""
        content = '{"a": 1}\nnot json\n{"b": 2}'
        file_path = tmp_path / "test.jsonl"
        file_path.write_text(content)

        results = list(parse_jsonl(file_path))
        assert len(results) == 2
        assert results[0]["a"] == 1
        assert results[1]["b"] == 2

    def test_parse_jsonl_raise_on_malformed(self, tmp_path: Path) -> None:
        """Test that malformed lines raise when skip_malformed=False."""
        content = '{"a": 1}\nnot json\n{"b": 2}'
        file_path = tmp_path / "test.jsonl"
        file_path.write_text(content)

        with pytest.raises(orjson.JSONDecodeError):
            list(parse_jsonl(file_path, skip_malformed=False))

    def test_parse_jsonl_with_model(self, tmp_path: Path) -> None:
        """Test parsing JSONL with Pydantic model validation."""
        lines = [
            {"id": "1", "subject": "Task 1", "description": "First", "status": "pending"},
            {"id": "2", "subject": "Task 2", "description": "Second", "status": "completed"},
        ]
        file_path = tmp_path / "tasks.jsonl"
        file_path.write_text("\n".join(json.dumps(line) for line in lines))

        results = list(parse_jsonl(file_path, Task))
        assert len(results) == 2
        assert all(isinstance(r, Task) for r in results)
        task0 = results[0]
        task1 = results[1]
        assert isinstance(task0, Task)
        assert isinstance(task1, Task)
        assert task0.subject == "Task 1"
        assert task1.subject == "Task 2"

    def test_parse_jsonl_skip_invalid_model_data(self, tmp_path: Path) -> None:
        """Test that invalid model data is skipped by default."""
        lines = [
            {"id": "1", "subject": "Valid", "description": "OK", "status": "pending"},
            {"invalid": "data"},  # Missing required fields
            {"id": "2", "subject": "Also valid", "description": "OK", "status": "pending"},
        ]
        file_path = tmp_path / "tasks.jsonl"
        file_path.write_text("\n".join(json.dumps(line) for line in lines))

        results = list(parse_jsonl(file_path, Task))
        assert len(results) == 2

    def test_parse_empty_jsonl(self, tmp_path: Path) -> None:
        """Test parsing an empty JSONL file."""
        file_path = tmp_path / "empty.jsonl"
        file_path.write_text("")

        results = list(parse_jsonl(file_path))
        assert results == []

    def test_parse_jsonl_trailing_newline(self, tmp_path: Path) -> None:
        """Test that trailing newlines don't cause issues."""
        content = '{"a": 1}\n{"b": 2}\n\n\n'
        file_path = tmp_path / "test.jsonl"
        file_path.write_text(content)

        results = list(parse_jsonl(file_path))
        assert len(results) == 2


class TestIterJsonlFiles:
    """Tests for iter_jsonl_files function."""

    def test_iter_jsonl_files_returns_sorted(self, tmp_path: Path) -> None:
        """Test that JSONL files are returned sorted."""
        (tmp_path / "z.jsonl").touch()
        (tmp_path / "a.jsonl").touch()
        (tmp_path / "m.jsonl").touch()

        files = list(iter_jsonl_files(tmp_path))
        names = [f.name for f in files]
        assert names == ["a.jsonl", "m.jsonl", "z.jsonl"]

    def test_iter_jsonl_files_filters_by_extension(self, tmp_path: Path) -> None:
        """Test that only JSONL files are returned."""
        (tmp_path / "data.jsonl").touch()
        (tmp_path / "data.json").touch()
        (tmp_path / "data.txt").touch()

        files = list(iter_jsonl_files(tmp_path))
        assert len(files) == 1
        assert files[0].name == "data.jsonl"

    def test_iter_jsonl_files_empty_dir(self, tmp_path: Path) -> None:
        """Test with empty directory."""
        files = list(iter_jsonl_files(tmp_path))
        assert files == []

    def test_iter_jsonl_files_nonexistent_dir(self, tmp_path: Path) -> None:
        """Test with nonexistent directory."""
        files = list(iter_jsonl_files(tmp_path / "nonexistent"))
        assert files == []

    def test_iter_jsonl_files_custom_pattern(self, tmp_path: Path) -> None:
        """Test with custom glob pattern."""
        (tmp_path / "session.jsonl").touch()
        (tmp_path / "history.jsonl").touch()

        files = list(iter_jsonl_files(tmp_path, pattern="session*.jsonl"))
        assert len(files) == 1
        assert files[0].name == "session.jsonl"


class TestIterJsonFiles:
    """Tests for iter_json_files function."""

    def test_iter_json_files_returns_sorted(self, tmp_path: Path) -> None:
        """Test that JSON files are returned sorted."""
        (tmp_path / "3.json").touch()
        (tmp_path / "1.json").touch()
        (tmp_path / "2.json").touch()

        files = list(iter_json_files(tmp_path))
        names = [f.name for f in files]
        assert names == ["1.json", "2.json", "3.json"]

    def test_iter_json_files_filters_by_extension(self, tmp_path: Path) -> None:
        """Test that only JSON files are returned."""
        (tmp_path / "task.json").touch()
        (tmp_path / "data.jsonl").touch()
        (tmp_path / "readme.txt").touch()

        files = list(iter_json_files(tmp_path))
        assert len(files) == 1
        assert files[0].name == "task.json"

    def test_iter_json_files_empty_dir(self, tmp_path: Path) -> None:
        """Test with empty directory."""
        files = list(iter_json_files(tmp_path))
        assert files == []

    def test_iter_json_files_nonexistent_dir(self, tmp_path: Path) -> None:
        """Test with nonexistent directory."""
        files = list(iter_json_files(tmp_path / "nonexistent"))
        assert files == []


class TestParserIntegration:
    """Integration tests for parser functions."""

    def test_parse_session_jsonl_format(self, sample_session_file: Path) -> None:
        """Test parsing a session file in the expected format."""
        results = list(parse_jsonl(sample_session_file))
        assert len(results) == 2

        # Check user message
        user_msg = results[0]
        assert user_msg["type"] == "user"
        assert user_msg["uuid"] == "msg-001"
        assert user_msg["message"]["content"][0]["text"] == "Hello"

        # Check assistant message
        assistant_msg = results[1]
        assert assistant_msg["type"] == "assistant"
        assert assistant_msg["uuid"] == "msg-002"
        assert assistant_msg["parentMessageUuid"] == "msg-001"

    def test_parse_task_json_format(self, sample_task_file: Path) -> None:
        """Test parsing a task file in the expected format."""
        result = parse_json(sample_task_file, Task)
        assert isinstance(result, Task)
        assert result.id == "1"
        assert result.subject == "Test task"
        assert result.description == "A test task"
        assert result.status == "pending"
