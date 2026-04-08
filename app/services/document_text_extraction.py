from __future__ import annotations

import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from pypdf import PdfReader

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TextExtractionResult:
    requires_ocr: bool
    extracted_text: str | None
    extracted_fields: dict[str, Any]
    extraction_method: str
    manual_review_required: bool = False
    error_message: str | None = None


class DocumentLocator(Protocol):
    def resolve_path(self, *, storage_backend: str, storage_key: str) -> Path: ...


class LocalDocumentLocator:
    def resolve_path(self, *, storage_backend: str, storage_key: str) -> Path:
        if storage_backend != "local":
            raise ValueError(f"Unsupported storage backend '{storage_backend}' for text extraction")
        return Path(settings.document_storage_path) / storage_key


class EmbeddedPdfTextExtractor:
    def extract(self, file_path: Path) -> str:
        reader = PdfReader(str(file_path))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


class TesseractAdapter:
    def extract_image_text(self, file_path: Path) -> str:
        result = subprocess.run(
            [settings.tesseract_command, str(file_path), "stdout", "-l", settings.document_ocr_language],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "tesseract failed")
        return result.stdout.strip()

    def extract_pdf_text_via_ocrmypdf(self, file_path: Path) -> str:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_pdf = Path(temp_dir) / f"{file_path.stem}-ocr.pdf"
            result = subprocess.run(
                [
                    settings.ocrmypdf_command,
                    "--skip-text",
                    "--force-ocr",
                    "-l",
                    settings.document_ocr_language,
                    str(file_path),
                    str(output_pdf),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "ocrmypdf failed")
            return EmbeddedPdfTextExtractor().extract(output_pdf)


class SimpleFieldDetector:
    def detect(self, text: str) -> dict[str, Any]:
        normalized = " ".join(text.split())
        return {
            "raw_text_length": len(text),
            "lines": [line.strip() for line in text.splitlines() if line.strip()][:50],
            "contains_passport_keyword": "passport" in normalized.lower(),
            "contains_birth_keyword": "birth" in normalized.lower() or "nacimiento" in normalized.lower(),
        }


class DocumentTextExtractionService:
    def __init__(
        self,
        locator: DocumentLocator | None = None,
        embedded_pdf_extractor: EmbeddedPdfTextExtractor | None = None,
        tesseract_adapter: TesseractAdapter | None = None,
        field_detector: SimpleFieldDetector | None = None,
    ) -> None:
        self.locator = locator or LocalDocumentLocator()
        self.embedded_pdf_extractor = embedded_pdf_extractor or EmbeddedPdfTextExtractor()
        self.tesseract_adapter = tesseract_adapter or TesseractAdapter()
        self.field_detector = field_detector or SimpleFieldDetector()

    def extract_for_document(
        self,
        *,
        storage_backend: str,
        storage_key: str,
        mime_type: str,
        original_filename: str,
        force_reprocess: bool = False,
    ) -> TextExtractionResult:
        try:
            file_path = self.locator.resolve_path(storage_backend=storage_backend, storage_key=storage_key)
            suffix = file_path.suffix.lower() or Path(original_filename).suffix.lower()

            if mime_type == "application/pdf" or suffix == ".pdf":
                return self._extract_from_pdf(file_path, force_reprocess=force_reprocess)

            if mime_type in {"image/jpeg", "image/png"} or suffix in {".jpg", ".jpeg", ".png"}:
                return self._extract_from_image(file_path)

            return TextExtractionResult(
                requires_ocr=False,
                extracted_text=None,
                extracted_fields={},
                extraction_method="unsupported",
                manual_review_required=True,
                error_message="unsupported_file_type",
            )
        except Exception as exc:  # noqa: BLE001
            return TextExtractionResult(
                requires_ocr=False,
                extracted_text=None,
                extracted_fields={},
                extraction_method="unavailable",
                manual_review_required=True,
                error_message=str(exc),
            )

    def _extract_from_pdf(self, file_path: Path, *, force_reprocess: bool) -> TextExtractionResult:
        embedded_text = ""
        if not force_reprocess:
            try:
                embedded_text = self.embedded_pdf_extractor.extract(file_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Embedded PDF extraction failed for %s: %s", file_path, exc)

        if embedded_text and len(embedded_text.strip()) >= settings.document_embedded_text_min_chars:
            return TextExtractionResult(
                requires_ocr=False,
                extracted_text=embedded_text,
                extracted_fields=self.field_detector.detect(embedded_text),
                extraction_method="embedded_pdf_text",
            )

        try:
            ocr_text = self.tesseract_adapter.extract_pdf_text_via_ocrmypdf(file_path)
            return TextExtractionResult(
                requires_ocr=True,
                extracted_text=ocr_text,
                extracted_fields=self.field_detector.detect(ocr_text),
                extraction_method="ocrmypdf",
            )
        except Exception as exc:  # noqa: BLE001
            return TextExtractionResult(
                requires_ocr=True,
                extracted_text=None,
                extracted_fields={},
                extraction_method="ocrmypdf",
                manual_review_required=True,
                error_message=str(exc),
            )

    def _extract_from_image(self, file_path: Path) -> TextExtractionResult:
        try:
            ocr_text = self.tesseract_adapter.extract_image_text(file_path)
            return TextExtractionResult(
                requires_ocr=True,
                extracted_text=ocr_text,
                extracted_fields=self.field_detector.detect(ocr_text),
                extraction_method="tesseract",
            )
        except Exception as exc:  # noqa: BLE001
            return TextExtractionResult(
                requires_ocr=True,
                extracted_text=None,
                extracted_fields={},
                extraction_method="tesseract",
                manual_review_required=True,
                error_message=str(exc),
            )
