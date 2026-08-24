"""Status bar widget for displaying workspace/project info."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from textual.reactive import reactive
from textual.widgets import Static

if TYPE_CHECKING:
    from rally_tui.widgets.ticket_list import SortMode


class CacheStatusDisplay(Enum):
    """Cache status for display in status bar."""

    LIVE = "live"
    CACHED = "cached"
    REFRESHING = "refreshing"
    OFFLINE = "offline"


class StatusBar(Static):
    """Displays workspace/project info and connection status.

    Shows workspace name, project name, and connection status in a single line
    at the top of the application (below the header).

    All mutable display state is held in `reactive` attributes; Textual
    automatically re-renders (via `render()`) whenever one of them changes.
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

    _filter_info: reactive[str] = reactive("")
    _iteration_filter: reactive[str | None] = reactive(None)
    _user_filter_active: reactive[bool] = reactive(False)
    _sort_mode: reactive[str | None] = reactive(None)  # Display name of current sort mode
    selection_count: reactive[int] = reactive(0)
    _cache_status: reactive[CacheStatusDisplay | None] = reactive(None)
    _cache_age_minutes: reactive[int | None] = reactive(None)
    _loading: reactive[bool] = reactive(False)

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

    def render(self) -> str:
        """Compute the status bar content from current display state."""
        parts = []
        if self._project:
            parts.append(f"Project: {self._project}")

        # Show loading indicator if fetching tickets
        if self._loading:
            parts.append("[bold cyan]Loading...[/]")

        # Show selection count if any tickets selected
        if self.selection_count > 0:
            parts.append(f"[bold cyan]{self.selection_count} selected[/]")

        # Build filter display
        filters = []
        if self._iteration_filter:
            filters.append(f"Sprint: {self._iteration_filter}")
        if self._user_filter_active:
            filters.append("[cyan]My Items[/]")
        if filters:
            parts.append(" ".join(filters))

        # Show sort mode
        if self._sort_mode:
            parts.append(f"Sort: {self._sort_mode}")

        if self._filter_info:
            parts.append(self._filter_info)

        # Show cache status if set
        if self._cache_status:
            cache_display = self._format_cache_status()
            if cache_display:
                parts.append(cache_display)

        if self._connected:
            if self._current_user:
                status = f"Connected as {self._current_user}"
            else:
                status = "Connected"
        else:
            status = "Offline"
        parts.append(status)
        return " | ".join(parts)

    def _format_cache_status(self) -> str:
        """Format cache status for display.

        Returns:
            Formatted cache status string with symbol and optional age.
        """
        if not self._cache_status:
            return ""

        if self._cache_status == CacheStatusDisplay.LIVE:
            return "[green]● Live[/]"
        elif self._cache_status == CacheStatusDisplay.CACHED:
            age_str = f" ({self._cache_age_minutes}m)" if self._cache_age_minutes else ""
            return f"[yellow]○ Cached{age_str}[/]"
        elif self._cache_status == CacheStatusDisplay.REFRESHING:
            return "[cyan]◌ Refreshing...[/]"
        elif self._cache_status == CacheStatusDisplay.OFFLINE:
            return "[red]⚠ Offline[/]"
        return ""

    @property
    def display_content(self) -> str:
        """Get the current display content string."""
        return self.render()

    def set_filter_info(self, filtered: int, total: int, query: str = "") -> None:
        """Show filter count and search query in status bar.

        Args:
            filtered: Number of tickets matching filter.
            total: Total number of tickets.
            query: The search query being filtered on.
        """
        if query:
            self._filter_info = f"Search: [cyan]{query}[/] ({filtered}/{total})"
        else:
            self._filter_info = f"Filtered: {filtered}/{total}"

    def clear_filter_info(self) -> None:
        """Clear filter info from status bar."""
        self._filter_info = ""

    def set_iteration_filter(self, iteration_name: str | None) -> None:
        """Set the iteration filter display.

        Args:
            iteration_name: Name of the iteration to show, or None to clear.
        """
        self._iteration_filter = iteration_name

    def set_user_filter(self, active: bool) -> None:
        """Set whether the user filter (My Items) is active.

        Args:
            active: Whether the user filter is active.
        """
        self._user_filter_active = active

    def set_sort_mode(self, mode: SortMode) -> None:
        """Set the current sort mode display.

        Args:
            mode: The sort mode to display.
        """
        # Import here to avoid circular import
        from rally_tui.widgets.ticket_list import SortMode

        mode_names = {
            SortMode.CREATED: "Recent",
            SortMode.STATE: "State",
            SortMode.OWNER: "Owner",
            SortMode.PARENT: "Parent",
        }
        self._sort_mode = mode_names.get(mode)

    def set_selection_count(self, count: int) -> None:
        """Set the number of selected tickets.

        Args:
            count: Number of selected tickets.
        """
        self.selection_count = count

    def set_cache_status(self, status: CacheStatusDisplay, age_minutes: int | None = None) -> None:
        """Set the cache status display.

        Args:
            status: The cache status to display.
            age_minutes: Age of the cache in minutes (for CACHED status).
        """
        self._cache_status = status
        self._cache_age_minutes = age_minutes

    def set_loading(self, loading: bool) -> None:
        """Set the loading indicator state.

        Args:
            loading: Whether tickets are currently being loaded.
        """
        self._loading = loading
