# SRD: Rally CLI Comprehensive Enhancement

## Document Info

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Date | 2026-02-22 |
| Status | DRAFT - Ready for Implementation |
| Base Version | 0.8.3 |
| Target Version | 1.0.0 |
| Package | `rally-tui` (PyPI) / `rally-cli` (command) |
| Repository | `~/repos/rally-cli` |

---

## 1. Overview

This Software Requirements Document specifies a comprehensive enhancement of the `rally-cli` command-line interface to expose the full breadth of the Rally WSAPI v2.0 through composable, scriptable CLI commands. The current CLI (v0.8.3) supports three operations: querying tickets, creating tickets, and posting comments. This SRD defines the expansion to a full-featured Rally CLI covering ticket updates, field mutations, iteration/release management, portfolio items, attachments, discussions, search, bulk operations, and UX polish.

### 1.1 Business Objective

Transform `rally-cli` from a minimal query tool into the definitive command-line interface for Rally, enabling:

- **Daily workflow automation**: Update tickets, change states, reassign owners, and move iterations from the terminal
- **CI/CD integration**: Post deployment comments, update ticket states, and attach build artifacts programmatically
- **Reporting**: Generate sprint reports, velocity metrics, and team breakdowns via JSON/CSV export
- **Scripting**: Compose rally-cli commands into bash workflows with proper exit codes and machine-parseable output

### 1.2 Success Criteria

| Metric | Target |
|--------|--------|
| CLI commands covering Rally WSAPI operations | 90%+ of common operations |
| JSON output support on ALL list/query commands | 100% |
| Backward compatibility with existing v0.8.3 commands | 100% |
| Test coverage for new CLI code | 90%+ |
| CLI response time (typical query, 10-50 tickets) | < 2 seconds |

---

## 2. Current State Analysis

### 2.1 Existing CLI Commands (v0.8.3)

| Command | Verb | Description | JSON Support |
|---------|------|-------------|:------------:|
| `rally-cli tickets` | LIST | Query tickets with filters | Via `--format json` at top level |
| `rally-cli tickets create` | CREATE | Create User Story or Defect | Via `--format json` at top level |
| `rally-cli comment` | CREATE | Post discussion comment | Via `--format json` at top level |

### 2.2 Existing CLI Architecture

```
src/rally_tui/cli/
  __init__.py              # Exports cli group
  main.py                  # Click group, CLIContext, global options (--format, --server, etc.)
  commands/
    __init__.py
    query.py               # tickets group (list + create subcommand)
    comment.py             # comment command
  formatters/
    __init__.py
    base.py                # BaseFormatter ABC, CLIResult, OutputFormat enum
    text.py                # TextFormatter (table output)
    json.py                # JSONFormatter
    csv.py                 # CSVFormatter
```

### 2.3 Existing Service Layer (AsyncRallyClient)

The CLI already uses `AsyncRallyClient` (httpx-based, async) via `asyncio.run()`. The client exposes these methods that the CLI does NOT yet surface:

| Method | CLI Exposed? | Notes |
|--------|:------------:|-------|
| `get_tickets(query)` | Yes | tickets list |
| `get_ticket(formatted_id)` | Yes (internal) | Used by comment lookup |
| `create_ticket(...)` | Yes | tickets create |
| `add_comment(ticket, text)` | Yes | comment command |
| `update_points(ticket, points)` | **No** | TUI-only (`p` key) |
| `update_state(ticket, state)` | **No** | TUI-only (`s` key) |
| `set_parent(ticket, parent_id)` | **No** | TUI-only |
| `assign_owner(ticket, owner)` | **No** | TUI-only |
| `get_discussions(ticket)` | **No** | TUI-only (`d` key) |
| `get_iterations(count)` | **No** | TUI-only (`i` key) |
| `get_feature(formatted_id)` | **No** | TUI-only |
| `get_attachments(ticket)` | **No** | TUI-only |
| `download_attachment(...)` | **No** | TUI-only |
| `upload_attachment(...)` | **No** | TUI-only |
| `get_users(display_names)` | **No** | TUI-only |
| `bulk_set_parent(...)` | **No** | TUI-only |
| `bulk_update_state(...)` | **No** | TUI-only |
| `bulk_set_iteration(...)` | **No** | TUI-only |
| `bulk_update_points(...)` | **No** | TUI-only |
| `bulk_assign_owner(...)` | **No** | TUI-only |

### 2.4 Existing Data Models

| Model | File | Fields |
|-------|------|--------|
| `Ticket` | `models/ticket.py` | formatted_id, name, ticket_type, state, owner, description, notes, iteration, points, object_id, parent_id |
| `Discussion` | `models/discussion.py` | object_id, text, user, created_at, artifact_id |
| `Iteration` | `models/iteration.py` | object_id, name, start_date, end_date, state |
| `Attachment` | `models/attachment.py` | name, size, content_type, object_id |
| `Owner` | `models/owner.py` | object_id, display_name, user_name |

### 2.5 Known Gaps / Pain Points

1. **`--format json` placement**: Must be placed on the TOP-LEVEL group (`rally-cli --format json tickets`), not on the subcommand. Users expect `rally-cli tickets --format json`.
2. **No ticket update from CLI**: Cannot change state, points, owner, iteration, description, notes, or parent from the command line.
3. **No discussion listing**: Cannot view comments/discussions from CLI.
4. **No iteration listing**: Cannot list sprints from CLI.
5. **No attachment operations**: Cannot list, download, or upload attachments from CLI.
6. **No user listing**: Cannot list team members from CLI.
7. **No release support**: Neither TUI nor CLI support Rally Releases.
8. **No tag support**: Neither TUI nor CLI support Rally Tags.
9. **No `show` command**: Cannot fetch a single ticket's full details from CLI.
10. **Missing Rally fields**: Acceptance criteria (c_AcceptanceCriteria), blocked/blocked_reason, severity, priority, schedule_state, ready, expedite, target_date not exposed.

---

## 3. Goals and Non-Goals

### 3.1 Goals

1. **Expose all existing AsyncRallyClient methods** as CLI commands
2. **Add `--format` flag to every subcommand** (not just top level) for ergonomic JSON/CSV output
3. **Add ticket update command** (`rally-cli tickets update`) for field mutations
4. **Add discussion listing** (`rally-cli discussions`)
5. **Add iteration listing** (`rally-cli iterations`)
6. **Add attachment operations** (`rally-cli attachments list/download/upload`)
7. **Add user listing** (`rally-cli users`)
8. **Add release support** to the service layer and CLI
9. **Add tag support** to the service layer and CLI
10. **Add `rally-cli tickets show`** for single-ticket detail view
11. **Extend Ticket model** with acceptance_criteria, blocked, blocked_reason, severity, priority, release, tags, ready, expedite, schedule_state, target_date
12. **Bulk operations from CLI** via piped input or multi-ID arguments
13. **Backward compatibility**: All existing commands work identically

### 3.2 Non-Goals

1. **TUI changes**: This SRD covers CLI enhancements only. TUI remains unchanged.
2. **Offline mode for CLI**: CLI requires active API connection.
3. **Interactive prompts**: CLI remains non-interactive (no inquirer-style prompts).
4. **Plugin system**: Extensibility via plugins is a future enhancement.
5. **Custom field discovery**: Users must know their custom field names. No introspection UI.
6. **Test Case management**: TestCase CRUD is out of scope (query-only is sufficient).
7. **Lookback API**: Historical analytics API is out of scope.

---

## 4. Architecture

### 4.1 Design Principles

| Principle | Description |
|-----------|-------------|
| **Composable** | Every command produces clean output suitable for piping to `jq`, `grep`, `awk`, etc. |
| **Consistent** | All list commands support `--format json\|csv\|text`. All mutations return the modified object. |
| **Backward Compatible** | v0.8.3 commands work identically. `--format` remains valid on the top-level group AND on subcommands. |
| **Exit Codes** | 0=success, 1=API/general error, 2=invalid input, 3=auth error, 4=config error |
| **Async Native** | All operations use `AsyncRallyClient` via `asyncio.run()` |

### 4.2 Revised CLI Command Tree

```
rally-cli [GLOBAL_OPTIONS] <command> [SUBCOMMAND] [OPTIONS]

Global Options (unchanged):
  --server TEXT               Rally server hostname
  --apikey TEXT               Rally API key
  --workspace TEXT            Workspace name
  --project TEXT              Project name
  --format [text|json|csv]    Output format (default: text) [ALSO on subcommands]
  -v, --verbose               Enable verbose logging
  -q, --quiet                 Suppress non-essential output
  --version                   Show version

Commands:
  tickets                     Query, create, show, update, delete tickets
  comment                     Add comment to a ticket (existing)
  discussions                 List discussions for a ticket
  iterations                  List iterations/sprints
  releases                    List and manage releases
  users                       List project team members
  attachments                 List, download, upload attachments
  tags                        List and manage tags
```

### 4.3 Revised File Structure

```
src/rally_tui/cli/
  __init__.py
  main.py                         # Click group, CLIContext (MODIFIED: --format on subcommands)
  commands/
    __init__.py
    query.py                      # MODIFIED: tickets group + show, update, delete subcommands
    comment.py                    # EXISTING (unchanged)
    discussions.py                # NEW: list discussions
    iterations.py                 # NEW: list iterations
    releases.py                   # NEW: list/manage releases
    users.py                      # NEW: list users
    attachments.py                # NEW: list/download/upload attachments
    tags.py                       # NEW: list/manage tags
  formatters/
    __init__.py
    base.py                       # MODIFIED: add format_* methods for new types
    text.py                       # MODIFIED: add format_* methods for new types
    json.py                       # MODIFIED: add format_* methods for new types
    csv.py                        # MODIFIED: add format_* methods for new types
```

### 4.4 Service Layer Extensions

New methods to add to `AsyncRallyClient`:

```python
# Ticket field updates (granular)
async def update_ticket(self, ticket: Ticket, fields: dict[str, Any]) -> Ticket | None
async def update_description(self, ticket: Ticket, description: str) -> Ticket | None
async def update_notes(self, ticket: Ticket, notes: str) -> Ticket | None
async def set_iteration(self, ticket: Ticket, iteration_name: str | None) -> Ticket | None
async def delete_ticket(self, formatted_id: str) -> bool

# Release operations
async def get_releases(self, count: int = 10) -> list[Release]
async def get_release(self, name: str) -> Release | None
async def set_release(self, ticket: Ticket, release_name: str | None) -> Ticket | None

# Tag operations
async def get_tags(self) -> list[Tag]
async def add_tag(self, ticket: Ticket, tag_name: str) -> bool
async def remove_tag(self, ticket: Ticket, tag_name: str) -> bool
async def create_tag(self, name: str) -> Tag | None

# Extended ticket fields
async def update_blocked(self, ticket: Ticket, blocked: bool, reason: str = "") -> Ticket | None
async def update_ready(self, ticket: Ticket, ready: bool) -> Ticket | None
```

### 4.5 Model Extensions

**New models:**

```python
# models/release.py
@dataclass(frozen=True)
class Release:
    object_id: str
    name: str
    start_date: date
    end_date: date
    state: str  # Planning, Active, Locked
    theme: str = ""
    notes: str = ""

# models/tag.py
@dataclass(frozen=True)
class Tag:
    object_id: str
    name: str
```

**Extended Ticket model:**

```python
@dataclass(frozen=True)
class Ticket:
    # Existing fields (unchanged)
    formatted_id: str
    name: str
    ticket_type: TicketType
    state: str
    owner: str | None = None
    description: str = ""
    notes: str = ""
    iteration: str | None = None
    points: int | float | None = None
    object_id: str | None = None
    parent_id: str | None = None

    # New fields (Phase 1+)
    acceptance_criteria: str = ""        # c_AcceptanceCriteria custom field
    blocked: bool = False
    blocked_reason: str = ""
    schedule_state: str = ""             # Defined, In-Progress, Completed, Accepted
    severity: str | None = None          # Defect only
    priority: str | None = None          # Defect only
    release: str | None = None
    tags: tuple[str, ...] = ()           # Immutable tuple for frozen dataclass
    ready: bool = False
    expedite: bool = False
    target_date: str | None = None       # ISO date string
    creation_date: str | None = None     # ISO datetime string
    last_update_date: str | None = None  # ISO datetime string
```

---

## 5. Phase 1: Core Ticket Operations & JSON Output Fix

**Goal**: Add `tickets show`, `tickets update`, `tickets delete`, and fix `--format` placement.

**Priority**: HIGHEST -- these are the most commonly requested features.

### 5.1 Fix `--format` on Subcommands

Currently `--format` is only on the top-level `cli` group. Users must write:

```bash
rally-cli --format json tickets --current-iteration   # Current (awkward)
```

After this fix, BOTH placements work:

```bash
rally-cli --format json tickets --current-iteration   # Still works (backward compat)
rally-cli tickets --format json --current-iteration    # NEW: also works
```

**Implementation**: Add `--format` as a Click option on the `tickets` group (and all other command groups). If present on the subcommand, it overrides the top-level value.

### 5.2 `rally-cli tickets show <TICKET_ID>`

Fetch and display full details for a single ticket.

```bash
rally-cli tickets show US12345
rally-cli tickets show US12345 --format json
rally-cli tickets show DE67890 --format json | jq '.data.description'
```

**Text output:**
```
US12345 - Implement OAuth2 login flow
========================================
Type:        User Story
State:       In-Progress
Owner:       Daniel Elliot
Iteration:   FY26-Q1 PI Sprint 7
Points:      3
Release:     2026.Q1
Parent:      F59625 - Authentication Epic
Tags:        security, oauth, sprint-goal
Blocked:     No
Ready:       Yes
Created:     2026-01-15
Updated:     2026-02-20

Acceptance Criteria:
  - User can log in via Google OAuth
  - Session persists across page refresh
  - Logout clears session

Description:
  As a user, I want to log in using OAuth2 so that I don't need
  to manage a separate password for this application.

Notes:
  Implementation uses passport.js middleware. Token refresh
  handled automatically by the client SDK.
```

**JSON output:**
```json
{
  "success": true,
  "data": {
    "formatted_id": "US12345",
    "name": "Implement OAuth2 login flow",
    "ticket_type": "UserStory",
    "state": "In-Progress",
    "owner": "Daniel Elliot",
    "description": "As a user...",
    "notes": "Implementation uses...",
    "acceptance_criteria": "- User can log in via Google OAuth\n...",
    "iteration": "FY26-Q1 PI Sprint 7",
    "points": 3,
    "release": "2026.Q1",
    "parent_id": "F59625",
    "tags": ["security", "oauth", "sprint-goal"],
    "blocked": false,
    "blocked_reason": "",
    "ready": true,
    "creation_date": "2026-01-15T10:30:00Z",
    "last_update_date": "2026-02-20T14:22:00Z",
    "object_id": "123456789"
  },
  "error": null
}
```

### 5.3 `rally-cli tickets update <TICKET_ID> [OPTIONS]`

Update one or more fields on a ticket.

```bash
# Change state
rally-cli tickets update US12345 --state "Completed"

# Change owner
rally-cli tickets update US12345 --owner "Jane Smith"

# Change iteration
rally-cli tickets update US12345 --iteration "FY26-Q1 PI Sprint 8"

# Change points
rally-cli tickets update US12345 --points 5

# Set parent feature
rally-cli tickets update US12345 --parent F59625

# Set description from file
rally-cli tickets update US12345 --description-file desc.md

# Set acceptance criteria from file
rally-cli tickets update US12345 --ac-file ac.md

# Set notes
rally-cli tickets update US12345 --notes "Implementation complete, PR #42 merged"

# Set blocked status
rally-cli tickets update US12345 --blocked --blocked-reason "Waiting on API team"

# Unblock
rally-cli tickets update US12345 --no-blocked

# Set release
rally-cli tickets update US12345 --release "2026.Q1"

# Remove from iteration (move to backlog)
rally-cli tickets update US12345 --no-iteration

# Multiple fields at once
rally-cli tickets update US12345 --state "In-Progress" --points 3 --owner "Daniel Elliot"

# JSON output for scripting
rally-cli tickets update US12345 --state "Completed" --format json
```

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--state TEXT` | str | Workflow state (FlowState name) |
| `--owner TEXT` | str | Owner display name |
| `--iteration TEXT` | str | Iteration name |
| `--no-iteration` | flag | Remove from iteration (backlog) |
| `--points FLOAT` | float | Story points (PlanEstimate) |
| `--parent TEXT` | str | Parent Feature formatted ID |
| `--release TEXT` | str | Release name |
| `--no-release` | flag | Remove release assignment |
| `--name TEXT` | str | Rename the ticket |
| `--description TEXT` | str | Set description (inline) |
| `--description-file PATH` | file | Set description from file |
| `--notes TEXT` | str | Set notes (inline) |
| `--notes-file PATH` | file | Set notes from file |
| `--ac TEXT` | str | Set acceptance criteria (inline) |
| `--ac-file PATH` | file | Set acceptance criteria from file |
| `--blocked / --no-blocked` | flag | Set/clear blocked status |
| `--blocked-reason TEXT` | str | Reason for blocking |
| `--ready / --no-ready` | flag | Set/clear ready status |
| `--expedite / --no-expedite` | flag | Set/clear expedite flag |
| `--severity TEXT` | str | Severity (Defect only) |
| `--priority TEXT` | str | Priority (Defect only) |
| `--target-date TEXT` | str | Target date (YYYY-MM-DD) |

**Output**: Returns the updated ticket in the selected format (text/json/csv).

### 5.4 `rally-cli tickets delete <TICKET_ID>`

Delete a ticket from Rally. Requires `--confirm` flag for safety.

```bash
rally-cli tickets delete US12345 --confirm
rally-cli tickets delete DE67890 --confirm --format json
```

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--confirm` | flag | **Required** safety flag |

### 5.5 Extended Ticket Model Fields

Update `_to_ticket()` in `AsyncRallyClient` to populate new fields. Update `DEFAULT_FETCH_FIELDS` in `rally_api.py` to request additional fields from the API.

**New fetch fields for HierarchicalRequirement / Defect:**
- `c_AcceptanceCriteria` (custom field - may not exist in all workspaces)
- `Blocked`
- `BlockedReason`
- `ScheduleState`
- `Severity` (Defect only)
- `Priority` (Defect only)
- `Release`
- `Tags`
- `Ready`
- `Expedite`
- `TargetDate`
- `CreationDate`
- `LastUpdateDate`

### 5.6 Implementation Checklist - Phase 1

**Service Layer:**
- [ ] Add new fields to `DEFAULT_FETCH_FIELDS` in `rally_api.py`
- [ ] Extend `_to_ticket()` in `AsyncRallyClient` to populate new Ticket fields
- [ ] Add `update_ticket(ticket, fields)` method to `AsyncRallyClient`
- [ ] Add `update_description()`, `update_notes()` convenience methods
- [ ] Add `set_iteration(ticket, name)` method to `AsyncRallyClient`
- [ ] Add `delete_ticket(formatted_id)` method to `AsyncRallyClient`
- [ ] Update `RallyClientProtocol` with new method signatures
- [ ] Update `MockRallyClient` and `AsyncMockRallyClient` with new methods

**Model Layer:**
- [ ] Extend `Ticket` dataclass with new fields (acceptance_criteria, blocked, blocked_reason, schedule_state, severity, priority, release, tags, ready, expedite, target_date, creation_date, last_update_date)
- [ ] Update `asdict()` serialization to handle tuple fields (tags)
- [ ] Update `sample_data.py` with new fields

**CLI Layer:**
- [ ] Add `--format` option to `tickets` group (and all future command groups)
- [ ] Implement format override logic (subcommand --format takes precedence over global)
- [ ] Add `tickets show` subcommand in `commands/query.py`
- [ ] Add `tickets update` subcommand in `commands/query.py`
- [ ] Add `tickets delete` subcommand in `commands/query.py`
- [ ] Add `format_ticket_detail()` method to all formatters (for show command)
- [ ] Add `format_update_result()` method to all formatters
- [ ] Add `format_delete_result()` method to all formatters

**Testing:**
- [ ] Unit tests for extended Ticket model (new fields, defaults, serialization)
- [ ] Unit tests for `update_ticket()` with various field combinations
- [ ] Unit tests for `delete_ticket()`
- [ ] Unit tests for `tickets show` command (text, json, csv output)
- [ ] Unit tests for `tickets update` command (all options)
- [ ] Unit tests for `tickets delete` command (with/without --confirm)
- [ ] Unit tests for --format override logic
- [ ] Integration tests with AsyncMockRallyClient
- [ ] Test backward compatibility: existing `rally-cli tickets` and `rally-cli --format json tickets` still work

**Documentation:**
- [ ] Update `docs/CLI.md` with new commands
- [ ] Add examples for `tickets show`, `tickets update`, `tickets delete`

---

## 6. Phase 2: Discussions, Iterations & Users

**Goal**: Add list commands for discussions, iterations, and users.

### 6.1 `rally-cli discussions <TICKET_ID>`

List discussion comments for a ticket.

```bash
rally-cli discussions US12345
rally-cli discussions US12345 --format json
rally-cli discussions US12345 --format json | jq '.data[].text'
```

**Text output:**
```
Discussions for US12345 (3 comments)
====================================

Daniel Elliot - Feb 15, 2026 10:30 AM
  Started working on the OAuth integration.
  PR #42 is up for review.

Jane Smith - Feb 16, 2026 02:15 PM
  Reviewed the PR. Looks good, minor
  feedback on error handling.

Daniel Elliot - Feb 17, 2026 09:00 AM
  Addressed all feedback. Ready for merge.
```

**JSON output:**
```json
{
  "success": true,
  "data": [
    {
      "object_id": "111222333",
      "text": "Started working on the OAuth integration...",
      "user": "Daniel Elliot",
      "created_at": "2026-02-15T10:30:00Z",
      "artifact_id": "US12345"
    }
  ],
  "error": null
}
```

### 6.2 `rally-cli iterations`

List iterations/sprints.

```bash
rally-cli iterations
rally-cli iterations --count 10
rally-cli iterations --format json
rally-cli iterations --current            # Show only current iteration
rally-cli iterations --future             # Show future iterations
rally-cli iterations --state "Committed"  # Filter by state
```

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--count INT` | int | Number of iterations to show (default: 5) |
| `--current` | flag | Show only the current iteration |
| `--future` | flag | Show future iterations |
| `--past` | flag | Show past iterations only |
| `--state TEXT` | str | Filter by state (Planning, Committed, Accepted) |
| `--format` | choice | Output format |

**Text output:**
```
Iterations
==========
Name                          Start       End         State      Current
FY26-Q1 PI Sprint 7          Feb 10      Feb 21      Committed  *
FY26-Q1 PI Sprint 6          Jan 27      Feb 07      Accepted
FY26-Q1 PI Sprint 5          Jan 13      Jan 24      Accepted
FY26-Q1 PI Sprint 8          Feb 24      Mar 07      Planning
FY26-Q1 PI Sprint 9          Mar 10      Mar 21      Planning
```

### 6.3 `rally-cli users`

List project team members.

```bash
rally-cli users
rally-cli users --format json
rally-cli users --search "Daniel"
```

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--search TEXT` | str | Filter users by display name |
| `--format` | choice | Output format |

**Text output:**
```
Team Members
============
Name              Username
Daniel Elliot     daniel.elliot@broadcom.com
Jane Smith        jane.smith@broadcom.com
Bob Johnson       bob.johnson@broadcom.com
```

### 6.4 Implementation Checklist - Phase 2

**CLI Layer:**
- [ ] Create `commands/discussions.py` with `discussions` command
- [ ] Create `commands/iterations.py` with `iterations` command
- [ ] Create `commands/users.py` with `users` command
- [ ] Add `--format` option to each new command
- [ ] Register new commands in `cli/main.py`

**Formatters:**
- [ ] Add `format_discussions()` method to BaseFormatter and all implementations
- [ ] Add `format_iterations()` method to BaseFormatter and all implementations
- [ ] Add `format_users()` method to BaseFormatter and all implementations

**Service Layer:**
- [ ] Add `get_future_iterations()` method to AsyncRallyClient
- [ ] Update `get_iterations()` to accept state filter parameter

**Testing:**
- [ ] Unit tests for `discussions` command (text, json, csv)
- [ ] Unit tests for `iterations` command (all options, all formats)
- [ ] Unit tests for `users` command (all options, all formats)
- [ ] Test with empty results
- [ ] Test error cases (ticket not found for discussions, no API key)

**Documentation:**
- [ ] Update `docs/CLI.md` with discussions, iterations, users commands
- [ ] Add scripting examples

---

## 7. Phase 3: Releases & Tags

**Goal**: Add release and tag management to both service layer and CLI.

### 7.1 `rally-cli releases`

```bash
rally-cli releases
rally-cli releases --format json
rally-cli releases --current             # Show only current/active release
rally-cli releases --state "Active"      # Filter by state
```

**Text output:**
```
Releases
========
Name          Start       End         State    Theme
2026.Q1       Jan 01      Mar 31      Active   Security hardening
2025.Q4       Oct 01      Dec 31      Locked   Performance sprint
2026.Q2       Apr 01      Jun 30      Planning API v2 migration
```

### 7.2 `rally-cli tags`

```bash
rally-cli tags                           # List all tags
rally-cli tags --format json
rally-cli tags create "sprint-goal"      # Create a new tag
rally-cli tags add US12345 "sprint-goal" # Add tag to ticket
rally-cli tags remove US12345 "sprint-goal" # Remove tag from ticket
```

### 7.3 Release Assignment via `tickets update`

```bash
rally-cli tickets update US12345 --release "2026.Q1"
rally-cli tickets update US12345 --no-release   # Unschedule
```

### 7.4 Tag Management via `tickets update`

```bash
rally-cli tickets update US12345 --add-tag "sprint-goal"
rally-cli tickets update US12345 --remove-tag "backlog"
```

### 7.5 Service Layer Additions

```python
# New methods in AsyncRallyClient

async def get_releases(self, count: int = 10) -> list[Release]:
    """Fetch releases from Rally."""

async def get_release(self, name: str) -> Release | None:
    """Fetch a single release by name."""

async def set_release(self, ticket: Ticket, release_name: str | None) -> Ticket | None:
    """Set or remove release assignment on a ticket."""

async def get_tags(self) -> list[Tag]:
    """Fetch all tags in the workspace."""

async def add_tag(self, ticket: Ticket, tag_name: str) -> bool:
    """Add a tag to a ticket. Creates the tag if it doesn't exist."""

async def remove_tag(self, ticket: Ticket, tag_name: str) -> bool:
    """Remove a tag from a ticket."""

async def create_tag(self, name: str) -> Tag | None:
    """Create a new tag."""
```

### 7.6 New Data Models

```python
# models/release.py
@dataclass(frozen=True)
class Release:
    object_id: str
    name: str
    start_date: date
    end_date: date
    state: str = "Planning"  # Planning, Active, Locked
    theme: str = ""
    notes: str = ""

    @property
    def is_current(self) -> bool:
        today = date.today()
        return self.start_date <= today <= self.end_date

    @property
    def formatted_dates(self) -> str:
        start = self.start_date.strftime("%b %d")
        end = self.end_date.strftime("%b %d")
        return f"{start} - {end}"

# models/tag.py
@dataclass(frozen=True)
class Tag:
    object_id: str
    name: str
```

### 7.7 Implementation Checklist - Phase 3

**Model Layer:**
- [ ] Create `models/release.py` with Release dataclass
- [ ] Create `models/tag.py` with Tag dataclass
- [ ] Update `models/__init__.py` to export Release and Tag
- [ ] Update Ticket model to include `release` and `tags` fields

**Service Layer:**
- [ ] Add Release entity to `ENTITY_TYPES` and `DEFAULT_FETCH_FIELDS` in `rally_api.py`
- [ ] Add Tag entity to `ENTITY_TYPES` and `DEFAULT_FETCH_FIELDS` in `rally_api.py`
- [ ] Add `get_releases()` method to AsyncRallyClient
- [ ] Add `get_release()` method to AsyncRallyClient
- [ ] Add `set_release()` method to AsyncRallyClient
- [ ] Add `get_tags()` method to AsyncRallyClient
- [ ] Add `add_tag()` method to AsyncRallyClient (uses `addCollectionItems` pattern)
- [ ] Add `remove_tag()` method to AsyncRallyClient (uses `dropCollectionItems` pattern)
- [ ] Add `create_tag()` method to AsyncRallyClient
- [ ] Update `_to_ticket()` to parse Release and Tags from API response
- [ ] Update protocol.py with new method signatures
- [ ] Update MockRallyClient with mock release/tag data

**CLI Layer:**
- [ ] Create `commands/releases.py` with `releases` command
- [ ] Create `commands/tags.py` with `tags` group (list, create, add, remove)
- [ ] Add `--release`, `--no-release`, `--add-tag`, `--remove-tag` to `tickets update`
- [ ] Register new commands in `cli/main.py`

**Formatters:**
- [ ] Add `format_releases()` method to all formatters
- [ ] Add `format_tags()` method to all formatters

**Testing:**
- [ ] Unit tests for Release model
- [ ] Unit tests for Tag model
- [ ] Unit tests for release service methods
- [ ] Unit tests for tag service methods
- [ ] Unit tests for `releases` CLI command
- [ ] Unit tests for `tags` CLI commands
- [ ] Unit tests for `--release` and tag options on `tickets update`
- [ ] Integration tests with mock data

**Documentation:**
- [ ] Update `docs/CLI.md` with releases and tags commands
- [ ] Add `rally_api.py` constants for Release and Tag entities

---

## 8. Phase 4: Attachments & Portfolio Items

**Goal**: Expose attachment operations and portfolio item hierarchy through CLI.

### 8.1 `rally-cli attachments list <TICKET_ID>`

```bash
rally-cli attachments list US12345
rally-cli attachments list US12345 --format json
```

**Text output:**
```
Attachments for US12345 (3 files)
==================================
#   Name                           Size       Type
1   requirements.pdf               245 KB     pdf
2   screenshot.png                 1.2 MB     png
3   test-data.csv                  12 KB      csv
```

### 8.2 `rally-cli attachments download <TICKET_ID> <FILENAME>`

```bash
rally-cli attachments download US12345 requirements.pdf
rally-cli attachments download US12345 requirements.pdf --output /tmp/requirements.pdf
rally-cli attachments download US12345 --all --output-dir ./attachments/
```

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--output PATH` | str | Output file path (default: current directory) |
| `--all` | flag | Download all attachments |
| `--output-dir PATH` | str | Directory for --all downloads |

### 8.3 `rally-cli attachments upload <TICKET_ID> <FILE>`

```bash
rally-cli attachments upload US12345 ./screenshot.png
rally-cli attachments upload US12345 ./screenshot.png --format json
```

### 8.4 `rally-cli features` (Portfolio Items)

```bash
rally-cli features                           # List features in project
rally-cli features --format json
rally-cli features show F59625               # Show feature details
rally-cli features show F59625 --children    # Show child stories
```

**Text output (list):**
```
Features
========
ID       Name                           State       Owner          Stories
F59625   Authentication Epic            In Progress Daniel Elliot  12
F59627   Dashboard Redesign             Defined     Jane Smith     8
F59628   API v2 Migration               Planning    Bob Johnson    23
```

**Text output (show --children):**
```
F59625 - Authentication Epic
=============================
State:    In Progress
Owner:    Daniel Elliot
Release:  2026.Q1

Child Stories:
  US12345  In-Progress  Implement OAuth2 login flow
  US12346  Completed    Add SSO support
  US12347  Defined      Password reset redesign
```

### 8.5 Implementation Checklist - Phase 4

**CLI Layer:**
- [ ] Create `commands/attachments.py` with `attachments` group (list, download, upload)
- [ ] Create `commands/features.py` with `features` group (list, show)
- [ ] Add `--children` flag to `features show`
- [ ] Register new commands in `cli/main.py`

**Service Layer:**
- [ ] Add `get_features(query)` method to AsyncRallyClient
- [ ] Add `get_feature_children(feature_id)` method to AsyncRallyClient
- [ ] Extend `get_feature()` to return full Feature details (not just tuple)
- [ ] Add PortfolioItem/Feature to expanded fetch fields

**Formatters:**
- [ ] Add `format_attachments()` method to all formatters
- [ ] Add `format_features()` method to all formatters
- [ ] Add `format_feature_detail()` method to all formatters

**Testing:**
- [ ] Unit tests for `attachments list` command
- [ ] Unit tests for `attachments download` command (mock file I/O)
- [ ] Unit tests for `attachments upload` command (mock file I/O)
- [ ] Unit tests for `features` command
- [ ] Unit tests for `features show --children`
- [ ] Integration tests with mock data

**Documentation:**
- [ ] Update `docs/CLI.md` with attachments and features commands

---

## 9. Phase 5: Search, Bulk Operations & UX Polish

**Goal**: Add full-text search, bulk CLI operations, and UX improvements.

### 9.1 `rally-cli search <QUERY>`

Full-text search across tickets.

```bash
rally-cli search "OAuth login"
rally-cli search "OAuth login" --format json
rally-cli search "OAuth login" --type UserStory
rally-cli search "OAuth login" --state "In-Progress"
```

**Implementation**: Uses Rally WSAPI `contains` operator:
```
((Name contains "OAuth login") OR (Description contains "OAuth login"))
```

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--type TEXT` | str | Filter by ticket type |
| `--state TEXT` | str | Filter by state |
| `--current-iteration` | flag | Limit to current iteration |
| `--limit INT` | int | Max results (default: 50) |
| `--format` | choice | Output format |

### 9.2 Bulk Operations via Pipe/Multi-ID

```bash
# Update multiple tickets (space-separated)
rally-cli tickets update US12345 US12346 US12347 --state "Completed"

# Pipe ticket IDs from a query
rally-cli tickets --current-iteration --format json | \
  jq -r '.data[] | select(.state == "Defined") | .formatted_id' | \
  xargs rally-cli tickets update --state "In-Progress"

# Bulk comment
rally-cli tickets --current-iteration --format json | \
  jq -r '.data[].formatted_id' | \
  xargs -I {} rally-cli comment {} "Sprint review completed"

# Move all my tickets to next sprint
rally-cli tickets --current-iteration --my-tickets --format json | \
  jq -r '.data[].formatted_id' | \
  xargs rally-cli tickets update --iteration "FY26-Q1 PI Sprint 8"
```

**Implementation**: Modify `tickets update` to accept multiple TICKET_ID arguments:

```python
@tickets.command("update")
@click.argument("ticket_ids", nargs=-1, required=True)
# ... options ...
def tickets_update(ctx, ticket_ids, **kwargs):
    """Update one or more tickets."""
```

### 9.3 `rally-cli config`

Show current configuration (for debugging).

```bash
rally-cli config
rally-cli config --format json
```

**Text output:**
```
Rally CLI Configuration
=======================
Server:     rally1.rallydev.com
Workspace:  My Workspace
Project:    My Project
User:       Daniel Elliot
Iteration:  FY26-Q1 PI Sprint 7
API Key:    ****...1234 (set via RALLY_APIKEY)
```

### 9.4 Shell Completions

```bash
# Generate completions
rally-cli completions bash > /etc/bash_completion.d/rally-cli
rally-cli completions zsh > ~/.zsh/completions/_rally-cli
rally-cli completions fish > ~/.config/fish/completions/rally-cli.fish
```

**Implementation**: Use Click's built-in shell completion support (`click.shell_complete`).

### 9.5 Summary / Sprint Report

```bash
# Sprint summary
rally-cli summary
rally-cli summary --format json
rally-cli summary --iteration "FY26-Q1 PI Sprint 7"
```

**Text output:**
```
Sprint Summary: FY26-Q1 PI Sprint 7 (Feb 10 - Feb 21)
=======================================================
Total Tickets:  24
Total Points:   47

By State:
  Defined:       5 tickets,  12 points
  In-Progress:   8 tickets,  18 points
  Completed:     9 tickets,  14 points
  Accepted:      2 tickets,   3 points

By Owner:
  Daniel Elliot: 6 tickets,  15 points
  Jane Smith:    8 tickets,  16 points
  Bob Johnson:  10 tickets,  16 points

Blocked: 2 tickets
  US12345 - Waiting on API team
  DE67890 - Environment issue
```

### 9.6 `rally-cli open <TICKET_ID>`

Open a ticket in the default web browser.

```bash
rally-cli open US12345   # Opens https://rally1.rallydev.com/#/detail/userstory/123456789
```

### 9.7 Implementation Checklist - Phase 5

**CLI Layer:**
- [ ] Create `commands/search.py` with `search` command
- [ ] Modify `tickets update` to accept multiple ticket IDs (`nargs=-1`)
- [ ] Create `commands/config.py` with `config` command
- [ ] Create `commands/completions.py` for shell completion generation
- [ ] Create `commands/summary.py` with `summary` command
- [ ] Create `commands/open_cmd.py` with `open` command (browser launch)
- [ ] Register all new commands in `cli/main.py`

**Service Layer:**
- [ ] Add `search_tickets(text, type, state, limit)` method to AsyncRallyClient
- [ ] Add `get_sprint_summary(iteration)` method to AsyncRallyClient

**Formatters:**
- [ ] Add `format_summary()` method to all formatters
- [ ] Add `format_config()` method to all formatters
- [ ] Add `format_search_results()` method to all formatters (reuse format_tickets)

**Testing:**
- [ ] Unit tests for `search` command
- [ ] Unit tests for bulk `tickets update` (multiple IDs)
- [ ] Unit tests for `config` command
- [ ] Unit tests for `summary` command
- [ ] Unit tests for `open` command (mock browser launch)
- [ ] Integration tests for piped bulk operations

**Documentation:**
- [ ] Update `docs/CLI.md` with search, bulk, config, summary, open commands
- [ ] Add shell completion installation instructions
- [ ] Add bulk operation scripting examples

---

## 10. Rally WSAPI Entity Reference

### 10.1 Entity Types and URL Paths

| Entity | API Name | URL Path | Supported |
|--------|----------|----------|:---------:|
| User Story | `HierarchicalRequirement` | `hierarchicalrequirement` | Existing |
| Defect | `Defect` | `defect` | Existing |
| Task | `Task` | `task` | Existing |
| Test Case | `TestCase` | `testcase` | Existing |
| Iteration | `Iteration` | `iteration` | Existing |
| Feature | `PortfolioItem/Feature` | `portfolioitem/feature` | Existing |
| Initiative | `PortfolioItem/Initiative` | `portfolioitem/initiative` | Phase 4 |
| Release | `Release` | `release` | **Phase 3** |
| Tag | `Tag` | `tag` | **Phase 3** |
| User | `User` | `user` | Existing |
| Attachment | `Attachment` | `attachment` | Existing |
| AttachmentContent | `AttachmentContent` | `attachmentcontent` | Existing |
| ConversationPost | `ConversationPost` | `conversationpost` | Existing |
| FlowState | `FlowState` | `flowstate` | Existing |

### 10.2 User Story Fields (HierarchicalRequirement)

| Field | API Name | Type | In Model? |
|-------|----------|------|:---------:|
| ID | FormattedID | string | Yes |
| Name | Name | string | Yes |
| Description | Description | text/html | Yes |
| Notes | Notes | text/html | Yes |
| Owner | Owner | ref | Yes |
| State | FlowState | ref | Yes |
| Schedule State | ScheduleState | string | **Phase 1** |
| Iteration | Iteration | ref | Yes |
| Points | PlanEstimate | decimal | Yes |
| Parent Feature | PortfolioItem | ref | Yes |
| Object ID | ObjectID | int | Yes |
| Acceptance Criteria | c_AcceptanceCriteria | text | **Phase 1** |
| Blocked | Blocked | bool | **Phase 1** |
| Blocked Reason | BlockedReason | text | **Phase 1** |
| Release | Release | ref | **Phase 3** |
| Tags | Tags | collection | **Phase 3** |
| Ready | Ready | bool | **Phase 1** |
| Expedite | Expedite | bool | **Phase 1** |
| Target Date | TargetDate | date | **Phase 1** |
| Creation Date | CreationDate | datetime | **Phase 1** |
| Last Update Date | LastUpdateDate | datetime | **Phase 1** |
| Task Status | TaskStatus | string | Future |
| Test Case Status | TestCaseStatus | string | Future |
| Predecessors | Predecessors | collection | Future |
| Successors | Successors | collection | Future |

### 10.3 Defect-Specific Fields

| Field | API Name | Type | In Model? |
|-------|----------|------|:---------:|
| Severity | Severity | string | **Phase 1** |
| Priority | Priority | string | **Phase 1** |
| Environment | Environment | string | Future |
| Found In Build | FoundInBuild | string | Future |
| Fixed In Build | FixedInBuild | string | Future |
| Target Build | TargetBuild | string | Future |
| Verified In Build | VerifiedInBuild | string | Future |
| Resolution | Resolution | string | Future |
| Duplicates | Duplicates | collection | Future |

---

## 11. Testing Strategy

### 11.1 Test Architecture

```
tests/
  cli/                              # NEW: CLI-specific tests
    __init__.py
    test_tickets_show.py            # show subcommand tests
    test_tickets_update.py          # update subcommand tests
    test_tickets_delete.py          # delete subcommand tests
    test_discussions.py             # discussions command tests
    test_iterations.py              # iterations command tests
    test_releases.py                # releases command tests
    test_tags.py                    # tags command tests
    test_users.py                   # users command tests
    test_attachments.py             # attachments command tests
    test_features.py                # features command tests
    test_search.py                  # search command tests
    test_summary.py                 # summary command tests
    test_config.py                  # config command tests
    test_format_override.py         # --format on subcommand tests
    test_bulk_operations.py         # multi-ID update tests
    test_backward_compat.py         # v0.8.3 command compatibility tests
  test_release_model.py             # Release model unit tests
  test_tag_model.py                 # Tag model unit tests
  test_extended_ticket_model.py     # Extended Ticket field tests
```

### 11.2 Testing Approach

| Test Type | Tool | Coverage Target |
|-----------|------|-----------------|
| Unit (models) | pytest | 100% |
| Unit (formatters) | pytest | 100% |
| Unit (CLI commands) | pytest + Click CliRunner | 95% |
| Unit (service methods) | pytest + AsyncMockRallyClient | 95% |
| Integration | pytest + mock client | 90% |
| Manual QA | Real Rally API | All new commands |

### 11.3 Click CliRunner Pattern

```python
from click.testing import CliRunner
from rally_tui.cli.main import cli

def test_tickets_show_json(mock_async_client):
    """Test tickets show with JSON output."""
    runner = CliRunner()
    result = runner.invoke(cli, [
        "--apikey", "test_key",
        "--format", "json",
        "tickets", "show", "US12345",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["formatted_id"] == "US12345"
```

### 11.4 Backward Compatibility Tests

Every existing CLI invocation must continue to work:

```python
def test_backward_compat_tickets_list():
    """v0.8.3: rally-cli tickets --current-iteration --my-tickets"""
    runner = CliRunner()
    result = runner.invoke(cli, [
        "--apikey", "test_key",
        "tickets", "--current-iteration", "--my-tickets",
    ])
    assert result.exit_code == 0

def test_backward_compat_format_on_group():
    """v0.8.3: rally-cli --format json tickets --current-iteration"""
    runner = CliRunner()
    result = runner.invoke(cli, [
        "--apikey", "test_key",
        "--format", "json",
        "tickets", "--current-iteration",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "data" in data

def test_backward_compat_comment():
    """v0.8.3: rally-cli comment US12345 'text'"""
    runner = CliRunner()
    result = runner.invoke(cli, [
        "--apikey", "test_key",
        "comment", "US12345", "Test message",
    ])
    assert result.exit_code == 0

def test_backward_compat_tickets_create():
    """v0.8.3: rally-cli tickets create 'Title' --type UserStory"""
    runner = CliRunner()
    result = runner.invoke(cli, [
        "--apikey", "test_key",
        "tickets", "create", "Test Ticket",
        "--type", "UserStory",
    ])
    assert result.exit_code == 0
```

---

## 12. Migration & Compatibility

### 12.1 Backward Compatibility Guarantees

| Aspect | Guarantee |
|--------|-----------|
| Existing CLI commands | 100% backward compatible |
| `--format` on top-level group | Continues to work |
| Exit codes | Unchanged (0, 1, 2, 3, 4) |
| Environment variables | Unchanged (RALLY_APIKEY, etc.) |
| pyproject.toml entry points | `rally-cli` unchanged |
| TUI (`rally-tui`) | Completely unaffected |
| Existing Ticket model fields | All preserved, only new fields added |

### 12.2 Version Bump Strategy

| Phase | Version | Release Type |
|-------|---------|-------------|
| Phase 1 | 0.9.0 | Minor (new features, backward compatible) |
| Phase 2 | 0.10.0 | Minor |
| Phase 3 | 0.11.0 | Minor |
| Phase 4 | 0.12.0 | Minor |
| Phase 5 | 1.0.0 | Major (feature-complete CLI) |

### 12.3 Breaking Changes

**None planned.** All changes are additive:
- New Ticket fields have defaults (empty string, False, None, empty tuple)
- New commands do not affect existing commands
- New formatter methods do not change existing method signatures
- New service methods do not change existing method signatures

### 12.4 Deprecation Notice

The `--format` option on the top-level group (`rally-cli --format json tickets`) will be marked as deprecated in v1.0.0 documentation (but will continue to work indefinitely). Users should prefer `rally-cli tickets --format json`.

---

## 13. Complete Command Reference (Post-Enhancement)

```
rally-cli [GLOBAL_OPTIONS] COMMAND [ARGS]

GLOBAL OPTIONS:
  --server TEXT               Rally server hostname (default: rally1.rallydev.com)
  --apikey TEXT               Rally API key (or RALLY_APIKEY env var)
  --workspace TEXT            Workspace name (or RALLY_WORKSPACE env var)
  --project TEXT              Project name (or RALLY_PROJECT env var)
  --format [text|json|csv]    Output format (default: text) -- DEPRECATED, use on subcommand
  -v, --verbose               Enable verbose logging
  -q, --quiet                 Suppress non-essential output
  --version                   Show version and exit

TICKET COMMANDS:
  rally-cli tickets [--current-iteration] [--my-tickets] [--iteration TEXT]
                    [--owner TEXT] [--state TEXT] [--ticket-type TYPE]
                    [--query TEXT] [--fields TEXT] [--sort-by TEXT]
                    [--format FORMAT]

  rally-cli tickets show <TICKET_ID> [--format FORMAT]

  rally-cli tickets create <NAME> [--type TYPE] [--description TEXT]
                    [--points FLOAT] [--backlog] [--format FORMAT]

  rally-cli tickets update <TICKET_ID> [TICKET_ID...]
                    [--state TEXT] [--owner TEXT] [--iteration TEXT]
                    [--no-iteration] [--points FLOAT] [--parent TEXT]
                    [--release TEXT] [--no-release] [--name TEXT]
                    [--description TEXT] [--description-file PATH]
                    [--notes TEXT] [--notes-file PATH]
                    [--ac TEXT] [--ac-file PATH]
                    [--blocked/--no-blocked] [--blocked-reason TEXT]
                    [--ready/--no-ready] [--expedite/--no-expedite]
                    [--severity TEXT] [--priority TEXT]
                    [--target-date TEXT] [--add-tag TEXT] [--remove-tag TEXT]
                    [--format FORMAT]

  rally-cli tickets delete <TICKET_ID> --confirm [--format FORMAT]

COMMENT:
  rally-cli comment <TICKET_ID> [MESSAGE] [--message-file PATH]
                    [--format FORMAT]

DISCUSSIONS:
  rally-cli discussions <TICKET_ID> [--format FORMAT]

ITERATIONS:
  rally-cli iterations [--count INT] [--current] [--future] [--past]
                    [--state TEXT] [--format FORMAT]

RELEASES:
  rally-cli releases [--current] [--state TEXT] [--format FORMAT]

USERS:
  rally-cli users [--search TEXT] [--format FORMAT]

ATTACHMENTS:
  rally-cli attachments list <TICKET_ID> [--format FORMAT]
  rally-cli attachments download <TICKET_ID> <FILENAME>
                    [--output PATH] [--all] [--output-dir PATH]
  rally-cli attachments upload <TICKET_ID> <FILE> [--format FORMAT]

FEATURES:
  rally-cli features [--format FORMAT]
  rally-cli features show <FEATURE_ID> [--children] [--format FORMAT]

TAGS:
  rally-cli tags [--format FORMAT]
  rally-cli tags create <NAME>
  rally-cli tags add <TICKET_ID> <TAG_NAME>
  rally-cli tags remove <TICKET_ID> <TAG_NAME>

SEARCH:
  rally-cli search <QUERY> [--type TYPE] [--state TEXT]
                    [--current-iteration] [--limit INT] [--format FORMAT]

SUMMARY:
  rally-cli summary [--iteration TEXT] [--format FORMAT]

CONFIG:
  rally-cli config [--format FORMAT]

OPEN:
  rally-cli open <TICKET_ID>

COMPLETIONS:
  rally-cli completions [bash|zsh|fish]
```

---

## 14. Implementation Priority Matrix

| Phase | Commands | Effort | Impact | Priority |
|-------|----------|--------|--------|----------|
| Phase 1 | tickets show/update/delete, --format fix, extended fields | 3-4 days | HIGHEST | P0 |
| Phase 2 | discussions, iterations, users | 2-3 days | HIGH | P1 |
| Phase 3 | releases, tags | 2-3 days | MEDIUM | P2 |
| Phase 4 | attachments, features | 2-3 days | MEDIUM | P2 |
| Phase 5 | search, bulk, summary, config, open, completions | 3-4 days | MEDIUM | P3 |

**Total estimated effort**: 12-17 development days for a single developer.

---

## 15. Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Custom field `c_AcceptanceCriteria` not in all workspaces | Medium | Medium | Graceful fallback to empty string, document as optional |
| Rally API rate limiting with bulk operations | High | Low | Use existing semaphore (5 concurrent), add per-request delay option |
| Breaking changes to Ticket model affecting TUI | High | Low | All new fields have defaults, TUI unaffected |
| Large test matrix growth | Medium | High | Focus on Click CliRunner tests, reuse existing mock infrastructure |
| Tag/Release collection operations differ from simple field updates | Medium | Medium | Use Rally's `addCollectionItems`/`dropCollectionItems` pattern via raw HTTP |
| `--format` placement change causing confusion | Low | Medium | Support BOTH placements indefinitely, deprecation notice only |

---

## 16. Definition of Done

A phase is considered done when:

1. All checklist items for the phase are complete
2. All new commands work with `--format text`, `--format json`, and `--format csv`
3. All new commands have proper exit codes (0, 1, 2, 3, 4)
4. Test coverage for new code exceeds 90%
5. `docs/CLI.md` is updated with new command documentation
6. All existing commands pass backward compatibility tests
7. Manual QA against real Rally API confirms functionality
8. `ruff check` and `mypy` pass with no errors
9. CI pipeline passes (pytest across Python 3.11, 3.12, 3.13)
10. Version bumped in `pyproject.toml`

---

## Appendix A: Rally WSAPI Query Quick Reference

### Operators

| Operator | Example |
|----------|---------|
| `=` | `(State = "Open")` |
| `!=` | `(State != "Closed")` |
| `<` / `>` | `(CreationDate > "2026-01-01")` |
| `<=` / `>=` | `(PlanEstimate >= 3)` |
| `contains` | `(Name contains "login")` |
| `!contains` | `(Name !contains "test")` |
| `in` | `(Severity in "High,Critical")` |

### Combining

```
((State = "Open") AND (Severity = "Major Problem"))
((Priority = "High") OR (Priority = "Critical"))
```

### Null checks

```
(Owner = null)
(Owner != null)
```

### Nested fields

```
(Owner.DisplayName = "Daniel Elliot")
(Iteration.Name = "Sprint 7")
(Project.Name = "My Project")
(PortfolioItem.FormattedID = "F59625")
```

---

## Appendix B: Scripting Cookbook (Post-Enhancement)

### Daily Standup Report

```bash
#!/bin/bash
echo "=== My Current Sprint ==="
rally-cli tickets --current-iteration --my-tickets

echo ""
echo "=== In Progress ==="
rally-cli tickets --current-iteration --my-tickets --state "In-Progress"

echo ""
echo "=== Blocked ==="
rally-cli tickets --current-iteration --format json | \
  jq -r '.data[] | select(.blocked == true) | .formatted_id + " - " + .blocked_reason'
```

### CI/CD Integration

```bash
#!/bin/bash
# Post-deploy: update ticket and add comment
TICKET_ID="$1"
VERSION="$2"
ENV="$3"

rally-cli tickets update "$TICKET_ID" --state "Completed"
rally-cli comment "$TICKET_ID" "Deployed v${VERSION} to ${ENV} at $(date -u)"
rally-cli attachments upload "$TICKET_ID" ./build-report.pdf
```

### Sprint Velocity Tracking

```bash
#!/bin/bash
# Export last 5 sprints to CSV for velocity chart
for i in $(rally-cli iterations --count 5 --format json | jq -r '.data[].name'); do
  POINTS=$(rally-cli tickets --iteration "$i" --format json | \
    jq '[.data[].points // 0] | add')
  echo "${i},${POINTS}"
done
```

### Team Workload Balance

```bash
#!/bin/bash
rally-cli summary --format json | \
  jq -r '.data.by_owner[] | [.name, .ticket_count, .total_points] | @csv'
```

### Bulk State Transition

```bash
#!/bin/bash
# Move all Defined tickets to In-Progress
rally-cli tickets --current-iteration --state "Defined" --format json | \
  jq -r '.data[].formatted_id' | \
  xargs rally-cli tickets update --state "In-Progress"
```

### Acceptance Criteria Template

```bash
#!/bin/bash
# Set AC from a template file
rally-cli tickets update US12345 --ac-file templates/standard-ac.md
```

---

## Appendix C: Formatter Method Matrix

Each formatter (TextFormatter, JSONFormatter, CSVFormatter) must implement:

| Method | Phase | Used By |
|--------|-------|---------|
| `format_tickets()` | Existing | tickets list, search |
| `format_ticket_detail()` | Phase 1 | tickets show |
| `format_comment()` | Existing | comment |
| `format_update_result()` | Phase 1 | tickets update |
| `format_delete_result()` | Phase 1 | tickets delete |
| `format_discussions()` | Phase 2 | discussions |
| `format_iterations()` | Phase 2 | iterations |
| `format_users()` | Phase 2 | users |
| `format_releases()` | Phase 3 | releases |
| `format_tags()` | Phase 3 | tags |
| `format_attachments()` | Phase 4 | attachments list |
| `format_download_result()` | Phase 4 | attachments download |
| `format_upload_result()` | Phase 4 | attachments upload |
| `format_features()` | Phase 4 | features list |
| `format_feature_detail()` | Phase 4 | features show |
| `format_summary()` | Phase 5 | summary |
| `format_config()` | Phase 5 | config |
| `format_error()` | Existing | all commands |

---

**End of Document**
