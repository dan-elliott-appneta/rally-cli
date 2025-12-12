# Iteration 14: Local Caching & Offline Mode

## Goal

Dramatically improve startup performance and enable offline ticket viewing through intelligent local caching with a **stale-while-revalidate** strategy.

**Key Constraint**: Offline mode is **read-only** - users cannot create, edit, or update tickets when offline.

## Problem Statement

Current limitations without caching:

| Issue | Impact |
|-------|--------|
| **Slow startup** | 2-5 seconds waiting for Rally API on every launch |
| **No offline access** | Cannot view tickets without network connectivity |
| **Redundant fetches** | Same data fetched repeatedly across sessions |
| **Rate limit risk** | Heavy usage can trigger Rally API limits |
| **Filter latency** | Changing iteration filter requires server round-trip |

## Solution: Stale-While-Revalidate Caching

```
┌─────────────────────────────────────────────────────────────────┐
│                         RallyTUI App                            │
├─────────────────────────────────────────────────────────────────┤
│                      CachingRallyClient                         │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │   CacheManager      │    │      RallyClient (API)          │ │
│  │  ┌───────────────┐  │    │                                 │ │
│  │  │ tickets.json  │  │ ◄──┼── Background refresh            │ │
│  │  │ meta.json     │  │    │                                 │ │
│  │  │ iterations/   │  │    │                                 │ │
│  │  └───────────────┘  │    └─────────────────────────────────┘ │
│  │  ~/.cache/rally-tui │                                        │
│  └─────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
```

### How It Works

1. **On startup**: Load tickets from cache immediately (instant UI)
2. **Background refresh**: Fetch fresh data from Rally in background thread
3. **Update UI**: When fresh data arrives, update ticket list seamlessly
4. **Status indicator**: StatusBar shows cache status (Live/Cached/Refreshing/Offline)
5. **Manual refresh**: `r` key forces immediate fresh fetch

### Offline Mode Behavior

When offline (no network or Rally unavailable):
- Show cached tickets (read-only)
- Disable write operations (state change, points, comments, etc.)
- Show "Offline" indicator in StatusBar
- Notify user when they attempt a write operation

## Implementation Plan

### Phase 1: Cache Infrastructure

**File: `src/rally_tui/services/cache_manager.py`**

Create `CacheManager` class with:
- Cache directory setup (`~/.cache/rally-tui/`)
- Atomic file writes (write to temp, then rename)
- TTL-based cache validity checking
- JSON serialization for Ticket objects
- Cache metadata tracking (workspace, project, timestamps)

```python
@dataclass
class CacheMetadata:
    version: int = 1
    workspace: str = ""
    project: str = ""
    tickets_updated: datetime | None = None

class CacheManager:
    def __init__(self, cache_dir: Path | None = None):
        self._cache_dir = cache_dir or Path.home() / ".cache" / "rally-tui"

    def get_cached_tickets(self) -> tuple[list[Ticket], CacheMetadata | None]
    def save_tickets(self, tickets: list[Ticket], workspace: str, project: str) -> None
    def is_cache_valid(self, ttl_minutes: int) -> bool
    def get_cache_age_minutes(self) -> int | None
    def clear_cache(self) -> None
```

### Phase 2: Cache Configuration

**File: `src/rally_tui/user_settings.py`**

Add cache settings:

```python
# In UserSettings class
@property
def cache_enabled(self) -> bool:
    return self._data.get("cache_enabled", True)

@property
def cache_ttl_minutes(self) -> int:
    return self._data.get("cache_ttl_minutes", 15)

@property
def cache_auto_refresh(self) -> bool:
    return self._data.get("cache_auto_refresh", True)
```

**Configuration options in `~/.config/rally-tui/config.json`:**

```json
{
  "cache_enabled": true,
  "cache_ttl_minutes": 15,
  "cache_auto_refresh": true
}
```

### Phase 3: CachingRallyClient Wrapper

**File: `src/rally_tui/services/caching_client.py`**

Create wrapper that implements `RallyClientProtocol`:

```python
class CachingRallyClient:
    """Wraps RallyClient with caching layer."""

    def __init__(
        self,
        client: RallyClient,
        cache_manager: CacheManager,
        cache_enabled: bool = True,
        ttl_minutes: int = 15,
    ):
        self._client = client
        self._cache = cache_manager
        self._enabled = cache_enabled
        self._ttl = ttl_minutes
        self._is_offline = False

    def get_tickets(self, query: str = "") -> list[Ticket]:
        """Return cached tickets, trigger background refresh if stale."""
        # 1. Try to return cached tickets first
        # 2. Check if cache is stale
        # 3. If stale and online, return cached + trigger refresh
        # 4. If no cache, fetch from API

    def refresh_cache(self) -> list[Ticket]:
        """Force refresh from API and update cache."""

    @property
    def is_offline(self) -> bool:
        return self._is_offline

    @property
    def cache_age_minutes(self) -> int | None:
        return self._cache.get_cache_age_minutes()
```

### Phase 4: StatusBar Cache Status

**File: `src/rally_tui/widgets/status_bar.py`**

Add cache status display:

```
┌─────────────────────────────────────────────────────────────────┐
│ rally-tui │ MyProject │ ● Live                 │ Connected     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ rally-tui │ MyProject │ ○ Cached (5m)          │ Connected     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ rally-tui │ MyProject │ ◌ Refreshing...        │ Connected     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ rally-tui │ MyProject │ ⚠ Offline              │ Disconnected  │
└─────────────────────────────────────────────────────────────────┘
```

```python
class CacheStatus(Enum):
    LIVE = "live"           # Fresh data from API
    CACHED = "cached"       # Showing cached data
    REFRESHING = "refresh"  # Background refresh in progress
    OFFLINE = "offline"     # No network, using cache

# Add to StatusBar
def set_cache_status(self, status: CacheStatus, age_minutes: int | None = None) -> None
```

### Phase 5: App Integration

**File: `src/rally_tui/app.py`**

1. Create `CachingRallyClient` wrapper around `RallyClient`
2. Load from cache on startup (instant)
3. Trigger background refresh
4. Add `r` keybinding for manual refresh
5. Handle `CacheUpdated` message to refresh UI
6. Disable write operations when offline

```python
# New keybindings
"action.refresh": ("refresh_cache", "Refresh", True),

# New action
def action_refresh_cache(self) -> None:
    """Force refresh tickets from Rally API."""
    if self._caching_client:
        self._caching_client.refresh_cache()
        self.notify("Refreshing...", timeout=1)
```

### Phase 6: Offline Write Protection

When offline, disable these operations with user notification:
- `action_set_state()` - "Cannot change state while offline"
- `action_set_points()` - "Cannot set points while offline"
- `action_open_discussions()` - Allow viewing, disable posting
- `action_quick_ticket()` - "Cannot create tickets while offline"
- All bulk operations

## Data Model

### Cache Directory Structure

```
~/.cache/rally-tui/
├── meta.json           # Cache metadata
└── tickets.json        # Cached tickets
```

### meta.json Schema

```json
{
  "version": 1,
  "workspace": "MyWorkspace",
  "project": "MyProject",
  "tickets_updated": "2024-01-15T10:35:00Z"
}
```

### tickets.json Schema

```json
{
  "tickets": [
    {
      "formatted_id": "US1234",
      "name": "User login feature",
      "ticket_type": "UserStory",
      "state": "In-Progress",
      "owner": "John Smith",
      "iteration": "Sprint 5",
      "points": 3.0,
      "description": "...",
      "notes": "...",
      "parent_id": "F12345",
      "object_id": "123456789"
    }
  ]
}
```

## Key Bindings

| Key | Action |
|-----|--------|
| `r` | Force refresh from Rally API |

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `cache_enabled` | bool | `true` | Enable/disable local caching |
| `cache_ttl_minutes` | int | `15` | Time before cache is considered stale |
| `cache_auto_refresh` | bool | `true` | Auto-refresh when cache is stale |

## Performance Targets

| Metric | Before | After |
|--------|--------|-------|
| Cold startup (no cache) | 3-5s | 3-5s |
| Warm startup (with cache) | 3-5s | **<0.5s** |
| Iteration filter change | 1-2s | **<0.1s** (from cache) |
| Offline access | ❌ | ✅ (read-only) |

## Key Files

```
src/rally_tui/
├── services/
│   ├── cache_manager.py      # NEW: CacheManager class
│   ├── caching_client.py     # NEW: CachingRallyClient wrapper
│   └── __init__.py           # Export new classes
├── user_settings.py          # Add cache configuration
├── utils/
│   └── keybindings.py        # Add action.refresh
├── widgets/
│   └── status_bar.py         # Add cache status display
└── app.py                    # Integrate caching

tests/
├── test_cache_manager.py     # NEW: CacheManager tests
├── test_caching_client.py    # NEW: CachingRallyClient tests
└── test_offline_mode.py      # NEW: Offline mode tests
```

## Test Coverage

### CacheManager Tests
- `test_cache_directory_creation` - Creates ~/.cache/rally-tui/ if missing
- `test_save_and_load_tickets` - Round-trip serialization
- `test_cache_metadata` - Workspace/project/timestamp tracking
- `test_cache_validity_fresh` - TTL not expired
- `test_cache_validity_stale` - TTL expired
- `test_cache_age_calculation` - Minutes since last update
- `test_clear_cache` - Removes all cached files
- `test_empty_cache_returns_empty_list` - No crash on missing cache
- `test_corrupt_cache_handled` - Graceful handling of invalid JSON
- `test_atomic_write` - File not corrupted on crash

### CachingRallyClient Tests
- `test_returns_cached_tickets_when_available` - Cache-first behavior
- `test_fetches_from_api_when_cache_empty` - Fallback to API
- `test_refresh_updates_cache` - Manual refresh
- `test_stale_cache_triggers_refresh` - Auto-refresh when stale
- `test_offline_mode_uses_cache` - Network failure handling
- `test_offline_flag_set_on_error` - is_offline property
- `test_cache_disabled_always_fetches` - Bypass cache when disabled

### StatusBar Tests
- `test_cache_status_live` - "● Live" display
- `test_cache_status_cached` - "○ Cached (Xm)" display
- `test_cache_status_refreshing` - "◌ Refreshing..." display
- `test_cache_status_offline` - "⚠ Offline" display

### Integration Tests
- `test_warm_startup_from_cache` - Fast startup with cache
- `test_background_refresh` - UI updates after refresh
- `test_offline_blocks_writes` - Write operations disabled
- `test_r_key_triggers_refresh` - Manual refresh keybinding

## Implementation Notes

1. **Atomic Writes**: Write to temp file then rename to prevent corruption
2. **Graceful Degradation**: If cache is corrupt, delete and continue without cache
3. **No Write-Through**: Cache is read-only; writes go directly to API
4. **Background Refresh**: Use Textual workers for non-blocking refresh
5. **Cache Invalidation**: Clear cache when workspace/project changes
6. **Error Handling**: Network errors set offline mode, don't crash

## Commit Plan

1. `docs: add ITERATION_14.md - Local Caching plan`
2. `feat: add CacheManager with file I/O and TTL`
3. `feat: add cache configuration to UserSettings`
4. `feat: create CachingRallyClient wrapper`
5. `feat: add cache status to StatusBar`
6. `feat: add 'r' keybinding for manual refresh`
7. `feat: integrate caching into app startup`
8. `feat: add offline mode write protection`
9. `test: add comprehensive cache tests`
10. `docs: update README and PLAN.md`

## UI Mockup

### Normal Operation (cached, connected)
```
┌─────────────────────────────────────────────────────────────────┐
│ rally-tui │ MyProject       │ ○ Cached (3m)     │ Connected    │
├─────────────────────────────────────────────────────────────────┤
│  TICKETS                │  DETAILS                              │
│  ...                    │  ...                                  │
├─────────────────────────────────────────────────────────────────┤
│ j Down  k Up  a Attach  d Discuss  r Refresh  s State  q Quit  │
└─────────────────────────────────────────────────────────────────┘
```

### Offline Mode
```
┌─────────────────────────────────────────────────────────────────┐
│ rally-tui │ MyProject       │ ⚠ Offline         │ Disconnected │
├─────────────────────────────────────────────────────────────────┤
│  TICKETS                │  DETAILS                              │
│  ...                    │  ... (read-only)                      │
├─────────────────────────────────────────────────────────────────┤
│ j Down  k Up  a Attach  d Discuss  r Refresh           q Quit  │
└─────────────────────────────────────────────────────────────────┘

[Notification: "Offline mode - viewing cached data (read-only)"]
```
