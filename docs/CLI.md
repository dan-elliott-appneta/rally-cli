# Rally CLI Reference

Command-line interface for querying Rally tickets and posting comments without launching the full TUI.

## Installation

The CLI is included with rally-tui. After installing rally-tui, both commands are available:

```bash
# TUI (terminal user interface)
rally-tui

# CLI (command-line interface)
rally-cli
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `RALLY_APIKEY` | Yes | Your Rally API key |
| `RALLY_WORKSPACE` | No | Workspace name (uses default if not set) |
| `RALLY_PROJECT` | No | Project name (uses default if not set) |
| `RALLY_SERVER` | No | Rally server hostname (default: `rally1.rallydev.com`) |

### Getting Your API Key

1. Log in to Rally
2. Go to your profile settings
3. Navigate to "API Keys"
4. Create a new API key with appropriate permissions

### Example Setup

```bash
# Add to ~/.bashrc or ~/.zshrc
export RALLY_APIKEY="your_api_key_here"
export RALLY_WORKSPACE="Your Workspace"
export RALLY_PROJECT="Your Project"
```

## Commands

### Global Options

```
rally-cli [OPTIONS] COMMAND [ARGS]

Options:
  --server TEXT               Rally server hostname
  --apikey TEXT               Rally API key (overrides RALLY_APIKEY)
  --workspace TEXT            Workspace name (overrides RALLY_WORKSPACE)
  --project TEXT              Project name (overrides RALLY_PROJECT)
  --format [text|json|csv]    Output format (default: text)
  -v, --verbose               Enable verbose logging
  -q, --quiet                 Suppress non-essential output
  --version                   Show version and exit
  --help                      Show help and exit
```

---

### `rally-cli tickets`

Query and display tickets from Rally.

```bash
rally-cli tickets [OPTIONS]
```

#### Options

| Option | Description |
|--------|-------------|
| `--current-iteration` | Show only tickets in current iteration |
| `--my-tickets` | Show only tickets assigned to current user |
| `--iteration TEXT` | Filter by specific iteration name |
| `--owner TEXT` | Filter by owner display name |
| `--state TEXT` | Filter by workflow state |
| `--ticket-type TYPE` | Filter by type: `userstory`, `defect`, `task`, `testcase` |
| `--query TEXT` | Custom Rally WSAPI query string |
| `--fields TEXT` | Comma-separated fields to display |
| `--sort-by TEXT` | Sort by field (prefix with `-` for descending) |

#### Examples

```bash
# Show my tickets in current iteration (most common)
rally-cli tickets --current-iteration --my-tickets

# Show all defects in current iteration
rally-cli tickets --current-iteration --ticket-type defect

# Show tickets for a specific user
rally-cli tickets --owner "John Doe"

# Show tickets in a specific sprint
rally-cli tickets --iteration "FY26-Q1 PI Sprint 7"

# Filter by state
rally-cli tickets --state "In-Progress"

# Custom WSAPI query
rally-cli tickets --query '(State = "Defined")'

# JSON output for scripting
rally-cli --format json tickets --current-iteration --my-tickets

# CSV output for spreadsheets
rally-cli --format csv tickets --current-iteration > sprint-tickets.csv
```

#### Output Formats

**Text (default):**
```
ID       Type   State        Owner          Points  Iteration        Title
S459344  Story  In-Progress  Daniel Elliot  0.5     FY26-Q1 PI...    RC creation ticket
DE12345  Defect Completed    Jane Smith     1       FY26-Q1 PI...    Fix login bug
```

**JSON:**
```json
{
  "success": true,
  "data": [
    {
      "formatted_id": "S459344",
      "name": "RC creation ticket",
      "ticket_type": "UserStory",
      "state": "In-Progress",
      "owner": "Daniel Elliot",
      "points": 0.5,
      "iteration": "FY26-Q1 PI Sprint 7"
    }
  ]
}
```

**CSV:**
```csv
formatted_id,name,ticket_type,state,owner,points,iteration
S459344,RC creation ticket,UserStory,In-Progress,Daniel Elliot,0.5,FY26-Q1 PI Sprint 7
```

---

### `rally-cli tickets create`

Create a new ticket in Rally from the command line.

```bash
rally-cli tickets create NAME [OPTIONS]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `NAME` | Ticket title (required) |

#### Options

| Option | Description |
|--------|-------------|
| `--description TEXT` | Ticket description |
| `--points FLOAT` | Story points to set |
| `--type [UserStory\|Defect]` | Ticket type (default: UserStory) |
| `--backlog` | Put in backlog (skip iteration assignment) |

#### Examples

```bash
# Create a user story in current iteration
rally-cli tickets create "Implement login page" --description "OAuth2 flow" --points 3

# Create a defect
rally-cli tickets create "Fix null pointer in auth" --type Defect --points 1

# Create a backlog item (no iteration)
rally-cli tickets create "Future: dark mode support" --backlog

# JSON output for scripting
rally-cli --format json tickets create "My Story" --points 2
```

New tickets are automatically:
- Assigned to the current user
- Added to the current iteration (unless `--backlog` is specified)

---

### `rally-cli tickets show`

Show detailed information for a single ticket.

```bash
rally-cli tickets show TICKET_ID [OPTIONS]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `TICKET_ID` | Ticket formatted ID (e.g., `US12345`, `DE67890`) |

#### Options

| Option | Description |
|--------|-------------|
| `--format [text\|json\|csv]` | Output format |

#### Examples

```bash
# Show full ticket details
rally-cli tickets show US12345

# Show ticket details in JSON
rally-cli tickets show DE67890 --format json
```

---

### `rally-cli search`

Full-text search across Rally tickets by Name and Description.

```bash
rally-cli search QUERY [OPTIONS]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `QUERY` | Text to search for |

#### Options

| Option | Description |
|--------|-------------|
| `--type [UserStory\|Defect\|Task\|TestCase]` | Filter by ticket type |
| `--state TEXT` | Filter by workflow state |
| `--current-iteration` | Limit to the current iteration |
| `--limit INT` | Maximum number of results (default: 50) |
| `--format [text\|json\|csv]` | Output format |

#### Examples

```bash
# Search for tickets mentioning OAuth
rally-cli search "OAuth login"

# Search only user stories
rally-cli search "OAuth" --type UserStory

# Search in current iteration
rally-cli search "payment" --current-iteration

# Search with state filter
rally-cli search "login bug" --state "In-Progress"

# Limit results
rally-cli search "API" --limit 10

# JSON output for scripting
rally-cli search "authentication" --format json | jq '.data[].formatted_id'
```

---

### `rally-cli summary`

Show a sprint summary report for an iteration.

```bash
rally-cli summary [OPTIONS]
```

#### Options

| Option | Description |
|--------|-------------|
| `--iteration TEXT` | Iteration name to summarise (defaults to current iteration) |
| `--format [text\|json\|csv]` | Output format |

#### Examples

```bash
# Summary for the current iteration
rally-cli summary

# Summary for a specific iteration
rally-cli summary --iteration "FY26-Q1 PI Sprint 7"

# JSON output for scripting
rally-cli summary --format json

# CSV export
rally-cli summary --format csv > sprint-summary.csv
```

#### Output

```
Sprint Summary: FY26-Q1 PI Sprint 7 (Feb 10 - Feb 21)
=======================================================
Total Tickets:  24
Total Points:   47

By State:
  Defined            5 tickets,  12 points
  In-Progress        8 tickets,  18 points
  Completed          9 tickets,  14 points
  Accepted           2 tickets,   3 points

By Owner:
  Daniel Elliot      6 tickets,  15 points
  Jane Smith         8 tickets,  16 points
  Bob Johnson       10 tickets,  16 points

Blocked: 2 tickets
  US12345 - Waiting on API team
  DE67890 - Environment issue
```

---

### `rally-cli config`

Show the current Rally CLI configuration values.

```bash
rally-cli config [OPTIONS]
```

#### Options

| Option | Description |
|--------|-------------|
| `--format [text\|json\|csv]` | Output format |

#### Examples

```bash
# Show current configuration
rally-cli config

# Show as JSON
rally-cli config --format json
```

#### Output

```
Rally CLI Configuration
=======================
Server:     rally1.rallydev.com
Workspace:  My Workspace
Project:    My Project
API Key:    ****...1234 (set via RALLY_APIKEY)
```

---

### `rally-cli open`

Open a Rally ticket in the default web browser.

```bash
rally-cli open TICKET_ID
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `TICKET_ID` | Ticket formatted ID (e.g., `US12345`, `DE67890`) |

#### Examples

```bash
# Open a user story in browser
rally-cli open US12345

# Open a defect
rally-cli open DE67890
```

---

### `rally-cli completions`

Generate shell completion scripts for rally-cli.

```bash
rally-cli completions SHELL
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `SHELL` | Shell type: `bash`, `zsh`, or `fish` |

#### Examples

```bash
# Install bash completions (add to ~/.bashrc)
eval "$(rally-cli completions bash)"

# Install zsh completions (add to ~/.zshrc)
eval "$(rally-cli completions zsh)"

# Install fish completions (add to ~/.config/fish/config.fish)
rally-cli completions fish | source
```

---

### `rally-cli tickets update`

Update fields on one or more existing tickets.

```bash
rally-cli tickets update TICKET_IDS... [OPTIONS]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `TICKET_IDS` | One or more ticket formatted IDs (e.g., `US12345 US12346 DE67890`) |

#### Options

| Option | Description |
|--------|-------------|
| `--state TEXT` | Set workflow state |
| `--owner TEXT` | Set owner by display name |
| `--iteration TEXT` | Set iteration by name |
| `--no-iteration` | Remove from iteration (move to backlog) |
| `--points FLOAT` | Set story points |
| `--parent TEXT` | Set parent Feature ID |
| `--name TEXT` | Rename ticket |
| `--description TEXT` | Append to description (or set if empty) |
| `--description-file PATH` | Append description from file |
| `--notes TEXT` | Append to notes (or set if empty) |
| `--notes-file PATH` | Append notes from file |
| `--ac TEXT` | Append to acceptance criteria (or set if empty) |
| `--ac-file PATH` | Append acceptance criteria from file |
| `--overwrite` | Overwrite description/notes/ac instead of appending |
| `--blocked / --no-blocked` | Set/clear blocked status |
| `--blocked-reason TEXT` | Set blocked reason |
| `--ready / --no-ready` | Set/clear ready status |
| `--expedite / --no-expedite` | Set/clear expedite flag |
| `--severity TEXT` | Set severity (Defect only) |
| `--priority TEXT` | Set priority (Defect only) |
| `--target-date TEXT` | Set target date (YYYY-MM-DD) |
| `--format [text\|json\|csv]` | Output format |

#### Examples

```bash
# Update state and points (single ticket)
rally-cli tickets update US12345 --state "In-Progress" --points 3

# Change owner
rally-cli tickets update DE67890 --owner "Jane Smith"

# Move to backlog
rally-cli tickets update US12345 --no-iteration

# Append to notes (existing content preserved)
rally-cli tickets update US12345 --notes "Added deployment link"

# Overwrite description instead of appending
rally-cli tickets update US12345 --description "New description" --overwrite

# Set description from file (appends by default)
rally-cli tickets update US12345 --description-file desc.txt

# Set multiple fields at once
rally-cli tickets update US12345 --state "Completed" --ready --points 5

# Bulk update multiple tickets at once
rally-cli tickets update US12345 US12346 US12347 --state "Completed"

# Bulk move multiple tickets to a sprint
rally-cli tickets update US100 US101 US102 --iteration "FY26-Q1 PI Sprint 8"

# Pipe from search for bulk operations
rally-cli --format json tickets --current-iteration --state "Defined" | \
  jq -r '.data[].formatted_id' | \
  xargs rally-cli tickets update --state "In-Progress"
```

---

### `rally-cli tickets delete`

Delete a ticket from Rally. Requires the `--confirm` safety flag.

```bash
rally-cli tickets delete TICKET_ID --confirm [OPTIONS]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `TICKET_ID` | Ticket formatted ID (e.g., `US12345`, `DE67890`) |

#### Options

| Option | Description |
|--------|-------------|
| `--confirm` | Required safety flag to confirm deletion |
| `--format [text\|json\|csv]` | Output format |

#### Examples

```bash
# Delete a ticket (requires --confirm)
rally-cli tickets delete US12345 --confirm

# Delete with JSON output
rally-cli tickets delete DE67890 --confirm --format json
```

---

### `rally-cli discussions`

Show the discussion thread (comments) for a ticket.

```bash
rally-cli discussions TICKET_ID [OPTIONS]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `TICKET_ID` | Ticket formatted ID (e.g., `US12345`, `DE67890`) |

#### Options

| Option | Description |
|--------|-------------|
| `--format [text\|json\|csv]` | Output format |

#### Examples

```bash
# Show discussions for a ticket
rally-cli discussions US12345

# JSON output for scripting
rally-cli discussions US12345 --format json

# Extract just the comment text with jq
rally-cli discussions US12345 --format json | jq '.data.discussions[].text'

# CSV output
rally-cli discussions DE67890 --format csv
```

#### Output

```
Discussions for US12345 (2 comments)
=====================================

Jane Smith - Jan 15, 2026 10:30 AM
  Updated the implementation to use async handlers.

John Doe - Jan 16, 2026 02:15 PM
  Looks good, approved.
```

---

### `rally-cli iterations`

Show project iterations (sprints) with optional filtering.

```bash
rally-cli iterations [OPTIONS]
```

#### Options

| Option | Description |
|--------|-------------|
| `--count INT` | Number of iterations to show (default: 5) |
| `--current` | Show only the current iteration |
| `--future` | Show future iterations |
| `--past` | Show past iterations only |
| `--state TEXT` | Filter by state (Planning, Committed, Accepted) |
| `--format [text\|json\|csv]` | Output format |

#### Examples

```bash
# Show recent iterations
rally-cli iterations

# Show more iterations
rally-cli iterations --count 10

# Show only the current sprint
rally-cli iterations --current

# Show future sprints
rally-cli iterations --future

# Show past sprints
rally-cli iterations --past

# Filter by state
rally-cli iterations --state "Committed"

# JSON output for scripting
rally-cli iterations --format json

# CSV output
rally-cli iterations --format csv > iterations.csv
```

#### Output

```
Name                                    Dates                 State         Current
--------------------------------------------------------------------------------
FY26-Q1 PI Sprint 7                     Feb 10 - Feb 23       Committed     *
FY26-Q1 PI Sprint 6                     Jan 27 - Feb 09       Accepted
FY26-Q1 PI Sprint 5                     Jan 13 - Jan 26       Accepted
```

---

### `rally-cli users`

Show project members/users with optional search filtering.

```bash
rally-cli users [OPTIONS]
```

#### Options

| Option | Description |
|--------|-------------|
| `--search TEXT` | Filter users by display name (substring match) |
| `--format [text\|json\|csv]` | Output format |

#### Examples

```bash
# List all project users
rally-cli users

# Search for a specific user
rally-cli users --search "Daniel"

# JSON output for scripting
rally-cli users --format json

# CSV export
rally-cli users --format csv > team-members.csv

# Get user emails with jq
rally-cli users --format json | jq -r '.data[].user_name'
```

#### Output

```
Display Name                    Username
--------------------------------------------
Alice Baker                     abaker@example.com
Daniel Elliot                   delliot@example.com
Jane Smith                      jsmith@example.com
```

---

### `rally-cli releases`

Show project releases with optional filtering.

```bash
rally-cli releases [OPTIONS]
```

#### Options

| Option | Description |
|--------|-------------|
| `--count INT` | Number of releases to show (default: 10) |
| `--current` | Show only the current/active release |
| `--state TEXT` | Filter by state (Planning, Active, Locked) |
| `--format [text\|json\|csv]` | Output format |

#### Examples

```bash
# Show recent releases
rally-cli releases

# Show more releases
rally-cli releases --count 20

# Show only the current release
rally-cli releases --current

# Filter by state
rally-cli releases --state "Active"

# JSON output for scripting
rally-cli releases --format json

# CSV export
rally-cli releases --format csv > releases.csv
```

#### Output

```
Releases
========
Name          Start       End         State       Theme
---------------------------------------------------------
2026.Q1       Jan 01      Mar 31      Active      Security hardening
2025.Q4       Oct 01      Dec 31      Locked      Performance
```

---

### `rally-cli tags`

Manage Rally tags - list, create, and manage tags on tickets.

```bash
rally-cli tags [OPTIONS]
rally-cli tags create TAG_NAME
rally-cli tags add TICKET_ID TAG_NAME
rally-cli tags remove TICKET_ID TAG_NAME
```

#### Subcommands

| Subcommand | Description |
|------------|-------------|
| *(none)* | List all available tags |
| `create` | Create a new tag |
| `add` | Add a tag to a ticket |
| `remove` | Remove a tag from a ticket |

#### Options

| Option | Description |
|--------|-------------|
| `--format [text\|json\|csv]` | Output format |

#### Examples

```bash
# List all tags
rally-cli tags

# List tags in JSON
rally-cli tags --format json

# Create a new tag
rally-cli tags create "sprint-goal"

# Add a tag to a ticket
rally-cli tags add US12345 "sprint-goal"

# Remove a tag from a ticket
rally-cli tags remove US12345 "sprint-goal"
```

#### Output

```
Tags
====
Name
----
backlog
sprint-goal
technical-debt
```

---

### `rally-cli tickets update` (Tag & Release Options)

The `tickets update` command also supports tag and release management:

```bash
# Schedule a ticket into a release
rally-cli tickets update US12345 --release "2026.Q1"

# Unschedule from release
rally-cli tickets update US12345 --no-release

# Add a tag to a ticket
rally-cli tickets update US12345 --add-tag "sprint-goal"

# Remove a tag from a ticket
rally-cli tickets update US12345 --remove-tag "backlog"
```

| Option | Description |
|--------|-------------|
| `--release TEXT` | Release name to schedule into |
| `--no-release` | Remove from release (unschedule) |
| `--add-tag TEXT` | Add a tag to the ticket |
| `--remove-tag TEXT` | Remove a tag from the ticket |

---

### `rally-cli attachments`

Manage file attachments on Rally tickets - list, download, and upload.

```bash
rally-cli attachments list TICKET_ID [OPTIONS]
rally-cli attachments download TICKET_ID FILENAME [OPTIONS]
rally-cli attachments download TICKET_ID --all [OPTIONS]
rally-cli attachments upload TICKET_ID FILE_PATH [OPTIONS]
```

#### Subcommands

| Subcommand | Description |
|------------|-------------|
| `list` | List all attachments on a ticket |
| `download` | Download attachment(s) from a ticket |
| `upload` | Upload a file to a ticket |

#### List Options

| Option | Description |
|--------|-------------|
| `--format [text\|json\|csv]` | Output format |

#### Download Options

| Option | Description |
|--------|-------------|
| `--output PATH` | Output file path for single download |
| `--all` | Download all attachments |
| `--output-dir PATH` | Directory for `--all` downloads |
| `--format [text\|json\|csv]` | Output format |

#### Upload Options

| Option | Description |
|--------|-------------|
| `--format [text\|json\|csv]` | Output format |

#### Examples

```bash
# List attachments on a ticket
rally-cli attachments list US12345

# List in JSON format
rally-cli attachments list US12345 --format json

# Download a specific attachment
rally-cli attachments download US12345 requirements.pdf

# Download to a specific path
rally-cli attachments download US12345 requirements.pdf --output /tmp/req.pdf

# Download all attachments to a directory
rally-cli attachments download US12345 --all --output-dir ./attachments/

# Upload a file
rally-cli attachments upload US12345 ./screenshot.png

# Upload with JSON output
rally-cli attachments upload US12345 ./screenshot.png --format json
```

#### Output

```
Attachments for US12345 (2 files)
=================================
#     Name                            Size    Type
----------------------------------------------------
1     requirements.pdf               245 KB    pdf
2     screenshot.png                 100 KB    png
```

---

### `rally-cli features`

View Rally portfolio features (epics) and their child stories.

```bash
rally-cli features [OPTIONS]
rally-cli features show FEATURE_ID [OPTIONS]
```

#### Subcommands

| Subcommand | Description |
|------------|-------------|
| *(none)* | List all features in the project |
| `show` | Show details for a specific feature |

#### List Options

| Option | Description |
|--------|-------------|
| `--query TEXT` | Filter features by name |
| `--format [text\|json\|csv]` | Output format |

#### Show Options

| Option | Description |
|--------|-------------|
| `--children` | Show child user stories |
| `--format [text\|json\|csv]` | Output format |

#### Examples

```bash
# List all features
rally-cli features

# List features in JSON
rally-cli features --format json

# Filter features by name
rally-cli features --query "authentication"

# Show feature details
rally-cli features show F59625

# Show feature with child stories
rally-cli features show F59625 --children

# Show feature in JSON
rally-cli features show F59625 --format json
```

#### Output

```
Features
========
ID        Name                            State            Owner            Stories
----------------------------------------------------------------------------------
F59625    Authentication Epic              Developing       Daniel Elliot    5
F59626    Dashboard Redesign               Ideation         Jane Smith       3
```

**Show with children:**
```
F59625 - Authentication Epic
============================
State:      Developing
Owner:      Daniel Elliot
Release:    2026.Q1
Stories:    5

Child Stories:
  US12345  In-Progress      Login page implementation
  US12346  Defined           OAuth integration
```

---

### `rally-cli comment`

Add a comment to a ticket's discussion.

```bash
rally-cli comment TICKET_ID MESSAGE
rally-cli comment TICKET_ID --message-file FILE
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `TICKET_ID` | Ticket formatted ID (e.g., `S459344`, `US12345`, `DE67890`) |
| `MESSAGE` | Comment text (optional if using `--message-file`) |

#### Options

| Option | Description |
|--------|-------------|
| `--message-file PATH` | Read comment from file (use `-` for stdin) |

#### Supported Ticket Prefixes

- `S` - Story (HierarchicalRequirement)
- `US` - User Story (HierarchicalRequirement)
- `DE` - Defect
- `TA` - Task
- `TC` - Test Case

#### Examples

```bash
# Add inline comment
rally-cli comment S459344 "Deployed to staging environment"

# Add comment from file
rally-cli comment S459344 --message-file deployment-notes.txt

# Add comment from stdin (useful in scripts)
echo "Build passed: $BUILD_NUMBER" | rally-cli comment S459344 --message-file -

# JSON output for scripting
rally-cli --format json comment S459344 "Done"
```

#### Output

```
Comment added to S459344
User: Daniel Elliot
Time: Feb 05, 2026 06:08 AM
Text: Deployed to staging environment
```

---

## Scripting Examples

### Daily Standup Report

```bash
#!/bin/bash
# Generate daily standup report

echo "=== My Current Sprint Tickets ==="
rally-cli tickets --current-iteration --my-tickets

echo ""
echo "=== In Progress ==="
rally-cli tickets --current-iteration --my-tickets --state "In-Progress"

echo ""
echo "=== Sprint Summary ==="
rally-cli summary
```

### Sprint Summary Report

```bash
#!/bin/bash
# Email sprint summary as JSON for dashboard integration
rally-cli summary --format json | jq '{
  iteration: .data.iteration_name,
  total: .data.total_tickets,
  points: .data.total_points,
  blocked: (.data.blocked | length)
}'
```

### Bulk Ticket Operations

```bash
#!/bin/bash
# Move all defined tickets to in-progress at sprint start
rally-cli --format json tickets --current-iteration --state "Defined" | \
  jq -r '.data[].formatted_id' | \
  xargs rally-cli tickets update --state "In-Progress"

# Mark multiple tickets completed
rally-cli tickets update US12345 US12346 US12347 --state "Completed"

# Move tickets to next sprint
rally-cli tickets update US100 US101 US102 --iteration "FY26-Q1 PI Sprint 8"
```

### Export Sprint to CSV

```bash
#!/bin/bash
# Export current sprint tickets to CSV

DATE=$(date +%Y-%m-%d)
rally-cli --format csv tickets --current-iteration > "sprint-export-$DATE.csv"
echo "Exported to sprint-export-$DATE.csv"
```

### Automated Deployment Comment

```bash
#!/bin/bash
# Post deployment comment after CI/CD

TICKET_ID="$1"
ENVIRONMENT="$2"
VERSION="$3"

rally-cli comment "$TICKET_ID" "Deployed v$VERSION to $ENVIRONMENT at $(date)"
```

### JSON Processing with jq

```bash
# Get ticket IDs in progress
rally-cli --format json tickets --current-iteration --state "In-Progress" | \
  jq -r '.data[].formatted_id'

# Count tickets by state
rally-cli --format json tickets --current-iteration | \
  jq '.data | group_by(.state) | map({state: .[0].state, count: length})'

# Sum story points
rally-cli --format json tickets --current-iteration --my-tickets | \
  jq '[.data[].points // 0] | add'
```

### Batch Comments

```bash
#!/bin/bash
# Add the same comment to multiple tickets

COMMENT="Sprint review completed"
TICKETS="S459344 S459345 S459346"

for ticket in $TICKETS; do
  rally-cli comment "$ticket" "$COMMENT"
  echo "Commented on $ticket"
done
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (API error, network failure) |
| 2 | Invalid arguments or input |
| 3 | Authentication error |
| 4 | Configuration error |

---

## Troubleshooting

### "RALLY_APIKEY environment variable not set"

Set your API key:
```bash
export RALLY_APIKEY="your_api_key_here"
```

### "Authentication failed: Invalid API key"

- Verify your API key is correct
- Check the key hasn't expired
- Ensure the key has appropriate permissions

### "Ticket not found"

- Verify the ticket ID format (S459344, US12345, DE67890)
- Check you have access to the project containing the ticket
- Ensure the ticket exists in Rally

### Verbose Mode

Enable verbose logging to debug issues:
```bash
rally-cli -v tickets --current-iteration
```

---

## See Also

- [README.md](../README.md) - Main project documentation
- [USER.md](USER.md) - TUI user guide
- [API.md](API.md) - Rally API documentation
