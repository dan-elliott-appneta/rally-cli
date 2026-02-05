"""Owner model for Rally TUI ticket assignment."""

from dataclasses import dataclass


@dataclass(frozen=True, eq=False)
class Owner:
    """Represents a Rally user who can own tickets.

    Uses frozen=True for immutability (matching other models).
    Uses eq=False with custom __eq__ to compare only by object_id,
    enabling proper deduplication in owner cache sets.
    """

    object_id: str  # Rally ObjectID for API calls
    display_name: str  # Full name for display
    user_name: str | None = None  # Username/email for reference

    def __hash__(self) -> int:
        """Hash by object_id for set/dict operations."""
        return hash(self.object_id)

    def __eq__(self, other: object) -> bool:
        """Equality based on object_id only.

        Two Owner instances with the same object_id represent the same
        Rally user, even if display_name differs (e.g., name update).
        """
        if not isinstance(other, Owner):
            return False
        return self.object_id == other.object_id
