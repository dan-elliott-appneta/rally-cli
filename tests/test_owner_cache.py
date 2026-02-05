"""Tests for owner cache functionality."""

from pathlib import Path

import pytest

from rally_tui.models import Owner, Ticket
from rally_tui.services.cache_manager import CacheManager
from rally_tui.services.owner_utils import extract_owners_from_tickets


class TestExtractOwnersFromTickets:
    """Tests for extract_owners_from_tickets function."""

    def test_extracts_unique_owners(self):
        """Should extract unique owners from tickets."""
        tickets = [
            Ticket(
                formatted_id="US1", name="T1", ticket_type="UserStory",
                state="Defined", owner="Alice",
            ),
            Ticket(
                formatted_id="US2", name="T2", ticket_type="UserStory",
                state="Defined", owner="Bob",
            ),
            Ticket(
                formatted_id="US3", name="T3", ticket_type="UserStory",
                state="Defined", owner="Alice",
            ),
        ]
        owners = extract_owners_from_tickets(tickets)
        assert len(owners) == 2
        object_ids = {o.object_id for o in owners}
        assert object_ids == {"TEMP:Alice", "TEMP:Bob"}

    def test_skips_tickets_without_owner(self):
        """Should skip tickets with no owner."""
        tickets = [
            Ticket(
                formatted_id="US1", name="T1", ticket_type="UserStory",
                state="Defined", owner="Alice",
            ),
            Ticket(
                formatted_id="US2", name="T2", ticket_type="UserStory",
                state="Defined", owner=None,
            ),
        ]
        owners = extract_owners_from_tickets(tickets)
        assert len(owners) == 1

    def test_empty_tickets_list(self):
        """Should return empty set for empty tickets list."""
        owners = extract_owners_from_tickets([])
        assert owners == set()


class TestCacheManagerOwners:
    """Tests for CacheManager owner cache functionality."""

    @pytest.fixture
    def cache_manager(self, tmp_path: Path) -> CacheManager:
        """Create CacheManager with temp directory."""
        return CacheManager(cache_dir=tmp_path)

    def test_get_empty_cache(self, cache_manager: CacheManager):
        """Should return empty set when no owners cached."""
        owners = cache_manager.get_iteration_owners("Sprint 1")
        assert owners == set()

    def test_set_and_get_owners(self, cache_manager: CacheManager):
        """Should store and retrieve owners correctly."""
        owners = {
            Owner(object_id="123", display_name="Alice", user_name="alice@test.com"),
            Owner(object_id="456", display_name="Bob", user_name=None),
        }
        cache_manager.set_iteration_owners("Sprint 1", owners)

        retrieved = cache_manager.get_iteration_owners("Sprint 1")
        assert len(retrieved) == 2
        assert {o.object_id for o in retrieved} == {"123", "456"}

    def test_multiple_iterations(self, cache_manager: CacheManager):
        """Should keep separate caches per iteration."""
        sprint1_owners = {Owner(object_id="1", display_name="Alice", user_name=None)}
        sprint2_owners = {Owner(object_id="2", display_name="Bob", user_name=None)}

        cache_manager.set_iteration_owners("Sprint 1", sprint1_owners)
        cache_manager.set_iteration_owners("Sprint 2", sprint2_owners)

        assert len(cache_manager.get_iteration_owners("Sprint 1")) == 1
        assert len(cache_manager.get_iteration_owners("Sprint 2")) == 1

    def test_clear_specific_iteration(self, cache_manager: CacheManager):
        """Should clear only specified iteration."""
        cache_manager.set_iteration_owners("Sprint 1", {Owner("1", "Alice", None)})
        cache_manager.set_iteration_owners("Sprint 2", {Owner("2", "Bob", None)})

        cache_manager.clear_iteration_owners("Sprint 1")

        assert cache_manager.get_iteration_owners("Sprint 1") == set()
        assert len(cache_manager.get_iteration_owners("Sprint 2")) == 1

    def test_clear_all_iterations(self, cache_manager: CacheManager):
        """Should clear all iterations when no iteration specified."""
        cache_manager.set_iteration_owners("Sprint 1", {Owner("1", "Alice", None)})
        cache_manager.set_iteration_owners("Sprint 2", {Owner("2", "Bob", None)})

        cache_manager.clear_iteration_owners()  # Clear all

        assert cache_manager.get_iteration_owners("Sprint 1") == set()
        assert cache_manager.get_iteration_owners("Sprint 2") == set()

    def test_clear_cache_includes_owners(self, cache_manager: CacheManager):
        """clear_cache() should also clear owner cache."""
        cache_manager.set_iteration_owners("Sprint 1", {Owner("1", "Alice", None)})

        cache_manager.clear_cache()

        assert cache_manager.get_iteration_owners("Sprint 1") == set()

    def test_owners_persist_to_disk(self, cache_manager: CacheManager):
        """Should persist owners to disk and reload correctly."""
        owners = {Owner(object_id="123", display_name="Alice", user_name=None)}
        cache_manager.set_iteration_owners("Sprint 1", owners)

        # Create new cache manager instance (simulates app restart)
        new_manager = CacheManager(cache_dir=cache_manager.cache_dir)
        retrieved = new_manager.get_iteration_owners("Sprint 1")

        assert len(retrieved) == 1
        assert next(iter(retrieved)).object_id == "123"

    def test_corrupted_cache_file(self, cache_manager: CacheManager):
        """Should handle corrupted JSON file gracefully."""
        cache_manager._ensure_cache_dir()
        cache_manager._owners_file.write_text("{corrupted json")

        # Should return empty set instead of crashing
        owners = cache_manager.get_iteration_owners("Sprint 1")
        assert owners == set()

        # Writing new data should work (overwrites corrupted file)
        new_owners = {Owner("1", "Alice", None)}
        cache_manager.set_iteration_owners("Sprint 1", new_owners)
        assert len(cache_manager.get_iteration_owners("Sprint 1")) == 1
