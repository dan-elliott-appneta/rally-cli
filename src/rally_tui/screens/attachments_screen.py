"""Attachments screen for viewing, downloading, and uploading attachments."""

from dataclasses import dataclass
from typing import NamedTuple

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Input, Label, Static

from rally_tui.models import Attachment, Ticket
from rally_tui.services.protocol import RallyClientProtocol


class AttachmentItem(Static):
    """Widget for displaying a single attachment."""

    DEFAULT_CSS = """
    AttachmentItem {
        height: 3;
        padding: 0 2;
        background: $surface;
        margin: 0 0 1 0;
    }

    AttachmentItem:hover {
        background: $primary-lighten-2;
    }

    AttachmentItem .attachment-number {
        width: 4;
        color: $primary;
        text-style: bold;
    }

    AttachmentItem .attachment-name {
        width: 32;
    }

    AttachmentItem .attachment-size {
        width: 12;
        text-align: right;
        color: $text-muted;
    }

    AttachmentItem .attachment-type {
        width: 16;
        color: $text-muted;
    }
    """

    def __init__(self, attachment: Attachment, number: int) -> None:
        super().__init__()
        self._attachment = attachment
        self._number = number

    @property
    def attachment(self) -> Attachment:
        return self._attachment

    @property
    def number(self) -> int:
        return self._number

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(
                f"[{self._number}] {self._attachment.name:<30} "
                f"{self._attachment.formatted_size:>10}    {self._attachment.short_type}"
            )


class DownloadRequest(NamedTuple):
    """Request to download an attachment."""

    ticket: Ticket
    attachment: Attachment


class UploadRequest(NamedTuple):
    """Request to upload a file as attachment."""

    ticket: Ticket
    file_path: str


@dataclass
class AttachmentsResult:
    """Result from the attachments screen."""

    action: str  # "download", "upload", "cancel"
    ticket: Ticket
    attachment: Attachment | None = None
    file_path: str | None = None


class AttachmentsScreen(ModalScreen[AttachmentsResult | None]):
    """Screen for viewing and managing ticket attachments."""

    BINDINGS = [
        Binding("escape", "cancel", "Close"),
        Binding("u", "upload", "Upload"),
        Binding("1", "download_1", "1", show=False),
        Binding("2", "download_2", "2", show=False),
        Binding("3", "download_3", "3", show=False),
        Binding("4", "download_4", "4", show=False),
        Binding("5", "download_5", "5", show=False),
        Binding("6", "download_6", "6", show=False),
        Binding("7", "download_7", "7", show=False),
        Binding("8", "download_8", "8", show=False),
        Binding("9", "download_9", "9", show=False),
    ]

    DEFAULT_CSS = """
    AttachmentsScreen {
        align: center middle;
    }

    #attachments-dialog {
        width: 70;
        height: auto;
        max-height: 24;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #attachments-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }

    #attachments-container {
        height: auto;
        max-height: 14;
    }

    #no-attachments {
        text-align: center;
        color: $text-muted;
        padding: 2;
    }

    #upload-container {
        height: auto;
        margin-top: 1;
        border-top: solid $primary;
        padding-top: 1;
    }

    #upload-label {
        margin-bottom: 1;
    }

    #upload-input {
        width: 100%;
    }

    #attachments-footer {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
        padding-top: 1;
        border-top: solid $primary-darken-2;
    }
    """

    class Downloaded(Message):
        """Message sent when an attachment is selected for download."""

        def __init__(self, ticket: Ticket, attachment: Attachment) -> None:
            super().__init__()
            self.ticket = ticket
            self.attachment = attachment

    class Uploaded(Message):
        """Message sent when a file is uploaded."""

        def __init__(self, ticket: Ticket, file_path: str) -> None:
            super().__init__()
            self.ticket = ticket
            self.file_path = file_path

    def __init__(
        self,
        ticket: Ticket,
        client: RallyClientProtocol,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._ticket = ticket
        self._client = client
        self._attachments: list[Attachment] = []
        self._upload_mode = False

    @property
    def ticket(self) -> Ticket:
        return self._ticket

    @property
    def attachments(self) -> list[Attachment]:
        return self._attachments

    def compose(self) -> ComposeResult:
        with Vertical(id="attachments-dialog"):
            yield Static(
                f"Attachments - {self._ticket.formatted_id}",
                id="attachments-title",
            )
            yield VerticalScroll(id="attachments-container")
            with Vertical(id="upload-container"):
                yield Static("Enter file path:", id="upload-label")
                yield Input(placeholder="/path/to/file", id="upload-input")
            yield Static(
                "[1-9] Download  [u] Upload  [Esc] Close",
                id="attachments-footer",
            )
        yield Footer()

    def on_mount(self) -> None:
        # Initially hide upload container
        self.query_one("#upload-container").display = False
        # Load attachments
        self._load_attachments()

    def _load_attachments(self) -> None:
        """Load attachments from the client."""
        container = self.query_one("#attachments-container")
        container.remove_children()

        self._attachments = self._client.get_attachments(self._ticket)

        if not self._attachments:
            container.mount(
                Static("No attachments on this ticket.", id="no-attachments")
            )
        else:
            for i, att in enumerate(self._attachments, start=1):
                container.mount(AttachmentItem(att, i))

    def _download_attachment(self, number: int) -> None:
        """Request download of attachment by number."""
        if 1 <= number <= len(self._attachments):
            attachment = self._attachments[number - 1]
            result = AttachmentsResult(
                action="download",
                ticket=self._ticket,
                attachment=attachment,
            )
            self.dismiss(result)

    def action_cancel(self) -> None:
        """Close the screen."""
        if self._upload_mode:
            # Just exit upload mode
            self._upload_mode = False
            self.query_one("#upload-container").display = False
            self.query_one("#upload-input", Input).value = ""
        else:
            self.dismiss(None)

    def action_upload(self) -> None:
        """Enter upload mode."""
        self._upload_mode = True
        self.query_one("#upload-container").display = True
        self.query_one("#upload-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle upload path submission."""
        file_path = event.value.strip()
        if file_path:
            result = AttachmentsResult(
                action="upload",
                ticket=self._ticket,
                file_path=file_path,
            )
            self.dismiss(result)

    def action_download_1(self) -> None:
        self._download_attachment(1)

    def action_download_2(self) -> None:
        self._download_attachment(2)

    def action_download_3(self) -> None:
        self._download_attachment(3)

    def action_download_4(self) -> None:
        self._download_attachment(4)

    def action_download_5(self) -> None:
        self._download_attachment(5)

    def action_download_6(self) -> None:
        self._download_attachment(6)

    def action_download_7(self) -> None:
        self._download_attachment(7)

    def action_download_8(self) -> None:
        self._download_attachment(8)

    def action_download_9(self) -> None:
        self._download_attachment(9)
