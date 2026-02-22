"""Feature (Portfolio Item) data model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Feature:
    """Represents a Rally Portfolio Item / Feature.

    Maps to Rally's PortfolioItem/Feature entity.
    """

    object_id: str
    formatted_id: str  # e.g. "F59625"
    name: str
    state: str = ""
    owner: str = ""
    release: str = ""
    story_count: int = 0
    description: str = ""

    @property
    def display_text(self) -> str:
        """Format for list display: 'F59625 Authentication Epic'."""
        return f"{self.formatted_id} {self.name}"
