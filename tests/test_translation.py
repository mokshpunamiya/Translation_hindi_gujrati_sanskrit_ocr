import os
import sys
import logging
from app.services.translation_service import TranslationService
from config.settings import Config

logging.basicConfig(level=logging.INFO)

def test_translate():
    print("Testing TranslationService...")
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        print("Warning: GEMINI_API_KEY not set in environment or config. Using dummy test text but translation will fall back.")
        # We can still test that it returns the original text
    
    translator = TranslationService(api_key=api_key)
    
    text_to_translate = "Bonjour tout le monde"
    print(f"Original text: {text_to_translate}")
    
    result = translator.translate(text_to_translate, target_language="English")
    print(f"Translated text: {result}")
    
    # If API key is not set, it returns the original text
    if api_key:
        assert text_to_translate not in result or text_to_translate.lower() == result.lower(), "Translation failed, returned original string unexpectedly"
        assert "Hello" in result or "everybody" in result.lower() or "everyone" in result.lower(), f"Unexpected translation: {result}"
        print("TranslationService test passed (with API call)!")
    else:
        assert result == text_to_translate, "Fallback mechanism failed"
        print("TranslationService test passed (fallback mechanism)!")

if __name__ == "__main__":
    test_translate()
