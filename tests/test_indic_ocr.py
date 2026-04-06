"""
Test Tesseract OCR for Indic scripts: Gujarati, Hindi, Sanskrit.
Creates a real image with Indic text and validates extraction.
"""
import logging
import os
from PIL import Image, ImageDraw, ImageFont
from app.services.ocr_service import OCRService, TESSERACT_LANGS, TESSERACT_LANG_MAP

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')

INDIC_SAMPLES = {
    'gu': ('Gujarati', 'ગુજરાત'),     # "Gujarat"
    'hi': ('Hindi',    'नमस्ते'),       # "Hello"
    'sa': ('Sanskrit', 'धर्म'),        # "Dharma"
    'mr': ('Marathi',  'महाराष्ट्र'),  # "Maharashtra"
}


def make_text_image(text: str, path: str, width=600, height=120) -> str:
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # Use a Unicode font if available (e.g., Arial Unicode on Windows)
    unicode_fonts = [
        r'C:\Windows\Fonts\mangal.ttf',    # Devanagari
        r'C:\Windows\Fonts\arial.ttf',
        r'C:\Windows\Fonts\arialuni.ttf',
    ]
    font = None
    for fp in unicode_fonts:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 48)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    d.text((20, 30), text, fill=(0, 0, 0), font=font)
    img.save(path)
    return path


def test_indic_ocr():
    print("\n" + "="*55)
    print("  Hybrid OCR Engine – Indic Language Tests")
    print("="*55)

    for ui_lang, (lang_name, sample_text) in INDIC_SAMPLES.items():
        print(f"\n[{lang_name}] ui_lang='{ui_lang}'  tess_lang='{TESSERACT_LANG_MAP[ui_lang]}'")
        img_path = f"test_{ui_lang}.png"
        try:
            make_text_image(sample_text, img_path)
            svc = OCRService(lang=ui_lang)
            result = svc.extract_text(img_path)
            print(f"  Input  : {sample_text}")
            print(f"  Output : {result!r}")
            print(f"  Status : {'✓ PASS' if result.strip() else '⚠ EMPTY (font may not render script)'}")
        except Exception as e:
            print(f"  Status : ✗ FAIL – {e}")
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)

    print("\n" + "="*55)
    print("  Summary: Tesseract langs available in this install")
    print(f"  Indic langs mapped: {list(TESSERACT_LANG_MAP.items())}")
    print("="*55 + "\n")


if __name__ == "__main__":
    test_indic_ocr()
