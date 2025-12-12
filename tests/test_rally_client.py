"""Tests for RallyClient mapping and entity type detection."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from rally_tui.config import RallyConfig
from rally_tui.services.rally_client import RallyClient


class MockRallyEntity:
    """Mock pyral entity for testing."""

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


def create_mock_client() -> RallyClient:
    """Create a RallyClient with mocked Rally connection."""
    with patch("rally_tui.services.rally_client.Rally") as mock_rally:
        mock_instance = MagicMock()
        mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Test Workspace")
        mock_instance.getProject.return_value = MockRallyEntity(Name="Test Project")
        mock_rally.return_value = mock_instance

        config = RallyConfig(apikey="test_key")
        client = RallyClient(config)
        return client


class TestRallyClientEntityTypeDetection:
    """Tests for prefix-to-entity-type mapping."""

    @pytest.fixture
    def client(self) -> RallyClient:
        """Create a RallyClient for testing."""
        return create_mock_client()

    def test_user_story_prefix(self, client: RallyClient) -> None:
        """US prefix maps to HierarchicalRequirement."""
        assert client._get_entity_type("US1234") == "HierarchicalRequirement"

    def test_defect_prefix(self, client: RallyClient) -> None:
        """DE prefix maps to Defect."""
        assert client._get_entity_type("DE456") == "Defect"

    def test_task_prefix(self, client: RallyClient) -> None:
        """TA prefix maps to Task."""
        assert client._get_entity_type("TA789") == "Task"

    def test_testcase_prefix(self, client: RallyClient) -> None:
        """TC prefix maps to TestCase."""
        assert client._get_entity_type("TC101") == "TestCase"

    def test_lowercase_prefix(self, client: RallyClient) -> None:
        """Lowercase prefix is handled correctly."""
        assert client._get_entity_type("us1234") == "HierarchicalRequirement"

    def test_unknown_prefix_defaults_to_story(self, client: RallyClient) -> None:
        """Unknown prefix defaults to HierarchicalRequirement."""
        assert client._get_entity_type("XX999") == "HierarchicalRequirement"


class TestRallyClientTicketMapping:
    """Tests for entity-to-ticket mapping."""

    @pytest.fixture
    def client(self) -> RallyClient:
        """Create a RallyClient for testing."""
        return create_mock_client()

    def test_map_user_story_all_fields(self, client: RallyClient) -> None:
        """User story with all fields maps correctly."""
        entity = MockRallyEntity(
            FormattedID="US1234",
            Name="User story name",
            ScheduleState="In-Progress",
            Owner=MockRallyEntity(Name="John Doe"),
            Description="Story description",
            Iteration=MockRallyEntity(Name="Sprint 5"),
            PlanEstimate=5.0,
        )

        ticket = client._to_ticket(entity, "HierarchicalRequirement")

        assert ticket.formatted_id == "US1234"
        assert ticket.name == "User story name"
        assert ticket.ticket_type == "UserStory"
        assert ticket.state == "In-Progress"
        assert ticket.owner == "John Doe"
        assert ticket.description == "Story description"
        assert ticket.iteration == "Sprint 5"
        assert ticket.points == 5

    def test_map_defect(self, client: RallyClient) -> None:
        """Defect maps correctly."""
        entity = MockRallyEntity(
            FormattedID="DE456",
            Name="Bug name",
            State="Open",
            Owner=None,
            Description="",
            Iteration=None,
            PlanEstimate=None,
        )

        ticket = client._to_ticket(entity, "Defect")

        assert ticket.formatted_id == "DE456"
        assert ticket.ticket_type == "Defect"
        assert ticket.state == "Open"
        assert ticket.owner is None
        assert ticket.points is None

    def test_map_task(self, client: RallyClient) -> None:
        """Task maps correctly."""
        entity = MockRallyEntity(
            FormattedID="TA789",
            Name="Task name",
            ScheduleState="Completed",
            Owner=MockRallyEntity(_refObjectName="Jane Smith"),
            Description="Task details",
            Iteration=MockRallyEntity(_refObjectName="Sprint 3"),
            PlanEstimate=2.0,
        )

        ticket = client._to_ticket(entity, "Task")

        assert ticket.formatted_id == "TA789"
        assert ticket.ticket_type == "Task"
        assert ticket.state == "Completed"
        assert ticket.owner == "Jane Smith"
        assert ticket.iteration == "Sprint 3"
        assert ticket.points == 2

    def test_map_with_none_owner(self, client: RallyClient) -> None:
        """Entity with None owner maps to None."""
        entity = MockRallyEntity(
            FormattedID="US100",
            Name="Unassigned story",
            ScheduleState="Defined",
            Owner=None,
            Description="",
            Iteration=None,
            PlanEstimate=None,
        )

        ticket = client._to_ticket(entity, "HierarchicalRequirement")

        assert ticket.owner is None

    def test_map_with_none_iteration(self, client: RallyClient) -> None:
        """Entity with None iteration maps to None."""
        entity = MockRallyEntity(
            FormattedID="US100",
            Name="Unscheduled story",
            ScheduleState="Defined",
            Owner=None,
            Description="",
            Iteration=None,
            PlanEstimate=None,
        )

        ticket = client._to_ticket(entity, "HierarchicalRequirement")

        assert ticket.iteration is None

    def test_map_with_none_description(self, client: RallyClient) -> None:
        """Entity with None description maps to empty string."""
        entity = MockRallyEntity(
            FormattedID="US100",
            Name="Story without description",
            ScheduleState="Defined",
            Owner=None,
            Description=None,
            Iteration=None,
            PlanEstimate=None,
        )

        ticket = client._to_ticket(entity, "HierarchicalRequirement")

        assert ticket.description == ""

    def test_map_with_float_points(self, client: RallyClient) -> None:
        """Float points are preserved."""
        entity = MockRallyEntity(
            FormattedID="US100",
            Name="Story with points",
            ScheduleState="Defined",
            Owner=None,
            Description="",
            Iteration=None,
            PlanEstimate=3.5,
        )

        ticket = client._to_ticket(entity, "HierarchicalRequirement")

        assert ticket.points == 3.5

    def test_map_uses_schedule_state_for_stories(self, client: RallyClient) -> None:
        """Stories use ScheduleState for state."""
        entity = MockRallyEntity(
            FormattedID="US100",
            Name="Story",
            ScheduleState="Accepted",
            State="SomeOtherState",
            Owner=None,
            Description="",
            Iteration=None,
            PlanEstimate=None,
        )

        ticket = client._to_ticket(entity, "HierarchicalRequirement")

        assert ticket.state == "Accepted"

    def test_map_falls_back_to_state(self, client: RallyClient) -> None:
        """Falls back to State when ScheduleState is not set."""
        entity = MockRallyEntity(
            FormattedID="DE100",
            Name="Defect",
            State="Fixed",
            Owner=None,
            Description="",
            Iteration=None,
            PlanEstimate=None,
        )
        # Remove ScheduleState attribute
        if hasattr(entity, "ScheduleState"):
            delattr(entity, "ScheduleState")

        ticket = client._to_ticket(entity, "Defect")

        assert ticket.state == "Fixed"


class TestRallyClientConnection:
    """Tests for RallyClient connection behavior."""

    def test_workspace_from_config(self) -> None:
        """Workspace from config is used."""
        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="API Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="API Project")
            mock_instance.getUserInfo.return_value = []
            mock_instance.get.return_value = iter([])
            mock_rally.return_value = mock_instance

            config = RallyConfig(
                apikey="test_key",
                workspace="Config Workspace",
                project="Config Project",
            )
            client = RallyClient(config)

            assert client.workspace == "Config Workspace"
            assert client.project == "Config Project"

    def test_workspace_from_api_when_not_in_config(self) -> None:
        """Workspace from API is used when not in config."""
        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="API Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="API Project")
            mock_instance.getUserInfo.return_value = []
            mock_instance.get.return_value = iter([])
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            assert client.workspace == "API Workspace"
            assert client.project == "API Project"


class TestRallyClientCurrentUserAndIteration:
    """Tests for current user and iteration fetching."""

    def test_current_user_from_api(self) -> None:
        """Current user is fetched from API via User entity query."""
        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            # First get() call is for User, second for Iteration
            mock_instance.get.side_effect = [
                iter([MockRallyEntity(DisplayName="John Doe")]),  # User query
                iter([]),  # Iteration query
            ]
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            assert client.current_user == "John Doe"

    def test_current_user_none_when_not_available(self) -> None:
        """Current user is None when API returns empty."""
        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            mock_instance.get.return_value = iter([])
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            assert client.current_user is None

    def test_current_user_none_on_exception(self) -> None:
        """Current user is None when API throws exception."""
        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            mock_instance.get.side_effect = Exception("API error")
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            assert client.current_user is None

    def test_current_iteration_from_api(self) -> None:
        """Current iteration is fetched from API via Iteration entity query."""
        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            # First get() call is for User, second for Iteration
            mock_instance.get.side_effect = [
                iter([]),  # User query
                iter([MockRallyEntity(Name="Sprint 5")]),  # Iteration query
            ]
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            assert client.current_iteration == "Sprint 5"

    def test_current_iteration_none_when_not_found(self) -> None:
        """Current iteration is None when no iteration matches."""
        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            mock_instance.get.return_value = iter([])
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            assert client.current_iteration is None

    def test_current_iteration_none_on_exception(self) -> None:
        """Current iteration is None when API throws exception."""
        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            mock_instance.get.side_effect = Exception("API error")
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            assert client.current_iteration is None


class TestRallyClientDefaultQuery:
    """Tests for default query building."""

    def test_build_default_query_both_user_and_iteration(self) -> None:
        """Query includes both user and iteration when available."""
        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            # First get() call is for User, second for Iteration
            mock_instance.get.side_effect = [
                iter([MockRallyEntity(DisplayName="John Doe")]),  # User query
                iter([MockRallyEntity(Name="Sprint 5")]),  # Iteration query
            ]
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            query = client._build_default_query()
            assert query is not None
            assert 'Iteration.Name = "Sprint 5"' in query
            assert 'Owner.DisplayName = "John Doe"' in query
            assert "AND" in query
            # Rally requires format: ((condition1) AND (condition2))
            assert query.startswith("((")
            assert ") AND (" in query

    def test_build_default_query_only_iteration(self) -> None:
        """Query includes only iteration when user not available."""
        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            # First get() call is for User, second for Iteration
            mock_instance.get.side_effect = [
                iter([]),  # User query - empty
                iter([MockRallyEntity(Name="Sprint 5")]),  # Iteration query
            ]
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            query = client._build_default_query()
            assert query is not None
            assert 'Iteration.Name = "Sprint 5"' in query
            assert "Owner" not in query
            assert "AND" not in query

    def test_build_default_query_only_user(self) -> None:
        """Query includes only user when iteration not available."""
        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            # First get() call is for User, second for Iteration
            mock_instance.get.side_effect = [
                iter([MockRallyEntity(DisplayName="John Doe")]),  # User query
                iter([]),  # Iteration query - empty
            ]
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            query = client._build_default_query()
            assert query is not None
            assert 'Owner.DisplayName = "John Doe"' in query
            assert "Iteration" not in query
            assert "AND" not in query

    def test_build_default_query_none_when_neither_available(self) -> None:
        """Query is None when neither user nor iteration available."""
        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            mock_instance.get.return_value = iter([])
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            query = client._build_default_query()
            assert query is None


class TestRallyClientAttachments:
    """Tests for RallyClient attachment methods."""

    def test_get_attachments_returns_list(self) -> None:
        """get_attachments returns list of Attachment objects."""
        from rally_tui.models import Attachment, Ticket

        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            # User query, Iteration query, then attachment query
            mock_instance.get.side_effect = [
                iter([]),  # User query
                iter([]),  # Iteration query
                iter([MockRallyEntity(ObjectID="12345", Name="Test")]),  # Artifact query
            ]
            mock_instance.getAttachments.return_value = [
                MockRallyEntity(
                    Name="doc.pdf", Size=1024, ContentType="application/pdf", ObjectID="att1"
                ),
                MockRallyEntity(
                    Name="img.png", Size=2048, ContentType="image/png", ObjectID="att2"
                ),
            ]
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            ticket = Ticket("US1234", "Test", "UserStory", "Defined", object_id="12345")
            attachments = client.get_attachments(ticket)

            assert len(attachments) == 2
            assert all(isinstance(a, Attachment) for a in attachments)
            assert attachments[0].name == "doc.pdf"
            assert attachments[0].size == 1024
            assert attachments[0].content_type == "application/pdf"

    def test_get_attachments_empty_without_object_id(self) -> None:
        """get_attachments returns empty list when ticket has no object_id."""
        from rally_tui.models import Ticket

        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            mock_instance.get.return_value = iter([])
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            ticket = Ticket("US1234", "Test", "UserStory", "Defined")  # No object_id
            attachments = client.get_attachments(ticket)

            assert attachments == []

    def test_get_attachments_handles_exception(self) -> None:
        """get_attachments returns empty list on exception."""
        from rally_tui.models import Ticket

        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            mock_instance.get.side_effect = [iter([]), iter([]), Exception("API error")]
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            ticket = Ticket("US1234", "Test", "UserStory", "Defined", object_id="12345")
            attachments = client.get_attachments(ticket)

            assert attachments == []

    def test_download_attachment_writes_file(self, tmp_path: Any) -> None:
        """download_attachment writes decoded content to file."""
        import base64

        from rally_tui.models import Attachment, Ticket

        content = b"Test file content"
        encoded_content = base64.b64encode(content).decode("utf-8")

        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            # User query, Iteration query, then artifact query
            mock_instance.get.side_effect = [
                iter([]),  # User query
                iter([]),  # Iteration query
                iter([MockRallyEntity(ObjectID="12345", Name="Test")]),  # Artifact query
            ]
            mock_instance.getAttachment.return_value = MockRallyEntity(Content=encoded_content)
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            ticket = Ticket("US1234", "Test", "UserStory", "Defined", object_id="12345")
            attachment = Attachment("doc.pdf", 1024, "application/pdf", "att1")
            dest_path = str(tmp_path / "downloaded.pdf")

            result = client.download_attachment(ticket, attachment, dest_path)

            assert result is True
            with open(dest_path, "rb") as f:
                assert f.read() == content

    def test_download_attachment_returns_false_without_object_id(self) -> None:
        """download_attachment returns False when ticket has no object_id."""
        from rally_tui.models import Attachment, Ticket

        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            mock_instance.get.return_value = iter([])
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            ticket = Ticket("US1234", "Test", "UserStory", "Defined")  # No object_id
            attachment = Attachment("doc.pdf", 1024, "application/pdf", "att1")

            result = client.download_attachment(ticket, attachment, "/tmp/test.pdf")

            assert result is False

    def test_upload_attachment_returns_attachment(self, tmp_path: Any) -> None:
        """upload_attachment returns Attachment on success."""
        from rally_tui.models import Attachment, Ticket

        # Create a test file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"Test content")

        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            # User query, Iteration query, then artifact query
            mock_instance.get.side_effect = [
                iter([]),  # User query
                iter([]),  # Iteration query
                iter([MockRallyEntity(ObjectID="12345", Name="Test")]),  # Artifact query
            ]
            mock_instance.addAttachment.return_value = MockRallyEntity(ObjectID="att123")
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            ticket = Ticket("US1234", "Test", "UserStory", "Defined", object_id="12345")
            result = client.upload_attachment(ticket, str(test_file))

            assert result is not None
            assert isinstance(result, Attachment)
            assert result.name == "test.pdf"
            assert result.content_type == "application/pdf"

    def test_upload_attachment_returns_none_without_object_id(self, tmp_path: Any) -> None:
        """upload_attachment returns None when ticket has no object_id."""
        from rally_tui.models import Ticket

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"Test content")

        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            mock_instance.get.return_value = iter([])
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            ticket = Ticket("US1234", "Test", "UserStory", "Defined")  # No object_id
            result = client.upload_attachment(ticket, str(test_file))

            assert result is None

    def test_upload_attachment_returns_none_for_missing_file(self) -> None:
        """upload_attachment returns None when file doesn't exist."""
        from rally_tui.models import Ticket

        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            mock_instance.get.return_value = iter([])
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            ticket = Ticket("US1234", "Test", "UserStory", "Defined", object_id="12345")
            result = client.upload_attachment(ticket, "/nonexistent/path/file.pdf")

            assert result is None

    def test_upload_attachment_returns_none_for_large_file(self, tmp_path: Any) -> None:
        """upload_attachment returns None when file exceeds 50MB limit."""
        from rally_tui.models import Ticket

        with patch("rally_tui.services.rally_client.Rally") as mock_rally:
            mock_instance = MagicMock()
            mock_instance.getWorkspace.return_value = MockRallyEntity(Name="Workspace")
            mock_instance.getProject.return_value = MockRallyEntity(Name="Project")
            mock_instance.get.return_value = iter([])
            mock_rally.return_value = mock_instance

            config = RallyConfig(apikey="test_key")
            client = RallyClient(config)

            # Create a file larger than 50MB (use sparse file for speed)
            large_file = tmp_path / "large.zip"
            with open(large_file, "wb") as f:
                f.seek(51 * 1024 * 1024)  # 51 MB
                f.write(b"\0")

            ticket = Ticket("US1234", "Test", "UserStory", "Defined", object_id="12345")
            result = client.upload_attachment(ticket, str(large_file))

            assert result is None

    def test_has_get_attachments_method(self) -> None:
        """RallyClient should have get_attachments method."""
        client = create_mock_client()
        assert hasattr(client, "get_attachments")
        assert callable(client.get_attachments)

    def test_has_download_attachment_method(self) -> None:
        """RallyClient should have download_attachment method."""
        client = create_mock_client()
        assert hasattr(client, "download_attachment")
        assert callable(client.download_attachment)

    def test_has_upload_attachment_method(self) -> None:
        """RallyClient should have upload_attachment method."""
        client = create_mock_client()
        assert hasattr(client, "upload_attachment")
        assert callable(client.upload_attachment)
