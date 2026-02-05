"""Owner model for Rally TUI ticket assignment."""

from dataclasses import dataclass


@dataclass
class Owner:
    """Represents a Rally user who can own tickets."""

    object_id: str  # Rally ObjectID for API calls
    display_name: str  # Full name for display
    user_name: str | None = None  # Username/email for reference

    def __hash__(self) -> int:
        """Hash by object_id for set/dict operations."""
        return hash(self.object_id)

    def __eq__(self, other: object) -> bool:
        """Equality based on object_id."""
        if not isinstance(other, Owner):
            return False
        return self.object_id == other.object_id
