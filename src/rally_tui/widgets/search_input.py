"""Search input widget for filtering tickets."""

from textual.binding import Binding
from textual.message import Message
from textual.widgets import Input


class SearchInput(Input):
    """Input field for search/filter queries.

    Emits SearchChanged on each keystroke and SearchCleared on Escape.
    """

    BINDINGS = [
        Binding("escape", "clear_search", "Clear", show=False, priority=True),
    ]

    class SearchChanged(Message):
        """Posted when search text changes."""

        def __init__(self, query: str) -> None:
            self.query = query
            super().__init__()

    class SearchCleared(Message):
        """Posted when search is cleared (Escape)."""

        pass

    class SearchSubmitted(Message):
        """Posted when search is submitted (Enter)."""

        def __init__(self, query: str) -> None:
            self.query = query
            super().__init__()

    DEFAULT_CSS = """
    SearchInput {
        height: 1;
        border: none;
        background: $surface;
        padding: 0 1;
    }

    SearchInput:focus {
        border: none;
    }

    SearchInput > .input--placeholder {
        color: $text-muted;
    }
    """

    def __init__(
        self,
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the search input.

        Args:
            id: Widget ID for CSS targeting.
            classes: CSS classes to apply.
        """
        super().__init__(
            placeholder="Search...",
            id=id,
            classes=classes,
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        """Emit SearchChanged when input changes."""
        self.post_message(self.SearchChanged(event.value))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Emit SearchSubmitted when Enter pressed."""
        self.post_message(self.SearchSubmitted(event.value))

    def action_clear_search(self) -> None:
        """Clear search and emit SearchCleared."""
        self.value = ""
        self.post_message(self.SearchCleared())
