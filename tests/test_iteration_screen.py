"""Tests for IterationScreen."""

from datetime import date, timedelta

import pytest

from rally_tui.app import RallyTUI
from rally_tui.models import Iteration
from rally_tui.screens import FILTER_ALL, FILTER_BACKLOG, IterationScreen
from rally_tui.services import MockRallyClient


@pytest.fixture
def sample_iterations() -> list[Iteration]:
    """Sample iterations for testing."""
    today = date.today()
    return [
        Iteration(
            object_id="1",
            name="Sprint 27",
            start_date=today + timedelta(days=14),
            end_date=today + timedelta(days=27),
            state="Planning",
        ),
        Iteration(
            object_id="2",
            name="Sprint 26",
            start_date=today - timedelta(days=7),
            end_date=today + timedelta(days=6),
            state="Committed",
        ),
        Iteration(
            object_id="3",
            name="Sprint 25",
            start_date=today - timedelta(days=21),
            end_date=today - timedelta(days=8),
            state="Accepted",
        ),
    ]


class TestIterationScreenCompose:
    """Tests for IterationScreen composition."""

    async def test_screen_renders(self, sample_iterations: list[Iteration]) -> None:
        """Screen should render without error."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(IterationScreen(sample_iterations))
            await pilot.pause()

            title = app.screen.query_one("#iteration-title")
            assert "Filter by Iteration" in str(title.render())

    async def test_screen_shows_current_filter(
        self, sample_iterations: list[Iteration]
    ) -> None:
        """Screen should show the current filter."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(
                IterationScreen(sample_iterations, current_filter="Sprint 25")
            )
            await pilot.pause()

            current = app.screen.query_one("#iteration-current")
            assert "Sprint 25" in str(current.render())

    async def test_screen_shows_all_when_no_filter(
        self, sample_iterations: list[Iteration]
    ) -> None:
        """Screen should show 'All Iterations' when no filter."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(IterationScreen(sample_iterations, current_filter=None))
            await pilot.pause()

            current = app.screen.query_one("#iteration-current")
            assert "All Iterations" in str(current.render())

    async def test_screen_shows_backlog_filter(
        self, sample_iterations: list[Iteration]
    ) -> None:
        """Screen should show 'Backlog' when backlog filter is set."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(
                IterationScreen(sample_iterations, current_filter=FILTER_BACKLOG)
            )
            await pilot.pause()

            current = app.screen.query_one("#iteration-current")
            assert "Backlog" in str(current.render())

    async def test_screen_has_iteration_buttons(
        self, sample_iterations: list[Iteration]
    ) -> None:
        """Screen should have iteration selection buttons."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(IterationScreen(sample_iterations))
            await pilot.pause()

            btn1 = app.screen.query_one("#btn-iter-1")
            btn2 = app.screen.query_one("#btn-iter-2")
            btn3 = app.screen.query_one("#btn-iter-3")
            assert btn1 is not None
            assert btn2 is not None
            assert btn3 is not None

    async def test_screen_has_special_buttons(
        self, sample_iterations: list[Iteration]
    ) -> None:
        """Screen should have All and Backlog buttons."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(IterationScreen(sample_iterations))
            await pilot.pause()

            all_btn = app.screen.query_one("#btn-iter-all")
            backlog_btn = app.screen.query_one("#btn-iter-backlog")
            assert all_btn is not None
            assert backlog_btn is not None


class TestIterationScreenHighlighting:
    """Tests for button highlighting."""

    async def test_current_iteration_highlighted(
        self, sample_iterations: list[Iteration]
    ) -> None:
        """Current iteration button should have -current class."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(IterationScreen(sample_iterations))
            await pilot.pause()

            # Sprint 26 is current (index 1, button 2)
            btn2 = app.screen.query_one("#btn-iter-2")
            assert "-current" in btn2.classes

    async def test_selected_filter_highlighted(
        self, sample_iterations: list[Iteration]
    ) -> None:
        """Selected filter button should have -selected class."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(
                IterationScreen(sample_iterations, current_filter="Sprint 25")
            )
            await pilot.pause()

            btn3 = app.screen.query_one("#btn-iter-3")
            assert "-selected" in btn3.classes

    async def test_all_selected_when_no_filter(
        self, sample_iterations: list[Iteration]
    ) -> None:
        """All button should be selected when no filter."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(IterationScreen(sample_iterations, current_filter=None))
            await pilot.pause()

            all_btn = app.screen.query_one("#btn-iter-all")
            assert "-selected" in all_btn.classes

    async def test_backlog_selected_when_backlog_filter(
        self, sample_iterations: list[Iteration]
    ) -> None:
        """Backlog button should be selected when backlog filter."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(
                IterationScreen(sample_iterations, current_filter=FILTER_BACKLOG)
            )
            await pilot.pause()

            backlog_btn = app.screen.query_one("#btn-iter-backlog")
            assert "-selected" in backlog_btn.classes


class TestIterationScreenSelection:
    """Tests for iteration selection."""

    async def test_click_button_selects_iteration(
        self, sample_iterations: list[Iteration]
    ) -> None:
        """Clicking an iteration button should select that iteration."""
        result = None

        def callback(value: str | None) -> None:
            nonlocal result
            result = value

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(IterationScreen(sample_iterations), callback=callback)
            await pilot.pause()

            btn2 = app.screen.query_one("#btn-iter-2")
            await pilot.click(btn2)
            await pilot.pause()

            assert result == "Sprint 26"

    async def test_number_key_selects_iteration(
        self, sample_iterations: list[Iteration]
    ) -> None:
        """Pressing number key should select corresponding iteration."""
        result = None

        def callback(value: str | None) -> None:
            nonlocal result
            result = value

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(IterationScreen(sample_iterations), callback=callback)
            await pilot.pause()

            await pilot.press("3")
            await pilot.pause()

            assert result == "Sprint 25"

    async def test_zero_selects_all(self, sample_iterations: list[Iteration]) -> None:
        """Pressing 0 should select All Iterations."""
        result = None

        def callback(value: str | None) -> None:
            nonlocal result
            result = value

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(IterationScreen(sample_iterations), callback=callback)
            await pilot.pause()

            await pilot.press("0")
            await pilot.pause()

            assert result == FILTER_ALL

    async def test_b_selects_backlog(self, sample_iterations: list[Iteration]) -> None:
        """Pressing B should select Backlog."""
        result = None

        def callback(value: str | None) -> None:
            nonlocal result
            result = value

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(IterationScreen(sample_iterations), callback=callback)
            await pilot.pause()

            await pilot.press("b")
            await pilot.pause()

            assert result == FILTER_BACKLOG

    async def test_click_all_button(self, sample_iterations: list[Iteration]) -> None:
        """Clicking All button should select All."""
        result = None

        def callback(value: str | None) -> None:
            nonlocal result
            result = value

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(IterationScreen(sample_iterations), callback=callback)
            await pilot.pause()

            all_btn = app.screen.query_one("#btn-iter-all")
            await pilot.click(all_btn)
            await pilot.pause()

            assert result == FILTER_ALL

    async def test_click_backlog_button(
        self, sample_iterations: list[Iteration]
    ) -> None:
        """Clicking Backlog button should select Backlog."""
        result = None

        def callback(value: str | None) -> None:
            nonlocal result
            result = value

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(IterationScreen(sample_iterations), callback=callback)
            await pilot.pause()

            backlog_btn = app.screen.query_one("#btn-iter-backlog")
            await pilot.click(backlog_btn)
            await pilot.pause()

            assert result == FILTER_BACKLOG


class TestIterationScreenCancel:
    """Tests for cancel behavior."""

    async def test_escape_cancels(self, sample_iterations: list[Iteration]) -> None:
        """Pressing escape should cancel and return None."""
        result = "not_called"

        def callback(value: str | None) -> None:
            nonlocal result
            result = value

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(IterationScreen(sample_iterations), callback=callback)
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

            assert result is None


class TestIterationScreenProperties:
    """Tests for IterationScreen properties."""

    def test_iterations_property(self, sample_iterations: list[Iteration]) -> None:
        """iterations property should return the iterations list."""
        screen = IterationScreen(sample_iterations)
        assert screen.iterations == sample_iterations

    def test_current_filter_property(self, sample_iterations: list[Iteration]) -> None:
        """current_filter property should return the filter."""
        screen = IterationScreen(sample_iterations, current_filter="Sprint 25")
        assert screen.current_filter == "Sprint 25"

    def test_current_filter_none(self, sample_iterations: list[Iteration]) -> None:
        """current_filter should be None when not set."""
        screen = IterationScreen(sample_iterations)
        assert screen.current_filter is None

    def test_max_five_iterations(self) -> None:
        """Screen should only show maximum 5 iterations."""
        iterations = [
            Iteration(
                object_id=str(i),
                name=f"Sprint {i}",
                start_date=date(2024, 1, i),
                end_date=date(2024, 1, i + 13),
            )
            for i in range(1, 10)
        ]
        screen = IterationScreen(iterations)
        assert len(screen.iterations) == 5


class TestIterationScreenEmptyIterations:
    """Tests for empty iterations list."""

    async def test_empty_iterations_renders(self) -> None:
        """Screen should render with empty iterations."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(IterationScreen([]))
            await pilot.pause()

            # Should still have All and Backlog buttons
            all_btn = app.screen.query_one("#btn-iter-all")
            backlog_btn = app.screen.query_one("#btn-iter-backlog")
            assert all_btn is not None
            assert backlog_btn is not None

    async def test_empty_iterations_focuses_all(self) -> None:
        """Empty iterations should focus All button."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(IterationScreen([]))
            await pilot.pause()

            all_btn = app.screen.query_one("#btn-iter-all")
            assert all_btn.has_focus
