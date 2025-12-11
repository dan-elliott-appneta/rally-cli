"""Status bar widget for displaying workspace/project info."""

from textual.widgets import Static


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
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the status bar.

        Args:
            workspace: Workspace name to display.
            project: Project name to display.
            id: Widget ID for CSS targeting.
            classes: CSS classes to apply.
        """
        super().__init__(id=id, classes=classes)
        self._workspace = workspace
        self._project = project
        self._display_content = ""

    def on_mount(self) -> None:
        """Set initial content when mounted."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the status bar content."""
        parts = [f"Workspace: {self._workspace}"]
        if self._project:
            parts.append(f"Project: {self._project}")
        parts.append("Offline")
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
