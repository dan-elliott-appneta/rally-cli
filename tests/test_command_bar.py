"""Tests for the CommandBar widget."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.widgets import CommandBar, TicketDetail, TicketList


class TestCommandBarWidget:
    """Tests for CommandBar widget behavior."""

    async def test_command_bar_exists(self) -> None:
        """CommandBar should be present in the app."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            command_bar = app.query_one(CommandBar)
            assert command_bar is not None

    async def test_initial_context_is_list(self) -> None:
        """CommandBar should start with 'list' context."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            command_bar = app.query_one(CommandBar)
            assert command_bar.context == "list"

    async def test_shows_list_commands_initially(self) -> None:
        """CommandBar should show list commands on startup."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            command_bar = app.query_one(CommandBar)
            # Context should be list
            assert command_bar.context == "list"
            # Verify the list context has expected commands
            list_commands = CommandBar.CONTEXTS["list"]
            assert "Create" in list_commands
            assert "Points" in list_commands
            assert "Notes" in list_commands

    async def test_context_changes_on_tab(self) -> None:
        """Pressing Tab should change context to 'detail'."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            command_bar = app.query_one(CommandBar)
            assert command_bar.context == "list"

            await pilot.press("tab")
            assert command_bar.context == "detail"

    async def test_context_toggles_back_on_second_tab(self) -> None:
        """Pressing Tab twice should return to 'list' context."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            command_bar = app.query_one(CommandBar)

            await pilot.press("tab")
            assert command_bar.context == "detail"

            await pilot.press("tab")
            assert command_bar.context == "list"

    async def test_detail_context_shows_similar_commands(self) -> None:
        """Detail context should show similar commands to list context."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            command_bar = app.query_one(CommandBar)

            # Verify list context has action commands
            assert command_bar.context == "list"
            list_commands = CommandBar.CONTEXTS["list"]
            assert "Create" in list_commands

            await pilot.press("tab")

            # Verify detail context has same action commands
            assert command_bar.context == "detail"
            detail_commands = CommandBar.CONTEXTS["detail"]
            assert "Create" in detail_commands
            assert "Points" in detail_commands
            assert "Notes" in detail_commands
            # Should have Tab and quit
            assert "Tab" in detail_commands
            assert "q" in detail_commands

    async def test_focus_switches_with_tab(self) -> None:
        """Tab should switch focus between list and detail panels."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            ticket_detail = app.query_one(TicketDetail)

            # List has focus initially
            assert ticket_list.has_focus

            await pilot.press("tab")
            # Detail should now have focus
            assert ticket_detail.has_focus

            await pilot.press("tab")
            # Back to list
            assert ticket_list.has_focus


class TestCommandBarUnit:
    """Unit tests for CommandBar widget in isolation."""

    def test_contexts_dict_has_list_and_detail(self) -> None:
        """CONTEXTS should have 'list', 'detail', and 'search' keys."""
        assert "list" in CommandBar.CONTEXTS
        assert "detail" in CommandBar.CONTEXTS
        assert "search" in CommandBar.CONTEXTS

    def test_list_context_has_action_commands(self) -> None:
        """List context should include action keys."""
        list_commands = CommandBar.CONTEXTS["list"]
        assert "[c] Create" in list_commands
        assert "[p] Points" in list_commands
        assert "[n] Notes" in list_commands
        assert "[d] Discuss" in list_commands
        assert "Search" in list_commands
        assert "[q] Quit" in list_commands

    def test_detail_context_has_action_commands(self) -> None:
        """Detail context should have action commands and Tab."""
        detail_commands = CommandBar.CONTEXTS["detail"]
        assert "[c] Create" in detail_commands
        assert "[p] Points" in detail_commands
        assert "[n] Notes" in detail_commands
        assert "[d] Discuss" in detail_commands
        assert "[Tab] Switch" in detail_commands
        assert "[q] Quit" in detail_commands

    def test_set_context_updates_internal_state(self) -> None:
        """set_context should update the internal context."""
        bar = CommandBar()
        assert bar.context == "list"

        bar.set_context("detail")
        assert bar.context == "detail"

        bar.set_context("list")
        assert bar.context == "list"

    def test_initial_context_parameter(self) -> None:
        """Constructor should accept initial context."""
        bar = CommandBar(context="detail")
        assert bar.context == "detail"

        bar2 = CommandBar(context="list")
        assert bar2.context == "list"

    def test_unknown_context_returns_empty(self) -> None:
        """Unknown context should return empty string."""
        bar = CommandBar()
        bar.set_context("unknown")
        assert bar.context == "unknown"
        # The CONTEXTS.get() returns empty string for unknown keys
        assert CommandBar.CONTEXTS.get("unknown", "") == ""

    def test_list_context_has_search_key(self) -> None:
        """List context should include search key."""
        list_commands = CommandBar.CONTEXTS["list"]
        assert "Search" in list_commands
        # The / is escaped as \\[/\\] for rich markup
        assert "[/]" in list_commands or "\\[/\\]" in list_commands

    def test_search_context_has_instructions(self) -> None:
        """Search context should have Enter, Esc, and type instruction."""
        search_commands = CommandBar.CONTEXTS["search"]
        assert "Enter" in search_commands
        assert "Esc" in search_commands
        assert "filter" in search_commands.lower()
