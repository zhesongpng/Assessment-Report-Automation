"""Template merge — Word MERGEFIELD substitution via python-docx."""
import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn


def _extract_merge_fields(doc):
    """Extract MERGEFIELD names from a python-docx Document."""
    fields = set()
    for element in doc.element.iter():
        if element.tag == qn('w:instrText'):
            text = element.text or ''
            match = re.search(r'MERGEFIELD\s+"?([A-Za-z_]\w*)"?', text, re.IGNORECASE)
            if match:
                fields.add(match.group(1))
        if element.tag == qn('w:fldSimple'):
            instr = element.get(qn('w:instr'), '') or ''
            match = re.search(r'MERGEFIELD\s+"?([A-Za-z_]\w*)"?', instr, re.IGNORECASE)
            if match:
                fields.add(match.group(1))
    return fields


def build_replacements(row, config):
    """Build the merge-field replacement mapping for one learner row.

    Args:
        row: dict from one DataFrame row (e.g. {"Learner Name": "Tan Wei Ming", "Grades": "Distinction"})
        config: {"programme_name": str, "end_date": str, ...}

    Returns:
        Dict mapping template merge-field names to replacement values.
        Keys use underscores (matching Word MERGEFIELD naming convention).
    """
    replacements = {}

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

    replacements["Programme_Name"] = config.get("programme_name", "")
    replacements["End_Date"] = config.get("end_date", "")

    return replacements


def merge_template(template_path, replacements, output_path):
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

    doc = Document(str(template))

    merge_fields = _extract_merge_fields(doc)
    if not merge_fields:
        raise ValueError(
            f"Template '{template_path}' has no merge fields. "
            "Add MERGEFIELD codes in Word before using this template."
        )

    applicable = {k: v for k, v in replacements.items() if k in merge_fields}
    _replace_fields(doc, applicable)

    doc.save(output_path)
    return output_path


def _replace_fields(doc, replacements):
    """Replace MERGEFIELD values throughout the document.

    Handles both complex fields (begin/instrText/separate/content/end)
    and simple fields (fldSimple elements).
    """
    for p in doc.element.body.iter(qn('w:p')):
        _replace_complex_fields_in_paragraph(p, replacements)

    for fld_simple in doc.element.iter(qn('w:fldSimple')):
        instr = fld_simple.get(qn('w:instr'), '') or ''
        match = re.search(r'MERGEFIELD\s+"?([A-Za-z_]\w*)"?', instr, re.IGNORECASE)
        if match:
            field_name = match.group(1)
            if field_name in replacements:
                for t in fld_simple.iter(qn('w:t')):
                    t.text = replacements[field_name]


def _replace_complex_fields_in_paragraph(paragraph, replacements):
    """Replace complex MERGEFIELDs within a paragraph element.

    Complex fields span runs:
      begin -> instrText(MERGEFIELD Name) -> separate -> display text -> end
    """
    children = list(paragraph)
    i = 0
    while i < len(children):
        child = children[i]
        fld_type = _get_fld_char_type(child)

        if fld_type == 'begin':
            field_name = None
            j = i + 1

            while j < len(children):
                inner = children[j]

                instr = _get_instr_text(inner)
                if instr:
                    match = re.search(r'MERGEFIELD\s+"?([A-Za-z_]\w*)"?', instr, re.IGNORECASE)
                    if match:
                        field_name = match.group(1)

                inner_type = _get_fld_char_type(inner)
                if inner_type == 'separate':
                    k = j + 1
                    first_run = True
                    while k < len(children):
                        if _get_fld_char_type(children[k]) == 'end':
                            break
                        if field_name and field_name in replacements:
                            _set_run_text(children[k], replacements[field_name] if first_run else '')
                            first_run = False
                        k += 1
                    break

                j += 1

        i += 1


def _get_fld_char_type(element):
    """Get the fldChar type from an element, or None."""
    for child in element:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag == 'fldChar':
            return child.get(qn('w:fldCharType'))
    return None


def _get_instr_text(element):
    """Get instrText content from an element, or None."""
    for child in element:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag == 'instrText':
            return child.text
    return None


def _set_run_text(run, text):
    """Set the text content of a run element."""
    from lxml import etree

    t_elements = run.findall(qn('w:t'))
    if t_elements:
        t_elements[0].text = text
        for t in t_elements[1:]:
            run.remove(t)
    else:
        t = etree.SubElement(run, qn('w:t'))
        t.text = text
        t.set(qn('xml:space'), 'preserve')


def get_template_fields(template_path):
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

    doc = Document(str(template))
    return _extract_merge_fields(doc)
