"""Tests for the Attachment model."""

import pytest

from rally_tui.models import Attachment


class TestAttachment:
    """Tests for Attachment dataclass."""

    def test_creation(self) -> None:
        """Test basic attachment creation."""
        attachment = Attachment(
            name="test.pdf",
            size=1024,
            content_type="application/pdf",
            object_id="12345",
        )
        assert attachment.name == "test.pdf"
        assert attachment.size == 1024
        assert attachment.content_type == "application/pdf"
        assert attachment.object_id == "12345"

    def test_immutability(self) -> None:
        """Test that Attachment is immutable (frozen)."""
        attachment = Attachment(
            name="test.pdf",
            size=1024,
            content_type="application/pdf",
            object_id="12345",
        )
        with pytest.raises(AttributeError):
            attachment.name = "other.pdf"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Test attachment equality."""
        a1 = Attachment(
            name="test.pdf",
            size=1024,
            content_type="application/pdf",
            object_id="12345",
        )
        a2 = Attachment(
            name="test.pdf",
            size=1024,
            content_type="application/pdf",
            object_id="12345",
        )
        assert a1 == a2

    def test_inequality(self) -> None:
        """Test attachment inequality."""
        a1 = Attachment(
            name="test.pdf",
            size=1024,
            content_type="application/pdf",
            object_id="12345",
        )
        a2 = Attachment(
            name="other.pdf",
            size=1024,
            content_type="application/pdf",
            object_id="12345",
        )
        assert a1 != a2


class TestFormattedSize:
    """Tests for formatted_size property."""

    def test_bytes(self) -> None:
        """Test size less than 1KB shows bytes."""
        attachment = Attachment(
            name="tiny.txt",
            size=512,
            content_type="text/plain",
            object_id="1",
        )
        assert attachment.formatted_size == "512 B"

    def test_zero_bytes(self) -> None:
        """Test zero bytes."""
        attachment = Attachment(
            name="empty.txt",
            size=0,
            content_type="text/plain",
            object_id="1",
        )
        assert attachment.formatted_size == "0 B"

    def test_kilobytes(self) -> None:
        """Test size in KB range."""
        attachment = Attachment(
            name="small.txt",
            size=2048,
            content_type="text/plain",
            object_id="1",
        )
        assert attachment.formatted_size == "2 KB"

    def test_kilobytes_boundary(self) -> None:
        """Test exactly 1KB."""
        attachment = Attachment(
            name="onekb.txt",
            size=1024,
            content_type="text/plain",
            object_id="1",
        )
        assert attachment.formatted_size == "1 KB"

    def test_megabytes(self) -> None:
        """Test size in MB range."""
        attachment = Attachment(
            name="large.pdf",
            size=1572864,  # 1.5 MB
            content_type="application/pdf",
            object_id="1",
        )
        assert attachment.formatted_size == "1.5 MB"

    def test_megabytes_boundary(self) -> None:
        """Test exactly 1MB."""
        attachment = Attachment(
            name="onemb.pdf",
            size=1024 * 1024,
            content_type="application/pdf",
            object_id="1",
        )
        assert attachment.formatted_size == "1.0 MB"

    def test_large_megabytes(self) -> None:
        """Test large MB size."""
        attachment = Attachment(
            name="huge.zip",
            size=50 * 1024 * 1024,  # 50 MB
            content_type="application/zip",
            object_id="1",
        )
        assert attachment.formatted_size == "50.0 MB"


class TestShortType:
    """Tests for short_type property."""

    def test_application_pdf(self) -> None:
        """Test application/pdf -> pdf."""
        attachment = Attachment(
            name="doc.pdf",
            size=1024,
            content_type="application/pdf",
            object_id="1",
        )
        assert attachment.short_type == "pdf"

    def test_image_png(self) -> None:
        """Test image/png -> png."""
        attachment = Attachment(
            name="image.png",
            size=1024,
            content_type="image/png",
            object_id="1",
        )
        assert attachment.short_type == "png"

    def test_text_plain(self) -> None:
        """Test text/plain -> plain."""
        attachment = Attachment(
            name="notes.txt",
            size=1024,
            content_type="text/plain",
            object_id="1",
        )
        assert attachment.short_type == "plain"

    def test_text_csv(self) -> None:
        """Test text/csv -> csv."""
        attachment = Attachment(
            name="data.csv",
            size=1024,
            content_type="text/csv",
            object_id="1",
        )
        assert attachment.short_type == "csv"

    def test_no_slash(self) -> None:
        """Test content type without slash returns as-is."""
        attachment = Attachment(
            name="file.bin",
            size=1024,
            content_type="octet-stream",
            object_id="1",
        )
        assert attachment.short_type == "octet-stream"

    def test_complex_type(self) -> None:
        """Test complex MIME type takes part after slash."""
        attachment = Attachment(
            name="doc.docx",
            size=1024,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            object_id="1",
        )
        # Takes everything after the first slash
        assert (
            attachment.short_type == "vnd.openxmlformats-officedocument.wordprocessingml.document"
        )


class TestDisplayLine:
    """Tests for display_line property."""

    def test_basic_display(self) -> None:
        """Test basic display line format."""
        attachment = Attachment(
            name="requirements.pdf",
            size=250880,  # ~245 KB
            content_type="application/pdf",
            object_id="1",
        )
        display = attachment.display_line
        assert "requirements.pdf" in display
        assert "245 KB" in display
        assert "pdf" in display

    def test_short_name_padding(self) -> None:
        """Test short names are padded."""
        attachment = Attachment(
            name="a.txt",
            size=100,
            content_type="text/plain",
            object_id="1",
        )
        display = attachment.display_line
        # Name should be left-padded to 30 chars
        assert display.startswith("a.txt")
        assert len(display.split()[0]) == 5  # Just the name part

    def test_display_alignment(self) -> None:
        """Test display line has consistent format."""
        attachment = Attachment(
            name="screenshot.png",
            size=91136,  # ~89 KB
            content_type="image/png",
            object_id="1",
        )
        display = attachment.display_line
        # Check the format has proper spacing
        assert "screenshot.png" in display
        assert "89 KB" in display
        assert "png" in display
