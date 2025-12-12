"""State selection screen for changing ticket state."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from rally_tui.models import Ticket
from rally_tui.user_settings import UserSettings
from rally_tui.utils.keybindings import VIM_KEYBINDINGS


# Common workflow states for User Stories and Defects
# Note: Rally uses hyphenated "In-Progress" (not "In Progress")
WORKFLOW_STATES: list[str] = [
    "Defined",
    "In-Progress",
    "Completed",
    "Accepted",
]

# Additional states for defects
DEFECT_STATES: list[str] = [
    "Submitted",
    "Open",
    "Fixed",
    "Closed",
]


class StateScreen(Screen[str | None]):
    """Screen for changing a ticket's state."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("1", "select_1", "1", show=False),
        Binding("2", "select_2", "2", show=False),
        Binding("3", "select_3", "3", show=False),
        Binding("4", "select_4", "4", show=False),
    ]

    DEFAULT_CSS = """
    StateScreen {
        background: $background;
    }

    #state-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #state-current {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #state-hint {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #state-buttons {
        align: center middle;
        padding: 1 2;
    }

    #state-buttons Button {
        margin: 0 1;
        min-width: 16;
    }

    #state-buttons Button.-selected {
        background: $primary;
    }
    """

    def __init__(
        self,
        ticket: Ticket,
        name: str | None = None,
        user_settings: UserSettings | None = None,
    ) -> None:
        super().__init__(name=name)
        self._ticket = ticket
        self._states = self._get_states_for_type()
        self._user_settings = user_settings

    @property
    def ticket(self) -> Ticket:
        """Get the ticket being updated."""
        return self._ticket

    def _get_states_for_type(self) -> list[str]:
        """Get appropriate states based on ticket type."""
        if self._ticket.ticket_type == "Defect":
            return DEFECT_STATES
        return WORKFLOW_STATES

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"Set State - {self._ticket.formatted_id}",
            id="state-title",
        )
        yield Static(f"Current: {self._ticket.state}", id="state-current")
        yield Static(
            "Select a state or press 1-4:",
            id="state-hint",
        )
        with Horizontal(id="state-buttons"):
            for i, state in enumerate(self._states, 1):
                btn = Button(f"{i}. {state}", id=f"btn-state-{i}")
                if state == self._ticket.state:
                    btn.add_class("-selected")
                yield btn
        yield Footer()

    def on_mount(self) -> None:
        """Focus the first button and apply keybindings."""
        self._apply_keybindings()
        self.query_one("#btn-state-1", Button).focus()

    def _apply_keybindings(self) -> None:
        """Apply vim-style keybindings for button navigation."""
        if self._user_settings:
            keybindings = self._user_settings.keybindings
        else:
            keybindings = VIM_KEYBINDINGS

        navigation_bindings = {
            "navigation.down": "focus_next_button",
            "navigation.up": "focus_prev_button",
        }

        for action_id, handler in navigation_bindings.items():
            if action_id in keybindings:
                key = keybindings[action_id]
                self._bindings.bind(key, handler, show=False)

    def action_focus_next_button(self) -> None:
        """Move focus to the next button."""
        self.focus_next()

    def action_focus_prev_button(self) -> None:
        """Move focus to the previous button."""
        self.focus_previous()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle state button clicks."""
        btn_id = event.button.id
        if btn_id and btn_id.startswith("btn-state-"):
            index = int(btn_id.split("-")[-1]) - 1
            if 0 <= index < len(self._states):
                self.dismiss(self._states[index])

    def action_cancel(self) -> None:
        """Cancel and return without changes."""
        self.dismiss(None)

    def action_select_1(self) -> None:
        """Select first state."""
        if len(self._states) >= 1:
            self.dismiss(self._states[0])

    def action_select_2(self) -> None:
        """Select second state."""
        if len(self._states) >= 2:
            self.dismiss(self._states[1])

    def action_select_3(self) -> None:
        """Select third state."""
        if len(self._states) >= 3:
            self.dismiss(self._states[2])

    def action_select_4(self) -> None:
        """Select fourth state."""
        if len(self._states) >= 4:
            self.dismiss(self._states[3])
