"""Tests for QuickTicketScreen."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.screens import QuickTicketData, QuickTicketScreen
from rally_tui.services import MockRallyClient
from rally_tui.widgets import TicketList


class TestQuickTicketScreenCompose:
    """Tests for QuickTicketScreen composition."""

    async def test_screen_renders(self) -> None:
        """Screen should render without error."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(QuickTicketScreen())
            await pilot.pause()

            # Check title is present
            title = app.screen.query_one("#quick-ticket-title")
            assert "Create New Ticket" in str(title.render())

    async def test_screen_has_title_input(self) -> None:
        """Screen should have a title input field."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(QuickTicketScreen())
            await pilot.pause()

            title_input = app.screen.query_one("#title-input")
            assert title_input is not None

    async def test_screen_has_type_buttons(self) -> None:
        """Screen should have type selection buttons."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(QuickTicketScreen())
            await pilot.pause()

            btn_story = app.screen.query_one("#btn-story")
            btn_defect = app.screen.query_one("#btn-defect")
            assert btn_story is not None
            assert btn_defect is not None

    async def test_screen_has_description_input(self) -> None:
        """Screen should have a description input field."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(QuickTicketScreen())
            await pilot.pause()

            desc_input = app.screen.query_one("#description-input")
            assert desc_input is not None


class TestQuickTicketScreenTypeSelection:
    """Tests for ticket type selection."""

    async def test_default_type_is_user_story(self) -> None:
        """Default ticket type should be User Story."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            screen = QuickTicketScreen()
            app.push_screen(screen)
            await pilot.pause()

            assert screen._ticket_type == "HierarchicalRequirement"
            btn_story = app.screen.query_one("#btn-story")
            assert "-selected" in btn_story.classes

    async def test_select_defect_type(self) -> None:
        """Clicking defect button should change type."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            screen = QuickTicketScreen()
            app.push_screen(screen)
            await pilot.pause()

            # Click defect button
            btn_defect = app.screen.query_one("#btn-defect")
            await pilot.click(btn_defect)

            assert screen._ticket_type == "Defect"
            assert "-selected" in btn_defect.classes
            btn_story = app.screen.query_one("#btn-story")
            assert "-selected" not in btn_story.classes

    async def test_switch_back_to_story(self) -> None:
        """Can switch back to User Story after selecting Defect."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            screen = QuickTicketScreen()
            app.push_screen(screen)
            await pilot.pause()

            # Select defect then story
            btn_defect = app.screen.query_one("#btn-defect")
            btn_story = app.screen.query_one("#btn-story")
            await pilot.click(btn_defect)
            await pilot.click(btn_story)

            assert screen._ticket_type == "HierarchicalRequirement"
            assert "-selected" in btn_story.classes


class TestQuickTicketScreenValidation:
    """Tests for form validation."""

    async def test_empty_title_shows_error(self) -> None:
        """Submitting with empty title should show error."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            screen = QuickTicketScreen()
            app.push_screen(screen)
            await pilot.pause()

            # Try to submit without title
            await pilot.press("ctrl+s")

            error = app.screen.query_one("#quick-ticket-error")
            assert error.display is True
            assert "Title is required" in str(error.render())

    async def test_valid_submission(self) -> None:
        """Valid form should dismiss with data."""
        result = None

        def callback(data: QuickTicketData | None) -> None:
            nonlocal result
            result = data

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(QuickTicketScreen(), callback=callback)
            await pilot.pause()

            # Fill in title
            title_input = app.screen.query_one("#title-input")
            title_input.value = "Test Ticket"

            # Submit
            await pilot.press("ctrl+s")
            await pilot.pause()

            assert result is not None
            assert result.title == "Test Ticket"
            assert result.ticket_type == "HierarchicalRequirement"


class TestQuickTicketScreenCancel:
    """Tests for cancel behavior."""

    async def test_escape_cancels(self) -> None:
        """Pressing escape should cancel and return None."""
        result = "not_called"

        def callback(data: QuickTicketData | None) -> None:
            nonlocal result
            result = data

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(QuickTicketScreen(), callback=callback)
            await pilot.pause()

            # Press escape
            await pilot.press("escape")
            await pilot.pause()

            assert result is None


class TestMockClientCreateTicket:
    """Tests for MockRallyClient.create_ticket."""

    def test_create_user_story(self) -> None:
        """Should create a user story with correct type."""
        client = MockRallyClient(
            tickets=[],
            current_user="Test User",
            current_iteration="Sprint 1",
        )

        ticket = client.create_ticket(
            title="New Story",
            ticket_type="HierarchicalRequirement",
            description="Test description",
        )

        assert ticket is not None
        assert ticket.formatted_id.startswith("US")
        assert ticket.name == "New Story"
        assert ticket.ticket_type == "UserStory"
        assert ticket.owner == "Test User"
        assert ticket.iteration == "Sprint 1"
        assert ticket.description == "Test description"
        assert ticket.state == "Defined"

    def test_create_defect(self) -> None:
        """Should create a defect with correct type."""
        client = MockRallyClient(
            tickets=[],
            current_user="Test User",
            current_iteration="Sprint 1",
        )

        ticket = client.create_ticket(
            title="New Bug",
            ticket_type="Defect",
            description="Bug description",
        )

        assert ticket is not None
        assert ticket.formatted_id.startswith("DE")
        assert ticket.name == "New Bug"
        assert ticket.ticket_type == "Defect"
        assert ticket.owner == "Test User"

    def test_created_ticket_added_to_list(self) -> None:
        """Created ticket should be added to internal list."""
        client = MockRallyClient(tickets=[])

        ticket = client.create_ticket(
            title="Test",
            ticket_type="HierarchicalRequirement",
        )

        assert ticket is not None
        assert len(client.get_tickets()) == 1
        assert client.get_tickets()[0].formatted_id == ticket.formatted_id

    def test_increments_id_counter(self) -> None:
        """Should generate unique IDs for each ticket."""
        client = MockRallyClient(tickets=[])

        ticket1 = client.create_ticket("First", "HierarchicalRequirement")
        ticket2 = client.create_ticket("Second", "HierarchicalRequirement")

        assert ticket1 is not None
        assert ticket2 is not None
        assert ticket1.formatted_id != ticket2.formatted_id


class TestQuickTicketIntegration:
    """Integration tests for quick ticket creation."""

    async def test_create_ticket_adds_to_list(self) -> None:
        """Creating a ticket should add it to the ticket list."""
        client = MockRallyClient(
            tickets=[],
            current_user="Test User",
            current_iteration="Sprint 1",
        )
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            # Open quick ticket screen
            await pilot.press("w")
            await pilot.pause()

            # Fill in title
            title_input = app.screen.query_one("#title-input")
            title_input.value = "Integration Test Ticket"

            # Submit
            await pilot.press("ctrl+s")
            await pilot.pause()

            # Check ticket was added
            ticket_list = app.query_one(TicketList)
            assert ticket_list.total_count == 1
            assert ticket_list._tickets[0].name == "Integration Test Ticket"

    async def test_cancel_does_not_add_ticket(self) -> None:
        """Cancelling should not add a ticket."""
        client = MockRallyClient(tickets=[])
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            # Open quick ticket screen
            await pilot.press("w")
            await pilot.pause()

            # Cancel
            await pilot.press("escape")
            await pilot.pause()

            # Check no ticket was added
            ticket_list = app.query_one(TicketList)
            assert ticket_list.total_count == 0
