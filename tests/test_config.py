"""Tests for configuration loading."""

import pytest

from rally_tui.config import RallyConfig


class TestRallyConfig:
    """Tests for RallyConfig."""

    def test_default_server(self) -> None:
        """Default server is rally1.rallydev.com."""
        config = RallyConfig()
        assert config.server == "rally1.rallydev.com"

    def test_default_apikey_empty(self) -> None:
        """Default API key is empty."""
        config = RallyConfig()
        assert config.apikey == ""

    def test_default_workspace_empty(self) -> None:
        """Default workspace is empty."""
        config = RallyConfig()
        assert config.workspace == ""

    def test_default_project_empty(self) -> None:
        """Default project is empty."""
        config = RallyConfig()
        assert config.project == ""

    def test_is_configured_false_by_default(self) -> None:
        """Config is not configured without API key."""
        config = RallyConfig()
        assert not config.is_configured

    def test_is_configured_true_with_apikey(self) -> None:
        """Config is considered configured when API key is set."""
        config = RallyConfig(apikey="test_key")
        assert config.is_configured

    def test_explicit_values(self) -> None:
        """Config accepts explicit values."""
        config = RallyConfig(
            server="custom.rally.com",
            apikey="my_api_key",
            workspace="My Workspace",
            project="My Project",
        )
        assert config.server == "custom.rally.com"
        assert config.apikey == "my_api_key"
        assert config.workspace == "My Workspace"
        assert config.project == "My Project"
        assert config.is_configured


class TestRallyConfigFromEnvironment:
    """Tests for loading config from environment variables."""

    def test_loads_apikey_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config loads RALLY_APIKEY from environment."""
        monkeypatch.setenv("RALLY_APIKEY", "env_api_key")
        config = RallyConfig()
        assert config.apikey == "env_api_key"
        assert config.is_configured

    def test_loads_server_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config loads RALLY_SERVER from environment."""
        monkeypatch.setenv("RALLY_SERVER", "custom.server.com")
        config = RallyConfig()
        assert config.server == "custom.server.com"

    def test_loads_workspace_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config loads RALLY_WORKSPACE from environment."""
        monkeypatch.setenv("RALLY_WORKSPACE", "Test Workspace")
        config = RallyConfig()
        assert config.workspace == "Test Workspace"

    def test_loads_project_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config loads RALLY_PROJECT from environment."""
        monkeypatch.setenv("RALLY_PROJECT", "Test Project")
        config = RallyConfig()
        assert config.project == "Test Project"

    def test_loads_all_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config loads all values from environment."""
        monkeypatch.setenv("RALLY_SERVER", "env.server.com")
        monkeypatch.setenv("RALLY_APIKEY", "env_key")
        monkeypatch.setenv("RALLY_WORKSPACE", "Env Workspace")
        monkeypatch.setenv("RALLY_PROJECT", "Env Project")

        config = RallyConfig()

        assert config.server == "env.server.com"
        assert config.apikey == "env_key"
        assert config.workspace == "Env Workspace"
        assert config.project == "Env Project"
        assert config.is_configured
