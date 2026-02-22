"""Text formatter for human-readable CLI output."""

import html
import os
import re

from rally_tui.cli.formatters.base import BaseFormatter, CLIResult
from rally_tui.models import Attachment, Discussion, Feature, Iteration, Owner, Release, Tag, Ticket


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

    def format_ticket_detail(self, result: CLIResult) -> str:
        """Format a single ticket with full details for the show command.

        Args:
            result: CLIResult containing a single Ticket.

        Returns:
            Multi-line formatted string with all ticket fields.
        """
        if not result.success:
            return self.format_error(result)

        ticket: Ticket = result.data
        if ticket is None:
            return "No ticket found."

        # Header line
        header = f"{ticket.formatted_id} - {ticket.name}"
        try:
            terminal_width = os.get_terminal_size().columns
        except (ValueError, OSError):
            terminal_width = 80
        separator = "=" * min(len(header), terminal_width)

        lines = [header, separator]

        # Core fields
        label_width = 12
        type_label = self.TYPE_ABBREV.get(ticket.ticket_type, ticket.ticket_type)
        lines.append(f"{'Type:':<{label_width}}{type_label}")
        lines.append(f"{'State:':<{label_width}}{ticket.state}")
        lines.append(f"{'Owner:':<{label_width}}{ticket.owner or '-'}")
        lines.append(f"{'Iteration:':<{label_width}}{ticket.iteration or '-'}")

        # Points
        if ticket.points is not None:
            p = ticket.points
            pts = int(p) if isinstance(p, float) and p == int(p) else p
            lines.append(f"{'Points:':<{label_width}}{pts}")
        else:
            lines.append(f"{'Points:':<{label_width}}-")

        lines.append(f"{'Parent:':<{label_width}}{ticket.parent_id or '-'}")
        lines.append(f"{'Blocked:':<{label_width}}{'Yes' if ticket.blocked else 'No'}")
        lines.append(f"{'Ready:':<{label_width}}{'Yes' if ticket.ready else 'No'}")

        if ticket.expedite:
            lines.append(f"{'Expedite:':<{label_width}}Yes")

        if ticket.severity:
            lines.append(f"{'Severity:':<{label_width}}{ticket.severity}")
        if ticket.priority:
            lines.append(f"{'Priority:':<{label_width}}{ticket.priority}")
        if ticket.target_date:
            date_str = ticket.target_date[:10]
            lines.append(f"{'Target Date:':<{label_width}}{date_str}")

        # Dates (trim to date only)
        if ticket.creation_date:
            lines.append(f"{'Created:':<{label_width}}{ticket.creation_date[:10]}")
        if ticket.last_update_date:
            lines.append(f"{'Updated:':<{label_width}}{ticket.last_update_date[:10]}")

        # Rich text sections
        if ticket.acceptance_criteria:
            lines.append("")
            lines.append("Acceptance Criteria:")
            for ac_line in ticket.acceptance_criteria.splitlines():
                lines.append(f"  {ac_line}")

        if ticket.description:
            lines.append("")
            lines.append("Description:")
            for desc_line in ticket.description.splitlines():
                lines.append(f"  {desc_line}")

        if ticket.notes:
            lines.append("")
            lines.append("Notes:")
            for notes_line in ticket.notes.splitlines():
                lines.append(f"  {notes_line}")

        if ticket.blocked and ticket.blocked_reason:
            lines.append("")
            lines.append("Blocked Reason:")
            for br_line in ticket.blocked_reason.splitlines():
                lines.append(f"  {br_line}")

        return "\n".join(lines)

    def format_update_result(self, result: CLIResult) -> str:
        """Format ticket update result showing what changed.

        Args:
            result: CLIResult with data dict containing 'ticket' and 'changes'.

        Returns:
            Concise update summary string.
        """
        if not result.success:
            return self.format_error(result)

        data = result.data
        if isinstance(data, dict):
            ticket_id = data.get("formatted_id", "")
            changes = data.get("changes", {})
            if changes:
                change_parts = [f"{k} -> {v}" for k, v in changes.items()]
                return f"Updated {ticket_id}: {', '.join(change_parts)}"
            else:
                return f"Updated {ticket_id}"
        elif hasattr(data, "formatted_id"):
            return f"Updated {data.formatted_id}"
        return "Updated ticket"

    def format_delete_result(self, result: CLIResult) -> str:
        """Format ticket delete result confirming deletion.

        Args:
            result: CLIResult with data dict containing 'formatted_id'.

        Returns:
            Deletion confirmation string.
        """
        if not result.success:
            return self.format_error(result)

        data = result.data
        if isinstance(data, dict):
            ticket_id = data.get("formatted_id", "")
            return f"Deleted {ticket_id}"
        return "Deleted ticket"

    def format_discussions(self, result: CLIResult) -> str:
        """Format discussion list as human-readable text.

        Args:
            result: CLIResult containing discussion data. The data field
                can be a dict with 'discussions', 'formatted_id', 'count'
                keys, or a plain list of Discussion objects.

        Returns:
            Formatted discussion output.
        """
        if not result.success:
            return self.format_error(result)

        data = result.data

        # Support both dict-style (from CLI commands) and list-style data
        if isinstance(data, dict):
            discussions: list[Discussion] = data.get("discussions", [])
            formatted_id = data.get("formatted_id", "")
            count = data.get("count", len(discussions))
        else:
            discussions = data if data else []
            formatted_id = ""
            count = len(discussions)

        if not discussions:
            return "No discussions found."

        lines: list[str] = []

        # Header with ticket ID and count
        if formatted_id:
            header = f"Discussions for {formatted_id} ({count} comments)"
            lines.append(header)
            lines.append("=" * len(header))
            lines.append("")

        for disc in discussions:
            lines.append(disc.display_header)
            # Strip HTML tags for plain text display
            text = disc.text.replace("<br>", "\n").replace("<br/>", "\n")
            text = re.sub(r"<[^>]+>", "", text)
            text = html.unescape(text)
            for text_line in text.splitlines():
                stripped = text_line.strip()
                if stripped:
                    lines.append(f"  {stripped}")
            lines.append("")  # blank line between discussions

        return "\n".join(lines).rstrip()

    def format_iterations(self, result: CLIResult) -> str:
        """Format iteration list as a human-readable table.

        Args:
            result: CLIResult containing iteration data. The data field
                should contain a list of Iteration objects.

        Returns:
            Formatted iteration table.
        """
        if not result.success:
            return self.format_error(result)

        iterations: list[Iteration] = result.data
        if not iterations:
            return "No iterations found."

        lines: list[str] = []
        lines.append("Iterations")
        lines.append("==========")

        # Column widths
        name_w = max(max(len(it.name) for it in iterations), 4)
        name_w = min(name_w, 40)

        header = f"{'Name':<{name_w}}  {'Start':<12}  {'End':<12}  {'State':<12}  {'Current'}"
        lines.append(header)
        lines.append("-" * len(header))

        for it in iterations:
            current_marker = "*" if it.is_current else ""
            name_display = self._truncate(it.name, name_w).ljust(name_w)
            start_str = it.start_date.strftime("%b %d")
            end_str = it.end_date.strftime("%b %d")
            lines.append(
                f"{name_display}  {start_str:<12}  {end_str:<12}  {it.state:<12}  {current_marker}"
            )

        return "\n".join(lines)

    def format_users(self, result: CLIResult) -> str:
        """Format user list as a human-readable table.

        Args:
            result: CLIResult containing user/owner data. The data field
                should contain a list of Owner objects.

        Returns:
            Formatted user table.
        """
        if not result.success:
            return self.format_error(result)

        users: list[Owner] = result.data
        if not users:
            return "No users found."

        lines: list[str] = []
        lines.append("Team Members")
        lines.append("============")

        # Column widths
        name_w = max(max(len(u.display_name) for u in users), 4)
        name_w = min(name_w, 30)
        uname_w = max(max(len(u.user_name or "") for u in users), 8)
        uname_w = min(uname_w, 40)

        header = f"{'Name':<{name_w}}  {'Username':<{uname_w}}"
        lines.append(header)
        lines.append("-" * len(header))

        for u in users:
            display = self._truncate(u.display_name, name_w).ljust(name_w)
            username = self._truncate(u.user_name or "-", uname_w).ljust(uname_w)
            lines.append(f"{display}  {username}")

        return "\n".join(lines)

    def format_releases(self, result: CLIResult) -> str:
        """Format release list as a human-readable table.

        Args:
            result: CLIResult containing release data. The data field
                should contain a list of Release objects.

        Returns:
            Formatted release table.
        """
        if not result.success:
            return self.format_error(result)

        releases: list[Release] = result.data
        if not releases:
            return "No releases found."

        lines: list[str] = []
        lines.append("Releases")
        lines.append("========")

        # Column widths
        name_w = max(max(len(r.name) for r in releases), 4)
        name_w = min(name_w, 40)
        theme_w = (
            max(max(len(r.theme) for r in releases), 5) if any(r.theme for r in releases) else 5
        )
        theme_w = min(theme_w, 30)

        header = (
            f"{'Name':<{name_w}}  {'Start':<12}  {'End':<12}  {'State':<10}  {'Theme':<{theme_w}}"
        )
        lines.append(header)
        lines.append("-" * len(header))

        for r in releases:
            name_display = self._truncate(r.name, name_w).ljust(name_w)
            start_str = r.start_date.strftime("%b %d")
            end_str = r.end_date.strftime("%b %d")
            theme_display = self._truncate(r.theme, theme_w).ljust(theme_w)
            lines.append(
                f"{name_display}  {start_str:<12}  {end_str:<12}  {r.state:<10}  {theme_display}"
            )

        return "\n".join(lines)

    def format_tags(self, result: CLIResult) -> str:
        """Format tag list as a human-readable table.

        Args:
            result: CLIResult containing tag data. The data field
                should contain a list of Tag objects.

        Returns:
            Formatted tag table.
        """
        if not result.success:
            return self.format_error(result)

        tags: list[Tag] = result.data
        if not tags:
            return "No tags found."

        lines: list[str] = []
        lines.append("Tags")
        lines.append("====")
        lines.append("Name")
        lines.append("-" * max(max(len(t.name) for t in tags), 4))

        for t in tags:
            lines.append(t.name)

        return "\n".join(lines)

    def format_tag_action(self, result: CLIResult) -> str:
        """Format tag action result (create/add/remove).

        Args:
            result: CLIResult containing tag action data.

        Returns:
            Formatted action confirmation string.
        """
        if not result.success:
            return self.format_error(result)

        data = result.data
        if isinstance(data, dict):
            action = data.get("action", "")
            tag_name = data.get("tag_name", "")
            ticket_id = data.get("ticket_id", "")

            if action == "created":
                tag = data.get("tag")
                name = tag.name if tag else tag_name
                return f"Tag created: {name}"
            elif action == "added":
                return f"Tag '{tag_name}' added to {ticket_id}"
            elif action == "removed":
                return f"Tag '{tag_name}' removed from {ticket_id}"

        return "Tag operation completed"

    def format_attachment_action(self, result: CLIResult) -> str:
        """Format attachment action result (download/upload).

        Args:
            result: CLIResult containing attachment action data.

        Returns:
            Formatted action confirmation string.
        """
        if not result.success:
            return self.format_error(result)

        data = result.data
        if isinstance(data, dict):
            action = data.get("action", "")
            ticket_id = data.get("ticket_id", "")

            if action == "uploaded":
                attachment = data.get("attachment")
                name = attachment.name if attachment else ""
                return f"Uploaded '{name}' to {ticket_id}"
            elif action == "downloaded":
                filename = data.get("filename", "")
                dest = data.get("dest", filename)
                return f"Downloaded '{filename}' from {ticket_id} -> {dest}"
            elif action == "downloaded_all":
                downloaded = data.get("downloaded", [])
                count = data.get("count", len(downloaded))
                if count == 0:
                    return f"No attachments to download from {ticket_id}."
                lines = [f"Downloaded {count} attachment(s) from {ticket_id}:"]
                for name in downloaded:
                    lines.append(f"  - {name}")
                return "\n".join(lines)

        return "Attachment operation completed"

    def format_attachments(self, result: CLIResult) -> str:
        """Format attachment list as a human-readable table.

        Args:
            result: CLIResult containing attachment data. The data field
                should contain a dict with 'attachments', 'formatted_id', 'count'.

        Returns:
            Formatted attachment table.
        """
        if not result.success:
            return self.format_error(result)

        data = result.data
        if isinstance(data, dict):
            attachments: list[Attachment] = data.get("attachments", [])
            formatted_id = data.get("formatted_id", "")
            count = data.get("count", len(attachments))
        else:
            attachments = data if data else []
            formatted_id = ""
            count = len(attachments)

        if not attachments:
            return "No attachments found."

        lines: list[str] = []

        # Header
        if formatted_id:
            header = f"Attachments for {formatted_id} ({count} files)"
            lines.append(header)
            lines.append("=" * len(header))

        # Column widths
        name_w = max(max(len(a.name) for a in attachments), 4)
        name_w = min(name_w, 30)

        col_header = f"{'#':<4}  {'Name':<{name_w}}  {'Size':>10}  {'Type'}"
        lines.append(col_header)
        lines.append("-" * len(col_header))

        for i, att in enumerate(attachments, 1):
            name_display = self._truncate(att.name, name_w).ljust(name_w)
            lines.append(f"{i:<4}  {name_display}  {att.formatted_size:>10}  {att.short_type}")

        return "\n".join(lines)

    def format_features(self, result: CLIResult) -> str:
        """Format feature list as a human-readable table.

        Args:
            result: CLIResult containing feature data. The data field
                should contain a list of Feature objects.

        Returns:
            Formatted feature table.
        """
        if not result.success:
            return self.format_error(result)

        features: list[Feature] = result.data
        if not features:
            return "No features found."

        lines: list[str] = []
        lines.append("Features")
        lines.append("========")

        # Column widths
        id_w = max(max(len(f.formatted_id) for f in features), 2)
        id_w = min(id_w, 10)
        name_w = max(max(len(f.name) for f in features), 4)
        name_w = min(name_w, 30)
        state_w = (
            max(max(len(f.state) for f in features if f.state), 5)
            if any(f.state for f in features)
            else 5
        )
        state_w = min(state_w, 15)
        owner_w = (
            max(max(len(f.owner) for f in features if f.owner), 5)
            if any(f.owner for f in features)
            else 5
        )
        owner_w = min(owner_w, 15)

        header = (
            f"{'ID':<{id_w}}  {'Name':<{name_w}}  {'State':<{state_w}}  "
            f"{'Owner':<{owner_w}}  {'Stories'}"
        )
        lines.append(header)
        lines.append("-" * len(header))

        for f in features:
            id_display = self._truncate(f.formatted_id, id_w).ljust(id_w)
            name_display = self._truncate(f.name, name_w).ljust(name_w)
            state_display = self._truncate(f.state or "-", state_w).ljust(state_w)
            owner_display = self._truncate(f.owner or "-", owner_w).ljust(owner_w)
            lines.append(
                f"{id_display}  {name_display}  {state_display}  {owner_display}  {f.story_count}"
            )

        return "\n".join(lines)

    def format_feature_detail(self, result: CLIResult) -> str:
        """Format a single feature with full details.

        Args:
            result: CLIResult containing a dict with 'feature' and optionally 'children'.

        Returns:
            Multi-line formatted string with feature details and child stories.
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
            return "No feature found."

        if feature is None:
            return "No feature found."

        # Header line
        header = f"{feature.formatted_id} - {feature.name}"
        try:
            import os

            terminal_width = os.get_terminal_size().columns
        except (ValueError, OSError):
            terminal_width = 80
        separator = "=" * min(len(header), terminal_width)

        lines = [header, separator]

        label_width = 12
        lines.append(f"{'State:':<{label_width}}{feature.state or '-'}")
        lines.append(f"{'Owner:':<{label_width}}{feature.owner or '-'}")
        lines.append(f"{'Release:':<{label_width}}{feature.release or '-'}")
        lines.append(f"{'Stories:':<{label_width}}{feature.story_count}")

        if feature.description:
            lines.append("")
            lines.append("Description:")
            for desc_line in feature.description.splitlines():
                lines.append(f"  {desc_line}")

        if children:
            lines.append("")
            lines.append("Child Stories:")
            for child in children:
                if isinstance(child, dict):
                    fid = child.get("formatted_id", "")
                    state_display = child.get("state", "-") or "-"
                    name = child.get("name", "")
                else:
                    fid = child.formatted_id
                    state_display = child.state or "-"
                    name = child.name
                lines.append(f"  {fid}  {state_display:<15}  {name}")

        return "\n".join(lines)

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
