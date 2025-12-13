# Log Redaction Implementation Plan

## Overview

This document outlines the implementation plan for redacting sensitive data from rally-tui application logs. The goal is to prevent accidental exposure of PII, credentials, and other sensitive information in log files.

## Problem Statement

Application logs may contain sensitive information including:
- **API Keys**: Rally API keys in headers, config, or error messages
- **User Information**: Display names, email addresses, usernames
- **Credentials**: Passwords, tokens, session IDs
- **Business Data**: Project names, workspace names (may be confidential)
- **URLs**: May contain embedded credentials or API keys
- **Query Strings**: May contain user names, project filters

### Current Logging Locations

Logs are written to `~/.config/rally-tui/rally-tui.log` and include:
- Connection information (server, workspace, project, user)
- API queries (contain user/project/iteration filters)
- Ticket operations (IDs, sometimes content)
- Error messages (may include stack traces with sensitive data)

## Design Goals

1. **Centralized**: Single point of redaction for all log output
2. **Non-invasive**: Existing logging calls don't need modification
3. **Configurable**: Users can enable/disable and customize patterns
4. **Performant**: Minimal overhead on logging operations
5. **Testable**: Easy to unit test redaction logic
6. **Safe Defaults**: Redaction enabled by default with sensible patterns

## Technical Approach

### Architecture

```
Log Call → Logger → RedactingFilter → Formatter → Handler → File
                          ↑
                    Pattern Matching
                    & Replacement
```

### Implementation: Custom Logging Filter

Python's `logging.Filter` class allows inspection and modification of log records before they reach handlers. We'll create a `RedactingFilter` that:

1. Intercepts each log record
2. Applies regex patterns to the message
3. Replaces matches with redaction placeholders
4. Passes the modified record to handlers

### Redaction Patterns

| Category | Pattern | Example Input | Redacted Output |
|----------|---------|---------------|-----------------|
| API Key | `apikey[=:]["']?[\w\-_]+` | `apikey=_abc123xyz` | `apikey=[REDACTED]` |
| ZSESSIONID | `zsessionid[=:]["']?[\w\-_]+` | `ZSESSIONID: _key123` | `ZSESSIONID: [REDACTED]` |
| Bearer Token | `bearer\s+[\w\-_.]+` | `Bearer abc.def.ghi` | `Bearer [REDACTED]` |
| Password | `password[=:]["']?[^\s"']+` | `password=secret123` | `password=[REDACTED]` |
| Email | `[\w\.-]+@[\w\.-]+\.\w+` | `user@example.com` | `[EMAIL]` |
| Display Name in Query | `DisplayName\s*=\s*"[^"]+"\)` | `DisplayName = "John Doe")` | `DisplayName = "[REDACTED]")` |
| URL Credentials | `://[^:]+:[^@]+@` | `://user:pass@host` | `://[REDACTED]@` |

### Configuration

Add to `~/.config/rally-tui/config.json`:

```json
{
  "redact_logs": true,
  "redact_patterns": {
    "api_keys": true,
    "emails": true,
    "display_names": true,
    "urls": true
  }
}
```

## Implementation Steps

### Step 1: Create RedactingFilter Class

Create `src/rally_tui/utils/redacting_filter.py`:

```python
import logging
import re
from typing import ClassVar

class RedactingFilter(logging.Filter):
    """Filter that redacts sensitive data from log messages."""

    # Patterns are ordered from most specific to least specific
    # Each tuple: (name, replacement_text, compiled_regex)
    PATTERNS: ClassVar[list[tuple[str, str, re.Pattern[str]]]] = [
        # API credentials (most important)
        ("api_key", r"apikey=[REDACTED]", re.compile(r"apikey[=:]\s*[\"']?[\w\-_]+", re.I)),
        ("zsessionid", r"ZSESSIONID: [REDACTED]", re.compile(r"zsessionid[=:]\s*[\"']?[\w\-_]+", re.I)),
        ("bearer", r"Bearer [REDACTED]", re.compile(r"bearer\s+[\w\-_.]+", re.I)),

        # Rally query parameters (contains user/project info)
        ("display_name", r'DisplayName = "[REDACTED]"', re.compile(r'DisplayName\s*=\s*"[^"]+"', re.I)),
        ("owner_name", r'Owner.DisplayName = "[REDACTED]"', re.compile(r'Owner\.DisplayName\s*=\s*"[^"]+"', re.I)),
        ("project_name", r'Project.Name = "[REDACTED]"', re.compile(r'Project\.Name\s*=\s*"[^"]+"', re.I)),

        # Generic credentials
        ("password", r"password=[REDACTED]", re.compile(r"password[=:]\s*[\"']?[^\s\"']+", re.I)),
        ("url_creds", r"://[REDACTED]@", re.compile(r"://[^:]+:[^@]+@")),

        # PII
        ("email", r"[EMAIL]", re.compile(r"[\w\.-]+@[\w\.-]+\.\w{2,}")),
    ]

    def __init__(self, enabled: bool = True):
        super().__init__()
        self.enabled = enabled

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and redact sensitive data from log record."""
        if self.enabled:
            # Redact main message
            record.msg = self._redact(str(record.msg))

            # Redact string arguments
            if record.args:
                record.args = tuple(
                    self._redact(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )

            # Redact exception info if present
            if record.exc_text:
                record.exc_text = self._redact(record.exc_text)

        return True  # Always allow the record through

    def _redact(self, message: str) -> str:
        """Apply all redaction patterns to a message."""
        for name, replacement, pattern in self.PATTERNS:
            message = pattern.sub(replacement, message)
        return message
```

**Key Design Decisions:**
- Patterns are compiled once at class level (ClassVar) for performance
- Patterns are ordered from most specific to least specific
- The filter always returns True (allows all records through after redaction)
- Exception text is also redacted (stack traces may contain sensitive data)
- String arguments are individually redacted

### Step 2: Add Tests

Create `tests/test_redacting_filter.py`:

```python
def test_redacts_api_key():
    filter = RedactingFilter()
    assert "[REDACTED]" in filter._redact("apikey=_abc123")

def test_redacts_email():
    filter = RedactingFilter()
    assert "[EMAIL]" in filter._redact("user@example.com")

def test_disabled_filter_passes_through():
    filter = RedactingFilter(enabled=False)
    msg = "apikey=_abc123"
    assert filter._redact(msg) == msg  # No redaction when disabled
```

### Step 3: Integrate into Logging Setup

Modify `src/rally_tui/utils/logging.py`:

```python
from rally_tui.utils.redacting_filter import RedactingFilter

def setup_logging(settings: UserSettings | None = None) -> logging.Logger:
    # ... existing setup ...

    # Add redacting filter to all handlers
    redacting_filter = RedactingFilter(enabled=settings.redact_logs)
    for handler in logger.handlers:
        handler.addFilter(redacting_filter)
```

### Step 4: Add User Settings

Modify `src/rally_tui/user_settings.py`:

```python
class UserSettings:
    redact_logs: bool = True  # Default to enabled
```

### Step 5: Update Documentation

- Update README.md with redaction feature
- Update user settings documentation
- Add security considerations section

## Testing Strategy

### Unit Tests
- Test each redaction pattern individually
- Test pattern combinations
- Test edge cases (partial matches, no matches)
- Test disabled filter
- Test empty/None messages

### Integration Tests
- Test that setup_logging applies filter
- Test that logs are actually redacted in output
- Test runtime enable/disable

### Performance Tests
- Benchmark redaction overhead
- Test with high-volume logging

## Security Considerations

1. **Defense in Depth**: Redaction is a safety net, not a replacement for secure coding
2. **Pattern Updates**: Patterns should be reviewed and updated as new sensitive data types are identified
3. **Log Rotation**: Existing logs are not retroactively redacted
4. **Debug Mode**: Consider warning users when redaction is disabled

## Rollout Plan

1. Implement with redaction enabled by default
2. Add configuration option to disable (for debugging)
3. Document the feature in README
4. Consider adding a log message on startup indicating redaction status

## Future Enhancements

- Custom user-defined patterns
- Different redaction levels (minimal, standard, paranoid)
- Audit log of redaction events
- Integration with external secrets management
