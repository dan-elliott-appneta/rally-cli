"""Configuration screen for editing user settings."""

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static

from rally_tui.user_settings import UserSettings

# Available themes in Textual
AVAILABLE_THEMES: list[tuple[str, str]] = [
    ("textual-dark", "Textual Dark"),
    ("textual-light", "Textual Light"),
    ("catppuccin-mocha", "Catppuccin Mocha"),
    ("catppuccin-latte", "Catppuccin Latte"),
    ("nord", "Nord"),
    ("gruvbox", "Gruvbox"),
    ("dracula", "Dracula"),
    ("tokyo-night", "Tokyo Night"),
    ("monokai", "Monokai"),
    ("flexoki", "Flexoki"),
    ("solarized-light", "Solarized Light"),
]

# Log level options
LOG_LEVELS: list[tuple[str, str]] = [
    ("DEBUG", "Debug"),
    ("INFO", "Info"),
    ("WARNING", "Warning"),
    ("ERROR", "Error"),
    ("CRITICAL", "Critical"),
]


@dataclass
class ConfigData:
    """Data returned from ConfigScreen when saved."""

    theme_name: str
    log_level: str
    parent_options: list[str]


class ConfigScreen(Screen[ConfigData | None]):
    """Screen for editing user settings."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
    ]

    DEFAULT_CSS = """
    ConfigScreen {
        background: $background;
    }

    #config-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #config-content {
        padding: 1 2;
    }

    .config-section {
        margin-bottom: 1;
    }

    .section-label {
        text-style: bold;
        margin-bottom: 0;
    }

    .section-hint {
        color: $text-muted;
        margin-bottom: 0;
    }

    Select {
        width: 100%;
        margin-bottom: 1;
    }

    .parent-inputs {
        margin-top: 0;
    }

    .parent-input {
        width: 100%;
        margin-bottom: 0;
    }

    #button-row {
        align: center middle;
        padding: 1;
        margin-top: 1;
    }

    #button-row Button {
        margin: 0 2;
        min-width: 16;
    }

    #btn-save {
        background: $success;
    }

    #config-path {
        text-align: center;
        color: $text-muted;
        padding: 1;
    }
    """

    def __init__(
        self,
        settings: UserSettings,
        name: str | None = None,
    ) -> None:
        """Initialize the config screen.

        Args:
            settings: The user settings to edit.
            name: Optional screen name.
        """
        super().__init__(name=name)
        self._settings = settings

    @property
    def settings(self) -> UserSettings:
        """Get the user settings being edited."""
        return self._settings

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Settings", id="config-title")

        with Vertical(id="config-content"):
            # Theme section
            with Vertical(classes="config-section"):
                yield Label("Theme", classes="section-label")
                yield Label("Color scheme for the application", classes="section-hint")
                yield Select(
                    [(name, value) for value, name in AVAILABLE_THEMES],
                    value=self._settings.theme_name,
                    id="theme-select",
                    allow_blank=False,
                )

            # Log level section
            with Vertical(classes="config-section"):
                yield Label("Log Level", classes="section-label")
                yield Label(
                    "Minimum severity for log messages",
                    classes="section-hint",
                )
                yield Select(
                    [(name, value) for value, name in LOG_LEVELS],
                    value=self._settings.log_level,
                    id="log-level-select",
                    allow_blank=False,
                )

            # Parent options section
            with Vertical(classes="config-section"):
                yield Label("Parent Feature IDs", classes="section-label")
                yield Label(
                    "Quick-select options when setting parent (e.g., F12345)",
                    classes="section-hint",
                )
                parent_options = self._settings.parent_options
                with Vertical(classes="parent-inputs"):
                    yield Input(
                        value=parent_options[0] if len(parent_options) > 0 else "",
                        placeholder="Feature ID 1 (e.g., F12345)",
                        id="parent-1",
                        classes="parent-input",
                    )
                    yield Input(
                        value=parent_options[1] if len(parent_options) > 1 else "",
                        placeholder="Feature ID 2 (e.g., F12346)",
                        id="parent-2",
                        classes="parent-input",
                    )
                    yield Input(
                        value=parent_options[2] if len(parent_options) > 2 else "",
                        placeholder="Feature ID 3 (e.g., F12347)",
                        id="parent-3",
                        classes="parent-input",
                    )

            # Buttons
            with Horizontal(id="button-row"):
                yield Button("Save (Ctrl+S)", id="btn-save", variant="success")
                yield Button("Cancel (Esc)", id="btn-cancel", variant="default")

        # Show config file path
        yield Static(
            f"Config: {self._settings.CONFIG_FILE}",
            id="config-path",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Focus the theme selector on mount."""
        self.query_one("#theme-select", Select).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-save":
            self._save_and_dismiss()
        elif event.button.id == "btn-cancel":
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Cancel and return without saving."""
        self.dismiss(None)

    def action_save(self) -> None:
        """Save settings and dismiss."""
        self._save_and_dismiss()

    def _save_and_dismiss(self) -> None:
        """Gather form data, save to settings, and dismiss."""
        # Get theme
        theme_select = self.query_one("#theme-select", Select)
        theme_name = str(theme_select.value) if theme_select.value else "textual-dark"

        # Get log level
        log_level_select = self.query_one("#log-level-select", Select)
        log_level = str(log_level_select.value) if log_level_select.value else "INFO"

        # Get parent options (filter out empty strings)
        parent_1 = self.query_one("#parent-1", Input).value.strip().upper()
        parent_2 = self.query_one("#parent-2", Input).value.strip().upper()
        parent_3 = self.query_one("#parent-3", Input).value.strip().upper()
        parent_options = [p for p in [parent_1, parent_2, parent_3] if p]

        # Save to settings
        self._settings.theme_name = theme_name
        self._settings.log_level = log_level
        self._settings.parent_options = parent_options

        # Return the config data
        self.dismiss(
            ConfigData(
                theme_name=theme_name,
                log_level=log_level,
                parent_options=parent_options,
            )
        )
