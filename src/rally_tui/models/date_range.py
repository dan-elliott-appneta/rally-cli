"""Shared date-range display logic for Iteration and Release."""

from datetime import date


class DateRangeMixin:
    """Mixin for models with a name and a start/end date range.

    Requires the including dataclass to define `name`, `start_date`, and
    `end_date` fields.
    """

    name: str
    start_date: date
    end_date: date

    @property
    def is_current(self) -> bool:
        """Check if today falls within the date range."""
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
