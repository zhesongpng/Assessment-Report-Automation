# Data Handling Spec

## Overview

How assessment data is validated, parsed, and mapped to template merge fields.

## Supported Formats

| Format | Extension | Library |
|--------|-----------|---------|
| Excel | .xlsx | openpyxl (via pandas) |
| CSV | .csv | pandas |

Auto-detect format from file extension. User does not need to specify.

## Data Structure Expectations

- **One row per learner**
- First row is headers (column names)
- Empty cells are allowed — the field is left blank in the output

### Actual Data Columns (from sample)

| Column | Purpose | Used in Template |
|--------|---------|-----------------|
| `Group No.` | Group identifier | No |
| `Learner Name` | Learner's full name | Yes → `[Learner Name]` |
| `Marks` | Numeric score | No (not in template) |
| `Grades` | Text grade (Distinction/Merit/Pass/Fail) | Yes → `[Grades]` |
| `Winning Team (Indicate Y)` | Manual fill column | No |

Only `Learner Name` and `Grades` are merged into the template per learner. The other columns are ignored.

The data file may contain extra unnamed columns (reference tables, notes) — these should be ignored. Only process the main data table in columns A-E.

## Field Mapping

### Auto-matching Rules

1. Column name = merge field name → matched (exact match)
2. Column name matches after lowercasing and removing spaces/underscores → matched
3. Column name is a substring or partial match → NOT auto-matched (too error-prone)

Examples of successful auto-matches:
- `LearnerName` ↔ `LearnerName` ✓
- `Learner Name` ↔ `Learner_Name` ✓
- `learnername` ↔ `LEARNERNAME` ✓

Examples that require manual mapping:
- `Student Name` ↔ `LearnerName` (different words)
- `Name` ↔ `FullName` (different scope)

### Manual Mapping

If auto-match fails for some fields, the user sees a dropdown for each unmatched field:
- Dropdown lists all data column names
- Includes a "Leave blank" option
- User maps fields and proceeds

## Data Quality Warnings

Before processing, show warnings for:

| Condition | Warning Level | Message |
|-----------|---------------|---------|
| Required naming field (e.g., Name) is empty for some rows | Error | "Cannot generate reports for 2 learners — name is missing" |
| Optional field is empty for >50% of rows | Info | "Field 'Comments' is empty for 20 of 30 learners" |
| Duplicate values in the naming field | Warning | "2 learners share the name 'John Smith'" |
| Data has more columns than template fields | Info | "3 data columns are not used in the template" |
| Template has more fields than data columns | Warning | "2 template fields have no matching data column" |

## Data Size Limits

| Metric | Limit |
|--------|-------|
| Maximum file size | 50 MB |
| Maximum rows | 500 learners |
| Maximum columns | 50 |

These are practical limits to prevent browser/server timeout.
