"""JSON formatter for machine-readable CLI output."""

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any

from rally_tui.cli.formatters.base import BaseFormatter, CLIResult
from rally_tui.models import Discussion, Ticket


class JSONFormatter(BaseFormatter):
    """Formatter for JSON output."""

    def format_tickets(self, result: CLIResult, fields: list[str] | None = None) -> str:
        """Format ticket list as JSON.

        Args:
            result: CLIResult containing ticket data.
            fields: Optional list of fields to include (ignored for JSON - all fields included).

        Returns:
            JSON string.
        """
        output = self._prepare_output(result)

        if result.success and result.data is not None:
            tickets: list[Ticket] = result.data
            output["data"] = [self._ticket_to_dict(t) for t in tickets]

        return json.dumps(output, indent=2, default=self._json_serializer)

    def format_comment(self, result: CLIResult) -> str:
        """Format comment confirmation as JSON.

        Args:
            result: CLIResult containing comment data.

        Returns:
            JSON string.
        """
        output = self._prepare_output(result)

        if result.success and result.data:
            discussion = result.data
            if isinstance(discussion, Discussion):
                output["data"] = self._discussion_to_dict(discussion)
            elif isinstance(discussion, dict):
                output["data"] = discussion

        return json.dumps(output, indent=2, default=self._json_serializer)

    def format_error(self, result: CLIResult) -> str:
        """Format error as JSON.

        Args:
            result: CLIResult containing error information.

        Returns:
            JSON string.
        """
        output = self._prepare_output(result)
        return json.dumps(output, indent=2)

    def _prepare_output(self, result: CLIResult) -> dict[str, Any]:
        """Prepare the base output dictionary.

        Args:
            result: CLIResult to convert.

        Returns:
            Dictionary with success, data, and error fields.
        """
        return {
            "success": result.success,
            "data": result.data if not result.success else None,
            "error": result.error,
        }

    def _ticket_to_dict(self, ticket: Ticket) -> dict[str, Any]:
        """Convert a Ticket to a dictionary.

        Args:
            ticket: The ticket to convert.

        Returns:
            Dictionary representation.
        """
        return asdict(ticket)

    def _discussion_to_dict(self, discussion: Discussion) -> dict[str, Any]:
        """Convert a Discussion to a dictionary.

        Args:
            discussion: The discussion to convert.

        Returns:
            Dictionary representation.
        """
        return {
            "object_id": discussion.object_id,
            "text": discussion.text,
            "user": discussion.user,
            "created_at": discussion.created_at.isoformat(),
            "artifact_id": discussion.artifact_id,
        }

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for non-standard types.

        Args:
            obj: The object to serialize.

        Returns:
            Serializable representation.

        Raises:
            TypeError: If object is not serializable.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
