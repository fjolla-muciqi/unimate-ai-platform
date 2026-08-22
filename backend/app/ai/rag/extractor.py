from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


def extract_text_from_pdf(file_path: str) -> list[dict]:
    reader = PdfReader(file_path)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        pages.append(
            {
                "page_number": page_number,
                "text": text.strip(),
            }
        )

    return pages


def extract_text_from_docx(file_path: str) -> list[dict]:
    document = DocxDocument(file_path)

    text = "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    )

    return [
        {
            "page_number": None,
            "text": text.strip(),
        }
    ]


def extract_text_from_txt(file_path: str) -> list[dict]:
    text = Path(file_path).read_text(
        encoding="utf-8",
        errors="ignore",
    )

    return [
        {
            "page_number": None,
            "text": text.strip(),
        }
    ]


def extract_document_text(file_path: str) -> list[dict]:
    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)

    if extension == ".docx":
        return extract_text_from_docx(file_path)

    if extension == ".txt":
        return extract_text_from_txt(file_path)

    raise ValueError(
        f"Unsupported file type: {extension}"
    )