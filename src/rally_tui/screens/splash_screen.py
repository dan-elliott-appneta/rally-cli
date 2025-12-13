"""Splash screen with ASCII art title."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.widgets import Static

from rally_tui import __version__

RALLY_TUI_ART = r"""

 ██████╗  █████╗ ██╗     ██╗  ██╗   ██╗    ████████╗██╗   ██╗██╗
 ██╔══██╗██╔══██╗██║     ██║  ╚██╗ ██╔╝    ╚══██╔══╝██║   ██║██║
 ██████╔╝███████║██║     ██║   ╚████╔╝        ██║   ██║   ██║██║
 ██╔══██╗██╔══██║██║     ██║    ╚██╔╝         ██║   ██║   ██║██║
 ██║  ██║██║  ██║███████╗███████╗██║          ██║   ╚██████╔╝██║
 ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝          ╚═╝    ╚═════╝ ╚═╝

"""


def get_splash_text() -> str:
    """Get the splash screen text with version."""
    return f"""{RALLY_TUI_ART}
            Terminal UI for Rally Work Items
                       v{__version__}

                Press any key to continue...
"""


class SplashScreen(Screen[None]):
    """Splash screen displayed on application startup."""

    BINDINGS = [
        Binding("any", "dismiss_splash", "Continue", show=False),
    ]

    DEFAULT_CSS = """
    SplashScreen {
        background: $background;
    }

    #splash-art {
        color: orange;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                yield Static(get_splash_text(), id="splash-art")

    def on_key(self, event) -> None:
        """Dismiss splash on any key press."""
        self.dismiss()

    def on_click(self, event) -> None:
        """Dismiss splash on click."""
        self.dismiss()

    def on_mount(self) -> None:
        """Set a timer to auto-dismiss after a few seconds."""
        self.set_timer(3.0, self._auto_dismiss)

    def _auto_dismiss(self) -> None:
        """Auto-dismiss the splash screen."""
        if self.is_active:
            self.dismiss()
