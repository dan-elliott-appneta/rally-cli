"""Tests for the PointsScreen."""

from textual.widgets import Input

from rally_tui.app import RallyTUI
from rally_tui.models import Ticket
from rally_tui.screens import PointsScreen
from rally_tui.services.mock_client import MockRallyClient


class TestPointsScreenBasic:
    """Basic tests for PointsScreen."""

    async def test_points_screen_shows_ticket_id(self) -> None:
        """Points screen should show ticket formatted ID in title."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
        )

        app = RallyTUI(show_splash=False)
        async with app.run_test():
            await app.push_screen(PointsScreen(ticket))

            title = app.screen.query_one("#points-title")
            rendered = str(title.render())
            assert "US1234" in rendered

    async def test_points_screen_shows_current_points(self) -> None:
        """Points screen should show current points value."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
            points=5,
        )

        app = RallyTUI(show_splash=False)
        async with app.run_test():
            await app.push_screen(PointsScreen(ticket))

            current = app.screen.query_one("#points-current")
            rendered = str(current.render())
            assert "5" in rendered

    async def test_points_screen_shows_not_set_when_none(self) -> None:
        """Points screen should show 'Not set' when points is None."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
        )

        app = RallyTUI(show_splash=False)
        async with app.run_test():
            await app.push_screen(PointsScreen(ticket))

            current = app.screen.query_one("#points-current")
            rendered = str(current.render())
            assert "Not set" in rendered

    async def test_points_screen_has_input(self) -> None:
        """Points screen should have an Input widget."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
        )

        app = RallyTUI(show_splash=False)
        async with app.run_test():
            await app.push_screen(PointsScreen(ticket))

            input_widget = app.screen.query_one("#points-input", Input)
            assert input_widget is not None

    async def test_points_screen_prefills_current_value(self) -> None:
        """Points screen should pre-fill input with current points."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
            points=8,
        )

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await app.push_screen(PointsScreen(ticket))
            await pilot.pause()

            input_widget = app.screen.query_one("#points-input", Input)
            assert input_widget.value == "8"


class TestPointsScreenNavigation:
    """Tests for PointsScreen navigation."""

    async def test_escape_dismisses_screen(self) -> None:
        """Pressing Escape should dismiss the points screen."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
        )

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(PointsScreen(ticket))
            await pilot.pause()

            # Verify we're on points screen
            assert app.screen.__class__.__name__ == "PointsScreen"

            # Press escape to cancel
            await pilot.press("escape")
            await pilot.pause()

            # Should no longer be on points screen
            assert app.screen.__class__.__name__ != "PointsScreen"


class TestPointsScreenSubmission:
    """Tests for PointsScreen submission behavior."""

    async def test_enter_submits_points(self) -> None:
        """Pressing Enter should submit the points value."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
            object_id="12345",
        )

        received_points = []

        def callback(points: float | None) -> None:
            received_points.append(points)

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await app.push_screen(PointsScreen(ticket), callback=callback)

            # Type points
            input_widget = app.screen.query_one("#points-input", Input)
            input_widget.value = "13"
            await pilot.pause()

            # Submit with Enter
            await pilot.press("enter")
            await pilot.pause()

            assert len(received_points) == 1
            assert received_points[0] == 13

    async def test_enter_submits_decimal_points(self) -> None:
        """Pressing Enter should submit decimal points value."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
            object_id="12345",
        )

        received_points = []

        def callback(points: float | None) -> None:
            received_points.append(points)

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await app.push_screen(PointsScreen(ticket), callback=callback)

            # Type decimal points
            input_widget = app.screen.query_one("#points-input", Input)
            input_widget.value = "0.5"
            await pilot.pause()

            # Submit with Enter
            await pilot.press("enter")
            await pilot.pause()

            assert len(received_points) == 1
            assert received_points[0] == 0.5

    async def test_escape_returns_none(self) -> None:
        """Pressing Escape should return None."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
        )

        received_points = []

        def callback(points: float | None) -> None:
            received_points.append(points)

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(PointsScreen(ticket), callback=callback)
            await pilot.pause()

            # Cancel with Escape
            await pilot.press("escape")
            await pilot.pause()

            assert len(received_points) == 1
            assert received_points[0] is None

    async def test_empty_value_submits_zero(self) -> None:
        """Empty input should submit 0 (clear points)."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
            points=5,
        )

        received_points = []

        def callback(points: float | None) -> None:
            received_points.append(points)

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await app.push_screen(PointsScreen(ticket), callback=callback)

            # Clear the input
            input_widget = app.screen.query_one("#points-input", Input)
            input_widget.value = ""
            await pilot.pause()

            # Submit with Enter
            await pilot.press("enter")
            await pilot.pause()

            assert len(received_points) == 1
            assert received_points[0] == 0


class TestPointsScreenProperty:
    """Tests for PointsScreen properties."""

    def test_ticket_property(self) -> None:
        """PointsScreen should expose ticket property."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        screen = PointsScreen(ticket)
        assert screen.ticket == ticket
        assert screen.ticket.formatted_id == "US1234"


class TestMockClientUpdatePoints:
    """Tests for MockRallyClient.update_points method."""

    def test_update_points_returns_updated_ticket(self) -> None:
        """update_points should return ticket with new points."""
        ticket = Ticket(
            formatted_id="US1",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
            points=3,
        )
        client = MockRallyClient(tickets=[ticket])

        updated = client.update_points(ticket, 8)

        assert updated is not None
        assert updated.points == 8
        assert updated.formatted_id == "US1"

    def test_update_points_modifies_internal_list(self) -> None:
        """update_points should update ticket in client's list."""
        ticket = Ticket(
            formatted_id="US1",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
            points=3,
        )
        client = MockRallyClient(tickets=[ticket])

        client.update_points(ticket, 13)

        # Fetch the ticket again
        fetched = client.get_ticket("US1")
        assert fetched is not None
        assert fetched.points == 13

    def test_update_points_not_found(self) -> None:
        """update_points should return None for non-existent ticket."""
        ticket = Ticket(
            formatted_id="US999",
            name="Not in list",
            ticket_type="UserStory",
            state="Defined",
        )
        client = MockRallyClient(tickets=[])

        result = client.update_points(ticket, 5)

        assert result is None
