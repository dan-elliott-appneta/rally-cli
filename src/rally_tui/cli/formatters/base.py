"""Base formatter interface for CLI output."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class OutputFormat(StrEnum):
    """Supported output formats."""

    TEXT = "text"
    JSON = "json"
    CSV = "csv"


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
            "error": self.error,
        }


class BaseFormatter(ABC):
    """Abstract base class for output formatters."""

    @abstractmethod
    def format_tickets(self, result: CLIResult, fields: list[str] | None = None) -> str:
        """Format ticket list output.

        Args:
            result: CLIResult containing ticket data.
            fields: Optional list of fields to include.

        Returns:
            Formatted string output.
        """
        pass

    @abstractmethod
    def format_comment(self, result: CLIResult) -> str:
        """Format comment confirmation output.

        Args:
            result: CLIResult containing comment data.

        Returns:
            Formatted string output.
        """
        pass

    @abstractmethod
    def format_error(self, result: CLIResult) -> str:
        """Format error output.

        Args:
            result: CLIResult containing error information.

        Returns:
            Formatted string output.
        """
        pass

    @abstractmethod
    def format_ticket_detail(self, result: CLIResult) -> str:
        """Format single ticket detail output for the show command.

        Args:
            result: CLIResult containing a single ticket.

        Returns:
            Formatted string output with full ticket details.
        """
        pass

    @abstractmethod
    def format_update_result(self, result: CLIResult) -> str:
        """Format ticket update result for the update command.

        Args:
            result: CLIResult containing the updated ticket and change summary.

        Returns:
            Formatted string output summarising what changed.
        """
        pass

    @abstractmethod
    def format_delete_result(self, result: CLIResult) -> str:
        """Format ticket delete result for the delete command.

        Args:
            result: CLIResult containing deletion confirmation data.

        Returns:
            Formatted string output confirming deletion.
        """
        pass

    @abstractmethod
    def format_discussions(self, result: CLIResult) -> str:
        """Format discussion list output.

        Args:
            result: CLIResult containing discussion data. The data field
                should contain a dict with 'discussions' (list[Discussion]),
                'formatted_id' (str), and 'count' (int).

        Returns:
            Formatted string output.
        """
        pass

    @abstractmethod
    def format_iterations(self, result: CLIResult) -> str:
        """Format iteration list output.

        Args:
            result: CLIResult containing iteration data. The data field
                should contain a list of Iteration objects.

        Returns:
            Formatted string output.
        """
        pass

    @abstractmethod
    def format_users(self, result: CLIResult) -> str:
        """Format user list output.

        Args:
            result: CLIResult containing user data. The data field
                should contain a list of Owner objects.

        Returns:
            Formatted string output.
        """
        pass
