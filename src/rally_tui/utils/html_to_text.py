"""HTML to plain text conversion utility."""

import html
import re
from html.parser import HTMLParser


class _HTMLToTextParser(HTMLParser):
    """Parser that converts HTML to plain text."""

    def __init__(self) -> None:
        super().__init__()
        self._text_parts: list[str] = []
        self._in_block = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Handle opening tags."""
        # Block elements that need line breaks
        if tag in ("p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "tr"):
            if self._text_parts and not self._text_parts[-1].endswith("\n"):
                self._text_parts.append("\n")
        # List items get bullet points
        elif tag == "li":
            if self._text_parts and not self._text_parts[-1].endswith("\n"):
                self._text_parts.append("\n")
            self._text_parts.append("  - ")

    def handle_endtag(self, tag: str) -> None:
        """Handle closing tags."""
        # Add line break after block elements
        if tag in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "table"):
            if self._text_parts and not self._text_parts[-1].endswith("\n"):
                self._text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        """Handle text content."""
        self._text_parts.append(data)

    def get_text(self) -> str:
        """Get the extracted plain text."""
        return "".join(self._text_parts)


def html_to_text(html_content: str) -> str:
    """Convert HTML to plain text for terminal display.

    Handles common HTML elements from Rally descriptions:
    - Strips all HTML tags
    - Converts <br>, <p>, <div> to line breaks
    - Converts <li> items to bullet points
    - Decodes HTML entities (&nbsp;, &amp;, etc.)
    - Normalizes whitespace

    Args:
        html_content: HTML string from Rally description field.

    Returns:
        Plain text suitable for terminal display.
    """
    if not html_content:
        return ""

    # Parse HTML and extract text
    parser = _HTMLToTextParser()
    try:
        parser.feed(html_content)
        text = parser.get_text()
    except Exception:
        # Fallback: strip tags with regex if parsing fails
        text = re.sub(r"<[^>]+>", " ", html_content)

    # Decode HTML entities
    text = html.unescape(text)

    # Normalize whitespace: collapse multiple spaces, preserve line breaks
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        # Collapse multiple spaces into one
        cleaned = re.sub(r"[ \t]+", " ", line).strip()
        cleaned_lines.append(cleaned)

    # Join lines, collapse multiple blank lines into one
    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
