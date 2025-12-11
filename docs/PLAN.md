# Rally CLI - Project Plan

## Overview

A Python command-line interface for interacting with Rally (Broadcom) via the WSAPI.

## Goals

- Provide a simple CLI for common Rally operations
- Support querying, creating, updating, and viewing work items
- Enable scripting and automation workflows

## Planned Features

### Phase 1: Core Functionality

- [ ] Project setup (pyproject.toml, dependencies)
- [ ] Configuration management (API key, workspace, project)
- [ ] Basic authentication flow
- [ ] Query commands for artifacts (user stories, defects, tasks)
- [ ] View single item details by FormattedID

### Phase 2: CRUD Operations

- [ ] Create new artifacts
- [ ] Update existing artifacts
- [ ] Delete artifacts
- [ ] Bulk operations support

### Phase 3: Enhanced Features

- [ ] Interactive mode
- [ ] Output formatting (table, JSON, CSV)
- [ ] Filtering and sorting options
- [ ] Iteration/Release scoping
- [ ] Attachment handling

### Phase 4: Advanced

- [ ] Caching for improved performance
- [ ] Custom field support
- [ ] Templates for common operations
- [ ] Shell completions

## Technical Decisions

### Dependencies

- `pyral` - Rally REST API toolkit
- `click` or `typer` - CLI framework (TBD)
- `rich` - Terminal formatting (optional)

### Configuration

- Config file: `~/.rally-cli/config.yaml` or `~/.rally-cli.yaml`
- Environment variables: `RALLY_APIKEY`, `RALLY_WORKSPACE`, `RALLY_PROJECT`
- Command-line overrides

### Command Structure

```
rally [OPTIONS] COMMAND [ARGS]

Commands:
  config    Manage configuration
  query     Query artifacts
  show      Show artifact details
  create    Create new artifact
  update    Update artifact
  delete    Delete artifact
```

## Notes

- See `docs/API.md` for Rally WSAPI reference
