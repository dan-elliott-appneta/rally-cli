"""Tests for the StatusBar widget."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.widgets import StatusBar


class TestStatusBarUnit:
    """Unit tests for StatusBar widget in isolation."""

    def test_default_workspace(self) -> None:
        """Default workspace should be 'Not Connected'."""
        bar = StatusBar()
        assert bar.workspace == "Not Connected"

    def test_default_project_is_empty(self) -> None:
        """Default project should be empty string."""
        bar = StatusBar()
        assert bar.project == ""

    def test_custom_workspace(self) -> None:
        """StatusBar should accept custom workspace."""
        bar = StatusBar(workspace="My Workspace")
        assert bar.workspace == "My Workspace"

    def test_custom_project(self) -> None:
        """StatusBar should accept custom project."""
        bar = StatusBar(project="My Project")
        assert bar.project == "My Project"

    def test_custom_workspace_and_project(self) -> None:
        """StatusBar should accept both workspace and project."""
        bar = StatusBar(workspace="Test Workspace", project="Test Project")
        assert bar.workspace == "Test Workspace"
        assert bar.project == "Test Project"

    def test_set_workspace_updates_value(self) -> None:
        """set_workspace should update the workspace property."""
        bar = StatusBar()
        bar.set_workspace("New Workspace")
        assert bar.workspace == "New Workspace"

    def test_set_project_updates_value(self) -> None:
        """set_project should update the project property."""
        bar = StatusBar()
        bar.set_project("New Project")
        assert bar.project == "New Project"

    def test_default_connected_is_false(self) -> None:
        """Default connected status should be False."""
        bar = StatusBar()
        assert bar.connected is False

    def test_custom_connected(self) -> None:
        """StatusBar should accept custom connected status."""
        bar = StatusBar(connected=True)
        assert bar.connected is True

    def test_set_connected_updates_value(self) -> None:
        """set_connected should update the connected property."""
        bar = StatusBar()
        bar.set_connected(True)
        assert bar.connected is True

    def test_default_filter_info_is_empty(self) -> None:
        """Default filter_info should be empty string."""
        bar = StatusBar()
        assert bar.filter_info == ""

    def test_set_filter_info(self) -> None:
        """set_filter_info should update filter_info."""
        bar = StatusBar()
        bar.set_filter_info(5, 10)
        assert bar.filter_info == "Filtered: 5/10"

    def test_clear_filter_info(self) -> None:
        """clear_filter_info should reset filter_info to empty."""
        bar = StatusBar()
        bar.set_filter_info(3, 8)
        bar.clear_filter_info()
        assert bar.filter_info == ""

    def test_default_iteration_filter_is_none(self) -> None:
        """Default iteration_filter should be None."""
        bar = StatusBar()
        assert bar.iteration_filter is None

    def test_set_iteration_filter(self) -> None:
        """set_iteration_filter should update iteration_filter."""
        bar = StatusBar()
        bar.set_iteration_filter("Sprint 26")
        assert bar.iteration_filter == "Sprint 26"

    def test_set_iteration_filter_none(self) -> None:
        """set_iteration_filter with None should clear the filter."""
        bar = StatusBar()
        bar.set_iteration_filter("Sprint 26")
        bar.set_iteration_filter(None)
        assert bar.iteration_filter is None

    def test_default_user_filter_is_false(self) -> None:
        """Default user_filter_active should be False."""
        bar = StatusBar()
        assert bar.user_filter_active is False

    def test_set_user_filter_true(self) -> None:
        """set_user_filter(True) should activate user filter."""
        bar = StatusBar()
        bar.set_user_filter(True)
        assert bar.user_filter_active is True

    def test_set_user_filter_false(self) -> None:
        """set_user_filter(False) should deactivate user filter."""
        bar = StatusBar()
        bar.set_user_filter(True)
        bar.set_user_filter(False)
        assert bar.user_filter_active is False


class TestStatusBarWidget:
    """Integration tests for StatusBar widget behavior."""

    async def test_status_bar_renders_default(self) -> None:
        """StatusBar should render with default values."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert status_bar is not None
            assert status_bar.workspace == "Not Connected"

    async def test_status_bar_shows_banner(self) -> None:
        """StatusBar should display RALLY TUI banner."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(workspace="My Workspace", id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert status_bar.workspace == "My Workspace"
            # Check the rendered content includes RALLY TUI banner
            assert "RALLY TUI" in status_bar.display_content

    async def test_status_bar_shows_project(self) -> None:
        """StatusBar should display project name when set."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(
                    workspace="Test Workspace",
                    project="Test Project",
                    id="status-bar",
                )

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert "Test Project" in status_bar.display_content

    async def test_status_bar_shows_offline(self) -> None:
        """StatusBar should show 'Offline' status indicator."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert "Offline" in status_bar.display_content

    async def test_status_bar_update_workspace(self) -> None:
        """StatusBar workspace property updates but banner stays."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            status_bar.set_workspace("Updated Workspace")
            # Workspace property updates, but banner stays RALLY TUI
            assert status_bar.workspace == "Updated Workspace"
            assert "RALLY TUI" in status_bar.display_content

    async def test_status_bar_format_with_project(self) -> None:
        """StatusBar should format with pipe separators."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(
                    workspace="WS",
                    project="PR",
                    id="status-bar",
                )

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            content = status_bar.display_content
            # Should contain banner, project, and offline with separators
            assert "RALLY TUI" in content
            assert "Project: PR" in content
            assert "|" in content

    async def test_status_bar_format_without_project(self) -> None:
        """StatusBar should omit project when empty."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(
                    workspace="WS",
                    project="",
                    id="status-bar",
                )

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            content = status_bar.display_content
            assert "RALLY TUI" in content
            assert "Project:" not in content

    async def test_status_bar_shows_connected(self) -> None:
        """StatusBar should show 'Connected' when connected=True."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(connected=True, id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert "Connected" in status_bar.display_content
            assert "Offline" not in status_bar.display_content

    async def test_status_bar_set_connected_updates_display(self) -> None:
        """StatusBar should update display when set_connected is called."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert "Offline" in status_bar.display_content
            status_bar.set_connected(True)
            assert "Connected" in status_bar.display_content

    async def test_status_bar_shows_filter_info(self) -> None:
        """StatusBar should show filter info when set."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            status_bar.set_filter_info(3, 10)
            assert "Filtered: 3/10" in status_bar.display_content

    async def test_status_bar_clears_filter_info(self) -> None:
        """StatusBar should clear filter info when cleared."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            status_bar.set_filter_info(3, 10)
            assert "Filtered: 3/10" in status_bar.display_content
            status_bar.clear_filter_info()
            assert "Filtered:" not in status_bar.display_content

    async def test_status_bar_shows_iteration_filter(self) -> None:
        """StatusBar should show iteration filter when set."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            status_bar.set_iteration_filter("Sprint 26")
            assert "Sprint: Sprint 26" in status_bar.display_content

    async def test_status_bar_clears_iteration_filter(self) -> None:
        """StatusBar should clear iteration filter when set to None."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            status_bar.set_iteration_filter("Sprint 26")
            assert "Sprint:" in status_bar.display_content
            status_bar.set_iteration_filter(None)
            assert "Sprint:" not in status_bar.display_content

    async def test_status_bar_shows_user_filter(self) -> None:
        """StatusBar should show 'My Items' when user filter is active."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            status_bar.set_user_filter(True)
            assert "My Items" in status_bar.display_content

    async def test_status_bar_hides_user_filter(self) -> None:
        """StatusBar should hide 'My Items' when user filter is inactive."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            status_bar.set_user_filter(True)
            assert "My Items" in status_bar.display_content
            status_bar.set_user_filter(False)
            assert "My Items" not in status_bar.display_content

    async def test_status_bar_shows_both_filters(self) -> None:
        """StatusBar should show both filters when both are active."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            status_bar.set_iteration_filter("Sprint 26")
            status_bar.set_user_filter(True)
            content = status_bar.display_content
            assert "Sprint: Sprint 26" in content
            assert "My Items" in content


class TestStatusBarInApp:
    """Tests for StatusBar integration in the RallyTUI app."""

    async def test_status_bar_exists_in_app(self) -> None:
        """StatusBar should be present in the app."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert status_bar is not None

    async def test_status_bar_shows_banner_in_app(self) -> None:
        """StatusBar should show RALLY TUI banner in app."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert "RALLY TUI" in status_bar.display_content

    async def test_status_bar_shows_project_in_app(self) -> None:
        """StatusBar should show project name in app."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert "My Project" in status_bar.display_content


class TestStatusBarCacheStatus:
    """Tests for cache status display in StatusBar."""

    def test_default_cache_status_is_none(self) -> None:
        """Default cache_status should be None."""
        bar = StatusBar()
        assert bar.cache_status is None

    def test_default_cache_age_is_none(self) -> None:
        """Default cache_age_minutes should be None."""
        bar = StatusBar()
        assert bar.cache_age_minutes is None

    def test_set_cache_status_live(self) -> None:
        """set_cache_status should set LIVE status."""
        from rally_tui.widgets.status_bar import CacheStatusDisplay

        bar = StatusBar()
        bar.set_cache_status(CacheStatusDisplay.LIVE)
        assert bar.cache_status == CacheStatusDisplay.LIVE

    def test_set_cache_status_cached_with_age(self) -> None:
        """set_cache_status should set CACHED status with age."""
        from rally_tui.widgets.status_bar import CacheStatusDisplay

        bar = StatusBar()
        bar.set_cache_status(CacheStatusDisplay.CACHED, age_minutes=5)
        assert bar.cache_status == CacheStatusDisplay.CACHED
        assert bar.cache_age_minutes == 5

    def test_set_cache_status_refreshing(self) -> None:
        """set_cache_status should set REFRESHING status."""
        from rally_tui.widgets.status_bar import CacheStatusDisplay

        bar = StatusBar()
        bar.set_cache_status(CacheStatusDisplay.REFRESHING)
        assert bar.cache_status == CacheStatusDisplay.REFRESHING

    def test_set_cache_status_offline(self) -> None:
        """set_cache_status should set OFFLINE status."""
        from rally_tui.widgets.status_bar import CacheStatusDisplay

        bar = StatusBar()
        bar.set_cache_status(CacheStatusDisplay.OFFLINE)
        assert bar.cache_status == CacheStatusDisplay.OFFLINE

    def test_clear_cache_status(self) -> None:
        """clear_cache_status should clear the status."""
        from rally_tui.widgets.status_bar import CacheStatusDisplay

        bar = StatusBar()
        bar.set_cache_status(CacheStatusDisplay.LIVE)
        bar.clear_cache_status()
        assert bar.cache_status is None
        assert bar.cache_age_minutes is None

    async def test_cache_status_live_display(self) -> None:
        """Live status should show green bullet."""
        from textual.app import App, ComposeResult

        from rally_tui.widgets.status_bar import CacheStatusDisplay

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            status_bar.set_cache_status(CacheStatusDisplay.LIVE)
            assert "Live" in status_bar.display_content

    async def test_cache_status_cached_display(self) -> None:
        """Cached status should show age in minutes."""
        from textual.app import App, ComposeResult

        from rally_tui.widgets.status_bar import CacheStatusDisplay

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            status_bar.set_cache_status(CacheStatusDisplay.CACHED, age_minutes=5)
            assert "Cached" in status_bar.display_content
            assert "5m" in status_bar.display_content

    async def test_cache_status_refreshing_display(self) -> None:
        """Refreshing status should show loading indicator."""
        from textual.app import App, ComposeResult

        from rally_tui.widgets.status_bar import CacheStatusDisplay

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            status_bar.set_cache_status(CacheStatusDisplay.REFRESHING)
            assert "Refreshing" in status_bar.display_content

    async def test_cache_status_offline_display(self) -> None:
        """Offline status should show warning."""
        from textual.app import App, ComposeResult

        from rally_tui.widgets.status_bar import CacheStatusDisplay

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            status_bar.set_cache_status(CacheStatusDisplay.OFFLINE)
            # Note: "Offline" appears twice - once for cache status, once for connection
            content = status_bar.display_content
            assert "Offline" in content


class TestStatusBarLoading:
    """Tests for loading indicator in StatusBar."""

    def test_default_loading_is_false(self) -> None:
        """Default loading should be False."""
        bar = StatusBar()
        assert bar.loading is False

    def test_set_loading_true(self) -> None:
        """set_loading(True) should set loading to True."""
        bar = StatusBar()
        bar.set_loading(True)
        assert bar.loading is True

    def test_set_loading_false(self) -> None:
        """set_loading(False) should set loading to False."""
        bar = StatusBar()
        bar.set_loading(True)
        bar.set_loading(False)
        assert bar.loading is False

    async def test_loading_indicator_display(self) -> None:
        """Loading indicator should show 'Loading...' when active."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            status_bar.set_loading(True)
            assert "Loading..." in status_bar.display_content

    async def test_loading_indicator_hidden(self) -> None:
        """Loading indicator should be hidden when not loading."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert "Loading..." not in status_bar.display_content

    async def test_loading_clears_on_complete(self) -> None:
        """Loading indicator should clear after setting to False."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            status_bar.set_loading(True)
            assert "Loading..." in status_bar.display_content
            status_bar.set_loading(False)
            assert "Loading..." not in status_bar.display_content
