"""CSV formatter for CLI output."""

import csv
import io
from typing import Any

from rally_tui.cli.formatters.base import BaseFormatter, CLIResult
from rally_tui.models import Discussion, Ticket


class CSVFormatter(BaseFormatter):
    """Formatter for CSV output."""

    # Default fields for ticket CSV
    DEFAULT_FIELDS = [
        "formatted_id",
        "name",
        "ticket_type",
        "state",
        "owner",
        "points",
        "iteration",
    ]

    def format_tickets(self, result: CLIResult, fields: list[str] | None = None) -> str:
        """Format ticket list as CSV.

        Args:
            result: CLIResult containing ticket data.
            fields: Optional list of fields to include.

        Returns:
            CSV string.
        """
        if not result.success:
            return self.format_error(result)

        tickets: list[Ticket] = result.data
        if not tickets:
            return ""

        # Use specified fields or defaults
        if fields is None:
            fields = self.DEFAULT_FIELDS

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Write header
        writer.writerow(fields)

        # Write data rows
        for ticket in tickets:
            row = [self._get_field_value(ticket, f) for f in fields]
            writer.writerow(row)

        return output.getvalue().rstrip("\n")

    def format_comment(self, result: CLIResult) -> str:
        """Format comment confirmation as CSV.

        Note: CSV format for single comment is less useful but provided
        for consistency. Returns a single-row CSV.

        Args:
            result: CLIResult containing comment data.

        Returns:
            CSV string.
        """
        if not result.success:
            return self.format_error(result)

        discussion = result.data
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header
        headers = ["artifact_id", "user", "created_at", "text"]
        writer.writerow(headers)

        # Data
        if isinstance(discussion, Discussion):
            row = [
                discussion.artifact_id,
                discussion.user,
                discussion.created_at.isoformat(),
                discussion.text,
            ]
        elif isinstance(discussion, dict):
            row = [
                discussion.get("artifact_id", ""),
                discussion.get("user", ""),
                discussion.get("created_at", ""),
                discussion.get("text", ""),
            ]
        else:
            row = ["", "", "", ""]

        writer.writerow(row)

        return output.getvalue().rstrip("\n")

    def format_error(self, result: CLIResult) -> str:
        """Format error as plain text.

        Note: Errors are not formatted as CSV since they're not tabular data.

        Args:
            result: CLIResult containing error information.

        Returns:
            Error string.
        """
        return f"Error: {result.error}"

    def _get_field_value(self, ticket: Ticket, field: str) -> Any:
        """Extract a field value from a ticket.

        Args:
            ticket: The ticket to extract the field from.
            field: The field name.

        Returns:
            The field value, or empty string if None.
        """
        value = getattr(ticket, field, None)

        if value is None:
            return ""

        if field == "points":
            if isinstance(value, float) and value == int(value):
                return int(value)
            return value

        return value
