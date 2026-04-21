"""Template merge — Word MERGEFIELD substitution via docx-mailmerge."""
from pathlib import Path
from mailmerge import MailMerge


def build_replacements(row: dict, config: dict) -> dict:
    """Build the merge-field replacement mapping for one learner row.

    Args:
        row: dict from one DataFrame row (e.g. {"Learner Name": "Tan Wei Ming", "Grades": "Distinction"})
        config: {"programme_name": str, "end_date": str, ...}

    Returns:
        Dict mapping template merge-field names to replacement values.
        Keys use underscores (matching Word MERGEFIELD naming convention).
    """
    replacements = {}

    # Per-learner fields from the data row
    field_map = {
        "Learner Name": "Learner_Name",
        "Grades": "Grades",
    }
    for col_name, merge_name in field_map.items():
        val = row.get(col_name)
        if val is None or (isinstance(val, float) and str(val) == "nan"):
            replacements[merge_name] = ""
        else:
            replacements[merge_name] = str(val)

    # Configuration-level fields (same for every learner)
    replacements["Programme_Name"] = config.get("programme_name", "")
    replacements["End_Date"] = config.get("end_date", "")

    return replacements


def merge_template(template_path: str, replacements: dict, output_path: str) -> str:
    """Merge a .docx template with replacement values.

    Args:
        template_path: Path to the .docx template containing MERGEFIELDs
        replacements: Dict mapping merge-field names to values
        output_path: Where to save the merged document

    Returns:
        The output_path string

    Raises:
        FileNotFoundError: if template does not exist
        ValueError: if template has no merge fields
    """
    template = Path(template_path)
    if not template.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    doc = MailMerge(str(template))

    # Validate that the template has merge fields
    merge_fields = doc.get_merge_fields()
    if not merge_fields:
        raise ValueError(
            f"Template '{template_path}' has no merge fields. "
            "Add MERGEFIELD codes in Word before using this template."
        )

    # Only pass fields that the template actually uses
    applicable = {k: v for k, v in replacements.items() if k in merge_fields}
    doc.merge(**applicable)

    doc.write(output_path)
    return output_path


def get_template_fields(template_path: str) -> set[str]:
    """Return the set of merge-field names detected in a template.

    Args:
        template_path: Path to .docx template

    Returns:
        Set of field name strings (e.g. {"Learner_Name", "Grades", "Programme_Name"})

    Raises:
        FileNotFoundError: if template does not exist
    """
    template = Path(template_path)
    if not template.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    doc = MailMerge(str(template))
    fields = doc.get_merge_fields()
    return fields
