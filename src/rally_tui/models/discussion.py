"""Discussion/comment data model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Discussion:
    """Represents a Rally discussion post (comment).

    Maps to Rally's ConversationPost entity.
    """

    object_id: str
    text: str
    user: str
    created_at: datetime
    artifact_id: str  # FormattedID of the parent artifact

    @property
    def formatted_date(self) -> str:
        """Format date for display: 'Jan 15, 2024 10:30 AM'."""
        return self.created_at.strftime("%b %d, %Y %I:%M %p")

    @property
    def display_header(self) -> str:
        """Format header for display: 'John Smith - Jan 15, 2024 10:30 AM'."""
        return f"{self.user} - {self.formatted_date}"
