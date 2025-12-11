"""Snapshot tests for visual regression."""

import pytest


class TestAppSnapshots:
    """Visual regression tests using pytest-textual-snapshot."""

    def test_initial_render(self, snap_compare) -> None:
        """Snapshot of initial app state with first item selected."""
        from rally_tui.app import RallyTUI

        assert snap_compare(RallyTUI())

    def test_selection_moved_down(self, snap_compare) -> None:
        """Snapshot after moving selection down twice."""
        from rally_tui.app import RallyTUI

        assert snap_compare(RallyTUI(), press=["j", "j"])

    def test_selection_at_bottom(self, snap_compare) -> None:
        """Snapshot with selection at the last item."""
        from rally_tui.app import RallyTUI

        assert snap_compare(RallyTUI(), press=["G"])

    def test_smaller_terminal(self, snap_compare) -> None:
        """Snapshot at a smaller terminal size."""
        from rally_tui.app import RallyTUI

        assert snap_compare(RallyTUI(), terminal_size=(60, 15))
