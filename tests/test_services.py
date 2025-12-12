"""Tests for the service layer."""

from datetime import date

import pytest

from rally_tui.app import RallyTUI
from rally_tui.models import Iteration, Ticket
from rally_tui.models.sample_data import SAMPLE_TICKETS
from rally_tui.services import MockRallyClient
from rally_tui.widgets import StatusBar, TicketDetail, TicketList


class TestMockRallyClient:
    """Tests for MockRallyClient."""

    def test_default_workspace(self) -> None:
        """Default workspace should be 'My Workspace'."""
        client = MockRallyClient()
        assert client.workspace == "My Workspace"

    def test_default_project(self) -> None:
        """Default project should be 'My Project'."""
        client = MockRallyClient()
        assert client.project == "My Project"

    def test_custom_workspace(self) -> None:
        """Client should accept custom workspace."""
        client = MockRallyClient(workspace="Custom Workspace")
        assert client.workspace == "Custom Workspace"

    def test_custom_project(self) -> None:
        """Client should accept custom project."""
        client = MockRallyClient(project="Custom Project")
        assert client.project == "Custom Project"

    def test_get_tickets_returns_all(self) -> None:
        """get_tickets() without query returns all tickets."""
        client = MockRallyClient()
        tickets = client.get_tickets()
        assert len(tickets) == len(SAMPLE_TICKETS)

    def test_get_tickets_default_uses_sample_data(self) -> None:
        """Default client uses SAMPLE_TICKETS."""
        client = MockRallyClient()
        tickets = client.get_tickets()
        assert tickets[0].formatted_id == "US1234"

    def test_get_tickets_custom_data(self) -> None:
        """Client should accept custom ticket data."""
        custom_tickets = [
            Ticket(
                formatted_id="US999",
                name="Custom Ticket",
                ticket_type="UserStory",
                state="Defined",
            ),
        ]
        client = MockRallyClient(tickets=custom_tickets)
        tickets = client.get_tickets()
        assert len(tickets) == 1
        assert tickets[0].formatted_id == "US999"

    def test_get_tickets_query_filters_by_name(self) -> None:
        """get_tickets(query) filters by ticket name."""
        client = MockRallyClient()
        tickets = client.get_tickets(query="login")
        # Should match "User login feature"
        assert len(tickets) >= 1
        assert any("login" in t.name.lower() for t in tickets)

    def test_get_tickets_query_filters_by_id(self) -> None:
        """get_tickets(query) filters by formatted ID."""
        client = MockRallyClient()
        tickets = client.get_tickets(query="US1234")
        assert len(tickets) == 1
        assert tickets[0].formatted_id == "US1234"

    def test_get_tickets_query_case_insensitive(self) -> None:
        """Query filter should be case-insensitive."""
        client = MockRallyClient()
        tickets_lower = client.get_tickets(query="login")
        tickets_upper = client.get_tickets(query="LOGIN")
        assert len(tickets_lower) == len(tickets_upper)

    def test_get_tickets_query_no_match(self) -> None:
        """Query with no matches returns empty list."""
        client = MockRallyClient()
        tickets = client.get_tickets(query="nonexistent12345")
        assert tickets == []

    def test_get_ticket_found(self) -> None:
        """get_ticket() returns ticket when found."""
        client = MockRallyClient()
        ticket = client.get_ticket("US1234")
        assert ticket is not None
        assert ticket.formatted_id == "US1234"
        assert ticket.name == "User login feature"

    def test_get_ticket_not_found(self) -> None:
        """get_ticket() returns None when not found."""
        client = MockRallyClient()
        ticket = client.get_ticket("NONEXISTENT999")
        assert ticket is None

    def test_get_ticket_exact_match(self) -> None:
        """get_ticket() requires exact ID match."""
        client = MockRallyClient()
        # US123 should not match US1234
        ticket = client.get_ticket("US123")
        assert ticket is None

    def test_empty_tickets_list(self) -> None:
        """Client should handle empty ticket list."""
        client = MockRallyClient(tickets=[])
        assert client.get_tickets() == []
        assert client.get_ticket("US1234") is None

    def test_default_current_user_none(self) -> None:
        """Default current_user should be None."""
        client = MockRallyClient()
        assert client.current_user is None

    def test_default_current_iteration_none(self) -> None:
        """Default current_iteration should be None."""
        client = MockRallyClient()
        assert client.current_iteration is None

    def test_custom_current_user(self) -> None:
        """Client should accept custom current_user."""
        client = MockRallyClient(current_user="John Doe")
        assert client.current_user == "John Doe"

    def test_custom_current_iteration(self) -> None:
        """Client should accept custom current_iteration."""
        client = MockRallyClient(current_iteration="Sprint 5")
        assert client.current_iteration == "Sprint 5"


class TestMockRallyClientProtocol:
    """Tests to verify MockRallyClient implements RallyClientProtocol."""

    def test_has_workspace_property(self) -> None:
        """MockRallyClient has workspace property."""
        client = MockRallyClient()
        assert hasattr(client, "workspace")
        assert isinstance(client.workspace, str)

    def test_has_project_property(self) -> None:
        """MockRallyClient has project property."""
        client = MockRallyClient()
        assert hasattr(client, "project")
        assert isinstance(client.project, str)

    def test_has_current_user_property(self) -> None:
        """MockRallyClient has current_user property."""
        client = MockRallyClient()
        assert hasattr(client, "current_user")

    def test_has_current_iteration_property(self) -> None:
        """MockRallyClient has current_iteration property."""
        client = MockRallyClient()
        assert hasattr(client, "current_iteration")

    def test_has_get_tickets_method(self) -> None:
        """MockRallyClient has get_tickets method."""
        client = MockRallyClient()
        assert hasattr(client, "get_tickets")
        assert callable(client.get_tickets)

    def test_has_get_ticket_method(self) -> None:
        """MockRallyClient has get_ticket method."""
        client = MockRallyClient()
        assert hasattr(client, "get_ticket")
        assert callable(client.get_ticket)

    def test_get_tickets_returns_list(self) -> None:
        """get_tickets() returns a list."""
        client = MockRallyClient()
        result = client.get_tickets()
        assert isinstance(result, list)

    def test_get_tickets_returns_ticket_objects(self) -> None:
        """get_tickets() returns Ticket objects."""
        client = MockRallyClient()
        tickets = client.get_tickets()
        assert all(isinstance(t, Ticket) for t in tickets)

    def test_get_ticket_returns_ticket_or_none(self) -> None:
        """get_ticket() returns Ticket or None."""
        client = MockRallyClient()
        found = client.get_ticket("US1234")
        not_found = client.get_ticket("NONEXISTENT")
        assert isinstance(found, Ticket)
        assert not_found is None


class TestRallyTUIWithClient:
    """Tests for RallyTUI with injected client."""

    async def test_app_accepts_client(self) -> None:
        """RallyTUI should accept a client parameter."""
        client = MockRallyClient(
            tickets=[
                Ticket(
                    formatted_id="CUSTOM1",
                    name="Custom Ticket",
                    ticket_type="UserStory",
                    state="Defined",
                ),
            ],
            workspace="Custom Workspace",
            project="Custom Project",
        )
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            # Verify the app uses the injected client's data
            ticket_list = app.query_one(TicketList)
            assert ticket_list is not None

    async def test_app_shows_rally_tui_banner(self) -> None:
        """StatusBar should show rally-tui banner."""
        client = MockRallyClient(
            workspace="Injected Workspace",
            project="Injected Project",
        )
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert "rally-tui" in status_bar.display_content

    async def test_app_shows_client_project(self) -> None:
        """StatusBar should show the client's project."""
        client = MockRallyClient(
            workspace="Test Workspace",
            project="Injected Project",
        )
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert "Injected Project" in status_bar.display_content

    async def test_app_uses_client_tickets(self) -> None:
        """App should display tickets from the injected client."""
        custom_tickets = [
            Ticket(
                formatted_id="TEST001",
                name="Test Ticket One",
                ticket_type="UserStory",
                state="Defined",
            ),
            Ticket(
                formatted_id="TEST002",
                name="Test Ticket Two",
                ticket_type="Defect",
                state="Open",
            ),
        ]
        client = MockRallyClient(tickets=custom_tickets)
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            detail = app.query_one(TicketDetail)
            # First ticket should be shown in detail
            assert detail.ticket is not None
            assert detail.ticket.formatted_id == "TEST001"

    async def test_app_default_client(self) -> None:
        """App should use MockRallyClient with SAMPLE_TICKETS by default."""
        app = RallyTUI(show_splash=False)  # No client passed
        async with app.run_test() as pilot:
            detail = app.query_one(TicketDetail)
            # Should show first ticket from SAMPLE_TICKETS (sorted by state)
            # First ticket after sorting is US1235 (Defined state)
            assert detail.ticket is not None
            assert detail.ticket.formatted_id == "US1235"


class TestMockRallyClientIterations:
    """Tests for MockRallyClient iteration support."""

    def test_get_iterations_returns_list(self) -> None:
        """get_iterations() should return a list."""
        client = MockRallyClient()
        iterations = client.get_iterations()
        assert isinstance(iterations, list)

    def test_get_iterations_returns_iteration_objects(self) -> None:
        """get_iterations() should return Iteration objects."""
        client = MockRallyClient()
        iterations = client.get_iterations()
        assert all(isinstance(i, Iteration) for i in iterations)

    def test_get_iterations_default_returns_sample_iterations(self) -> None:
        """Default client should return generated sample iterations."""
        client = MockRallyClient()
        iterations = client.get_iterations()
        assert len(iterations) >= 3  # At least prev, current, next

    def test_get_iterations_sorted_by_date_descending(self) -> None:
        """Iterations should be sorted by start date (most recent first)."""
        client = MockRallyClient()
        iterations = client.get_iterations()
        # Check that dates are in descending order
        for i in range(len(iterations) - 1):
            assert iterations[i].start_date >= iterations[i + 1].start_date

    def test_get_iterations_respects_count(self) -> None:
        """get_iterations(count) should limit results."""
        client = MockRallyClient()
        iterations = client.get_iterations(count=2)
        assert len(iterations) <= 2

    def test_get_iterations_custom_iterations(self) -> None:
        """Client should accept custom iterations."""
        custom_iterations = [
            Iteration(
                object_id="1",
                name="Custom Sprint 1",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 14),
            ),
            Iteration(
                object_id="2",
                name="Custom Sprint 2",
                start_date=date(2024, 1, 15),
                end_date=date(2024, 1, 28),
            ),
        ]
        client = MockRallyClient(iterations=custom_iterations)
        iterations = client.get_iterations()
        assert len(iterations) == 2
        # Should be sorted descending
        assert iterations[0].name == "Custom Sprint 2"
        assert iterations[1].name == "Custom Sprint 1"

    def test_has_get_iterations_method(self) -> None:
        """MockRallyClient should have get_iterations method."""
        client = MockRallyClient()
        assert hasattr(client, "get_iterations")
        assert callable(client.get_iterations)


class TestMockRallyClientFeatures:
    """Tests for MockRallyClient get_feature and set_parent methods."""

    def test_get_feature_returns_tuple(self) -> None:
        """get_feature should return (formatted_id, name) tuple."""
        client = MockRallyClient()
        result = client.get_feature("F59625")
        assert result is not None
        assert result[0] == "F59625"
        assert result[1] == "API Platform Modernization Initiative"

    def test_get_feature_not_found(self) -> None:
        """get_feature should return None for unknown ID."""
        client = MockRallyClient()
        result = client.get_feature("F99999")
        assert result is None

    def test_get_feature_custom_features(self) -> None:
        """get_feature should use custom features dict."""
        custom_features = {"F111": "Custom Feature One"}
        client = MockRallyClient(features=custom_features)
        result = client.get_feature("F111")
        assert result == ("F111", "Custom Feature One")
        # Default should not be available
        assert client.get_feature("F59625") is None

    def test_set_parent_updates_ticket(self) -> None:
        """set_parent should return updated ticket with parent_id."""
        ticket = Ticket("US1234", "Test Story", "UserStory", "Defined")
        client = MockRallyClient(tickets=[ticket])

        result = client.set_parent(ticket, "F59625")

        assert result is not None
        assert result.parent_id == "F59625"
        assert result.formatted_id == "US1234"

    def test_set_parent_not_found(self) -> None:
        """set_parent should return None if ticket not in list."""
        ticket = Ticket("US9999", "Unknown Story", "UserStory", "Defined")
        client = MockRallyClient(tickets=[])

        result = client.set_parent(ticket, "F59625")

        assert result is None

    def test_set_parent_preserves_fields(self) -> None:
        """set_parent should preserve all other ticket fields."""
        ticket = Ticket(
            "US1234",
            "Test Story",
            "UserStory",
            "In Progress",
            owner="John Doe",
            description="Test description",
            notes="Test notes",
            iteration="Sprint 1",
            points=5,
            object_id="12345",
        )
        client = MockRallyClient(tickets=[ticket])

        result = client.set_parent(ticket, "F59627")

        assert result is not None
        assert result.parent_id == "F59627"
        assert result.owner == "John Doe"
        assert result.description == "Test description"
        assert result.notes == "Test notes"
        assert result.iteration == "Sprint 1"
        assert result.points == 5

    def test_has_get_feature_method(self) -> None:
        """MockRallyClient should have get_feature method."""
        client = MockRallyClient()
        assert hasattr(client, "get_feature")
        assert callable(client.get_feature)

    def test_has_set_parent_method(self) -> None:
        """MockRallyClient should have set_parent method."""
        client = MockRallyClient()
        assert hasattr(client, "set_parent")
        assert callable(client.set_parent)


class TestMockRallyClientBulkOperations:
    """Tests for MockRallyClient bulk operations."""

    def test_bulk_set_parent_updates_tickets(self) -> None:
        """bulk_set_parent should update multiple tickets."""
        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined"),
            Ticket("US2", "Story 2", "UserStory", "Defined"),
            Ticket("US3", "Story 3", "UserStory", "Defined"),
        ]
        client = MockRallyClient(tickets=tickets)

        result = client.bulk_set_parent(tickets, "F59625")

        assert result.success_count == 3
        assert result.failed_count == 0
        assert len(result.updated_tickets) == 3
        assert all(t.parent_id == "F59625" for t in result.updated_tickets)

    def test_bulk_set_parent_skips_tickets_with_parent(self) -> None:
        """bulk_set_parent should skip tickets that already have a parent."""
        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined", parent_id="F59627"),
            Ticket("US2", "Story 2", "UserStory", "Defined"),  # No parent
        ]
        client = MockRallyClient(tickets=tickets)

        result = client.bulk_set_parent(tickets, "F59625")

        # Only US2 should be updated
        assert result.success_count == 1
        assert result.failed_count == 0
        assert len(result.updated_tickets) == 1
        assert result.updated_tickets[0].formatted_id == "US2"

    def test_bulk_set_parent_all_have_parents(self) -> None:
        """bulk_set_parent should return 0 success when all have parents."""
        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined", parent_id="F111"),
            Ticket("US2", "Story 2", "UserStory", "Defined", parent_id="F222"),
        ]
        client = MockRallyClient(tickets=tickets)

        result = client.bulk_set_parent(tickets, "F59625")

        assert result.success_count == 0
        assert result.failed_count == 0
        assert len(result.updated_tickets) == 0

    def test_bulk_update_state_updates_tickets(self) -> None:
        """bulk_update_state should update multiple tickets."""
        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined"),
            Ticket("US2", "Story 2", "UserStory", "Defined"),
        ]
        client = MockRallyClient(tickets=tickets)

        result = client.bulk_update_state(tickets, "Completed")

        assert result.success_count == 2
        assert result.failed_count == 0
        assert len(result.updated_tickets) == 2
        assert all(t.state == "Completed" for t in result.updated_tickets)

    def test_bulk_update_state_preserves_other_fields(self) -> None:
        """bulk_update_state should preserve other ticket fields."""
        ticket = Ticket(
            "US1", "Story 1", "UserStory", "Defined",
            owner="John", points=5, iteration="Sprint 1"
        )
        client = MockRallyClient(tickets=[ticket])

        result = client.bulk_update_state([ticket], "In-Progress")

        updated = result.updated_tickets[0]
        assert updated.state == "In-Progress"
        assert updated.owner == "John"
        assert updated.points == 5
        assert updated.iteration == "Sprint 1"

    def test_bulk_set_iteration_updates_tickets(self) -> None:
        """bulk_set_iteration should update multiple tickets."""
        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined"),
            Ticket("US2", "Story 2", "UserStory", "Defined"),
        ]
        client = MockRallyClient(tickets=tickets)

        result = client.bulk_set_iteration(tickets, "Sprint 5")

        assert result.success_count == 2
        assert result.failed_count == 0
        assert all(t.iteration == "Sprint 5" for t in result.updated_tickets)

    def test_bulk_set_iteration_to_backlog(self) -> None:
        """bulk_set_iteration with None should move to backlog."""
        ticket = Ticket("US1", "Story 1", "UserStory", "Defined", iteration="Sprint 1")
        client = MockRallyClient(tickets=[ticket])

        result = client.bulk_set_iteration([ticket], None)

        assert result.success_count == 1
        assert result.updated_tickets[0].iteration is None

    def test_bulk_update_points_updates_tickets(self) -> None:
        """bulk_update_points should update multiple tickets."""
        tickets = [
            Ticket("US1", "Story 1", "UserStory", "Defined"),
            Ticket("US2", "Story 2", "UserStory", "Defined"),
        ]
        client = MockRallyClient(tickets=tickets)

        result = client.bulk_update_points(tickets, 5)

        assert result.success_count == 2
        assert result.failed_count == 0
        assert all(t.points == 5 for t in result.updated_tickets)

    def test_bulk_update_points_decimal_values(self) -> None:
        """bulk_update_points should handle decimal values."""
        ticket = Ticket("US1", "Story 1", "UserStory", "Defined")
        client = MockRallyClient(tickets=[ticket])

        result = client.bulk_update_points([ticket], 0.5)

        assert result.updated_tickets[0].points == 0.5

    def test_bulk_operation_not_found(self) -> None:
        """Bulk operations should handle missing tickets gracefully."""
        ticket = Ticket("US999", "Not in list", "UserStory", "Defined")
        client = MockRallyClient(tickets=[])  # Empty list

        result = client.bulk_update_state([ticket], "Completed")

        assert result.success_count == 0
        assert result.failed_count == 1
        assert len(result.errors) == 1

    def test_has_bulk_set_parent_method(self) -> None:
        """MockRallyClient should have bulk_set_parent method."""
        client = MockRallyClient()
        assert hasattr(client, "bulk_set_parent")
        assert callable(client.bulk_set_parent)

    def test_has_bulk_update_state_method(self) -> None:
        """MockRallyClient should have bulk_update_state method."""
        client = MockRallyClient()
        assert hasattr(client, "bulk_update_state")
        assert callable(client.bulk_update_state)

    def test_has_bulk_set_iteration_method(self) -> None:
        """MockRallyClient should have bulk_set_iteration method."""
        client = MockRallyClient()
        assert hasattr(client, "bulk_set_iteration")
        assert callable(client.bulk_set_iteration)

    def test_has_bulk_update_points_method(self) -> None:
        """MockRallyClient should have bulk_update_points method."""
        client = MockRallyClient()
        assert hasattr(client, "bulk_update_points")
        assert callable(client.bulk_update_points)


class TestMockRallyClientAttachments:
    """Tests for MockRallyClient attachment methods."""

    def test_get_attachments_returns_list(self) -> None:
        """get_attachments should return a list."""
        from rally_tui.models import Attachment

        client = MockRallyClient()
        ticket = client.get_ticket("US1234")
        assert ticket is not None
        attachments = client.get_attachments(ticket)
        assert isinstance(attachments, list)
        assert all(isinstance(a, Attachment) for a in attachments)

    def test_get_attachments_returns_sample_attachments(self) -> None:
        """Default client returns sample attachments for US1234."""
        client = MockRallyClient()
        ticket = client.get_ticket("US1234")
        assert ticket is not None
        attachments = client.get_attachments(ticket)
        assert len(attachments) == 2
        assert attachments[0].name == "requirements.pdf"
        assert attachments[1].name == "screenshot.png"

    def test_get_attachments_empty_for_unknown_ticket(self) -> None:
        """get_attachments returns empty list for ticket without attachments."""
        client = MockRallyClient()
        ticket = Ticket("US9999", "Unknown", "UserStory", "Defined")
        attachments = client.get_attachments(ticket)
        assert attachments == []

    def test_get_attachments_custom_attachments(self) -> None:
        """Client should accept custom attachments dict."""
        from rally_tui.models import Attachment

        custom_attachments = {
            "US1": [
                Attachment("doc.pdf", 1024, "application/pdf", "att_1"),
            ],
        }
        ticket = Ticket("US1", "Test", "UserStory", "Defined")
        client = MockRallyClient(tickets=[ticket], attachments=custom_attachments)
        attachments = client.get_attachments(ticket)
        assert len(attachments) == 1
        assert attachments[0].name == "doc.pdf"

    def test_download_attachment_returns_true_for_valid(self) -> None:
        """download_attachment returns True when attachment exists."""
        client = MockRallyClient()
        ticket = client.get_ticket("US1234")
        assert ticket is not None
        attachments = client.get_attachments(ticket)
        result = client.download_attachment(ticket, attachments[0], "/tmp/test.pdf")
        assert result is True

    def test_download_attachment_returns_false_for_invalid(self) -> None:
        """download_attachment returns False when attachment not found."""
        from rally_tui.models import Attachment

        client = MockRallyClient()
        ticket = client.get_ticket("US1234")
        assert ticket is not None
        fake_attachment = Attachment("fake.pdf", 100, "application/pdf", "invalid_id")
        result = client.download_attachment(ticket, fake_attachment, "/tmp/fake.pdf")
        assert result is False

    def test_upload_attachment_returns_attachment(self) -> None:
        """upload_attachment creates and returns new Attachment."""
        from rally_tui.models import Attachment

        client = MockRallyClient()
        ticket = client.get_ticket("US1234")
        assert ticket is not None

        result = client.upload_attachment(ticket, "/home/user/docs/report.pdf")

        assert result is not None
        assert isinstance(result, Attachment)
        assert result.name == "report.pdf"
        assert result.content_type == "application/pdf"

    def test_upload_attachment_adds_to_ticket(self) -> None:
        """upload_attachment adds the attachment to the ticket's list."""
        client = MockRallyClient()
        ticket = client.get_ticket("US1234")
        assert ticket is not None
        original_count = len(client.get_attachments(ticket))

        client.upload_attachment(ticket, "/path/to/newfile.txt")

        assert len(client.get_attachments(ticket)) == original_count + 1

    def test_upload_attachment_guesses_mime_type(self) -> None:
        """upload_attachment guesses MIME type from extension."""
        client = MockRallyClient()
        ticket = client.get_ticket("US1234")
        assert ticket is not None

        # Test various file types
        png = client.upload_attachment(ticket, "/path/image.png")
        csv = client.upload_attachment(ticket, "/path/data.csv")

        assert png is not None
        assert png.content_type == "image/png"
        assert csv is not None
        assert csv.content_type == "text/csv"

    def test_upload_attachment_unknown_type(self) -> None:
        """upload_attachment uses octet-stream for unknown types."""
        client = MockRallyClient()
        ticket = client.get_ticket("US1234")
        assert ticket is not None

        result = client.upload_attachment(ticket, "/path/file.qzx123")

        assert result is not None
        assert result.content_type == "application/octet-stream"

    def test_upload_attachment_to_new_ticket(self) -> None:
        """upload_attachment works for tickets without existing attachments."""
        client = MockRallyClient()
        ticket = Ticket("US9999", "New Ticket", "UserStory", "Defined")
        client._tickets.append(ticket)

        result = client.upload_attachment(ticket, "/path/new.pdf")

        assert result is not None
        attachments = client.get_attachments(ticket)
        assert len(attachments) == 1
        assert attachments[0].name == "new.pdf"

    def test_has_get_attachments_method(self) -> None:
        """MockRallyClient should have get_attachments method."""
        client = MockRallyClient()
        assert hasattr(client, "get_attachments")
        assert callable(client.get_attachments)

    def test_has_download_attachment_method(self) -> None:
        """MockRallyClient should have download_attachment method."""
        client = MockRallyClient()
        assert hasattr(client, "download_attachment")
        assert callable(client.download_attachment)

    def test_has_upload_attachment_method(self) -> None:
        """MockRallyClient should have upload_attachment method."""
        client = MockRallyClient()
        assert hasattr(client, "upload_attachment")
        assert callable(client.upload_attachment)
