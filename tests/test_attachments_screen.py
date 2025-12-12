"""Tests for the AttachmentsScreen."""

from rally_tui.app import RallyTUI
from rally_tui.models import Attachment, Ticket
from rally_tui.screens import AttachmentsResult, AttachmentsScreen
from rally_tui.screens.attachments_screen import AttachmentItem
from rally_tui.services.mock_client import MockRallyClient


class TestAttachmentsScreenBasic:
    """Basic tests for AttachmentsScreen."""

    async def test_attachments_screen_shows_ticket_id(self) -> None:
        """Attachments screen should show ticket formatted ID in title."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
            object_id="100001",
        )
        client = MockRallyClient()

        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test():
            await app.push_screen(AttachmentsScreen(ticket, client))

            title = app.screen.query_one("#attachments-title")
            rendered = str(title.render())
            assert "US1234" in rendered

    async def test_attachments_screen_shows_no_attachments_message(self) -> None:
        """Attachments screen should show empty message when no attachments."""
        ticket = Ticket(
            formatted_id="US9999",
            name="No attachments",
            ticket_type="UserStory",
            state="Defined",
            object_id="999999",
        )
        client = MockRallyClient(attachments={})

        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test():
            await app.push_screen(AttachmentsScreen(ticket, client))

            no_attachments = app.screen.query_one("#no-attachments")
            rendered = str(no_attachments.render())
            assert "No attachments" in rendered

    async def test_attachments_screen_shows_attachments(self) -> None:
        """Attachments screen should display attachment items."""
        ticket = Ticket(
            formatted_id="TEST123",
            name="Test ticket",
            ticket_type="UserStory",
            state="Defined",
            object_id="123456",
        )
        attachments = {
            "TEST123": [
                Attachment(
                    name="doc.pdf",
                    size=1024,
                    content_type="application/pdf",
                    object_id="att_001",
                ),
                Attachment(
                    name="image.png",
                    size=2048,
                    content_type="image/png",
                    object_id="att_002",
                ),
            ]
        }
        client = MockRallyClient(attachments=attachments)

        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test():
            await app.push_screen(AttachmentsScreen(ticket, client))

            items = app.screen.query(AttachmentItem)
            assert len(items) == 2


class TestAttachmentsScreenNavigation:
    """Tests for AttachmentsScreen navigation."""

    async def test_escape_closes_screen(self) -> None:
        """Pressing Escape should close the attachments screen."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
            object_id="100001",
        )
        client = MockRallyClient()

        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(AttachmentsScreen(ticket, client))
            await pilot.pause()

            assert app.screen.__class__.__name__ == "AttachmentsScreen"

            await pilot.press("escape")
            await pilot.pause()

            assert app.screen.__class__.__name__ != "AttachmentsScreen"

    async def test_number_key_downloads_attachment(self) -> None:
        """Pressing a number key should select that attachment for download."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
            object_id="100001",
        )
        attachments = {
            "US1234": [
                Attachment(
                    name="first.pdf",
                    size=1024,
                    content_type="application/pdf",
                    object_id="att_001",
                ),
                Attachment(
                    name="second.png",
                    size=2048,
                    content_type="image/png",
                    object_id="att_002",
                ),
            ]
        }
        client = MockRallyClient(attachments=attachments)

        results = []

        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:

            def callback(result: AttachmentsResult | None) -> None:
                results.append(result)

            app.push_screen(AttachmentsScreen(ticket, client), callback)
            await pilot.pause()

            await pilot.press("1")
            await pilot.pause()

        assert len(results) == 1
        result = results[0]
        assert result is not None
        assert result.action == "download"
        assert result.attachment is not None
        assert result.attachment.name == "first.pdf"

    async def test_number_key_2_downloads_second_attachment(self) -> None:
        """Pressing '2' should select the second attachment."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
            object_id="100001",
        )
        attachments = {
            "US1234": [
                Attachment(
                    name="first.pdf",
                    size=1024,
                    content_type="application/pdf",
                    object_id="att_001",
                ),
                Attachment(
                    name="second.png",
                    size=2048,
                    content_type="image/png",
                    object_id="att_002",
                ),
            ]
        }
        client = MockRallyClient(attachments=attachments)

        results = []

        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:

            def callback(result: AttachmentsResult | None) -> None:
                results.append(result)

            app.push_screen(AttachmentsScreen(ticket, client), callback)
            await pilot.pause()

            await pilot.press("2")
            await pilot.pause()

        assert len(results) == 1
        result = results[0]
        assert result is not None
        assert result.action == "download"
        assert result.attachment is not None
        assert result.attachment.name == "second.png"

    async def test_invalid_number_key_does_nothing(self) -> None:
        """Pressing a number key beyond attachment count should do nothing."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
            object_id="100001",
        )
        attachments = {
            "US1234": [
                Attachment(
                    name="only.pdf",
                    size=1024,
                    content_type="application/pdf",
                    object_id="att_001",
                ),
            ]
        }
        client = MockRallyClient(attachments=attachments)

        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(AttachmentsScreen(ticket, client))
            await pilot.pause()

            assert app.screen.__class__.__name__ == "AttachmentsScreen"

            await pilot.press("5")
            await pilot.pause()

            # Should still be on attachments screen
            assert app.screen.__class__.__name__ == "AttachmentsScreen"


class TestAttachmentsScreenUpload:
    """Tests for AttachmentsScreen upload functionality."""

    async def test_u_key_shows_upload_input(self) -> None:
        """Pressing 'u' should show the upload input."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
            object_id="100001",
        )
        client = MockRallyClient()

        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(AttachmentsScreen(ticket, client))
            await pilot.pause()

            # Upload container should be hidden initially
            container = app.screen.query_one("#upload-container")
            assert container.display is False

            await pilot.press("u")
            await pilot.pause()

            # Upload container should now be visible
            assert container.display is True

    async def test_escape_in_upload_mode_hides_input(self) -> None:
        """Pressing Escape in upload mode should hide input, not close screen."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
            object_id="100001",
        )
        client = MockRallyClient()

        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(AttachmentsScreen(ticket, client))
            await pilot.pause()

            # Enter upload mode
            await pilot.press("u")
            await pilot.pause()

            container = app.screen.query_one("#upload-container")
            assert container.display is True

            # Press escape
            await pilot.press("escape")
            await pilot.pause()

            # Should still be on attachments screen but upload hidden
            assert app.screen.__class__.__name__ == "AttachmentsScreen"
            assert container.display is False

    async def test_upload_submission_returns_result(self) -> None:
        """Submitting upload path should return upload result."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
            object_id="100001",
        )
        client = MockRallyClient()

        results = []

        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:

            def callback(result: AttachmentsResult | None) -> None:
                results.append(result)

            app.push_screen(AttachmentsScreen(ticket, client), callback)
            await pilot.pause()

            # Enter upload mode
            await pilot.press("u")
            await pilot.pause()

            # Type file path
            input_widget = app.screen.query_one("#upload-input")
            input_widget.value = "/path/to/file.pdf"
            await pilot.pause()

            # Submit
            await pilot.press("enter")
            await pilot.pause()

        assert len(results) == 1
        result = results[0]
        assert result is not None
        assert result.action == "upload"
        assert result.file_path == "/path/to/file.pdf"
        assert result.ticket == ticket

    async def test_empty_upload_path_does_not_submit(self) -> None:
        """Empty upload path should not submit."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test ticket",
            ticket_type="UserStory",
            state="In-Progress",
            object_id="100001",
        )
        client = MockRallyClient()

        app = RallyTUI(client=client, show_splash=False)
        async with app.run_test() as pilot:
            app.push_screen(AttachmentsScreen(ticket, client))
            await pilot.pause()

            # Enter upload mode
            await pilot.press("u")
            await pilot.pause()

            # Submit with empty input
            await pilot.press("enter")
            await pilot.pause()

            # Should still be on attachments screen
            assert app.screen.__class__.__name__ == "AttachmentsScreen"


class TestAttachmentsScreenProperty:
    """Tests for AttachmentsScreen properties."""

    def test_ticket_property(self) -> None:
        """AttachmentsScreen should expose ticket property."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        client = MockRallyClient()
        screen = AttachmentsScreen(ticket, client)
        assert screen.ticket == ticket
        assert screen.ticket.formatted_id == "US1234"

    def test_attachments_property_initially_empty(self) -> None:
        """Attachments property should be empty before mount."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        client = MockRallyClient()
        screen = AttachmentsScreen(ticket, client)
        assert screen.attachments == []


class TestAttachmentItem:
    """Tests for AttachmentItem widget."""

    def test_attachment_item_stores_attachment(self) -> None:
        """AttachmentItem should store the attachment."""
        attachment = Attachment(
            name="test.pdf",
            size=1024,
            content_type="application/pdf",
            object_id="att_001",
        )
        item = AttachmentItem(attachment, 1)
        assert item.attachment == attachment

    def test_attachment_item_stores_number(self) -> None:
        """AttachmentItem should store the number."""
        attachment = Attachment(
            name="test.pdf",
            size=1024,
            content_type="application/pdf",
            object_id="att_001",
        )
        item = AttachmentItem(attachment, 3)
        assert item.number == 3


class TestAttachmentsScreenFromApp:
    """Tests for opening AttachmentsScreen from the main app."""

    async def test_a_key_opens_attachments_screen(self) -> None:
        """Pressing 'a' should open the attachments screen."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.press("a")
            await pilot.pause()

            assert app.screen.__class__.__name__ == "AttachmentsScreen"

    async def test_a_key_shows_attachments_for_selected_ticket(self) -> None:
        """Attachments screen should show the selected ticket ID."""
        app = RallyTUI(show_splash=False)
        async with app.run_test() as pilot:
            await pilot.press("a")
            await pilot.pause()

            title = app.screen.query_one("#attachments-title")
            rendered = str(title.render())
            # First ticket in sorted list (by most recent/highest ID)
            assert "US1237" in rendered


class TestAttachmentsResult:
    """Tests for AttachmentsResult dataclass."""

    def test_download_result(self) -> None:
        """Download result should have correct fields."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        attachment = Attachment(
            name="file.pdf",
            size=1024,
            content_type="application/pdf",
            object_id="att_001",
        )
        result = AttachmentsResult(
            action="download",
            ticket=ticket,
            attachment=attachment,
        )
        assert result.action == "download"
        assert result.ticket == ticket
        assert result.attachment == attachment
        assert result.file_path is None

    def test_upload_result(self) -> None:
        """Upload result should have correct fields."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        result = AttachmentsResult(
            action="upload",
            ticket=ticket,
            file_path="/path/to/file.pdf",
        )
        assert result.action == "upload"
        assert result.ticket == ticket
        assert result.attachment is None
        assert result.file_path == "/path/to/file.pdf"

    def test_cancel_result(self) -> None:
        """Cancel result should have correct fields."""
        ticket = Ticket(
            formatted_id="US1234",
            name="Test",
            ticket_type="UserStory",
            state="Defined",
        )
        result = AttachmentsResult(
            action="cancel",
            ticket=ticket,
        )
        assert result.action == "cancel"
        assert result.ticket == ticket
        assert result.attachment is None
        assert result.file_path is None
