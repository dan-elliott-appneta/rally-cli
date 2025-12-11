"""Tests for the logging module."""

import logging
from pathlib import Path

import pytest

from rally_tui.user_settings import UserSettings
from rally_tui.utils.logging import get_logger, setup_logging, set_log_level


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_creates_log_file(self, tmp_path: Path, monkeypatch) -> None:
        """setup_logging should create log file in config directory."""
        log_file = tmp_path / "rally-tui.log"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")
        monkeypatch.setattr(UserSettings, "LOG_FILE", log_file)

        # Reset initialization flag
        import rally_tui.utils.logging as logging_module
        logging_module._initialized = False

        settings = UserSettings()
        logger = setup_logging(settings)

        # Write a log message
        logger.info("Test message")

        assert log_file.exists()

    def test_returns_logger(self, tmp_path: Path, monkeypatch) -> None:
        """setup_logging should return a logger instance."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")
        monkeypatch.setattr(UserSettings, "LOG_FILE", tmp_path / "rally-tui.log")

        # Reset initialization flag
        import rally_tui.utils.logging as logging_module
        logging_module._initialized = False

        settings = UserSettings()
        logger = setup_logging(settings)

        assert isinstance(logger, logging.Logger)
        assert logger.name == "rally_tui"

    def test_respects_log_level(self, tmp_path: Path, monkeypatch) -> None:
        """setup_logging should use log level from settings."""
        log_file = tmp_path / "rally-tui.log"
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", config_file)
        monkeypatch.setattr(UserSettings, "LOG_FILE", log_file)

        # Reset initialization flag
        import rally_tui.utils.logging as logging_module
        logging_module._initialized = False

        settings = UserSettings()
        settings.log_level = "DEBUG"
        logger = setup_logging(settings)

        assert logger.level == logging.DEBUG


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_root_logger(self) -> None:
        """get_logger with no name returns root rally_tui logger."""
        logger = get_logger()
        assert logger.name == "rally_tui"

    def test_get_named_logger(self) -> None:
        """get_logger with name returns child logger."""
        logger = get_logger("rally_tui.app")
        assert logger.name == "rally_tui.app"

    def test_child_logger_inherits(self) -> None:
        """Child loggers should inherit from rally_tui."""
        logger = get_logger("rally_tui.services.client")
        assert "rally_tui" in logger.name


class TestSetLogLevel:
    """Tests for set_log_level function."""

    def test_changes_log_level(self, tmp_path: Path, monkeypatch) -> None:
        """set_log_level should change the logger level."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")
        monkeypatch.setattr(UserSettings, "LOG_FILE", tmp_path / "rally-tui.log")

        # Reset initialization flag
        import rally_tui.utils.logging as logging_module
        logging_module._initialized = False

        settings = UserSettings()
        logger = setup_logging(settings)

        set_log_level("ERROR")
        assert logger.level == logging.ERROR

    def test_accepts_lowercase(self, tmp_path: Path, monkeypatch) -> None:
        """set_log_level should accept lowercase level names."""
        monkeypatch.setattr(UserSettings, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(UserSettings, "CONFIG_FILE", tmp_path / "config.json")
        monkeypatch.setattr(UserSettings, "LOG_FILE", tmp_path / "rally-tui.log")

        # Reset initialization flag
        import rally_tui.utils.logging as logging_module
        logging_module._initialized = False

        settings = UserSettings()
        logger = setup_logging(settings)

        set_log_level("warning")
        assert logger.level == logging.WARNING
