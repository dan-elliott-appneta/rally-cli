"""Attachments screen for viewing, downloading, and uploading attachments."""

from dataclasses import dataclass
from typing import NamedTuple
from urllib.parse import urlparse

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Input, Label, Static

from rally_tui.models import Attachment, Ticket
from rally_tui.services.protocol import RallyClientProtocol
from rally_tui.user_settings import UserSettings
from rally_tui.utils import extract_images_from_html
from rally_tui.utils.keybindings import VIM_KEYBINDINGS


@dataclass(frozen=True)
class EmbeddedImage:
    """Represents an image embedded in ticket description/notes."""

    url: str
    alt: str

    @property
    def name(self) -> str:
        """Extract filename from URL or use alt text."""
        if self.alt:
            return self.alt[:30]
        # Extract filename from URL path
        path = urlparse(self.url).path
        if path:
            parts = path.rstrip("/").split("/")
            if parts:
                return parts[-1][:30]
        return "embedded_image"

    @property
    def display_line(self) -> str:
        """Formatted line for list display."""
        return f"{self.name:<30} [embedded]    image"


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


class EmbeddedImageItem(Static):
    """Widget for displaying an embedded image."""

    DEFAULT_CSS = """
    EmbeddedImageItem {
        height: 3;
        padding: 0 2;
        background: $surface;
        margin: 0 0 1 0;
    }

    EmbeddedImageItem:hover {
        background: $primary-lighten-2;
    }
    """

    def __init__(self, image: EmbeddedImage, number: int) -> None:
        super().__init__()
        self._image = image
        self._number = number

    @property
    def image(self) -> EmbeddedImage:
        return self._image

    @property
    def number(self) -> int:
        return self._number

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(
                f"[{self._number}] {self._image.name:<30} "
                f"{'[embedded]':>10}    image"
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

    action: str  # "download", "upload", "download_embedded", "cancel"
    ticket: Ticket
    attachment: Attachment | None = None
    embedded_image: EmbeddedImage | None = None
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
        user_settings: UserSettings | None = None,
    ) -> None:
        super().__init__(name=name)
        self._ticket = ticket
        self._client = client
        self._attachments: list[Attachment] = []
        self._embedded_images: list[EmbeddedImage] = []
        self._all_items: list[Attachment | EmbeddedImage] = []
        self._upload_mode = False
        self._user_settings = user_settings

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
        # Apply vim keybindings
        self._apply_keybindings()
        # Load attachments
        self._load_attachments()

    def _apply_keybindings(self) -> None:
        """Apply vim-style keybindings for navigation."""
        if self._user_settings:
            keybindings = self._user_settings.keybindings
        else:
            keybindings = VIM_KEYBINDINGS

        navigation_bindings = {
            "navigation.down": "scroll_down",
            "navigation.up": "scroll_up",
            "navigation.top": "scroll_top",
            "navigation.bottom": "scroll_bottom",
        }

        for action_id, handler in navigation_bindings.items():
            if action_id in keybindings:
                key = keybindings[action_id]
                self._bindings.bind(key, handler, show=False)

    def action_scroll_down(self) -> None:
        """Scroll attachments container down."""
        container = self.query_one("#attachments-container", VerticalScroll)
        container.scroll_down()

    def action_scroll_up(self) -> None:
        """Scroll attachments container up."""
        container = self.query_one("#attachments-container", VerticalScroll)
        container.scroll_up()

    def action_scroll_top(self) -> None:
        """Scroll attachments container to top."""
        container = self.query_one("#attachments-container", VerticalScroll)
        container.scroll_home()

    def action_scroll_bottom(self) -> None:
        """Scroll attachments container to bottom."""
        container = self.query_one("#attachments-container", VerticalScroll)
        container.scroll_end()

    def _load_attachments(self) -> None:
        """Load attachments and embedded images from the client."""
        container = self.query_one("#attachments-container")
        container.remove_children()

        # Load regular attachments
        self._attachments = self._client.get_attachments(self._ticket)

        # Extract embedded images from description and notes
        self._embedded_images = []
        for html_content in [self._ticket.description, self._ticket.notes]:
            if html_content:
                images = extract_images_from_html(html_content)
                for img in images:
                    self._embedded_images.append(
                        EmbeddedImage(url=img["src"], alt=img["alt"])
                    )

        # Combine all items for numbered access
        self._all_items = list(self._attachments) + list(self._embedded_images)

        if not self._all_items:
            container.mount(
                Static("No attachments or embedded images.", id="no-attachments")
            )
        else:
            number = 1
            # Show regular attachments first
            for att in self._attachments:
                container.mount(AttachmentItem(att, number))
                number += 1
            # Then show embedded images
            for img in self._embedded_images:
                container.mount(EmbeddedImageItem(img, number))
                number += 1

    def _download_attachment(self, number: int) -> None:
        """Request download of attachment or embedded image by number."""
        if 1 <= number <= len(self._all_items):
            item = self._all_items[number - 1]
            if isinstance(item, Attachment):
                result = AttachmentsResult(
                    action="download",
                    ticket=self._ticket,
                    attachment=item,
                )
            else:
                # It's an EmbeddedImage
                result = AttachmentsResult(
                    action="download_embedded",
                    ticket=self._ticket,
                    embedded_image=item,
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
