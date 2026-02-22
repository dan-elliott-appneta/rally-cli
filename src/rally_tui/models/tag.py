"""Tag data model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Tag:
    """Represents a Rally tag.

    Maps to Rally's Tag entity.
    """

    object_id: str
    name: str
