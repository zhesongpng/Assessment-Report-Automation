# Assessment Report Automation

Generate individual, password-protected PDF assessment reports from a Word template and an Excel data file — in one click.

## How It Works

1. Upload your Word template (.docx) with mail merge fields
2. Upload your assessment results (.xlsx or .csv)
3. Fill in the programme name, end date, and a password
4. Click **Generate Reports**
5. Download a ZIP file with one protected PDF per learner

## Template Requirements

Your Word template must use **mail merge fields** (not bracket placeholders). The expected fields are:

| Field            | Source                                                |
| ---------------- | ----------------------------------------------------- |
| `Learner_Name`   | Picked up from the "Learner Name" column in your data |
| `Grades`         | Picked up from the "Grades" column in your data       |
| `Programme_Name` | Typed in by you when generating                       |
| `End_Date`       | Typed in by you when generating                       |

To add merge fields in Word: **Insert → Quick Parts → Field → MergeField**.

## Data File Requirements

- Excel (.xlsx) or CSV file
- Must have columns named **"Learner Name"** and **"Grades"** (case-insensitive)
- Other columns are ignored
- Each row = one learner = one PDF

## Output

- One PDF per learner, named: `LearnerName_ProgrammeName_AssessmentReport.pdf`
- Each PDF is password-protected (AES-256 encryption)
- Editing is restricted; printing is allowed
- All PDFs packaged in a single ZIP download

## Deployment (Streamlit Community Cloud)

This app is designed to run on **Streamlit Community Cloud**:

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Set the main file to `app.py`
5. Deploy — colleagues get a link, no installation needed

The `packages.txt` file ensures LibreOffice is installed on the server for PDF conversion.

## Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

For PDF conversion, LibreOffice must be installed (not needed for template/data validation).
