"""
Document Service - Enhanced with high-quality OCR support.
Handles document parsing and text extraction with advanced preprocessing.
Supports text files, PDFs (with multi-method extraction and OCR).
"""
import os
import io
import base64
import logging
import tempfile
import hashlib
import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

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

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import cv2
    import numpy as np
    OPENCV_SUPPORT = True
except ImportError:
    OPENCV_SUPPORT = False
    logger.warning("OpenCV/PIL not available, image preprocessing disabled")


# OCR Configuration for form documents
FORM_OCR_CONFIG = r'--oem 3 --psm 6'  # LSTM engine, uniform block of text
FORM_OCR_CONFIG_ALT1 = r'--oem 3 --psm 4'  # Single column
FORM_OCR_CONFIG_ALT2 = r'--oem 3 --psm 3'  # Fully automatic

# Character whitelist for forms
FORM_CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,?!-:()[]/@#$%&*+=<>'

# DPI settings
HIGH_DPI = 300  # High quality OCR
MEDIUM_DPI = 200  # Standard quality
LOW_DPI = 150  # Fast processing


class DocumentService:
    """
    Enhanced service for parsing and extracting text from documents.
    Features:
    - Multi-method PDF extraction (PyPDF2, pdfplumber, OCR)
    - Advanced image preprocessing for OCR
    - Resolution upscaling
    - Multi-pass OCR with different configurations
    - Quality validation
    - Result caching
    """

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    SUPPORTED_TYPES = {"text", "pdf"}
    MIN_VIABLE_TEXT_LENGTH = 20  # Minimum characters for valid extraction
    CACHE_DIR = "/tmp/formflow_ocr_cache"

    def __init__(self, use_cache: bool = True, high_quality: bool = True):
        """
        Initialize the document service.

        Args:
            use_cache: Enable result caching to avoid reprocessing
            high_quality: Use high-quality settings (slower but more accurate)
        """
        self.ocr_available = OCR_SUPPORT
        self.pdf_available = PDF_SUPPORT or PDFPLUMBER_SUPPORT
        self.opencv_available = OPENCV_SUPPORT
        self.use_cache = use_cache
        self.high_quality = high_quality

        # Create cache directory
        if self.use_cache:
            Path(self.CACHE_DIR).mkdir(parents=True, exist_ok=True)

        logger.info(f"DocumentService initialized - OCR: {self.ocr_available}, "
                   f"OpenCV: {self.opencv_available}, Cache: {self.use_cache}, "
                   f"HQ: {self.high_quality}")

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
                    logger.info(f"Extracted {len(text)} characters from {doc_name}")
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
            # Try cache first
            if self.use_cache:
                cached_text = self._get_cached_result(decoded_content)
                if cached_text:
                    logger.info(f"Using cached result for {doc_name}")
                    return cached_text

            # Extract text
            text = self._extract_text_from_pdf(decoded_content)

            # Cache result
            if self.use_cache and text:
                self._cache_result(decoded_content, text)

            return text

        return ""

    def _get_cache_key(self, content: bytes) -> str:
        """Generate cache key from content hash."""
        return hashlib.md5(content).hexdigest()

    def _get_cached_result(self, content: bytes) -> Optional[str]:
        """Retrieve cached extraction result."""
        try:
            cache_key = self._get_cache_key(content)
            cache_file = Path(self.CACHE_DIR) / f"{cache_key}.json"

            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    return data.get('text', '')
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")

        return None

    def _cache_result(self, content: bytes, text: str):
        """Cache extraction result."""
        try:
            cache_key = self._get_cache_key(content)
            cache_file = Path(self.CACHE_DIR) / f"{cache_key}.json"

            with open(cache_file, 'w') as f:
                json.dump({'text': text}, f)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

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
        Extract text from a PDF file using multiple methods with fallbacks.

        Strategy:
        1. Try native text extraction (PyPDF2) - fastest, best for digital PDFs
        2. Try pdfplumber with table support - better for structured PDFs
        3. Try enhanced OCR - for scanned/image PDFs

        Args:
            content: PDF file bytes

        Returns:
            Extracted text
        """
        logger.info(f"PDF Support: PyPDF2={PDF_SUPPORT}, pdfplumber={PDFPLUMBER_SUPPORT}, OCR={OCR_SUPPORT}")

        # Method 1: PyPDF2 (fastest)
        if PDF_SUPPORT:
            try:
                text = self._extract_with_pypdf2(content)
                if self._validate_extracted_text(text):
                    logger.info(f"✓ PyPDF2 extracted {len(text)} chars")
                    return text
                else:
                    logger.info("PyPDF2 extraction insufficient, trying next method")
            except Exception as e:
                logger.warning(f"PyPDF2 extraction failed: {e}")

        # Method 2: pdfplumber (better for tables/structure)
        if PDFPLUMBER_SUPPORT:
            try:
                text = self._extract_with_pdfplumber_enhanced(content)
                if self._validate_extracted_text(text):
                    logger.info(f"✓ pdfplumber extracted {len(text)} chars")
                    return text
                else:
                    logger.info("pdfplumber extraction insufficient, trying OCR")
            except Exception as e:
                logger.warning(f"pdfplumber extraction failed: {e}")

        # Method 3: Enhanced OCR (slowest but works on scanned documents)
        if OCR_SUPPORT:
            try:
                text = self._extract_with_enhanced_ocr(content)
                if text.strip():
                    logger.info(f"✓ OCR extracted {len(text)} chars")
                    return text
            except Exception as e:
                logger.error(f"OCR extraction failed: {e}")

        logger.warning("No viable text could be extracted from PDF")
        return ""

    def _validate_extracted_text(self, text: str) -> bool:
        """
        Validate if extracted text is of sufficient quality.

        Args:
            text: Extracted text

        Returns:
            True if text meets quality standards
        """
        if not text or len(text.strip()) < self.MIN_VIABLE_TEXT_LENGTH:
            return False

        # Check for reasonable word count
        words = text.split()
        if len(words) < 5:
            return False

        # Check for too many special characters (corruption indicator)
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if len(text) > 0 and special_chars / len(text) > 0.5:
            logger.warning("Text appears corrupted (too many special characters)")
            return False

        return True

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
        for page_num, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            except Exception as e:
                logger.warning(f"Failed to extract page {page_num}: {e}")
                continue

        return "\n\n".join(text_parts)

    def _extract_with_pdfplumber_enhanced(self, content: bytes) -> str:
        """
        Extract text using pdfplumber with table detection.

        Args:
            content: PDF bytes

        Returns:
            Extracted text with tables
        """
        pdf_file = io.BytesIO(content)

        text_parts = []
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    # Extract regular text
                    page_text = page.extract_text() or ""

                    # Extract tables separately
                    tables = page.extract_tables()
                    if tables:
                        for table_num, table in enumerate(tables):
                            if table:
                                # Convert table to text format
                                table_rows = []
                                for row in table:
                                    if row:
                                        # Filter out None values
                                        clean_row = [str(cell) if cell else "" for cell in row]
                                        table_rows.append(" | ".join(clean_row))

                                if table_rows:
                                    table_text = f"\n[Table {table_num + 1}]\n" + "\n".join(table_rows)
                                    page_text += f"\n{table_text}\n"

                    if page_text.strip():
                        text_parts.append(page_text)

                except Exception as e:
                    logger.warning(f"Failed to extract page {page_num}: {e}")
                    continue

        return "\n\n".join(text_parts)

    def _extract_with_enhanced_ocr(self, content: bytes) -> str:
        """
        Extract text using enhanced OCR with preprocessing.

        Args:
            content: PDF bytes

        Returns:
            Extracted text
        """
        # Select DPI based on quality setting
        dpi = HIGH_DPI if self.high_quality else MEDIUM_DPI

        logger.info(f"Converting PDF to images at {dpi} DPI...")

        # Convert PDF pages to images
        try:
            images = convert_from_bytes(
                content,
                dpi=dpi,
                fmt='png',
                grayscale=False  # Keep color for better preprocessing
            )
        except Exception as e:
            logger.error(f"PDF to image conversion failed: {e}")
            return ""

        text_parts = []
        for i, image in enumerate(images):
            logger.info(f"Processing page {i + 1}/{len(images)} with OCR...")

            # Preprocess image if OpenCV is available
            if self.opencv_available:
                image = self._preprocess_image_for_ocr(image)
            else:
                # Basic upscaling if needed
                image = self._upscale_if_needed(image)

            # Extract text with multi-pass strategy
            text = self._extract_text_multipass(image)

            if text.strip():
                text_parts.append(f"--- Page {i + 1} ---\n{text}")

        return "\n\n".join(text_parts)

    def _preprocess_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy.

        Applies:
        - Resolution upscaling if needed
        - Grayscale conversion
        - Denoising
        - Contrast enhancement (CLAHE)
        - Binarization (Otsu's method)
        - Morphological cleaning

        Args:
            image: PIL Image

        Returns:
            Preprocessed PIL Image
        """
        try:
            # Upscale if too small
            image = self._upscale_if_needed(image)

            # Convert PIL to numpy array
            img_array = np.array(image)

            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # Denoise
            denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)

            # Increase contrast with CLAHE (adaptive histogram equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            contrast = clahe.apply(denoised)

            # Binarization (Otsu's method - automatic threshold)
            _, binary = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Morphological operations to remove small noise
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            # Convert back to PIL Image
            return Image.fromarray(cleaned)

        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, using original")
            return image

    def _upscale_if_needed(self, image: Image.Image) -> Image.Image:
        """
        Upscale low-resolution images for better OCR.

        Args:
            image: PIL Image

        Returns:
            Upscaled image if needed
        """
        width, height = image.size

        # If image is too small, upscale it
        min_dimension = 1500 if self.high_quality else 1200

        if width < min_dimension or height < min_dimension:
            scale_factor = 2
            new_size = (width * scale_factor, height * scale_factor)
            logger.info(f"Upscaling image from {width}x{height} to {new_size[0]}x{new_size[1]}")
            # Use LANCZOS for high-quality upscaling
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        return image

    def _extract_text_multipass(self, image: Image.Image) -> str:
        """
        Extract text using multiple OCR configurations and pick best result.

        Args:
            image: PIL Image

        Returns:
            Best extracted text
        """
        if not OCR_SUPPORT:
            return ""

        configs = [
            (FORM_OCR_CONFIG, "form-optimized"),
            (FORM_OCR_CONFIG_ALT1, "single-column"),
            (FORM_OCR_CONFIG_ALT2, "auto-detect"),
        ]

        results = []

        for config, name in configs:
            try:
                text = pytesseract.image_to_string(
                    image,
                    lang='eng',
                    config=config
                )

                # Score based on length and word count
                # More text and more words = higher confidence
                word_count = len(text.split())
                char_count = len(text.strip())
                score = char_count + (word_count * 5)

                results.append((score, text, name))
                logger.debug(f"OCR config '{name}': {char_count} chars, {word_count} words, score={score}")

            except Exception as e:
                logger.warning(f"OCR with config '{name}' failed: {e}")
                continue

        if results:
            # Return result with highest score
            best_score, best_text, best_config = max(results, key=lambda x: x[0])
            logger.info(f"Best OCR result from '{best_config}' config (score: {best_score})")
            return best_text

        return ""

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

        # Remove excessive whitespace but preserve paragraph breaks
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Normalize whitespace within each line
            cleaned_line = re.sub(r'[ \t]+', ' ', line).strip()
            if cleaned_line:  # Only keep non-empty lines
                cleaned_lines.append(cleaned_line)

        text = '\n'.join(cleaned_lines)

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
