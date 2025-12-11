"""Tests for the CommentScreen."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.models import Ticket
from rally_tui.screens import CommentScreen
from rally_tui.services.mock_client import MockRallyClient
from textual.widgets import TextArea


class TestCommentScreenBasic:
    """Basic tests for CommentScreen."""

    async def test_comment_screen_shows_ticket_id(self) -> None:
        """Comment screen should show ticket formatted ID in title."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In Progress",
        )

        app = RallyTUI()
        async with app.run_test() as pilot:
            await app.push_screen(CommentScreen(ticket))

            title = app.screen.query_one("#comment-title")
            rendered = str(title.render())
            assert "US1234" in rendered

    async def test_comment_screen_shows_hint(self) -> None:
        """Comment screen should show usage hint."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In Progress",
        )

        app = RallyTUI()
        async with app.run_test() as pilot:
            await app.push_screen(CommentScreen(ticket))

            hint = app.screen.query_one("#comment-hint")
            rendered = str(hint.render())
            assert "Ctrl+S" in rendered
            assert "Escape" in rendered

    async def test_comment_screen_has_text_area(self) -> None:
        """Comment screen should have a TextArea for input."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In Progress",
        )

        app = RallyTUI()
        async with app.run_test() as pilot:
            await app.push_screen(CommentScreen(ticket))

            text_area = app.screen.query_one("#comment-input", TextArea)
            assert text_area is not None


class TestCommentScreenNavigation:
    """Tests for CommentScreen navigation."""

    async def test_escape_dismisses_screen(self) -> None:
        """Pressing Escape should dismiss the comment screen."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In Progress",
        )

        app = RallyTUI()
        async with app.run_test() as pilot:
            app.push_screen(CommentScreen(ticket))
            await pilot.pause()

            # Verify we're on comment screen
            assert app.screen.__class__.__name__ == "CommentScreen"

            # Press escape to cancel
            await pilot.press("escape")
            await pilot.pause()

            # Should no longer be on comment screen
            assert app.screen.__class__.__name__ != "CommentScreen"


class TestCommentScreenCallback:
    """Tests for CommentScreen callback behavior."""

    async def test_on_submit_called_with_text(self) -> None:
        """on_submit callback should receive the entered text."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In Progress",
        )

        received_text = []

        def on_submit(text: str | None) -> None:
            received_text.append(text)

        app = RallyTUI()
        async with app.run_test() as pilot:
            await app.push_screen(CommentScreen(ticket, on_submit=on_submit))

            # Type some text
            text_area = app.screen.query_one("#comment-input", TextArea)
            text_area.load_text("My test comment")
            await pilot.pause()

            # Submit with Ctrl+S
            await pilot.press("ctrl+s")
            await pilot.pause()

            assert len(received_text) == 1
            assert received_text[0] == "My test comment"

    async def test_on_submit_called_with_none_on_cancel(self) -> None:
        """on_submit callback should receive None when cancelled."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In Progress",
        )

        received_text = []

        def on_submit(text: str | None) -> None:
            received_text.append(text)

        app = RallyTUI()
        async with app.run_test() as pilot:
            app.push_screen(CommentScreen(ticket, on_submit=on_submit))
            await pilot.pause()

            # Cancel with Escape
            await pilot.press("escape")
            await pilot.pause()

            assert len(received_text) == 1
            assert received_text[0] is None

    async def test_empty_text_not_submitted(self) -> None:
        """Empty text should not trigger on_submit with text."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In Progress",
        )

        received_text = []

        def on_submit(text: str | None) -> None:
            received_text.append(text)

        app = RallyTUI()
        async with app.run_test() as pilot:
            app.push_screen(CommentScreen(ticket, on_submit=on_submit))
            await pilot.pause()

            # Submit without entering text
            await pilot.press("ctrl+s")
            await pilot.pause()

            # Should receive None for empty text
            assert len(received_text) == 1
            assert received_text[0] is None


class TestCommentScreenProperty:
    """Tests for CommentScreen properties."""

    def test_ticket_property(self) -> None:
        """CommentScreen should expose ticket property."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        screen = CommentScreen(ticket)
        assert screen.ticket == ticket
        assert screen.ticket.formatted_id == "US1234"
