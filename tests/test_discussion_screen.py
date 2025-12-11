"""Tests for the DiscussionScreen."""

from datetime import datetime

import pytest

from rally_tui.app import RallyTUI
from rally_tui.models import Discussion, Ticket
from rally_tui.screens import DiscussionScreen
from rally_tui.services.mock_client import MockRallyClient


class TestDiscussionScreenBasic:
    """Basic tests for DiscussionScreen."""

    async def test_discussion_screen_shows_ticket_id(self) -> None:
        """Discussion screen should show ticket formatted ID in title."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In Progress",
            object_id="100001",
        )
        client = MockRallyClient()

        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await app.push_screen(DiscussionScreen(ticket, client))

            title = app.screen.query_one("#discussion-title")
            rendered = str(title.render())
            assert "US1234" in rendered

    async def test_discussion_screen_shows_no_discussions_message(self) -> None:
        """Discussion screen should show empty message when no discussions."""
        ticket = Ticket(
            formatted_id="US9999",
            name="No discussions",
            ticket_type="UserStory",
            state="Defined",
            object_id="999999",
        )
        client = MockRallyClient(discussions={})

        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await app.push_screen(DiscussionScreen(ticket, client))

            no_discussions = app.screen.query_one("#no-discussions")
            rendered = str(no_discussions.render())
            assert "No discussions" in rendered

    async def test_discussion_screen_shows_discussions(self) -> None:
        """Discussion screen should display discussion items."""
        ticket = Ticket(
            formatted_id="TEST123",
            name="Test ticket",
            ticket_type="UserStory",
            state="Defined",
            object_id="123456",
        )
        discussions = {
            "TEST123": [
                Discussion(
                    object_id="1",
                    text="First comment",
                    user="User One",
                    created_at=datetime(2024, 1, 15, 10, 30),
                    artifact_id="TEST123",
                ),
                Discussion(
                    object_id="2",
                    text="Second comment",
                    user="User Two",
                    created_at=datetime(2024, 1, 15, 14, 45),
                    artifact_id="TEST123",
                ),
            ]
        }
        client = MockRallyClient(discussions=discussions)

        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            await app.push_screen(DiscussionScreen(ticket, client))

            # Check that DiscussionItems are displayed
            from rally_tui.screens.discussion_screen import DiscussionItem

            items = app.screen.query(DiscussionItem)
            assert len(items) == 2


class TestDiscussionScreenNavigation:
    """Tests for DiscussionScreen navigation."""

    async def test_escape_returns_to_main_screen(self) -> None:
        """Pressing Escape should return to the main screen."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In Progress",
            object_id="100001",
        )
        client = MockRallyClient()

        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            # Push discussion screen
            app.push_screen(DiscussionScreen(ticket, client))
            await pilot.pause()

            # Verify we're on discussion screen
            assert app.screen.__class__.__name__ == "DiscussionScreen"

            # Press escape to go back
            await pilot.press("escape")
            await pilot.pause()

            # Should be back on main screen
            assert app.screen.__class__.__name__ != "DiscussionScreen"


class TestDiscussionScreenFromApp:
    """Tests for opening DiscussionScreen from the main app."""

    async def test_d_key_opens_discussion_screen(self) -> None:
        """Pressing 'd' should open the discussion screen."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            # Press 'd' to open discussions
            await pilot.press("d")
            await pilot.pause()

            # Should be on discussion screen
            assert app.screen.__class__.__name__ == "DiscussionScreen"

    async def test_d_key_shows_discussions_for_selected_ticket(self) -> None:
        """Discussion screen should show discussions for the selected ticket."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            # Press 'd' to open discussions for first ticket (US1235 - sorted by state)
            await pilot.press("d")
            await pilot.pause()

            # Verify the ticket ID in the title
            title = app.screen.query_one("#discussion-title")
            rendered = str(title.render())
            assert "US1235" in rendered

    async def test_discussion_screen_for_different_ticket(self) -> None:
        """Discussion screen should show discussions for navigated ticket."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            # Navigate to second ticket (TC101 - sorted by state)
            await pilot.press("j")
            await pilot.pause()

            # Open discussions
            await pilot.press("d")
            await pilot.pause()

            # Verify the ticket ID in the title
            title = app.screen.query_one("#discussion-title")
            rendered = str(title.render())
            assert "TC101" in rendered


class TestDiscussionScreenProperty:
    """Tests for DiscussionScreen properties."""

    def test_ticket_property(self) -> None:
        """DiscussionScreen should expose ticket property."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        client = MockRallyClient()
        screen = DiscussionScreen(ticket, client)
        assert screen.ticket == ticket
        assert screen.ticket.formatted_id == "US1234"
