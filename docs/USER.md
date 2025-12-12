# Rally TUI User Manual

A comprehensive guide to using Rally TUI for managing Rally (Broadcom) work items from your terminal.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Interface Overview](#interface-overview)
3. [Navigation](#navigation)
4. [Viewing Tickets](#viewing-tickets)
5. [Searching and Filtering](#searching-and-filtering)
6. [Managing Tickets](#managing-tickets)
7. [Bulk Operations](#bulk-operations)
8. [Discussions and Comments](#discussions-and-comments)
9. [Attachments](#attachments)
10. [Settings and Configuration](#settings-and-configuration)
11. [Keyboard Shortcuts Reference](#keyboard-shortcuts-reference)
12. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- A modern terminal with color support
- Rally API key (for live data)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd rally-cli

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install
pip install -e ".[dev]"
```

### Configuration

Set environment variables to connect to Rally:

```bash
export RALLY_APIKEY=your_api_key_here
export RALLY_WORKSPACE="Your Workspace"
export RALLY_PROJECT="Your Project"
```

| Variable | Description | Default |
|----------|-------------|---------|
| `RALLY_SERVER` | Rally server hostname | `rally1.rallydev.com` |
| `RALLY_APIKEY` | Rally API key (required) | (none) |
| `RALLY_WORKSPACE` | Workspace name | (from API) |
| `RALLY_PROJECT` | Project name | (from API) |

### Running Rally TUI

```bash
# With Rally API connection
rally-tui

# Check version
rally-tui --version
```

**Offline Mode**: If `RALLY_APIKEY` is not set, Rally TUI runs with sample data for demonstration purposes.

---

## Interface Overview

Rally TUI uses a split-pane layout:

```
┌─────────────────────────────────────────────────────────────────┐
│ Header                                                          │
├─────────────────────────────────────────────────────────────────┤
│ Project: My Project | Sort: State | Connected as username       │  <- Status Bar
├─────────────────────────┬───────────────────────────────────────┤
│                         │                                       │
│   Ticket List           │        Ticket Details                 │
│   (Left Panel)          │        (Right Panel)                  │
│                         │                                       │
│  . US12345 User Story   │  US12345: Implement feature           │
│  + US12346 Another...   │  ─────────────────────────            │
│  - DE12347 Fix bug      │  Type: User Story                     │
│  ✓ US12348 Completed    │  State: In Progress                   │
│                         │  Owner: John Smith                    │
│                         │  Points: 5                            │
│                         │                                       │
│                         │  Description:                         │
│                         │  This is the ticket description...    │
│                         │                                       │
├─────────────────────────┴───────────────────────────────────────┤
│ Footer: Keyboard shortcuts                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Status Bar Indicators

The status bar shows:
- **Project**: Current Rally project
- **Loading.../Refreshing...**: When fetching data (cyan)
- **X selected**: Number of selected tickets (for bulk operations)
- **Sprint: X**: Active sprint/iteration filter
- **My Items**: When filtering to your tickets only
- **Sort: X**: Current sort mode (State, Recent, Owner)
- **Search: query (X/Y)**: Active search with match count
- **Cache status**: Live, Cached (Xm), Refreshing, or Offline
- **Connection**: Connected as username / Offline

### State Indicators

Tickets show workflow state with colored symbols:
- `.` (dim) - Not Started (Defined, Idea)
- `+` (yellow) - In Progress
- `-` (blue) - Done (Completed)
- `✓` (green) - Accepted

### Color Coding

Ticket types are color-coded:
- **Green** - User Stories (US)
- **Red** - Defects (DE)
- **Yellow** - Tasks (TA)
- **Blue** - Test Cases (TC)

---

## Navigation

### Basic Movement

| Key | Action |
|-----|--------|
| `j` or `↓` | Move down |
| `k` or `↑` | Move up |
| `g` | Jump to top |
| `G` | Jump to bottom |
| `Tab` | Switch between list and detail panels |
| `Enter` | Select/confirm |
| `Esc` | Go back / Clear |
| `q` | Quit |

### Panel Focus

- Press `Tab` to switch focus between the ticket list and detail panel
- The focused panel has a highlighted border
- Most actions work regardless of which panel is focused

---

## Viewing Tickets

### Ticket List (Left Panel)

The ticket list shows all tickets matching your current filters:
- Scroll with `j`/`k` or arrow keys
- Tickets are sorted by workflow state by default
- The highlighted ticket's details appear in the right panel

### Ticket Details (Right Panel)

Shows full information for the highlighted ticket:
- Ticket ID and title
- Type, State, Owner, Points
- Iteration/Sprint assignment
- Parent Feature (if set)
- Description or Notes

### Toggle Description/Notes

Press `n` to toggle between viewing the ticket's **Description** and **Notes** field.

### Sorting

Press `o` to cycle through sort modes:
1. **State** (default) - Workflow order (Defined → In Progress → Completed → Accepted)
2. **Recent** - Recently created tickets first
3. **Owner** - Alphabetical by owner name

The current sort mode is shown in the status bar.

---

## Searching and Filtering

### Quick Search

Press `/` to enter search mode:
1. Type your search query
2. Results filter in real-time as you type
3. Press `Enter` to confirm and return to the list
4. Press `Esc` to clear the search

Search matches against:
- Ticket ID (US12345, DE12346, etc.)
- Ticket name/title
- Owner name
- State

The status bar shows: `Search: <query> (X/Y)` where X is matches and Y is total.

### Sprint/Iteration Filter

Press `i` to open the iteration picker:
- Select a sprint to show only tickets in that sprint
- Select "All Iterations" to show all tickets
- Select "Backlog" to show unscheduled tickets

### My Items Filter

Press `u` to toggle showing only tickets assigned to you.

### Combined Filters

Filters can be combined:
- Sprint filter + My Items shows your tickets in a specific sprint
- Search works within your filtered results

Active filters are shown in the status bar.

---

## Managing Tickets

### Copy Ticket URL

Press `y` to copy the Rally URL for the current ticket to your clipboard.

### Set Story Points

Press `p` to set story points:
1. Select from common values (1, 2, 3, 5, 8, 13)
2. Or enter a custom value
3. Press `Enter` to confirm

### Change Ticket State

Press `s` to change the ticket's workflow state:
- **Defined** - Not started
- **In Progress** - Work has begun
- **Completed** - Work is done
- **Accepted** - Verified and closed

**Note**: Moving to "In Progress" may require setting a parent Feature first.

### Set Parent Feature

When required (e.g., before moving to In Progress):
1. Press `s` to change state
2. If prompted, select a parent Feature
3. Choose from configured options or enter a custom Feature ID

Configure parent options in settings (F2) or `~/.config/rally-tui/config.json`.

### Create New Ticket

Press `w` to create a new work item:
1. Enter the ticket title
2. Select type: User Story or Defect
3. Optionally add a description
4. Press `Ctrl+S` to create

New tickets are automatically:
- Assigned to you
- Added to the current iteration

---

## Bulk Operations

### Selecting Multiple Tickets

| Key | Action |
|-----|--------|
| `Space` | Toggle selection on current ticket |
| `Ctrl+A` | Select all / Deselect all |

Selected tickets show a checkbox marker. The status bar shows the selection count.

### Bulk Actions Menu

Press `m` with tickets selected to open the bulk actions menu:

1. **Set Parent** - Assign a parent Feature to all selected tickets
2. **Set State** - Change state on all selected tickets
3. **Set Iteration** - Move all selected tickets to a sprint
4. **Set Points** - Set story points on all selected tickets

### Example: Move Multiple Tickets to a Sprint

1. Press `Space` on each ticket to select, or `Ctrl+A` for all
2. Press `m` to open bulk actions
3. Select "Set Iteration"
4. Choose the target sprint
5. All selected tickets are moved

---

## Discussions and Comments

### View Discussions

Press `d` to open the discussions screen for the current ticket:
- Shows all comments/discussion posts
- Displays author and timestamp for each
- HTML content is converted to readable text

### Add a Comment

From the discussions screen:
1. Press `c` to open the comment editor
2. Type your comment
3. Press `Ctrl+S` to submit
4. Press `Esc` to cancel

---

## Attachments

### View Attachments

Press `a` to view attachments for the current ticket:
- Shows file attachments uploaded to the ticket
- Shows embedded images from the description/notes
- Displays file size and upload date

### Download Attachments

From the attachments screen:
1. Select the attachment to download
2. Press `Enter` or `d`
3. Choose download location
4. File is downloaded to your system

### Upload Attachments

From the attachments screen:
1. Press `u` to upload
2. Enter the file path
3. File is uploaded to the ticket

---

## Settings and Configuration

### Settings Screen (F2)

Press `F2` to open the settings screen:

- **Theme**: Choose from available themes
- **Log Level**: Set logging verbosity (DEBUG, INFO, WARNING, ERROR)
- **Parent Options**: Configure Feature IDs for quick parent selection

Press `Ctrl+S` or click Save to apply changes.

### Keybindings Screen (F3)

Press `F3` to view and customize keyboard shortcuts:

- **Profiles**: Choose Vim, Emacs, or Custom
- **Edit Bindings**: Click a row to change a keybinding
- **Conflict Detection**: Warns if a key is already assigned
- **Reset**: Restore default keybindings

### Themes

Available themes:
- `textual-dark` / `textual-light`
- `catppuccin-mocha` / `catppuccin-latte`
- `nord`
- `gruvbox`
- `dracula`
- `tokyo-night`
- `monokai`
- `flexoki`
- `solarized-light`

Press `t` for quick dark/light toggle, or use the command palette (`Ctrl+P`).

### Configuration File

Settings are stored in `~/.config/rally-tui/config.json`:

```json
{
  "theme": "dark",
  "theme_name": "catppuccin-mocha",
  "log_level": "INFO",
  "parent_options": ["F12345", "F12346", "F12347"],
  "keybinding_profile": "vim",
  "keybindings": {
    "navigation.down": "j",
    "navigation.up": "k"
  },
  "cache_enabled": true,
  "cache_ttl_minutes": 5,
  "cache_auto_refresh": true
}
```

### Cache Settings

Rally TUI caches tickets locally for performance:

- **cache_enabled**: Enable/disable caching (default: true)
- **cache_ttl_minutes**: Cache lifetime in minutes (default: 5)
- **cache_auto_refresh**: Auto-refresh stale cache (default: true)

Cache files are stored in `~/.cache/rally-tui/`.

Press `r` to manually refresh the cache.

### Logging

Logs are written to `~/.config/rally-tui/rally-tui.log`:
- Automatic rotation (5MB max, 3 backups)
- Set log level in settings (F2) or config file

---

## Keyboard Shortcuts Reference

### Global

| Key | Action |
|-----|--------|
| `Ctrl+P` | Open command palette |
| `t` | Toggle dark/light theme |
| `F2` | Open settings |
| `F3` | Open keybindings |
| `q` | Quit |
| `Esc` | Go back / Cancel |

### List Navigation

| Key | Action |
|-----|--------|
| `j` / `↓` | Move down |
| `k` / `↑` | Move up |
| `g` | Jump to top |
| `G` | Jump to bottom |
| `Tab` | Switch to detail panel |
| `Enter` | Select item |

### Ticket Actions

| Key | Action |
|-----|--------|
| `y` | Copy ticket URL |
| `s` | Set state |
| `p` | Set points |
| `n` | Toggle description/notes |
| `d` | Open discussions |
| `a` | View attachments |
| `w` | Create new ticket |

### Filtering

| Key | Action |
|-----|--------|
| `/` | Search/filter |
| `i` | Filter by iteration |
| `u` | Toggle My Items |
| `o` | Cycle sort mode |
| `r` | Refresh cache |

### Selection (Bulk Operations)

| Key | Action |
|-----|--------|
| `Space` | Toggle selection |
| `Ctrl+A` | Select/deselect all |
| `m` | Open bulk actions menu |

### Discussions

| Key | Action |
|-----|--------|
| `c` | Add comment |
| `Ctrl+S` | Submit comment |

---

## Troubleshooting

### Connection Issues

**Problem**: "Offline" status when you expect to be connected

**Solutions**:
1. Check `RALLY_APIKEY` is set correctly
2. Verify network connectivity to Rally server
3. Check logs at `~/.config/rally-tui/rally-tui.log`

### Tickets Not Showing

**Problem**: Ticket list appears empty

**Solutions**:
1. Check your filters - press `u` to toggle My Items off
2. Press `i` and select "All Iterations"
3. Press `Esc` to clear any search filter
4. Press `r` to refresh the cache

### Cache Issues

**Problem**: Stale data or tickets not updating

**Solutions**:
1. Press `r` to manually refresh
2. Check cache settings in `~/.config/rally-tui/config.json`
3. Delete cache files in `~/.cache/rally-tui/`

### Keybinding Conflicts

**Problem**: A key doesn't work as expected

**Solutions**:
1. Press `F3` to view current keybindings
2. Check for conflicts (highlighted in red)
3. Reset to defaults if needed

### Log Files

For debugging, check the log file:
```bash
cat ~/.config/rally-tui/rally-tui.log
```

Set log level to DEBUG in settings (F2) for more detail.

---

## Tips and Tricks

1. **Quick Navigation**: Use `g` and `G` to jump to top/bottom of the list
2. **Efficient Filtering**: Combine sprint filter (`i`) with My Items (`u`) for focused views
3. **Bulk Updates**: Select multiple tickets with `Space`, then use `m` for batch operations
4. **Theme Switching**: Use `Ctrl+P` command palette for quick theme access
5. **URL Sharing**: Press `y` to quickly copy a ticket URL for sharing
6. **Keyboard Profiles**: Try Emacs profile (`F3`) if you prefer Emacs-style navigation

---

## Version Information

- Current Version: 0.7.5
- Check version: `rally-tui --version`
- Version shown on splash screen at startup

For the latest updates, see the [README](../README.md) and [PLAN.md](PLAN.md).
