import logging
import time
import random
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self, api_key):
        self.api_key = api_key
        # Rate Limiting configuration
        self.request_timestamps = []
        self.max_requests_per_minute = 14  # Staying safely under the free tier limit (15)

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.model_id = 'gemini-2.5-flash'
            logger.info("Translation service initialized with google-genai (gemini-2.5-flash).")
        else:
            logger.warning("No Gemini API key provided. Translation will not work.")
            self.client = None

    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits (15 requests per minute typical for free tier)."""
        now = time.time()
        # Remove timestamps older than 60 seconds
        self.request_timestamps = [ts for ts in self.request_timestamps if now - ts < 60]

        if len(self.request_timestamps) >= self.max_requests_per_minute:
            # Wait until we can make another request
            oldest = min(self.request_timestamps)
            wait_time = 60 - (now - oldest) + 1
            logger.info(f"API Rate limit approaching, purposefully sleeping for {wait_time:.2f} seconds.")
            time.sleep(wait_time)

        self.request_timestamps.append(time.time())

    def translate(self, text, target_language="English"):
        """Translate text using Gemini with robust exponential backoff and rate limit tracking."""
        if not self.client:
            logger.error("Gemini client not configured. Returning original text.")
            return text

        if not text or not text.strip():
            return ""

        prompt = (
            f"Translate the following text to {target_language}.\n"
            f"If the text is already in {target_language}, return it as-is.\n"
            f"Preserve all formatting and line breaks.\n"
            f"Return ONLY the translated text, nothing else.\n\n"
            f"TEXT:\n{text}"
        )

        max_retries = 5
        for attempt in range(max_retries):
            try:
                # 1) Wait if we are firing requests too fast
                self._wait_for_rate_limit()

                # 2) Call Gemini
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text.strip()
                else:
                    logger.warning(f"Empty translation response on attempt {attempt + 1}")
                    
            except Exception as e:
                err_str = str(e)
                # Check for rate limit / 429 exhaust errors
                if '429' in err_str or 'ResourceExhausted' in err_str or 'RESOURCE_EXHAUSTED' in err_str:
                    wait_time = (2 ** attempt) * 15  # 15s, 30s, 60s, 120s...
                    wait_time += random.uniform(0, 5)  # Jitter
                    
                    if attempt == max_retries - 1:
                        logger.error(f"Rate limit exhausted completely after {max_retries} attempts.")
                        return text
                    
                    logger.warning(f"Google API rate limit hit (429). Attempt {attempt + 1}/{max_retries}. Waiting {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Translation attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        logger.error("All translation attempts failed due to critical errors. Returning original text.")
                        return text
                    time.sleep(2 ** attempt) # standard small backoff for 500s or timeouts

        return text
