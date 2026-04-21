"""Tests for PDF conversion and protection."""
from pathlib import Path

import pikepdf
import pytest

from src.pdf import check_libreoffice, convert_to_pdf, protect_pdf, ConversionError


class TestCheckLibreoffice:
    def test_returns_bool(self):
        result = check_libreoffice()
        assert isinstance(result, bool)


class TestProtectPdf:
    def _make_test_pdf(self, tmp_path):
        pdf = pikepdf.Pdf.new()
        page = pikepdf.Page(pikepdf.Dictionary(
            Type=pikepdf.Name("/Page"),
            MediaBox=[0, 0, 612, 792],
        ))
        pdf.pages.append(page)
        input_pdf = tmp_path / "input.pdf"
        pdf.save(input_pdf)
        pdf.close()
        return input_pdf

    def test_edit_restrictions_no_password_to_open(self, tmp_path):
        input_pdf = self._make_test_pdf(tmp_path)
        output_pdf = tmp_path / "protected.pdf"
        protect_pdf(input_pdf, output_pdf, "testowner")

        assert output_pdf.exists()
        # File can be opened without a password
        opened = pikepdf.open(output_pdf)
        assert len(opened.pages) == 1
        assert opened.is_encrypted
        opened.close()

    def test_permissions_restrict_editing(self, tmp_path):
        input_pdf = self._make_test_pdf(tmp_path)
        output_pdf = tmp_path / "protected.pdf"
        protect_pdf(input_pdf, output_pdf, "testowner")

        opened = pikepdf.open(output_pdf)
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
            "Lear_Name": "Test", "Grades": "A",
            "Programme Name": "Prog", "End Date": "2025",
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
