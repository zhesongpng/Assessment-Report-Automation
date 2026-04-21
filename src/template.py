"""Template validation and merge field detection."""
from mailmerge import MailMerge
from pathlib import Path
import tempfile
import shutil


def detect_merge_fields(template_path: str) -> list[str]:
    """Detect MERGEFIELD entries in a Word template.

    Returns sorted list of unique field names.
    """
    doc = MailMerge(template_path)
    fields = doc.get_merge_fields()
    return sorted(fields)


def validate_template(uploaded_file) -> dict:
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

    # Save to temp file for mailmerge to read
    tmp = None
    try:
        content = uploaded_file.getvalue()
        if len(content) == 0:
            return {"valid": False, "fields": [], "error": "The file is empty. Please upload a valid .docx file."}

        tmp = tempfile.NamedTemporaryFile(suffix='.docx', delete=False)
        tmp.write(content)
        tmp.close()

        fields = detect_merge_fields(tmp.name)

        if not fields:
            return {
                "valid": False,
                "fields": [],
                "error": "No merge fields found in this template. Your template needs Word mail merge fields (Insert \u2192 Quick Parts \u2192 Field \u2192 MergeField)."
            }

        return {"valid": True, "fields": fields, "error": None}

    except Exception as e:
        return {"valid": False, "fields": [], "error": "Could not read this file. It may be corrupted or not a valid Word document."}

    finally:
        if tmp:
            try:
                Path(tmp.name).unlink(missing_ok=True)
            except Exception:
                pass
