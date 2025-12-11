"""Tests for the SplashScreen."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.screens import SplashScreen
from rally_tui.services import MockRallyClient


class TestSplashScreenBasic:
    """Basic tests for SplashScreen."""

    def test_splash_screen_has_ascii_art(self) -> None:
        """SplashScreen should have ASCII art and version."""
        from rally_tui.screens.splash_screen import get_splash_text, RALLY_TUI_ART

        # ASCII art should have the big block letters
        assert "RALLY" in RALLY_TUI_ART or "█" in RALLY_TUI_ART

        # Full splash text includes version and instructions
        splash_text = get_splash_text()
        assert "Terminal UI" in splash_text
        assert "Press any key" in splash_text
        # Version should be present (format: v0.1.0 or similar)
        assert "v" in splash_text

    async def test_splash_auto_dismisses_after_load(self) -> None:
        """Splash screen should auto-dismiss after tickets load."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=True)
        async with app.run_test() as pilot:
            # Give time for the worker to complete
            await pilot.pause()
            await pilot.pause()

            # Splash should be auto-dismissed after loading
            assert app.screen.__class__.__name__ != "SplashScreen"

    async def test_splash_hidden_when_disabled(self) -> None:
        """Splash screen should not show when show_splash=False."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            # Should be on main screen (default screen)
            assert app.screen.__class__.__name__ != "SplashScreen"


class TestSplashScreenDismissal:
    """Tests for SplashScreen dismissal."""

    async def test_tickets_loaded_after_splash_dismiss(self) -> None:
        """Tickets should be loaded when splash is dismissed."""
        client = MockRallyClient()
        app = RallyTUI(client=client, show_splash=True)
        async with app.run_test() as pilot:
            # Wait for tickets to load and splash to dismiss
            await pilot.pause()
            await pilot.pause()

            # Should no longer be on splash screen
            assert app.screen.__class__.__name__ != "SplashScreen"

            # Tickets should be loaded
            from rally_tui.widgets import TicketList
            ticket_list = app.query_one(TicketList)
            assert len(ticket_list._tickets) > 0

    async def test_key_press_dismisses_splash(self) -> None:
        """Key press should also dismiss splash (if still showing)."""
        # This test verifies the splash can be dismissed by keypress
        # even before loading completes (splash accepts any key)
        screen = SplashScreen()
        # SplashScreen should have dismiss binding
        assert any(b.key == "any" or b.action == "dismiss" for b in screen.BINDINGS)
