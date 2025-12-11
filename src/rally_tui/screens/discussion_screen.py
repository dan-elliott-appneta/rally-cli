"""Discussion screen for viewing and adding comments."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from rally_tui.models import Discussion, Ticket
from rally_tui.services.protocol import RallyClientProtocol
from rally_tui.utils import html_to_text


class DiscussionItem(Static):
    """Widget for displaying a single discussion post."""

    DEFAULT_CSS = """
    DiscussionItem {
        background: $surface;
        border: solid $primary;
        margin: 1 2;
        padding: 1 2;
    }

    DiscussionItem .discussion-header {
        color: $text-muted;
        text-style: italic;
    }

    DiscussionItem .discussion-text {
        margin-top: 1;
    }
    """

    def __init__(self, discussion: Discussion) -> None:
        super().__init__()
        self._discussion = discussion

    def compose(self) -> ComposeResult:
        yield Static(self._discussion.display_header, classes="discussion-header")
        text = html_to_text(self._discussion.text) or self._discussion.text
        yield Static(text, classes="discussion-text")


class DiscussionScreen(Screen[None]):
    """Screen for viewing ticket discussions."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("c", "compose", "Add Comment"),
        Binding("q", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    DiscussionScreen {
        background: $background;
    }

    #discussion-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #discussion-container {
        height: 1fr;
    }

    #no-discussions {
        text-align: center;
        padding: 4;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        ticket: Ticket,
        client: RallyClientProtocol,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._ticket = ticket
        self._client = client
        self._discussions: list[Discussion] = []

    @property
    def ticket(self) -> Ticket:
        """Get the ticket being viewed."""
        return self._ticket

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"Discussions - {self._ticket.formatted_id}",
            id="discussion-title",
        )
        yield VerticalScroll(id="discussion-container")
        yield Footer()

    def on_mount(self) -> None:
        """Load discussions when screen mounts."""
        self._load_discussions()

    def _load_discussions(self) -> None:
        """Fetch and display discussions."""
        container = self.query_one("#discussion-container", VerticalScroll)
        container.remove_children()

        self._discussions = self._client.get_discussions(self._ticket)

        if not self._discussions:
            container.mount(Static("No discussions yet.", id="no-discussions"))
        else:
            for discussion in self._discussions:
                container.mount(DiscussionItem(discussion))

    def action_back(self) -> None:
        """Return to the main screen."""
        self.app.pop_screen()

    def action_compose(self) -> None:
        """Open comment input."""
        from rally_tui.screens.comment_screen import CommentScreen

        def on_comment_submitted(text: str | None) -> None:
            if text:
                result = self._client.add_comment(self._ticket, text)
                if result:
                    self._load_discussions()

        self.app.push_screen(
            CommentScreen(self._ticket, on_submit=on_comment_submitted)
        )
