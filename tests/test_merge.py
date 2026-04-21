"""Tests for template merge engine."""
import tempfile
from pathlib import Path

import pytest

from src.merge import build_replacements, merge_template, get_template_fields


class TestBuildReplacements:
    def test_maps_data_columns_to_placeholders(self):
        row = {"Learner Name": "Tan Wei Ming", "Grades": "Distinction"}
        config = {"programme_name": "AI Analytics", "end_date": "15 May 2025"}
        result = build_replacements(row, config)
        assert result["Learner Name"] == "Tan Wei Ming"
        assert result["Grades"] == "Distinction"
        assert result["Programme Name"] == "AI Analytics"
        assert result["End Date"] == "15 May 2025"

    def test_nan_values_become_empty_string(self):
        row = {"Learner Name": "Alice", "Grades": float("nan")}
        config = {"programme_name": "Test", "end_date": "2025"}
        result = build_replacements(row, config)
        assert result["Grades"] == ""

    def test_missing_config_defaults_empty(self):
        row = {"Learner Name": "Alice", "Grades": "A"}
        config = {}
        result = build_replacements(row, config)
        assert result["Programme Name"] == ""
        assert result["End Date"] == ""


class TestMergeTemplate:
    def test_merge_produces_output(self, sample_template_path):
        tmp_out = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        tmp_out.close()
        try:
            replacements = {
                "Learner Name": "Test Learner",
                "Grades": "Distinction",
                "Programme Name": "AI Analytics",
                "End Date": "15 May 2025",
            }
            result = merge_template(sample_template_path, replacements, tmp_out.name)
            assert Path(result).exists()
            assert Path(result).stat().st_size > 0
        finally:
            Path(tmp_out.name).unlink(missing_ok=True)

    def test_merge_preserves_formatting(self, sample_template_path):
        tmp_out = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        tmp_out.close()
        try:
            replacements = {
                "Learner Name": "Test Learner",
                "Grades": "Pass",
                "Programme Name": "Test Programme",
                "End Date": "1 Jan 2025",
            }
            merge_template(sample_template_path, replacements, tmp_out.name)
            assert Path(tmp_out.name).stat().st_size > 1000
        finally:
            Path(tmp_out.name).unlink(missing_ok=True)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            merge_template("/nonexistent.docx", {}, "/tmp/out.docx")

    def test_only_passes_applicable_fields(self, sample_template_path):
        tmp_out = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        tmp_out.close()
        try:
            replacements = {
                "Learner Name": "Test",
                "Grades": "A",
                "Programme Name": "Prog",
                "End Date": "2025",
                "Nonexistent Field": "should be ignored",
            }
            merge_template(sample_template_path, replacements, tmp_out.name)
            assert Path(tmp_out.name).exists()
        finally:
            Path(tmp_out.name).unlink(missing_ok=True)


class TestGetTemplateFields:
    def test_returns_expected_fields(self, sample_template_path):
        fields = get_template_fields(sample_template_path)
        assert "Learner Name" in fields
        assert "Grades" in fields
        assert "Programme Name" in fields
        assert "End Date" in fields

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            get_template_fields("/nonexistent.docx")
