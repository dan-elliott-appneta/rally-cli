"""Team breakdown screen showing ticket distribution by owner."""

from collections import defaultdict
from dataclasses import dataclass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from rally_tui.models import Ticket


@dataclass
class OwnerStats:
    """Statistics for a single owner."""

    owner: str
    ticket_count: int
    total_points: float

    @property
    def avg_points(self) -> float:
        """Calculate average points per ticket."""
        if self.ticket_count == 0:
            return 0.0
        return self.total_points / self.ticket_count


class TeamBreakdownScreen(Screen[None]):
    """Screen showing team breakdown by ticket owner."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("q", "close", "Close"),
    ]

    DEFAULT_CSS = """
    TeamBreakdownScreen {
        background: $background;
    }

    #breakdown-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #breakdown-sprint {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #breakdown-summary {
        text-align: center;
        padding: 1;
        color: $text;
    }

    #breakdown-table {
        height: 1fr;
        margin: 1 2;
    }

    DataTable > .datatable--cursor {
        background: $accent 40%;
    }
    """

    def __init__(
        self,
        tickets: list[Ticket],
        sprint_name: str,
        name: str | None = None,
    ) -> None:
        """Initialize the team breakdown screen.

        Args:
            tickets: List of tickets to analyze.
            sprint_name: Name of the sprint being analyzed.
            name: Screen name.
        """
        super().__init__(name=name)
        self._tickets = tickets
        self._sprint_name = sprint_name
        self._stats = self._calculate_stats()

    def _calculate_stats(self) -> list[OwnerStats]:
        """Calculate statistics grouped by owner."""
        owner_data: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "points": 0.0})

        for ticket in self._tickets:
            owner = ticket.owner or "Unassigned"
            owner_data[owner]["count"] += 1
            if ticket.points is not None:
                owner_data[owner]["points"] += ticket.points

        stats = [
            OwnerStats(
                owner=owner,
                ticket_count=int(data["count"]),
                total_points=data["points"],
            )
            for owner, data in owner_data.items()
        ]

        # Sort by total points descending, then by ticket count
        stats.sort(key=lambda s: (-s.total_points, -s.ticket_count))
        return stats

    @property
    def stats(self) -> list[OwnerStats]:
        """Get the calculated owner statistics."""
        return self._stats

    @property
    def total_tickets(self) -> int:
        """Get total ticket count."""
        return len(self._tickets)

    @property
    def total_points(self) -> float:
        """Get total points across all tickets."""
        return sum(t.points or 0 for t in self._tickets)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Team Breakdown", id="breakdown-title")
        yield Static(f"Sprint: {self._sprint_name}", id="breakdown-sprint")
        yield Static(
            f"Total: {self.total_tickets} tickets, {self.total_points:.0f} points",
            id="breakdown-summary",
        )
        yield DataTable(id="breakdown-table")
        yield Footer()

    def on_mount(self) -> None:
        """Set up the data table."""
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Add columns
        table.add_column("Owner", width=30)
        table.add_column("Tickets", width=10)
        table.add_column("Points", width=10)
        table.add_column("Avg", width=8)

        # Add rows
        for stat in self._stats:
            avg_display = f"{stat.avg_points:.1f}" if stat.ticket_count > 0 else "-"
            table.add_row(
                stat.owner,
                str(stat.ticket_count),
                f"{stat.total_points:.0f}" if stat.total_points > 0 else "-",
                avg_display,
            )

        table.focus()

    def action_close(self) -> None:
        """Close the screen."""
        self.dismiss(None)
