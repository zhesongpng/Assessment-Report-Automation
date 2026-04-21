"""Assessment Report Automation — Streamlit web app."""
import tempfile
import time
from pathlib import Path

import streamlit as st

from src.template import validate_template, detect_merge_fields
from src.data import parse_data, validate_data, _find_column
from src.merge import build_replacements
from src.naming import generate_all_filenames, sanitize_filename, DEFAULT_PATTERN
from src.pdf import check_libreoffice
from src.pipeline import process_batch, cleanup_session

st.set_page_config(page_title="Assessment Report Automation", page_icon="📄", layout="centered")

st.title("Assessment Report Automation")
st.caption("Upload your Word template and Excel data, then generate password-protected PDF reports for each learner.")

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
    help="Upload a Word document with mail merge fields (Learner_Name, Grades, Programme_Name, End_Date).",
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
st.header("2. Upload Assessment Data")
data_file = st.file_uploader(
    "Assessment results (.xlsx or .csv)",
    type=["xlsx", "csv"],
    key="data_uploader",
    help="Excel or CSV file with 'Learner Name' and 'Grades' columns.",
)

data_valid = False
if data_file:
    try:
        df = parse_data(data_file)
        validation = validate_data(df)
        if validation["valid"]:
            st.success(f"Data loaded — {validation['row_count']} learner(s) found.")
            st.session_state.data_df = df
            data_valid = True

            with st.expander("Data preview"):
                st.dataframe(df.head(10), use_container_width=True)

            # Show field mapping
            name_col = _find_column(df, "Learner Name")
            grades_col = _find_column(df, "Grades")
            if name_col and grades_col:
                st.info(f"Column mapping: '{name_col}' → Learner_Name, '{grades_col}' → Grades")
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
end_date = st.text_input("End Date", placeholder="e.g., 15 May 2025")
password = st.text_input("PDF Password", type="password", help="All PDFs will be protected with this password. Users need it to open the files. Minimum 4 characters.")
st.caption("Minimum 4 characters. This password will be required to open each PDF.")
confirm_password = st.text_input("Confirm Password", type="password")

# Password match feedback
if password and confirm_password:
    if password != confirm_password:
        st.error("Passwords do not match.")
    elif len(password) < 4:
        st.error("Password must be at least 4 characters.")
    else:
        st.success("Passwords match.")

# Naming preview
if template_valid and data_valid and programme_name:
    st.subheader("File Name Preview")
    st.caption(f"Pattern: `{DEFAULT_PATTERN}`")

    try:
        filenames, name_errors, name_warnings = generate_all_filenames(
            DEFAULT_PATTERN, st.session_state.data_df, programme_name
        )
        preview_count = min(5, len(filenames))
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
st.header("4. Generate Reports")

ready = (
    template_valid
    and data_valid
    and programme_name
    and end_date
    and password
    and confirm_password
    and password == confirm_password
    and len(password) >= 4
    and st.session_state.libreoffice_ok
)

if st.button("Generate Reports", disabled=not ready, type="primary"):
    # Save template to temp file for processing
    tmp_template = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    tmp_template.write(st.session_state.template_bytes)
    tmp_template.close()

    config = {
        "programme_name": programme_name,
        "end_date": end_date,
        "password": password,
        "pattern": DEFAULT_PATTERN,
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
        status_text.text(f"Completed: {result['success_count']} report(s) generated.")
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

    st.header("5. Download Reports")

    st.success(f"{result['success_count']} report(s) generated successfully.")

    if result["error_count"] > 0:
        st.warning(f"{result['error_count']} learner(s) could not be processed:")
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
            file_name=f"{sanitize_filename(programme_name or 'Assessment')}_Reports.zip",
            mime="application/zip",
            type="primary",
        )

    # File list
    if result["filenames"]:
        with st.expander("Files included"):
            for f in result["filenames"]:
                st.text(f)

    # Password reminder
    if password:
        show_pw = st.checkbox("Show password")
        if show_pw:
            st.code(password)
        else:
            st.text("Password: ••••••••")

    # Start over
    if st.button("Start Over"):
        if "zip_path" in result:
            cleanup_session(Path(result["zip_path"]).parent)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
