"""Tests for the CacheManager."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from rally_tui.models import Ticket
from rally_tui.services.cache_manager import (
    CACHE_VERSION,
    CacheManager,
    CacheMetadata,
)


class TestCacheMetadata:
    """Tests for CacheMetadata dataclass."""

    def test_default_values(self) -> None:
        """CacheMetadata should have sensible defaults."""
        meta = CacheMetadata()
        assert meta.version == CACHE_VERSION
        assert meta.workspace == ""
        assert meta.project == ""
        assert meta.tickets_updated is None

    def test_tickets_updated_dt_none(self) -> None:
        """tickets_updated_dt should return None when no timestamp."""
        meta = CacheMetadata()
        assert meta.tickets_updated_dt is None

    def test_tickets_updated_dt_valid(self) -> None:
        """tickets_updated_dt should parse valid ISO timestamp."""
        now = datetime.now(UTC)
        meta = CacheMetadata(tickets_updated=now.isoformat())
        assert meta.tickets_updated_dt is not None
        # Allow small time difference due to parsing
        assert abs((meta.tickets_updated_dt - now).total_seconds()) < 1

    def test_tickets_updated_dt_invalid(self) -> None:
        """tickets_updated_dt should return None for invalid timestamp."""
        meta = CacheMetadata(tickets_updated="not-a-date")
        assert meta.tickets_updated_dt is None


class TestCacheManagerInit:
    """Tests for CacheManager initialization."""

    def test_default_cache_dir(self) -> None:
        """CacheManager should use ~/.cache/rally-tui/ by default."""
        manager = CacheManager()
        expected = Path.home() / ".cache" / "rally-tui"
        assert manager.cache_dir == expected

    def test_custom_cache_dir(self, tmp_path: Path) -> None:
        """CacheManager should accept custom cache directory."""
        cache_dir = tmp_path / "custom-cache"
        manager = CacheManager(cache_dir=cache_dir)
        assert manager.cache_dir == cache_dir


class TestCacheManagerDirectoryCreation:
    """Tests for cache directory creation."""

    def test_creates_directory_on_save(self, tmp_path: Path) -> None:
        """Cache directory should be created when saving."""
        cache_dir = tmp_path / "new-cache"
        manager = CacheManager(cache_dir=cache_dir)
        assert not cache_dir.exists()

        manager.save_tickets([], workspace="Test", project="Test")
        assert cache_dir.exists()

    def test_handles_existing_directory(self, tmp_path: Path) -> None:
        """Should handle already existing cache directory."""
        cache_dir = tmp_path / "existing-cache"
        cache_dir.mkdir()
        manager = CacheManager(cache_dir=cache_dir)

        # Should not raise
        manager.save_tickets([], workspace="Test", project="Test")


class TestCacheManagerSaveAndLoad:
    """Tests for saving and loading tickets."""

    def test_save_and_load_tickets(self, tmp_path: Path) -> None:
        """Should round-trip tickets through cache."""
        manager = CacheManager(cache_dir=tmp_path)
        tickets = [
            Ticket(
                formatted_id="US1234",
                name="Test story",
                ticket_type="UserStory",
                state="Defined",
                owner="John",
                points=3,
            ),
            Ticket(
                formatted_id="DE5678",
                name="Test defect",
                ticket_type="Defect",
                state="In-Progress",
                description="Bug description",
            ),
        ]

        manager.save_tickets(tickets, workspace="MyWorkspace", project="MyProject")
        loaded, metadata = manager.get_cached_tickets()

        assert len(loaded) == 2
        assert loaded[0].formatted_id == "US1234"
        assert loaded[0].name == "Test story"
        assert loaded[0].owner == "John"
        assert loaded[0].points == 3
        assert loaded[1].formatted_id == "DE5678"
        assert loaded[1].description == "Bug description"

    def test_save_updates_metadata(self, tmp_path: Path) -> None:
        """Saving should update metadata."""
        manager = CacheManager(cache_dir=tmp_path)
        before = datetime.now(UTC)

        manager.save_tickets([], workspace="TestWS", project="TestProj")

        metadata = manager.get_metadata()
        assert metadata is not None
        assert metadata.workspace == "TestWS"
        assert metadata.project == "TestProj"
        assert metadata.tickets_updated_dt is not None
        assert metadata.tickets_updated_dt >= before

    def test_load_empty_cache(self, tmp_path: Path) -> None:
        """Loading from empty cache should return empty list."""
        manager = CacheManager(cache_dir=tmp_path)
        tickets, metadata = manager.get_cached_tickets()
        assert tickets == []
        assert metadata is None

    def test_save_all_ticket_fields(self, tmp_path: Path) -> None:
        """All ticket fields should be saved and loaded."""
        manager = CacheManager(cache_dir=tmp_path)
        ticket = Ticket(
            formatted_id="US9999",
            name="Full ticket",
            ticket_type="UserStory",
            state="Completed",
            owner="Jane Doe",
            description="Full description",
            notes="Some notes",
            iteration="Sprint 5",
            points=8,
            object_id="123456789",
            parent_id="F12345",
        )

        manager.save_tickets([ticket])
        loaded, _ = manager.get_cached_tickets()

        assert len(loaded) == 1
        t = loaded[0]
        assert t.formatted_id == "US9999"
        assert t.name == "Full ticket"
        assert t.ticket_type == "UserStory"
        assert t.state == "Completed"
        assert t.owner == "Jane Doe"
        assert t.description == "Full description"
        assert t.notes == "Some notes"
        assert t.iteration == "Sprint 5"
        assert t.points == 8
        assert t.object_id == "123456789"
        assert t.parent_id == "F12345"


class TestCacheManagerValidity:
    """Tests for cache validity checking."""

    def test_cache_valid_fresh(self, tmp_path: Path) -> None:
        """Fresh cache should be valid."""
        manager = CacheManager(cache_dir=tmp_path)
        manager.save_tickets([])

        assert manager.is_cache_valid(ttl_minutes=15) is True

    def test_cache_invalid_stale(self, tmp_path: Path) -> None:
        """Stale cache should be invalid."""
        manager = CacheManager(cache_dir=tmp_path)
        # Create metadata with old timestamp
        old_time = datetime.now(UTC) - timedelta(minutes=20)
        metadata = {
            "version": CACHE_VERSION,
            "workspace": "Test",
            "project": "Test",
            "tickets_updated": old_time.isoformat(),
        }
        (tmp_path / "meta.json").write_text(json.dumps(metadata))

        assert manager.is_cache_valid(ttl_minutes=15) is False

    def test_cache_invalid_empty(self, tmp_path: Path) -> None:
        """Empty cache should be invalid."""
        manager = CacheManager(cache_dir=tmp_path)
        assert manager.is_cache_valid() is False

    def test_cache_age_fresh(self, tmp_path: Path) -> None:
        """Fresh cache should have age 0."""
        manager = CacheManager(cache_dir=tmp_path)
        manager.save_tickets([])

        age = manager.get_cache_age_minutes()
        assert age is not None
        assert age == 0

    def test_cache_age_old(self, tmp_path: Path) -> None:
        """Old cache should report correct age."""
        manager = CacheManager(cache_dir=tmp_path)
        old_time = datetime.now(UTC) - timedelta(minutes=10)
        metadata = {
            "version": CACHE_VERSION,
            "workspace": "Test",
            "project": "Test",
            "tickets_updated": old_time.isoformat(),
        }
        (tmp_path / "meta.json").write_text(json.dumps(metadata))

        age = manager.get_cache_age_minutes()
        assert age is not None
        assert 9 <= age <= 11  # Allow small variance

    def test_cache_age_empty(self, tmp_path: Path) -> None:
        """Empty cache should return None for age."""
        manager = CacheManager(cache_dir=tmp_path)
        assert manager.get_cache_age_minutes() is None


class TestCacheManagerClear:
    """Tests for clearing cache."""

    def test_clear_cache(self, tmp_path: Path) -> None:
        """Clearing cache should remove all files."""
        manager = CacheManager(cache_dir=tmp_path)
        manager.save_tickets(
            [
                Ticket(
                    formatted_id="US1",
                    name="Test",
                    ticket_type="UserStory",
                    state="Defined",
                )
            ]
        )

        # Verify files exist
        assert (tmp_path / "meta.json").exists()
        assert (tmp_path / "tickets.json").exists()

        manager.clear_cache()

        # Verify files removed
        assert not (tmp_path / "meta.json").exists()
        assert not (tmp_path / "tickets.json").exists()

    def test_clear_empty_cache(self, tmp_path: Path) -> None:
        """Clearing empty cache should not raise."""
        manager = CacheManager(cache_dir=tmp_path)
        # Should not raise
        manager.clear_cache()


class TestCacheManagerCorruptData:
    """Tests for handling corrupt cache data."""

    def test_corrupt_json_tickets(self, tmp_path: Path) -> None:
        """Should handle corrupt tickets.json gracefully."""
        manager = CacheManager(cache_dir=tmp_path)
        tmp_path.mkdir(exist_ok=True)
        (tmp_path / "tickets.json").write_text("not valid json {{{")

        tickets, metadata = manager.get_cached_tickets()
        assert tickets == []

    def test_corrupt_json_metadata(self, tmp_path: Path) -> None:
        """Should handle corrupt meta.json gracefully."""
        manager = CacheManager(cache_dir=tmp_path)
        tmp_path.mkdir(exist_ok=True)
        (tmp_path / "meta.json").write_text("invalid json")

        metadata = manager.get_metadata()
        assert metadata is None

    def test_missing_ticket_fields(self, tmp_path: Path) -> None:
        """Should skip tickets with missing required fields."""
        manager = CacheManager(cache_dir=tmp_path)
        tmp_path.mkdir(exist_ok=True)
        data = {
            "tickets": [
                {"formatted_id": "US1"},  # Missing required fields
                {
                    "formatted_id": "US2",
                    "name": "Valid",
                    "ticket_type": "UserStory",
                    "state": "Defined",
                },
            ]
        }
        (tmp_path / "tickets.json").write_text(json.dumps(data))

        tickets, _ = manager.get_cached_tickets()
        assert len(tickets) == 1
        assert tickets[0].formatted_id == "US2"


class TestCacheManagerAtomicWrite:
    """Tests for atomic write behavior."""

    def test_atomic_write_creates_file(self, tmp_path: Path) -> None:
        """Atomic write should create the file."""
        manager = CacheManager(cache_dir=tmp_path)
        manager.save_tickets(
            [
                Ticket(
                    formatted_id="US1",
                    name="Test",
                    ticket_type="UserStory",
                    state="Defined",
                )
            ]
        )

        assert (tmp_path / "tickets.json").exists()
        content = json.loads((tmp_path / "tickets.json").read_text())
        assert len(content["tickets"]) == 1

    def test_no_temp_files_left(self, tmp_path: Path) -> None:
        """No temporary files should remain after write."""
        manager = CacheManager(cache_dir=tmp_path)
        manager.save_tickets([])

        # Check for .tmp files
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0


class TestCacheManagerProjectMatching:
    """Tests for project matching."""

    def test_matches_correct_project(self, tmp_path: Path) -> None:
        """Should match when workspace and project match."""
        manager = CacheManager(cache_dir=tmp_path)
        manager.save_tickets([], workspace="WorkspaceA", project="ProjectX")

        assert manager.is_cache_for_project("WorkspaceA", "ProjectX") is True

    def test_no_match_different_workspace(self, tmp_path: Path) -> None:
        """Should not match with different workspace."""
        manager = CacheManager(cache_dir=tmp_path)
        manager.save_tickets([], workspace="WorkspaceA", project="ProjectX")

        assert manager.is_cache_for_project("WorkspaceB", "ProjectX") is False

    def test_no_match_different_project(self, tmp_path: Path) -> None:
        """Should not match with different project."""
        manager = CacheManager(cache_dir=tmp_path)
        manager.save_tickets([], workspace="WorkspaceA", project="ProjectX")

        assert manager.is_cache_for_project("WorkspaceA", "ProjectY") is False

    def test_no_match_empty_cache(self, tmp_path: Path) -> None:
        """Should not match when cache is empty."""
        manager = CacheManager(cache_dir=tmp_path)

        assert manager.is_cache_for_project("WorkspaceA", "ProjectX") is False
