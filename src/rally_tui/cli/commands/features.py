"""Features command for viewing Rally portfolio features.

This module implements the 'features' command group for listing features
and showing feature details, including child user stories.
"""

import asyncio
import re
import sys

import click

from rally_tui.cli.commands._common import apply_format_override, format_option, require_apikey
from rally_tui.cli.formatters.base import CLIResult
from rally_tui.cli.main import CLIContext, cli, pass_context
from rally_tui.config import RallyConfig
from rally_tui.services.async_rally_client import AsyncRallyClient

# Pattern matching valid Rally feature IDs (case-insensitive)
_FEATURE_ID_RE = re.compile(r"^F\d+$", re.IGNORECASE)


@click.group("features", invoke_without_command=True)
@format_option
@click.option(
    "--query",
    "query_filter",
    default=None,
    help="Filter features by query text.",
)
@click.pass_context
def features(
    click_ctx: click.Context,
    sub_format: str | None,
    query_filter: str | None,
) -> None:
    """View Rally portfolio features.

    Without a subcommand, lists all features in the project.
    Use 'show' to view a specific feature's details.

    Examples:

    \b
        rally-cli features
        rally-cli features --format json
        rally-cli features show F59625
        rally-cli features show F59625 --children
    """
    ctx = click_ctx.obj
    apply_format_override(ctx, sub_format)

    if click_ctx.invoked_subcommand is not None:
        return

    # Default: list features
    _features_list(ctx, query_filter)


def _features_list(ctx: CLIContext, query_filter: str | None) -> None:
    """Run the list-features flow (default when no subcommand)."""
    require_apikey(ctx)

    result = asyncio.run(_fetch_features(ctx, query_filter))

    if result.success:
        output = ctx.formatter.format_features(result)
        click.echo(output)
        sys.exit(0)
    else:
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


@features.command("show")
@click.argument("feature_id")
@click.option(
    "--children",
    is_flag=True,
    default=False,
    help="Show child user stories.",
)
@format_option
@pass_context
def features_show(
    ctx: CLIContext,
    feature_id: str,
    children: bool,
    sub_format: str | None,
) -> None:
    """Show detailed information for a feature.

    FEATURE_ID is the feature's formatted ID (e.g., F59625).

    Examples:

    \b
        rally-cli features show F59625
        rally-cli features show F59625 --children
        rally-cli features show F59625 --format json
    """
    apply_format_override(ctx, sub_format)
    require_apikey(ctx)

    if not _FEATURE_ID_RE.match(feature_id):
        result = CLIResult(
            success=False,
            data=None,
            error=f"Invalid feature ID format: {feature_id}. "
            "Feature ID must match pattern F followed by digits (e.g., F59625).",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(2)

    result = asyncio.run(_fetch_feature_detail(ctx, feature_id, children))

    if result.success:
        output = ctx.formatter.format_feature_detail(result)
        click.echo(output)
        sys.exit(0)
    else:
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(1)


async def _fetch_features(ctx: CLIContext, query_filter: str | None) -> CLIResult:
    """Fetch features from Rally.

    Args:
        ctx: CLI context.
        query_filter: Optional query text to filter features.

    Returns:
        CLIResult with feature data or error.
    """
    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    try:
        async with AsyncRallyClient(config) as client:
            query = None
            if query_filter:
                sanitized = query_filter.replace("\\", "\\\\").replace('"', '\\"')
                query = f'(Name contains "{sanitized}")'

            feature_list = await client.get_features(query=query)
            return CLIResult(success=True, data=feature_list)

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
            error=f"Failed to fetch features: {error_msg}",
        )


async def _fetch_feature_detail(
    ctx: CLIContext, feature_id: str, include_children: bool
) -> CLIResult:
    """Fetch a single feature with optional child stories.

    Args:
        ctx: CLI context.
        feature_id: Feature formatted ID.
        include_children: Whether to fetch child user stories.

    Returns:
        CLIResult with feature detail data or error.
    """
    config = RallyConfig(
        server=ctx.server,
        apikey=ctx.apikey,
        workspace=ctx.workspace,
        project=ctx.project,
    )

    try:
        async with AsyncRallyClient(config) as client:
            sanitized_id = feature_id.replace("\\", "\\\\").replace('"', '\\"')
            query = f'(FormattedID = "{sanitized_id}")'
            features = await client.get_features(query=query, count=1)

            if not features:
                return CLIResult(
                    success=False,
                    data=None,
                    error=f"Feature {feature_id} not found.",
                )

            feature = features[0]

            children = []
            if include_children and feature.story_count > 0:
                children = await client.get_feature_children(feature_id)

            return CLIResult(
                success=True,
                data={
                    "feature": feature,
                    "children": children,
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
            error=f"Failed to fetch feature: {error_msg}",
        )


# Register command with CLI
cli.add_command(features)
