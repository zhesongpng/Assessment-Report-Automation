"""Data file parsing and validation for document automation."""
from typing import Optional

import pandas as pd
import io

MAX_FILE_SIZE_MB = 50
MAX_ROWS = 500


def parse_data(uploaded_file) -> pd.DataFrame:
    """Parse uploaded Excel or CSV assessment data.

    Returns DataFrame with only the main data columns (first 5 named columns).
    Strips empty trailing rows.
    """
    name = getattr(uploaded_file, 'name', '') or ''
    content = uploaded_file.getvalue()

    # File size check
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(
            f"The file is {size_mb:.1f} MB, which exceeds the {MAX_FILE_SIZE_MB} MB limit. "
            "Please reduce the data and try again."
        )

    if name.lower().endswith('.csv'):
        df = pd.read_csv(io.BytesIO(content))
    else:
        df = pd.read_excel(io.BytesIO(content))

    # Drop completely empty rows
    df = df.dropna(how='all')

    # Keep only named columns (drop unnamed/extra columns)
    named_cols = [c for c in df.columns if not str(c).startswith('Unnamed')]
    df = df[named_cols]

    # Drop rows where ALL named columns are NaN
    df = df.dropna(how='all').reset_index(drop=True)

    return df


def validate_data(df: pd.DataFrame, template_fields: list = None) -> dict:
    """Validate parsed data against template requirements.

    Args:
        df: DataFrame from parse_data()
        template_fields: list of placeholder names from the template (e.g. ["Learner Name", "Grades"]).
            When provided, shows which data columns map to template placeholders.

    Returns:
        {
            "valid": bool,
            "row_count": int,
            "columns": list[str],
            "warnings": list[str],
            "errors": list[str],
            "field_mapping": list[tuple[str, str]]  # (data_column, placeholder)
        }
    """
    warnings = []
    errors = []
    field_mapping = []

    if len(df) == 0:
        errors.append("The spreadsheet appears to be empty. No data rows found.")
        return {"valid": False, "row_count": 0, "columns": list(df.columns),
                "warnings": warnings, "errors": errors, "field_mapping": field_mapping}

    if len(df) > MAX_ROWS:
        errors.append(
            f"The data has {len(df)} rows, which exceeds the {MAX_ROWS} row limit. "
            "Please split the data into smaller batches."
        )

    columns = list(df.columns)

    # Build field mapping if template fields are provided
    if template_fields:
        for field in template_fields:
            matched_col = _find_column(df, field)
            if matched_col:
                field_mapping.append((matched_col, field))

        if not field_mapping:
            warnings.append(
                "No data columns match your template placeholders. "
                "Make sure your column names match the <<Placeholder>> names in your template."
            )
    else:
        # Without template context, just accept any data with columns
        pass

    # Check for empty values in name-like columns (any column containing "name")
    name_col = _find_column(df, "Learner Name") or _find_column(df, "Name")
    if name_col:
        empty_names = df[name_col].isna().sum()
        if empty_names > 0:
            errors.append(f"{empty_names} row(s) have no value in '{name_col}' — these will be skipped.")

        # Check for duplicate names
        duplicates = df[name_col].dropna().duplicated().sum()
        if duplicates > 0:
            warnings.append(f"{duplicates} row(s) have duplicate values in '{name_col}' — files will be numbered to avoid overwrites.")

    valid = len([e for e in errors if "not found" in e or "exceeds" in e or "empty" in e]) == 0

    return {
        "valid": valid,
        "row_count": len(df),
        "columns": columns,
        "warnings": warnings,
        "errors": errors,
        "field_mapping": field_mapping,
    }


def _find_column(df: pd.DataFrame, name: str) -> Optional[str]:
    """Find a column by case-insensitive, flexible name matching."""
    target = name.lower().replace(" ", "_")
    for col in df.columns:
        if col.lower().replace(" ", "_") == target:
            return col
    # Try substring match
    for col in df.columns:
        if target in col.lower().replace(" ", "_") or col.lower().replace(" ", "_") in target:
            return col
    return None
