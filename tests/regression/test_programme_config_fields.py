"""Regression: user-entered Programme dates must win over spreadsheet columns.

Bug: template placeholders <<Programme Start Date>> / <<Programme End Date>>
resolved to spreadsheet values (or empty) instead of the dates the user typed
into the form. Two causes:
  1. config fields were keyed "Start Date"/"End Date", which did not match the
     "Programme Start Date"/"Programme End Date" spelling users put in templates;
  2. spreadsheet columns were matched BEFORE config fields, so any same-named
     column overrode the user's input.
"""
import pytest

from src.merge import build_replacements


@pytest.mark.regression
def test_programme_date_placeholders_use_user_input_not_spreadsheet():
    """<<Programme Start Date>>/<<Programme End Date>> resolve to typed-in config,
    even when the spreadsheet has same-named columns."""
    row = {
        "Learner Name": "Tan Wei Ming",
        "Grades": "Distinction",
        "Programme Start Date": "OLD-EXCEL-START",
        "Programme End Date": "OLD-EXCEL-END",
    }
    config = {
        "programme_name": "AI Powered Business Analytics",
        "start_date": "1 January 2025",
        "end_date": "15 May 2025",
    }
    fields = [
        "Learner Name",
        "Programme Name",
        "Programme Start Date",
        "Programme End Date",
        "Programme Date",
    ]
    result = build_replacements(row, config, template_fields=fields)

    # Per-learner data still comes from the spreadsheet
    assert result["Learner Name"] == "Tan Wei Ming"
    # Programme-level fields come from user input, NOT the spreadsheet columns
    assert result["Programme Name"] == "AI Powered Business Analytics"
    assert result["Programme Start Date"] == "1 January 2025"
    assert result["Programme End Date"] == "15 May 2025"
    assert result["Programme Date"] == "1 January 2025 to 15 May 2025"


@pytest.mark.regression
def test_short_date_placeholder_spellings_still_match():
    """The shorter <<Start Date>>/<<End Date>> spellings remain supported."""
    config = {"programme_name": "P", "start_date": "1 Jan", "end_date": "30 Jun"}
    result = build_replacements(
        {"Learner Name": "Alice"},
        config,
        template_fields=["Start Date", "End Date"],
    )
    assert result["Start Date"] == "1 Jan"
    assert result["End Date"] == "30 Jun"
