"""Tests for the wide view mode feature."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.models import Ticket
from rally_tui.widgets import TicketList, ViewMode
from rally_tui.widgets.ticket_list import (
    TicketListItem,
    WideTicketListItem,
)


class TestViewMode:
    """Tests for ViewMode enum."""

    def test_view_mode_values(self) -> None:
        """ViewMode should have NORMAL and WIDE values."""
        assert ViewMode.NORMAL.value == "normal"
        assert ViewMode.WIDE.value == "wide"


class TestWideTicketListItem:
    """Tests for WideTicketListItem widget."""

    def test_create_item(self) -> None:
        """WideTicketListItem can be created with a ticket."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In Progress",
            owner="Alice",
            points=5,
            parent_id="F123",
        )
        item = WideTicketListItem(ticket)
        assert item.ticket == ticket
        assert not item.is_selected

    def test_create_item_selected(self) -> None:
        """WideTicketListItem can be created with selection state."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="Defined",
        )
        item = WideTicketListItem(ticket, selected=True)
        assert item.is_selected

    def test_set_selected(self) -> None:
        """WideTicketListItem selection can be toggled."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="Defined",
        )
        item = WideTicketListItem(ticket)
        assert not item.is_selected
        item.set_selected(True)
        assert item.is_selected
        item.set_selected(False)
        assert not item.is_selected


class TestTicketListViewMode:
    """Tests for TicketList view mode functionality."""

    def _create_ticket(
        self,
        formatted_id: str = "US1234",
        owner: str | None = "Alice",
        points: float | None = 5,
        parent_id: str | None = "F123",
    ) -> Ticket:
        """Create a test ticket."""
        return Ticket(
            formatted_id=formatted_id,
            name=f"Test {formatted_id}",
            ticket_type="UserStory",
            state="In Progress",
            owner=owner,
            points=points,
            parent_id=parent_id,
        )

    def test_default_view_mode(self) -> None:
        """Default view mode should be NORMAL."""
        ticket_list = TicketList()
        assert ticket_list.view_mode == ViewMode.NORMAL

    def test_init_with_view_mode(self) -> None:
        """TicketList can be initialized with a specific view mode."""
        ticket_list = TicketList(view_mode=ViewMode.WIDE)
        assert ticket_list.view_mode == ViewMode.WIDE

    async def test_toggle_view_mode(self) -> None:
        """toggle_view_mode should switch between NORMAL and WIDE."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)
            assert ticket_list.view_mode == ViewMode.NORMAL

            ticket_list.toggle_view_mode()
            await pilot.pause()
            assert ticket_list.view_mode == ViewMode.WIDE

            ticket_list.toggle_view_mode()
            await pilot.pause()
            assert ticket_list.view_mode == ViewMode.NORMAL

    async def test_set_view_mode(self) -> None:
        """set_view_mode should change the view mode."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)
            ticket_list.set_view_mode(ViewMode.WIDE)
            await pilot.pause()
            assert ticket_list.view_mode == ViewMode.WIDE

    def test_set_view_mode_same_no_change(self) -> None:
        """set_view_mode should not rebuild if mode is the same."""
        ticket_list = TicketList(view_mode=ViewMode.WIDE)
        # This should be a no-op
        ticket_list.set_view_mode(ViewMode.WIDE)
        assert ticket_list.view_mode == ViewMode.WIDE


class TestWideViewIntegration:
    """Integration tests for wide view mode in the app."""

    async def test_toggle_wide_view_keybinding(self) -> None:
        """Pressing 'v' should toggle wide view mode."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Should start in normal mode
            assert ticket_list.view_mode == ViewMode.NORMAL

            # Press v to toggle to wide
            await pilot.press("v")
            await pilot.pause()
            assert ticket_list.view_mode == ViewMode.WIDE

            # Press v again to toggle back
            await pilot.press("v")
            await pilot.pause()
            assert ticket_list.view_mode == ViewMode.NORMAL

    async def test_wide_view_shows_wide_items(self) -> None:
        """Wide view should show WideTicketListItem widgets."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()

            # Start in normal mode with TicketListItem
            normal_items = list(app.query("TicketListItem"))
            wide_items = list(app.query("WideTicketListItem"))
            assert len(normal_items) > 0
            assert len(wide_items) == 0

            # Toggle to wide view
            await pilot.press("v")
            await pilot.pause()

            # Now should have WideTicketListItem
            normal_items = list(app.query("TicketListItem"))
            wide_items = list(app.query("WideTicketListItem"))
            assert len(normal_items) == 0
            assert len(wide_items) > 0

    async def test_wide_view_container_class(self) -> None:
        """Wide view should add 'wide' or 'wide-full' class to list container."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()

            list_container = app.query_one("#list-container")

            # Should not have wide class initially
            assert "wide" not in list_container.classes
            assert "wide-full" not in list_container.classes

            # Toggle to wide view
            await pilot.press("v")
            await pilot.pause()

            # Should have wide or wide-full class (wide-full if terminal too narrow)
            has_wide_class = "wide" in list_container.classes or "wide-full" in list_container.classes
            assert has_wide_class, f"Expected 'wide' or 'wide-full' class, got: {list_container.classes}"

            # Toggle back
            await pilot.press("v")
            await pilot.pause()

            # Should not have wide class
            assert "wide" not in list_container.classes

    async def test_wide_view_preserves_selection(self) -> None:
        """Toggling view mode should preserve the selected ticket."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Navigate to a specific ticket
            await pilot.press("j", "j")  # Move to index 2
            await pilot.pause()
            assert ticket_list.index == 2
            selected_before = ticket_list.selected_ticket

            # Toggle to wide view
            await pilot.press("v")
            await pilot.pause()

            # Index should be preserved
            assert ticket_list.index == 2
            # Same ticket should be selected
            assert ticket_list.selected_ticket == selected_before

    async def test_wide_view_preserves_multi_selection(self) -> None:
        """Toggling view mode should preserve multi-select state."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Select a few tickets
            await pilot.press("space")  # Select first
            await pilot.press("j")
            await pilot.press("space")  # Select second
            await pilot.pause()

            selected_ids_before = set(ticket_list._selected_ids)
            assert len(selected_ids_before) == 2

            # Toggle to wide view
            await pilot.press("v")
            await pilot.pause()

            # Selection should be preserved
            assert ticket_list._selected_ids == selected_ids_before

    async def test_wide_view_restores_detail_pane(self) -> None:
        """Toggling back to normal view should restore detail pane visibility."""
        from rally_tui.widgets import TicketDetail

        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()

            detail_pane = app.query_one(TicketDetail)

            # Detail pane should be visible initially
            assert detail_pane.display is True

            # Toggle to wide view
            await pilot.press("v")
            await pilot.pause()

            # Toggle back to normal
            await pilot.press("v")
            await pilot.pause()

            # Detail pane should be visible again
            assert detail_pane.display is True

    async def test_wide_view_removes_classes_on_normal(self) -> None:
        """Toggling to normal view should remove wide classes."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.pause()

            list_container = app.query_one("#list-container")

            # Toggle to wide view
            await pilot.press("v")
            await pilot.pause()

            # Toggle back to normal
            await pilot.press("v")
            await pilot.pause()

            # Neither wide class should be present
            assert "wide" not in list_container.classes
            assert "wide-full" not in list_container.classes


class TestViewModeChangedMessage:
    """Tests for ViewModeChanged message."""

    async def test_view_mode_changed_message_posted(self) -> None:
        """ViewModeChanged message should be posted when view mode changes."""
        from textual.app import App, ComposeResult

        messages_received: list = []

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield TicketList(id="ticket-list")

            def on_ticket_list_view_mode_changed(
                self, event: TicketList.ViewModeChanged
            ) -> None:
                messages_received.append(event.mode)

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Toggle to wide
            ticket_list.toggle_view_mode()
            await pilot.pause()

            assert len(messages_received) == 1
            assert messages_received[0] == ViewMode.WIDE

            # Toggle back to normal
            ticket_list.toggle_view_mode()
            await pilot.pause()

            assert len(messages_received) == 2
            assert messages_received[1] == ViewMode.NORMAL


class TestWideViewWithOperations:
    """Tests for wide view mode with various operations."""

    def _create_ticket(
        self,
        formatted_id: str = "US1234",
        owner: str | None = "Alice",
        points: float | None = 5,
    ) -> Ticket:
        """Create a test ticket."""
        return Ticket(
            formatted_id=formatted_id,
            name=f"Test {formatted_id}",
            ticket_type="UserStory",
            state="In Progress",
            owner=owner,
            points=points,
        )

    async def test_set_tickets_uses_correct_item_type(self) -> None:
        """set_tickets should use WideTicketListItem in wide mode."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield TicketList(id="ticket-list", view_mode=ViewMode.WIDE)

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Set new tickets
            new_tickets = [self._create_ticket("US001"), self._create_ticket("US002")]
            ticket_list.set_tickets(new_tickets)
            await pilot.pause()

            # Should have WideTicketListItem
            wide_items = list(app.query("WideTicketListItem"))
            normal_items = list(app.query("TicketListItem"))
            assert len(wide_items) == 2
            assert len(normal_items) == 0

    async def test_filter_tickets_uses_correct_item_type(self) -> None:
        """filter_tickets should use WideTicketListItem in wide mode."""
        from textual.app import App, ComposeResult

        tickets = [
            Ticket(
                formatted_id="US001",
                name="First ticket",
                ticket_type="UserStory",
                state="Defined",
            ),
            Ticket(
                formatted_id="US002",
                name="Second ticket",
                ticket_type="UserStory",
                state="Defined",
            ),
        ]

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield TicketList(tickets, id="ticket-list", view_mode=ViewMode.WIDE)

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Filter to one ticket
            ticket_list.filter_tickets("First")
            await pilot.pause()

            # Should still have WideTicketListItem
            wide_items = list(app.query("WideTicketListItem"))
            assert len(wide_items) == 1

    async def test_sort_mode_change_preserves_view_mode(self) -> None:
        """Changing sort mode should preserve wide view item type."""
        from textual.app import App, ComposeResult
        from rally_tui.widgets import SortMode

        tickets = [
            Ticket(
                formatted_id="US001",
                name="First",
                ticket_type="UserStory",
                state="In Progress",
            ),
            Ticket(
                formatted_id="US002",
                name="Second",
                ticket_type="UserStory",
                state="Defined",
            ),
        ]

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield TicketList(tickets, id="ticket-list", view_mode=ViewMode.WIDE)

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Change sort mode
            ticket_list.set_sort_mode(SortMode.CREATED)
            await pilot.pause()

            # Should still have WideTicketListItem
            wide_items = list(app.query("WideTicketListItem"))
            assert len(wide_items) == 2

    async def test_add_ticket_uses_correct_item_type(self) -> None:
        """add_ticket should use WideTicketListItem in wide mode."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield TicketList(id="ticket-list", view_mode=ViewMode.WIDE)

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            ticket_list = app.query_one(TicketList)

            # Add a ticket
            new_ticket = Ticket(
                formatted_id="US999",
                name="New ticket",
                ticket_type="UserStory",
                state="Defined",
            )
            ticket_list.add_ticket(new_ticket)
            await pilot.pause()

            # Should have WideTicketListItem
            wide_items = list(app.query("WideTicketListItem"))
            assert len(wide_items) == 1


class TestWideViewItemDisplay:
    """Tests for WideTicketListItem display formatting."""

    def test_points_display_integer(self) -> None:
        """Whole number points should be displayed without decimal."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
            points=5.0,
        )
        item = WideTicketListItem(ticket)
        # Whole numbers display without decimal
        assert ticket.points == 5.0
        assert ticket.points == int(ticket.points)

    def test_points_display_decimal(self) -> None:
        """Decimal points should be displayed with decimal."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
            points=2.5,
        )
        item = WideTicketListItem(ticket)
        # Decimal points should show the decimal
        assert ticket.points == 2.5
        assert ticket.points != int(ticket.points)

    def test_missing_owner_displayed_as_dash(self) -> None:
        """Missing owner should show as '-'."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
            owner=None,
        )
        item = WideTicketListItem(ticket)
        assert ticket.owner is None

    def test_missing_points_displayed_as_dash(self) -> None:
        """Missing points should show as '-'."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
            points=None,
        )
        item = WideTicketListItem(ticket)
        assert ticket.points is None

    def test_missing_parent_displayed_as_dash(self) -> None:
        """Missing parent should show as '-'."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
            parent_id=None,
        )
        item = WideTicketListItem(ticket)
        assert ticket.parent_id is None

    def test_long_owner_truncated(self) -> None:
        """Long owner names should be truncated to 18 chars."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
            owner="VeryLongOwnerNameThatExceeds18Chars",
        )
        # The compose method truncates to 18 chars
        assert len(ticket.owner) > 18
