"""Release data model."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Release:
    """Represents a Rally release.

    Maps to Rally's Release entity.
    """

    object_id: str
    name: str
    start_date: date
    end_date: date
    state: str = "Planning"  # Planning, Active, Locked
    theme: str = ""
    notes: str = ""

    @property
    def is_current(self) -> bool:
        """Check if this release is currently active."""
        today = date.today()
        return self.start_date <= today <= self.end_date

    @property
    def formatted_dates(self) -> str:
        """Format date range for display: 'Jan 15 - Feb 28'."""
        start = self.start_date.strftime("%b %d")
        end = self.end_date.strftime("%b %d")
        return f"{start} - {end}"

    @property
    def display_name(self) -> str:
        """Format for display: 'Release 2.0 (Jan 15 - Feb 28)'."""
        return f"{self.name} ({self.formatted_dates})"
