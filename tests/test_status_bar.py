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

    async def test_status_bar_shows_workspace(self) -> None:
        """StatusBar should display workspace name."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(workspace="My Workspace", id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert status_bar.workspace == "My Workspace"
            # Check the rendered content includes workspace
            assert "My Workspace" in status_bar.display_content

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
        """StatusBar should update display when workspace changes."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield StatusBar(id="status-bar")

        app = TestApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            status_bar.set_workspace("Updated Workspace")
            assert "Updated Workspace" in status_bar.display_content

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
            # Should contain workspace, project, and offline with separators
            assert "Workspace: WS" in content
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
            assert "Workspace: WS" in content
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


class TestStatusBarInApp:
    """Tests for StatusBar integration in the RallyTUI app."""

    async def test_status_bar_exists_in_app(self) -> None:
        """StatusBar should be present in the app."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert status_bar is not None

    async def test_status_bar_shows_workspace_in_app(self) -> None:
        """StatusBar should show workspace name in app."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert "My Workspace" in status_bar.display_content

    async def test_status_bar_shows_project_in_app(self) -> None:
        """StatusBar should show project name in app."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert "My Project" in status_bar.display_content
