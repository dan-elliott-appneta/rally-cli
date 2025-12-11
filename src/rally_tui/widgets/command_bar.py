"""Command bar widget for displaying context-sensitive keyboard shortcuts."""

from textual.widgets import Static


class CommandBar(Static):
    """Displays context-sensitive keyboard shortcuts at the bottom of the screen.

    The command bar shows different commands based on which panel has focus.
    It provides a cleaner alternative to the default Footer widget.
    """

    # Command sets for different contexts
    CONTEXTS = {
        "list": "[w] Workitem  [p] Points  [n] Notes  [d] Discuss  [\\[/\\]] Search  [Ctrl+P] Palette  [q] Quit",
        "detail": "[w] Workitem  [p] Points  [n] Notes  [d] Discuss  [Tab] Switch  [Ctrl+P] Palette  [q] Quit",
        "search": "[Enter] Confirm  [Esc] Clear  Type to filter...",
        "discussion": "[c] Comment  [Esc] Back  [q] Quit",
        "comment": "[Ctrl+S] Submit  [Esc] Cancel",
    }

    DEFAULT_CSS = """
    CommandBar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        context: str = "list",
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the command bar.

        Args:
            context: Initial context ("list" or "detail").
            id: Widget ID for CSS targeting.
            classes: CSS classes to apply.
        """
        super().__init__(id=id, classes=classes)
        self._current_ctx = context

    def on_mount(self) -> None:
        """Set initial content when mounted."""
        self.update(self.CONTEXTS.get(self._current_ctx, ""))

    def set_context(self, context: str) -> None:
        """Update the command bar for a new context.

        Args:
            context: The new context ("list" or "detail").
        """
        self._current_ctx = context
        commands = self.CONTEXTS.get(context, "")
        self.update(commands)

    @property
    def context(self) -> str:
        """Get the current context."""
        return self._current_ctx
