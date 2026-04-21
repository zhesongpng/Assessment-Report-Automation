"""Tests for file naming module."""
import pytest

from src.naming import (
    sanitize_filename,
    validate_filename_length,
    generate_filename,
    check_duplicates,
    generate_all_filenames,
    DEFAULT_PATTERN,
)
import pandas as pd


class TestSanitizeFilename:
    def test_removes_invalid_chars(self):
        assert sanitize_filename('test<>file') == "test--file"

    def test_strips_whitespace(self):
        assert sanitize_filename("  test  ") == "test"

    def test_collapses_multiple_spaces(self):
        assert sanitize_filename("test   file") == "test file"

    def test_normal_name_unchanged(self):
        assert sanitize_filename("Alice_Tan.pdf") == "Alice_Tan.pdf"

    def test_removes_path_traversal(self):
        assert ".." not in sanitize_filename("../../etc/passwd.pdf")
        assert ".." not in sanitize_filename("test..file.pdf")

    def test_removes_double_dot_sequences(self):
        result = sanitize_filename("name_with..dots.pdf")
        assert ".." not in result


class TestValidateFilenameLength:
    def test_short_name_unchanged(self):
        assert validate_filename_length("short.pdf") == "short.pdf"

    def test_truncates_long_name(self):
        long_name = "a" * 300 + ".pdf"
        result = validate_filename_length(long_name)
        assert len(result) <= 200

    def test_no_extension(self):
        long_name = "b" * 300
        result = validate_filename_length(long_name)
        assert len(result) <= 200


class TestGenerateFilename:
    def test_default_pattern(self):
        row = {"Learner Name": "Alice Tan", "Grades": "Distinction"}
        result = generate_filename(DEFAULT_PATTERN, row, "AI Analytics")
        assert "Alice Tan" in result
        assert "AI Analytics" in result
        assert result.endswith(".pdf")

    def test_special_chars_sanitized(self):
        row = {"Learner Name": "O'Brien/Test", "Grades": "A"}
        result = generate_filename(DEFAULT_PATTERN, row, "Programme")
        assert "/" not in result

    def test_empty_name_raises(self):
        row = {"Learner Name": None, "Grades": "A"}
        with pytest.raises(ValueError, match="empty"):
            generate_filename(DEFAULT_PATTERN, row, "Programme")

    def test_nan_name_raises(self):
        row = {"Learner Name": float("nan"), "Grades": "A"}
        with pytest.raises(ValueError):
            generate_filename(DEFAULT_PATTERN, row, "Programme")


class TestCheckDuplicates:
    def test_no_duplicates(self):
        result = check_duplicates(["a.pdf", "b.pdf", "c.pdf"])
        assert result == ["a.pdf", "b.pdf", "c.pdf"]

    def test_two_duplicates(self):
        result = check_duplicates(["a.pdf", "a.pdf"])
        assert result[0] == "a.pdf"
        assert result[1] == "a_2.pdf"

    def test_three_duplicates(self):
        result = check_duplicates(["a.pdf", "a.pdf", "a.pdf"])
        assert result[0] == "a.pdf"
        assert result[1] == "a_2.pdf"
        assert result[2] == "a_3.pdf"


class TestGenerateAllFilenames:
    def test_generates_for_all_rows(self):
        df = pd.DataFrame({
            "Learner Name": ["Alice", "Bob", "Charlie"],
            "Grades": ["A", "B", "C"],
        })
        names, errors, warnings = generate_all_filenames(DEFAULT_PATTERN, df, "Prog")
        assert len(names) == 3
        assert len(errors) == 0

    def test_skips_empty_names(self):
        df = pd.DataFrame({
            "Learner Name": ["Alice", None, "Charlie"],
            "Grades": ["A", "B", "C"],
        })
        names, errors, warnings = generate_all_filenames(DEFAULT_PATTERN, df, "Prog")
        assert len(errors) == 1
        assert len(names) == 2

    def test_warns_on_duplicates(self):
        df = pd.DataFrame({
            "Learner Name": ["Alice", "Alice"],
            "Grades": ["A", "B"],
        })
        names, errors, warnings = generate_all_filenames(DEFAULT_PATTERN, df, "Prog")
        assert len(warnings) > 0
        assert "_2." in names[1]
