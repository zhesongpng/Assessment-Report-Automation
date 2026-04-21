"""Template validation and merge field detection via python-docx."""
import re
import tempfile
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn


def _extract_merge_fields(doc):
    """Extract MERGEFIELD names from a python-docx Document.

    Scans both complex fields (<w:instrText>) and simple fields (<w:fldSimple>).
    """
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


def detect_merge_fields(template_path):
    """Detect MERGEFIELD entries in a Word template.

    Returns sorted list of unique field names.
    """
    doc = Document(template_path)
    fields = _extract_merge_fields(doc)
    return sorted(fields)


def validate_template(uploaded_file):
    """Validate an uploaded Word template.

    Args:
        uploaded_file: Streamlit UploadedFile object (has .name, .getvalue(), .read())

    Returns:
        {"valid": bool, "fields": list[str], "error": str|None}
    """
    if uploaded_file is None:
        return {"valid": False, "fields": [], "error": "No file uploaded."}

    name = getattr(uploaded_file, 'name', '') or ''
    if not name.lower().endswith('.docx'):
        return {"valid": False, "fields": [], "error": "Please upload a Word document (.docx)."}

    tmp = None
    try:
        content = uploaded_file.getvalue()
        if len(content) == 0:
            return {"valid": False, "fields": [], "error": "The file is empty. Please upload a valid .docx file."}

        tmp = tempfile.NamedTemporaryFile(suffix='.docx', delete=False)
        tmp.write(content)
        tmp.close()

        doc = Document(tmp.name)
        fields = _extract_merge_fields(doc)

        if not fields:
            return {
                "valid": False,
                "fields": [],
                "error": "No merge fields found in this template. Your template needs Word mail merge fields (Insert → Quick Parts → Field → MergeField)."
            }

        return {"valid": True, "fields": sorted(fields), "error": None}

    except Exception:
        return {"valid": False, "fields": [], "error": "Could not read this file. It may be corrupted or not a valid Word document."}

    finally:
        if tmp:
            try:
                Path(tmp.name).unlink(missing_ok=True)
            except Exception:
                pass
