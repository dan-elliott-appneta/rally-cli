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
