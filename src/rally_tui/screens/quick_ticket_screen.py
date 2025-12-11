"""Quick ticket creation screen."""

from dataclasses import dataclass
from typing import Literal

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static, TextArea


TicketType = Literal["HierarchicalRequirement", "Defect"]


@dataclass
class QuickTicketData:
    """Data for creating a quick ticket."""

    title: str
    ticket_type: TicketType
    description: str


class QuickTicketScreen(Screen[QuickTicketData | None]):
    """Screen for quickly creating a new ticket."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "submit", "Submit"),
    ]

    DEFAULT_CSS = """
    QuickTicketScreen {
        background: $background;
    }

    #quick-ticket-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #quick-ticket-hint {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    .form-row {
        height: auto;
        padding: 0 2;
        margin-bottom: 1;
    }

    .form-label {
        width: 15;
        padding: 1 0;
    }

    #title-input {
        width: 1fr;
    }

    .type-buttons {
        width: 1fr;
    }

    .type-btn {
        margin-right: 1;
    }

    .type-btn.-selected {
        background: $primary;
    }

    #description-input {
        height: 10;
        margin: 0 2;
        border: solid $primary;
    }

    #quick-ticket-error {
        text-align: center;
        padding: 1;
        color: $error;
        display: none;
    }
    """

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name=name)
        self._ticket_type: TicketType = "HierarchicalRequirement"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Create New Ticket", id="quick-ticket-title")
        yield Static(
            "Press Ctrl+S to submit, Escape to cancel",
            id="quick-ticket-hint",
        )

        # Title row
        with Horizontal(classes="form-row"):
            yield Label("Title:", classes="form-label")
            yield Input(placeholder="Enter ticket title", id="title-input")

        # Type row
        with Horizontal(classes="form-row"):
            yield Label("Type:", classes="form-label")
            with Horizontal(classes="type-buttons"):
                yield Button(
                    "User Story",
                    id="btn-story",
                    classes="type-btn -selected",
                )
                yield Button("Defect", id="btn-defect", classes="type-btn")

        # Description label
        with Horizontal(classes="form-row"):
            yield Label("Description:", classes="form-label")

        yield TextArea(id="description-input")
        yield Static("", id="quick-ticket-error")
        yield Footer()

    def on_mount(self) -> None:
        """Focus the title input."""
        self.query_one("#title-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle type button selection."""
        btn_story = self.query_one("#btn-story", Button)
        btn_defect = self.query_one("#btn-defect", Button)

        if event.button.id == "btn-story":
            self._ticket_type = "HierarchicalRequirement"
            btn_story.add_class("-selected")
            btn_defect.remove_class("-selected")
        elif event.button.id == "btn-defect":
            self._ticket_type = "Defect"
            btn_defect.add_class("-selected")
            btn_story.remove_class("-selected")

    def action_cancel(self) -> None:
        """Cancel and return without creating."""
        self.dismiss(None)

    def action_submit(self) -> None:
        """Submit the new ticket."""
        title_input = self.query_one("#title-input", Input)
        description_input = self.query_one("#description-input", TextArea)
        error_widget = self.query_one("#quick-ticket-error", Static)

        title = title_input.value.strip()
        description = description_input.text.strip()

        if not title:
            error_widget.update("Title is required")
            error_widget.display = True
            title_input.focus()
            return

        # Hide error and submit
        error_widget.display = False
        self.dismiss(
            QuickTicketData(
                title=title,
                ticket_type=self._ticket_type,
                description=description,
            )
        )
