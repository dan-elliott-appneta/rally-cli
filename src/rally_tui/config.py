"""Rally TUI Configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class RallyConfig(BaseSettings):
    """Rally API configuration.

    Loads settings from environment variables with RALLY_ prefix.
    Can also load from a .env file if present.

    Environment Variables:
        RALLY_SERVER: Rally server hostname (default: rally1.rallydev.com)
        RALLY_APIKEY: Rally API key (required for real API access)
        RALLY_WORKSPACE: Workspace name to connect to
        RALLY_PROJECT: Project name to connect to
    """

    model_config = SettingsConfigDict(
        env_prefix="RALLY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    server: str = "rally1.rallydev.com"
    apikey: str = ""
    workspace: str = ""
    project: str = ""

    @property
    def is_configured(self) -> bool:
        """Check if API key is configured.

        Returns:
            True if an API key is present, False otherwise.
        """
        return bool(self.apikey)
