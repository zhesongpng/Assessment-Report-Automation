# Document Processing Spec

## Overview

The core pipeline: take a Word template with merge fields and a spreadsheet of assessment data, produce individual PDFs for each learner.

## Architecture Decision: Per-Learner Processing

Each learner is processed individually rather than merging all learners into one document and splitting.

**Why**: Eliminates the page-count risk entirely. When you merge all learners into one document, you must split the resulting PDF at correct boundaries — and if any learner produces 1 or 3 pages instead of 2, every subsequent file is wrong. Processing each learner independently means each gets their own .docx and .pdf. No splitting logic needed.

## Pipeline Steps

### Step 1: Template Validation

**Input**: Uploaded .docx file
**Output**: List of detected placeholder fields, or rejection with error message

- Accept only .docx files (reject .doc, .pdf, .txt, corrupted files)
- Scan for Word MERGEFIELD codes using `docx-mailmerge`
- Known merge fields (template to be updated by user):
  - `Learner_Name` — per-learner, from data column "Learner Name"
  - `Grades` — per-learner, from data column "Grades"
  - `Programme_Name` — set once, user input
  - `End_Date` — set once, user input
- Reject templates with zero merge fields with actionable error
- Display detected field count to user

### Step 2: Template Merge Per Learner

**Input**: Template + one row of assessment data
**Output**: One merged .docx file for that learner

- Use `docx-mailmerge` to populate Word MERGEFIELD entries
- Replace `Learner_Name` and `Grades` from the current data row
- Replace `Programme_Name` and `End_Date` from user-provided configuration values
- Empty/missing data fields are left blank (not an error)
- Special characters in data values are preserved (apostrophes, hyphens, non-ASCII)
- Each merged document is saved to a per-session temp directory

### Step 3: PDF Conversion

**Input**: Merged .docx file
**Output**: PDF file

- Use LibreOffice headless mode: `soffice --headless --convert-to pdf --outdir <dir> <input.docx>`
- **Profile isolation**: Each LibreOffice invocation MUST use a unique temporary profile directory to prevent concurrent-invocation conflicts:
  ```
  soffice --headless --env:UserInstallation=file:///tmp/libreoffice_profile_{session_id}_{learner_idx} --convert-to pdf ...
  ```
- Timeout: 30 seconds per document (fail that learner, continue others)
- Conversion preserves formatting: fonts, images, tables, page layout
- Check at app startup that LibreOffice is installed; show clear error if missing

### Step 4: Cleanup

After the ZIP is downloaded (or session ends), delete all temp files:
- Merged .docx files
- Generated PDFs
- ZIP archive

No assessment data persists on the server after the session closes.

## Error Handling

- If a single learner's merge fails: log the error, skip that learner, continue batch
- If LibreOffice conversion fails for one document: skip, report in error summary
- If all learners fail: show error message with likely cause, no download offered

## Performance Targets

| Batch Size | Target Time |
|------------|-------------|
| 10 learners | < 30 seconds |
| 30 learners | < 60 seconds |
| 50 learners | < 2 minutes |
| 100 learners | < 5 minutes |
