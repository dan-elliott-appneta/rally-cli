"""Attachment data model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Attachment:
    """Represents a file attachment on a Rally artifact.

    Maps to Rally's Attachment entity.
    """

    name: str
    size: int  # size in bytes
    content_type: str
    object_id: str

    @property
    def formatted_size(self) -> str:
        """Human-readable file size.

        Examples:
            512 -> "512 B"
            2048 -> "2 KB"
            1572864 -> "1.5 MB"
        """
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size // 1024} KB"
        else:
            mb = self.size / (1024 * 1024)
            return f"{mb:.1f} MB"

    @property
    def short_type(self) -> str:
        """Short content type for display.

        Examples:
            application/pdf -> pdf
            image/png -> png
            text/plain -> plain
        """
        if "/" in self.content_type:
            return self.content_type.split("/")[-1]
        return self.content_type

    @property
    def display_line(self) -> str:
        """Formatted line for list display.

        Example: "requirements.pdf              245 KB    pdf"
        """
        return f"{self.name:<30} {self.formatted_size:>10}    {self.short_type}"
