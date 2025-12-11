"""Ticket data model - decoupled from Rally API responses."""

from dataclasses import dataclass
from typing import Literal

TicketType = Literal["UserStory", "Defect", "Task", "TestCase"]


@dataclass(frozen=True)
class Ticket:
    """Represents a Rally work item.

    This is an internal model, separate from pyral's response objects.
    Using a frozen dataclass provides immutability and easy equality checks.
    """

    formatted_id: str
    name: str
    ticket_type: TicketType
    state: str
    owner: str | None = None
    description: str = ""
    iteration: str | None = None
    points: int | None = None
    object_id: str | None = None  # Rally ObjectID for API calls

    @property
    def display_text(self) -> str:
        """Format for list display: 'US1234 User login feature'."""
        return f"{self.formatted_id} {self.name}"

    @property
    def type_prefix(self) -> str:
        """Extract prefix from formatted_id (US, DE, TA, TC)."""
        for i, char in enumerate(self.formatted_id):
            if char.isdigit():
                return self.formatted_id[:i]
        return self.formatted_id[:2]

    def rally_url(self, server: str = "rally1.rallydev.com") -> str | None:
        """Generate Rally web URL for this ticket.

        Args:
            server: Rally server hostname.

        Returns:
            URL to view the ticket in Rally, or None if object_id unavailable.
        """
        if not self.object_id:
            return None

        # Map ticket type to Rally URL path
        type_map = {
            "UserStory": "userstory",
            "Defect": "defect",
            "Task": "task",
            "TestCase": "testcase",
        }
        url_type = type_map.get(self.ticket_type, "artifact")
        return f"https://{server}/#/detail/{url_type}/{self.object_id}"
