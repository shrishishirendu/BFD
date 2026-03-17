"""Tests for template_service and placeholder_utils."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.placeholder_utils import (
    extract_placeholders_from_text,
    merge_text_with_context,
    find_missing_placeholders,
)


class TestExtractPlaceholders:
    def test_basic_extraction(self):
        text = "Hello {{ name }}, welcome to {{ event_name }}."
        result = extract_placeholders_from_text(text)
        assert "name" in result
        assert "event_name" in result

    def test_no_placeholders(self):
        assert extract_placeholders_from_text("No placeholders here.") == []

    def test_duplicate_placeholders(self):
        text = "{{ name }} and {{ name }} again"
        result = extract_placeholders_from_text(text)
        assert result.count("name") == 1

    def test_tight_spacing(self):
        text = "Hello {{name}}, welcome."
        result = extract_placeholders_from_text(text)
        assert "name" in result

    def test_extra_spacing(self):
        text = "Hello {{   name   }}, welcome."
        result = extract_placeholders_from_text(text)
        assert "name" in result


class TestMergeText:
    def test_basic_merge(self):
        text = "Dear {{ name }}, your event is {{ event_name }}."
        context = {"name": "Alice", "event_name": "Gala"}
        result = merge_text_with_context(text, context)
        assert "Alice" in result
        assert "Gala" in result

    def test_unmatched_placeholder_preserved(self):
        text = "Hello {{ name }}, venue is {{ venue }}."
        context = {"name": "Bob"}
        result = merge_text_with_context(text, context)
        assert "Bob" in result
        assert "{{ venue }}" in result

    def test_case_insensitive_keys(self):
        text = "Hello {{ Name }}."
        context = {"name": "Carol"}
        result = merge_text_with_context(text, context)
        assert "Carol" in result


class TestFindMissingPlaceholders:
    def test_none_missing(self):
        assert find_missing_placeholders(["name"], ["name", "email"]) == []

    def test_some_missing(self):
        result = find_missing_placeholders(["name", "venue"], ["name"])
        assert "venue" in result
