# Iteration 8: Discussions & Comments - Implementation Guide

## Overview

This iteration adds the ability to view ticket discussions and add comments from the TUI. Users can press `d` from the ticket detail view to open a discussion screen showing all comments, and press `c` to add a new comment.

## Rally API Background

Rally stores discussions as `ConversationPost` entities linked to artifacts:

- **Entity Type**: `ConversationPost`
- **Key Fields**: `Text`, `User`, `CreationDate`, `Artifact`
- **Query Pattern**: `(Artifact = "/artifact/<ObjectID>")`
- **Create Pattern**: `rally.create('ConversationPost', {Text: '...', Artifact: '<ref>'})`

The `Discussion` attribute on artifacts is a collection of `ConversationPost` objects.

**References**:
- [Rally WSAPI Discussions](https://knowledge.broadcom.com/external/article/16712/how-to-extract-artifact-discussions-usin.html)
- [Rally WSAPI Documentation](https://techdocs.broadcom.com/us/en/ca-enterprise-software/valueops/rally/rally-help/reference/rally-web-services-api.html)

---

## Implementation Steps

### Step 1: Add Discussion Model and Update Ticket Model

**Goal**: Create data models for discussions and add ObjectID to Ticket for API lookups.

#### 1.1 Update Ticket Model

Add `object_id` field to enable fetching discussions:

```python
# src/rally_tui/models/ticket.py
@dataclass(frozen=True)
class Ticket:
    formatted_id: str
    name: str
    ticket_type: TicketType
    state: str
    owner: str | None = None
    description: str = ""
    iteration: str | None = None
    points: int | None = None
    object_id: str | None = None  # Rally ObjectID for API calls
```

#### 1.2 Create Discussion Model

```python
# src/rally_tui/models/discussion.py
"""Discussion/comment data model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Discussion:
    """Represents a Rally discussion post (comment).

    Maps to Rally's ConversationPost entity.
    """

    object_id: str
    text: str
    user: str
    created_at: datetime
    artifact_id: str  # FormattedID of the parent artifact

    @property
    def formatted_date(self) -> str:
        """Format date for display: 'Jan 15, 2024 10:30 AM'."""
        return self.created_at.strftime("%b %d, %Y %I:%M %p")

    @property
    def display_header(self) -> str:
        """Format header for display: 'John Smith • Jan 15, 2024 10:30 AM'."""
        return f"{self.user} • {self.formatted_date}"
```

#### 1.3 Update Models __init__.py

```python
# src/rally_tui/models/__init__.py
from rally_tui.models.discussion import Discussion
from rally_tui.models.ticket import Ticket, TicketType

__all__ = ["Discussion", "Ticket", "TicketType"]
```

#### 1.4 Update Sample Data

Add sample discussions for offline mode testing:

```python
# src/rally_tui/models/sample_data.py
SAMPLE_DISCUSSIONS: dict[str, list[Discussion]] = {
    "US1234": [
        Discussion(
            object_id="100001",
            text="I've started working on the login form...",
            user="John Smith",
            created_at=datetime(2024, 1, 15, 10, 30),
            artifact_id="US1234",
        ),
        # ... more sample discussions
    ],
}
```

**Tests**: `tests/test_discussion_model.py`
- Test Discussion dataclass properties
- Test formatted_date output
- Test display_header format

**Commit**: "Add Discussion model and object_id to Ticket"

---

### Step 2: Add Discussion Methods to Protocol and Clients

**Goal**: Define the interface and implement discussion fetching/creation.

#### 2.1 Update RallyClientProtocol

```python
# src/rally_tui/services/protocol.py
class RallyClientProtocol(Protocol):
    # ... existing methods ...

    def get_discussions(self, ticket: Ticket) -> list[Discussion]:
        """Fetch discussion posts for a ticket.

        Args:
            ticket: The ticket to fetch discussions for.

        Returns:
            List of discussions, ordered by creation date (oldest first).
        """
        ...

    def add_comment(self, ticket: Ticket, text: str) -> Discussion | None:
        """Add a comment to a ticket's discussion.

        Args:
            ticket: The ticket to comment on.
            text: The comment text.

        Returns:
            The created Discussion, or None on failure.
        """
        ...
```

#### 2.2 Implement in RallyClient

```python
# src/rally_tui/services/rally_client.py
def get_discussions(self, ticket: Ticket) -> list[Discussion]:
    """Fetch discussion posts for a ticket from Rally API."""
    if not ticket.object_id:
        return []

    try:
        # Query ConversationPost by artifact reference
        response = self._rally.get(
            "ConversationPost",
            fetch="ObjectID,Text,User,CreationDate,Artifact",
            query=f'(Artifact = "/artifact/{ticket.object_id}")',
            order="CreationDate",
        )

        discussions = []
        for post in response:
            discussions.append(self._to_discussion(post, ticket.formatted_id))
        return discussions
    except Exception:
        return []

def add_comment(self, ticket: Ticket, text: str) -> Discussion | None:
    """Add a comment to a ticket's discussion."""
    if not ticket.object_id:
        return None

    try:
        # Get artifact reference
        entity_type = self._get_entity_type(ticket.formatted_id)
        response = self._rally.get(
            entity_type,
            fetch="ObjectID",
            query=f'FormattedID = "{ticket.formatted_id}"',
        )
        artifact = response.next()

        # Create the conversation post
        post_data = {
            "Text": text,
            "Artifact": artifact.ref,
        }
        post = self._rally.create("ConversationPost", post_data)

        return Discussion(
            object_id=str(post.ObjectID),
            text=text,
            user=self._current_user or "Unknown",
            created_at=datetime.now(timezone.utc),
            artifact_id=ticket.formatted_id,
        )
    except Exception:
        return None

def _to_discussion(self, post: Any, artifact_id: str) -> Discussion:
    """Convert a pyral ConversationPost to our Discussion model."""
    from datetime import datetime

    # Parse creation date
    created_str = getattr(post, "CreationDate", "")
    try:
        created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        created_at = datetime.now()

    # Get user name
    user = "Unknown"
    if hasattr(post, "User") and post.User:
        user = getattr(post.User, "DisplayName", None) or \
               getattr(post.User, "_refObjectName", "Unknown")

    # Get and convert HTML text
    text = getattr(post, "Text", "") or ""
    text = html_to_text(text)

    return Discussion(
        object_id=str(post.ObjectID),
        text=text,
        user=user,
        created_at=created_at,
        artifact_id=artifact_id,
    )
```

#### 2.3 Update _to_ticket to Include ObjectID

```python
# In rally_client.py _to_ticket method
return Ticket(
    formatted_id=item.FormattedID,
    name=item.Name,
    # ... other fields ...
    object_id=str(item.ObjectID) if hasattr(item, "ObjectID") else None,
)
```

#### 2.4 Implement in MockRallyClient

```python
# src/rally_tui/services/mock_client.py
def __init__(
    self,
    tickets: list[Ticket] | None = None,
    discussions: dict[str, list[Discussion]] | None = None,
    # ... other params ...
):
    self._discussions = discussions if discussions is not None else SAMPLE_DISCUSSIONS

def get_discussions(self, ticket: Ticket) -> list[Discussion]:
    """Return mock discussions for a ticket."""
    return self._discussions.get(ticket.formatted_id, [])

def add_comment(self, ticket: Ticket, text: str) -> Discussion | None:
    """Create a mock discussion post."""
    discussion = Discussion(
        object_id=str(uuid.uuid4()),
        text=text,
        user=self._current_user or "Mock User",
        created_at=datetime.now(),
        artifact_id=ticket.formatted_id,
    )
    # Add to mock data
    if ticket.formatted_id not in self._discussions:
        self._discussions[ticket.formatted_id] = []
    self._discussions[ticket.formatted_id].append(discussion)
    return discussion
```

**Tests**: `tests/test_rally_client.py` (add to existing), `tests/test_services.py` (add to existing)
- Test get_discussions returns list
- Test get_discussions with empty result
- Test add_comment creates discussion
- Test _to_discussion mapping

**Commit**: "Add discussion methods to RallyClient and MockRallyClient"

---

### Step 3: Create DiscussionScreen

**Goal**: Create a screen to display discussions for a ticket.

#### 3.1 Create DiscussionScreen

Use Textual's Screen for a modal-like discussion view:

```python
# src/rally_tui/screens/discussion_screen.py
"""Discussion screen for viewing and adding comments."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from rally_tui.models import Discussion, Ticket
from rally_tui.services import RallyClientProtocol
from rally_tui.utils import html_to_text


class DiscussionItem(Static):
    """Widget for displaying a single discussion post."""

    DEFAULT_CSS = """
    DiscussionItem {
        background: $surface;
        border: solid $primary;
        margin: 1 2;
        padding: 1 2;
    }

    DiscussionItem .header {
        color: $text-muted;
        text-style: italic;
    }

    DiscussionItem .text {
        margin-top: 1;
    }
    """

    def __init__(self, discussion: Discussion) -> None:
        super().__init__()
        self._discussion = discussion

    def compose(self) -> ComposeResult:
        yield Static(self._discussion.display_header, classes="header")
        yield Static(self._discussion.text, classes="text")


class DiscussionScreen(Screen[None]):
    """Screen for viewing ticket discussions."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("c", "compose", "Add Comment"),
        Binding("q", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    DiscussionScreen {
        background: $background;
    }

    #discussion-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #discussion-container {
        height: 1fr;
    }

    #no-discussions {
        text-align: center;
        padding: 4;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        ticket: Ticket,
        client: RallyClientProtocol,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._ticket = ticket
        self._client = client
        self._discussions: list[Discussion] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"Discussions - {self._ticket.formatted_id}",
            id="discussion-title",
        )
        yield VerticalScroll(id="discussion-container")
        yield Footer()

    def on_mount(self) -> None:
        """Load discussions when screen mounts."""
        self._load_discussions()

    def _load_discussions(self) -> None:
        """Fetch and display discussions."""
        container = self.query_one("#discussion-container")
        container.remove_children()

        self._discussions = self._client.get_discussions(self._ticket)

        if not self._discussions:
            container.mount(
                Static("No discussions yet.", id="no-discussions")
            )
        else:
            for discussion in self._discussions:
                container.mount(DiscussionItem(discussion))

    def action_back(self) -> None:
        """Return to the main screen."""
        self.app.pop_screen()

    def action_compose(self) -> None:
        """Open comment input."""
        from rally_tui.screens.comment_screen import CommentScreen

        def on_submit(text: str) -> None:
            result = self._client.add_comment(self._ticket, text)
            if result:
                self._load_discussions()  # Refresh discussions

        self.app.push_screen(
            CommentScreen(self._ticket, on_submit=on_submit)
        )
```

**Tests**: `tests/test_discussion_screen.py`
- Test screen displays ticket ID in title
- Test screen shows "No discussions" when empty
- Test screen displays discussion items
- Test Escape returns to main screen
- Test 'c' opens comment screen

**Commit**: "Add DiscussionScreen for viewing ticket discussions"

---

### Step 4: Create CommentScreen

**Goal**: Create a screen for composing and submitting comments.

```python
# src/rally_tui/screens/comment_screen.py
"""Comment input screen for adding discussions."""

from typing import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, TextArea

from rally_tui.models import Ticket


class CommentScreen(Screen[str | None]):
    """Screen for composing a comment."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "submit", "Submit"),
    ]

    DEFAULT_CSS = """
    CommentScreen {
        background: $background;
    }

    #comment-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
    }

    #comment-hint {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #comment-input {
        height: 1fr;
        margin: 1 2;
        border: solid $primary;
    }
    """

    def __init__(
        self,
        ticket: Ticket,
        on_submit: Callable[[str], None] | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._ticket = ticket
        self._on_submit = on_submit

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"Add Comment - {self._ticket.formatted_id}",
            id="comment-title",
        )
        yield Static(
            "Press Ctrl+S to submit, Escape to cancel",
            id="comment-hint",
        )
        yield TextArea(id="comment-input")
        yield Footer()

    def on_mount(self) -> None:
        """Focus the text input."""
        self.query_one("#comment-input").focus()

    def action_cancel(self) -> None:
        """Cancel and return to discussions."""
        self.dismiss(None)

    def action_submit(self) -> None:
        """Submit the comment."""
        text_area = self.query_one("#comment-input", TextArea)
        text = text_area.text.strip()

        if text and self._on_submit:
            self._on_submit(text)

        self.dismiss(text if text else None)
```

**Tests**: `tests/test_comment_screen.py`
- Test screen displays ticket ID in title
- Test TextArea receives focus on mount
- Test Escape dismisses screen
- Test Ctrl+S submits text
- Test empty text doesn't call on_submit

**Commit**: "Add CommentScreen for composing comments"

---

### Step 5: Integrate with App and Add Keybindings

**Goal**: Wire up the discussion feature to the main app.

#### 5.1 Update App with Discussion Binding

```python
# src/rally_tui/app.py
from rally_tui.screens.discussion_screen import DiscussionScreen

class RallyTUI(App[None]):
    BINDINGS = [
        # ... existing bindings ...
        Binding("d", "open_discussions", "Discussions", show=False),
    ]

    def action_open_discussions(self) -> None:
        """Open discussions for the currently selected ticket."""
        detail = self.query_one(TicketDetail)
        if detail.ticket:
            self.push_screen(
                DiscussionScreen(detail.ticket, self._client)
            )
```

#### 5.2 Update Screens __init__.py

```python
# src/rally_tui/screens/__init__.py
from rally_tui.screens.comment_screen import CommentScreen
from rally_tui.screens.discussion_screen import DiscussionScreen

__all__ = ["CommentScreen", "DiscussionScreen"]
```

#### 5.3 Update CommandBar with Discussion Context

```python
# src/rally_tui/widgets/command_bar.py
COMMANDS = {
    "list": "[j/k] Navigate  [g/G] Jump  [Enter] Select  [/] Search  [Tab] Panel  [q] Quit",
    "detail": "[d] Discussions  [Tab] Panel  [q] Quit",
    "search": "[Enter] Confirm  [Esc] Clear  [q] Quit",
    "discussion": "[c] Comment  [Esc] Back  [q] Quit",
}
```

**Tests**: Integration tests in `tests/test_app.py` or existing test files
- Test 'd' key opens discussion screen from detail
- Test discussion screen can be closed with Escape
- Test comment workflow

**Commit**: "Integrate DiscussionScreen with main app"

---

### Step 6: Add Tests

**Goal**: Comprehensive test coverage for all new functionality.

#### Test Files

1. `tests/test_discussion_model.py` - Discussion dataclass tests
2. `tests/test_discussion_screen.py` - DiscussionScreen widget tests
3. `tests/test_comment_screen.py` - CommentScreen widget tests
4. Update `tests/test_rally_client.py` - Add discussion API tests
5. Update `tests/test_services.py` - Add MockRallyClient discussion tests

#### Test Coverage Targets

- **Unit Tests**: ~20 new tests
  - Discussion model properties
  - Date formatting
  - Header formatting
  - Discussion item rendering
  - Comment screen behavior

- **Integration Tests**: ~10 new tests
  - Navigation to/from discussion screen
  - Comment submission flow
  - Empty state handling
  - Client method mocking

- **Snapshot Tests**: ~3 new tests
  - Discussion screen with comments
  - Empty discussion screen
  - Comment input screen

**Commit**: "Add tests for discussion and comment functionality"

---

## File Summary

### New Files

```
src/rally_tui/
├── models/
│   └── discussion.py           # Discussion dataclass
├── screens/
│   ├── __init__.py             # Screen exports
│   ├── discussion_screen.py    # DiscussionScreen
│   └── comment_screen.py       # CommentScreen

tests/
├── test_discussion_model.py    # Discussion model tests
├── test_discussion_screen.py   # DiscussionScreen tests
└── test_comment_screen.py      # CommentScreen tests
```

### Modified Files

```
src/rally_tui/
├── models/
│   ├── __init__.py             # Add Discussion export
│   ├── ticket.py               # Add object_id field
│   └── sample_data.py          # Add SAMPLE_DISCUSSIONS
├── services/
│   ├── protocol.py             # Add get_discussions, add_comment
│   ├── rally_client.py         # Implement discussion methods
│   └── mock_client.py          # Mock discussion support
├── widgets/
│   └── command_bar.py          # Add discussion context
└── app.py                      # Add 'd' binding, push_screen

tests/
├── test_rally_client.py        # Add discussion tests
└── test_services.py            # Add MockRallyClient discussion tests
```

---

## Key Bindings Summary

| Key | Context | Action |
|-----|---------|--------|
| `d` | detail | Open discussions for selected ticket |
| `c` | discussion | Open comment input |
| `Ctrl+S` | comment | Submit comment |
| `Esc` | discussion/comment | Return to previous screen |

---

## Implementation Checklist

- [ ] Step 1: Add Discussion model and update Ticket model
  - [ ] Create `discussion.py` with Discussion dataclass
  - [ ] Add `object_id` to Ticket model
  - [ ] Update models `__init__.py`
  - [ ] Add sample discussions to `sample_data.py`
  - [ ] Write model tests
  - [ ] Commit

- [ ] Step 2: Add discussion methods to clients
  - [ ] Update RallyClientProtocol with new methods
  - [ ] Implement in RallyClient
  - [ ] Implement in MockRallyClient
  - [ ] Update _to_ticket to include ObjectID
  - [ ] Write client tests
  - [ ] Commit

- [ ] Step 3: Create DiscussionScreen
  - [ ] Create `discussion_screen.py`
  - [ ] Create DiscussionItem widget
  - [ ] Handle empty state
  - [ ] Write screen tests
  - [ ] Commit

- [ ] Step 4: Create CommentScreen
  - [ ] Create `comment_screen.py`
  - [ ] Implement TextArea input
  - [ ] Handle submit/cancel
  - [ ] Write screen tests
  - [ ] Commit

- [ ] Step 5: Integrate with app
  - [ ] Add 'd' binding to app
  - [ ] Update CommandBar contexts
  - [ ] Update screens `__init__.py`
  - [ ] Write integration tests
  - [ ] Commit

- [ ] Step 6: Final testing and documentation
  - [ ] Run full test suite
  - [ ] Update README.md
  - [ ] Update PLAN.md
  - [ ] Final commit

---

## Notes

- **HTML Conversion**: Discussion text from Rally is HTML - use existing `html_to_text` utility
- **Date Handling**: Rally returns ISO-8601 dates, parse with `datetime.fromisoformat()`
- **ObjectID Requirement**: Need ticket's ObjectID to query ConversationPost entities
- **Optimistic Updates**: After posting, immediately refresh discussion list
- **Error Handling**: Gracefully handle API failures, show user-friendly messages
