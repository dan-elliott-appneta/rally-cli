"""Release data model."""

from dataclasses import dataclass
from datetime import date

from rally_tui.models.date_range import DateRangeMixin


@dataclass(frozen=True)
class Release(DateRangeMixin):
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
