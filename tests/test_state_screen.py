"""Tests for StateScreen."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.models import Ticket
from rally_tui.screens import StateScreen
from rally_tui.services import MockRallyClient
from rally_tui.widgets import TicketList


@pytest.fixture
def story_ticket() -> Ticket:
    """A user story ticket for testing.

    Note: Includes parent_id so tests can change to "In-Progress"
    without triggering parent selection flow.
    """
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
        parent_id="F59625",  # Has parent to allow In-Progress transition
    )


@pytest.fixture
def defect_ticket() -> Ticket:
    """A defect ticket for testing."""
    return Ticket(
        formatted_id="DE200",
        name="Test defect",
        ticket_type="Defect",
        state="Open",
        owner="Test User",
        description="Bug description",
        iteration="Sprint 1",
        points=2,
        object_id="234567",
    )


class TestStateScreenCompose:
    """Tests for StateScreen composition."""

    async def test_screen_renders(self, story_ticket: Ticket) -> None:
        """Screen should render without error."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(StateScreen(story_ticket))
            await pilot.pause()

            # Check title is present
            title = app.screen.query_one("#state-title")
            assert "Set State" in str(title.render())
            assert "US100" in str(title.render())

    async def test_screen_shows_current_state(self, story_ticket: Ticket) -> None:
        """Screen should show the current state."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(StateScreen(story_ticket))
            await pilot.pause()

            current = app.screen.query_one("#state-current")
            assert "Defined" in str(current.render())

    async def test_screen_has_state_buttons(self, story_ticket: Ticket) -> None:
        """Screen should have state selection buttons."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(StateScreen(story_ticket))
            await pilot.pause()

            # Check for state buttons
            btn1 = app.screen.query_one("#btn-state-1")
            btn2 = app.screen.query_one("#btn-state-2")
            btn3 = app.screen.query_one("#btn-state-3")
            btn4 = app.screen.query_one("#btn-state-4")
            assert btn1 is not None
            assert btn2 is not None
            assert btn3 is not None
            assert btn4 is not None


class TestStateScreenStoryStates:
    """Tests for User Story state options."""

    async def test_story_has_workflow_states(self, story_ticket: Ticket) -> None:
        """User stories should show workflow states."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            screen = StateScreen(story_ticket)
            app.push_screen(screen)
            await pilot.pause()

            # Check states are workflow states
            assert screen._states == ["Defined", "In-Progress", "Completed", "Accepted"]

    async def test_current_state_button_highlighted(self, story_ticket: Ticket) -> None:
        """Current state button should be highlighted."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(StateScreen(story_ticket))
            await pilot.pause()

            # Defined is the first state, button 1 should be selected
            btn1 = app.screen.query_one("#btn-state-1")
            assert "-selected" in btn1.classes


class TestStateScreenDefectStates:
    """Tests for Defect state options."""

    async def test_defect_has_defect_states(self, defect_ticket: Ticket) -> None:
        """Defects should show defect-specific states."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            screen = StateScreen(defect_ticket)
            app.push_screen(screen)
            await pilot.pause()

            # Check states are defect states
            assert screen._states == ["Submitted", "Open", "Fixed", "Closed"]


class TestStateScreenSelection:
    """Tests for state selection."""

    async def test_click_button_selects_state(self, story_ticket: Ticket) -> None:
        """Clicking a state button should select that state."""
        result = None

        def callback(state: str | None) -> None:
            nonlocal result
            result = state

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(StateScreen(story_ticket), callback=callback)
            await pilot.pause()

            # Click "In-Progress" button (button 2)
            btn2 = app.screen.query_one("#btn-state-2")
            await pilot.click(btn2)
            await pilot.pause()

            assert result == "In-Progress"

    async def test_number_key_selects_state(self, story_ticket: Ticket) -> None:
        """Pressing number key should select corresponding state."""
        result = None

        def callback(state: str | None) -> None:
            nonlocal result
            result = state

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(StateScreen(story_ticket), callback=callback)
            await pilot.pause()

            # Press "3" for Completed
            await pilot.press("3")
            await pilot.pause()

            assert result == "Completed"


class TestStateScreenCancel:
    """Tests for cancel behavior."""

    async def test_escape_cancels(self, story_ticket: Ticket) -> None:
        """Pressing escape should cancel and return None."""
        result = "not_called"

        def callback(state: str | None) -> None:
            nonlocal result
            result = state

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(StateScreen(story_ticket), callback=callback)
            await pilot.pause()

            # Press escape
            await pilot.press("escape")
            await pilot.pause()

            assert result is None


class TestMockClientUpdateState:
    """Tests for MockRallyClient.update_state."""

    def test_update_state_returns_updated_ticket(self, story_ticket: Ticket) -> None:
        """Should return ticket with new state."""
        client = MockRallyClient(tickets=[story_ticket])

        updated = client.update_state(story_ticket, "In-Progress")

        assert updated is not None
        assert updated.state == "In-Progress"
        assert updated.formatted_id == story_ticket.formatted_id

    def test_update_state_modifies_internal_list(self, story_ticket: Ticket) -> None:
        """Should update the ticket in the internal list."""
        client = MockRallyClient(tickets=[story_ticket])

        client.update_state(story_ticket, "Completed")

        # Verify the ticket in the list was updated
        tickets = client.get_tickets()
        assert tickets[0].state == "Completed"

    def test_update_state_nonexistent_ticket(self, story_ticket: Ticket) -> None:
        """Should return None for nonexistent ticket."""
        client = MockRallyClient(tickets=[])

        result = client.update_state(story_ticket, "In-Progress")

        assert result is None


class TestStateIntegration:
    """Integration tests for state change feature."""

    async def test_change_state_updates_list(self, story_ticket: Ticket) -> None:
        """Changing state should update ticket in list."""
        client = MockRallyClient(tickets=[story_ticket])
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            # Open state screen
            await pilot.press("s")
            await pilot.pause()

            # Select "In-Progress" (button 2)
            await pilot.press("2")
            await pilot.pause()

            # Check ticket was updated in list
            ticket_list = app.query_one(TicketList)
            assert ticket_list._tickets[0].state == "In-Progress"

    async def test_cancel_does_not_change_state(self, story_ticket: Ticket) -> None:
        """Cancelling should not change the state."""
        client = MockRallyClient(tickets=[story_ticket])
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            # Open state screen
            await pilot.press("s")
            await pilot.pause()

            # Cancel
            await pilot.press("escape")
            await pilot.pause()

            # Check state unchanged
            ticket_list = app.query_one(TicketList)
            assert ticket_list._tickets[0].state == "Defined"

    async def test_state_change_resorts_list(self) -> None:
        """Changing state should re-sort the ticket list."""
        # Create tickets in different states
        ticket1 = Ticket(
            formatted_id="US100",
            name="First ticket",
            ticket_type="UserStory",
            state="Defined",  # Early state (order 10)
            owner="Test User",
            object_id="100",
        )
        ticket2 = Ticket(
            formatted_id="US200",
            name="Second ticket",
            ticket_type="UserStory",
            state="Completed",  # Late state (order 40)
            owner="Test User",
            object_id="200",
        )

        client = MockRallyClient(tickets=[ticket1, ticket2])
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            # Initially: Defined (US100) should be first, Completed (US200) second
            assert ticket_list._tickets[0].formatted_id == "US100"
            assert ticket_list._tickets[1].formatted_id == "US200"

            # Open state screen for US100
            await pilot.press("s")
            await pilot.pause()

            # Change US100 to "Accepted" (order 50, after Completed)
            await pilot.press("4")  # Accepted is the 4th option
            await pilot.pause()

            # Now: Completed (US200) should be first, Accepted (US100) second
            assert ticket_list._tickets[0].formatted_id == "US200"
            assert ticket_list._tickets[1].formatted_id == "US100"
            assert ticket_list._tickets[1].state == "Accepted"


class TestParentSelectionIntegration:
    """Integration tests for parent selection when moving to In-Progress."""

    async def test_in_progress_without_parent_shows_parent_screen(self) -> None:
        """Moving to In-Progress without parent should show ParentScreen."""
        # Ticket without a parent
        ticket = Ticket(
            formatted_id="US100",
            name="Test story",
            ticket_type="UserStory",
            state="Defined",
            owner="Test User",
            object_id="123456",
        )
        client = MockRallyClient(tickets=[ticket])
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            # Open state screen
            await pilot.press("s")
            await pilot.pause()

            # Select "In-Progress" (button 2)
            await pilot.press("2")
            await pilot.pause()

            # Should now be on ParentScreen
            from rally_tui.screens import ParentScreen

            assert isinstance(app.screen, ParentScreen)

    async def test_in_progress_with_parent_skips_parent_screen(self) -> None:
        """Moving to In-Progress with existing parent should update directly."""
        # Ticket with a parent already set
        ticket = Ticket(
            formatted_id="US100",
            name="Test story",
            ticket_type="UserStory",
            state="Defined",
            owner="Test User",
            object_id="123456",
            parent_id="F59625",  # Has parent
        )
        client = MockRallyClient(tickets=[ticket])
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            # Open state screen
            await pilot.press("s")
            await pilot.pause()

            # Select "In-Progress" (button 2)
            await pilot.press("2")
            await pilot.pause()

            # Should NOT be on ParentScreen (should be back to main screen)
            from rally_tui.screens import ParentScreen

            assert not isinstance(app.screen, ParentScreen)

            # Verify state was updated
            ticket_list = app.query_one(TicketList)
            assert ticket_list._tickets[0].state == "In-Progress"

    async def test_other_states_skip_parent_screen(self) -> None:
        """Changing to other states should not show ParentScreen."""
        ticket = Ticket(
            formatted_id="US100",
            name="Test story",
            ticket_type="UserStory",
            state="Defined",
            owner="Test User",
            object_id="123456",
        )
        client = MockRallyClient(tickets=[ticket])
        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            # Open state screen
            await pilot.press("s")
            await pilot.pause()

            # Select "Completed" (button 3)
            await pilot.press("3")
            await pilot.pause()

            # Should NOT be on ParentScreen
            from rally_tui.screens import ParentScreen

            assert not isinstance(app.screen, ParentScreen)

            # Verify state was updated
            ticket_list = app.query_one(TicketList)
            assert ticket_list._tickets[0].state == "Completed"

    async def test_parent_selection_then_state_update(self, mock_user_settings) -> None:
        """After selecting parent, state should also be updated."""
        ticket = Ticket(
            formatted_id="US100",
            name="Test story",
            ticket_type="UserStory",
            state="Defined",
            owner="Test User",
            object_id="123456",
        )
        client = MockRallyClient(tickets=[ticket])
        app = RallyTUI(client=client, show_splash=False, user_settings=mock_user_settings)
        async with app.run_test() as pilot:
            # Open state screen -> In-Progress -> ParentScreen
            await pilot.press("s")
            await pilot.pause()
            await pilot.press("2")  # In-Progress
            await pilot.pause()

            # Select first parent option
            await pilot.press("1")
            await pilot.pause()

            # Verify both parent and state were updated
            ticket_list = app.query_one(TicketList)
            updated_ticket = ticket_list._tickets[0]
            assert updated_ticket.parent_id == "F59625"
            assert updated_ticket.state == "In-Progress"

    async def test_cancel_parent_selection_cancels_state_change(self, mock_user_settings) -> None:
        """Cancelling parent selection should not change state."""
        ticket = Ticket(
            formatted_id="US100",
            name="Test story",
            ticket_type="UserStory",
            state="Defined",
            owner="Test User",
            object_id="123456",
        )
        client = MockRallyClient(tickets=[ticket])
        app = RallyTUI(client=client, show_splash=False, user_settings=mock_user_settings)
        async with app.run_test() as pilot:
            # Open state screen -> In-Progress -> ParentScreen
            await pilot.press("s")
            await pilot.pause()
            await pilot.press("2")  # In-Progress
            await pilot.pause()

            # Cancel parent selection
            await pilot.press("escape")
            await pilot.pause()

            # Verify state was not changed
            ticket_list = app.query_one(TicketList)
            assert ticket_list._tickets[0].state == "Defined"
            assert ticket_list._tickets[0].parent_id is None

    async def test_custom_parent_id_updates_ticket(self, mock_user_settings) -> None:
        """Entering custom parent ID should set parent and update state."""
        ticket = Ticket(
            formatted_id="US100",
            name="Test story",
            ticket_type="UserStory",
            state="Defined",
            owner="Test User",
            object_id="123456",
        )
        client = MockRallyClient(tickets=[ticket])
        app = RallyTUI(client=client, show_splash=False, user_settings=mock_user_settings)
        async with app.run_test() as pilot:
            # Open state screen -> In-Progress -> ParentScreen
            await pilot.press("s")
            await pilot.pause()
            await pilot.press("2")  # In-Progress
            await pilot.pause()

            # Press 4 for custom input
            await pilot.press("4")
            await pilot.pause()

            # Type custom parent ID
            await pilot.press("f", "9", "9", "9", "9", "9")
            await pilot.press("enter")
            await pilot.pause()

            # Verify custom parent and state were updated
            ticket_list = app.query_one(TicketList)
            updated_ticket = ticket_list._tickets[0]
            assert updated_ticket.parent_id == "F99999"
            assert updated_ticket.state == "In-Progress"
