"""Owner model for Rally TUI ticket assignment."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Owner:
    """Represents a Rally user who can own tickets.

    Uses frozen=True for immutability (matching other models).
    display_name/user_name are excluded from equality/hash so two Owner
    instances with the same object_id are treated as the same Rally user,
    even if display_name differs (e.g., name update) — this enables proper
    deduplication in owner cache sets.
    """

    object_id: str  # Rally ObjectID for API calls
    display_name: str = field(compare=False)  # Full name for display
    user_name: str | None = field(default=None, compare=False)  # Username/email for reference
