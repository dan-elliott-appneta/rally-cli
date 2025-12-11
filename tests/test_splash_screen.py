"""Tests for the SplashScreen."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.screens import SplashScreen


class TestSplashScreenBasic:
    """Basic tests for SplashScreen."""

    def test_splash_screen_has_ascii_art(self) -> None:
        """SplashScreen should have ASCII art."""
        from rally_tui.screens.splash_screen import RALLY_TUI_ART

        assert "Terminal UI" in RALLY_TUI_ART
        assert "Rally" in RALLY_TUI_ART
        assert "Press any key" in RALLY_TUI_ART

    async def test_splash_shows_on_startup(self) -> None:
        """Splash screen should show on app startup when enabled."""
        app = RallyTUI(show_splash=True)
        async with app.run_test() as pilot:
            # Splash screen should be the active screen
            assert app.screen.__class__.__name__ == "SplashScreen"

    async def test_splash_hidden_when_disabled(self) -> None:
        """Splash screen should not show when show_splash=False."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            # Should be on main screen (default screen)
            assert app.screen.__class__.__name__ != "SplashScreen"


class TestSplashScreenDismissal:
    """Tests for SplashScreen dismissal."""

    async def test_key_press_dismisses_splash(self) -> None:
        """Any key press should dismiss the splash screen."""
        app = RallyTUI(show_splash=True)
        async with app.run_test() as pilot:
            # Verify we're on splash screen
            assert app.screen.__class__.__name__ == "SplashScreen"

            # Press a key to dismiss
            await pilot.press("space")
            await pilot.pause()

            # Should no longer be on splash screen
            assert app.screen.__class__.__name__ != "SplashScreen"

    async def test_escape_dismisses_splash(self) -> None:
        """Escape should dismiss the splash screen."""
        app = RallyTUI(show_splash=True)
        async with app.run_test() as pilot:
            assert app.screen.__class__.__name__ == "SplashScreen"

            await pilot.press("escape")
            await pilot.pause()

            assert app.screen.__class__.__name__ != "SplashScreen"

    async def test_enter_dismisses_splash(self) -> None:
        """Enter should dismiss the splash screen."""
        app = RallyTUI(show_splash=True)
        async with app.run_test() as pilot:
            assert app.screen.__class__.__name__ == "SplashScreen"

            await pilot.press("enter")
            await pilot.pause()

            assert app.screen.__class__.__name__ != "SplashScreen"
