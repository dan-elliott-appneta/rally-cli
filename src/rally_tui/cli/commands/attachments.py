"""Attachments command for managing Rally ticket attachments.

This module implements the 'attachments' command group for listing,
downloading, and uploading file attachments on Rally tickets.
"""

import asyncio
import os
import re
import sys

import click

from rally_tui.cli.formatters.base import CLIResult, OutputFormat
from rally_tui.cli.main import CLIContext, cli, pass_context
from rally_tui.config import RallyConfig
from rally_tui.services.async_rally_client import AsyncRallyClient

# Pattern matching valid Rally ticket IDs (case-insensitive)
_TICKET_ID_RE = re.compile(r"^(US|S|DE|TA|TC|F)\d+$", re.IGNORECASE)


def _validate_ticket_id(ticket_id: str) -> CLIResult | None:
    """Validate a ticket ID and return an error CLIResult if invalid.

    Args:
        ticket_id: The ticket ID to validate.

    Returns:
        CLIResult with error if invalid, None if valid.
    """
    if not _TICKET_ID_RE.match(ticket_id):
        return CLIResult(
            success=False,
            data=None,
            error=f"Invalid ticket ID format: {ticket_id}. "
            "Ticket ID must match pattern US/S/DE/TA/TC/F followed by digits.",
        )
    return None


def _check_apikey(ctx: CLIContext) -> CLIResult | None:
    """Check for API key and return error CLIResult if missing.

    Args:
        ctx: CLI context.

    Returns:
        CLIResult with error if missing, None if present.
    """
    if not ctx.apikey:
        return CLIResult(
            success=False,
            data=None,
            error="RALLY_APIKEY environment variable not set. "
            "Set RALLY_APIKEY or use --apikey flag.",
        )
    return None


@click.group("attachments", invoke_without_command=True)
@click.pass_context
def attachments(click_ctx: click.Context) -> None:
    """Manage Rally ticket attachments.

    Without a subcommand, shows help. Use subcommands to list, download,
    or upload attachments on tickets.

    Examples:

    \b
        rally-cli attachments list US12345
        rally-cli attachments download US12345 requirements.pdf
        rally-cli attachments upload US12345 ./screenshot.png
    """
    if click_ctx.invoked_subcommand is None:
        click.echo(click_ctx.get_help())


@attachments.command("list")
@click.argument("ticket_id")
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format (overrides global --format).",
)
@pass_context
def attachments_list(ctx: CLIContext, ticket_id: str, sub_format: str | None) -> None:
    """List attachments on a ticket.

    TICKET_ID is the formatted ID (e.g., US12345, DE67890).

    Examples:

    \b
        rally-cli attachments list US12345
        rally-cli attachments list US12345 --format json
    """
    if sub_format:
        ctx.set_format(OutputFormat(sub_format.lower()))

    error = _check_apikey(ctx)
    if error:
        click.echo(ctx.formatter.format_error(error), err=True)
        sys.exit(4)

    error = _validate_ticket_id(ticket_id)
    if error:
        click.echo(ctx.formatter.format_error(error), err=True)
        sys.exit(2)

    result = asyncio.run(_fetch_attachments(ctx, ticket_id))

    if result.success:
        output = ctx.formatter.format_attachments(result)
        click.echo(output)
        sys.exit(0)
    else:
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


@attachments.command("download")
@click.argument("ticket_id")
@click.argument("filename", required=False, default=None)
@click.option(
    "--output",
    "output_path",
    type=click.Path(),
    default=None,
    help="Output file path.",
)
@click.option(
    "--all",
    "download_all",
    is_flag=True,
    default=False,
    help="Download all attachments.",
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default=None,
    help="Output directory for --all downloads.",
)
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@pass_context
def attachments_download(
    ctx: CLIContext,
    ticket_id: str,
    filename: str | None,
    output_path: str | None,
    download_all: bool,
    output_dir: str | None,
    sub_format: str | None,
) -> None:
    """Download attachment(s) from a ticket.

    TICKET_ID is the formatted ID (e.g., US12345, DE67890).
    FILENAME is the name of the attachment to download.

    Use --all to download all attachments at once.

    Examples:

    \b
        rally-cli attachments download US12345 requirements.pdf
        rally-cli attachments download US12345 requirements.pdf --output /tmp/req.pdf
        rally-cli attachments download US12345 --all --output-dir ./attachments/
    """
    if sub_format:
        ctx.set_format(OutputFormat(sub_format.lower()))

    error = _check_apikey(ctx)
    if error:
        click.echo(ctx.formatter.format_error(error), err=True)
        sys.exit(4)

    error = _validate_ticket_id(ticket_id)
    if error:
        click.echo(ctx.formatter.format_error(error), err=True)
        sys.exit(2)

    if not download_all and not filename:
        result = CLIResult(
            success=False,
            data=None,
            error="Provide a FILENAME to download, or use --all to download all attachments.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(2)

    if download_all:
        result = asyncio.run(_download_all_attachments(ctx, ticket_id, output_dir))
    else:
        assert filename is not None
        result = asyncio.run(_download_single_attachment(ctx, ticket_id, filename, output_path))

    if result.success:
        output = ctx.formatter.format_attachment_action(result)
        click.echo(output)
        sys.exit(0)
    else:
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


@attachments.command("upload")
@click.argument("ticket_id")
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@pass_context
def attachments_upload(
    ctx: CLIContext,
    ticket_id: str,
    file_path: str,
    sub_format: str | None,
) -> None:
    """Upload a file as an attachment to a ticket.

    TICKET_ID is the formatted ID (e.g., US12345, DE67890).
    FILE_PATH is the local path to the file to upload.

    Examples:

    \b
        rally-cli attachments upload US12345 ./screenshot.png
        rally-cli attachments upload US12345 ./screenshot.png --format json
    """
    if sub_format:
        ctx.set_format(OutputFormat(sub_format.lower()))

    error = _check_apikey(ctx)
    if error:
        click.echo(ctx.formatter.format_error(error), err=True)
        sys.exit(4)

    error = _validate_ticket_id(ticket_id)
    if error:
        click.echo(ctx.formatter.format_error(error), err=True)
        sys.exit(2)

    result = asyncio.run(_upload_attachment(ctx, ticket_id, file_path))

    if result.success:
        output = ctx.formatter.format_attachment_action(result)
        click.echo(output)
        sys.exit(0)
    else:
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


async def _fetch_attachments(ctx: CLIContext, ticket_id: str) -> CLIResult:
    """Fetch attachments for a ticket.

    Args:
        ctx: CLI context.
        ticket_id: The ticket's formatted ID.

    Returns:
        CLIResult with attachment data or error.
    """
    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    try:
        async with AsyncRallyClient(config) as client:
            ticket = await client.get_ticket(ticket_id)
            if not ticket:
                return CLIResult(
                    success=False,
                    data=None,
                    error=f"Ticket {ticket_id} not found.",
                )
            attachment_list = await client.get_attachments(ticket)
            return CLIResult(
                success=True,
                data={
                    "formatted_id": ticket_id,
                    "attachments": attachment_list,
                    "count": len(attachment_list),
                },
            )
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            return CLIResult(
                success=False,
                data=None,
                error="Authentication failed: Invalid API key",
            )
        return CLIResult(
            success=False,
            data=None,
            error=f"Failed to fetch attachments: {error_msg}",
        )


async def _download_single_attachment(
    ctx: CLIContext,
    ticket_id: str,
    filename: str,
    output_path: str | None,
) -> CLIResult:
    """Download a single attachment from a ticket.

    Args:
        ctx: CLI context.
        ticket_id: The ticket's formatted ID.
        filename: Name of the attachment to download.
        output_path: Optional path to save the file.

    Returns:
        CLIResult with download result or error.
    """
    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    try:
        async with AsyncRallyClient(config) as client:
            ticket = await client.get_ticket(ticket_id)
            if not ticket:
                return CLIResult(success=False, data=None, error=f"Ticket {ticket_id} not found.")

            attachments_list = await client.get_attachments(ticket)
            target = next((a for a in attachments_list if a.name == filename), None)
            if not target:
                return CLIResult(
                    success=False,
                    data=None,
                    error=f"Attachment '{filename}' not found on {ticket_id}.",
                )

            dest = output_path or filename
            success = await client.download_attachment(ticket, target, dest)
            if success:
                return CLIResult(
                    success=True,
                    data={
                        "ticket_id": ticket_id,
                        "filename": filename,
                        "dest": dest,
                        "action": "downloaded",
                    },
                )
            else:
                return CLIResult(
                    success=False,
                    data=None,
                    error=f"Failed to download attachment '{filename}'.",
                )

    except Exception as e:
        error_msg = str(e)
        return CLIResult(
            success=False,
            data=None,
            error=f"Failed to download attachment: {error_msg}",
        )


async def _download_all_attachments(
    ctx: CLIContext,
    ticket_id: str,
    output_dir: str | None,
) -> CLIResult:
    """Download all attachments from a ticket.

    Args:
        ctx: CLI context.
        ticket_id: The ticket's formatted ID.
        output_dir: Optional directory to save files to.

    Returns:
        CLIResult with download result or error.
    """
    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    dest_dir = output_dir or "."
    os.makedirs(dest_dir, exist_ok=True)

    try:
        async with AsyncRallyClient(config) as client:
            ticket = await client.get_ticket(ticket_id)
            if not ticket:
                return CLIResult(success=False, data=None, error=f"Ticket {ticket_id} not found.")

            attachments_list = await client.get_attachments(ticket)
            if not attachments_list:
                return CLIResult(
                    success=True,
                    data={
                        "ticket_id": ticket_id,
                        "downloaded": [],
                        "count": 0,
                        "total": 0,
                        "action": "downloaded_all",
                    },
                )

            downloaded = []
            for att in attachments_list:
                dest = os.path.join(dest_dir, att.name)
                if await client.download_attachment(ticket, att, dest):
                    downloaded.append(att.name)

            total = len(attachments_list)
            partial_failure = len(downloaded) < total
            return CLIResult(
                success=not partial_failure,
                data={
                    "ticket_id": ticket_id,
                    "downloaded": downloaded,
                    "count": len(downloaded),
                    "total": total,
                    "action": "downloaded_all",
                },
                error=(
                    f"Downloaded {len(downloaded)} of {total} attachments "
                    f"({total - len(downloaded)} failed)."
                    if partial_failure
                    else None
                ),
            )

    except Exception as e:
        error_msg = str(e)
        return CLIResult(
            success=False,
            data=None,
            error=f"Failed to download attachments: {error_msg}",
        )


async def _upload_attachment(ctx: CLIContext, ticket_id: str, file_path: str) -> CLIResult:
    """Upload a file as attachment to a ticket.

    Args:
        ctx: CLI context.
        ticket_id: The ticket's formatted ID.
        file_path: Local path to the file.

    Returns:
        CLIResult with upload result or error.
    """
    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    try:
        async with AsyncRallyClient(config) as client:
            ticket = await client.get_ticket(ticket_id)
            if not ticket:
                return CLIResult(
                    success=False,
                    data=None,
                    error=f"Ticket {ticket_id} not found.",
                )
            attachment = await client.upload_attachment(ticket, file_path)
            if attachment:
                return CLIResult(
                    success=True,
                    data={
                        "ticket_id": ticket_id,
                        "attachment": attachment,
                        "action": "uploaded",
                    },
                )
            else:
                return CLIResult(
                    success=False,
                    data=None,
                    error=f"Failed to upload '{os.path.basename(file_path)}' to {ticket_id}.",
                )
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            return CLIResult(
                success=False,
                data=None,
                error="Authentication failed: Invalid API key",
            )
        return CLIResult(
            success=False,
            data=None,
            error=f"Failed to upload attachment: {error_msg}",
        )


# Register command with CLI
cli.add_command(attachments)
