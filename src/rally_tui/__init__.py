"""Rally TUI - A terminal user interface for Rally work items."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("rally-tui")
except PackageNotFoundError:
    # Package not installed (development mode without pip install -e)
    __version__ = "0.0.0-dev"

__all__ = ["__version__"]
