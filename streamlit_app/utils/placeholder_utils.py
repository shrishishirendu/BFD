"""
Utilities for extracting and matching Jinja-style placeholders in PDF templates.
"""

import re


# Matches {{ variable_name }} with optional whitespace
PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def extract_placeholders_from_text(text: str) -> list[str]:
    """Extract unique placeholder names from text containing {{ name }} patterns."""
    return sorted(set(PLACEHOLDER_PATTERN.findall(text)))


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract readable text from a PDF file's bytes."""
    try:
        import pypdf
        reader = pypdf.PdfReader(__import__("io").BytesIO(pdf_bytes))
        parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
        return "\n".join(parts)
    except Exception:
        return ""


def extract_placeholders_from_pdf(pdf_bytes: bytes) -> list[str]:
    """Extract placeholder names from a PDF template."""
    text = extract_text_from_pdf(pdf_bytes)
    return extract_placeholders_from_text(text)


def find_missing_placeholders(
    template_placeholders: list[str],
    available_keys: list[str],
) -> list[str]:
    """Return placeholders that are required by the template but not available in data."""
    available_set = {k.lower() for k in available_keys}
    return [p for p in template_placeholders if p.lower() not in available_set]


def merge_text_with_context(text: str, context: dict[str, str]) -> str:
    """Replace {{ placeholder }} tokens in text with values from context dict."""
    def replacer(match):
        key = match.group(1).strip().lower()
        return context.get(key, match.group(0))
    return PLACEHOLDER_PATTERN.sub(replacer, text)
