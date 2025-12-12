"""Cache manager for local ticket storage."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rally_tui.models import Ticket

logger = logging.getLogger(__name__)

CACHE_VERSION = 1


@dataclass
class CacheMetadata:
    """Metadata about the cached data."""

    version: int = CACHE_VERSION
    workspace: str = ""
    project: str = ""
    tickets_updated: str | None = None  # ISO format timestamp

    @property
    def tickets_updated_dt(self) -> datetime | None:
        """Get tickets_updated as datetime."""
        if not self.tickets_updated:
            return None
        try:
            return datetime.fromisoformat(self.tickets_updated)
        except ValueError:
            return None


class CacheManager:
    """Manages local caching of Rally tickets.

    Provides file I/O operations with TTL-based cache validity checking
    and atomic writes to prevent corruption.

    Cache directory structure:
        ~/.cache/rally-tui/
        ├── meta.json      # Cache metadata
        └── tickets.json   # Cached tickets
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize cache manager.

        Args:
            cache_dir: Custom cache directory. Defaults to ~/.cache/rally-tui/
        """
        self._cache_dir = cache_dir or Path.home() / ".cache" / "rally-tui"
        self._meta_file = self._cache_dir / "meta.json"
        self._tickets_file = self._cache_dir / "tickets.json"

    @property
    def cache_dir(self) -> Path:
        """Get the cache directory path."""
        return self._cache_dir

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _atomic_write(self, path: Path, data: dict[str, Any]) -> None:
        """Write data to file atomically.

        Writes to a temp file then renames to prevent corruption on crash.

        Args:
            path: Target file path
            data: Dictionary to write as JSON
        """
        self._ensure_cache_dir()

        # Write to temp file in same directory (same filesystem for rename)
        fd, temp_path = tempfile.mkstemp(
            dir=self._cache_dir, suffix=".tmp", prefix=path.stem
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            # Atomic rename
            os.replace(temp_path, path)
        except Exception:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    def _read_json(self, path: Path) -> dict[str, Any] | None:
        """Read and parse JSON file.

        Args:
            path: File path to read

        Returns:
            Parsed JSON as dict, or None if file doesn't exist or is invalid
        """
        if not path.exists():
            return None
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read cache file {path}: {e}")
            return None

    def get_metadata(self) -> CacheMetadata | None:
        """Get cache metadata.

        Returns:
            CacheMetadata object, or None if no metadata exists
        """
        data = self._read_json(self._meta_file)
        if not data:
            return None
        try:
            return CacheMetadata(
                version=data.get("version", CACHE_VERSION),
                workspace=data.get("workspace", ""),
                project=data.get("project", ""),
                tickets_updated=data.get("tickets_updated"),
            )
        except (TypeError, KeyError) as e:
            logger.warning(f"Invalid cache metadata: {e}")
            return None

    def get_cached_tickets(self) -> tuple[list[Ticket], CacheMetadata | None]:
        """Load tickets from cache.

        Returns:
            Tuple of (list of Ticket objects, CacheMetadata or None)
        """
        metadata = self.get_metadata()
        data = self._read_json(self._tickets_file)

        if not data or "tickets" not in data:
            return [], metadata

        tickets = []
        for ticket_data in data["tickets"]:
            try:
                ticket = Ticket(
                    formatted_id=ticket_data["formatted_id"],
                    name=ticket_data["name"],
                    ticket_type=ticket_data["ticket_type"],
                    state=ticket_data["state"],
                    owner=ticket_data.get("owner"),
                    description=ticket_data.get("description", ""),
                    notes=ticket_data.get("notes", ""),
                    iteration=ticket_data.get("iteration"),
                    points=ticket_data.get("points"),
                    object_id=ticket_data.get("object_id"),
                    parent_id=ticket_data.get("parent_id"),
                )
                tickets.append(ticket)
            except (TypeError, KeyError) as e:
                logger.warning(f"Skipping invalid cached ticket: {e}")
                continue

        return tickets, metadata

    def save_tickets(
        self, tickets: list[Ticket], workspace: str = "", project: str = ""
    ) -> None:
        """Save tickets to cache.

        Args:
            tickets: List of Ticket objects to cache
            workspace: Workspace name for metadata
            project: Project name for metadata
        """
        # Save tickets
        ticket_data = {"tickets": [asdict(t) for t in tickets]}
        self._atomic_write(self._tickets_file, ticket_data)

        # Save metadata
        now = datetime.now(timezone.utc).isoformat()
        metadata = {
            "version": CACHE_VERSION,
            "workspace": workspace,
            "project": project,
            "tickets_updated": now,
        }
        self._atomic_write(self._meta_file, metadata)

        logger.info(f"Saved {len(tickets)} tickets to cache")

    def is_cache_valid(self, ttl_minutes: int = 15) -> bool:
        """Check if cache is still valid based on TTL.

        Args:
            ttl_minutes: Time-to-live in minutes

        Returns:
            True if cache exists and is within TTL, False otherwise
        """
        metadata = self.get_metadata()
        if not metadata or not metadata.tickets_updated_dt:
            return False

        age = datetime.now(timezone.utc) - metadata.tickets_updated_dt
        return age.total_seconds() < ttl_minutes * 60

    def get_cache_age_minutes(self) -> int | None:
        """Get the age of the cache in minutes.

        Returns:
            Age in minutes, or None if no cache exists
        """
        metadata = self.get_metadata()
        if not metadata or not metadata.tickets_updated_dt:
            return None

        age = datetime.now(timezone.utc) - metadata.tickets_updated_dt
        return int(age.total_seconds() / 60)

    def clear_cache(self) -> None:
        """Remove all cached files."""
        for path in [self._meta_file, self._tickets_file]:
            try:
                path.unlink(missing_ok=True)
            except OSError as e:
                logger.warning(f"Failed to remove {path}: {e}")

        logger.info("Cache cleared")

    def is_cache_for_project(self, workspace: str, project: str) -> bool:
        """Check if cache is for the specified workspace and project.

        Args:
            workspace: Expected workspace name
            project: Expected project name

        Returns:
            True if cache matches workspace and project
        """
        metadata = self.get_metadata()
        if not metadata:
            return False
        return metadata.workspace == workspace and metadata.project == project
