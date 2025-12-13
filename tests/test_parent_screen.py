"""Tests for ParentScreen."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.models import Ticket
from rally_tui.screens import ParentOption, ParentScreen


@pytest.fixture
def ticket() -> Ticket:
    """A ticket for testing."""
    return Ticket(
        formatted_id="US100",
        name="Test story",
        ticket_type="UserStory",
        state="Defined",
        owner="Test User",
        description="Test description",
        iteration="Sprint 1",
        points=3,
        object_id="123456",
    )


@pytest.fixture
def parent_options() -> list[ParentOption]:
    """Sample parent options for testing."""
    return [
        ParentOption("F59625", "API Platform Modernization Initiative"),
        ParentOption("F59627", "Customer Portal Enhancement Phase 2"),
        ParentOption("F59628", "Infrastructure Reliability Improvements"),
    ]


class TestParentOption:
    """Tests for ParentOption dataclass."""

    def test_truncated_name_short(self) -> None:
        """Short names should not be truncated."""
        option = ParentOption("F100", "Short Name")
        assert option.truncated_name == "Short Name"

    def test_truncated_name_long(self) -> None:
        """Long names should be truncated with ellipsis."""
        option = ParentOption(
            "F100", "This is a very long feature name that exceeds the maximum length"
        )
        truncated = option.truncated_name
        assert len(truncated) <= 35
        assert truncated.endswith("...")

    def test_display_text(self) -> None:
        """Display text should include index, ID, and name."""
        option = ParentOption("F59625", "Feature Name")
        display = option.display_text(1)
        assert "1." in display
        assert "F59625" in display
        assert "Feature Name" in display


class TestParentScreenCompose:
    """Tests for ParentScreen composition."""

    async def test_screen_renders(self, ticket: Ticket, parent_options: list[ParentOption]) -> None:
        """Screen should render without error."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(ParentScreen(ticket, parent_options))
            await pilot.pause()

            # Check title is present
            title = app.screen.query_one("#parent-title")
            assert "Select Parent Feature" in str(title.render())
            assert "US100" in str(title.render())

    async def test_screen_shows_info_message(
        self, ticket: Ticket, parent_options: list[ParentOption]
    ) -> None:
        """Screen should show info message about parent requirement."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(ParentScreen(ticket, parent_options))
            await pilot.pause()

            info = app.screen.query_one("#parent-info")
            assert "parent" in str(info.render()).lower()

    async def test_screen_shows_buttons(
        self, ticket: Ticket, parent_options: list[ParentOption]
    ) -> None:
        """Screen should show buttons for parent options."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(ParentScreen(ticket, parent_options))
            await pilot.pause()

            btn1 = app.screen.query_one("#btn-parent-1")
            assert "F59625" in str(btn1.render())

            btn2 = app.screen.query_one("#btn-parent-2")
            assert "F59627" in str(btn2.render())

            btn3 = app.screen.query_one("#btn-parent-3")
            assert "F59628" in str(btn3.render())

    async def test_screen_shows_custom_button(
        self, ticket: Ticket, parent_options: list[ParentOption]
    ) -> None:
        """Screen should show button for custom ID entry."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(ParentScreen(ticket, parent_options))
            await pilot.pause()

            custom_btn = app.screen.query_one("#btn-parent-custom")
            assert "custom" in str(custom_btn.render()).lower()


class TestParentScreenSelection:
    """Tests for ParentScreen selection behavior."""

    async def test_number_key_1_selects_first(
        self, ticket: Ticket, parent_options: list[ParentOption]
    ) -> None:
        """Pressing 1 should select first parent."""
        app = RallyTUI(show_splash=False)
        result = None

        def capture_result(value: str | None) -> None:
            nonlocal result
            result = value

        async with app.run_test() as pilot:
            app.push_screen(ParentScreen(ticket, parent_options), capture_result)
            await pilot.pause()
            await pilot.press("1")
            await pilot.pause()

        assert result == "F59625"

    async def test_number_key_2_selects_second(
        self, ticket: Ticket, parent_options: list[ParentOption]
    ) -> None:
        """Pressing 2 should select second parent."""
        app = RallyTUI(show_splash=False)
        result = None

        def capture_result(value: str | None) -> None:
            nonlocal result
            result = value

        async with app.run_test() as pilot:
            app.push_screen(ParentScreen(ticket, parent_options), capture_result)
            await pilot.pause()
            await pilot.press("2")
            await pilot.pause()

        assert result == "F59627"

    async def test_number_key_3_selects_third(
        self, ticket: Ticket, parent_options: list[ParentOption]
    ) -> None:
        """Pressing 3 should select third parent."""
        app = RallyTUI(show_splash=False)
        result = None

        def capture_result(value: str | None) -> None:
            nonlocal result
            result = value

        async with app.run_test() as pilot:
            app.push_screen(ParentScreen(ticket, parent_options), capture_result)
            await pilot.pause()
            await pilot.press("3")
            await pilot.pause()

        assert result == "F59628"

    async def test_escape_cancels(self, ticket: Ticket, parent_options: list[ParentOption]) -> None:
        """Pressing Escape should cancel and return None."""
        app = RallyTUI(show_splash=False)
        result = "not_set"  # Use sentinel value

        def capture_result(value: str | None) -> None:
            nonlocal result
            result = value

        async with app.run_test() as pilot:
            app.push_screen(ParentScreen(ticket, parent_options), capture_result)
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

        assert result is None


class TestParentScreenCustomInput:
    """Tests for ParentScreen custom input functionality."""

    async def test_number_key_4_shows_input(
        self, ticket: Ticket, parent_options: list[ParentOption]
    ) -> None:
        """Pressing 4 should show custom input field."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(ParentScreen(ticket, parent_options))
            await pilot.pause()
            await pilot.press("4")
            await pilot.pause()

            input_field = app.screen.query_one("#custom-input")
            assert "visible" in input_field.classes

    async def test_custom_input_submission(
        self, ticket: Ticket, parent_options: list[ParentOption]
    ) -> None:
        """Submitting custom input should return the entered ID."""
        app = RallyTUI(show_splash=False)
        result = None

        def capture_result(value: str | None) -> None:
            nonlocal result
            result = value

        async with app.run_test() as pilot:
            app.push_screen(ParentScreen(ticket, parent_options), capture_result)
            await pilot.pause()
            await pilot.press("4")  # Show custom input
            await pilot.pause()
            # Type custom ID and submit
            await pilot.press("f", "1", "2", "3", "4", "5")
            await pilot.press("enter")
            await pilot.pause()

        assert result == "F12345"

    async def test_custom_input_uppercases(
        self, ticket: Ticket, parent_options: list[ParentOption]
    ) -> None:
        """Custom input should be uppercased."""
        app = RallyTUI(show_splash=False)
        result = None

        def capture_result(value: str | None) -> None:
            nonlocal result
            result = value

        async with app.run_test() as pilot:
            app.push_screen(ParentScreen(ticket, parent_options), capture_result)
            await pilot.pause()
            await pilot.press("4")
            await pilot.pause()
            await pilot.press("f", "9", "9")
            await pilot.press("enter")
            await pilot.pause()

        assert result == "F99"


class TestParentScreenProperties:
    """Tests for ParentScreen properties."""

    def test_ticket_property(self, ticket: Ticket, parent_options: list[ParentOption]) -> None:
        """Screen should expose ticket property."""
        screen = ParentScreen(ticket, parent_options)
        assert screen.ticket == ticket
        assert screen.ticket.formatted_id == "US100"
