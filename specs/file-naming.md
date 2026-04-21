# File Naming Spec

## Overview

Files are named automatically from assessment data columns, eliminating the need for manual renaming.

## Naming Pattern

The user specifies a naming pattern using column names as placeholders:

```
{ColumnName1}_{ColumnName2}_AssessmentReport.pdf
```

**Confirmed pattern**: `{LearnerName}_{ProgrammeName}_AssessmentReport.pdf`

The pattern is configurable. The user selects from common patterns or enters a custom one. The confirmed default above is pre-filled.

## Pattern Evaluation

Before processing begins, the app evaluates the pattern against all data rows and shows a preview of the first 3-5 filenames. This catches problems before the batch runs.

## Filename Sanitization

After substituting data values, filenames are sanitized:

| Character | Replacement | Reason |
|-----------|-------------|--------|
| `\ / : * ? " < > \|` | `-` (hyphen) | Invalid on Windows |
| Leading/trailing spaces | Removed | Cause issues in some tools |
| Multiple consecutive spaces | Single space | Clean appearance |
| Empty name field | ERROR — skip that learner | Cannot name a file with blank |

**Preserved characters**: Apostrophes (O'Brien), hyphens (Mary-Jane), non-ASCII characters (Wei Chen, Jose Garcia-Lopez). These are valid in modern filesystems.

## Duplicate Name Handling

If two learners produce the same filename:

1. Detect before processing begins
2. Show warning in the naming preview
3. Auto-append a sequence number to the duplicate: `Smith_John_AssessmentReport.pdf`, `Smith_John_AssessmentReport_2.pdf`
4. Display which rows are affected

## Filename Length

Maximum filename length: 200 characters (well under the 255-char OS limit, leaving room for path). Filenames exceeding this are truncated with `...` and a sequence number appended.

## Open Question

**Naming convention confirmed**: `{LearnerName}_{ProgrammeName}_AssessmentReport.pdf`. The data must contain columns named "LearnerName" (or close variants) and "ProgrammeName" (or close variants). Auto-matching handles case and spacing differences.
