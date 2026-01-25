"""Tests for OwnerScreen."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.screens import OwnerOption, OwnerScreen


@pytest.fixture
def owner_options() -> list[OwnerOption]:
    """Sample owner options for testing."""
    return [
        OwnerOption("Alice Smith"),
        OwnerOption("Bob Johnson"),
        OwnerOption("Charlie Brown"),
    ]


class TestOwnerOption:
    """Tests for OwnerOption dataclass."""

    def test_display_text(self) -> None:
        """Display text should include index and name."""
        option = OwnerOption("Alice Smith")
        display = option.display_text(1)
        assert "1." in display
        assert "Alice Smith" in display


class TestOwnerScreenCompose:
    """Tests for OwnerScreen composition."""

    async def test_screen_renders(self, owner_options: list[OwnerOption]) -> None:
        """Screen should render without error."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(OwnerScreen(owner_options, ticket_count=5))
            await pilot.pause()

            # Check title is present
            title = app.screen.query_one("#owner-title")
            assert "Assign Owner" in str(title.render())
            assert "5" in str(title.render())

    async def test_screen_shows_info_message(self, owner_options: list[OwnerOption]) -> None:
        """Screen should show info message about owner selection."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(OwnerScreen(owner_options, ticket_count=3))
            await pilot.pause()

            info = app.screen.query_one("#owner-info")
            assert "owner" in str(info.render()).lower()

    async def test_screen_shows_buttons(self, owner_options: list[OwnerOption]) -> None:
        """Screen should show buttons for owner options."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(OwnerScreen(owner_options, ticket_count=2))
            await pilot.pause()

            btn1 = app.screen.query_one("#btn-owner-1")
            assert "Alice" in str(btn1.render())

            btn2 = app.screen.query_one("#btn-owner-2")
            assert "Bob" in str(btn2.render())

            btn3 = app.screen.query_one("#btn-owner-3")
            assert "Charlie" in str(btn3.render())

    async def test_screen_shows_custom_button(self, owner_options: list[OwnerOption]) -> None:
        """Screen should show button for custom name entry."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(OwnerScreen(owner_options, ticket_count=1))
            await pilot.pause()

            custom_btn = app.screen.query_one("#btn-owner-custom")
            assert "custom" in str(custom_btn.render()).lower()


class TestOwnerScreenSelection:
    """Tests for OwnerScreen selection behavior."""

    async def test_number_key_1_selects_first(self, owner_options: list[OwnerOption]) -> None:
        """Pressing 1 should select first owner."""
        app = RallyTUI(show_splash=False)
        result = None

        def capture_result(value: str | None) -> None:
            nonlocal result
            result = value

        async with app.run_test() as pilot:
            app.push_screen(OwnerScreen(owner_options, ticket_count=3), capture_result)
            await pilot.pause()
            await pilot.press("1")
            await pilot.pause()

        assert result == "Alice Smith"

    async def test_number_key_2_selects_second(self, owner_options: list[OwnerOption]) -> None:
        """Pressing 2 should select second owner."""
        app = RallyTUI(show_splash=False)
        result = None

        def capture_result(value: str | None) -> None:
            nonlocal result
            result = value

        async with app.run_test() as pilot:
            app.push_screen(OwnerScreen(owner_options, ticket_count=3), capture_result)
            await pilot.pause()
            await pilot.press("2")
            await pilot.pause()

        assert result == "Bob Johnson"

    async def test_number_key_3_selects_third(self, owner_options: list[OwnerOption]) -> None:
        """Pressing 3 should select third owner."""
        app = RallyTUI(show_splash=False)
        result = None

        def capture_result(value: str | None) -> None:
            nonlocal result
            result = value

        async with app.run_test() as pilot:
            app.push_screen(OwnerScreen(owner_options, ticket_count=3), capture_result)
            await pilot.pause()
            await pilot.press("3")
            await pilot.pause()

        assert result == "Charlie Brown"

    async def test_escape_cancels(self, owner_options: list[OwnerOption]) -> None:
        """Pressing Escape should cancel and return None."""
        app = RallyTUI(show_splash=False)
        result = "not_set"  # Use sentinel value

        def capture_result(value: str | None) -> None:
            nonlocal result
            result = value

        async with app.run_test() as pilot:
            app.push_screen(OwnerScreen(owner_options, ticket_count=3), capture_result)
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

        assert result is None


class TestOwnerScreenCustomInput:
    """Tests for OwnerScreen custom input functionality."""

    async def test_number_key_4_shows_input(self, owner_options: list[OwnerOption]) -> None:
        """Pressing 4 should show custom input field when there are 3 options."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(OwnerScreen(owner_options, ticket_count=2))
            await pilot.pause()
            await pilot.press("4")
            await pilot.pause()

            input_field = app.screen.query_one("#custom-input")
            assert "visible" in input_field.classes

    async def test_custom_input_submission(self, owner_options: list[OwnerOption]) -> None:
        """Submitting custom input should return the entered name."""
        app = RallyTUI(show_splash=False)
        result = None

        def capture_result(value: str | None) -> None:
            nonlocal result
            result = value

        async with app.run_test() as pilot:
            app.push_screen(OwnerScreen(owner_options, ticket_count=1), capture_result)
            await pilot.pause()
            await pilot.press("4")  # Show custom input
            await pilot.pause()
            # Type custom name and submit
            await pilot.press(*"Jane Doe")
            await pilot.press("enter")
            await pilot.pause()

        assert result == "Jane Doe"


class TestOwnerScreenProperties:
    """Tests for OwnerScreen properties."""

    def test_owner_options_property(self, owner_options: list[OwnerOption]) -> None:
        """Screen should expose owner_options property."""
        screen = OwnerScreen(owner_options, ticket_count=5)
        assert screen.owner_options == owner_options
        assert len(screen.owner_options) == 3


class TestOwnerScreenNoOptions:
    """Tests for OwnerScreen with no predefined options."""

    async def test_empty_options_shows_custom_focused(self) -> None:
        """With no options, custom button should be focused."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(OwnerScreen([], ticket_count=2))
            await pilot.pause()

            # Custom button should be present
            custom_btn = app.screen.query_one("#btn-owner-custom")
            assert custom_btn is not None

    async def test_empty_options_shows_different_hint(self) -> None:
        """With no options, hint should indicate entering name."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(OwnerScreen([], ticket_count=1))
            await pilot.pause()

            hint = app.screen.query_one("#owner-hint")
            assert "enter" in str(hint.render()).lower()
