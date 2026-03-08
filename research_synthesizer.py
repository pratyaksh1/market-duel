import google.genai as genai
import json
import logging
import time
import re
import config

logger = logging.getLogger(__name__)

# Only use gemini-flash-latest — this is Gemini 3 Flash on your project
# Do NOT fall back to gemini-2.0-flash — it has limit:0 on this account
MODEL = "gemini-flash-latest"
MAX_RETRIES = 3
RETRY_DELAYS = [10, 30, 60]  # seconds between retries on 503


class ResearchSynthesizer:
    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
        self.client = genai.Client(
            api_key=config.GEMINI_API_KEY,
            http_options={"api_version": "v1beta"}
        )

    def synthesize(self, raw_data):
        logger.info("Synthesizing research brief using Gemini...")

        prompt = f"""
        You are a senior equity research analyst specializing in the Indian stock market.
        Analyze the following raw data for {raw_data['symbol']} and create a structured JSON research brief.

        RAW DATA:
        {json.dumps(raw_data, indent=2)}

        OUTPUT FORMAT (JSON ONLY):
        {{
            "company_name": "...",
            "symbol": "...",
            "company_overview": "...",
            "current_price": "...",
            "valuation_snapshot": "...",
            "recent_performance": "...",
            "key_positives": ["point 1", "point 2", "point 3", "point 4"],
            "key_risks": ["point 1", "point 2", "point 3"],
            "recent_catalysts": "...",
            "analyst_sentiment": "...",
            "bull_thesis": "...",
            "bear_thesis": "...",
            "price_context": "...",
            "sector_context": "...",
            "key_metrics_to_watch": "...",
            "upcoming_events": "..."
        }}

        Rules:
        1. Return ONLY valid JSON.
        2. No markdown formatting, no backticks, no preamble.
        3. Be objective and data-driven.
        4. Use Indian numbering system (Lakhs/Crores) where appropriate.
        """

        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Synthesis attempt {attempt + 1}/{MAX_RETRIES} using {MODEL}...")
                response = self.client.models.generate_content(
                    model=MODEL,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json"
                    )
                )
                result = json.loads(response.text)
                logger.info(f"Gemini synthesis succeeded on attempt {attempt + 1}")
                return result

            except Exception as e:
                error_str = str(e)
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_DELAYS[attempt]
                    # If API gives us a retry delay, use that instead
                    match = re.search(r'"retryDelay":\s*"(\d+)s"', error_str)
                    if match:
                        wait = int(match.group(1)) + 5
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"All {MAX_RETRIES} synthesis attempts failed: {e}")

        return {
            "company_name": raw_data.get('symbol'),
            "symbol": raw_data.get('symbol'),
            "company_overview": "Data synthesis failed — model temporarily unavailable.",
            "current_price": "N/A",
            "key_positives": [],
            "key_risks": [],
            "bull_thesis": "N/A",
            "bear_thesis": "N/A"
        }
