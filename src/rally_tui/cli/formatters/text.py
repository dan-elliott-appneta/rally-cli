"""Text formatter for human-readable CLI output."""

from rally_tui.cli.formatters.base import BaseFormatter, CLIResult
from rally_tui.models import Discussion, Ticket


class TextFormatter(BaseFormatter):
    """Formatter for human-readable text output."""

    # Default column widths for ticket table
    DEFAULT_WIDTHS = {
        "formatted_id": 10,
        "ticket_type": 7,
        "state": 15,
        "owner": 15,
        "points": 6,
        "iteration": 20,
        "name": 40,
    }

    # Field aliases for display headers
    FIELD_HEADERS = {
        "formatted_id": "ID",
        "ticket_type": "Type",
        "state": "State",
        "owner": "Owner",
        "points": "Points",
        "iteration": "Iteration",
        "name": "Title",
        "description": "Description",
        "notes": "Notes",
        "object_id": "ObjectID",
        "parent_id": "Parent",
    }

    # Type abbreviations
    TYPE_ABBREV = {
        "UserStory": "Story",
        "Defect": "Defect",
        "Task": "Task",
        "TestCase": "Test",
    }

    def format_tickets(self, result: CLIResult, fields: list[str] | None = None) -> str:
        """Format ticket list as a human-readable table.

        Args:
            result: CLIResult containing ticket data.
            fields: Optional list of fields to include.

        Returns:
            Formatted table string.
        """
        if not result.success:
            return self.format_error(result)

        tickets: list[Ticket] = result.data
        if not tickets:
            return "No tickets found."

        # Default fields if not specified
        if fields is None:
            fields = [
                "formatted_id",
                "ticket_type",
                "state",
                "owner",
                "points",
                "iteration",
                "name",
            ]

        # Build header row
        headers = [self.FIELD_HEADERS.get(f, f.title()) for f in fields]

        # Build data rows
        rows: list[list[str]] = []
        for ticket in tickets:
            row = []
            for field in fields:
                value = self._get_field_value(ticket, field)
                row.append(value)
            rows.append(row)

        # Calculate column widths
        widths = []
        for i, field in enumerate(fields):
            max_data_width = max((len(row[i]) for row in rows), default=0)
            header_width = len(headers[i])
            default_width = self.DEFAULT_WIDTHS.get(field, 20)
            widths.append(max(header_width, min(max_data_width, default_width)))

        # Format output
        lines = []

        # Header
        header_line = "  ".join(headers[i].ljust(widths[i]) for i in range(len(headers)))
        lines.append(header_line)

        # Separator
        separator = "  ".join("-" * w for w in widths)
        lines.append(separator)

        # Data rows
        for row in rows:
            row_line = "  ".join(
                self._truncate(row[i], widths[i]).ljust(widths[i]) for i in range(len(row))
            )
            lines.append(row_line)

        return "\n".join(lines)

    def format_comment(self, result: CLIResult) -> str:
        """Format comment confirmation as human-readable text.

        Args:
            result: CLIResult containing comment data.

        Returns:
            Formatted confirmation string.
        """
        if not result.success:
            return self.format_error(result)

        discussion: Discussion | dict = result.data
        if isinstance(discussion, dict):
            artifact_id = discussion.get("artifact_id", "")
            user = discussion.get("user", "Unknown")
            created_at = discussion.get("created_at", "Unknown")
            text = discussion.get("text", "")
        else:
            artifact_id = discussion.artifact_id
            user = discussion.user
            created_at = discussion.formatted_date
            text = discussion.text

        lines = [
            f"Comment added to {artifact_id}",
            f"User: {user}",
            f"Time: {created_at}",
            f"Text: {text}",
        ]
        return "\n".join(lines)

    def format_error(self, result: CLIResult) -> str:
        """Format error as human-readable text.

        Args:
            result: CLIResult containing error information.

        Returns:
            Formatted error string.
        """
        return f"Error: {result.error}"

    def _get_field_value(self, ticket: Ticket, field: str) -> str:
        """Extract and format a field value from a ticket.

        Args:
            ticket: The ticket to extract the field from.
            field: The field name.

        Returns:
            String representation of the field value.
        """
        value = getattr(ticket, field, None)

        if value is None:
            return "-"

        if field == "ticket_type":
            return self.TYPE_ABBREV.get(value, str(value))

        if field == "points":
            if isinstance(value, float) and value == int(value):
                return str(int(value))
            return str(value)

        return str(value)

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length with ellipsis.

        Args:
            text: The text to truncate.
            max_length: Maximum length.

        Returns:
            Truncated text.
        """
        if len(text) <= max_length:
            return text
        if max_length <= 3:
            return text[:max_length]
        return text[: max_length - 3] + "..."
