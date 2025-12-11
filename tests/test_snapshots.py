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

    def test_two_panel_defect_view(self, snap_compare) -> None:
        """Snapshot showing defect details in the right panel."""
        from rally_tui.app import RallyTUI

        # Navigate to first defect (DE456) at index 2
        assert snap_compare(RallyTUI(), press=["j", "j"])

    def test_unassigned_ticket(self, snap_compare) -> None:
        """Snapshot showing ticket with no owner (Unassigned)."""
        from rally_tui.app import RallyTUI

        # Navigate to DE457 which has no owner (index 5)
        assert snap_compare(RallyTUI(), press=["j", "j", "j", "j", "j"])

    def test_unscheduled_ticket(self, snap_compare) -> None:
        """Snapshot showing ticket with no iteration (Unscheduled)."""
        from rally_tui.app import RallyTUI

        # Navigate to US1237 which has no iteration (last item)
        assert snap_compare(RallyTUI(), press=["G"])
