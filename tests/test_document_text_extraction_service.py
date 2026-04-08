from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("ALEMBIC_DATABASE_URL", "postgresql+psycopg://caseprep:caseprep@localhost:5432/caseprep")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.services.document_text_extraction import (
    DocumentTextExtractionService,
    EmbeddedPdfTextExtractor,
    LocalDocumentLocator,
    SimpleFieldDetector,
    TesseractAdapter,
)


class FakeLocator:
    def __init__(self, path: Path) -> None:
        self.path = path

    def resolve_path(self, *, storage_backend: str, storage_key: str) -> Path:
        return self.path


class FakeEmbeddedPdfExtractor:
    def __init__(self, text: str = "", error: Exception | None = None) -> None:
        self.text = text
        self.error = error

    def extract(self, file_path: Path) -> str:
        if self.error is not None:
            raise self.error
        return self.text


class FakeTesseractAdapter:
    def __init__(self, pdf_text: str = "", image_text: str = "", error: Exception | None = None) -> None:
        self.pdf_text = pdf_text
        self.image_text = image_text
        self.error = error

    def extract_image_text(self, file_path: Path) -> str:
        if self.error is not None:
            raise self.error
        return self.image_text

    def extract_pdf_text_via_ocrmypdf(self, file_path: Path) -> str:
        if self.error is not None:
            raise self.error
        return self.pdf_text


def test_pdf_with_embedded_text_skips_ocr() -> None:
    service = DocumentTextExtractionService(
        locator=FakeLocator(Path("dummy.pdf")),
        embedded_pdf_extractor=FakeEmbeddedPdfExtractor("This PDF already contains searchable text " * 2),
        tesseract_adapter=FakeTesseractAdapter(pdf_text="unused"),
        field_detector=SimpleFieldDetector(),
    )

    result = service.extract_for_document(
        storage_backend="local",
        storage_key="case/doc.pdf",
        mime_type="application/pdf",
        original_filename="doc.pdf",
    )

    assert result.requires_ocr is False
    assert result.extraction_method == "embedded_pdf_text"
    assert result.extracted_text is not None
    assert result.manual_review_required is False


def test_scanned_pdf_falls_back_to_ocr() -> None:
    service = DocumentTextExtractionService(
        locator=FakeLocator(Path("scanned.pdf")),
        embedded_pdf_extractor=FakeEmbeddedPdfExtractor("short"),
        tesseract_adapter=FakeTesseractAdapter(pdf_text="OCR extracted text from scanned PDF"),
        field_detector=SimpleFieldDetector(),
    )

    result = service.extract_for_document(
        storage_backend="local",
        storage_key="case/scanned.pdf",
        mime_type="application/pdf",
        original_filename="scanned.pdf",
    )

    assert result.requires_ocr is True
    assert result.extraction_method == "ocrmypdf"
    assert result.extracted_text == "OCR extracted text from scanned PDF"


def test_unsupported_file_marks_manual_review() -> None:
    service = DocumentTextExtractionService(
        locator=FakeLocator(Path("archive.zip")),
        embedded_pdf_extractor=FakeEmbeddedPdfExtractor(),
        tesseract_adapter=FakeTesseractAdapter(),
        field_detector=SimpleFieldDetector(),
    )

    result = service.extract_for_document(
        storage_backend="local",
        storage_key="case/archive.zip",
        mime_type="application/zip",
        original_filename="archive.zip",
    )

    assert result.manual_review_required is True
    assert result.error_message == "unsupported_file_type"


def test_ocr_failure_marks_manual_review_without_raising() -> None:
    service = DocumentTextExtractionService(
        locator=FakeLocator(Path("image.png")),
        embedded_pdf_extractor=FakeEmbeddedPdfExtractor(),
        tesseract_adapter=FakeTesseractAdapter(error=RuntimeError("tesseract failed")),
        field_detector=SimpleFieldDetector(),
    )

    result = service.extract_for_document(
        storage_backend="local",
        storage_key="case/image.png",
        mime_type="image/png",
        original_filename="image.png",
    )

    assert result.manual_review_required is True
    assert result.extracted_text is None
    assert "tesseract failed" in (result.error_message or "")
