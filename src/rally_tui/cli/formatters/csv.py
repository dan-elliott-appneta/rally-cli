"""CSV formatter for CLI output."""

import csv
import io
from typing import Any

from rally_tui.cli.formatters.base import BaseFormatter, CLIResult
from rally_tui.models import Attachment, Discussion, Feature, Iteration, Owner, Release, Tag, Ticket


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

    def format_ticket_detail(self, result: CLIResult) -> str:
        """Format a single ticket with full details as a single CSV row.

        Args:
            result: CLIResult containing a single Ticket.

        Returns:
            CSV string with all ticket fields as a single row.
        """
        if not result.success:
            return self.format_error(result)

        ticket = result.data
        if ticket is None:
            return ""

        detail_fields = [
            "formatted_id",
            "name",
            "ticket_type",
            "state",
            "owner",
            "points",
            "iteration",
            "parent_id",
            "blocked",
            "ready",
            "expedite",
            "severity",
            "priority",
            "target_date",
            "creation_date",
            "last_update_date",
            "acceptance_criteria",
            "description",
            "notes",
            "blocked_reason",
        ]

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(detail_fields)
        row = [self._get_field_value(ticket, f) for f in detail_fields]
        writer.writerow(row)
        return output.getvalue().rstrip("\n")

    def format_update_result(self, result: CLIResult) -> str:
        """Format ticket update result as CSV.

        Args:
            result: CLIResult with data dict or Ticket.

        Returns:
            CSV string with updated ticket fields.
        """
        if not result.success:
            return self.format_error(result)

        from rally_tui.models import Ticket

        data = result.data
        if isinstance(data, Ticket):
            single_result = type(result)(success=True, data=data, error=None)
            return self.format_ticket_detail(single_result)
        elif isinstance(data, dict):
            ticket = data.get("ticket")
            if isinstance(ticket, Ticket):
                single_result = type(result)(success=True, data=ticket, error=None)
                return self.format_ticket_detail(single_result)

            # Fallback: render dict as key/value rows
            output = io.StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["field", "value"])
            for k, v in data.items():
                if k != "ticket":
                    writer.writerow([k, v])
            return output.getvalue().rstrip("\n")

        return ""

    def format_delete_result(self, result: CLIResult) -> str:
        """Format ticket delete result as CSV.

        Args:
            result: CLIResult with data dict containing 'formatted_id'.

        Returns:
            CSV string confirming deletion.
        """
        if not result.success:
            return self.format_error(result)

        data = result.data
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["formatted_id", "deleted"])
        if isinstance(data, dict):
            writer.writerow([data.get("formatted_id", ""), "true"])
        else:
            writer.writerow(["", "true"])
        return output.getvalue().rstrip("\n")

    def format_discussions(self, result: CLIResult) -> str:
        """Format discussion list as CSV.

        Args:
            result: CLIResult containing discussion data. The data field
                should contain a dict with 'discussions', 'formatted_id', 'count'.

        Returns:
            CSV string.
        """
        if not result.success:
            return self.format_error(result)

        data = result.data
        if isinstance(data, dict):
            discussions = data.get("discussions", [])
        else:
            discussions = data if data else []

        if not discussions:
            return ""

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["artifact_id", "user", "created_at", "text"])

        for disc in discussions:
            writer.writerow(
                [
                    disc.artifact_id,
                    disc.user,
                    disc.created_at.isoformat(),
                    disc.text,
                ]
            )

        return output.getvalue().rstrip("\n")

    def format_iterations(self, result: CLIResult) -> str:
        """Format iteration list as CSV.

        Args:
            result: CLIResult containing iteration data.

        Returns:
            CSV string.
        """
        if not result.success:
            return self.format_error(result)

        iterations: list[Iteration] = result.data
        if not iterations:
            return ""

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["name", "start_date", "end_date", "state", "is_current"])

        for it in iterations:
            writer.writerow(
                [
                    it.name,
                    it.start_date.isoformat(),
                    it.end_date.isoformat(),
                    it.state,
                    it.is_current,
                ]
            )

        return output.getvalue().rstrip("\n")

    def format_users(self, result: CLIResult) -> str:
        """Format user list as CSV.

        Args:
            result: CLIResult containing user/owner data.

        Returns:
            CSV string.
        """
        if not result.success:
            return self.format_error(result)

        users: list[Owner] = result.data
        if not users:
            return ""

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["display_name", "user_name", "object_id"])

        for u in users:
            writer.writerow(
                [
                    u.display_name,
                    u.user_name or "",
                    u.object_id,
                ]
            )

        return output.getvalue().rstrip("\n")

    def format_releases(self, result: CLIResult) -> str:
        """Format release list as CSV.

        Args:
            result: CLIResult containing release data.

        Returns:
            CSV string.
        """
        if not result.success:
            return self.format_error(result)

        releases: list[Release] = result.data
        if not releases:
            return ""

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["name", "start_date", "end_date", "state", "theme", "is_current"])

        for r in releases:
            writer.writerow(
                [
                    r.name,
                    r.start_date.isoformat(),
                    r.end_date.isoformat(),
                    r.state,
                    r.theme,
                    r.is_current,
                ]
            )

        return output.getvalue().rstrip("\n")

    def format_tags(self, result: CLIResult) -> str:
        """Format tag list as CSV.

        Args:
            result: CLIResult containing tag data.

        Returns:
            CSV string.
        """
        if not result.success:
            return self.format_error(result)

        tags: list[Tag] = result.data
        if not tags:
            return ""

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["name", "object_id"])

        for t in tags:
            writer.writerow([t.name, t.object_id])

        return output.getvalue().rstrip("\n")

    def format_tag_action(self, result: CLIResult) -> str:
        """Format tag action result as CSV.

        Args:
            result: CLIResult containing tag action data.

        Returns:
            CSV string.
        """
        if not result.success:
            return self.format_error(result)

        data = result.data
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["action", "tag_name", "ticket_id"])

        if isinstance(data, dict):
            action = data.get("action", "")
            tag_name = data.get("tag_name", "")
            ticket_id = data.get("ticket_id", "")
            if action == "created":
                tag = data.get("tag")
                tag_name = tag.name if tag else tag_name
            writer.writerow([action, tag_name, ticket_id])

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

    def format_attachment_action(self, result: CLIResult) -> str:
        """Format attachment action result as CSV.

        Args:
            result: CLIResult containing attachment action data.

        Returns:
            CSV string.
        """
        if not result.success:
            return self.format_error(result)

        data = result.data
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["action", "filename", "ticket_id"])

        if isinstance(data, dict):
            action = data.get("action", "")
            ticket_id = data.get("ticket_id", "")
            filename = data.get("filename", "")
            if action == "uploaded":
                attachment = data.get("attachment")
                filename = attachment.name if attachment else filename
            writer.writerow([action, filename, ticket_id])

        return output.getvalue().rstrip("\n")

    def format_attachments(self, result: CLIResult) -> str:
        """Format attachment list as CSV.

        Args:
            result: CLIResult containing attachment data.

        Returns:
            CSV string.
        """
        if not result.success:
            return self.format_error(result)

        data = result.data
        if isinstance(data, dict):
            attachments: list[Attachment] = data.get("attachments", [])
        else:
            attachments = data if data else []

        if not attachments:
            return ""

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["name", "size", "content_type", "object_id"])

        for att in attachments:
            writer.writerow([att.name, att.size, att.content_type, att.object_id])

        return output.getvalue().rstrip("\n")

    def format_features(self, result: CLIResult) -> str:
        """Format feature list as CSV.

        Args:
            result: CLIResult containing feature data.

        Returns:
            CSV string.
        """
        if not result.success:
            return self.format_error(result)

        features: list[Feature] = result.data
        if not features:
            return ""

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["formatted_id", "name", "state", "owner", "release", "story_count"])

        for f in features:
            writer.writerow([f.formatted_id, f.name, f.state, f.owner, f.release, f.story_count])

        return output.getvalue().rstrip("\n")

    def format_feature_detail(self, result: CLIResult) -> str:
        """Format single feature detail as CSV.

        Args:
            result: CLIResult containing feature data with optional children.

        Returns:
            CSV string.
        """
        if not result.success:
            return self.format_error(result)

        data = result.data
        if isinstance(data, dict):
            feature: Feature | None = data.get("feature")
            children: list[Ticket] = data.get("children", [])
        elif isinstance(data, Feature):
            feature = data
            children = []
        else:
            return ""

        if feature is None:
            return ""

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Feature header row
        writer.writerow(["formatted_id", "name", "state", "owner", "release", "story_count"])
        writer.writerow(
            [
                feature.formatted_id,
                feature.name,
                feature.state,
                feature.owner,
                feature.release,
                feature.story_count,
            ]
        )

        # Child stories section (if any)
        if children:
            writer.writerow([])  # blank separator
            writer.writerow(["child_id", "child_name", "child_state", "child_owner"])
            for child in children:
                if isinstance(child, dict):
                    writer.writerow(
                        [
                            child.get("formatted_id", ""),
                            child.get("name", ""),
                            child.get("state", ""),
                            child.get("owner", ""),
                        ]
                    )
                else:
                    writer.writerow(
                        [
                            child.formatted_id,
                            child.name,
                            child.state,
                            child.owner or "",
                        ]
                    )

        return output.getvalue().rstrip("\n")

    def format_config(self, result: CLIResult) -> str:
        """Format CLI configuration as CSV.

        Args:
            result: CLIResult containing configuration data.

        Returns:
            CSV string with key/value rows.
        """
        if not result.success:
            return self.format_error(result)

        data = result.data or {}
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["setting", "value"])

        for key in ("server", "workspace", "project", "apikey"):
            writer.writerow([key, data.get(key, "")])

        return output.getvalue().rstrip("\n")

    def format_summary(self, result: CLIResult) -> str:
        """Format sprint summary as CSV.

        Outputs three sections: totals, by_state, and by_owner as separate
        CSV tables separated by blank rows, followed by blocked tickets.

        Args:
            result: CLIResult containing sprint summary data.

        Returns:
            CSV string.
        """
        if not result.success:
            return self.format_error(result)

        data = result.data or {}
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Totals section
        writer.writerow(
            ["section", "iteration", "start_date", "end_date", "total_tickets", "total_points"]
        )
        writer.writerow(
            [
                "summary",
                data.get("iteration_name", ""),
                data.get("start_date", "") or "",
                data.get("end_date", "") or "",
                data.get("total_tickets", 0),
                data.get("total_points", 0),
            ]
        )

        # By state section
        by_state: list[dict] = data.get("by_state", [])
        if by_state:
            writer.writerow([])
            writer.writerow(["section", "state", "count", "points"])
            for entry in by_state:
                writer.writerow(["by_state", entry["state"], entry["count"], entry["points"]])

        # By owner section
        by_owner: list[dict] = data.get("by_owner", [])
        if by_owner:
            writer.writerow([])
            writer.writerow(["section", "owner", "count", "points"])
            for entry in by_owner:
                writer.writerow(["by_owner", entry["owner"], entry["count"], entry["points"]])

        # Blocked section
        blocked: list[dict] = data.get("blocked", [])
        if blocked:
            writer.writerow([])
            writer.writerow(["section", "formatted_id", "name", "blocked_reason"])
            for item in blocked:
                writer.writerow(
                    [
                        "blocked",
                        item["formatted_id"],
                        item.get("name", ""),
                        item.get("blocked_reason", ""),
                    ]
                )

        return output.getvalue().rstrip("\n")

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
