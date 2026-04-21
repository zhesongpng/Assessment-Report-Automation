"""Processing pipeline — orchestrates merge -> PDF -> protect -> name -> ZIP."""
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path

from src.merge import merge_template, build_replacements
from src.pdf import convert_to_pdf, protect_pdf, check_libreoffice
from src.naming import generate_filename, DEFAULT_PATTERN


def process_batch(
    template_path: str,
    data_df,
    config: dict,
    progress_callback=None,
) -> dict:
    """Process all learners: merge -> PDF -> protect -> name -> ZIP.

    Args:
        template_path: Path to .docx template
        data_df: DataFrame with learner data
        config: {"programme_name": str, "end_date": str, "password": str, "pattern": str}
        progress_callback: callable(current, total, message)

    Returns:
        {
            "zip_path": Path,
            "success_count": int,
            "error_count": int,
            "errors": list[str],
            "filenames": list[str]
        }
    """
    session_id = str(uuid.uuid4())[:8]
    temp_dir = Path(tempfile.mkdtemp(prefix=f"assessment_{session_id}_"))
    merge_dir = temp_dir / "merged"
    pdf_dir = temp_dir / "pdfs"
    protected_dir = temp_dir / "protected"
    merge_dir.mkdir()
    pdf_dir.mkdir()
    protected_dir.mkdir()

    pattern = config.get("pattern", DEFAULT_PATTERN)
    programme_name = config["programme_name"]
    owner_password = config["owner_password"]

    total = len(data_df)
    successes = []
    errors = []

    for idx, (_, row) in enumerate(data_df.iterrows()):
        learner_name = str(row.get("Learner Name", f"Row {idx + 2}"))
        msg = f"Processing learner {idx + 1} of {total}: {learner_name}"
        if progress_callback:
            progress_callback(idx, total, msg)

        try:
            # Build replacements
            replacements = build_replacements(row.to_dict(), config)

            # Merge template
            merged_docx = merge_dir / f"learner_{idx}.docx"
            merge_template(template_path, replacements, str(merged_docx))

            # Convert to PDF
            pdf_path = convert_to_pdf(merged_docx, pdf_dir, session_id, idx)

            # Generate filename
            filename = generate_filename(pattern, row.to_dict(), programme_name)

            # Protect PDF (edit-restricted, no password needed to open)
            protected_path = protected_dir / filename
            protect_pdf(pdf_path, protected_path, owner_password)

            successes.append((filename, protected_path))

        except Exception as e:
            errors.append(f"{learner_name}: {str(e)}")

    # Final progress update
    if progress_callback:
        progress_callback(total, total, "Packaging files...")

    # Create ZIP
    zip_path = temp_dir / "assessment_reports.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename, file_path in successes:
            zf.write(file_path, filename)

    if progress_callback:
        progress_callback(total, total, "Done!")

    return {
        "zip_path": zip_path,
        "success_count": len(successes),
        "error_count": len(errors),
        "errors": errors,
        "filenames": [f[0] for f in successes],
    }


def cleanup_session(temp_dir: Path) -> None:
    """Delete all temp files for a session."""
    try:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass
