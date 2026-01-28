"""Tests for Pydantic models."""

from __future__ import annotations

from datetime import UTC, date, datetime

from ccsinfo.core.models.messages import (
    Message,
    MessageContent,
    TextContent,
    ToolCall,
    ToolResult,
    ToolResultContent,
    ToolUseContent,
)
from ccsinfo.core.models.projects import Project
from ccsinfo.core.models.sessions import Session, SessionDetail, SessionSummary
from ccsinfo.core.models.stats import DailyStats, GlobalStats, ProjectStats
from ccsinfo.core.models.tasks import Task, TaskStatus


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_pending_value(self) -> None:
        """Test PENDING status value."""
        assert TaskStatus.PENDING.value == "pending"

    def test_in_progress_value(self) -> None:
        """Test IN_PROGRESS status value."""
        assert TaskStatus.IN_PROGRESS.value == "in_progress"

    def test_completed_value(self) -> None:
        """Test COMPLETED status value."""
        assert TaskStatus.COMPLETED.value == "completed"

    def test_enum_from_string(self) -> None:
        """Test creating enum from string value."""
        status = TaskStatus("pending")
        assert status == TaskStatus.PENDING


class TestTask:
    """Tests for Task model."""

    def test_task_creation_minimal(self) -> None:
        """Test creating a task with minimal fields."""
        task = Task(
            id="1",
            subject="Test",
            description="Test description",
            status=TaskStatus.PENDING,
        )
        assert task.id == "1"
        assert task.subject == "Test"
        assert task.description == "Test description"
        assert task.status == TaskStatus.PENDING

    def test_task_creation_full(self) -> None:
        """Test creating a task with all fields."""
        task = Task(
            id="1",
            subject="Test task",
            description="A comprehensive test",
            status=TaskStatus.IN_PROGRESS,
            owner="agent-1",
            blocked_by=["2", "3"],
            blocks=["4"],
            active_form="Testing",
            metadata={"key": "value"},
        )
        assert task.id == "1"
        assert task.owner == "agent-1"
        assert task.blocked_by == ["2", "3"]
        assert task.blocks == ["4"]
        assert task.active_form == "Testing"
        assert task.metadata == {"key": "value"}

    def test_task_from_json_with_aliases(self) -> None:
        """Test creating a task from JSON with camelCase aliases."""
        data = {
            "id": "1",
            "subject": "Test",
            "description": "Description",
            "status": "pending",
            "blockedBy": ["2"],
            "activeForm": "Working",
        }
        task = Task.model_validate(data)
        assert task.blocked_by == ["2"]
        assert task.active_form == "Working"

    def test_is_blocked_property_false(self) -> None:
        """Test is_blocked returns False when no blockers."""
        task = Task(
            id="1",
            subject="Test",
            description="Test",
            status=TaskStatus.PENDING,
        )
        assert task.is_blocked is False

    def test_is_blocked_property_true(self) -> None:
        """Test is_blocked returns True when has blockers."""
        task = Task(
            id="1",
            subject="Test",
            description="Test",
            status=TaskStatus.PENDING,
            blocked_by=["2"],
        )
        assert task.is_blocked is True

    def test_is_complete_property_false(self) -> None:
        """Test is_complete returns False when not completed."""
        task = Task(
            id="1",
            subject="Test",
            description="Test",
            status=TaskStatus.PENDING,
        )
        assert task.is_complete is False

    def test_is_complete_property_true(self) -> None:
        """Test is_complete returns True when completed."""
        task = Task(
            id="1",
            subject="Test",
            description="Test",
            status=TaskStatus.COMPLETED,
        )
        assert task.is_complete is True

    def test_is_complete_in_progress(self) -> None:
        """Test is_complete returns False when in progress."""
        task = Task(
            id="1",
            subject="Test",
            description="Test",
            status=TaskStatus.IN_PROGRESS,
        )
        assert task.is_complete is False


class TestSessionSummary:
    """Tests for SessionSummary model."""

    def test_session_summary_creation(self) -> None:
        """Test creating a session summary."""
        summary = SessionSummary(
            id="abc-123",
            project_path="/home/user/project",
            project_name="project",
            message_count=10,
            is_active=False,
        )
        assert summary.id == "abc-123"
        assert summary.project_path == "/home/user/project"
        assert summary.project_name == "project"
        assert summary.message_count == 10
        assert summary.is_active is False

    def test_session_summary_with_timestamps(self) -> None:
        """Test session summary with timestamps."""
        now = datetime.now(UTC)
        summary = SessionSummary(
            id="abc-123",
            project_path="/home/user/project",
            project_name="project",
            created_at=now,
            updated_at=now,
            message_count=5,
            is_active=True,
        )
        assert summary.created_at == now
        assert summary.updated_at == now
        assert summary.is_active is True

    def test_session_summary_defaults(self) -> None:
        """Test session summary default values."""
        summary = SessionSummary(
            id="abc",
            project_path="/path",
            project_name="name",
        )
        assert summary.created_at is None
        assert summary.updated_at is None
        assert summary.message_count == 0
        assert summary.is_active is False


class TestSession:
    """Tests for Session model."""

    def test_session_creation(self) -> None:
        """Test creating a session."""
        session = Session(
            id="abc-123",
            project_path="/home/user/project",
            project_name="project",
            message_count=10,
        )
        assert session.id == "abc-123"
        assert session.message_count == 10

    def test_session_to_summary(self) -> None:
        """Test converting session to summary."""
        session = Session(
            id="abc-123",
            project_path="/home/user/project",
            project_name="project",
            message_count=10,
            is_active=True,
        )
        summary = session.to_summary()
        assert isinstance(summary, SessionSummary)
        assert summary.id == session.id
        assert summary.project_path == session.project_path
        assert summary.message_count == session.message_count
        assert summary.is_active == session.is_active


class TestSessionDetail:
    """Tests for SessionDetail model."""

    def test_session_detail_creation(self) -> None:
        """Test creating a session detail."""
        detail = SessionDetail(
            id="abc-123",
            project_path="/home/user/project",
            project_name="project",
            message_count=2,
            messages=[],
        )
        assert detail.id == "abc-123"
        assert detail.messages == []

    def test_tool_call_count_empty(self) -> None:
        """Test tool_call_count with no messages."""
        detail = SessionDetail(
            id="abc",
            project_path="/path",
            project_name="name",
            messages=[],
        )
        assert detail.tool_call_count == 0

    def test_user_messages_empty(self) -> None:
        """Test user_messages with no user messages."""
        detail = SessionDetail(
            id="abc",
            project_path="/path",
            project_name="name",
            messages=[],
        )
        assert detail.user_messages == []

    def test_assistant_messages_empty(self) -> None:
        """Test assistant_messages with no assistant messages."""
        detail = SessionDetail(
            id="abc",
            project_path="/path",
            project_name="name",
            messages=[],
        )
        assert detail.assistant_messages == []


class TestProject:
    """Tests for Project model."""

    def test_project_creation(self) -> None:
        """Test creating a project."""
        project = Project(
            id="encoded-id",
            name="my-project",
            path="/home/user/my-project",
            session_count=5,
        )
        assert project.id == "encoded-id"
        assert project.name == "my-project"
        assert project.path == "/home/user/my-project"
        assert project.session_count == 5

    def test_project_defaults(self) -> None:
        """Test project default values."""
        project = Project(
            id="id",
            name="name",
            path="/path",
        )
        assert project.session_count == 0
        assert project.last_activity is None

    def test_project_with_last_activity(self) -> None:
        """Test project with last_activity set."""
        now = datetime.now(UTC)
        project = Project(
            id="id",
            name="name",
            path="/path",
            last_activity=now,
        )
        assert project.last_activity == now


class TestGlobalStats:
    """Tests for GlobalStats model."""

    def test_global_stats_creation(self) -> None:
        """Test creating global stats."""
        stats = GlobalStats(
            total_sessions=100,
            total_projects=10,
            total_messages=1000,
            total_tool_calls=500,
        )
        assert stats.total_sessions == 100
        assert stats.total_projects == 10
        assert stats.total_messages == 1000
        assert stats.total_tool_calls == 500

    def test_global_stats_defaults(self) -> None:
        """Test global stats default values."""
        stats = GlobalStats()
        assert stats.total_sessions == 0
        assert stats.total_projects == 0
        assert stats.total_messages == 0
        assert stats.total_tool_calls == 0


class TestDailyStats:
    """Tests for DailyStats model."""

    def test_daily_stats_creation(self) -> None:
        """Test creating daily stats."""
        stats = DailyStats(
            date=date(2024, 1, 15),
            session_count=5,
            message_count=50,
        )
        assert stats.date == date(2024, 1, 15)
        assert stats.session_count == 5
        assert stats.message_count == 50

    def test_daily_stats_defaults(self) -> None:
        """Test daily stats default values."""
        stats = DailyStats()
        assert stats.date is None
        assert stats.session_count == 0
        assert stats.message_count == 0


class TestProjectStats:
    """Tests for ProjectStats model."""

    def test_project_stats_creation(self) -> None:
        """Test creating project stats."""
        stats = ProjectStats(
            project_id="proj-1",
            project_name="My Project",
            session_count=10,
            message_count=100,
        )
        assert stats.project_id == "proj-1"
        assert stats.project_name == "My Project"
        assert stats.session_count == 10
        assert stats.message_count == 100


class TestTextContent:
    """Tests for TextContent model."""

    def test_text_content_creation(self) -> None:
        """Test creating text content."""
        content = TextContent(text="Hello world")
        assert content.type == "text"
        assert content.text == "Hello world"


class TestToolUseContent:
    """Tests for ToolUseContent model."""

    def test_tool_use_content_creation(self) -> None:
        """Test creating tool use content."""
        content = ToolUseContent(
            id="tool-1",
            name="read_file",
            input={"path": "/tmp/test.txt"},
        )
        assert content.type == "tool_use"
        assert content.id == "tool-1"
        assert content.name == "read_file"
        assert content.input == {"path": "/tmp/test.txt"}

    def test_tool_use_content_default_input(self) -> None:
        """Test tool use content with default empty input."""
        content = ToolUseContent(id="tool-1", name="list_files")
        assert content.input == {}


class TestToolResultContent:
    """Tests for ToolResultContent model."""

    def test_tool_result_content_creation(self) -> None:
        """Test creating tool result content."""
        content = ToolResultContent(
            tool_use_id="tool-1",
            content="File contents here",
            is_error=False,
        )
        assert content.type == "tool_result"
        assert content.tool_use_id == "tool-1"
        assert content.content == "File contents here"
        assert content.is_error is False

    def test_tool_result_content_error(self) -> None:
        """Test tool result content with error."""
        content = ToolResultContent(
            tool_use_id="tool-1",
            content="File not found",
            is_error=True,
        )
        assert content.is_error is True


class TestToolCall:
    """Tests for ToolCall model."""

    def test_tool_call_creation(self) -> None:
        """Test creating a tool call."""
        call = ToolCall(
            id="call-1",
            name="bash",
            input={"command": "ls -la"},
        )
        assert call.id == "call-1"
        assert call.name == "bash"
        assert call.input == {"command": "ls -la"}


class TestToolResult:
    """Tests for ToolResult model."""

    def test_tool_result_creation(self) -> None:
        """Test creating a tool result."""
        result = ToolResult(
            tool_use_id="call-1",
            content="output here",
            is_error=False,
        )
        assert result.tool_use_id == "call-1"
        assert result.content == "output here"
        assert result.is_error is False


class TestMessageContent:
    """Tests for MessageContent model."""

    def test_message_content_user(self) -> None:
        """Test creating user message content."""
        content = MessageContent(
            role="user",
            content=[TextContent(text="Hello")],
        )
        assert content.role == "user"
        assert len(content.content) == 1

    def test_message_content_assistant(self) -> None:
        """Test creating assistant message content."""
        content = MessageContent(
            role="assistant",
            content=[
                TextContent(text="Let me help"),
                ToolUseContent(id="t1", name="read_file", input={}),
            ],
        )
        assert content.role == "assistant"
        assert len(content.content) == 2


class TestMessage:
    """Tests for Message model."""

    def test_message_creation(self) -> None:
        """Test creating a message."""
        msg = Message(
            uuid="msg-1",
            type="user",
            message=MessageContent(
                role="user",
                content=[TextContent(text="Hello")],
            ),
        )
        assert msg.uuid == "msg-1"
        assert msg.type == "user"
        assert msg.parent_message_uuid is None

    def test_message_with_parent(self) -> None:
        """Test creating a message with parent reference."""
        msg = Message(
            uuid="msg-2",
            parent_message_uuid="msg-1",
            type="assistant",
            message=MessageContent(
                role="assistant",
                content=[TextContent(text="Hi there")],
            ),
        )
        assert msg.parent_message_uuid == "msg-1"

    def test_text_content_property(self) -> None:
        """Test text_content property extracts text."""
        msg = Message(
            uuid="msg-1",
            type="assistant",
            message=MessageContent(
                role="assistant",
                content=[
                    TextContent(text="First line"),
                    ToolUseContent(id="t1", name="tool", input={}),
                    TextContent(text="Second line"),
                ],
            ),
        )
        assert msg.text_content == "First line\nSecond line"

    def test_text_content_property_empty(self) -> None:
        """Test text_content property with no message."""
        msg = Message(uuid="msg-1", type="user", message=None)
        assert msg.text_content == ""

    def test_tool_calls_property(self) -> None:
        """Test tool_calls property extracts tool uses."""
        msg = Message(
            uuid="msg-1",
            type="assistant",
            message=MessageContent(
                role="assistant",
                content=[
                    TextContent(text="Let me run this"),
                    ToolUseContent(id="t1", name="bash", input={"command": "ls"}),
                    ToolUseContent(id="t2", name="read_file", input={"path": "/tmp"}),
                ],
            ),
        )
        calls = msg.tool_calls
        assert len(calls) == 2
        assert calls[0].name == "bash"
        assert calls[1].name == "read_file"

    def test_tool_calls_property_empty(self) -> None:
        """Test tool_calls property with no message."""
        msg = Message(uuid="msg-1", type="user", message=None)
        assert msg.tool_calls == []

    def test_tool_results_property(self) -> None:
        """Test tool_results property extracts tool results."""
        msg = Message(
            uuid="msg-1",
            type="user",
            message=MessageContent(
                role="user",
                content=[
                    ToolResultContent(tool_use_id="t1", content="output", is_error=False),
                ],
            ),
        )
        results = msg.tool_results
        assert len(results) == 1
        assert results[0].tool_use_id == "t1"

    def test_tool_results_property_empty(self) -> None:
        """Test tool_results property with no message."""
        msg = Message(uuid="msg-1", type="user", message=None)
        assert msg.tool_results == []


class TestBaseORJSONModel:
    """Tests for BaseORJSONModel configuration."""

    def test_populate_by_name(self) -> None:
        """Test that models can be populated by field name or alias."""
        task = Task.model_validate({
            "id": "1",
            "subject": "Test",
            "description": "Desc",
            "status": "pending",
            "blockedBy": ["2"],  # Using alias
        })
        assert task.blocked_by == ["2"]

        task2 = Task.model_validate({
            "id": "1",
            "subject": "Test",
            "description": "Desc",
            "status": "pending",
            "blocked_by": ["3"],  # Using field name
        })
        assert task2.blocked_by == ["3"]

    def test_use_enum_values(self) -> None:
        """Test that enum values are used in serialization."""
        task = Task(
            id="1",
            subject="Test",
            description="Desc",
            status=TaskStatus.PENDING,
        )
        data = task.model_dump()
        assert data["status"] == "pending"  # String value, not enum
