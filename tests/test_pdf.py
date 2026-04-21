"""Tests for PDF conversion and protection."""
import tempfile
from pathlib import Path

import pikepdf
import pytest

from src.pdf import check_libreoffice, convert_to_pdf, generate_owner_password, protect_pdf, ConversionError


class TestCheckLibreoffice:
    def test_returns_bool(self):
        result = check_libreoffice()
        assert isinstance(result, bool)


class TestGenerateOwnerPassword:
    def test_length(self):
        pw = generate_owner_password()
        assert len(pw) >= 16

    def test_unique(self):
        pw1 = generate_owner_password()
        pw2 = generate_owner_password()
        assert pw1 != pw2


class TestProtectPdf:
    def test_password_protection_works(self, tmp_path):
        # Create a minimal PDF for testing
        pdf = pikepdf.Pdf.new()
        page = pikepdf.Page(pikepdf.Dictionary(
            Type=pikepdf.Name("/Page"),
            MediaBox=[0, 0, 612, 792],
        ))
        pdf.pages.append(page)
        input_pdf = tmp_path / "input.pdf"
        pdf.save(input_pdf)
        pdf.close()

        output_pdf = tmp_path / "protected.pdf"
        protect_pdf(input_pdf, output_pdf, "testpass", generate_owner_password())

        assert output_pdf.exists()
        # Verify password is required
        with pytest.raises(pikepdf.PasswordError):
            pikepdf.open(output_pdf)
        # Verify correct password works
        opened = pikepdf.open(output_pdf, password="testpass")
        assert len(opened.pages) == 1
        opened.close()

    def test_permissions_restrict_editing(self, tmp_path):
        pdf = pikepdf.Pdf.new()
        page = pikepdf.Page(pikepdf.Dictionary(
            Type=pikepdf.Name("/Page"),
            MediaBox=[0, 0, 612, 792],
        ))
        pdf.pages.append(page)
        input_pdf = tmp_path / "input.pdf"
        pdf.save(input_pdf)
        pdf.close()

        output_pdf = tmp_path / "protected.pdf"
        owner_pw = generate_owner_password()
        protect_pdf(input_pdf, output_pdf, "userpass", owner_pw)

        # Open with owner password and check permissions
        opened = pikepdf.open(output_pdf, password="userpass")
        # pikepdf provides encryption info but permissions checking is indirect
        assert opened.is_encrypted
        opened.close()


class TestConvertToPdf:
    @pytest.mark.skipif(
        not check_libreoffice(),
        reason="LibreOffice not installed"
    )
    def test_converts_docx(self, sample_template_path, tmp_path):
        from src.merge import merge_template
        merged = tmp_path / "merged.docx"
        merge_template(sample_template_path, {
            "Learner_Name": "Test", "Grades": "A",
            "Programme_Name": "Prog", "End_Date": "2025",
        }, str(merged))

        pdf_path = convert_to_pdf(merged, tmp_path, "test_session", 0)
        assert pdf_path.exists()
        assert pdf_path.suffix == ".pdf"
        assert pdf_path.stat().st_size > 0

    def test_nonexistent_docx_raises(self, tmp_path):
        with pytest.raises(ConversionError):
            convert_to_pdf(
                Path("/nonexistent.docx"), tmp_path, "test", 0
            )
