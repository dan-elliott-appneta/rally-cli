"""Features command for viewing Rally portfolio features.

This module implements the 'features' command group for listing features
and showing feature details, including child user stories.
"""

import asyncio
import re
import sys

import click

from rally_tui.cli.formatters.base import CLIResult, OutputFormat
from rally_tui.cli.main import CLIContext, cli, pass_context
from rally_tui.config import RallyConfig
from rally_tui.models import Feature
from rally_tui.services.async_rally_client import AsyncRallyClient

# Pattern matching valid Rally feature IDs (case-insensitive)
_FEATURE_ID_RE = re.compile(r"^F\d+$", re.IGNORECASE)


@click.group("features", invoke_without_command=True)
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format (overrides global --format).",
)
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

    if sub_format:
        ctx.set_format(OutputFormat(sub_format.lower()))

    if click_ctx.invoked_subcommand is not None:
        return

    # Default: list features
    _features_list(ctx, query_filter)


def _features_list(ctx: CLIContext, query_filter: str | None) -> None:
    """Run the list-features flow (default when no subcommand)."""
    if not ctx.apikey:
        result = CLIResult(
            success=False,
            data=None,
            error="RALLY_APIKEY environment variable not set. "
            "Set RALLY_APIKEY or use --apikey flag.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(4)

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
@click.option(
    "--format",
    "sub_format",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    default=None,
    help="Output format.",
)
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
    if sub_format:
        ctx.set_format(OutputFormat(sub_format.lower()))

    if not ctx.apikey:
        result = CLIResult(
            success=False,
            data=None,
            error="RALLY_APIKEY environment variable not set. "
            "Set RALLY_APIKEY or use --apikey flag.",
        )
        click.echo(ctx.formatter.format_error(result), err=True)
        sys.exit(4)

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
            params: dict = {
                "fetch": "FormattedID,Name,State,Owner,Release,UserStories",
                "pagesize": "200",
                "order": "FormattedID desc",
                "projectScopeUp": "true",
                "projectScopeDown": "true",
            }

            if query_filter:
                sanitized = query_filter.replace("\\", "\\\\").replace('"', '\\"')
                params["query"] = f'(Name contains "{sanitized}")'

            response = await client._get("/portfolioitem/feature", params=params)

            # Parse the response
            from rally_tui.services.async_rally_client import parse_query_result

            results, _ = parse_query_result(response)

            feature_list = []
            for item in results:
                owner_ref = item.get("Owner")
                owner_name = ""
                if isinstance(owner_ref, dict):
                    owner_name = owner_ref.get("_refObjectName", "")

                release_ref = item.get("Release")
                release_name = ""
                if isinstance(release_ref, dict):
                    release_name = release_ref.get("_refObjectName", "")

                stories_ref = item.get("UserStories")
                story_count = 0
                if isinstance(stories_ref, dict):
                    story_count = stories_ref.get("Count", 0)

                state_ref = item.get("State")
                state_name = ""
                if isinstance(state_ref, dict):
                    state_name = state_ref.get("_refObjectName", "")
                elif isinstance(state_ref, str):
                    state_name = state_ref

                feature_list.append(
                    Feature(
                        object_id=str(item.get("ObjectID", "")),
                        formatted_id=item.get("FormattedID", ""),
                        name=item.get("Name", ""),
                        state=state_name,
                        owner=owner_name,
                        release=release_name,
                        story_count=story_count,
                        description=item.get("Description", "") or "",
                    )
                )

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
            response = await client._get(
                "/portfolioitem/feature",
                params={
                    "fetch": "FormattedID,Name,State,Owner,Release,Description,"
                    "UserStories,ObjectID",
                    "query": f'((FormattedID = "{sanitized_id}"))',
                    "projectScopeUp": "true",
                    "projectScopeDown": "true",
                },
            )
            from rally_tui.services.async_rally_client import parse_query_result

            results, _ = parse_query_result(response)

            if not results:
                return CLIResult(
                    success=False,
                    data=None,
                    error=f"Feature {feature_id} not found.",
                )

            item = results[0]

            owner_ref = item.get("Owner")
            owner_name = ""
            if isinstance(owner_ref, dict):
                owner_name = owner_ref.get("_refObjectName", "")

            release_ref = item.get("Release")
            release_name = ""
            if isinstance(release_ref, dict):
                release_name = release_ref.get("_refObjectName", "")

            stories_ref = item.get("UserStories")
            story_count = 0
            if isinstance(stories_ref, dict):
                story_count = stories_ref.get("Count", 0)

            state_ref = item.get("State")
            state_name = ""
            if isinstance(state_ref, dict):
                state_name = state_ref.get("_refObjectName", "")
            elif isinstance(state_ref, str):
                state_name = state_ref

            feature = Feature(
                object_id=str(item.get("ObjectID", "")),
                formatted_id=item.get("FormattedID", ""),
                name=item.get("Name", ""),
                state=state_name,
                owner=owner_name,
                release=release_name,
                story_count=story_count,
                description=item.get("Description", "") or "",
            )

            children = []
            if include_children and story_count > 0:
                children = await _fetch_children(client, feature_id)

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


async def _fetch_children(client: AsyncRallyClient, feature_id: str) -> list[dict]:
    """Fetch child user stories of a feature.

    Args:
        client: The Rally API client.
        feature_id: Feature formatted ID.

    Returns:
        List of child story dicts with formatted_id, name, state, owner.
    """
    sanitized_id = feature_id.replace("\\", "\\\\").replace('"', '\\"')
    response = await client._get(
        "/hierarchicalrequirement",
        params={
            "fetch": "FormattedID,Name,ScheduleState,Owner",
            "query": f'(Feature.FormattedID = "{sanitized_id}")',
            "order": "FormattedID",
            "pagesize": "200",
        },
    )
    from rally_tui.services.async_rally_client import parse_query_result

    results, _ = parse_query_result(response)

    children = []
    for item in results:
        owner_ref = item.get("Owner")
        owner_name = ""
        if isinstance(owner_ref, dict):
            owner_name = owner_ref.get("_refObjectName", "")

        children.append(
            {
                "formatted_id": item.get("FormattedID", ""),
                "name": item.get("Name", ""),
                "state": item.get("ScheduleState", ""),
                "owner": owner_name,
            }
        )

    return children


# Register command with CLI
cli.add_command(features)
