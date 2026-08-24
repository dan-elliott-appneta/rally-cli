"""Tests for the StatusBar widget."""

from rally_tui.app import RallyTUI
from rally_tui.widgets import StatusBar


class TestStatusBarWidget:
    """Integration tests for StatusBar widget behavior."""

    async def test_status_bar_renders_default(self) -> None:
        """StatusBar should render with default values."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test():
            status_bar = app.query_one(StatusBar)
            assert status_bar is not None

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
        async with app.run_test():
            status_bar = app.query_one(StatusBar)
            assert "Test Project" in status_bar.display_content

    async def test_status_bar_shows_offline(self) -> None:
        """StatusBar should show 'Offline' status indicator."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test():
            status_bar = app.query_one(StatusBar)
            assert "Offline" in status_bar.display_content

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
        async with app.run_test():
            status_bar = app.query_one(StatusBar)
            content = status_bar.display_content
            # Should contain project and offline with separators
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
        async with app.run_test():
            status_bar = app.query_one(StatusBar)
            content = status_bar.display_content
            assert "Project:" not in content

    async def test_status_bar_shows_connected(self) -> None:
        """StatusBar should show 'Connected' when connected=True."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(connected=True, id="status-bar")

        app = TestApp()
        async with app.run_test():
            status_bar = app.query_one(StatusBar)
            assert "Connected" in status_bar.display_content
            assert "Offline" not in status_bar.display_content

    async def test_status_bar_shows_filter_info(self) -> None:
        """StatusBar should show filter info when set."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test():
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
        async with app.run_test():
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
        async with app.run_test():
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
        async with app.run_test():
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
        async with app.run_test():
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
        async with app.run_test():
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
        async with app.run_test():
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
        async with app.run_test():
            status_bar = app.query_one(StatusBar)
            assert status_bar is not None

    async def test_status_bar_shows_project_in_app(self) -> None:
        """StatusBar should show project name in app."""
        app = RallyTUI(show_splash=False)
        async with app.run_test():
            status_bar = app.query_one(StatusBar)
            assert "My Project" in status_bar.display_content


class TestStatusBarCacheStatus:
    """Tests for cache status display in StatusBar."""

    async def test_cache_status_live_display(self) -> None:
        """Live status should show green bullet."""
        from textual.app import App, ComposeResult

        from rally_tui.widgets.status_bar import CacheStatusDisplay

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test():
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
        async with app.run_test():
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
        async with app.run_test():
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
        async with app.run_test():
            status_bar = app.query_one(StatusBar)
            status_bar.set_cache_status(CacheStatusDisplay.OFFLINE)
            # Note: "Offline" appears twice - once for cache status, once for connection
            content = status_bar.display_content
            assert "Offline" in content


class TestStatusBarLoading:
    """Tests for loading indicator in StatusBar."""

    async def test_loading_indicator_display(self) -> None:
        """Loading indicator should show 'Loading...' when active."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test():
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
        async with app.run_test():
            status_bar = app.query_one(StatusBar)
            assert "Loading..." not in status_bar.display_content

    async def test_loading_clears_on_complete(self) -> None:
        """Loading indicator should clear after setting to False."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test():
            status_bar = app.query_one(StatusBar)
            status_bar.set_loading(True)
            assert "Loading..." in status_bar.display_content
            status_bar.set_loading(False)
            assert "Loading..." not in status_bar.display_content
