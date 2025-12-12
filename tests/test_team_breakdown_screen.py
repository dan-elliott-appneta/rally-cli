"""Tests for the TeamBreakdownScreen."""

import pytest

from rally_tui.models import Ticket
from rally_tui.screens.team_breakdown_screen import OwnerStats, TeamBreakdownScreen


class TestOwnerStats:
    """Tests for OwnerStats dataclass."""

    def test_avg_points_with_tickets(self) -> None:
        """Average points calculated correctly."""
        stats = OwnerStats(owner="Alice", ticket_count=4, total_points=20.0)
        assert stats.avg_points == 5.0

    def test_avg_points_zero_tickets(self) -> None:
        """Average points is 0 when no tickets."""
        stats = OwnerStats(owner="Bob", ticket_count=0, total_points=0.0)
        assert stats.avg_points == 0.0

    def test_avg_points_fractional(self) -> None:
        """Average points handles fractional values."""
        stats = OwnerStats(owner="Charlie", ticket_count=3, total_points=10.0)
        assert stats.avg_points == pytest.approx(3.33, rel=0.01)


class TestTeamBreakdownScreen:
    """Tests for TeamBreakdownScreen."""

    def _create_ticket(
        self,
        formatted_id: str,
        owner: str | None = None,
        points: float | None = None,
    ) -> Ticket:
        """Create a test ticket."""
        return Ticket(
            formatted_id=formatted_id,
            name=f"Test {formatted_id}",
            ticket_type="UserStory",
            state="In Progress",
            owner=owner,
            description="Test description",
            points=points,
        )

    def test_calculate_stats_single_owner(self) -> None:
        """Stats calculated correctly for single owner."""
        tickets = [
            self._create_ticket("US1", owner="Alice", points=3),
            self._create_ticket("US2", owner="Alice", points=5),
        ]
        screen = TeamBreakdownScreen(tickets, "Sprint 1")

        assert len(screen.stats) == 1
        assert screen.stats[0].owner == "Alice"
        assert screen.stats[0].ticket_count == 2
        assert screen.stats[0].total_points == 8.0

    def test_calculate_stats_multiple_owners(self) -> None:
        """Stats calculated correctly for multiple owners."""
        tickets = [
            self._create_ticket("US1", owner="Alice", points=3),
            self._create_ticket("US2", owner="Bob", points=5),
            self._create_ticket("US3", owner="Alice", points=2),
        ]
        screen = TeamBreakdownScreen(tickets, "Sprint 1")

        assert len(screen.stats) == 2
        # Should be sorted by points descending
        assert screen.stats[0].owner == "Alice"
        assert screen.stats[0].ticket_count == 2
        assert screen.stats[0].total_points == 5.0

        assert screen.stats[1].owner == "Bob"
        assert screen.stats[1].ticket_count == 1
        assert screen.stats[1].total_points == 5.0

    def test_calculate_stats_unassigned(self) -> None:
        """Unassigned tickets grouped correctly."""
        tickets = [
            self._create_ticket("US1", owner=None, points=3),
            self._create_ticket("US2", owner="Alice", points=5),
        ]
        screen = TeamBreakdownScreen(tickets, "Sprint 1")

        assert len(screen.stats) == 2
        owners = [s.owner for s in screen.stats]
        assert "Unassigned" in owners
        assert "Alice" in owners

    def test_calculate_stats_no_points(self) -> None:
        """Tickets without points handled correctly."""
        tickets = [
            self._create_ticket("US1", owner="Alice", points=None),
            self._create_ticket("US2", owner="Alice", points=5),
        ]
        screen = TeamBreakdownScreen(tickets, "Sprint 1")

        assert len(screen.stats) == 1
        assert screen.stats[0].ticket_count == 2
        assert screen.stats[0].total_points == 5.0

    def test_total_tickets(self) -> None:
        """Total ticket count is correct."""
        tickets = [
            self._create_ticket("US1", owner="Alice", points=3),
            self._create_ticket("US2", owner="Bob", points=5),
            self._create_ticket("US3", owner="Charlie", points=2),
        ]
        screen = TeamBreakdownScreen(tickets, "Sprint 1")

        assert screen.total_tickets == 3

    def test_total_points(self) -> None:
        """Total points is correct."""
        tickets = [
            self._create_ticket("US1", owner="Alice", points=3),
            self._create_ticket("US2", owner="Bob", points=5),
            self._create_ticket("US3", owner="Charlie", points=None),
        ]
        screen = TeamBreakdownScreen(tickets, "Sprint 1")

        assert screen.total_points == 8.0

    def test_empty_tickets(self) -> None:
        """Empty ticket list handled correctly."""
        screen = TeamBreakdownScreen([], "Sprint 1")

        assert len(screen.stats) == 0
        assert screen.total_tickets == 0
        assert screen.total_points == 0.0

    def test_sorting_by_points_then_count(self) -> None:
        """Stats sorted by points descending, then ticket count."""
        tickets = [
            self._create_ticket("US1", owner="Alice", points=5),
            self._create_ticket("US2", owner="Bob", points=10),
            self._create_ticket("US3", owner="Charlie", points=5),
            self._create_ticket("US4", owner="Charlie", points=0),  # 2 tickets, 5 points
        ]
        screen = TeamBreakdownScreen(tickets, "Sprint 1")

        # Bob: 10 points, Alice: 5 points (1 ticket), Charlie: 5 points (2 tickets)
        assert screen.stats[0].owner == "Bob"
        assert screen.stats[1].owner == "Charlie"  # Same points but more tickets
        assert screen.stats[2].owner == "Alice"


class TestTeamBreakdownScreenWidget:
    """Widget tests for TeamBreakdownScreen."""

    def _create_ticket(
        self,
        formatted_id: str,
        owner: str | None = None,
        points: float | None = None,
    ) -> Ticket:
        """Create a test ticket."""
        return Ticket(
            formatted_id=formatted_id,
            name=f"Test {formatted_id}",
            ticket_type="UserStory",
            state="In Progress",
            owner=owner,
            description="Test description",
            points=points,
        )

    async def test_screen_renders(self) -> None:
        """Screen renders without errors."""
        from textual.app import App, ComposeResult

        tickets = [
            self._create_ticket("US1", owner="Alice", points=3),
            self._create_ticket("US2", owner="Bob", points=5),
        ]

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield from ()

        app = TestApp()
        async with app.run_test() as pilot:
            screen = TeamBreakdownScreen(tickets, "Sprint 1")
            await app.push_screen(screen)
            await pilot.pause()

            # Check that key elements exist (query from screen, not app)
            assert screen.query_one("#breakdown-title")
            assert screen.query_one("#breakdown-sprint")
            assert screen.query_one("#breakdown-summary")
            assert screen.query_one("#breakdown-table")

    async def test_screen_shows_sprint_name(self) -> None:
        """Screen displays the sprint name."""
        from textual.app import App, ComposeResult
        from textual.widgets import Static

        tickets = [self._create_ticket("US1", owner="Alice", points=3)]

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield from ()

        app = TestApp()
        async with app.run_test() as pilot:
            screen = TeamBreakdownScreen(tickets, "Sprint 42")
            await app.push_screen(screen)
            await pilot.pause()

            # Query from screen, not app
            sprint_label = screen.query_one("#breakdown-sprint", Static)
            # Static.render() returns the content - convert to string
            assert "Sprint 42" in str(sprint_label.render())

    async def test_escape_closes_screen(self) -> None:
        """Escape key closes the screen."""
        from textual.app import App, ComposeResult

        tickets = [self._create_ticket("US1", owner="Alice", points=3)]

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield from ()

        app = TestApp()
        async with app.run_test() as pilot:
            screen = TeamBreakdownScreen(tickets, "Sprint 1")
            await app.push_screen(screen)
            await pilot.pause()

            # Screen should be active
            assert isinstance(app.screen, TeamBreakdownScreen)

            # Press escape
            await pilot.press("escape")
            await pilot.pause()

            # Screen should be dismissed
            assert not isinstance(app.screen, TeamBreakdownScreen)
