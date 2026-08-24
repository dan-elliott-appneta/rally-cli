"""Iteration (sprint) data model."""

from dataclasses import dataclass
from datetime import date

from rally_tui.models.date_range import DateRangeMixin


@dataclass(frozen=True)
class Iteration(DateRangeMixin):
    """Represents a Rally iteration (sprint).

    Maps to Rally's Iteration entity.
    """

    object_id: str
    name: str
    start_date: date
    end_date: date
    state: str = "Planning"  # Planning, Committed, Accepted

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
