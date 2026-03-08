import google.genai as genai
import json
import logging
import config

logger = logging.getLogger(__name__)

# Try models in order until one works
MODELS_TO_TRY = [
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
]

class ResearchSynthesizer:
    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)

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

        for model in MODELS_TO_TRY:
            try:
                logger.info(f"Trying model: {model}")
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json"
                    )
                )
                result = json.loads(response.text)
                logger.info(f"Gemini synthesis succeeded with {model}")
                return result
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                continue

        logger.error("All Gemini models failed for synthesis")
        return {
            "company_name": raw_data.get('symbol'),
            "symbol": raw_data.get('symbol'),
            "company_overview": "Data synthesis failed — all models exhausted.",
            "current_price": "N/A",
            "key_positives": [],
            "key_risks": [],
            "bull_thesis": "N/A",
            "bear_thesis": "N/A"
        }
