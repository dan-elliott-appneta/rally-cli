"""Tests for the StatusBar widget."""

import pytest

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
