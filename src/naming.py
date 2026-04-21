"""File naming — pattern substitution, sanitization, deduplication."""
import re


DEFAULT_PATTERN = "{LearnerName}_{ProgrammeName}_AssessmentReport.pdf"

_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')
_MULTI_SPACE = re.compile(r'\s+')
_MAX_LENGTH = 200


def sanitize_filename(name: str) -> str:
    """Sanitize a filename by replacing invalid characters and cleaning whitespace."""
    name = _INVALID_CHARS.sub('-', name)
    # Remove path traversal sequences
    while '..' in name:
        name = name.replace('..', '')
    name = name.strip()
    name = _MULTI_SPACE.sub(' ', name)
    return name


def validate_filename_length(name: str) -> str:
    """Truncate filename to max length if needed."""
    if len(name) <= _MAX_LENGTH:
        return name
    base, ext = name.rsplit('.', 1) if '.' in name else (name, '')
    available = _MAX_LENGTH - len(ext) - 1 - 5  # 5 for "..._NNN"
    truncated = base[:available] + "..."
    if ext:
        return f"{truncated}.{ext}"
    return truncated


def generate_filename(pattern: str, data_row: dict, programme_name: str) -> str:
    """Generate a filename from a pattern by substituting data values.

    Pattern uses {ColumnName} placeholders. Spaces in column names are removed
    for matching (e.g., {LearnerName} matches "Learner Name" column).

    Args:
        pattern: e.g., "{LearnerName}_{ProgrammeName}_AssessmentReport.pdf"
        data_row: dict from DataFrame row
        programme_name: user-provided programme name

    Returns:
        Sanitized filename string

    Raises:
        ValueError: if the name field is empty
    """
    # Build lookup: "learnername" -> value, "programme" -> value
    lookup = {}
    for col, val in data_row.items():
        key = col.lower().replace(" ", "").replace("_", "")
        val_str = "" if val is None or (isinstance(val, float) and str(val) == "nan") else str(val)
        lookup[key] = val_str
    lookup["programme"] = programme_name
    lookup["programmename"] = programme_name

    # Substitute {placeholders} in pattern
    def replacer(match):
        placeholder = match.group(1)
        key = placeholder.lower().replace(" ", "").replace("_", "")
        if key in lookup:
            value = lookup[key]
            if not value:
                raise ValueError(f"Field '{placeholder}' is empty — cannot generate filename.")
            return value
        return match.group(0)

    result = re.sub(r'\{(\w+)\}', replacer, pattern)
    result = sanitize_filename(result)
    result = validate_filename_length(result)
    return result


def check_duplicates(filenames: list[str]) -> list[str]:
    """Detect duplicate filenames and return deduplicated list.

    Returns:
        List of filenames with _2, _3 suffixes for duplicates.
        First occurrence keeps the original name.
    """
    result = []
    seen: dict[str, int] = {}

    for fname in filenames:
        if fname in seen:
            seen[fname] += 1
            base, ext = fname.rsplit('.', 1) if '.' in fname else (fname, 'pdf')
            result.append(f"{base}_{seen[fname]}.{ext}")
        else:
            seen[fname] = 1
            result.append(fname)

    return result


def generate_all_filenames(pattern: str, data_df, programme_name: str) -> tuple[list[str], list[str], list[str]]:
    """Generate filenames for all learners.

    Returns:
        (filenames, errors, duplicates)
        - filenames: list of final filenames (with dedup suffixes)
        - errors: list of error messages for rows that can't be named
        - duplicates: list of warning messages about duplicates
    """
    raw_names = []
    errors = []
    row_indices = []

    for idx, row in data_df.iterrows():
        row_dict = row.to_dict()
        try:
            fname = generate_filename(pattern, row_dict, programme_name)
            raw_names.append(fname)
            row_indices.append(idx)
        except ValueError as e:
            errors.append(f"Row {idx + 2}: {str(e)}")

    # Check duplicates
    final_names = check_duplicates(raw_names)

    # Warnings for duplicates
    warnings = []
    seen = {}
    for i, name in enumerate(raw_names):
        final = final_names[i]
        if name in seen:
            seen[name] += 1
        else:
            seen[name] = 1
    for name, count in seen.items():
        if count > 1:
            warnings.append(f"{count} learners share the name '{name.rsplit('_', 1)[0]}...'")

    return final_names, errors, warnings
