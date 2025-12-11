"""Tests for BulkActionsScreen."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.models import Ticket
from rally_tui.screens import BulkAction, BulkActionsScreen
from rally_tui.services import MockRallyClient


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
            assert btn_parent is not None
            assert btn_state is not None
            assert btn_iteration is not None
            assert btn_points is not None


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

    def test_all_actions_unique(self) -> None:
        """All action values should be unique."""
        values = [action.value for action in BulkAction]
        assert len(values) == len(set(values))

    def test_has_four_actions(self) -> None:
        """BulkAction should have exactly 4 actions."""
        assert len(BulkAction) == 4
