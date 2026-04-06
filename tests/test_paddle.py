import os
import sys
from PIL import Image, ImageDraw, ImageFont
from app.services.ocr_service import OCRService
import logging

logging.basicConfig(level=logging.INFO)

def create_test_image(text="Hello PaddleOCR testing text", filename="test_img.png"):
    img = Image.new('RGB', (600, 150), color = (255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        # Try to use a larger font if available, or fallback to default
        font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        font = ImageFont.load_default()
        
    d.text((20, 50), text, fill=(0, 0, 0), font=font)
    img.save(filename)
    return filename

def test_ocr():
    print("Testing PaddleOCR initialization and inference...")
    try:
        ocr = OCRService(lang='en')
        img_path = create_test_image()
        
        print(f"Test image created at {img_path}")
        
        # test from file
        text_from_file = ocr.extract_text(img_path)
        print(f"Extracted from file: '{text_from_file}'")
        
        # test from PIL
        pil_img = Image.open(img_path)
        text_from_pil = ocr.extract_text_from_pil(pil_img)
        print(f"Extracted from PIL: '{text_from_pil}'")
        
        if os.path.exists(img_path):
            os.remove(img_path)
            
        print("Test completed successfully.")
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ocr()
