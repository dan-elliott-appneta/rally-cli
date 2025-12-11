"""Status bar widget for displaying workspace/project info."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.widgets import Static

if TYPE_CHECKING:
    from rally_tui.widgets.ticket_list import SortMode


class StatusBar(Static):
    """Displays workspace/project info and connection status.

    Shows workspace name, project name, and connection status in a single line
    at the top of the application (below the header).
    """

    DEFAULT_CSS = """
    StatusBar {
        dock: top;
        height: 1;
        background: $primary-background;
        color: $text;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        workspace: str = "Not Connected",
        project: str = "",
        connected: bool = False,
        current_user: str | None = None,
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the status bar.

        Args:
            workspace: Workspace name to display.
            project: Project name to display.
            connected: Whether connected to Rally API.
            current_user: Name of the logged-in user (shown when connected).
            id: Widget ID for CSS targeting.
            classes: CSS classes to apply.
        """
        super().__init__(id=id, classes=classes)
        self._workspace = workspace
        self._project = project
        self._connected = connected
        self._current_user = current_user
        self._display_content = ""
        self._filter_info = ""
        self._iteration_filter: str | None = None
        self._user_filter_active = False
        self._sort_mode: str | None = None  # Display name of current sort mode

    def on_mount(self) -> None:
        """Set initial content when mounted."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the status bar content."""
        parts = ["[bold orange]rally-tui[/]"]
        if self._project:
            parts.append(f"Project: {self._project}")

        # Build filter display
        filters = []
        if self._iteration_filter:
            filters.append(f"Sprint: {self._iteration_filter}")
        if self._user_filter_active:
            filters.append("[cyan]My Items[/]")
        if filters:
            parts.append(" ".join(filters))

        # Show sort mode if not default (State)
        if self._sort_mode:
            parts.append(f"Sort: {self._sort_mode}")

        if self._filter_info:
            parts.append(self._filter_info)
        if self._connected:
            if self._current_user:
                status = f"Connected as {self._current_user}"
            else:
                status = "Connected"
        else:
            status = "Offline"
        parts.append(status)
        self._display_content = " | ".join(parts)
        self.update(self._display_content)

    @property
    def display_content(self) -> str:
        """Get the current display content string."""
        return self._display_content

    def set_workspace(self, workspace: str) -> None:
        """Update the workspace name.

        Args:
            workspace: New workspace name.
        """
        self._workspace = workspace
        self._update_display()

    def set_project(self, project: str) -> None:
        """Update the project name.

        Args:
            project: New project name.
        """
        self._project = project
        self._update_display()

    @property
    def workspace(self) -> str:
        """Get the current workspace name."""
        return self._workspace

    @property
    def project(self) -> str:
        """Get the current project name."""
        return self._project

    @property
    def connected(self) -> bool:
        """Get the current connection status."""
        return self._connected

    def set_connected(self, connected: bool) -> None:
        """Update connection status.

        Args:
            connected: Whether connected to Rally API.
        """
        self._connected = connected
        self._update_display()

    def set_filter_info(self, filtered: int, total: int) -> None:
        """Show filter count in status bar.

        Args:
            filtered: Number of tickets matching filter.
            total: Total number of tickets.
        """
        self._filter_info = f"Filtered: {filtered}/{total}"
        self._update_display()

    def clear_filter_info(self) -> None:
        """Clear filter info from status bar."""
        self._filter_info = ""
        self._update_display()

    @property
    def filter_info(self) -> str:
        """Get the current filter info string."""
        return self._filter_info

    def set_iteration_filter(self, iteration_name: str | None) -> None:
        """Set the iteration filter display.

        Args:
            iteration_name: Name of the iteration to show, or None to clear.
        """
        self._iteration_filter = iteration_name
        self._update_display()

    @property
    def iteration_filter(self) -> str | None:
        """Get the current iteration filter."""
        return self._iteration_filter

    def set_user_filter(self, active: bool) -> None:
        """Set whether the user filter (My Items) is active.

        Args:
            active: Whether the user filter is active.
        """
        self._user_filter_active = active
        self._update_display()

    @property
    def user_filter_active(self) -> bool:
        """Get whether the user filter is active."""
        return self._user_filter_active

    def set_sort_mode(self, mode: SortMode) -> None:
        """Set the current sort mode display.

        Args:
            mode: The sort mode to display. STATE mode is considered
                  default and won't be shown in the status bar.
        """
        # Import here to avoid circular import
        from rally_tui.widgets.ticket_list import SortMode

        mode_names = {
            SortMode.STATE: None,  # Default, don't show
            SortMode.CREATED: "Recent",
            SortMode.OWNER: "Owner",
        }
        self._sort_mode = mode_names.get(mode)
        self._update_display()

    @property
    def sort_mode_display(self) -> str | None:
        """Get the current sort mode display string."""
        return self._sort_mode
