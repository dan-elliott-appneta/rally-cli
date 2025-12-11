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
