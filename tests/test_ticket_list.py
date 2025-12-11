"""Tests for the TicketList widget."""

import pytest

from rally_tui.app import RallyTUI
from rally_tui.models import Ticket
from rally_tui.widgets import TicketList


class TestTicketListWidget:
    """Tests for TicketList widget behavior."""

    async def test_initial_render(self) -> None:
        """List should render all provided tickets."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            items = list(app.query("TicketListItem"))
            assert len(items) == 8  # SAMPLE_TICKETS has 8 items

    async def test_first_item_highlighted_by_default(self) -> None:
        """First item should be highlighted on start."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            assert ticket_list.index == 0

    async def test_keyboard_navigation_j(self) -> None:
        """Pressing j should move selection down."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            assert ticket_list.index == 0

            await pilot.press("j")
            assert ticket_list.index == 1

    async def test_keyboard_navigation_k(self) -> None:
        """Pressing k should move selection up."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            await pilot.press("j", "j")
            assert ticket_list.index == 2

            await pilot.press("k")
            assert ticket_list.index == 1

    async def test_keyboard_navigation_down_arrow(self) -> None:
        """Down arrow should move selection down."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            await pilot.press("down")
            assert ticket_list.index == 1

    async def test_keyboard_navigation_up_arrow(self) -> None:
        """Up arrow should move selection up."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            await pilot.press("down", "down")
            await pilot.press("up")
            assert ticket_list.index == 1

    async def test_vim_go_to_top(self) -> None:
        """Pressing g should jump to first item."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            await pilot.press("j", "j", "j")
            assert ticket_list.index == 3

            await pilot.press("g")
            assert ticket_list.index == 0

    async def test_vim_go_to_bottom(self) -> None:
        """Pressing G should jump to last item."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            await pilot.press("G")
            assert ticket_list.index == 7  # Last of 8 items

    async def test_navigation_wraps_at_top(self) -> None:
        """Pressing k at top should stay at top."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)
            assert ticket_list.index == 0

            await pilot.press("k")
            assert ticket_list.index == 0

    async def test_navigation_wraps_at_bottom(self) -> None:
        """Pressing j at bottom should stay at bottom."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            ticket_list = app.query_one(TicketList)

            await pilot.press("G")  # Go to bottom
            bottom_index = ticket_list.index

            await pilot.press("j")
            assert ticket_list.index == bottom_index

    async def test_quit_binding(self) -> None:
        """Pressing q should quit the app."""
        app = RallyTUI()
        async with app.run_test() as pilot:
            await pilot.press("q")
            assert app._exit
