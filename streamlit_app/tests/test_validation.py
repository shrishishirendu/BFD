"""Tests for validation_service."""

import pandas as pd
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.validation_service import (
    validate_required_columns,
    validate_rows,
    get_validation_summary,
    get_valid_indices,
    check_placeholder_coverage,
)


def _make_df(data: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(data)


class TestValidateRequiredColumns:
    def test_all_present(self):
        df = _make_df([{"Name": "Alice", "Email": "a@b.com"}])
        assert validate_required_columns(df) == []

    def test_missing_email(self):
        df = _make_df([{"Name": "Alice"}])
        assert "email" in validate_required_columns(df)

    def test_missing_name(self):
        df = _make_df([{"Email": "a@b.com"}])
        assert "name" in validate_required_columns(df)

    def test_both_missing(self):
        df = _make_df([{"Organisation": "Org"}])
        missing = validate_required_columns(df)
        assert "name" in missing
        assert "email" in missing


class TestValidateRows:
    def test_valid_rows(self):
        df = _make_df([
            {"Name": "Alice", "Email": "alice@example.com"},
            {"Name": "Bob", "Email": "bob@example.com"},
        ])
        result = validate_rows(df)
        assert all(result["status"] == "Valid")

    def test_empty_name(self):
        df = _make_df([{"Name": "", "Email": "a@b.com"}])
        result = validate_rows(df)
        assert result.iloc[0]["status"] == "Invalid"
        assert "Name is empty" in result.iloc[0]["errors"]

    def test_empty_email(self):
        df = _make_df([{"Name": "Alice", "Email": ""}])
        result = validate_rows(df)
        assert result.iloc[0]["status"] == "Invalid"
        assert "Email is empty" in result.iloc[0]["errors"]

    def test_invalid_email_format(self):
        df = _make_df([{"Name": "Alice", "Email": "not-an-email"}])
        result = validate_rows(df)
        assert result.iloc[0]["status"] == "Invalid"
        assert "Invalid email" in result.iloc[0]["errors"]

    def test_duplicate_emails(self):
        df = _make_df([
            {"Name": "Alice", "Email": "same@example.com"},
            {"Name": "Bob", "Email": "same@example.com"},
        ])
        result = validate_rows(df)
        assert result.iloc[0]["status"] == "Valid"
        assert "Duplicate" in result.iloc[1]["errors"]


class TestValidationSummary:
    def test_summary_counts(self):
        df = _make_df([
            {"Name": "Alice", "Email": "alice@example.com"},
            {"Name": "", "Email": "bob@example.com"},
            {"Name": "Carol", "Email": "alice@example.com"},
        ])
        vdf = validate_rows(df)
        summary = get_validation_summary(vdf)
        assert summary["total"] == 3
        assert summary["valid"] == 1
        assert summary["invalid"] == 2
        assert summary["duplicates"] == 1


class TestGetValidIndices:
    def test_returns_correct_indices(self):
        df = _make_df([
            {"Name": "Alice", "Email": "alice@example.com"},
            {"Name": "", "Email": "bob@example.com"},
            {"Name": "Carol", "Email": "carol@example.com"},
        ])
        vdf = validate_rows(df)
        indices = get_valid_indices(df, vdf)
        assert 0 in indices
        assert 1 not in indices
        assert 2 in indices


class TestPlaceholderCoverage:
    def test_all_covered(self):
        missing = check_placeholder_coverage(
            ["name", "email"], ["name", "email"], []
        )
        assert missing == []

    def test_covered_by_global(self):
        missing = check_placeholder_coverage(
            ["name", "event_name"], ["name"], ["event_name"]
        )
        assert missing == []

    def test_missing_placeholder(self):
        missing = check_placeholder_coverage(
            ["name", "venue"], ["name"], []
        )
        assert "venue" in missing
