"""Iteration selection screen for filtering tickets by sprint."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from rally_tui.models import Iteration


# Special filter values
FILTER_ALL = "_all_"
FILTER_BACKLOG = "_backlog_"


class IterationScreen(Screen[str | None]):
    """Screen for selecting an iteration to filter tickets."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("1", "select_1", "1", show=False),
        Binding("2", "select_2", "2", show=False),
        Binding("3", "select_3", "3", show=False),
        Binding("4", "select_4", "4", show=False),
        Binding("5", "select_5", "5", show=False),
        Binding("0", "select_all", "0", show=False),
        Binding("b", "select_backlog", "Backlog", show=False),
    ]

    DEFAULT_CSS = """
    IterationScreen {
        background: $background;
    }

    #iteration-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #iteration-current {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #iteration-hint {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #iteration-container {
        align: center middle;
        padding: 1;
    }

    #iteration-buttons {
        align: center middle;
        padding: 1 2;
    }

    #iteration-buttons Button {
        margin: 0 1;
        min-width: 20;
    }

    #iteration-buttons Button.-current {
        background: $success;
    }

    #iteration-buttons Button.-selected {
        background: $primary;
    }

    #special-buttons {
        align: center middle;
        padding: 1 2;
    }

    #special-buttons Button {
        margin: 0 1;
        min-width: 16;
    }

    #special-buttons Button.-selected {
        background: $primary;
    }
    """

    def __init__(
        self,
        iterations: list[Iteration],
        current_filter: str | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize the iteration screen.

        Args:
            iterations: List of iterations to display.
            current_filter: Current iteration filter (iteration name, FILTER_ALL, FILTER_BACKLOG, or None).
            name: Screen name.
        """
        super().__init__(name=name)
        self._iterations = iterations[:5]  # Max 5 iterations
        self._current_filter = current_filter

    @property
    def iterations(self) -> list[Iteration]:
        """Get the iterations list."""
        return self._iterations

    @property
    def current_filter(self) -> str | None:
        """Get the current filter value."""
        return self._current_filter

    def _get_filter_display(self) -> str:
        """Get display text for current filter."""
        if self._current_filter is None or self._current_filter == FILTER_ALL:
            return "All Iterations"
        if self._current_filter == FILTER_BACKLOG:
            return "Backlog (Unscheduled)"
        return self._current_filter

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Filter by Iteration", id="iteration-title")
        yield Static(f"Current: {self._get_filter_display()}", id="iteration-current")
        yield Static(
            "Press 1-5 for iteration, 0 for All, B for Backlog:",
            id="iteration-hint",
        )
        with Vertical(id="iteration-container"):
            with Horizontal(id="iteration-buttons"):
                for i, iteration in enumerate(self._iterations, 1):
                    label = f"{i}. {iteration.short_name}"
                    btn = Button(label, id=f"btn-iter-{i}")
                    # Mark current sprint
                    if iteration.is_current:
                        btn.add_class("-current")
                    # Mark selected filter
                    if self._current_filter == iteration.name:
                        btn.add_class("-selected")
                    yield btn
            with Horizontal(id="special-buttons"):
                all_btn = Button("0. All", id="btn-iter-all")
                if self._current_filter is None or self._current_filter == FILTER_ALL:
                    all_btn.add_class("-selected")
                yield all_btn

                backlog_btn = Button("B. Backlog", id="btn-iter-backlog")
                if self._current_filter == FILTER_BACKLOG:
                    backlog_btn.add_class("-selected")
                yield backlog_btn
        yield Footer()

    def on_mount(self) -> None:
        """Focus the first button."""
        if self._iterations:
            self.query_one("#btn-iter-1", Button).focus()
        else:
            self.query_one("#btn-iter-all", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        btn_id = event.button.id
        if btn_id == "btn-iter-all":
            self.dismiss(FILTER_ALL)
        elif btn_id == "btn-iter-backlog":
            self.dismiss(FILTER_BACKLOG)
        elif btn_id and btn_id.startswith("btn-iter-"):
            index = int(btn_id.split("-")[-1]) - 1
            if 0 <= index < len(self._iterations):
                self.dismiss(self._iterations[index].name)

    def action_cancel(self) -> None:
        """Cancel and return without changes."""
        self.dismiss(None)

    def action_select_all(self) -> None:
        """Select all iterations (no filter)."""
        self.dismiss(FILTER_ALL)

    def action_select_backlog(self) -> None:
        """Select backlog (unscheduled items)."""
        self.dismiss(FILTER_BACKLOG)

    def action_select_1(self) -> None:
        """Select first iteration."""
        if len(self._iterations) >= 1:
            self.dismiss(self._iterations[0].name)

    def action_select_2(self) -> None:
        """Select second iteration."""
        if len(self._iterations) >= 2:
            self.dismiss(self._iterations[1].name)

    def action_select_3(self) -> None:
        """Select third iteration."""
        if len(self._iterations) >= 3:
            self.dismiss(self._iterations[2].name)

    def action_select_4(self) -> None:
        """Select fourth iteration."""
        if len(self._iterations) >= 4:
            self.dismiss(self._iterations[3].name)

    def action_select_5(self) -> None:
        """Select fifth iteration."""
        if len(self._iterations) >= 5:
            self.dismiss(self._iterations[4].name)
