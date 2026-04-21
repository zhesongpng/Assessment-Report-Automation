"""Tests for template validation and merge field detection."""
import io
import tempfile
from pathlib import Path

import pytest

from src.template import detect_merge_fields, validate_template


class FakeUploadedFile:
    """Minimal stub matching Streamlit UploadedFile interface."""
    def __init__(self, name, content):
        self.name = name
        self._content = content

    def getvalue(self):
        return self._content


class TestDetectMergeFields:
    def test_detects_fields_in_real_template(self, sample_template_path):
        fields = detect_merge_fields(sample_template_path)
        assert isinstance(fields, list)
        assert "Learner_Name" in fields
        assert "Grades" in fields
        assert "Programme_Name" in fields
        assert "End_Date" in fields

    def test_returns_sorted_list(self, sample_template_path):
        fields = detect_merge_fields(sample_template_path)
        assert fields == sorted(fields)


class TestValidateTemplate:
    def test_valid_template(self, sample_template_path):
        content = Path(sample_template_path).read_bytes()
        f = FakeUploadedFile("report.docx", content)
        result = validate_template(f)
        assert result["valid"] is True
        assert len(result["fields"]) >= 4
        assert result["error"] is None

    def test_non_docx_file(self):
        f = FakeUploadedFile("report.pdf", b"not a docx")
        result = validate_template(f)
        assert result["valid"] is False
        assert ".docx" in result["error"]

    def test_empty_file(self):
        f = FakeUploadedFile("report.docx", b"")
        result = validate_template(f)
        assert result["valid"] is False
        assert "empty" in result["error"].lower()

    def test_none_file(self):
        result = validate_template(None)
        assert result["valid"] is False

    def test_corrupted_docx(self):
        f = FakeUploadedFile("report.docx", b"this is not a real docx file at all")
        result = validate_template(f)
        assert result["valid"] is False
