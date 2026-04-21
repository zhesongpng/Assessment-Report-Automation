"""Shared test fixtures."""
import os
import pytest

BRIEFS_DIR = os.path.join(
    os.path.dirname(__file__), "..",
    "workspaces", "assessment-automation", "briefs"
)

SAMPLE_TEMPLATE = os.path.join(BRIEFS_DIR, "Assessment Report_AI Powered Business Analytics.docx")
SAMPLE_DATA = os.path.join(BRIEFS_DIR, "Assessment Result - For Release.xlsx")


@pytest.fixture
def sample_template_path():
    return SAMPLE_TEMPLATE


@pytest.fixture
def sample_data_path():
    return SAMPLE_DATA
