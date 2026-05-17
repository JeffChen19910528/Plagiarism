"""Parse PDF and DOCX files to extract raw text."""

import io
import re
from pathlib import Path


def parse_pdf(file_bytes: bytes) -> str:
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required: pip install pdfplumber")

    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def parse_docx(file_bytes: bytes) -> str:
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is required: pip install python-docx")

    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def parse_uploaded_file(uploaded_file) -> str:
    """Accept a Streamlit UploadedFile and return extracted text."""
    file_bytes = uploaded_file.read()
    name = uploaded_file.name.lower()

    if name.endswith(".pdf"):
        return parse_pdf(file_bytes)
    elif name.endswith(".docx") or name.endswith(".doc"):
        return parse_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {Path(name).suffix}")
