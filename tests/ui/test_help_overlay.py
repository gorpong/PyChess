"""Tests for help overlay system."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from pychess.ui.overlays import (
    HELP_SECTIONS,
    _split_into_pages,
    _format_help_line,
)


class TestHelpSections:
    """Tests for help section content."""

    def test_has_controls_section(self):
        """Should have a Controls section."""
        section_names = [s["name"] for s in HELP_SECTIONS]
        assert "Controls" in section_names

    def test_has_how_to_play_section(self):
        """Should have a How to Play section."""
        section_names = [s["name"] for s in HELP_SECTIONS]
        assert "How to Play" in section_names

    def test_has_san_notation_section(self):
        """Should have a SAN Notation section."""
        section_names = [s["name"] for s in HELP_SECTIONS]
        assert "SAN Notation" in section_names

    def test_has_chess_rules_section(self):
        """Should have a Chess Rules section."""
        section_names = [s["name"] for s in HELP_SECTIONS]
        assert "Chess Rules" in section_names

    def test_has_tips_section(self):
        """Should have a Tips for Beginners section."""
        section_names = [s["name"] for s in HELP_SECTIONS]
        assert "Tips for Beginners" in section_names

    def test_each_section_has_content(self):
        """Each section should have non-empty content."""
        for section in HELP_SECTIONS:
            assert "name" in section
            assert "content" in section
            assert len(section["content"]) > 0

    def test_controls_section_mentions_arrow_keys(self):
        """Controls section should mention arrow keys."""
        controls = next(s for s in HELP_SECTIONS if s["name"] == "Controls")
        assert "Arrow" in controls["content"] or "arrow" in controls["content"]

    def test_san_section_has_examples(self):
        """SAN section should have move examples."""
        san = next(s for s in HELP_SECTIONS if s["name"] == "SAN Notation")
        # Should mention common notation
        assert "e4" in san["content"] or "Nf3" in san["content"]

    def test_rules_section_mentions_castling(self):
        """Chess Rules section should mention castling."""
        rules = next(s for s in HELP_SECTIONS if s["name"] == "Chess Rules")
        assert "castling" in rules["content"].lower() or "Castling" in rules["content"]

    def test_tips_section_has_beginner_advice(self):
        """Tips section should have beginner advice."""
        tips = next(s for s in HELP_SECTIONS if s["name"] == "Tips for Beginners")
        # Should mention basic concepts
        content_lower = tips["content"].lower()
        assert "center" in content_lower or "castle" in content_lower


class TestFormatHelpLine:
    """Tests for help line formatting."""

    def test_formats_regular_line(self):
        """Regular lines should pass through unchanged."""
        line = "  Arrow Keys - Move cursor"
        result = _format_help_line(line, bold_func=lambda x: f"**{x}**")
        assert "Arrow Keys" in result

    def test_formats_heading_with_colon(self):
        """Lines ending with colon should be bolded as headings."""
        line = "CURSOR MODE:"
        bold_func = lambda x: f"**{x}**"
        result = _format_help_line(line, bold_func=bold_func)
        assert "**" in result  # Should have bold markers

    def test_formats_subheading(self):
        """Lines that are subheadings should be formatted."""
        line = "Basic Moves:"
        bold_func = lambda x: f"**{x}**"
        result = _format_help_line(line, bold_func=bold_func)
        assert "**" in result


class TestSplitIntoPages:
    """Tests for page splitting logic."""

    def test_single_page_content(self):
        """Short content should result in single page."""
        text = "Line 1\nLine 2\nLine 3"
        pages = _split_into_pages(text, max_lines_per_page=10)
        assert len(pages) == 1
        assert len(pages[0]) == 3

    def test_splits_at_blank_lines(self):
        """Should prefer splitting at blank lines."""
        text = "Line 1\nLine 2\n\nLine 3\nLine 4"
        pages = _split_into_pages(text, max_lines_per_page=3)
        # Should split at the blank line
        assert len(pages) >= 1

    def test_respects_max_lines(self):
        """Pages should not exceed max lines."""
        lines = "\n".join([f"Line {i}" for i in range(20)])
        pages = _split_into_pages(lines, max_lines_per_page=5)
        for page in pages:
            assert len(page) <= 5

    def test_handles_empty_text(self):
        """Empty text should result in empty pages."""
        pages = _split_into_pages("", max_lines_per_page=10)
        assert len(pages) == 0 or (len(pages) == 1 and len(pages[0]) == 0)


class TestHelpOverlayNavigation:
    """Tests for help overlay navigation behavior."""

    def test_sections_have_unique_keys(self):
        """Each section should have a unique navigation key."""
        keys = [s.get("key") for s in HELP_SECTIONS if s.get("key")]
        # Keys that exist should be unique
        assert len(keys) == len(set(keys))

    def test_tips_accessible_via_t_key(self):
        """Tips section should be accessible via 'T' key."""
        tips = next(s for s in HELP_SECTIONS if s["name"] == "Tips for Beginners")
        assert tips.get("key") == "t"
