"""Tests for the log redacting filter."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest

from rally_tui.utils.redacting_filter import RedactingFilter

if TYPE_CHECKING:
    pass


class TestRedactingFilterBasic:
    """Basic tests for RedactingFilter initialization and state."""

    def test_filter_enabled_by_default(self) -> None:
        """Filter should be enabled by default."""
        filter = RedactingFilter()
        assert filter.enabled is True

    def test_filter_can_be_disabled(self) -> None:
        """Filter can be disabled via constructor."""
        filter = RedactingFilter(enabled=False)
        assert filter.enabled is False

    def test_filter_always_returns_true(self) -> None:
        """Filter should always return True (allow record through)."""
        filter = RedactingFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )
        assert filter.filter(record) is True

    def test_disabled_filter_passes_through_unchanged(self) -> None:
        """Disabled filter should not modify messages."""
        filter = RedactingFilter(enabled=False)
        msg = "apikey=_secret123"
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=msg,
            args=(),
            exc_info=None,
        )
        filter.filter(record)
        assert record.msg == msg


class TestRedactAPICredentials:
    """Tests for API credential redaction patterns."""

    @pytest.fixture
    def filter(self) -> RedactingFilter:
        return RedactingFilter(enabled=True)

    def test_redacts_apikey_equals(self, filter: RedactingFilter) -> None:
        """Redacts apikey=value pattern."""
        result = filter._redact("apikey=_abc123xyz")
        assert "[REDACTED]" in result
        assert "_abc123xyz" not in result

    def test_redacts_apikey_colon(self, filter: RedactingFilter) -> None:
        """Redacts apikey:value pattern."""
        result = filter._redact("apikey: _abc123xyz")
        assert "[REDACTED]" in result
        assert "_abc123xyz" not in result

    def test_redacts_apikey_quoted(self, filter: RedactingFilter) -> None:
        """Redacts apikey='value' pattern."""
        result = filter._redact("apikey='_abc123xyz'")
        assert "[REDACTED]" in result
        assert "_abc123xyz" not in result

    def test_redacts_apikey_case_insensitive(self, filter: RedactingFilter) -> None:
        """Redacts APIKEY regardless of case."""
        result = filter._redact("APIKEY=_abc123xyz")
        assert "[REDACTED]" in result
        assert "_abc123xyz" not in result

    def test_redacts_zsessionid(self, filter: RedactingFilter) -> None:
        """Redacts ZSESSIONID header pattern."""
        result = filter._redact("ZSESSIONID: _abc123xyz")
        assert "[REDACTED]" in result
        assert "_abc123xyz" not in result

    def test_redacts_bearer_token(self, filter: RedactingFilter) -> None:
        """Redacts Bearer token pattern."""
        result = filter._redact("Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
        assert "[REDACTED]" in result
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result


class TestRedactRallyQueries:
    """Tests for Rally query parameter redaction."""

    @pytest.fixture
    def filter(self) -> RedactingFilter:
        return RedactingFilter(enabled=True)

    def test_redacts_owner_display_name(self, filter: RedactingFilter) -> None:
        """Redacts Owner.DisplayName in queries."""
        query = '(Owner.DisplayName = "John Doe")'
        result = filter._redact(query)
        assert "[REDACTED]" in result
        assert "John Doe" not in result

    def test_redacts_owner_display_name_not_equals(self, filter: RedactingFilter) -> None:
        """Redacts Owner.DisplayName != in queries."""
        query = '(Owner.DisplayName != "Jira Migration")'
        result = filter._redact(query)
        assert "[REDACTED]" in result
        assert "Jira Migration" not in result

    def test_redacts_display_name(self, filter: RedactingFilter) -> None:
        """Redacts DisplayName in queries."""
        query = '(DisplayName = "Jane Smith")'
        result = filter._redact(query)
        assert "[REDACTED]" in result
        assert "Jane Smith" not in result

    def test_redacts_project_name(self, filter: RedactingFilter) -> None:
        """Redacts Project.Name in queries."""
        query = '(Project.Name = "Secret Project")'
        result = filter._redact(query)
        assert "[REDACTED]" in result
        assert "Secret Project" not in result

    def test_redacts_iteration_name(self, filter: RedactingFilter) -> None:
        """Redacts Iteration.Name in queries."""
        query = '(Iteration.Name = "Sprint 5")'
        result = filter._redact(query)
        assert "[REDACTED]" in result
        assert "Sprint 5" not in result

    def test_redacts_complex_query(self, filter: RedactingFilter) -> None:
        """Redacts multiple patterns in complex query."""
        query = '((Project.Name = "My Project") AND (Owner.DisplayName = "John Doe"))'
        result = filter._redact(query)
        assert "My Project" not in result
        assert "John Doe" not in result
        assert result.count("[REDACTED]") == 2


class TestRedactGenericCredentials:
    """Tests for generic credential redaction."""

    @pytest.fixture
    def filter(self) -> RedactingFilter:
        return RedactingFilter(enabled=True)

    def test_redacts_password(self, filter: RedactingFilter) -> None:
        """Redacts password=value pattern."""
        result = filter._redact("password=secretpass123")
        assert "[REDACTED]" in result
        assert "secretpass123" not in result

    def test_redacts_secret(self, filter: RedactingFilter) -> None:
        """Redacts secret=value pattern."""
        result = filter._redact("secret=mysecretvalue")
        assert "[REDACTED]" in result
        assert "mysecretvalue" not in result

    def test_redacts_token(self, filter: RedactingFilter) -> None:
        """Redacts token=value pattern."""
        result = filter._redact("token=abc123def456")
        assert "[REDACTED]" in result
        assert "abc123def456" not in result

    def test_redacts_url_credentials(self, filter: RedactingFilter) -> None:
        """Redacts credentials in URLs."""
        result = filter._redact("https://user:password@example.com/api")
        assert "[REDACTED]" in result
        assert "user:password" not in result
        assert "example.com/api" in result  # Host and path preserved


class TestRedactPII:
    """Tests for PII (email) redaction."""

    @pytest.fixture
    def filter(self) -> RedactingFilter:
        return RedactingFilter(enabled=True)

    def test_redacts_email(self, filter: RedactingFilter) -> None:
        """Redacts email addresses."""
        result = filter._redact("Contact: user@example.com")
        assert "[EMAIL]" in result
        assert "user@example.com" not in result

    def test_redacts_email_in_text(self, filter: RedactingFilter) -> None:
        """Redacts email embedded in other text."""
        result = filter._redact("User john.doe@company.org logged in")
        assert "[EMAIL]" in result
        assert "john.doe@company.org" not in result

    def test_preserves_non_email_at_signs(self, filter: RedactingFilter) -> None:
        """Does not redact @-mentions or other non-email uses."""
        result = filter._redact("Invalid email: user@")
        # Should not match incomplete email
        assert "@" in result


class TestRedactLogRecords:
    """Tests for full log record redaction."""

    @pytest.fixture
    def filter(self) -> RedactingFilter:
        return RedactingFilter(enabled=True)

    def test_redacts_log_message(self, filter: RedactingFilter) -> None:
        """Redacts sensitive data in log message."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Connecting with apikey=_secret123",
            args=(),
            exc_info=None,
        )
        filter.filter(record)
        assert "[REDACTED]" in record.msg
        assert "_secret123" not in record.msg

    def test_redacts_log_args(self, filter: RedactingFilter) -> None:
        """Redacts sensitive data in log arguments."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Query: %s",
            args=('(Owner.DisplayName = "John Doe")',),
            exc_info=None,
        )
        filter.filter(record)
        assert record.args is not None
        assert "[REDACTED]" in record.args[0]
        assert "John Doe" not in record.args[0]

    def test_redacts_exception_text(self, filter: RedactingFilter) -> None:
        """Redacts sensitive data in exception text."""
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Error occurred",
            args=(),
            exc_info=None,
        )
        record.exc_text = "Traceback: apikey=_secret123 in config"
        filter.filter(record)
        assert record.exc_text is not None
        assert "[REDACTED]" in record.exc_text
        assert "_secret123" not in record.exc_text

    def test_handles_none_args(self, filter: RedactingFilter) -> None:
        """Handles None args gracefully."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Simple message",
            args=None,  # type: ignore[arg-type]
            exc_info=None,
        )
        # Should not raise
        filter.filter(record)
        assert record.msg == "Simple message"

    def test_handles_non_string_args(self, filter: RedactingFilter) -> None:
        """Handles non-string args gracefully."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Count: %d, Name: %s",
            args=(42, "apikey=_secret123"),
            exc_info=None,
        )
        filter.filter(record)
        assert record.args is not None
        assert record.args[0] == 42  # Number unchanged
        assert "[REDACTED]" in record.args[1]  # String redacted


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture
    def filter(self) -> RedactingFilter:
        return RedactingFilter(enabled=True)

    def test_empty_message(self, filter: RedactingFilter) -> None:
        """Handles empty message."""
        result = filter._redact("")
        assert result == ""

    def test_no_sensitive_data(self, filter: RedactingFilter) -> None:
        """Preserves message with no sensitive data."""
        msg = "Normal log message without sensitive info"
        result = filter._redact(msg)
        assert result == msg

    def test_multiple_patterns_same_message(self, filter: RedactingFilter) -> None:
        """Handles multiple sensitive items in one message."""
        msg = "User user@example.com set apikey=_secret123"
        result = filter._redact(msg)
        assert "[EMAIL]" in result
        assert "[REDACTED]" in result
        assert "user@example.com" not in result
        assert "_secret123" not in result

    def test_partial_pattern_not_matched(self, filter: RedactingFilter) -> None:
        """Does not match incomplete patterns."""
        msg = "apikey without value"
        result = filter._redact(msg)
        # Should not be changed since there's no value after apikey
        assert "apikey" in result

    def test_preserves_surrounding_text(self, filter: RedactingFilter) -> None:
        """Preserves text around redacted content."""
        msg = "Before apikey=_secret123 After"
        result = filter._redact(msg)
        assert result.startswith("Before")
        assert result.endswith("After")
