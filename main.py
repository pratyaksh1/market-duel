import asyncio
import logging
import sys
from datetime import datetime
import config

# Import modules
from company_selector import CompanySelector
from data_fetcher import DataFetcher
from news_fetcher import NewsFetcher
from research_scraper import ResearchScraper
from research_synthesizer import ResearchSynthesizer
from script_writer import ScriptWriter
from tts_engine import TTSEngine
from audio_mixer import AudioMixer
from email_sender import EmailSender

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('market_duel.log')
    ]
)
logger = logging.getLogger("MarketDuel")

async def run_pipeline():
    logger.info("🚀 Starting Market Duel Pipeline")
    start_time = datetime.now()

    try:
        # 1. Company Selection
        selector = CompanySelector()
        company = selector.select_company()
        symbol = company['symbol']
        name = company['name']
        
        # 2. Data Fetching
        data_fetcher = DataFetcher()
        raw_market_data = data_fetcher.get_all_data(symbol)
        
        news_fetcher = NewsFetcher()
        raw_news_data = news_fetcher.get_all_news(symbol, name)
        
        # 3. Research Scraping
        scraper = ResearchScraper()
        raw_research_data = scraper.get_research_data(symbol)
        
        # Combine all raw data
        full_raw_data = {
            **raw_market_data,
            **raw_news_data,
            **raw_research_data
        }
        
        # 4. Research Synthesis
        synthesizer = ResearchSynthesizer()
        research_brief = synthesizer.synthesize(full_raw_data)
        
        # 5. Script Writing
        writer = ScriptWriter()
        script = writer.write_script(research_brief)
        
        # 6. TTS Generation
        tts = TTSEngine()
        segment_paths = await tts.generate_audio_segments(script)
        
        # 7. Audio Mixing
        mixer = AudioMixer()
        filename = f"Market_Duel_{symbol}_{datetime.now().strftime('%Y%m%d')}.mp3"
        mp3_path = mixer.mix(segment_paths, script, filename)
        
        # 8. Email Delivery
        sender = EmailSender()
        sender.send_podcast(mp3_path, research_brief)
        
        # 9. Cleanup & History update
        mixer.cleanup(segment_paths)
        selector.save_history(symbol)
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"✅ Pipeline completed successfully in {duration}")

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(run_pipeline())
