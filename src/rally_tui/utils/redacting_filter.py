"""Log redaction filter for sensitive data.

This module provides a logging filter that redacts sensitive information
from log messages before they are written to log files.
"""

from __future__ import annotations

import logging
import re
from typing import ClassVar


class RedactingFilter(logging.Filter):
    """Filter that redacts sensitive data from log messages.

    This filter intercepts log records and applies regex patterns to redact
    sensitive information like API keys, credentials, emails, and PII.

    Attributes:
        enabled: Whether redaction is active. When False, logs pass through unchanged.

    Example:
        >>> filter = RedactingFilter(enabled=True)
        >>> filter._redact("apikey=_abc123xyz")
        'apikey=[REDACTED]'
    """

    # Patterns are ordered from most specific to least specific
    # Each tuple: (name, replacement_text, compiled_regex)
    PATTERNS: ClassVar[list[tuple[str, str, re.Pattern[str]]]] = [
        # API credentials (most important to redact)
        (
            "api_key",
            "apikey=[REDACTED]",
            re.compile(r"apikey[=:]\s*[\"']?[\w\-_]+", re.IGNORECASE),
        ),
        (
            "zsessionid",
            "ZSESSIONID: [REDACTED]",
            re.compile(r"zsessionid[=:]\s*[\"']?[\w\-_]+", re.IGNORECASE),
        ),
        (
            "bearer",
            "Bearer [REDACTED]",
            re.compile(r"bearer\s+[\w\-_.]+", re.IGNORECASE),
        ),
        # Rally query parameters (contains user/project info)
        # More specific patterns first
        (
            "owner_display_name",
            'Owner.DisplayName = "[REDACTED]"',
            re.compile(r'Owner\.DisplayName\s*=\s*"[^"]+"', re.IGNORECASE),
        ),
        (
            "owner_display_name_neq",
            'Owner.DisplayName != "[REDACTED]"',
            re.compile(r'Owner\.DisplayName\s*!=\s*"[^"]+"', re.IGNORECASE),
        ),
        (
            "display_name",
            'DisplayName = "[REDACTED]"',
            re.compile(r'DisplayName\s*=\s*"[^"]+"', re.IGNORECASE),
        ),
        (
            "project_name",
            'Project.Name = "[REDACTED]"',
            re.compile(r'Project\.Name\s*=\s*"[^"]+"', re.IGNORECASE),
        ),
        (
            "iteration_name",
            'Iteration.Name = "[REDACTED]"',
            re.compile(r'Iteration\.Name\s*=\s*"[^"]+"', re.IGNORECASE),
        ),
        # Generic credentials
        (
            "password",
            "password=[REDACTED]",
            re.compile(r"password[=:]\s*[\"']?[^\s\"']+", re.IGNORECASE),
        ),
        (
            "secret",
            "secret=[REDACTED]",
            re.compile(r"secret[=:]\s*[\"']?[^\s\"']+", re.IGNORECASE),
        ),
        (
            "token",
            "token=[REDACTED]",
            re.compile(r"token[=:]\s*[\"']?[\w\-_.]+", re.IGNORECASE),
        ),
        # URL credentials (user:pass@host)
        (
            "url_creds",
            "://[REDACTED]@",
            re.compile(r"://[^:]+:[^@]+@"),
        ),
        # PII - email addresses
        (
            "email",
            "[EMAIL]",
            re.compile(r"[\w\.-]+@[\w\.-]+\.\w{2,}"),
        ),
    ]

    def __init__(self, enabled: bool = True) -> None:
        """Initialize the redacting filter.

        Args:
            enabled: Whether redaction is active. Defaults to True.
        """
        super().__init__()
        self.enabled = enabled

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and redact sensitive data from log record.

        Args:
            record: The log record to process.

        Returns:
            True always - the record is allowed through after redaction.
        """
        if self.enabled:
            # Redact main message
            record.msg = self._redact(str(record.msg))

            # Redact string arguments
            if record.args:
                record.args = tuple(
                    self._redact(str(arg)) if isinstance(arg, str) else arg for arg in record.args
                )

            # Redact exception info if present
            if record.exc_text:
                record.exc_text = self._redact(record.exc_text)

        return True  # Always allow the record through

    def _redact(self, message: str) -> str:
        """Apply all redaction patterns to a message.

        Args:
            message: The message to redact.

        Returns:
            The message with sensitive data replaced by redaction placeholders.
        """
        for _name, replacement, pattern in self.PATTERNS:
            message = pattern.sub(replacement, message)
        return message
