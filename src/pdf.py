"""PDF conversion and edit restriction."""
import subprocess
import secrets
import tempfile
from pathlib import Path

import pikepdf


class ConversionError(Exception):
    """Raised when LibreOffice PDF conversion fails."""
    pass


def check_libreoffice() -> bool:
    """Check if LibreOffice is installed."""
    try:
        result = subprocess.run(
            ["which", "soffice"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return True
        # Try macOS-specific path
        mac_path = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
        return mac_path.exists()
    except Exception:
        return False


def convert_to_pdf(docx_path: Path, output_dir: Path, session_id: str, learner_idx: int) -> Path:
    """Convert a .docx to .pdf using LibreOffice headless.

    Args:
        docx_path: Path to input .docx file
        output_dir: Directory for output PDF
        session_id: Session identifier for profile isolation
        learner_idx: Learner index for profile isolation

    Returns:
        Path to generated PDF

    Raises:
        ConversionError: if conversion fails or times out
    """
    # Find soffice binary
    soffice = "soffice"
    mac_path = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    if mac_path.exists():
        soffice = str(mac_path)

    # Create isolated profile directory
    profile_dir = Path(tempfile.gettempdir()) / f"libreoffice_profile_{session_id}_{learner_idx}"
    profile_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        soffice,
        "--headless",
        f"-env:UserInstallation=file://{profile_dir}",
        "--convert-to", "pdf",
        "--outdir", str(output_dir),
        str(docx_path),
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
    except FileNotFoundError:
        raise ConversionError(
            "LibreOffice (soffice) not found. Install LibreOffice to enable PDF conversion."
        )
    except subprocess.TimeoutExpired:
        raise ConversionError(f"LibreOffice conversion timed out for learner {learner_idx}")
    finally:
        try:
            import shutil
            shutil.rmtree(profile_dir, ignore_errors=True)
        except Exception:
            pass

    if result.returncode != 0:
        raise ConversionError(
            f"LibreOffice conversion failed for learner {learner_idx}: {result.stderr[:200]}"
        )

    # Find the output PDF
    expected_pdf = output_dir / f"{docx_path.stem}.pdf"
    if expected_pdf.exists():
        return expected_pdf

    # Fallback: find any new PDF in output_dir
    pdfs = list(output_dir.glob("*.pdf"))
    if pdfs:
        return pdfs[-1]

    raise ConversionError(f"No PDF generated for learner {learner_idx}")


def protect_pdf(input_path: Path, output_path: Path, owner_password: str) -> Path:
    """Apply edit restrictions to a PDF. Anyone can open it, but cannot modify.

    Uses the owner password to enforce: print allowed, modify/extract/annotate denied.
    No user password means anyone can open the file without entering a password.
    Use the owner password in Adobe Acrobat to unlock editing if needed.

    Args:
        input_path: Path to unencrypted PDF
        output_path: Where to write the protected PDF
        owner_password: Password for permission enforcement (used to unlock editing)

    Returns:
        Path to protected PDF
    """
    pdf = pikepdf.open(input_path)
    pdf.save(
        output_path,
        encryption=pikepdf.Encryption(
            owner=owner_password,
            allow=pikepdf.Permissions(
                accessibility=True,
                extract=False,
                modify_annotation=False,
                modify_assembly=False,
                modify_form=False,
                modify_other=False,
                print_lowres=True,
                print_highres=True,
            )
        )
    )
    pdf.close()
    return output_path
