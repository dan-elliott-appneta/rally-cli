"""Tests for async mock Rally client."""

import pytest

from rally_tui.models import Ticket
from rally_tui.services.async_mock_client import AsyncMockRallyClient


@pytest.fixture
def sample_tickets() -> list[Ticket]:
    """Create sample tickets for testing."""
    return [
        Ticket(
            formatted_id="US1234",
            name="Test Story 1",
            ticket_type="UserStory",
            state="Defined",
            owner="Test User",
            object_id="obj_1",
        ),
        Ticket(
            formatted_id="US5678",
            name="Test Story 2",
            ticket_type="UserStory",
            state="In-Progress",
            owner="Test User",
            object_id="obj_2",
        ),
        Ticket(
            formatted_id="DE9012",
            name="Test Defect",
            ticket_type="Defect",
            state="Open",
            owner="Other User",
            object_id="obj_3",
        ),
    ]


class TestAsyncMockClientInit:
    """Tests for AsyncMockRallyClient initialization."""

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        async with AsyncMockRallyClient() as client:
            assert client.workspace == "My Workspace"
            assert client.project == "My Project"

    @pytest.mark.asyncio
    async def test_custom_workspace(self) -> None:
        client = AsyncMockRallyClient(
            workspace="Custom Workspace",
            project="Custom Project",
        )
        assert client.workspace == "Custom Workspace"
        assert client.project == "Custom Project"

    @pytest.mark.asyncio
    async def test_custom_user(self) -> None:
        client = AsyncMockRallyClient(current_user="John Doe")
        assert client.current_user == "John Doe"


class TestAsyncMockClientGetTickets:
    """Tests for get_tickets method."""

    @pytest.mark.asyncio
    async def test_get_all_tickets(self, sample_tickets: list[Ticket]) -> None:
        async with AsyncMockRallyClient(tickets=sample_tickets) as client:
            tickets = await client.get_tickets()
            assert len(tickets) == 3

    @pytest.mark.asyncio
    async def test_get_tickets_with_query(self, sample_tickets: list[Ticket]) -> None:
        async with AsyncMockRallyClient(tickets=sample_tickets) as client:
            tickets = await client.get_tickets(query="Story 1")
            assert len(tickets) == 1
            assert tickets[0].formatted_id == "US1234"

    @pytest.mark.asyncio
    async def test_get_tickets_empty_query(self, sample_tickets: list[Ticket]) -> None:
        async with AsyncMockRallyClient(tickets=sample_tickets) as client:
            tickets = await client.get_tickets(query="nonexistent")
            assert len(tickets) == 0


class TestAsyncMockClientGetTicket:
    """Tests for get_ticket method."""

    @pytest.mark.asyncio
    async def test_get_existing_ticket(self, sample_tickets: list[Ticket]) -> None:
        async with AsyncMockRallyClient(tickets=sample_tickets) as client:
            ticket = await client.get_ticket("US1234")
            assert ticket is not None
            assert ticket.name == "Test Story 1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_ticket(self, sample_tickets: list[Ticket]) -> None:
        async with AsyncMockRallyClient(tickets=sample_tickets) as client:
            ticket = await client.get_ticket("US9999")
            assert ticket is None


class TestAsyncMockClientUpdatePoints:
    """Tests for update_points method."""

    @pytest.mark.asyncio
    async def test_update_points(self, sample_tickets: list[Ticket]) -> None:
        async with AsyncMockRallyClient(tickets=sample_tickets) as client:
            ticket = sample_tickets[0]
            updated = await client.update_points(ticket, 5.0)
            assert updated is not None
            assert updated.points == 5

    @pytest.mark.asyncio
    async def test_update_points_decimal(self, sample_tickets: list[Ticket]) -> None:
        async with AsyncMockRallyClient(tickets=sample_tickets) as client:
            ticket = sample_tickets[0]
            updated = await client.update_points(ticket, 0.5)
            assert updated is not None
            assert updated.points == 0.5


class TestAsyncMockClientUpdateState:
    """Tests for update_state method."""

    @pytest.mark.asyncio
    async def test_update_state(self, sample_tickets: list[Ticket]) -> None:
        async with AsyncMockRallyClient(tickets=sample_tickets) as client:
            ticket = sample_tickets[0]
            updated = await client.update_state(ticket, "Completed")
            assert updated is not None
            assert updated.state == "Completed"


class TestAsyncMockClientCreateTicket:
    """Tests for create_ticket method."""

    @pytest.mark.asyncio
    async def test_create_user_story(self) -> None:
        async with AsyncMockRallyClient(tickets=[]) as client:
            ticket = await client.create_ticket(
                title="New Story",
                ticket_type="HierarchicalRequirement",
                description="Test description",
            )
            assert ticket is not None
            assert ticket.formatted_id.startswith("US")
            assert ticket.name == "New Story"

    @pytest.mark.asyncio
    async def test_create_defect(self) -> None:
        async with AsyncMockRallyClient(tickets=[]) as client:
            ticket = await client.create_ticket(
                title="New Defect",
                ticket_type="Defect",
            )
            assert ticket is not None
            assert ticket.formatted_id.startswith("DE")


class TestAsyncMockClientIterations:
    """Tests for get_iterations method."""

    @pytest.mark.asyncio
    async def test_get_iterations(self) -> None:
        async with AsyncMockRallyClient() as client:
            iterations = await client.get_iterations()
            assert len(iterations) > 0
            # Default mock generates sample iterations
            assert iterations[0].name is not None


class TestAsyncMockClientFeatures:
    """Tests for get_feature and set_parent methods."""

    @pytest.mark.asyncio
    async def test_get_feature(self) -> None:
        async with AsyncMockRallyClient() as client:
            feature = await client.get_feature("F59625")
            assert feature is not None
            assert feature[0] == "F59625"
            assert "API Platform" in feature[1]

    @pytest.mark.asyncio
    async def test_get_nonexistent_feature(self) -> None:
        async with AsyncMockRallyClient() as client:
            feature = await client.get_feature("F00000")
            assert feature is None

    @pytest.mark.asyncio
    async def test_set_parent(self, sample_tickets: list[Ticket]) -> None:
        async with AsyncMockRallyClient(tickets=sample_tickets) as client:
            ticket = sample_tickets[0]
            updated = await client.set_parent(ticket, "F59625")
            assert updated is not None
            assert updated.parent_id == "F59625"


class TestAsyncMockClientBulkOperations:
    """Tests for bulk operations."""

    @pytest.mark.asyncio
    async def test_bulk_update_state(self, sample_tickets: list[Ticket]) -> None:
        async with AsyncMockRallyClient(tickets=sample_tickets) as client:
            result = await client.bulk_update_state(sample_tickets[:2], "Completed")
            assert result.success_count == 2
            assert result.failed_count == 0

    @pytest.mark.asyncio
    async def test_bulk_set_parent(self, sample_tickets: list[Ticket]) -> None:
        async with AsyncMockRallyClient(tickets=sample_tickets) as client:
            result = await client.bulk_set_parent(sample_tickets[:2], "F59625")
            assert result.success_count == 2
            assert result.failed_count == 0

    @pytest.mark.asyncio
    async def test_bulk_update_points(self, sample_tickets: list[Ticket]) -> None:
        async with AsyncMockRallyClient(tickets=sample_tickets) as client:
            result = await client.bulk_update_points(sample_tickets[:2], 3.0)
            assert result.success_count == 2
            assert result.failed_count == 0


class TestAsyncMockClientDiscussions:
    """Tests for discussion operations."""

    @pytest.mark.asyncio
    async def test_get_discussions(self) -> None:
        async with AsyncMockRallyClient() as client:
            # Default mock has sample discussions for US1234
            ticket = await client.get_ticket("US1234")
            if ticket:
                discussions = await client.get_discussions(ticket)
                # May or may not have discussions depending on mock data
                assert isinstance(discussions, list)

    @pytest.mark.asyncio
    async def test_add_comment(self, sample_tickets: list[Ticket]) -> None:
        async with AsyncMockRallyClient(
            tickets=sample_tickets,
            current_user="Test User",
        ) as client:
            ticket = sample_tickets[0]
            discussion = await client.add_comment(ticket, "Test comment")
            assert discussion is not None
            assert discussion.text == "Test comment"
            assert discussion.user == "Test User"


class TestAsyncMockClientAttachments:
    """Tests for attachment operations."""

    @pytest.mark.asyncio
    async def test_get_attachments(self) -> None:
        async with AsyncMockRallyClient() as client:
            ticket = await client.get_ticket("US1234")
            if ticket:
                attachments = await client.get_attachments(ticket)
                # Default mock has sample attachments
                assert isinstance(attachments, list)

    @pytest.mark.asyncio
    async def test_download_embedded_image(self, tmp_path) -> None:
        async with AsyncMockRallyClient() as client:
            dest = tmp_path / "test.png"
            result = await client.download_embedded_image(
                "https://example.com/image.png",
                str(dest),
            )
            assert result is True
            assert dest.exists()
