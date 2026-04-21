# Security Spec

## Overview

Assessment data contains personal information. The tool must handle it carefully and leave no trace after use.

## Data Privacy

### No Persistent Storage

- All uploaded files and generated PDFs live in per-session temp directories only
- Temp directories are created with `tempfile.mkdtemp()` (unique per session)
- On download completion or session timeout: all temp files deleted
- No database, no file storage, no logging of file contents

### Session Isolation

- Each browser session gets its own temp directory (UUID-based)
- No cross-session data access possible
- Streamlit's per-session state handles this naturally

### No Data Logging

- Log file paths and operation status only (not data contents)
- Never log learner names, assessment scores, or other personal data
- Error messages reference row numbers, not personal identifiers

## Password Handling

- User password is transmitted over HTTPS (if deployed with TLS)
- Password exists in server memory only during the processing session
- Password is displayed to the user on the download screen so they can communicate it to recipients
- Owner password is auto-generated per file (random 16-char string)
- Neither password is logged or stored persistently

## PDF Encryption

- AES-256 encryption (pikepdf default)
- Owner password restricts: modification, text extraction, annotation
- User password allows: opening and printing only
- Encryption applies to all output PDFs — no option to skip

## Deployment Security

- For local deployment: no network exposure (Streamlit binds to localhost by default)
- For server deployment: recommend HTTPS + optional password protection on the Streamlit app itself
- LibreOffice headless runs in a sandboxed subprocess with timeout

## Cleanup Protocol

1. User clicks download → ZIP file served
2. User clicks "Start Over" or closes tab → temp directory deleted
3. On app restart → any orphaned temp directories from previous sessions cleaned up
4. Fallback: OS temp directory cleanup handles anything missed
