"""Tests for ticket assignment functionality."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.models import Owner, Ticket
from rally_tui.screens import BulkAction, BulkActionsScreen, OwnerSelectionScreen
from rally_tui.services.owner_utils import extract_owners_from_tickets


class TestIndividualAssignment:
    """Integration tests for individual ticket assignment."""

    async def test_a_key_opens_owner_selection_screen(self) -> None:
        """Pressing 'a' should open the owner selection screen."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("a")
            await pilot.pause()

            assert isinstance(app.screen, OwnerSelectionScreen)

    async def test_owner_screen_shows_title_for_selected_ticket(self) -> None:
        """Owner screen should show the selected ticket ID in title."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("a")
            await pilot.pause()

            # Screen should have ticket ID in title
            assert isinstance(app.screen, OwnerSelectionScreen)
            title_text = app.screen._title
            # Mock client returns tickets starting with US1234, US1235, etc.
            assert "US" in title_text

    async def test_escape_cancels_assignment(self) -> None:
        """Pressing escape should cancel assignment without changes."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("a")
            await pilot.pause()
            assert isinstance(app.screen, OwnerSelectionScreen)

            await pilot.press("escape")
            await pilot.pause()

            # Should return to main screen
            assert not isinstance(app.screen, OwnerSelectionScreen)


class TestBulkAssignment:
    """Integration tests for bulk ticket assignment."""

    async def test_bulk_menu_has_owner_option(self) -> None:
        """Bulk action menu should include Assign Owner option."""
        result: BulkAction | None = None

        def capture_result(action: BulkAction | None) -> None:
            nonlocal result
            result = action

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(BulkActionsScreen(3), callback=capture_result)
            await pilot.pause()
            await pilot.press("5")  # Owner option is now key 5
            await pilot.pause()

        assert result == BulkAction.SET_OWNER

    async def test_bulk_owner_assignment_flow(self) -> None:
        """Full bulk assignment flow should work."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()

            # Select first two tickets
            await pilot.press("space")  # Select first
            await pilot.press("j")
            await pilot.press("space")  # Select second
            await pilot.pause()

            # Open bulk actions menu
            await pilot.press("m")
            await pilot.pause()

            # Press 5 for owner assignment
            await pilot.press("5")
            await pilot.pause()

            # Should show owner selection screen
            assert isinstance(app.screen, OwnerSelectionScreen)


class TestOwnerExtraction:
    """Tests for owner extraction utility."""

    def test_extract_owners_from_tickets_deduplication(self) -> None:
        """Should extract unique owners from tickets."""
        tickets = [
            Ticket(
                formatted_id="US1",
                name="Test 1",
                ticket_type="UserStory",
                state="Defined",
                owner="Alice",
            ),
            Ticket(
                formatted_id="US2",
                name="Test 2",
                ticket_type="UserStory",
                state="Defined",
                owner="Alice",  # Duplicate
            ),
            Ticket(
                formatted_id="US3",
                name="Test 3",
                ticket_type="UserStory",
                state="Defined",
                owner="Bob",
            ),
        ]

        owners = extract_owners_from_tickets(tickets)

        assert len(owners) == 2
        owner_names = {o.display_name for o in owners}
        assert owner_names == {"Alice", "Bob"}

    def test_extract_owners_skips_none(self) -> None:
        """Should skip tickets with no owner."""
        tickets = [
            Ticket(
                formatted_id="US1",
                name="Test 1",
                ticket_type="UserStory",
                state="Defined",
                owner="Alice",
            ),
            Ticket(
                formatted_id="US2",
                name="Test 2",
                ticket_type="UserStory",
                state="Defined",
                owner=None,
            ),
        ]

        owners = extract_owners_from_tickets(tickets)

        assert len(owners) == 1
        assert next(iter(owners)).display_name == "Alice"

    def test_extract_owners_creates_temp_ids(self) -> None:
        """Extracted owners should have TEMP: prefix on object_id."""
        tickets = [
            Ticket(
                formatted_id="US1",
                name="Test 1",
                ticket_type="UserStory",
                state="Defined",
                owner="Alice",
            ),
        ]

        owners = extract_owners_from_tickets(tickets)
        owner = next(iter(owners))

        assert owner.object_id.startswith("TEMP:")
        assert owner.object_id == "TEMP:Alice"


class TestOwnerSelectionScreen:
    """Tests for owner selection screen behavior."""

    @pytest.fixture
    def sample_owners(self) -> set[Owner]:
        """Create sample owners for testing."""
        return {
            Owner(object_id="123", display_name="Alice", user_name="alice@test.com"),
            Owner(object_id="456", display_name="Bob", user_name="bob@test.com"),
            Owner(object_id="789", display_name="Carol", user_name=None),
        }

    async def test_owners_sorted_alphabetically(self, sample_owners: set[Owner]) -> None:
        """Owners should be sorted by display name."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            screen = OwnerSelectionScreen(owners=sample_owners, title="Test")
            app.push_screen(screen)
            await pilot.pause()

            # Check internal sorted list
            assert screen._owners[0].display_name == "Alice"
            assert screen._owners[1].display_name == "Bob"
            assert screen._owners[2].display_name == "Carol"

    async def test_enter_selects_owner(self, sample_owners: set[Owner]) -> None:
        """Pressing enter should select highlighted owner."""
        result: Owner | None = None

        def capture_result(owner: Owner | None) -> None:
            nonlocal result
            result = owner

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            screen = OwnerSelectionScreen(owners=sample_owners, title="Test")
            app.push_screen(screen, callback=capture_result)
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

        assert result is not None
        assert result.display_name == "Alice"  # First in sorted order

    async def test_navigation_changes_selection(self, sample_owners: set[Owner]) -> None:
        """J/K keys should navigate the owner list."""
        result: Owner | None = None

        def capture_result(owner: Owner | None) -> None:
            nonlocal result
            result = owner

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            screen = OwnerSelectionScreen(owners=sample_owners, title="Test")
            app.push_screen(screen, callback=capture_result)
            await pilot.pause()
            await pilot.press("j")  # Move to Bob
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

        assert result is not None
        assert result.display_name == "Bob"


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    async def test_assignment_with_no_ticket_selected(self) -> None:
        """Assignment should handle no ticket selected gracefully."""
        # This is an integration test - behavior depends on focus state
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            # Press 'a' - should not crash even if no ticket is properly focused
            await pilot.press("a")
            await pilot.pause()
            # App should still be responsive
            assert app.is_running

    async def test_empty_owner_list(self) -> None:
        """Owner screen should handle empty owner list."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            screen = OwnerSelectionScreen(owners=set(), title="Empty Test")
            app.push_screen(screen)
            await pilot.pause()

            # Should render without error
            assert isinstance(app.screen, OwnerSelectionScreen)
            assert len(screen._owners) == 0

            # Escape should still work
            await pilot.press("escape")
            await pilot.pause()
            assert not isinstance(app.screen, OwnerSelectionScreen)
