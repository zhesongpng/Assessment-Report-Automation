"""Tests for assessment data parsing and validation."""
import io

import pandas as pd
import pytest

from src.data import parse_data, validate_data, _find_column


class FakeUploadedFile:
    def __init__(self, name, content):
        self.name = name
        self._content = content

    def getvalue(self):
        return self._content


def _excel_file(df, name="data.xlsx"):
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return FakeUploadedFile(name, buf.read())


def _csv_file(df, name="data.csv"):
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return FakeUploadedFile(name, buf.read())


class TestParseData:
    def test_parses_real_excel(self, sample_data_path):
        content = open(sample_data_path, "rb").read()
        f = FakeUploadedFile("Assessment Result.xlsx", content)
        df = parse_data(f)
        assert len(df) >= 3
        assert "Learner Name" in df.columns or any("learner" in c.lower() for c in df.columns)

    def test_parses_csv(self):
        df = pd.DataFrame({
            "Learner Name": ["Alice", "Bob"],
            "Grades": ["Distinction", "Pass"],
        })
        f = _csv_file(df)
        result = parse_data(f)
        assert len(result) == 2
        assert "Learner Name" in result.columns

    def test_drops_unnamed_columns(self):
        df = pd.DataFrame({
            "Learner Name": ["Alice"],
            "Grades": ["A"],
            "Unnamed: 6": ["x"],
            "Unnamed: 7": ["y"],
        })
        f = _excel_file(df)
        result = parse_data(f)
        assert "Unnamed: 6" not in result.columns

    def test_strips_empty_rows(self):
        df = pd.DataFrame({
            "Learner Name": ["Alice", "Bob", None, None],
            "Grades": ["A", "B", None, None],
        })
        f = _excel_file(df)
        result = parse_data(f)
        assert len(result) == 2


class TestValidateData:
    def test_valid_data(self):
        df = pd.DataFrame({
            "Learner Name": ["Alice", "Bob"],
            "Grades": ["Distinction", "Pass"],
        })
        result = validate_data(df)
        assert result["valid"] is True
        assert result["row_count"] == 2

    def test_missing_learner_name_column(self):
        df = pd.DataFrame({"Grades": ["A"], "Name": ["Alice"]})
        result = validate_data(df)
        assert result["valid"] is False
        assert any("Learner Name" in e for e in result["errors"])

    def test_missing_grades_column(self):
        df = pd.DataFrame({"Learner Name": ["Alice"]})
        result = validate_data(df)
        assert result["valid"] is False
        assert any("Grades" in e for e in result["errors"])

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = validate_data(df)
        assert result["valid"] is False

    def test_empty_name_cells(self):
        df = pd.DataFrame({
            "Learner Name": ["Alice", None, "Charlie"],
            "Grades": ["A", "B", "C"],
        })
        result = validate_data(df)
        assert any("no name" in e.lower() for e in result["errors"])

    def test_duplicate_names(self):
        df = pd.DataFrame({
            "Learner Name": ["Alice", "Alice"],
            "Grades": ["A", "B"],
        })
        result = validate_data(df)
        assert any("duplicate" in w.lower() for w in result["warnings"])


class TestFindColumn:
    def test_exact_match(self):
        df = pd.DataFrame({"Learner Name": [1]})
        assert _find_column(df, "Learner Name") == "Learner Name"

    def test_case_insensitive(self):
        df = pd.DataFrame({"learner name": [1]})
        assert _find_column(df, "Learner Name") == "learner name"

    def test_no_match(self):
        df = pd.DataFrame({"Email": [1]})
        assert _find_column(df, "Learner Name") is None
