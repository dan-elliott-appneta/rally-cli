"""Iteration (sprint) data model."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Iteration:
    """Represents a Rally iteration (sprint).

    Maps to Rally's Iteration entity.
    """

    object_id: str
    name: str
    start_date: date
    end_date: date
    state: str = "Planning"  # Planning, Committed, Accepted

    @property
    def is_current(self) -> bool:
        """Check if this iteration is currently active."""
        today = date.today()
        return self.start_date <= today <= self.end_date

    @property
    def formatted_dates(self) -> str:
        """Format date range for display: 'Dec 2 - Dec 15'."""
        start = self.start_date.strftime("%b %d")
        end = self.end_date.strftime("%b %d")
        return f"{start} - {end}"

    @property
    def display_name(self) -> str:
        """Format for display: 'Sprint 3 (Dec 2 - Dec 15)'."""
        return f"{self.name} ({self.formatted_dates})"

    @property
    def short_name(self) -> str:
        """Extract short name from full iteration name.

        Rally iterations often have long names like 'FY26-Q1 PI Sprint 3'.
        This extracts just 'Sprint 3' if possible.
        """
        # Try to find 'Sprint N' pattern
        parts = self.name.split()
        for i, part in enumerate(parts):
            if part.lower() == "sprint" and i + 1 < len(parts):
                return f"Sprint {parts[i + 1]}"
        # Fallback to last part or full name
        if len(parts) > 1:
            return parts[-1]
        return self.name
