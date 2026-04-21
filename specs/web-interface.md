# Web Interface Spec

## Overview

A Streamlit web application providing the upload-configure-download workflow.

## Framework

**Streamlit** — chosen for built-in file upload, download, and progress widgets with zero frontend code. Runs locally via `streamlit run app.py`.

## Page Layout

Single-page application with a linear top-to-bottom flow:

### Section 1: File Upload

Two upload areas:
- **Template upload**: Accepts .docx only. Shows merge field count after upload.
- **Data upload**: Accepts .xlsx or .csv. Shows row (learner) count after upload.

### Section 2: Field Mapping (appears after both files uploaded)

- Auto-matched fields shown with green checkmarks
- Unmatched fields shown with yellow warning and manual mapping dropdown
- If >50% fields unmatched: prominent warning message

### Section 3: Configuration

| Setting | Type | Default | Required |
|---------|------|---------|----------|
| Programme Name | Text input | Derived from template filename | Yes |
| End Date | Text input | (empty) | Yes |
| PDF Password | Text input | (empty) | Yes |
| Confirm Password | Text input | (empty) | Yes |
| Restrict Editing | Always on | Enabled | — |
| Naming Pattern | Dropdown + custom | `{LearnerName}_{ProgrammeName}_AssessmentReport.pdf` | No |
| Name Preview | Read-only display | Shows first 3 filenames | — |

"Generate Reports" button — disabled until all required inputs are provided.

### Section 4: Processing

- Progress bar with current learner count: "Processing 12 of 30..."
- Status text showing current step
- On completion: summary with success/failure counts

### Section 5: Download

- Download button for ZIP file
- Summary: file count, total size, list of filenames, password (masked with show toggle)
- "Start Over" button to reset

## Error Display

All errors shown in plain language, never technical:
- Wrong file format: "This is a PDF file. Please upload a Word document (.docx)."
- No merge fields: "No merge fields found. Your template needs placeholders."
- Processing failure: "2 reports could not be generated:" followed by specific row/learner and reason

## Browser Support

Chrome, Firefox, Safari, Edge — latest versions.

## Session Behavior

- Settings persist within a browser session (page refresh keeps state)
- "Start Over" clears all state
- No user accounts, no login
- No data persists after the browser tab is closed
