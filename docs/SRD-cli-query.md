# SRD: CLI Query Functionality for Rally TUI

## Overview

This Software Requirements Document (SRD) specifies the design and implementation plan for adding pure CLI (Command-Line Interface) query functionality to the rally-cli repository. Currently, rally-cli is a full TUI (Terminal User Interface) application built with Textual. This enhancement will add non-interactive CLI commands that can be used for scripting, automation, and quick queries without launching the full TUI.

The CLI functionality will coexist with the existing TUI, leveraging the same underlying service layer (AsyncRallyClient) while providing a streamlined command-line interface for common query and update operations.

## Goals

1. **Query Current Iteration Tickets**: Provide a CLI command to fetch and display tickets assigned to the API user in the current iteration
2. **Post Comments**: Enable adding comments to tickets via CLI using ticket ID or formatted ID
3. **Scriptable Interface**: Output formats suitable for scripting (JSON, plain text, CSV)
4. **Reuse Architecture**: Leverage existing Rally API clients, models, and configuration
5. **Maintain Consistency**: Use the same authentication, error handling, and logging patterns as the TUI

## Non-Goals

1. **Full TUI Replacement**: The CLI is not intended to replace the rich interactive TUI experience
2. **Comprehensive CRUD**: Initial implementation focuses on querying and commenting only (no ticket creation, bulk updates, etc.)
3. **Advanced Filtering UI**: No interactive filter builders - users specify filters via command-line arguments
4. **Offline Mode**: CLI requires active Rally API connection (no sample data fallback like TUI)
5. **Configuration UI**: CLI users configure via environment variables or config files, not interactive prompts

## Technical Architecture

### Architecture Decision Records

**ADR-001: Use AsyncRallyClient for CLI Operations**
- **Decision**: Use the async Rally client for all CLI operations
- **Rationale**: AsyncRallyClient is the modern, well-tested client with better performance. CLI can run async code via asyncio.run()
- **Impact**: CLI will be async-native, enabling future concurrent operations

**ADR-002: Separate CLI Entry Point from TUI**
- **Decision**: Create new CLI entry point `rally-cli` separate from existing `rally-tui` TUI entry point
- **Rationale**: Clean separation of concerns, different command-line argument parsing, different user expectations
- **Impact**: pyproject.toml will define two console scripts: `rally-tui` (existing) and `rally-cli` (new)

**ADR-003: Use Click for CLI Framework**
- **Decision**: Use Click library for command-line argument parsing and command structure
- **Rationale**: Industry standard, excellent documentation, supports command groups, argument validation, and help text generation
- **Impact**: Add `click>=8.1.0` to dependencies

**ADR-004: Support Multiple Output Formats**
- **Decision**: Support text (default), JSON, and CSV output formats
- **Rationale**: Different use cases require different formats (human-readable vs machine-parseable)
- **Impact**: Each command implements format-agnostic data preparation and format-specific rendering

**ADR-005: Reuse Existing Configuration System**
- **Decision**: CLI uses the same RallyConfig (pydantic-settings) as TUI
- **Rationale**: Consistency, DRY principle, same environment variables work for both interfaces
- **Impact**: CLI and TUI share RALLY_APIKEY, RALLY_WORKSPACE, etc.

### Component Architecture

```
rally-cli/
├── src/rally_tui/
│   ├── cli/                      # NEW: CLI command structure
│   │   ├── __init__.py
│   │   ├── main.py               # CLI entry point (rally-cli command)
│   │   ├── commands/             # CLI command implementations
│   │   │   ├── __init__.py
│   │   │   ├── query.py          # Query commands (tickets, iterations, etc.)
│   │   │   └── comment.py        # Comment commands
│   │   ├── formatters/           # Output formatting utilities
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # Base formatter interface
│   │   │   ├── text.py           # Human-readable text output
│   │   │   ├── json.py           # JSON output
│   │   │   └── csv.py            # CSV output
│   │   └── utils.py              # CLI-specific utilities
│   ├── config.py                 # EXISTING: Shared configuration
│   ├── models/                   # EXISTING: Shared data models
│   └── services/                 # EXISTING: Shared API clients
│       └── async_rally_client.py # EXISTING: Primary client for CLI
```

### Data Flow

```
CLI Command Invocation
    ↓
Click Argument Parsing
    ↓
RallyConfig Loading (env vars)
    ↓
AsyncRallyClient Initialization
    ↓
API Query/Update
    ↓
Data Model (Ticket, Discussion, etc.)
    ↓
Format Selection (JSON/Text/CSV)
    ↓
Formatted Output to stdout
```

## Data Models

### Existing Models (Reused)

The CLI will use existing data models from `rally_tui.models`:

**Ticket** (from `models/ticket.py`):
```python
@dataclass(frozen=True)
class Ticket:
    formatted_id: str
    name: str
    ticket_type: TicketType  # "UserStory" | "Defect" | "Task" | "TestCase"
    state: str
    owner: str | None
    description: str
    notes: str
    iteration: str | None
    points: int | float | None
    object_id: str | None
    parent_id: str | None
```

**Discussion** (from `models/discussion.py`):
```python
@dataclass(frozen=True)
class Discussion:
    object_id: str
    text: str
    user: str
    created_at: datetime
    artifact_id: str  # Ticket formatted_id
```

### New Models

**CLIResult** (new in `cli/models.py`):
```python
@dataclass
class CLIResult:
    """Standard CLI command result wrapper."""
    success: bool
    data: Any
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error
        }
```

## CLI Design

### Command Structure

```
rally-cli [GLOBAL OPTIONS] <command> [COMMAND OPTIONS]

Global Options:
  --server TEXT        Rally server hostname (default: rally1.rallydev.com)
  --apikey TEXT        Rally API key (or use RALLY_APIKEY env var)
  --workspace TEXT     Workspace name (or use RALLY_WORKSPACE env var)
  --project TEXT       Project name (or use RALLY_PROJECT env var)
  --format [text|json|csv]  Output format (default: text)
  --verbose / --quiet  Enable/disable verbose logging
  --help               Show help message

Commands:
  tickets              Query tickets
  comment              Add comment to ticket
```

### Command: `rally-cli tickets`

**Purpose**: Query and display tickets with filtering options

**Syntax**:
```bash
rally-cli tickets [OPTIONS]
```

**Options**:
```
--current-iteration    Show only tickets in current iteration (default: False)
--my-tickets           Show only tickets assigned to current user (default: False)
--iteration TEXT       Filter by specific iteration name
--owner TEXT           Filter by owner display name
--state TEXT           Filter by workflow state
--ticket-type TEXT     Filter by type (UserStory, Defect, Task, TestCase)
--query TEXT           Custom Rally WSAPI query string
--fields TEXT          Comma-separated fields to display (default: id,name,state,owner,points)
--sort-by TEXT         Sort by field (default: formatted_id)
```

**Default Behavior**:
- Without flags: Returns ALL tickets in project (scoped to project, excludes "Jira Migration")
- With `--current-iteration`: Returns tickets in current iteration
- With `--my-tickets`: Returns tickets owned by API user
- Combine flags: `--current-iteration --my-tickets` (most common usage)

**Examples**:
```bash
# Show my tickets in current iteration
rally-cli tickets --current-iteration --my-tickets

# Show all tickets in a specific iteration
rally-cli tickets --iteration "Sprint 2024.01"

# Show tickets owned by specific user
rally-cli tickets --owner "John Doe"

# Show all defects in current iteration
rally-cli tickets --current-iteration --ticket-type Defect

# Custom query with JSON output
rally-cli tickets --query '(State = "In-Progress")' --format json

# Show specific fields
rally-cli tickets --my-tickets --fields id,name,state,points,iteration
```

**Output Format (text)**:
```
ID       Type    State        Owner        Points  Iteration         Title
US12345  Story   In-Progress  John Doe     5       Sprint 2024.01    User login feature
DE67890  Defect  Completed    Jane Smith   3       Sprint 2024.01    Fix API timeout
US23456  Story   Defined      John Doe     8       Sprint 2024.01    Dashboard widgets
```

**Output Format (json)**:
```json
{
  "success": true,
  "data": [
    {
      "formatted_id": "US12345",
      "name": "User login feature",
      "ticket_type": "UserStory",
      "state": "In-Progress",
      "owner": "John Doe",
      "description": "Implement OAuth2 login...",
      "notes": "",
      "iteration": "Sprint 2024.01",
      "points": 5,
      "object_id": "123456789",
      "parent_id": "F59625"
    }
  ],
  "error": null
}
```

**Output Format (csv)**:
```csv
formatted_id,name,ticket_type,state,owner,points,iteration
US12345,User login feature,UserStory,In-Progress,John Doe,5,Sprint 2024.01
DE67890,Fix API timeout,Defect,Completed,Jane Smith,3,Sprint 2024.01
```

### Command: `rally-cli comment`

**Purpose**: Add a comment to a ticket's discussion

**Syntax**:
```bash
rally-cli comment <TICKET_ID> <MESSAGE>
rally-cli comment <TICKET_ID> --message-file <FILE>
```

**Arguments**:
```
TICKET_ID            Ticket formatted ID (e.g., US12345, DE67890)
```

**Options**:
```
--message TEXT       Comment text (required if not using --message-file)
--message-file PATH  Read comment text from file (supports - for stdin)
```

**Examples**:
```bash
# Add comment with inline text
rally-cli comment US12345 "Updated the authentication flow"

# Add comment with message option (useful for special characters)
rally-cli comment US12345 --message "Fixed issue #123"

# Add comment from file
rally-cli comment US12345 --message-file comment.txt

# Add comment from stdin (pipeline usage)
echo "Deployment complete" | rally-cli comment US12345 --message-file -

# JSON output for scripting
rally-cli comment US12345 "Done" --format json
```

**Output Format (text)**:
```
✓ Comment added to US12345
User: John Doe
Time: 2024-01-25 14:30:00
Text: Updated the authentication flow
```

**Output Format (json)**:
```json
{
  "success": true,
  "data": {
    "object_id": "987654321",
    "text": "Updated the authentication flow",
    "user": "John Doe",
    "created_at": "2024-01-25T14:30:00Z",
    "artifact_id": "US12345"
  },
  "error": null
}
```

**Error Handling**:
```bash
# Ticket not found
rally-cli comment US99999 "Test"
# Output: Error: Ticket US99999 not found
# Exit code: 1

# API error
rally-cli comment US12345 "Test"
# Output: Error: Failed to add comment: API connection failed
# Exit code: 1
```

### Exit Codes

```
0  - Success
1  - General error (ticket not found, API error, etc.)
2  - Invalid arguments
3  - Authentication error (invalid API key)
4  - Configuration error (missing required config)
```

## Implementation Phases

### Phase 1: Project Setup and Foundation
**Goal**: Set up CLI infrastructure and configuration

**Tasks**:
- [ ] Add Click dependency to pyproject.toml (`click>=8.1.0`)
- [ ] Create `src/rally_tui/cli/` directory structure
- [ ] Create CLI entry point in `cli/main.py` with Click app and global options
- [ ] Add `rally-cli` console script to pyproject.toml
- [ ] Create base formatter interface in `cli/formatters/base.py`
- [ ] Implement text formatter in `cli/formatters/text.py`
- [ ] Implement JSON formatter in `cli/formatters/json.py`
- [ ] Implement CSV formatter in `cli/formatters/csv.py`

**Testing**:
- [ ] Test CLI entry point can be invoked (`rally-cli --help`)
- [ ] Test global option parsing (--server, --apikey, --format)
- [ ] Test each formatter with sample data
- [ ] Test configuration loading from environment variables

**Acceptance Criteria**:
- `rally-cli --help` displays help text with available commands
- `rally-cli --version` displays current version
- Global options are parsed correctly
- All three output formatters work with test data

---

### Phase 2: Tickets Query Command
**Goal**: Implement the `tickets` command with filtering

**Tasks**:
- [ ] Create `cli/commands/query.py` module
- [ ] Implement `tickets` Click command with all filtering options
- [ ] Implement query builder logic (current iteration, my tickets, custom query)
- [ ] Add AsyncRallyClient initialization and connection handling
- [ ] Implement ticket fetching with query filters
- [ ] Add field selection logic (--fields option)
- [ ] Implement sorting logic (--sort-by option)
- [ ] Wire up formatters for ticket output (text, JSON, CSV)
- [ ] Add error handling and logging
- [ ] Implement exit code logic

**Testing**:
- [ ] Unit test query builder for different filter combinations
- [ ] Unit test field selection logic
- [ ] Unit test sorting logic
- [ ] Integration test with MockRallyClient for basic query
- [ ] Integration test for --current-iteration flag
- [ ] Integration test for --my-tickets flag
- [ ] Integration test for combined filters
- [ ] Integration test for custom --query option
- [ ] Test all output formats (text, JSON, CSV)
- [ ] Test error cases (no API key, network error, no results)

**Acceptance Criteria**:
- `rally-cli tickets` returns all project tickets
- `rally-cli tickets --current-iteration --my-tickets` returns current user's current iteration tickets
- All filter options work correctly
- All output formats produce valid output
- Error messages are clear and actionable
- Exit codes are correct for success/failure cases

---

### Phase 3: Comment Command
**Goal**: Implement the `comment` command for adding comments

**Tasks**:
- [ ] Create `cli/commands/comment.py` module
- [ ] Implement `comment` Click command with ticket ID argument
- [ ] Add message input handling (inline, --message, --message-file)
- [ ] Add stdin support for --message-file (dash - for stdin)
- [ ] Implement ticket lookup by formatted ID
- [ ] Implement comment posting via AsyncRallyClient.add_comment()
- [ ] Wire up formatters for comment confirmation output
- [ ] Add error handling for ticket not found
- [ ] Add error handling for API failures
- [ ] Implement exit code logic

**Testing**:
- [ ] Unit test message input handling (inline vs file vs stdin)
- [ ] Integration test with MockRallyClient for successful comment
- [ ] Integration test for ticket not found error
- [ ] Integration test for API error handling
- [ ] Test comment from file (--message-file)
- [ ] Test comment from stdin (echo | rally-cli comment)
- [ ] Test all output formats (text, JSON)
- [ ] Test exit codes for success and error cases

**Acceptance Criteria**:
- `rally-cli comment US12345 "Test"` successfully adds comment
- `rally-cli comment US12345 --message-file comment.txt` reads from file
- `echo "Test" | rally-cli comment US12345 --message-file -` reads from stdin
- Error message shown for non-existent ticket
- Error message shown for API failures
- Output includes confirmation with comment details
- Exit codes are correct

---

### Phase 4: Documentation and Examples
**Goal**: Provide comprehensive documentation for CLI users

**Tasks**:
- [ ] Create `docs/CLI.md` with full CLI reference
- [ ] Add usage examples for common scenarios
- [ ] Document environment variable configuration
- [ ] Add scripting examples (bash, automation)
- [ ] Update README.md to mention CLI functionality
- [ ] Add CLI section to USER.md
- [ ] Create example scripts in `examples/` directory
- [ ] Add troubleshooting guide for CLI issues

**Testing**:
- [ ] Manual testing of all documented examples
- [ ] Verify all code snippets in docs execute correctly
- [ ] Test example scripts in `examples/`

**Acceptance Criteria**:
- Complete CLI reference documentation exists
- All examples in docs are tested and working
- Example scripts demonstrate common use cases
- README.md clearly distinguishes TUI vs CLI usage

---

### Phase 5: Testing and Quality Assurance
**Goal**: Ensure production-ready quality with comprehensive tests

**Tasks**:
- [ ] Create `tests/cli/` directory for CLI-specific tests
- [ ] Write unit tests for all CLI commands (target: 90%+ coverage)
- [ ] Write integration tests with AsyncMockRallyClient
- [ ] Add end-to-end tests with sample data
- [ ] Test error handling and edge cases
- [ ] Add tests for output format rendering
- [ ] Test CLI with real Rally API (manual QA)
- [ ] Add CI/CD checks for CLI tests
- [ ] Test cross-platform compatibility (Linux, macOS, Windows)

**Testing**:
- [ ] All tests pass in CI/CD
- [ ] Coverage report shows 90%+ for CLI code
- [ ] Manual QA with real Rally instance confirms functionality
- [ ] Cross-platform testing confirms compatibility

**Acceptance Criteria**:
- Test suite covers all CLI commands and options
- Coverage exceeds 90% for CLI modules
- All tests pass in CI/CD pipeline
- Manual QA confirms production readiness
- CLI works on Linux, macOS, and Windows

---

## Testing Requirements

### Unit Testing

**Test Coverage Goals**:
- CLI command logic: 95%+
- Query builder: 100%
- Formatters: 100%
- Error handling: 90%+

**Test Files**:
```
tests/cli/
├── __init__.py
├── test_main.py                 # CLI entry point tests
├── test_tickets_command.py      # Tickets query command tests
├── test_comment_command.py      # Comment command tests
├── test_query_builder.py        # Query construction logic
├── formatters/
│   ├── test_text_formatter.py   # Text output tests
│   ├── test_json_formatter.py   # JSON output tests
│   └── test_csv_formatter.py    # CSV output tests
└── test_integration.py          # End-to-end integration tests
```

**Mock Dependencies**:
- Use `AsyncMockRallyClient` from existing test infrastructure
- Mock `RallyConfig` for configuration testing
- Mock file I/O for `--message-file` testing

### Integration Testing

**Scenarios**:
1. Query tickets with various filters (current iteration, my tickets, custom query)
2. Add comment to existing ticket
3. Handle errors gracefully (ticket not found, API errors, auth failures)
4. Output formatting for all supported formats (text, JSON, CSV)
5. Environment variable configuration
6. Exit code verification for success/failure cases

**Test Fixtures**:
- Reuse existing `Ticket` and `Discussion` fixtures from TUI tests
- Create CLI-specific fixtures for command-line arguments
- Create sample output files for comparison testing

### Manual QA Checklist

Before release:
- [ ] Test with real Rally API connection
- [ ] Verify all command-line options work as documented
- [ ] Test error messages are clear and actionable
- [ ] Verify output formats are valid (JSON parseable, CSV importable)
- [ ] Test scripting scenarios (piping, automation)
- [ ] Verify environment variable configuration works
- [ ] Test on Linux, macOS, and Windows
- [ ] Verify help text is accurate and complete

## Security Considerations

### Authentication and Credentials

**API Key Handling**:
- API key never logged or printed to stdout/stderr
- Support RALLY_APIKEY environment variable (most secure)
- Support --apikey flag (less secure, visible in process list)
- Warn users about --apikey security implications in documentation

**Logging Redaction**:
- Reuse existing `RedactingFilter` from `utils/redacting_filter.py`
- Ensure API keys, user emails, and sensitive data are redacted from CLI logs
- Log CLI operations to same log file as TUI (`~/.config/rally-tui/rally-tui.log`)

### Data Exposure

**Output Sanitization**:
- Ticket descriptions may contain sensitive information - users should be aware
- JSON output includes all fields - document this clearly
- CSV output suitable for data export - warn about sensitive data
- Consider adding `--redact` flag for sanitized output in future iterations

### Error Messages

**Information Disclosure**:
- Error messages should not expose API internals
- Avoid showing full stack traces to users (log them instead)
- Generic error messages for authentication failures (don't reveal valid usernames)

### Network Security

**HTTPS Enforcement**:
- Always use HTTPS for Rally API (enforced by AsyncRallyClient)
- Certificate validation enabled by default
- No support for disabling SSL verification

## Future Enhancements

### Planned Features (Not in Scope for Initial Release)

1. **Ticket Creation**:
   - `rally-cli create [UserStory|Defect] --title "..." --description "..."`

2. **Ticket Updates**:
   - `rally-cli update US12345 --state "In-Progress" --points 5`

3. **Bulk Operations**:
   - `rally-cli bulk-update --query "..." --state "Completed"`

4. **Advanced Filtering**:
   - `rally-cli tickets --filter-file filters.yaml`

5. **Template Support**:
   - `rally-cli create --template user_story.yaml`

6. **Interactive Mode**:
   - `rally-cli interactive` - launches TUI from CLI

7. **Output Templates**:
   - `rally-cli tickets --template custom.jinja2`

8. **Caching**:
   - `rally-cli tickets --use-cache` - use local cache for faster queries

9. **Batch Comment**:
   - `rally-cli comment --batch tickets.txt comment.txt`

10. **Webhook Integration**:
    - `rally-cli watch --webhook https://...` - stream updates to webhook

### Extension Points

**Plugin System**:
- Design CLI with extension points for custom commands
- Future: `rally-cli plugins install <plugin-name>`

**Custom Formatters**:
- Allow users to define custom output formats
- Future: `rally-cli tickets --format custom --template myformat.jinja2`

**Workflow Automation**:
- Support for workflow definitions (YAML-based state transitions)
- Future: `rally-cli workflow apply --file deploy.yaml`

## Success Metrics

### Adoption Metrics
- CLI command usage (tracked via logs if users opt-in)
- Number of GitHub issues/questions about CLI vs TUI
- Community feedback and feature requests

### Performance Metrics
- CLI response time < 2 seconds for typical queries (10-50 tickets)
- CLI response time < 5 seconds for large queries (100+ tickets)
- Memory usage < 100MB for typical operations

### Quality Metrics
- Test coverage ≥ 90% for CLI code
- Zero critical bugs in first 30 days post-release
- Documentation completeness: all commands and options documented

## Rollout Plan

### Version Planning

**v0.9.0 - CLI Preview**:
- Basic CLI functionality (tickets query, comment)
- Alpha quality - for early adopters
- Documented as "experimental"

**v1.0.0 - CLI Stable**:
- Production-ready CLI
- Full documentation
- Comprehensive test coverage
- Stable API (semantic versioning from this point)

### Communication Plan

1. **Announcement**: Blog post and README update announcing CLI functionality
2. **Documentation**: Complete CLI guide in docs/
3. **Examples**: Sample scripts and use cases
4. **Feedback**: GitHub Discussions for user feedback
5. **Migration**: Guide for users who want CLI-first workflow

---

## Appendix A: Technology Choices

### Click CLI Framework

**Why Click?**
- Industry standard for Python CLIs (used by Flask, Pytest, etc.)
- Excellent documentation and community support
- Powerful argument parsing and validation
- Built-in help text generation
- Command groups for extensibility
- Testing utilities for CLI testing

**Alternatives Considered**:
- `argparse` (stdlib) - More verbose, less feature-rich
- `typer` - Newer, less mature, similar capabilities
- `fire` - Too magical, harder to customize

### AsyncRallyClient vs RallyClient

**Decision**: Use AsyncRallyClient exclusively in CLI

**Rationale**:
- AsyncRallyClient is the modern, better-tested implementation
- CLI can run async code via `asyncio.run()`
- Better performance for concurrent operations (future enhancement)
- Consistent with TUI's async architecture

### Output Format Choices

**Text Format**:
- Human-readable tabular output
- Uses Python `texttable` or custom formatting
- Default format for interactive use

**JSON Format**:
- Machine-parseable
- Standard for API responses
- Easy integration with jq, Python scripts, etc.

**CSV Format**:
- Spreadsheet import
- Data analysis workflows
- Simple columnar format

**Future Formats**:
- YAML - configuration-friendly
- Markdown - documentation-friendly
- XML - enterprise integration (if requested)

---

## Appendix B: Example Workflows

### Daily Standup Report
```bash
#!/bin/bash
# Generate daily standup report for current user

echo "My tickets in current iteration:"
rally-cli tickets --current-iteration --my-tickets --format text

echo "\nRecent activity:"
rally-cli tickets --current-iteration --my-tickets --format json | \
  jq -r '.data[] | select(.state == "In-Progress") | .formatted_id + ": " + .name'
```

### Automated Deployment Comment
```bash
#!/bin/bash
# Post deployment comment after successful deploy

TICKET_ID="US12345"
DEPLOY_ENV="production"
DEPLOY_TIME=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

rally-cli comment "$TICKET_ID" \
  "Deployed to $DEPLOY_ENV at $DEPLOY_TIME" \
  --format json > deploy-comment.json

if [ $? -eq 0 ]; then
  echo "✓ Deployment comment posted to $TICKET_ID"
else
  echo "✗ Failed to post deployment comment"
  exit 1
fi
```

### Team Velocity Report
```bash
#!/bin/bash
# Generate team velocity report for last 3 iterations

for iteration in "Sprint 2024.01" "Sprint 2024.02" "Sprint 2024.03"; do
  echo "=== $iteration ==="
  rally-cli tickets --iteration "$iteration" --format csv | \
    awk -F, '{sum+=$6} END {print "Total Points: " sum}'
done
```

### Ticket Status Export
```bash
#!/bin/bash
# Export all current iteration tickets to CSV for reporting

OUTPUT_FILE="tickets-$(date +%Y-%m-%d).csv"

rally-cli tickets --current-iteration --format csv > "$OUTPUT_FILE"

echo "✓ Exported tickets to $OUTPUT_FILE"

# Optional: Upload to cloud storage
# aws s3 cp "$OUTPUT_FILE" s3://reports/rally/
```

---

## Appendix C: Error Handling Patterns

### Error Categories

**1. Configuration Errors** (Exit Code: 4)
```python
# Missing API key
Error: RALLY_APIKEY environment variable not set
Help: Set RALLY_APIKEY or use --apikey flag

# Invalid server
Error: Cannot connect to Rally server: invalid.server.com
Help: Verify --server option or RALLY_SERVER environment variable
```

**2. Authentication Errors** (Exit Code: 3)
```python
# Invalid API key
Error: Authentication failed: Invalid API key
Help: Verify your RALLY_APIKEY is correct

# Insufficient permissions
Error: Permission denied: User does not have access to project
Help: Verify RALLY_PROJECT setting and user permissions
```

**3. Resource Errors** (Exit Code: 1)
```python
# Ticket not found
Error: Ticket US99999 not found
Help: Verify ticket ID and try again

# No results
Warning: No tickets found matching query
(Exit code 0 - not an error, just empty result)
```

**4. Network Errors** (Exit Code: 1)
```python
# Connection timeout
Error: Connection timeout connecting to Rally API
Help: Check network connection and try again

# API error
Error: Rally API error: 500 Internal Server Error
Help: Rally service may be experiencing issues, try again later
```

**5. Input Errors** (Exit Code: 2)
```python
# Invalid arguments
Error: Invalid ticket ID format: XYZ123
Help: Ticket ID must start with US, DE, TA, or TC

# Missing required argument
Error: Missing required argument: TICKET_ID
Usage: rally-cli comment <TICKET_ID> <MESSAGE>
```

### Error Output Format

**Text Format** (default):
```
Error: Ticket US99999 not found
Help: Verify ticket ID and try again
```

**JSON Format** (for scripting):
```json
{
  "success": false,
  "data": null,
  "error": "Ticket US99999 not found"
}
```

---

## Appendix D: Configuration Reference

### Environment Variables

```bash
# Required
export RALLY_APIKEY="your_api_key_here"

# Optional (with defaults)
export RALLY_SERVER="rally1.rallydev.com"       # Rally server hostname
export RALLY_WORKSPACE="Your Workspace"          # Workspace name
export RALLY_PROJECT="Your Project"              # Project name
```

### Configuration File

Future enhancement: Support for `~/.rally-cli/config.yaml`

```yaml
# Example configuration file (not implemented in initial release)
server: rally1.rallydev.com
apikey: ${RALLY_APIKEY}  # Reference env var
workspace: Engineering
project: Platform Team
default_output_format: json
default_fields:
  - formatted_id
  - name
  - state
  - owner
  - points
```

### Command-Line Options Priority

Priority order (highest to lowest):
1. Command-line flags (--server, --apikey, etc.)
2. Environment variables (RALLY_SERVER, RALLY_APIKEY, etc.)
3. Configuration file (future enhancement)
4. Built-in defaults

---

## Appendix E: Development Checklist

### Pre-Implementation Checklist
- [x] Review existing codebase architecture
- [x] Identify reusable components (models, services, config)
- [x] Define CLI command structure
- [x] Design output formats
- [x] Plan testing strategy

### Implementation Checklist
- [ ] Phase 1: Project Setup and Foundation (4-6 hours)
- [ ] Phase 2: Tickets Query Command (8-10 hours)
- [ ] Phase 3: Comment Command (4-6 hours)
- [ ] Phase 4: Documentation and Examples (4-6 hours)
- [ ] Phase 5: Testing and Quality Assurance (6-8 hours)

### Post-Implementation Checklist
- [ ] All tests passing (unit, integration, manual QA)
- [ ] Documentation complete and reviewed
- [ ] Code review completed
- [ ] Example scripts tested
- [ ] README.md updated
- [ ] Release notes drafted
- [ ] Version bumped in pyproject.toml
- [ ] Git tag created for release

### Total Estimated Effort
- **Development**: 26-36 hours
- **Testing**: 6-8 hours
- **Documentation**: 4-6 hours
- **Review & Release**: 2-4 hours
- **Total**: 38-54 hours (~1-1.5 weeks for single developer)

---

**Document Version**: 1.0
**Date**: 2024-01-25
**Author**: Principal Software Architect
**Status**: DRAFT - Ready for Implementation
