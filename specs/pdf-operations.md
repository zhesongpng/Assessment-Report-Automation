# PDF Operations Spec

## Overview

Password protection and editing restrictions applied to each individual PDF.

## Encryption

- **Library**: pikepdf (backed by QPDF, Apache-2.0 licensed)
- **Algorithm**: AES-256 encryption
- **User password**: Set by the user (required to open the PDF)
- **Owner password**: Auto-generated per file (used internally to enforce permissions)

## Permissions (Edit Restriction)

Applied to every output PDF:

| Permission | Value | Meaning |
|------------|-------|---------|
| Print | Allowed | Recipients can print |
| Modify | Denied | Recipients cannot edit |
| Extract | Denied | Recipients cannot copy text |
| Annotate | Denied | Recipients cannot add comments |

```python
pdf.save(output_path, encryption=pikepdf.Encryption(
    user_password=user_password,
    owner_password=owner_password,
    allow=pikepdf.Permissions(
        print=True,
        modify=False,
        extract=False,
        annotate=False,
    )
))
```

## Compatibility

Output PDFs must open correctly in:
- Adobe Acrobat Reader
- Chrome PDF viewer
- macOS Preview
- Firefox PDF viewer

AES-256 is supported by all modern PDF readers (PDF 2.0 standard). If compatibility issues arise, fallback to AES-128.

## Password Behavior

- One password is set by the user and applied to ALL files in the batch
- The password is displayed to the user on the download screen (masked by default, with a "show" toggle)
- The user is responsible for communicating the password to recipients

## Edge Cases

- Password must be at least 4 characters (PDF encryption minimum)
- Password and confirmation must match before processing starts
- Empty password is rejected
