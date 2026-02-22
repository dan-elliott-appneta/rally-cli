"""Tests for the 'features' command group."""

from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from rally_tui.cli.main import cli
from rally_tui.models import Feature


def _make_feature(
    formatted_id: str = "F59625",
    name: str = "Authentication Epic",
    state: str = "Developing",
    owner: str = "Test User",
    release: str = "2026.Q1",
    story_count: int = 5,
    object_id: str = "feat1",
    description: str = "",
) -> Feature:
    """Create a Feature for testing."""
    return Feature(
        object_id=object_id,
        formatted_id=formatted_id,
        name=name,
        state=state,
        owner=owner,
        release=release,
        story_count=story_count,
        description=description,
    )


def _mock_api_response(features_data):
    """Create a mock Rally API response for features.

    Args:
        features_data: List of dicts representing Rally API feature items.

    Returns:
        Dict mimicking the Rally WSAPI response structure.
    """
    return {
        "QueryResult": {
            "Results": features_data,
            "TotalResultCount": len(features_data),
        }
    }


def _feature_to_api_item(feature: Feature) -> dict:
    """Convert a Feature model to a Rally API response dict."""
    return {
        "ObjectID": feature.object_id,
        "FormattedID": feature.formatted_id,
        "Name": feature.name,
        "State": {"_refObjectName": feature.state} if feature.state else None,
        "Owner": {"_refObjectName": feature.owner} if feature.owner else None,
        "Release": {"_refObjectName": feature.release} if feature.release else None,
        "UserStories": {"Count": feature.story_count},
        "Description": feature.description,
    }


class TestFeaturesHelp:
    """Tests for features --help output."""

    def test_help_exits_0(self):
        """'features --help' should exit 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["features", "--help"])
        assert result.exit_code == 0

    def test_help_shows_format(self):
        """'features --help' should show --format option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["features", "--help"])
        assert "--format" in result.output

    def test_help_shows_show_subcommand(self):
        """'features --help' should show 'show' subcommand."""
        runner = CliRunner()
        result = runner.invoke(cli, ["features", "--help"])
        assert "show" in result.output


class TestFeaturesNoApiKey:
    """Tests for features without API key."""

    def test_no_apikey_exits_4(self):
        """Without API key, exits with code 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["features"])
        assert result.exit_code == 4
        assert "RALLY_APIKEY" in result.output


class TestFeaturesList:
    """Tests for listing features."""

    @patch("rally_tui.cli.commands.features.AsyncRallyClient")
    def test_features_list_default(self, mock_client_cls):
        """Default features command shows feature names."""
        features_list = [
            _make_feature("F59625", "Authentication Epic"),
            _make_feature("F59626", "Dashboard Redesign"),
        ]

        api_items = [_feature_to_api_item(f) for f in features_list]
        api_response = _mock_api_response(api_items)

        mock_client = AsyncMock()
        mock_client._get = AsyncMock(return_value=api_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["features"])
        assert result.exit_code == 0
        assert "F59625" in result.output
        assert "Authentication Epic" in result.output
        assert "Dashboard Redesign" in result.output

    @patch("rally_tui.cli.commands.features.AsyncRallyClient")
    def test_features_list_json_format(self, mock_client_cls):
        """--format json returns valid JSON output."""
        features_list = [_make_feature("F59625", "Auth Epic")]
        api_items = [_feature_to_api_item(f) for f in features_list]
        api_response = _mock_api_response(api_items)

        mock_client = AsyncMock()
        mock_client._get = AsyncMock(return_value=api_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["features", "--format", "json"])
        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert "F59625" in result.output

    @patch("rally_tui.cli.commands.features.AsyncRallyClient")
    def test_features_list_empty(self, mock_client_cls):
        """Empty features shows appropriate message."""
        api_response = _mock_api_response([])

        mock_client = AsyncMock()
        mock_client._get = AsyncMock(return_value=api_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["features"])
        assert result.exit_code == 0
        assert "No features found" in result.output


class TestFeaturesShow:
    """Tests for features show command."""

    @patch("rally_tui.cli.commands.features.AsyncRallyClient")
    def test_show_feature(self, mock_client_cls):
        """Showing a feature displays its details."""
        feature = _make_feature(
            "F59625",
            "Authentication Epic",
            state="Developing",
            owner="Test User",
        )
        api_items = [_feature_to_api_item(feature)]
        api_response = _mock_api_response(api_items)

        mock_client = AsyncMock()
        mock_client._get = AsyncMock(return_value=api_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["features", "show", "F59625"])
        assert result.exit_code == 0
        assert "F59625" in result.output
        assert "Authentication Epic" in result.output

    @patch("rally_tui.cli.commands.features.AsyncRallyClient")
    def test_show_feature_with_children(self, mock_client_cls):
        """Showing a feature with --children shows child stories."""
        feature = _make_feature(
            "F59625",
            "Authentication Epic",
            story_count=2,
        )
        feature_api = [_feature_to_api_item(feature)]
        feature_response = _mock_api_response(feature_api)

        children_response = _mock_api_response(
            [
                {
                    "FormattedID": "US12345",
                    "Name": "Login page",
                    "ScheduleState": "In-Progress",
                    "Owner": {"_refObjectName": "Dev User"},
                },
                {
                    "FormattedID": "US12346",
                    "Name": "OAuth integration",
                    "ScheduleState": "Defined",
                    "Owner": {"_refObjectName": "Other User"},
                },
            ]
        )

        mock_client = AsyncMock()
        # First call: feature detail, Second call: children
        mock_client._get = AsyncMock(side_effect=[feature_response, children_response])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["features", "show", "F59625", "--children"])
        assert result.exit_code == 0
        assert "F59625" in result.output
        assert "US12345" in result.output
        assert "Login page" in result.output
        assert "US12346" in result.output

    @patch("rally_tui.cli.commands.features.AsyncRallyClient")
    def test_show_feature_json_format(self, mock_client_cls):
        """features show --format json returns JSON output."""
        feature = _make_feature("F59625", "Auth Epic")
        api_items = [_feature_to_api_item(feature)]
        api_response = _mock_api_response(api_items)

        mock_client = AsyncMock()
        mock_client._get = AsyncMock(return_value=api_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["features", "show", "F59625", "--format", "json"])
        assert result.exit_code == 0
        assert '"success": true' in result.output
        assert "F59625" in result.output

    @patch("rally_tui.cli.commands.features.AsyncRallyClient")
    def test_show_feature_not_found(self, mock_client_cls):
        """Showing a nonexistent feature exits with error."""
        api_response = _mock_api_response([])

        mock_client = AsyncMock()
        mock_client._get = AsyncMock(return_value=api_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["features", "show", "F99999"])
        assert result.exit_code == 1
        assert "not found" in result.output


class TestFeaturesInvalidId:
    """Tests for invalid feature ID validation."""

    def test_show_invalid_feature_id(self):
        """Showing feature with invalid ID exits 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["features", "show", "INVALID"])
        assert result.exit_code == 2
        assert "Invalid feature ID" in result.output

    def test_show_ticket_id_not_feature(self):
        """Using a ticket ID (not feature) exits 2."""
        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["features", "show", "US12345"])
        assert result.exit_code == 2
        assert "Invalid feature ID" in result.output

    def test_show_no_apikey(self):
        """features show without API key exits 4."""
        runner = CliRunner(env={"RALLY_APIKEY": ""})
        result = runner.invoke(cli, ["features", "show", "F59625"])
        assert result.exit_code == 4


class TestFeaturesErrorCases:
    """Tests for error handling in features commands."""

    @patch("rally_tui.cli.commands.features.AsyncRallyClient")
    def test_list_api_error(self, mock_client_cls):
        """API error when listing features shows error message."""
        mock_client = AsyncMock()
        mock_client._get = AsyncMock(side_effect=Exception("Network error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["features"])
        assert result.exit_code == 1
        assert "Failed to fetch features" in result.output

    @patch("rally_tui.cli.commands.features.AsyncRallyClient")
    def test_list_auth_error(self, mock_client_cls):
        """Authentication error when listing features shows auth message."""
        mock_client = AsyncMock()
        mock_client._get = AsyncMock(side_effect=Exception("401 Unauthorized"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        runner = CliRunner(env={"RALLY_APIKEY": "test_key"})
        result = runner.invoke(cli, ["features"])
        assert result.exit_code == 1
        assert "Authentication failed" in result.output
