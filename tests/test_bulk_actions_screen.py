"""Tests for BulkActionsScreen."""

from rally_tui.app import RallyTUI
from rally_tui.screens import BulkAction, BulkActionsScreen


class TestBulkActionsScreenCompose:
    """Tests for BulkActionsScreen composition."""

    async def test_screen_renders(self) -> None:
        """Screen should render without error."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(BulkActionsScreen(5))
            await pilot.pause()

            # Screen should be active
            assert isinstance(app.screen, BulkActionsScreen)

    async def test_screen_shows_selection_count(self) -> None:
        """Screen should display number of selected tickets."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(BulkActionsScreen(5))
            await pilot.pause()

            title = app.screen.query_one("#bulk-title")
            rendered = str(title.render())
            assert "5" in rendered

    async def test_screen_shows_action_buttons(self) -> None:
        """Screen should show all action buttons."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(BulkActionsScreen(3))
            await pilot.pause()

            btn_parent = app.screen.query_one("#btn-parent")
            btn_state = app.screen.query_one("#btn-state")
            btn_iteration = app.screen.query_one("#btn-iteration")
            btn_points = app.screen.query_one("#btn-points")
            btn_owner = app.screen.query_one("#btn-owner")
            btn_yank = app.screen.query_one("#btn-yank")
            assert btn_parent is not None
            assert btn_state is not None
            assert btn_iteration is not None
            assert btn_points is not None
            assert btn_owner is not None
            assert btn_yank is not None


class TestBulkActionsScreenKeys:
    """Tests for BulkActionsScreen keyboard shortcuts."""

    async def test_number_1_selects_parent(self) -> None:
        """Pressing 1 should select SET_PARENT action."""
        result: BulkAction | None = None

        def capture_result(action: BulkAction | None) -> None:
            nonlocal result
            result = action

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(BulkActionsScreen(3), callback=capture_result)
            await pilot.pause()
            await pilot.press("1")
            await pilot.pause()

        assert result == BulkAction.SET_PARENT

    async def test_number_2_selects_state(self) -> None:
        """Pressing 2 should select SET_STATE action."""
        result: BulkAction | None = None

        def capture_result(action: BulkAction | None) -> None:
            nonlocal result
            result = action

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(BulkActionsScreen(3), callback=capture_result)
            await pilot.pause()
            await pilot.press("2")
            await pilot.pause()

        assert result == BulkAction.SET_STATE

    async def test_number_3_selects_iteration(self) -> None:
        """Pressing 3 should select SET_ITERATION action."""
        result: BulkAction | None = None

        def capture_result(action: BulkAction | None) -> None:
            nonlocal result
            result = action

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(BulkActionsScreen(3), callback=capture_result)
            await pilot.pause()
            await pilot.press("3")
            await pilot.pause()

        assert result == BulkAction.SET_ITERATION

    async def test_number_4_selects_points(self) -> None:
        """Pressing 4 should select SET_POINTS action."""
        result: BulkAction | None = None

        def capture_result(action: BulkAction | None) -> None:
            nonlocal result
            result = action

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(BulkActionsScreen(3), callback=capture_result)
            await pilot.pause()
            await pilot.press("4")
            await pilot.pause()

        assert result == BulkAction.SET_POINTS

    async def test_number_5_selects_owner(self) -> None:
        """Pressing 5 should select SET_OWNER action."""
        result: BulkAction | None = None

        def capture_result(action: BulkAction | None) -> None:
            nonlocal result
            result = action

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(BulkActionsScreen(3), callback=capture_result)
            await pilot.pause()
            await pilot.press("5")
            await pilot.pause()

        assert result == BulkAction.SET_OWNER

    async def test_number_6_selects_yank(self) -> None:
        """Pressing 6 should select YANK action."""
        result: BulkAction | None = None

        def capture_result(action: BulkAction | None) -> None:
            nonlocal result
            result = action

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(BulkActionsScreen(3), callback=capture_result)
            await pilot.pause()
            await pilot.press("6")
            await pilot.pause()

        assert result == BulkAction.YANK

    async def test_escape_cancels(self) -> None:
        """Pressing escape should return None."""
        result = "not_set"

        def capture_result(action: BulkAction | None) -> None:
            nonlocal result
            result = action  # type: ignore

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(BulkActionsScreen(3), callback=capture_result)
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

        assert result is None


class TestBulkActionEnum:
    """Tests for BulkAction enum."""

    def test_parent_value(self) -> None:
        """SET_PARENT should have value 'parent'."""
        assert BulkAction.SET_PARENT.value == "parent"

    def test_state_value(self) -> None:
        """SET_STATE should have value 'state'."""
        assert BulkAction.SET_STATE.value == "state"

    def test_iteration_value(self) -> None:
        """SET_ITERATION should have value 'iteration'."""
        assert BulkAction.SET_ITERATION.value == "iteration"

    def test_points_value(self) -> None:
        """SET_POINTS should have value 'points'."""
        assert BulkAction.SET_POINTS.value == "points"

    def test_owner_value(self) -> None:
        """SET_OWNER should have value 'owner'."""
        assert BulkAction.SET_OWNER.value == "owner"

    def test_yank_value(self) -> None:
        """YANK should have value 'yank'."""
        assert BulkAction.YANK.value == "yank"

    def test_all_actions_unique(self) -> None:
        """All action values should be unique."""
        values = [action.value for action in BulkAction]
        assert len(values) == len(set(values))

    def test_has_six_actions(self) -> None:
        """BulkAction should have exactly 6 actions."""
        assert len(BulkAction) == 6


class TestBulkYankIntegration:
    """Integration tests for bulk yank functionality."""

    async def test_bulk_yank_copies_ids(self) -> None:
        """Bulk yank should copy comma-separated IDs to clipboard."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()

            # Select first two tickets
            await pilot.press("space")  # Select first
            await pilot.press("j")
            await pilot.press("space")  # Select second
            await pilot.pause()

            # Open bulk actions menu
            await pilot.press("m")
            await pilot.pause()

            # Press 6 for yank
            await pilot.press("6")
            await pilot.pause()

            # Verify selection was cleared after yank
            from rally_tui.widgets import TicketList

            ticket_list = app.query_one(TicketList)
            assert ticket_list.selection_count == 0

    async def test_bulk_yank_button_click(self) -> None:
        """Clicking yank button should work."""
        result: BulkAction | None = None

        def capture_result(action: BulkAction | None) -> None:
            nonlocal result
            result = action

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(BulkActionsScreen(3), callback=capture_result)
            await pilot.pause()

            # Scroll to and click the yank button
            btn_yank = app.screen.query_one("#btn-yank")
            btn_yank.scroll_visible()
            await pilot.pause()
            btn_yank.press()
            await pilot.pause()

        assert result == BulkAction.YANK
