"""Document Automation — Streamlit web app."""
import tempfile
from pathlib import Path

import streamlit as st

from src.template import validate_template, detect_merge_fields
from src.data import parse_data, validate_data, _find_column
from src.merge import build_replacements
from src.naming import generate_all_filenames, sanitize_filename, DEFAULT_PATTERN
from src.pdf import check_libreoffice
from src.pipeline import process_batch, cleanup_session

st.set_page_config(page_title="Document Automation", page_icon="📄", layout="centered")

st.title("Document Automation")
st.caption("Upload your Word template and data, then generate personalized PDFs for each row. PDFs are restricted from editing.")

# Check LibreOffice availability once
if "libreoffice_ok" not in st.session_state:
    st.session_state.libreoffice_ok = check_libreoffice()

if not st.session_state.libreoffice_ok:
    st.warning("LibreOffice is not installed on this server. PDF conversion will not work. Contact your administrator.")

# ── Section 1: Template Upload ──────────────────────────────────────────────
st.header("1. Upload Template")
template_file = st.file_uploader(
    "Word template (.docx)",
    type=["docx"],
    key="template_uploader",
    help="Upload a Word document with placeholders like <<Column Name>> that match your data columns.",
)

template_valid = False
if template_file:
    result = validate_template(template_file)
    if result["valid"]:
        st.success(f"Template loaded — {len(result['fields'])} merge field(s) detected.")
        with st.expander("Merge fields found"):
            for f in result["fields"]:
                st.code(f)
        st.session_state.template_info = result
        st.session_state.template_bytes = template_file.getvalue()
        template_valid = True
    else:
        st.error(result["error"])
        st.session_state.pop("template_info", None)
        st.session_state.pop("template_bytes", None)

# ── Section 2: Data Upload ──────────────────────────────────────────────────
st.header("2. Upload Data")
data_file = st.file_uploader(
    "Data file (.xlsx or .csv)",
    type=["xlsx", "csv"],
    key="data_uploader",
    help="Excel or CSV file with columns matching the <<Placeholder>> names in your template.",
)

data_valid = False
if data_file:
    try:
        df = parse_data(data_file)

        # Pass template fields for dynamic column matching
        template_fields = st.session_state.get("template_info", {}).get("fields")
        validation = validate_data(df, template_fields=template_fields)

        if validation["valid"]:
            st.success(f"Data loaded — {validation['row_count']} row(s) found.")
            st.session_state.data_df = df
            data_valid = True

            with st.expander("Data preview"):
                st.dataframe(df.head(10), use_container_width=True)

            # Show field mapping
            if validation.get("field_mapping"):
                mappings = [f"'{col}' → <<{placeholder}>>" for col, placeholder in validation["field_mapping"]]
                st.info("Column mapping: " + ", ".join(mappings))
        else:
            for err in validation["errors"]:
                st.error(err)
            st.session_state.pop("data_df", None)

        for warn in validation.get("warnings", []):
            st.warning(warn)

    except ValueError as e:
        st.error(str(e))
        st.session_state.pop("data_df", None)
    except Exception:
        st.error("Could not read the file. Please check that it is a valid Excel or CSV file.")
        st.session_state.pop("data_df", None)

# ── Section 3: Configuration ────────────────────────────────────────────────
st.header("3. Configure")
programme_name = st.text_input("Programme Name", placeholder="e.g., AI Powered Business Analytics")
start_date = st.text_input("Programme Start Date", placeholder="e.g., 1 January 2025")
end_date = st.text_input("Programme End Date", placeholder="e.g., 15 May 2025")
owner_password = st.text_input("Owner Password", type="password", help="Set a password to lock PDF editing. Recipients can view and print but cannot edit. Use this password in Adobe Acrobat if you need to unlock editing later.")
st.caption("Keep this password safe — you'll need it to edit the PDFs later. Minimum 4 characters.")

# File name pattern
st.subheader("File Name Pattern")
file_pattern = st.text_input(
    "Pattern",
    value=DEFAULT_PATTERN,
    help="Use {ColumnName} to insert values from your data. "
         "Spaces in column names are removed (e.g., {LearnerName} matches 'Learner Name'). "
         "Always include .pdf at the end.",
)
st.caption("Available placeholders: any column name from your data, plus {ProgrammeName}, {StartDate}, {EndDate}, {ProgrammeDate}")

# Naming preview
if template_valid and data_valid and programme_name and file_pattern:
    try:
        filenames, name_errors, name_warnings = generate_all_filenames(
            file_pattern, st.session_state.data_df, programme_name
        )
        preview_count = min(5, len(filenames))
        if preview_count > 0:
            st.markdown("**Preview:**")
            for i in range(preview_count):
                st.text(f"  {filenames[i]}")
            if len(filenames) > preview_count:
                st.text(f"  ... and {len(filenames) - preview_count} more")

        for w in name_warnings:
            st.warning(w)
        for e in name_errors:
            st.error(e)
    except Exception as e:
        st.error(f"Naming error: {e}")

# ── Section 4: Generate ─────────────────────────────────────────────────────
st.header("4. Generate Documents")

ready = (
    template_valid
    and data_valid
    and programme_name
    and start_date
    and end_date
    and owner_password
    and len(owner_password) >= 4
    and file_pattern
    and st.session_state.libreoffice_ok
)

if st.button("Generate Documents", disabled=not ready, type="primary"):
    # Save template to temp file for processing
    tmp_template = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    tmp_template.write(st.session_state.template_bytes)
    tmp_template.close()

    config = {
        "programme_name": programme_name,
        "start_date": start_date,
        "end_date": end_date,
        "owner_password": owner_password,
        "pattern": file_pattern,
    }

    progress_bar = st.progress(0, text="Starting...")
    status_text = st.empty()

    def on_progress(current, total, message):
        pct = int((current / total) * 100) if total > 0 else 0
        progress_bar.progress(pct, text=message)
        status_text.text(message)

    try:
        result = process_batch(
            template_path=tmp_template.name,
            data_df=st.session_state.data_df,
            config=config,
            progress_callback=on_progress,
        )

        st.session_state.batch_result = result
        progress_bar.progress(100, text="Done!")
        status_text.text(f"Completed: {result['success_count']} document(s) generated.")
        st.rerun()

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error("Processing failed. Please try again. If the problem persists, check that your template and data are valid.")
    finally:
        Path(tmp_template.name).unlink(missing_ok=True)

# ── Section 5: Download ─────────────────────────────────────────────────────
if "batch_result" in st.session_state:
    result = st.session_state.batch_result

    st.header("5. Download Documents")

    st.success(f"{result['success_count']} document(s) generated successfully.")

    if result["error_count"] > 0:
        st.warning(f"{result['error_count']} row(s) could not be processed:")
        for err in result["errors"]:
            st.error(err)

    # Download button
    zip_path = result["zip_path"]
    if zip_path and Path(zip_path).exists():
        zip_bytes = Path(zip_path).read_bytes()
        zip_size_mb = len(zip_bytes) / (1024 * 1024)

        st.download_button(
            label=f"Download ZIP ({zip_size_mb:.1f} MB)",
            data=zip_bytes,
            file_name=f"{sanitize_filename(programme_name or 'Documents')}_Documents.zip",
            mime="application/zip",
            type="primary",
        )

    # File list
    if result["filenames"]:
        with st.expander("Files included"):
            for f in result["filenames"]:
                st.text(f)

    # Start over
    if st.button("Start Over"):
        if "zip_path" in result:
            cleanup_session(Path(result["zip_path"]).parent)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
