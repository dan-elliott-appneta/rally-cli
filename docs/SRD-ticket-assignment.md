# Software Requirements Document: Ticket Assignment Feature

**Project:** rally-tui
**Feature:** Ticket Owner Assignment (Individual & Bulk)
**Version:** 1.0
**Date:** 2026-02-05
**Status:** Draft

---

## 1. Overview

This document specifies requirements for adding ticket owner assignment functionality to the rally-tui application. The feature enables users to assign individual tickets or multiple selected tickets to different owners through an intuitive interface. The implementation includes an owner cache system that maintains a list of unique ticket owners per iteration to provide a contextual selection list.

### Key Capabilities
- **Individual Assignment**: Assign a single ticket to a new owner from the ticket list view
- **Bulk Assignment**: Assign multiple selected tickets to the same owner in one operation
- **Owner Caching**: Automatically maintain a cached list of owners for each iteration
- **Smart Selection**: Present relevant owner choices based on the current iteration's team

---

## 2. Goals

### Primary Goals
1. Enable efficient ticket reassignment workflows for individual tickets
2. Support bulk reassignment operations for sprint planning and workload management
3. Provide contextual owner suggestions based on iteration team composition
4. Maintain consistency with existing rally-tui UX patterns and conventions
5. Ensure robust error handling and clear user feedback

### Secondary Goals
1. Minimize Rally API calls through intelligent caching
2. Support both keyboard-driven and mouse-based interactions
3. Provide clear visual feedback during assignment operations
4. Handle edge cases gracefully (no owners, user not in list, etc.)

---

## 3. User Stories

### US1: Individual Ticket Assignment
**As a** Rally user
**I want to** assign a single ticket to a different owner
**So that** I can quickly redistribute work items as team priorities change

**Acceptance Criteria:**
- Pressing the assignment keybinding on a focused ticket opens the owner selection screen
- Owner selection screen displays a list of owners from the current iteration
- Selecting an owner updates the ticket and refreshes the view
- Cancel returns to the ticket list without changes
- Success/failure notification is displayed after the operation

### US2: Bulk Ticket Assignment
**As a** Rally user
**I want to** assign multiple selected tickets to the same owner
**So that** I can efficiently redistribute workload during sprint planning

**Acceptance Criteria:**
- "Assign Owner" option appears in the bulk actions menu
- Selecting the option opens the owner selection screen
- The selected owner is assigned to all selected tickets
- Success count and failure count are displayed after the operation
- Failed assignments show clear error messages
- Updated tickets reflect the new owner in the list

### US3: Owner Cache Management
**As a** Rally user
**I want** owner suggestions to reflect the current iteration's team
**So that** I see relevant team members when assigning tickets

**Acceptance Criteria:**
- Owner cache is populated when tickets are loaded for an iteration
- Owner cache updates automatically when the iteration filter changes
- Owner cache contains unique owners extracted from loaded tickets
- Users can manually add an owner not in the cached list
- Backlog view includes owners from all loaded backlog tickets

### US4: Keyboard-Driven Assignment
**As a** power user
**I want to** assign tickets using keyboard shortcuts
**So that** I can work efficiently without using the mouse

**Acceptance Criteria:**
- Keybinding (e.g., 'a') opens assignment screen from ticket list
- Keybinding ('m' → option) opens assignment screen from bulk menu
- Owner selection supports vim-style navigation (j/k)
- Enter key confirms selection, Escape cancels

---

## 4. Technical Design

### 4.1 Data Models

#### 4.1.1 Owner/User Representation

Rally's User object contains the following relevant fields:
```python
{
    "ObjectID": "123456789",
    "DisplayName": "John Smith",
    "UserName": "jsmith@example.com",
    "EmailAddress": "jsmith@example.com",
    "_ref": "/user/123456789"
}
```

**Internal Model:**
```python
@dataclass
class Owner:
    """Represents a Rally user who can own tickets."""

    object_id: str              # Rally ObjectID for API calls
    display_name: str           # Full name for display
    user_name: str | None       # Username/email for reference

    def __hash__(self) -> int:
        """Hash by object_id for set/dict operations."""
        return hash(self.object_id)

    def __eq__(self, other: object) -> bool:
        """Equality based on object_id."""
        if not isinstance(other, Owner):
            return False
        return self.object_id == other.object_id
```

#### 4.1.2 Ticket Model Updates

No changes required to the existing `Ticket` model. The `owner` field already exists:
```python
@dataclass(frozen=True)
class Ticket:
    # ... existing fields ...
    owner: str | None = None  # Owner display name
```

### 4.2 Protocol Interface Additions

Add the following methods to `RallyClientProtocol` in `src/rally_tui/services/protocol.py`:

```python
class RallyClientProtocol(Protocol):
    # ... existing methods ...

    def get_users(self, display_names: list[str] | None = None) -> list[Owner]:
        """Fetch Rally users, optionally filtered by display names.

        Args:
            display_names: Optional list of display names to filter by.
                          If None, returns all users in the project.

        Returns:
            List of Owner objects representing Rally users.
        """
        ...

    def assign_owner(self, ticket: Ticket, owner: Owner) -> Ticket | None:
        """Assign a ticket to a new owner.

        Args:
            ticket: The ticket to update.
            owner: The owner to assign (Owner object with object_id).

        Returns:
            The updated Ticket with new owner, or None on failure.
        """
        ...

    def bulk_assign_owner(
        self, tickets: list[Ticket], owner: Owner
    ) -> BulkResult:
        """Assign owner to multiple tickets.

        Args:
            tickets: List of tickets to update.
            owner: The owner to assign to all tickets.

        Returns:
            BulkResult with success/failure counts and updated tickets.
        """
        ...
```

### 4.3 Owner Cache Design

#### 4.3.1 Cache Manager Extension

Extend the existing `CacheManager` class to support owner caching:

```python
class CacheManager:
    # ... existing methods ...

    def get_iteration_owners(self, iteration: str) -> set[Owner]:
        """Get cached owners for an iteration.

        Args:
            iteration: Iteration name or FILTER_BACKLOG constant.

        Returns:
            Set of Owner objects for the iteration.
        """
        ...

    def set_iteration_owners(
        self, iteration: str, owners: set[Owner]
    ) -> None:
        """Cache owners for an iteration.

        Args:
            iteration: Iteration name or FILTER_BACKLOG constant.
            owners: Set of Owner objects to cache.
        """
        ...

    def clear_iteration_owners(self, iteration: str | None = None) -> None:
        """Clear cached owners.

        Args:
            iteration: Specific iteration to clear, or None for all.
        """
        ...
```

**Cache Storage:**
```python
# In CacheManager.__init__:
self._iteration_owners: dict[str, set[Owner]] = {}
```

**Cache Key Format:**
```python
# Use iteration name directly as key
cache_key = iteration_name  # e.g., "Sprint 42" or FILTER_BACKLOG
```

#### 4.3.2 Owner Extraction Logic

Implement owner extraction from ticket list:

```python
def extract_owners_from_tickets(tickets: list[Ticket]) -> set[Owner]:
    """Extract unique owners from a list of tickets.

    Args:
        tickets: List of tickets to extract owners from.

    Returns:
        Set of Owner objects (unique by object_id).

    Notes:
        - Filters out None owners
        - Requires fetching full User objects from Rally API
        - Uses display name from tickets to query Rally for User objects
    """
    owner_names = {t.owner for t in tickets if t.owner}
    if not owner_names:
        return set()

    # Query Rally API to get full User objects for these display names
    client = get_client()  # Application client instance
    owners = client.get_users(display_names=list(owner_names))
    return set(owners)
```

#### 4.3.3 Cache Update Points

Owner cache updates occur at:

1. **Initial Ticket Load**: After loading tickets in `_load_initial_tickets_async()`
2. **Iteration Filter Change**: When user changes iteration in `action_iteration_filter()`
3. **Manual Refresh**: When user triggers cache refresh with `action_refresh_cache()`
4. **Ticket Update**: After successful assignment that adds a new owner

**Implementation Location:**
```python
# In RallyTUI app.py
async def _update_owner_cache(
    self, iteration: str, tickets: list[Ticket]
) -> None:
    """Update owner cache for an iteration.

    Args:
        iteration: Iteration name or FILTER_BACKLOG.
        tickets: Tickets loaded for this iteration.
    """
    if not self._cache_manager:
        return

    owners = await self._extract_owners_async(tickets)
    self._cache_manager.set_iteration_owners(iteration, owners)
    _log.debug(f"Cached {len(owners)} owners for {iteration}")
```

### 4.4 Rally API Integration

#### 4.4.1 Get Users Query

```python
# In AsyncRallyClient
async def get_users(
    self, display_names: list[str] | None = None
) -> list[Owner]:
    """Fetch Rally users by display names.

    Args:
        display_names: List of display names to query.

    Returns:
        List of Owner objects.
    """
    params = {
        "fetch": "ObjectID,DisplayName,UserName,EmailAddress",
        "pagesize": 200,
    }

    if display_names:
        # Build query: (DisplayName = "Name1") OR (DisplayName = "Name2")
        conditions = [f'(DisplayName = "{name}")' for name in display_names]
        if len(conditions) == 1:
            params["query"] = conditions[0]
        else:
            query = conditions[0]
            for cond in conditions[1:]:
                query = f"({query} OR {cond})"
            params["query"] = query

    response = await self._get("/user", params)
    results, _ = parse_query_result(response)

    return [self._to_owner(item) for item in results]

def _to_owner(self, item: dict) -> Owner:
    """Convert Rally API response to Owner model."""
    return Owner(
        object_id=str(item.get("ObjectID", "")),
        display_name=item.get("DisplayName", ""),
        user_name=item.get("UserName"),
    )
```

#### 4.4.2 Assign Owner Operation

```python
# In AsyncRallyClient
async def assign_owner(
    self, ticket: Ticket, owner: Owner
) -> Ticket | None:
    """Assign a ticket to a new owner.

    Args:
        ticket: Ticket to update.
        owner: Owner to assign.

    Returns:
        Updated Ticket or None on failure.
    """
    if not ticket.object_id:
        _log.warning(f"Cannot assign owner: no object_id for {ticket.formatted_id}")
        return None

    _log.info(f"Assigning {ticket.formatted_id} to {owner.display_name}")

    try:
        entity_type = get_entity_type_from_prefix(ticket.formatted_id)
        path = f"/{get_url_path(entity_type)}/{ticket.object_id}"

        response = await self._post(
            path,
            data={
                entity_type: {
                    "Owner": f"/user/{owner.object_id}"
                }
            },
        )
        results, _ = parse_query_result(response)

        if results:
            _log.info(f"Owner updated successfully for {ticket.formatted_id}")
            return Ticket(
                formatted_id=ticket.formatted_id,
                name=ticket.name,
                ticket_type=ticket.ticket_type,
                state=ticket.state,
                owner=owner.display_name,
                description=ticket.description,
                notes=ticket.notes,
                iteration=ticket.iteration,
                points=ticket.points,
                object_id=ticket.object_id,
                parent_id=ticket.parent_id,
            )
    except Exception as e:
        _log.error(f"Error assigning owner for {ticket.formatted_id}: {e}")

    return None
```

#### 4.4.3 Bulk Assign Owner Operation

```python
# In AsyncRallyClient
async def bulk_assign_owner(
    self, tickets: list[Ticket], owner: Owner
) -> BulkResult:
    """Assign owner to multiple tickets concurrently.

    Args:
        tickets: List of tickets to update.
        owner: Owner to assign to all tickets.

    Returns:
        BulkResult with success/failure counts.
    """
    _log.info(f"Bulk assigning {len(tickets)} tickets to {owner.display_name}")
    result = BulkResult()

    async def update_one(ticket: Ticket) -> Ticket | Exception:
        try:
            updated = await self.assign_owner(ticket, owner)
            return updated if updated else Exception("Update failed")
        except Exception as e:
            return e

    results = await asyncio.gather(*[update_one(t) for t in tickets])

    for i, res in enumerate(results):
        if isinstance(res, Ticket):
            result.success_count += 1
            result.updated_tickets.append(res)
        elif isinstance(res, Exception):
            result.failed_count += 1
            result.errors.append(f"{tickets[i].formatted_id}: {str(res)}")

    _log.info(
        f"Bulk assign complete: {result.success_count} success, "
        f"{result.failed_count} failed"
    )
    return result
```

---

## 5. UI/UX Design

### 5.1 Individual Assignment Flow

#### 5.1.1 Keybinding
- **Key**: `a` (assign)
- **Action ID**: `action.assign_owner`
- **Handler**: `assign_owner`
- **Context**: Available when ticket list is focused and a ticket is selected

#### 5.1.2 Owner Selection Screen

**New Screen: `OwnerSelectionScreen`**

Location: `src/rally_tui/screens/owner_screen.py`

**Visual Design:**
```
╔═══════════════════════════════════════════╗
║ Assign Owner - US1234                    ║
╠═══════════════════════════════════════════╣
║                                           ║
║  Select an owner for this ticket:        ║
║                                           ║
║  ┌─────────────────────────────────────┐ ║
║  │ > Alice Johnson                     │ ║
║  │   Bob Smith                         │ ║
║  │   Carol Davis                       │ ║
║  │   David Wilson                      │ ║
║  │   Emma Martinez                     │ ║
║  │                                     │ ║
║  │ [Custom Owner...]                   │ ║
║  └─────────────────────────────────────┘ ║
║                                           ║
║  j/k: Navigate  Enter: Select  ESC: Cancel║
╚═══════════════════════════════════════════╝
```

**Features:**
- List of cached owners for the current iteration
- Scrollable list with vim navigation (j/k)
- "Custom Owner..." option at bottom (opens text input)
- Shows ticket ID in title for context
- Cancel with Escape key

**Custom Owner Input:**
If user selects "Custom Owner...", show text input modal:
```
╔═══════════════════════════════════════════╗
║ Enter Owner Name                          ║
╠═══════════════════════════════════════════╣
║                                           ║
║  Display Name: [____________________]     ║
║                                           ║
║  Press Enter to confirm, ESC to cancel    ║
╚═══════════════════════════════════════════╝
```

User enters owner display name, system queries Rally API for matching User object.

#### 5.1.3 Success/Failure Notifications

**Success:**
```
✓ Ticket US1234 assigned to Alice Johnson
```

**Failure:**
```
✗ Failed to assign US1234: Owner not found in Rally
```

### 5.2 Bulk Assignment Flow

#### 5.2.1 Bulk Menu Entry

Update `BulkActionsScreen` to include assignment option:

```python
class BulkAction(Enum):
    """Available bulk actions for selected tickets."""

    SET_PARENT = "parent"
    SET_STATE = "state"
    SET_ITERATION = "iteration"
    SET_POINTS = "points"
    SET_OWNER = "owner"      # NEW
    YANK = "yank"
```

**Updated Menu:**
```
╔═══════════════════════════════════════════╗
║ Bulk Actions - 5 tickets selected        ║
╠═══════════════════════════════════════════╣
║                                           ║
║  Select an action to perform on 5 tickets:║
║                                           ║
║  [ 1. Set Parent         ]                ║
║  [ 2. Set State          ]                ║
║  [ 3. Set Iteration      ]                ║
║  [ 4. Set Points         ]                ║
║  [ 5. Assign Owner       ]  ← NEW         ║
║  [ 6. Yank (Copy URLs)   ]                ║
║                                           ║
║  Press 1-6 or click, ESC to cancel        ║
╚═══════════════════════════════════════════╝
```

#### 5.2.2 Owner Selection

Same `OwnerSelectionScreen` as individual assignment, but title shows:
```
Assign Owner - 5 tickets selected
```

#### 5.2.3 Bulk Operation Results

**Success Modal:**
```
╔═══════════════════════════════════════════╗
║ Bulk Assignment Complete                  ║
╠═══════════════════════════════════════════╣
║                                           ║
║  Assigned 5 tickets to Alice Johnson      ║
║                                           ║
║  ✓ Success: 5                             ║
║  ✗ Failed:  0                             ║
║                                           ║
║  Press any key to continue                ║
╚═══════════════════════════════════════════╝
```

**Partial Failure Modal:**
```
╔═══════════════════════════════════════════╗
║ Bulk Assignment Complete                  ║
╠═══════════════════════════════════════════╣
║                                           ║
║  Assigned tickets to Alice Johnson        ║
║                                           ║
║  ✓ Success: 4                             ║
║  ✗ Failed:  1                             ║
║                                           ║
║  Errors:                                  ║
║  • US1234: No object_id                   ║
║                                           ║
║  Press any key to continue                ║
╚═══════════════════════════════════════════╝
```

### 5.3 Edge Cases

#### 5.3.1 No Owners in Cache

If iteration has no cached owners (empty sprint), show:
```
╔═══════════════════════════════════════════╗
║ Assign Owner - US1234                    ║
╠═══════════════════════════════════════════╣
║                                           ║
║  No owners found in current iteration.    ║
║                                           ║
║  ┌─────────────────────────────────────┐ ║
║  │ [Custom Owner...]                   │ ║
║  └─────────────────────────────────────┘ ║
║                                           ║
║  Enter: Custom  ESC: Cancel               ║
╚═══════════════════════════════════════════╝
```

#### 5.3.2 Custom Owner Not Found

If user enters a name that doesn't match any Rally user:
```
✗ Owner "John Doe" not found in Rally. Please check the name and try again.
```

Return to owner selection screen.

#### 5.3.3 Backlog View

In backlog view (no iteration filter), owner cache includes all owners from loaded backlog tickets.

---

## 6. Implementation Phases

### Phase 1: Data Models and Protocol
**Estimated Effort:** 2-3 hours

**Tasks:**
- [ ] Create `Owner` dataclass in `src/rally_tui/models/owner.py`
- [ ] Update `src/rally_tui/models/__init__.py` to export `Owner`
- [ ] Add `get_users()` method to `RallyClientProtocol`
- [ ] Add `assign_owner()` method to `RallyClientProtocol`
- [ ] Add `bulk_assign_owner()` method to `RallyClientProtocol`
- [ ] Add protocol methods to type stubs for IDE support

**Acceptance Criteria:**
- [ ] `Owner` model has all required fields
- [ ] `Owner` implements `__hash__` and `__eq__` for set operations
- [ ] Protocol methods have complete type hints and docstrings
- [ ] No import errors or type checking failures

### Phase 2: Rally API Implementation
**Estimated Effort:** 4-5 hours

**Tasks:**
- [ ] Implement `get_users()` in `AsyncRallyClient`
- [ ] Implement `_to_owner()` helper method
- [ ] Implement `assign_owner()` in `AsyncRallyClient`
- [ ] Implement `bulk_assign_owner()` in `AsyncRallyClient`
- [ ] Implement `get_users()` in `RallyClient` (sync version)
- [ ] Implement `assign_owner()` in `RallyClient` (sync version)
- [ ] Implement `bulk_assign_owner()` in `RallyClient` (sync version)
- [ ] Add mock implementations in `MockRallyClient` for testing
- [ ] Write unit tests for Rally API methods

**Acceptance Criteria:**
- [ ] `get_users()` correctly queries Rally /user endpoint
- [ ] `get_users()` handles display name filtering
- [ ] `assign_owner()` updates ticket owner in Rally
- [ ] `bulk_assign_owner()` processes tickets concurrently
- [ ] Error handling works for all API failures
- [ ] Mock client provides realistic test data
- [ ] All tests pass

### Phase 3: Owner Cache Implementation
**Estimated Effort:** 3-4 hours

**Tasks:**
- [ ] Add owner cache storage to `CacheManager`
- [ ] Implement `get_iteration_owners()` method
- [ ] Implement `set_iteration_owners()` method
- [ ] Implement `clear_iteration_owners()` method
- [ ] Create `extract_owners_from_tickets()` utility function
- [ ] Add `_update_owner_cache()` to `RallyTUI` app
- [ ] Hook owner cache update into `_load_initial_tickets_async()`
- [ ] Hook owner cache update into `action_iteration_filter()`
- [ ] Hook owner cache update into `action_refresh_cache()`
- [ ] Write unit tests for cache operations

**Acceptance Criteria:**
- [ ] Owner cache stores unique owners per iteration
- [ ] Cache updates automatically on iteration change
- [ ] Cache clears on manual refresh
- [ ] Cache handles FILTER_BACKLOG correctly
- [ ] No duplicate owners in cache (set uniqueness works)
- [ ] All tests pass

### Phase 4: Owner Selection Screen
**Estimated Effort:** 4-5 hours

**Tasks:**
- [ ] Create `OwnerSelectionScreen` in `src/rally_tui/screens/owner_screen.py`
- [ ] Implement owner list rendering from cache
- [ ] Add vim-style navigation (j/k)
- [ ] Add "Custom Owner..." option at bottom
- [ ] Create custom owner input modal
- [ ] Implement owner search via Rally API for custom names
- [ ] Add escape key to cancel
- [ ] Add enter key to select
- [ ] Update `src/rally_tui/screens/__init__.py` to export screen
- [ ] Write widget tests for owner selection

**Acceptance Criteria:**
- [ ] Screen displays cached owners for current iteration
- [ ] Navigation works with j/k keys
- [ ] Custom owner input allows text entry
- [ ] Custom owner search queries Rally API
- [ ] Selection returns chosen `Owner` object
- [ ] Cancel returns `None`
- [ ] Screen handles empty owner list gracefully
- [ ] All tests pass

### Phase 5: Individual Assignment Integration
**Estimated Effort:** 3-4 hours

**Tasks:**
- [ ] Add `action.assign_owner` to keybinding registry
- [ ] Add default keybinding 'a' for assign in VIM_KEYBINDINGS
- [ ] Add emacs keybinding for assign in EMACS_KEYBINDINGS
- [ ] Implement `action_assign_owner()` in `RallyTUI` app
- [ ] Call `push_screen(OwnerSelectionScreen(...))`
- [ ] Handle owner selection callback
- [ ] Call `assign_owner()` on client
- [ ] Update ticket in list view
- [ ] Show success/failure notification
- [ ] Update owner cache if new owner added
- [ ] Write integration tests

**Acceptance Criteria:**
- [ ] 'a' key opens owner selection screen on focused ticket
- [ ] Selecting owner updates ticket successfully
- [ ] Ticket list refreshes with new owner
- [ ] Notification shows success message
- [ ] Failed assignments show error notification
- [ ] Integration tests pass

### Phase 6: Bulk Assignment Integration
**Estimated Effort:** 3-4 hours

**Tasks:**
- [ ] Add `SET_OWNER` to `BulkAction` enum
- [ ] Update `BulkActionsScreen` UI to show "5. Assign Owner"
- [ ] Update button press handler to support assignment action
- [ ] Implement `_handle_bulk_assign_owner()` in `RallyTUI` app
- [ ] Push `OwnerSelectionScreen` with bulk context
- [ ] Call `bulk_assign_owner()` on client
- [ ] Show bulk result modal with success/failure counts
- [ ] Update ticket list with modified tickets
- [ ] Clear selection after bulk operation
- [ ] Write integration tests

**Acceptance Criteria:**
- [ ] Bulk menu shows "Assign Owner" option
- [ ] Selecting option opens owner selection
- [ ] Bulk operation updates all selected tickets
- [ ] Result modal shows accurate counts
- [ ] Failed tickets display error messages
- [ ] Selection clears after operation
- [ ] Integration tests pass

### Phase 7: Testing and Documentation
**Estimated Effort:** 2-3 hours

**Tasks:**
- [ ] Write end-to-end tests for individual assignment
- [ ] Write end-to-end tests for bulk assignment
- [ ] Write edge case tests (no owners, custom owner not found)
- [ ] Update user documentation with assignment instructions
- [ ] Update CHANGELOG.md with new feature
- [ ] Update README.md screenshots if needed
- [ ] Test with real Rally instance
- [ ] Performance test with large ticket lists

**Acceptance Criteria:**
- [ ] All tests pass (unit, integration, e2e)
- [ ] Test coverage > 80% for new code
- [ ] Documentation is clear and complete
- [ ] Feature works in production-like environment
- [ ] No performance regression on ticket list rendering

---

## 7. Testing Requirements

### 7.1 Unit Tests

**Rally API Tests:**
- Test `get_users()` with no filter
- Test `get_users()` with display name filter
- Test `assign_owner()` success case
- Test `assign_owner()` failure cases (no object_id, API error)
- Test `bulk_assign_owner()` all success
- Test `bulk_assign_owner()` partial failure
- Test `bulk_assign_owner()` all failure

**Cache Tests:**
- Test owner cache storage per iteration
- Test owner cache retrieval
- Test owner cache clearing
- Test owner extraction from tickets
- Test duplicate owner filtering (set uniqueness)

**Screen Tests:**
- Test owner list rendering
- Test navigation with j/k keys
- Test owner selection
- Test cancel operation
- Test custom owner input
- Test empty owner list display

### 7.2 Integration Tests

**Individual Assignment:**
- Test full flow: keybinding → screen → selection → API → update
- Test cancel flow
- Test error handling (API failure)
- Test custom owner flow

**Bulk Assignment:**
- Test full flow: bulk menu → owner screen → bulk API → results
- Test partial success scenario
- Test all failure scenario
- Test result modal display

**Cache Integration:**
- Test cache update on ticket load
- Test cache update on iteration change
- Test cache update on manual refresh

### 7.3 End-to-End Tests

**Scenarios:**
1. **Happy Path Individual:** Select ticket, assign owner, verify update
2. **Happy Path Bulk:** Select 5 tickets, assign owner, verify all updated
3. **Custom Owner:** Use custom owner input, verify API query and assignment
4. **No Cache:** Empty iteration, use custom owner, verify assignment
5. **Partial Failure:** Bulk assign with some tickets missing object_id
6. **Cancel Operations:** Cancel individual and bulk assignments
7. **Iteration Switch:** Load sprint 1, assign ticket, switch to sprint 2, verify owner cache differs

### 7.4 Performance Tests

**Criteria:**
- Owner cache extraction < 100ms for 200 tickets
- Individual assignment < 2s including API call
- Bulk assignment of 50 tickets < 10s
- Owner list rendering < 50ms for 50 owners

---

## 8. Acceptance Criteria

### 8.1 Functional Requirements

**Individual Assignment:**
- [ ] User can assign a ticket to an owner from cached list
- [ ] User can assign a ticket to a custom owner (text input)
- [ ] Assignment updates Rally and refreshes local view
- [ ] Success and failure notifications are clear

**Bulk Assignment:**
- [ ] User can bulk assign multiple tickets to one owner
- [ ] Bulk operation shows progress indication
- [ ] Bulk result displays success/failure counts
- [ ] Failed tickets show specific error messages

**Owner Cache:**
- [ ] Owner cache populates on ticket load
- [ ] Owner cache updates on iteration change
- [ ] Owner cache provides relevant owner suggestions
- [ ] Owner cache handles edge cases (no owners, backlog)

### 8.2 Non-Functional Requirements

**Performance:**
- [ ] Owner cache extraction completes in < 100ms
- [ ] Individual assignment completes in < 2s
- [ ] Bulk assignment (50 tickets) completes in < 10s
- [ ] No lag in UI when opening owner selection

**Reliability:**
- [ ] API errors are caught and reported clearly
- [ ] Partial bulk failures don't block successful updates
- [ ] Cache corruption doesn't crash application
- [ ] Edge cases (no owners) handled gracefully

**Usability:**
- [ ] Keyboard navigation works smoothly (j/k)
- [ ] Owner list is readable and well-formatted
- [ ] Result messages are clear and actionable
- [ ] UI follows existing rally-tui conventions

**Maintainability:**
- [ ] Code follows existing project patterns
- [ ] New code has > 80% test coverage
- [ ] Documentation is complete and accurate
- [ ] No code duplication with existing features

### 8.3 Compatibility Requirements

**Client Compatibility:**
- [ ] Works with `AsyncRallyClient`
- [ ] Works with `RallyClient` (sync fallback)
- [ ] Works with `MockRallyClient` (testing)
- [ ] Works with caching layer enabled/disabled

**Platform Compatibility:**
- [ ] Works on macOS
- [ ] Works on Linux
- [ ] Works on Windows (if applicable)

**Rally API Compatibility:**
- [ ] Compatible with Rally WSAPI v2.0
- [ ] Handles Rally API rate limits gracefully
- [ ] Works with different Rally permission levels

---

## 9. Risk Analysis

### 9.1 Technical Risks

**Risk:** Owner cache may become stale if tickets are assigned outside rally-tui
**Mitigation:** Include cache refresh keybinding, document auto-refresh behavior

**Risk:** Rally API may return duplicate User objects for the same person
**Mitigation:** Use `set[Owner]` with proper `__hash__` and `__eq__` implementation

**Risk:** Custom owner input may match multiple Rally users
**Mitigation:** If multiple matches, show disambiguation list

**Risk:** Bulk operations may timeout on large ticket counts
**Mitigation:** Implement reasonable concurrency limits (existing MAX_CONCURRENT_REQUESTS)

### 9.2 UX Risks

**Risk:** Users may expect autocomplete in custom owner input
**Mitigation:** Document that full display name is required, consider future autocomplete

**Risk:** Owner list may be very long for large teams
**Mitigation:** Implement scrolling, consider search/filter in future

**Risk:** No visual indication of current ticket owner in selection screen
**Mitigation:** Highlight current owner in list with "• " marker

### 9.3 Security Risks

**Risk:** User permissions may not allow assigning to certain owners
**Mitigation:** Rely on Rally API permission checks, display clear error on permission denied

**Risk:** Malicious input in custom owner field
**Mitigation:** Rally API handles validation, no SQL injection risk (REST API)

---

## 10. Future Enhancements

**Out of scope for this SRD, but potential future additions:**

1. **Owner Autocomplete**: Real-time search-as-you-type in custom owner input
2. **Owner Favorites**: Pin frequently used owners to top of list
3. **Team Filtering**: Filter owner list by team/department
4. **Owner History**: Show recently used owners across all iterations
5. **Batch Custom Assignment**: Assign different owners to different tickets in bulk
6. **Owner Workload Display**: Show current ticket count per owner in selection list
7. **Owner Availability**: Integrate with PTO/vacation calendar to show availability

---

## 11. Open Questions

**Q1:** Should we pre-load all project users on app startup for faster custom owner lookup?
**A1:** No. Lazy load on demand to minimize startup time. Cache can grow organically.

**Q2:** What happens if a ticket already has the selected owner?
**A2:** Treat as success (idempotent operation), skip API call, show success message.

**Q3:** Should bulk assignment skip tickets that already have the target owner?
**A3:** Yes. Count as success but skip API call for efficiency.

**Q4:** How to handle iteration-less tickets (backlog)?
**A4:** Use `FILTER_BACKLOG` constant as cache key, include all backlog ticket owners.

**Q5:** Should we support unassigning (setting owner to None)?
**A5:** Not in initial implementation. Future enhancement if needed.

---

## 12. References

### Existing Rally-TUI Patterns
- **Set State**: `src/rally_tui/screens/state_screen.py` - Selection screen pattern
- **Set Parent**: `src/rally_tui/screens/parent_screen.py` - Text input with validation
- **Bulk Operations**: `src/rally_tui/screens/bulk_actions_screen.py` - Menu pattern
- **Keybindings**: `src/rally_tui/utils/keybindings.py` - Action registry

### Rally API Documentation
- **User Object**: https://rally1.rallydev.com/slm/doc/webservice/user.jsp
- **WSAPI Query**: https://rally1.rallydev.com/slm/doc/webservice/querying.jsp
- **Reference Types**: https://rally1.rallydev.com/slm/doc/webservice/references.jsp

### Related Issues
- None (new feature)

---

## 13. Revision History

| Version | Date       | Author | Changes |
|---------|------------|--------|---------|
| 1.0     | 2026-02-05 | Atlas  | Initial SRD creation |

---

**Document Status:** Ready for Review
**Next Steps:** Review with development team, approve technical approach, begin Phase 1 implementation
