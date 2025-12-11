"""Comment input screen for adding discussions."""

from typing import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, TextArea

from rally_tui.models import Ticket


class CommentScreen(Screen[str | None]):
    """Screen for composing a comment."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "submit", "Submit"),
    ]

    DEFAULT_CSS = """
    CommentScreen {
        background: $background;
    }

    #comment-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #comment-hint {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #comment-input {
        height: 1fr;
        margin: 1 2;
        border: solid $primary;
    }
    """

    def __init__(
        self,
        ticket: Ticket,
        on_submit: Callable[[str | None], None] | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._ticket = ticket
        self._on_submit = on_submit

    @property
    def ticket(self) -> Ticket:
        """Get the ticket being commented on."""
        return self._ticket

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"Add Comment - {self._ticket.formatted_id}",
            id="comment-title",
        )
        yield Static(
            "Press Ctrl+S to submit, Escape to cancel",
            id="comment-hint",
        )
        yield TextArea(id="comment-input")
        yield Footer()

    def on_mount(self) -> None:
        """Focus the text input."""
        self.query_one("#comment-input", TextArea).focus()

    def action_cancel(self) -> None:
        """Cancel and return to discussions."""
        if self._on_submit:
            self._on_submit(None)
        self.dismiss(None)

    def action_submit(self) -> None:
        """Submit the comment."""
        text_area = self.query_one("#comment-input", TextArea)
        text = text_area.text.strip()

        if text and self._on_submit:
            self._on_submit(text)
            self.dismiss(text)
        elif not text:
            if self._on_submit:
                self._on_submit(None)
            self.dismiss(None)
        else:
            self.dismiss(text if text else None)
