"""Snapshot tests for visual regression.

Note: Tickets are sorted by state order:
- Defined (US1235, TC101, US1237) - indices 0, 1, 2
- Open (DE456, DE457) - indices 3, 4
- In Progress (US1234, TA789) - indices 5, 6
- Completed (US1236) - index 7
"""


class TestAppSnapshots:
    """Visual regression tests using pytest-textual-snapshot."""

    def test_initial_render(self, snap_compare) -> None:
        """Snapshot of initial app state with first item selected."""
        from rally_tui.app import RallyTUI

        assert snap_compare(RallyTUI(show_splash=False))

    def test_selection_moved_down(self, snap_compare) -> None:
        """Snapshot after moving selection down twice."""
        from rally_tui.app import RallyTUI

        assert snap_compare(RallyTUI(show_splash=False), press=["j", "j"])

    def test_selection_at_bottom(self, snap_compare) -> None:
        """Snapshot with selection at the last item."""
        from rally_tui.app import RallyTUI

        assert snap_compare(RallyTUI(show_splash=False), press=["G"])

    def test_smaller_terminal(self, snap_compare) -> None:
        """Snapshot at a smaller terminal size."""
        from rally_tui.app import RallyTUI

        assert snap_compare(RallyTUI(show_splash=False), terminal_size=(60, 15))

    def test_two_panel_defect_view(self, snap_compare) -> None:
        """Snapshot showing defect details in the right panel."""
        from rally_tui.app import RallyTUI

        # Navigate to first defect DE456 (index 3 after sorting by state)
        assert snap_compare(RallyTUI(show_splash=False), press=["j", "j", "j"])

    def test_unassigned_ticket(self, snap_compare) -> None:
        """Snapshot showing ticket with no owner (Unassigned)."""
        from rally_tui.app import RallyTUI

        # Navigate to DE457 which has no owner (index 4 after sorting)
        assert snap_compare(RallyTUI(show_splash=False), press=["j", "j", "j", "j"])

    def test_unscheduled_ticket(self, snap_compare) -> None:
        """Snapshot showing ticket with no iteration (Unscheduled)."""
        from rally_tui.app import RallyTUI

        # Navigate to DE457 which has no iteration (index 4 after sorting)
        # Note: US1237 also has no iteration but is at index 2
        assert snap_compare(RallyTUI(show_splash=False), press=["j", "j", "j", "j"])
