"""Tests for placeholder extraction from PDF-like content."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.placeholder_utils import (
    extract_placeholders_from_text,
    merge_text_with_context,
    PLACEHOLDER_PATTERN,
)
from utils.dataframe_utils import row_to_merge_dict, canonical_name
import pandas as pd


class TestPlaceholderPattern:
    def test_matches_standard(self):
        assert PLACEHOLDER_PATTERN.findall("{{ name }}") == ["name"]

    def test_matches_no_space(self):
        assert PLACEHOLDER_PATTERN.findall("{{email}}") == ["email"]

    def test_matches_underscored(self):
        assert PLACEHOLDER_PATTERN.findall("{{ event_name }}") == ["event_name"]

    def test_no_match_single_brace(self):
        assert PLACEHOLDER_PATTERN.findall("{ name }") == []

    def test_multiple_on_one_line(self):
        text = "{{ a }} and {{ b }}"
        assert sorted(PLACEHOLDER_PATTERN.findall(text)) == ["a", "b"]


class TestCanonicalName:
    def test_simple(self):
        assert canonical_name("Name") == "name"

    def test_with_spaces(self):
        assert canonical_name("  Event Name  ") == "event_name"


class TestRowToMergeDict:
    def test_basic_conversion(self):
        row = pd.Series({"Name": "Alice", "Email": "a@b.com", "Organisation": "Org"})
        result = row_to_merge_dict(row)
        assert result["name"] == "Alice"
        assert result["email"] == "a@b.com"
        assert result["organisation"] == "Org"


class TestMergeIntegration:
    def test_full_merge_flow(self):
        template_text = (
            "Dear {{ name }},\n"
            "You are invited to {{ event_name }} on {{ event_date }}.\n"
            "Venue: {{ venue }}\n"
            "RSVP: {{ rsvp_link }}\n"
        )
        row = pd.Series({"Name": "Dr Kumar", "Email": "kumar@example.com"})
        row_ctx = row_to_merge_dict(row)
        global_ctx = {
            "event_name": "Annual Gala",
            "event_date": "1 April 2026",
            "venue": "Grand Hall",
            "rsvp_link": "https://example.com/rsvp",
        }
        context = {**global_ctx, **row_ctx}
        result = merge_text_with_context(template_text, context)

        assert "Dr Kumar" in result
        assert "Annual Gala" in result
        assert "Grand Hall" in result
        assert "https://example.com/rsvp" in result
        assert "{{ " not in result  # All placeholders should be replaced
