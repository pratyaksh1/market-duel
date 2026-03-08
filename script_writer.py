import google.genai as genai
import logging
import config

logger = logging.getLogger(__name__)

class ScriptWriter:
    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)

    def write_script(self, research_brief):
        logger.info("Generating podcast script using Gemini...")

        prompt = f"""
        You are a professional podcast scriptwriter. Write a 30-minute podcast script titled "Market Duel" featuring two hosts: Priya (HOST_A) and Rahul (HOST_B).

        RESEARCH BRIEF:
        {research_brief}

        CHARACTERS:
        - Priya (HOST_A): Bullish, optimistic but data-driven, sharp, professional yet friendly.
        - Rahul (HOST_B): Bearish, skeptical, focuses on risks and valuations, "devil's advocate".

        TONE:
        Smart, conversational, like two sharp friends debating over chai. Use intermediate financial terminology (P/E, EBITDA, margins, ROE).

        STRUCTURE (Total ~4500 words):
        1. Cold open — Priya introduces show + company (2 min)
        2. Company overview — both introduce the business (3 min)
        3. The numbers — financials and valuation discussion (5 min)
        4. Bull case — Priya argues for, Rahul pushes back (8 min)
        5. Bear case — Rahul argues against, Priya pushes back (8 min)
        6. Recent catalysts — discuss news and announcements (4 min)
        7. Verdict and close — personal takes, what to watch (5 min)

        OUTPUT FORMAT:
        Alternating lines of HOST_A: and HOST_B: only.
        No stage directions, no headers, no asterisks, no music cues.
        Example:
        HOST_A: Welcome to Market Duel. I'm Priya.
        HOST_B: And I'm Rahul. Today we're looking at...

        Rules:
        - Target length is approximately 4500 words.
        - Ensure the debate is balanced and intellectually honest.
        - Use the provided research brief extensively.
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.7
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini script writing failed: {e}")
            return "HOST_A: Error generating script.\nHOST_B: Please check logs."
