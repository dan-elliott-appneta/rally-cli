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
