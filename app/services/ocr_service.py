import os
import logging
import subprocess
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Language routing table
# ---------------------------------------------------------------------------
# Indic languages with dedicated Tesseract trained data → use Tesseract
# Everything else → use PaddleOCR (where it genuinely excels)
# ---------------------------------------------------------------------------

# Tesseract language codes (requires the .traineddata packs to be installed)
TESSERACT_LANG_MAP = {
    'gu': 'guj',        # Gujarati  – dedicated script model
    'hi': 'hin',        # Hindi     – Devanagari
    'sa': 'san',        # Sanskrit  – Devanagari
    'mr': 'mar',        # Marathi   – Devanagari
    'ta': 'tam',        # Tamil
    'te': 'tel',        # Telugu
    'kn': 'kan',        # Kannada
    'en': 'eng',        # English (Tesseract also handles this well)
}

# PaddleOCR language codes for languages Tesseract does NOT excel at
PADDLE_LANG_MAP = {
    'ch':     'ch',          # Chinese Simplified
    'ch_tra': 'chinese_cht', # Chinese Traditional
    'ja':     'japan',       # Japanese
    'ko':     'korean',      # Korean
    'ar':     'ar',          # Arabic
    'fr':     'fr',          # French
    'de':     'german',      # German
}

# Indic languages that must go through Tesseract
TESSERACT_LANGS = set(TESSERACT_LANG_MAP.keys())

# PaddleOCR engine cache – initialised lazily, once per language
_paddle_cache: dict = {}


def _find_tesseract() -> str:
    """Return the Tesseract executable path, checking common Windows locations."""
    candidates = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        'tesseract',  # already on PATH
    ]
    for path in candidates:
        try:
            subprocess.run(
                [path, '--version'],
                capture_output=True, check=True, timeout=5
            )
            return path
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
    raise RuntimeError(
        "Tesseract not found. Install it from https://github.com/UB-Mannheim/tesseract/wiki"
    )


def _get_paddle_engine(paddle_lang: str):
    """Return a cached PaddleOCR engine (lazy init)."""
    if paddle_lang not in _paddle_cache:
        from paddleocr import PaddleOCR
        logger.info(f"Initialising PaddleOCR engine for lang='{paddle_lang}'")
        _paddle_cache[paddle_lang] = PaddleOCR(use_angle_cls=True, lang=paddle_lang)
    return _paddle_cache[paddle_lang]


# ---------------------------------------------------------------------------
# OCR Service
# ---------------------------------------------------------------------------

class OCRService:
    """
    Routes OCR to the best engine per language:
      • Indic scripts (Gujarati, Hindi, Sanskrit, Marathi, Tamil, Telugu, Kannada)
        → Tesseract 5 with dedicated language packs (highest accuracy for these scripts)
      • CJK, Arabic, European
        → PaddleOCR (superior for these character sets)
    """

    def __init__(self, lang: str = 'en'):
        self.ui_lang = lang

        if lang in TESSERACT_LANGS:
            self._engine = 'tesseract'
            self._tess_lang = TESSERACT_LANG_MAP[lang]
            self._tess_bin = _find_tesseract()
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = self._tess_bin
            self._pytesseract = pytesseract
            logger.info(
                f"OCRService: Tesseract engine for ui_lang='{lang}' "
                f"(tess_lang='{self._tess_lang}', bin='{self._tess_bin}')"
            )
        else:
            self._engine = 'paddle'
            paddle_lang = PADDLE_LANG_MAP.get(lang, 'en')
            self._paddle = _get_paddle_engine(paddle_lang)
            logger.info(
                f"OCRService: PaddleOCR engine for ui_lang='{lang}' "
                f"(paddle_lang='{paddle_lang}')"
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_text(self, image_path: str) -> str:
        """Extract text from an image file."""
        try:
            img = Image.open(image_path).convert('RGB')
            return self.extract_text_from_pil(img)
        except Exception as e:
            logger.error(f"Error loading image '{image_path}': {e}")
            return ''

    def extract_text_from_pil(self, pil_image: Image.Image) -> str:
        """Extract text from a PIL Image object."""
        try:
            if self._engine == 'tesseract':
                return self._tesseract_ocr(pil_image)
            else:
                return self._paddle_ocr(pil_image)
        except Exception as e:
            logger.error(f"OCR error (engine={self._engine}, lang={self.ui_lang}): {e}")
            return ''

    # ------------------------------------------------------------------
    # Internal engine implementations
    # ------------------------------------------------------------------

    def _tesseract_ocr(self, pil_image: Image.Image) -> str:
        """High-accuracy Tesseract OCR for Indic scripts."""
        # OEM 1 = LSTM neural net only (most accurate in Tesseract 5)
        # PSM 3 = Fully automatic page segmentation (default, good for documents)
        config = f'--oem 1 --psm 3'
        text = self._pytesseract.image_to_string(
            pil_image,
            lang=self._tess_lang,
            config=config
        )
        return text.strip()

    def _paddle_ocr(self, pil_image: Image.Image) -> str:
        """PaddleOCR for CJK, Arabic, European scripts."""
        img_array = np.array(pil_image.convert('RGB'))
        result = self._paddle.ocr(img_array)
        if not result or not result[0]:
            return ''
        lines = [line[1][0].strip() for line in result[0] if line[1][0].strip()]
        return '\n'.join(lines)
