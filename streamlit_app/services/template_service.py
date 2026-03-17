"""
Template service for PDF invitation personalisation.
Reads a PDF template, merges placeholders with recipient data,
generates personalised PDFs, and extracts preview text.
"""

import io
from pathlib import Path

from utils.placeholder_utils import (
    extract_placeholders_from_pdf,
    extract_text_from_pdf,
    merge_text_with_context,
)
from utils.file_utils import get_output_path, ensure_directory
from config import GENERATED_DOCS_DIR


def get_template_placeholders(pdf_bytes: bytes) -> list[str]:
    """Return the list of placeholder names found in the PDF template."""
    return extract_placeholders_from_pdf(pdf_bytes)


def get_template_text(pdf_bytes: bytes) -> str:
    """Extract readable text from the PDF template."""
    return extract_text_from_pdf(pdf_bytes)


def generate_preview_text(pdf_bytes: bytes, context: dict[str, str]) -> str:
    """
    Extract text from the PDF template and merge placeholders with context values.
    Returns the merged text suitable for display in the UI.
    """
    raw_text = extract_text_from_pdf(pdf_bytes)
    if not raw_text:
        return "(No readable text could be extracted from the PDF template.)"
    return merge_text_with_context(raw_text, context)


def generate_personalised_pdf(
    pdf_bytes: bytes,
    context: dict[str, str],
    recipient_name: str,
    output_dir: Path | None = None,
) -> tuple[bytes, Path]:
    """
    Generate a personalised PDF by overlaying merged text onto the template.

    Since true PDF form-field merging depends on the template structure,
    this implementation uses ReportLab to create an overlay with the merged text
    and merges it with the original PDF pages via pypdf.

    Returns (personalised_pdf_bytes, saved_file_path).
    """
    import pypdf
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas

    if output_dir is None:
        output_dir = GENERATED_DOCS_DIR
    ensure_directory(output_dir)

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))

    # Build merged text
    raw_text = extract_text_from_pdf(pdf_bytes)
    merged_text = merge_text_with_context(raw_text, context)

    # Create a text overlay PDF using ReportLab
    overlay_buf = io.BytesIO()
    c = rl_canvas.Canvas(overlay_buf, pagesize=A4)
    # We write the merged text as a watermark-style overlay on page 1
    # This is a pragmatic approach; for production templates with form fields,
    # a dedicated PDF form-fill library would be used.
    text_obj = c.beginText(50, A4[1] - 50)
    text_obj.setFont("Helvetica", 10)
    for line in merged_text.split("\n"):
        text_obj.textLine(line)
    c.drawText(text_obj)
    c.showPage()
    c.save()
    overlay_buf.seek(0)

    overlay_reader = pypdf.PdfReader(overlay_buf)

    writer = pypdf.PdfWriter()
    for i, page in enumerate(reader.pages):
        if i == 0 and len(overlay_reader.pages) > 0:
            # Merge overlay onto first page
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    output_buf = io.BytesIO()
    writer.write(output_buf)
    personalised_bytes = output_buf.getvalue()

    # Save to disk
    file_path = get_output_path(output_dir, recipient_name, suffix="_invitation")
    file_path.write_bytes(personalised_bytes)

    return personalised_bytes, file_path
