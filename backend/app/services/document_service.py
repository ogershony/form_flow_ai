"""
Document Service - Handles document parsing and text extraction.
Supports text files, PDFs (with OCR for images).
"""
import os
import io
import base64
import logging
import tempfile
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Optional imports for PDF processing
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logger.warning("PyPDF2 not available, PDF text extraction disabled")

try:
    import pdfplumber
    PDFPLUMBER_SUPPORT = True
except ImportError:
    PDFPLUMBER_SUPPORT = False
    logger.warning("pdfplumber not available")

try:
    from pdf2image import convert_from_bytes
    import pytesseract
    OCR_SUPPORT = True
except ImportError:
    OCR_SUPPORT = False
    logger.warning("OCR dependencies not available (pdf2image, pytesseract)")


class DocumentService:
    """
    Service for parsing and extracting text from documents.
    """

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    SUPPORTED_TYPES = {"text", "pdf"}

    def __init__(self):
        """Initialize the document service."""
        self.ocr_available = OCR_SUPPORT
        self.pdf_available = PDF_SUPPORT or PDFPLUMBER_SUPPORT

    def process_documents(self, documents: List[Dict[str, Any]]) -> str:
        """
        Process multiple documents and extract text.

        Args:
            documents: List of document dictionaries with name, type, and content

        Returns:
            Combined extracted text from all documents
        """
        if not documents:
            return ""

        extracted_texts = []

        for doc in documents:
            try:
                text = self.process_document(doc)
                if text:
                    doc_name = doc.get("name", "Unknown")
                    extracted_texts.append(f"--- Document: {doc_name} ---\n{text}")
            except Exception as e:
                logger.error(f"Error processing document {doc.get('name')}: {e}")
                continue

        return "\n\n".join(extracted_texts)

    def process_document(self, document: Dict[str, Any]) -> str:
        """
        Process a single document and extract text.

        Args:
            document: Document dictionary with name, type, and base64 content

        Returns:
            Extracted text
        """
        doc_type = document.get("type", "").lower()
        doc_name = document.get("name", "unknown")
        content = document.get("content", "")

        if doc_type not in self.SUPPORTED_TYPES:
            raise ValueError(f"Unsupported document type: {doc_type}")

        # Decode base64 content
        try:
            decoded_content = base64.b64decode(content)
        except Exception as e:
            logger.error(f"Failed to decode base64 content: {e}")
            raise ValueError("Invalid document content encoding")

        # Check file size
        if len(decoded_content) > self.MAX_FILE_SIZE:
            raise ValueError(f"Document too large (max {self.MAX_FILE_SIZE / 1024 / 1024}MB)")

        logger.info(f"Processing document: {doc_name} ({doc_type}, {len(decoded_content)} bytes)")

        if doc_type == "text":
            return self._extract_text_from_text(decoded_content)
        elif doc_type == "pdf":
            return self._extract_text_from_pdf(decoded_content)

        return ""

    def _extract_text_from_text(self, content: bytes) -> str:
        """
        Extract text from a text file.

        Args:
            content: Raw file bytes

        Returns:
            Decoded text
        """
        # Try different encodings
        encodings = ["utf-8", "latin-1", "cp1252", "ascii"]

        for encoding in encodings:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue

        # Fallback with error replacement
        return content.decode("utf-8", errors="replace")

    def _extract_text_from_pdf(self, content: bytes) -> str:
        """
        Extract text from a PDF file.
        Uses multiple methods: PyPDF2, pdfplumber, and OCR as fallback.

        Args:
            content: PDF file bytes

        Returns:
            Extracted text
        """
        extracted_text = ""

        # Try PyPDF2 first
        if PDF_SUPPORT:
            try:
                extracted_text = self._extract_with_pypdf2(content)
                if extracted_text.strip():
                    logger.info("Text extracted using PyPDF2")
                    return extracted_text
            except Exception as e:
                logger.warning(f"PyPDF2 extraction failed: {e}")

        # Try pdfplumber
        if PDFPLUMBER_SUPPORT:
            try:
                extracted_text = self._extract_with_pdfplumber(content)
                if extracted_text.strip():
                    logger.info("Text extracted using pdfplumber")
                    return extracted_text
            except Exception as e:
                logger.warning(f"pdfplumber extraction failed: {e}")

        # Fallback to OCR for scanned documents
        if OCR_SUPPORT:
            try:
                extracted_text = self._extract_with_ocr(content)
                if extracted_text.strip():
                    logger.info("Text extracted using OCR")
                    return extracted_text
            except Exception as e:
                logger.warning(f"OCR extraction failed: {e}")

        logger.warning("No text could be extracted from PDF")
        return extracted_text

    def _extract_with_pypdf2(self, content: bytes) -> str:
        """
        Extract text using PyPDF2.

        Args:
            content: PDF bytes

        Returns:
            Extracted text
        """
        pdf_file = io.BytesIO(content)
        reader = PyPDF2.PdfReader(pdf_file)

        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        return "\n\n".join(text_parts)

    def _extract_with_pdfplumber(self, content: bytes) -> str:
        """
        Extract text using pdfplumber.

        Args:
            content: PDF bytes

        Returns:
            Extracted text
        """
        pdf_file = io.BytesIO(content)

        text_parts = []
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

        return "\n\n".join(text_parts)

    def _extract_with_ocr(self, content: bytes) -> str:
        """
        Extract text using OCR (Tesseract).

        Args:
            content: PDF bytes

        Returns:
            Extracted text
        """
        # Convert PDF pages to images
        images = convert_from_bytes(content, dpi=200)

        text_parts = []
        for i, image in enumerate(images):
            logger.debug(f"Running OCR on page {i + 1}")
            text = pytesseract.image_to_string(image)
            if text:
                text_parts.append(text)

        return "\n\n".join(text_parts)

    def sanitize_text(self, text: str, max_length: int = 50000) -> str:
        """
        Sanitize and truncate extracted text.

        Args:
            text: Raw text
            max_length: Maximum allowed length

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Remove null bytes and other problematic characters
        text = text.replace("\x00", "")

        # Normalize whitespace
        import re
        text = re.sub(r"\s+", " ", text)

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length] + "... [truncated]"

        return text.strip()


# Singleton instance
_document_service = None


def get_document_service() -> DocumentService:
    """Get or create the document service singleton."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
