"""Template merge — <<Placeholder>> substitution via python-docx."""
import re
from pathlib import Path

from docx import Document


def build_replacements(row, config):
    """Build the placeholder replacement mapping for one learner row.

    Args:
        row: dict from one DataFrame row (e.g. {"Learner Name": "Tan Wei Ming", "Grades": "Distinction"})
        config: {"programme_name": str, "end_date": str, ...}

    Returns:
        Dict mapping placeholder names to replacement values.
        Keys match <<Placeholder>> text in the template.
    """
    replacements = {}

    field_map = {
        "Learner Name": "Learner Name",
        "Grades": "Grades",
    }
    for col_name, placeholder_name in field_map.items():
        val = row.get(col_name)
        if val is None or (isinstance(val, float) and str(val) == "nan"):
            replacements[placeholder_name] = ""
        else:
            replacements[placeholder_name] = str(val)

    replacements["Programme Name"] = config.get("programme_name", "")
    replacements["End Date"] = config.get("end_date", "")

    return replacements


def merge_template(template_path, replacements, output_path):
    """Merge a .docx template by replacing <<Placeholder>> text.

    Args:
        template_path: Path to the .docx template
        replacements: Dict mapping placeholder names to values
        output_path: Where to save the merged document

    Returns:
        The output_path string

    Raises:
        FileNotFoundError: if template does not exist
        ValueError: if template has no placeholders
    """
    template = Path(template_path)
    if not template.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    doc = Document(str(template))

    placeholders = _extract_placeholders(doc)
    if not placeholders:
        raise ValueError(
            f"Template '{template_path}' has no placeholders. "
            "Add <<Learner Name>>, <<Grades>>, etc. in your template."
        )

    applicable = {k: v for k, v in replacements.items() if k in placeholders}
    _replace_placeholders(doc, applicable)

    doc.save(output_path)
    return output_path


def _extract_placeholders(doc):
    """Find all <<Placeholder>> patterns in a python-docx Document."""
    placeholders = set()
    for paragraph in doc.paragraphs:
        placeholders.update(m.strip() for m in re.findall(r'<<(.+?)>>', paragraph.text))
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    placeholders.update(m.strip() for m in re.findall(r'<<(.+?)>>', paragraph.text))
    for section in doc.sections:
        for part in [section.header, section.first_page_header, section.even_page_header,
                      section.footer, section.first_page_footer, section.even_page_footer]:
            if part and not getattr(part, 'is_linked_to_previous', True):
                for paragraph in part.paragraphs:
                    placeholders.update(m.strip() for m in re.findall(r'<<(.+?)>>', paragraph.text))
    return placeholders


def _replace_placeholders(doc, replacements):
    """Replace <<Placeholder>> with values throughout the document."""
    replace_map = {}
    for key, value in replacements.items():
        replace_map[f'<<{key}>>'] = str(value)

    for paragraph in doc.paragraphs:
        _replace_in_paragraph(paragraph, replace_map)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    _replace_in_paragraph(paragraph, replace_map)

    for section in doc.sections:
        for part in [section.header, section.first_page_header, section.even_page_header,
                      section.footer, section.first_page_footer, section.even_page_footer]:
            if part and not getattr(part, 'is_linked_to_previous', True):
                for paragraph in part.paragraphs:
                    _replace_in_paragraph(paragraph, replace_map)


def _replace_in_paragraph(paragraph, replace_map):
    """Replace placeholders in a paragraph, handling cross-run cases."""
    full_text = paragraph.text
    if '<<' not in full_text:
        return

    # Try single-run replacement first (preserves formatting)
    for run in paragraph.runs:
        for pattern, value in replace_map.items():
            if pattern in run.text:
                run.text = run.text.replace(pattern, value)

    # If all placeholders replaced, done
    if '<<' not in paragraph.text:
        return

    # Cross-run case: merge text into first run
    runs = paragraph.runs
    if not runs:
        return

    merged = paragraph.text
    for pattern, value in replace_map.items():
        merged = merged.replace(pattern, value)

    runs[0].text = merged
    for run in runs[1:]:
        run.text = ''


def get_template_fields(template_path):
    """Return the set of placeholder names detected in a template.

    Raises:
        FileNotFoundError: if template does not exist
    """
    template = Path(template_path)
    if not template.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    doc = Document(str(template))
    return _extract_placeholders(doc)
