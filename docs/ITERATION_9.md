# Iteration 9: Configurable Keybindings

## Goal

Allow users to customize keyboard shortcuts via configuration file and UI, with support for preset profiles (Vim, Emacs).

## Overview

Currently, all keybindings are hardcoded in `app.py` and `ticket_list.py` using Textual's `BINDINGS` class variable. This iteration adds:

1. **Keybindings schema** in UserSettings for persistent storage
2. **KeybindingsScreen** modal for viewing/editing bindings
3. **Dynamic binding loading** at app startup
4. **Preset profiles** (Vim default, Emacs alternative)
5. **Reset to defaults** capability

## Architecture

### Keybinding Storage

Keybindings stored in `~/.config/rally-tui/config.json`:

```json
{
  "keybinding_profile": "vim",
  "keybindings": {
    "navigation.down": "j",
    "navigation.up": "k",
    "navigation.top": "g",
    "navigation.bottom": "G",
    "action.quit": "q",
    "action.search": "/",
    "action.state": "s",
    "action.points": "p",
    "action.workitem": "w",
    "action.notes": "n",
    "action.discuss": "d",
    "action.sprint": "i",
    "action.my_items": "u",
    "action.bulk": "m",
    "action.sort": "o",
    "action.settings": "f2",
    "action.copy_url": "y",
    "action.theme": "t",
    "panel.switch": "tab"
  }
}
```

### Action Registry

Map action names to handler methods:

| Action ID | Default (Vim) | Emacs | Handler Method |
|-----------|---------------|-------|----------------|
| `navigation.down` | `j` | `ctrl+n` | `action_cursor_down` |
| `navigation.up` | `k` | `ctrl+p` | `action_cursor_up` |
| `navigation.top` | `g` | `meta+<` | `action_scroll_home` |
| `navigation.bottom` | `G` | `meta+>` | `action_scroll_end` |
| `action.quit` | `q` | `ctrl+q` | `action_quit` |
| `action.search` | `/` | `ctrl+s` | `action_start_search` |
| `action.state` | `s` | `ctrl+shift+s` | `action_set_state` |
| `action.points` | `p` | `ctrl+shift+p` | `action_set_points` |
| `action.workitem` | `w` | `ctrl+shift+n` | `action_quick_ticket` |
| `action.notes` | `n` | `ctrl+shift+o` | `action_toggle_notes` |
| `action.discuss` | `d` | `ctrl+d` | `action_open_discussions` |
| `action.sprint` | `i` | `ctrl+i` | `action_iteration_filter` |
| `action.my_items` | `u` | `ctrl+u` | `action_toggle_user_filter` |
| `action.bulk` | `m` | `ctrl+m` | `action_bulk_actions` |
| `action.sort` | `o` | `ctrl+o` | `action_cycle_sort` |
| `action.settings` | `f2` | `f2` | `action_open_settings` |
| `action.copy_url` | `y` | `meta+w` | `action_copy_ticket_url` |
| `action.theme` | `t` | `ctrl+t` | `action_toggle_theme` |
| `panel.switch` | `tab` | `tab` | `action_switch_panel` |
| `selection.toggle` | `space` | `space` | `action_toggle_select` |
| `selection.all` | `ctrl+a` | `ctrl+a` | `action_select_all` |

### Preset Profiles

```python
VIM_PROFILE = {
    "navigation.down": "j",
    "navigation.up": "k",
    "navigation.top": "g",
    "navigation.bottom": "G",
    "action.quit": "q",
    "action.search": "/",
    ...
}

EMACS_PROFILE = {
    "navigation.down": "ctrl+n",
    "navigation.up": "ctrl+p",
    "navigation.top": "meta+<",
    "navigation.bottom": "meta+>",
    "action.quit": "ctrl+q",
    "action.search": "ctrl+s",
    ...
}
```

## Implementation Plan

### 1. Add Keybindings Schema to UserSettings

**File**: `src/rally_tui/user_settings.py`

Add:
- `DEFAULT_VIM_KEYBINDINGS` constant with all vim defaults
- `DEFAULT_EMACS_KEYBINDINGS` constant with emacs alternatives
- `VALID_PROFILES = ("vim", "emacs", "custom")`
- `keybinding_profile` property (getter/setter)
- `keybindings` property (getter/setter)
- `get_keybinding(action_id: str) -> str` method
- `set_keybinding(action_id: str, key: str) -> None` method
- `reset_keybindings(profile: str = "vim") -> None` method
- `validate_keybinding(key: str) -> bool` helper

### 2. Create Keybinding Utilities Module

**File**: `src/rally_tui/utils/keybindings.py`

- `KeyAction` dataclass with id, description, default_key, handler
- `ACTION_REGISTRY: dict[str, KeyAction]` - all actions with metadata
- `parse_key(key_str: str) -> tuple[str, set[str]]` - parse "ctrl+s" to ("s", {"ctrl"})
- `format_key(key: str, modifiers: set[str]) -> str` - format for display
- `key_conflicts(bindings: dict) -> list[tuple[str, str, str]]` - detect duplicates

### 3. Create KeybindingsScreen Modal

**File**: `src/rally_tui/screens/keybindings_screen.py`

UI Layout:
```
┌────────────────────────────────────────────────────────────┐
│ Keyboard Shortcuts                                          │
├────────────────────────────────────────────────────────────┤
│ Profile: [Vim ▼]                                            │
│                                                             │
│ Navigation                                                  │
│ ─────────────────────────────────────────────────────────   │
│  Move Down          [j     ]  ← currently editing           │
│  Move Up            [k     ]                                │
│  Jump to Top        [g     ]                                │
│  Jump to Bottom     [G     ]                                │
│                                                             │
│ Actions                                                     │
│ ─────────────────────────────────────────────────────────   │
│  Set State          [s     ]                                │
│  Set Points         [p     ]                                │
│  Create Ticket      [w     ]                                │
│  ...                                                        │
│                                                             │
├────────────────────────────────────────────────────────────┤
│ [Save] [Reset to Default] [Cancel]                          │
│ Press key to change, Esc to cancel                          │
└────────────────────────────────────────────────────────────┘
```

Features:
- Display all configurable bindings grouped by category
- Select a binding to edit (highlight row)
- Press any key to set new binding
- Detect and warn about conflicts
- Profile dropdown (Vim/Emacs/Custom)
- Reset to defaults button
- Save/Cancel buttons

### 4. Implement Dynamic Keybinding Loading in App

**File**: `src/rally_tui/app.py`

Changes:
- Remove hardcoded `BINDINGS` list
- Add `_build_bindings(settings: UserSettings) -> list[Binding]` class method
- Call `_build_bindings()` in `__init__` before `super().__init__()`
- Override `BINDINGS` dynamically using the built list
- Add `k` keybinding to open KeybindingsScreen (or use F3)
- Add `action_open_keybindings()` method

**File**: `src/rally_tui/widgets/ticket_list.py`

Changes:
- Accept `keybindings` parameter in `__init__`
- Build BINDINGS dynamically for navigation keys

### 5. Add Keybindings Access from ConfigScreen

**File**: `src/rally_tui/screens/config_screen.py`

Add:
- Button to open KeybindingsScreen
- Or include keybinding profile selector in existing ConfigScreen

### 6. Write Comprehensive Tests

**File**: `tests/test_keybindings.py`

Tests:
- `test_default_vim_keybindings` - verify defaults
- `test_default_emacs_keybindings` - verify emacs profile
- `test_get_keybinding_returns_default` - fallback behavior
- `test_set_keybinding_persists` - save to config
- `test_keybinding_conflict_detection` - duplicate key warning
- `test_reset_keybindings` - restore defaults
- `test_parse_key_with_modifiers` - ctrl+s parsing
- `test_invalid_keybinding_rejected` - validation

**File**: `tests/test_keybindings_screen.py`

Tests:
- `test_keybindings_screen_renders` - initial layout
- `test_profile_selector` - switch profiles
- `test_edit_keybinding` - change a key
- `test_conflict_warning` - duplicate detection
- `test_save_keybindings` - persist changes
- `test_cancel_keybindings` - discard changes
- `test_reset_to_default` - reset button

**File**: `tests/test_app_keybindings.py`

Tests:
- `test_app_loads_custom_keybindings` - custom config loaded
- `test_vim_navigation_keys` - j/k work
- `test_emacs_navigation_keys` - ctrl+n/p work with emacs profile
- `test_keybinding_override` - custom key works

## File Changes Summary

### New Files
- `src/rally_tui/utils/keybindings.py` - Keybinding utilities and registry
- `src/rally_tui/screens/keybindings_screen.py` - KeybindingsScreen modal
- `tests/test_keybindings.py` - Keybinding utility tests
- `tests/test_keybindings_screen.py` - Screen tests
- `tests/test_app_keybindings.py` - Integration tests

### Modified Files
- `src/rally_tui/user_settings.py` - Add keybindings schema
- `src/rally_tui/app.py` - Dynamic binding loading
- `src/rally_tui/widgets/ticket_list.py` - Accept custom nav keys
- `src/rally_tui/screens/__init__.py` - Export KeybindingsScreen
- `src/rally_tui/utils/__init__.py` - Export keybinding utilities
- `docs/PLAN.md` - Update iteration status
- `README.md` - Document keybinding customization

## Commit Plan

1. `feat: add keybinding utilities and action registry`
   - Create `utils/keybindings.py` with action registry and parse helpers

2. `feat: add keybindings schema to UserSettings`
   - Add keybindings storage and accessors to user_settings.py
   - Add unit tests

3. `feat: create KeybindingsScreen modal`
   - Create keybindings_screen.py with full UI
   - Add tests for screen functionality

4. `feat: implement dynamic keybinding loading in app`
   - Modify app.py to load bindings from config
   - Add F3 keybinding to open keybindings screen
   - Add integration tests

5. `feat: add Vim and Emacs preset profiles`
   - Complete preset definitions
   - Profile switching in KeybindingsScreen
   - Tests for profile switching

6. `docs: update documentation for configurable keybindings`
   - Update README with keybinding customization
   - Update PLAN.md marking iteration complete

7. `chore: bump version to 0.6.0`
   - Update pyproject.toml version

## Key Concepts

### Textual Binding Override

Textual's `BINDINGS` is processed at class definition time, but can be modified:

```python
class RallyTUI(App[None]):
    BINDINGS: ClassVar[list[Binding]] = []  # Start empty

    def __init__(self, settings: UserSettings):
        # Build bindings from settings before super().__init__()
        RallyTUI.BINDINGS = self._build_bindings(settings)
        super().__init__()

    @staticmethod
    def _build_bindings(settings: UserSettings) -> list[Binding]:
        bindings = []
        for action_id, action in ACTION_REGISTRY.items():
            key = settings.get_keybinding(action_id)
            bindings.append(Binding(key, action.handler, action.description))
        return bindings
```

### Conflict Detection

When setting a new keybinding, check for conflicts:

```python
def check_conflicts(bindings: dict[str, str], new_key: str, action_id: str) -> str | None:
    """Return conflicting action_id if key is already used, else None."""
    for aid, key in bindings.items():
        if key == new_key and aid != action_id:
            return aid
    return None
```

### Key Input Capture

In KeybindingsScreen, capture raw key input:

```python
def on_key(self, event: Key) -> None:
    if self._editing_action:
        # Capture the key for the currently editing action
        key_str = self._format_key(event)
        self._temp_bindings[self._editing_action] = key_str
        self._editing_action = None
        self._refresh_display()
        event.prevent_default()
```

## Test Coverage Target

- Keybinding utilities: 12 tests
- UserSettings keybindings: 10 tests
- KeybindingsScreen: 15 tests
- App integration: 8 tests
- **Total new tests: ~45**
- **Target total: ~540 tests**

## Deliverables

1. Users can view all keybindings via F3 or Settings > Keybindings
2. Users can customize any keybinding by selecting it and pressing a new key
3. Conflicts are detected and shown with warnings
4. Vim and Emacs presets available via profile selector
5. Reset to defaults restores original bindings
6. All customizations persist to config file
7. App loads custom bindings on startup
