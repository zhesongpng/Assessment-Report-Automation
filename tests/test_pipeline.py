"""Tests for the processing pipeline orchestrator."""
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.pdf import check_libreoffice
from src.pipeline import process_batch, cleanup_session

HAS_LIBREOFFICE = check_libreoffice()


@pytest.fixture
def sample_config():
    return {
        "programme_name": "AI Powered Business Analytics",
        "end_date": "15 May 2025",
        "owner_password": "TestOwner123",
        "pattern": "{LearnerName}_{ProgrammeName}_AssessmentReport.pdf",
    }


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "Learner Name": ["Alice Tan", "Bob Lim", "Charlie Wong"],
        "Grades": ["Distinction", "Pass", "Credit"],
    })


class TestProcessBatch:
    @pytest.mark.skipif(
        not HAS_LIBREOFFICE,
        reason="LibreOffice not installed — cannot test full pipeline"
    )
    def test_full_pipeline(self, sample_template_path, sample_df, sample_config):
        result = process_batch(
            template_path=sample_template_path,
            data_df=sample_df,
            config=sample_config,
        )
        assert result["success_count"] == 3
        assert result["error_count"] == 0
        assert len(result["filenames"]) == 3
        assert Path(result["zip_path"]).exists()

        # Cleanup
        cleanup_session(Path(result["zip_path"]).parent)

    @pytest.mark.skipif(
        not HAS_LIBREOFFICE,
        reason="LibreOffice not installed"
    )
    def test_progress_callback(self, sample_template_path, sample_df, sample_config):
        calls = []

        def callback(current, total, msg):
            calls.append((current, total, msg))

        result = process_batch(
            template_path=sample_template_path,
            data_df=sample_df,
            config=sample_config,
            progress_callback=callback,
        )
        assert len(calls) >= len(sample_df)
        cleanup_session(Path(result["zip_path"]).parent)

    def test_invalid_template_path(self, sample_df, sample_config):
        result = process_batch(
            template_path="/nonexistent.docx",
            data_df=sample_df,
            config=sample_config,
        )
        assert result["error_count"] > 0

    @pytest.mark.skipif(
        not HAS_LIBREOFFICE,
        reason="LibreOffice not installed"
    )
    def test_skips_empty_name_rows(self, sample_template_path, sample_config):
        df = pd.DataFrame({
            "Learner Name": ["Alice", None, "Charlie"],
            "Grades": ["A", "B", "C"],
        })
        result = process_batch(
            template_path=sample_template_path,
            data_df=df,
            config=sample_config,
        )
        assert result["success_count"] == 2
        assert result["error_count"] == 1
        cleanup_session(Path(result["zip_path"]).parent)
