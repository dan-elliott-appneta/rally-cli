"""Splash screen with ASCII art rally car."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.widgets import Static


RALLY_CAR_ART = r"""
                                         . -^   `--,
                                        /# =========`-_
                                       /# (--====___====\
                                      /#   .- --.  . --..|
                                     /##   |  * ) (   * ),
                                     |##   \    /\ \   / |
                                     |###   ---   \ ---  |
                                     |####      ___)    #|
                                     |######           ##|
                                      \##### ---------- /
                                       \####           (
                                        `\###          |
                                          \###         |
                                           \##        |
                                            \###.    .)
                                             `======/

                            ___________
                           /           \
          ___________     /   RALLY     \      ___________
         /           \   /     TUI       \    /           \
        /  _     _    \_/                 \__/    _     _  \
       |  | |   | |    |                   |    | |   | |  |
    ___|  |_|   |_|    |___________________|    |_|   |_|  |___
   /    \__/     \__/                           \__/   \__/    \
  /        ___________________________________________          \
 /________/   @@@@@                         @@@@@    \__________\
              @@@@@                         @@@@@
               @@@                           @@@


        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
       ~     ~     ~     ~  JUMP!  ~     ~     ~     ~     ~     ~
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

    #splash-container {
        width: 100%;
        height: 100%;
    }

    #splash-art {
        color: $success;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                yield Static(RALLY_CAR_ART, id="splash-art")

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
