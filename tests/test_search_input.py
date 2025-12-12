"""Tests for the SearchInput widget."""

from rally_tui.widgets import SearchInput


class TestSearchInputUnit:
    """Unit tests for SearchInput widget in isolation."""

    def test_default_placeholder(self) -> None:
        """SearchInput should have 'Search...' placeholder."""
        widget = SearchInput()
        assert widget.placeholder == "Search..."

    def test_initial_value_empty(self) -> None:
        """SearchInput should start empty."""
        widget = SearchInput()
        assert widget.value == ""

    def test_custom_id(self) -> None:
        """SearchInput should accept custom id."""
        widget = SearchInput(id="my-search")
        assert widget.id == "my-search"

    def test_custom_classes(self) -> None:
        """SearchInput should accept custom classes."""
        widget = SearchInput(classes="my-class")
        assert "my-class" in widget.classes


class TestSearchInputWidget:
    """Integration tests for SearchInput widget behavior."""

    async def test_renders_with_placeholder(self) -> None:
        """SearchInput should render with placeholder text."""
        from textual.app import App, ComposeResult

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield SearchInput(id="search")

        app = TestApp()
        async with app.run_test():
            search = app.query_one(SearchInput)
            assert search.placeholder == "Search..."

    async def test_typing_emits_search_changed(self) -> None:
        """Typing should emit SearchChanged messages."""
        from textual.app import App, ComposeResult

        messages: list[SearchInput.SearchChanged] = []

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield SearchInput(id="search")

            def on_search_input_search_changed(self, event: SearchInput.SearchChanged) -> None:
                messages.append(event)

        app = TestApp()
        async with app.run_test() as pilot:
            search = app.query_one(SearchInput)
            search.focus()
            await pilot.press("t", "e", "s", "t")
            assert len(messages) == 4
            assert messages[-1].query == "test"

    async def test_enter_emits_search_submitted(self) -> None:
        """Enter key should emit SearchSubmitted."""
        from textual.app import App, ComposeResult

        submitted: list[SearchInput.SearchSubmitted] = []

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield SearchInput(id="search")

            def on_search_input_search_submitted(self, event: SearchInput.SearchSubmitted) -> None:
                submitted.append(event)

        app = TestApp()
        async with app.run_test() as pilot:
            search = app.query_one(SearchInput)
            search.focus()
            await pilot.press("t", "e", "s", "t")
            await pilot.press("enter")
            assert len(submitted) == 1
            assert submitted[0].query == "test"

    async def test_escape_clears_and_emits(self) -> None:
        """Escape should clear input and emit SearchCleared."""
        from textual.app import App, ComposeResult

        cleared: list[SearchInput.SearchCleared] = []

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield SearchInput(id="search")

            def on_search_input_search_cleared(self, event: SearchInput.SearchCleared) -> None:
                cleared.append(event)

        app = TestApp()
        async with app.run_test() as pilot:
            search = app.query_one(SearchInput)
            search.focus()
            await pilot.press("t", "e", "s", "t")
            assert search.value == "test"
            await pilot.press("escape")
            assert search.value == ""
            assert len(cleared) == 1

    async def test_empty_search_emits_empty_query(self) -> None:
        """Empty search should emit empty query on submit."""
        from textual.app import App, ComposeResult

        submitted: list[SearchInput.SearchSubmitted] = []

        class TestApp(App[None]):
            def compose(self) -> ComposeResult:
                yield SearchInput(id="search")

            def on_search_input_search_submitted(self, event: SearchInput.SearchSubmitted) -> None:
                submitted.append(event)

        app = TestApp()
        async with app.run_test() as pilot:
            search = app.query_one(SearchInput)
            search.focus()
            await pilot.press("enter")
            assert len(submitted) == 1
            assert submitted[0].query == ""
