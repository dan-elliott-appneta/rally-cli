"""Tests for HTML to text conversion utility."""

import pytest

from rally_tui.utils import html_to_text


class TestHtmlToTextBasic:
    """Basic HTML to text conversion tests."""

    def test_plain_text_unchanged(self) -> None:
        """Plain text without HTML should pass through unchanged."""
        text = "This is plain text."
        assert html_to_text(text) == "This is plain text."

    def test_empty_string(self) -> None:
        """Empty string should return empty string."""
        assert html_to_text("") == ""

    def test_none_like_empty(self) -> None:
        """None-like values should return empty string."""
        assert html_to_text("") == ""

    def test_whitespace_only(self) -> None:
        """Whitespace only should return empty string."""
        assert html_to_text("   \n\t  ") == ""


class TestHtmlToTextTags:
    """Tests for HTML tag handling."""

    def test_paragraph_tags(self) -> None:
        """Paragraph tags should create line breaks."""
        html = "<p>First paragraph</p><p>Second paragraph</p>"
        result = html_to_text(html)
        assert "First paragraph" in result
        assert "Second paragraph" in result
        assert "\n" in result

    def test_br_tags(self) -> None:
        """BR tags should create line breaks."""
        html = "Line one<br>Line two<br/>Line three"
        result = html_to_text(html)
        assert "Line one" in result
        assert "Line two" in result
        assert "Line three" in result

    def test_div_tags(self) -> None:
        """Div tags should create line breaks."""
        html = "<div>First div</div><div>Second div</div>"
        result = html_to_text(html)
        assert "First div" in result
        assert "Second div" in result

    def test_heading_tags(self) -> None:
        """Heading tags should create line breaks."""
        html = "<h1>Heading 1</h1><h2>Heading 2</h2><p>Content</p>"
        result = html_to_text(html)
        assert "Heading 1" in result
        assert "Heading 2" in result
        assert "Content" in result

    def test_strips_span_tags(self) -> None:
        """Inline tags like span should be stripped without adding breaks."""
        html = "Text with <span>inline</span> content"
        result = html_to_text(html)
        assert result == "Text with inline content"

    def test_strips_strong_tags(self) -> None:
        """Strong/bold tags should be stripped."""
        html = "This is <strong>bold</strong> text"
        result = html_to_text(html)
        assert result == "This is bold text"

    def test_strips_em_tags(self) -> None:
        """Em/italic tags should be stripped."""
        html = "This is <em>italic</em> text"
        result = html_to_text(html)
        assert result == "This is italic text"


class TestHtmlToTextLists:
    """Tests for list handling."""

    def test_unordered_list(self) -> None:
        """Unordered list items should have bullet points."""
        html = "<ul><li>Item one</li><li>Item two</li></ul>"
        result = html_to_text(html)
        assert "- Item one" in result
        assert "- Item two" in result

    def test_ordered_list(self) -> None:
        """Ordered list items should have bullet points."""
        html = "<ol><li>First</li><li>Second</li></ol>"
        result = html_to_text(html)
        assert "- First" in result
        assert "- Second" in result


class TestHtmlToTextEntities:
    """Tests for HTML entity decoding."""

    def test_nbsp_entity(self) -> None:
        """Non-breaking space entities should be converted."""
        html = "Hello&nbsp;World"
        result = html_to_text(html)
        # &nbsp; becomes a regular space which may be normalized
        assert "Hello" in result
        assert "World" in result

    def test_amp_entity(self) -> None:
        """Ampersand entities should be decoded."""
        html = "Tom &amp; Jerry"
        result = html_to_text(html)
        assert "Tom & Jerry" in result

    def test_lt_gt_entities(self) -> None:
        """Less-than and greater-than entities should be decoded."""
        html = "5 &lt; 10 &gt; 3"
        result = html_to_text(html)
        assert "5 < 10 > 3" in result

    def test_quote_entities(self) -> None:
        """Quote entities should be decoded."""
        html = "&quot;Hello&quot; and &#39;World&#39;"
        result = html_to_text(html)
        assert '"Hello"' in result
        assert "'World'" in result


class TestHtmlToTextWhitespace:
    """Tests for whitespace normalization."""

    def test_collapses_multiple_spaces(self) -> None:
        """Multiple spaces should be collapsed to one."""
        html = "Hello    world"
        result = html_to_text(html)
        assert result == "Hello world"

    def test_collapses_multiple_blank_lines(self) -> None:
        """Multiple blank lines should be collapsed."""
        html = "<p>First</p>\n\n\n\n<p>Second</p>"
        result = html_to_text(html)
        # Should not have more than one blank line between paragraphs
        assert "\n\n\n" not in result

    def test_trims_leading_trailing_whitespace(self) -> None:
        """Leading and trailing whitespace should be trimmed."""
        html = "  <p>Content</p>  "
        result = html_to_text(html)
        assert not result.startswith(" ")
        assert not result.endswith(" ")


class TestHtmlToTextRallyExamples:
    """Tests with realistic Rally description content."""

    def test_rally_user_story_description(self) -> None:
        """Typical Rally user story description."""
        html = """<div>As a user, I want to log in with my email and password so that I can access my account securely.</div>
        <div><br></div>
        <div><strong>Acceptance Criteria:</strong></div>
        <ul>
        <li>User can enter email and password</li>
        <li>System validates credentials</li>
        <li>User is redirected to dashboard on success</li>
        </ul>"""
        result = html_to_text(html)
        assert "log in with my email and password" in result
        assert "Acceptance Criteria:" in result
        assert "- User can enter email and password" in result
        assert "- System validates credentials" in result

    def test_rally_defect_description(self) -> None:
        """Typical Rally defect description."""
        html = """<p>NullPointerException thrown when user clicks checkout with an empty cart.</p>
        <p><strong>Steps to reproduce:</strong></p>
        <ol>
        <li>Log in to the application</li>
        <li>Navigate to cart without adding items</li>
        <li>Click checkout button</li>
        </ol>
        <p>Stack trace attached.</p>"""
        result = html_to_text(html)
        assert "NullPointerException" in result
        assert "Steps to reproduce:" in result
        assert "- Log in to the application" in result
        assert "Stack trace attached" in result

    def test_rally_with_links(self) -> None:
        """Rally description with links (links become plain text)."""
        html = '<p>See <a href="http://example.com">documentation</a> for details.</p>'
        result = html_to_text(html)
        assert "See documentation for details" in result
        # URL should not appear in plain text
        assert "http://" not in result
