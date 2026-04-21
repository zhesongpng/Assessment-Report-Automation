"""Assessment data file parsing and validation."""
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


def validate_data(df: pd.DataFrame) -> dict:
    """Validate parsed assessment data.

    Returns:
        {
            "valid": bool,
            "row_count": int,
            "columns": list[str],
            "warnings": list[str],
            "errors": list[str]
        }
    """
    warnings = []
    errors = []

    if len(df) == 0:
        errors.append("The spreadsheet appears to be empty. No learner data found.")
        return {"valid": False, "row_count": 0, "columns": list(df.columns), "warnings": warnings, "errors": errors}

    if len(df) > MAX_ROWS:
        errors.append(
            f"The data has {len(df)} rows, which exceeds the {MAX_ROWS} row limit. "
            "Please split the data into smaller batches."
        )

    columns = list(df.columns)

    # Check for required columns (case-insensitive, flexible matching)
    col_map = {c.lower().replace(" ", "_"): c for c in columns}

    if "learner_name" not in col_map and "learner name" not in {c.lower() for c in columns}:
        errors.append("Column 'Learner Name' not found. Your data needs a column with learner names.")

    if "grades" not in col_map and "grades" not in {c.lower() for c in columns}:
        errors.append("Column 'Grades' not found. Your data needs a column with assessment grades.")

    # Check for empty name cells
    name_col = _find_column(df, "Learner Name")
    if name_col:
        empty_names = df[name_col].isna().sum()
        if empty_names > 0:
            errors.append(f"{empty_names} learner(s) have no name — these will be skipped.")

    # Check for duplicate names
    if name_col:
        duplicates = df[name_col].dropna().duplicated().sum()
        if duplicates > 0:
            warnings.append(f"{duplicates} learner(s) have duplicate names — files will be numbered to avoid overwrites.")

    valid = len(errors) == 0 or all("no name" in e for e in errors)
    # Valid even with empty-name warnings (those rows just get skipped)
    valid = len([e for e in errors if "not found" in e]) == 0

    return {
        "valid": valid,
        "row_count": len(df),
        "columns": columns,
        "warnings": warnings,
        "errors": errors
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
