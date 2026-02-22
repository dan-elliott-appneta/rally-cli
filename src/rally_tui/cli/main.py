"""CLI entry point for Rally command-line interface.

This module provides the main CLI application using Click.
"""

import logging

import click

from rally_tui.cli.formatters import CSVFormatter, JSONFormatter, OutputFormat, TextFormatter
from rally_tui.cli.formatters.base import BaseFormatter
from rally_tui.utils.redacting_filter import RedactingFilter

# Version from package
try:
    from importlib.metadata import version

    __version__ = version("rally-tui")
except Exception:
    __version__ = "0.0.0"


class CLIContext:
    """Context object passed to all CLI commands."""

    def __init__(
        self,
        server: str,
        apikey: str,
        workspace: str,
        project: str,
        output_format: OutputFormat,
        verbose: bool,
    ):
        self.server = server
        self.apikey = apikey
        self.workspace = workspace
        self.project = project
        self.output_format = output_format
        self.verbose = verbose
        self._formatter: BaseFormatter | None = None

    def set_format(self, fmt: OutputFormat) -> None:
        """Set the output format and reset the cached formatter.

        This is the public API for changing the output format after
        construction. It resets the internal formatter cache so the
        next access to ``formatter`` builds the correct instance.

        Args:
            fmt: The new output format.
        """
        self.output_format = fmt
        self._formatter = None

    @property
    def formatter(self) -> BaseFormatter:
        """Get the appropriate formatter based on output format."""
        if self._formatter is None:
            if self.output_format == OutputFormat.JSON:
                self._formatter = JSONFormatter()
            elif self.output_format == OutputFormat.CSV:
                self._formatter = CSVFormatter()
            else:
                self._formatter = TextFormatter()
        return self._formatter


pass_context = click.make_pass_decorator(CLIContext, ensure=True)


def _configure_logging(verbose: bool) -> None:
    """Configure logging with redacting filter.

    Args:
        verbose: If True, set DEBUG level; otherwise WARNING level.
    """
    logger = logging.getLogger("rally_tui")
    logger.setLevel(logging.DEBUG if verbose else logging.WARNING)

    handler = logging.StreamHandler()
    handler.addFilter(RedactingFilter())
    logger.addHandler(handler)


@click.group()
@click.option(
    "--server",
    envvar="RALLY_SERVER",
    default="rally1.rallydev.com",
    help="Rally server hostname.",
)
@click.option(
    "--apikey",
    envvar="RALLY_APIKEY",
    default="",
    help="Rally API key (or use RALLY_APIKEY env var).",
)
@click.option(
    "--workspace",
    envvar="RALLY_WORKSPACE",
    default="",
    help="Workspace name (or use RALLY_WORKSPACE env var).",
)
@click.option(
    "--project",
    envvar="RALLY_PROJECT",
    default="",
    help="Project name (or use RALLY_PROJECT env var).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default="text",
    help="Output format.",
)
@click.option(
    "--verbose/--quiet",
    "-v/-q",
    default=False,
    help="Enable/disable verbose logging.",
)
@click.version_option(version=__version__, prog_name="rally-cli")
@click.pass_context
def cli(
    ctx: click.Context,
    server: str,
    apikey: str,
    workspace: str,
    project: str,
    output_format: str,
    verbose: bool,
) -> None:
    """Rally CLI - Command-line interface for Rally work item management.

    Query tickets and add comments to Rally items directly from the command line.
    Configure via environment variables (RALLY_APIKEY, RALLY_WORKSPACE, RALLY_PROJECT)
    or command-line options.

    Examples:

    \b
        # Show my tickets in current iteration
        rally-cli tickets --current-iteration --my-tickets

    \b
        # Add a comment to a ticket
        rally-cli comment US12345 "Updated the implementation"

    \b
        # Export tickets to JSON
        rally-cli tickets --current-iteration --format json

    \b
        # Create a new ticket
        rally-cli tickets create "My Story" --description "Brief description" --points 1
    """
    # Configure logging based on verbose flag
    _configure_logging(verbose)

    ctx.obj = CLIContext(
        server=server,
        apikey=apikey,
        workspace=workspace,
        project=project,
        output_format=OutputFormat(output_format.lower()),
        verbose=verbose,
    )


# Import and register commands
# These are imported here to avoid circular imports
from rally_tui.cli.commands import (  # noqa: E402, F401
    comment,
    discussions,
    iterations,
    query,
    releases,
    tags,
    users,
)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
