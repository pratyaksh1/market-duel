import asyncio
import logging
import sys
from datetime import datetime
import config

from company_selector import CompanySelector
from data_fetcher import DataFetcher
from news_fetcher import NewsFetcher
from research_scraper import ResearchScraper
from research_synthesizer import ResearchSynthesizer
from script_writer import ScriptWriter
from tts_engine import TTSEngine
from audio_mixer import AudioMixer
from email_sender import EmailSender
from podcast_publisher import PodcastPublisher

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
    sources_used = []

    try:
        # 1. Company Selection
        selector = CompanySelector()
        company = selector.select_company()
        symbol = company['symbol']
        name = company['name']
        logger.info(f"Today's company: {name} ({symbol})")

        # 2. Market Data
        data_fetcher = DataFetcher()
        raw_market_data = data_fetcher.get_all_data(symbol)

        if raw_market_data.get('nse') and not raw_market_data['nse'].get('error'):
            sources_used.append("✅ NSE India — live price, P/E, 52-week range")
        else:
            sources_used.append("⚠️ NSE India — failed (used yfinance fallback)")

        if raw_market_data.get('financials'):
            sources_used.append("✅ Yahoo Finance (yfinance) — revenue, margins, EBITDA, market cap")

        # 3. News
        news_fetcher = NewsFetcher()
        raw_news_data = news_fetcher.get_all_news(symbol, name)

        news_count = len(raw_news_data.get('news_articles', []))
        ann_count = len(raw_news_data.get('announcements', []))
        shareholding = raw_news_data.get('shareholding_pattern', {})

        if news_count > 0:
            sources_used.append(f"✅ NewsAPI — {news_count} articles (last 7 days)")
        else:
            sources_used.append("⚠️ NewsAPI — no articles found")

        if ann_count > 0:
            sources_used.append(f"✅ NSE Corporate Announcements — {ann_count} announcements")
        else:
            sources_used.append("⚠️ NSE Announcements — none found")

        if shareholding:
            sources_used.append(
                f"✅ NSE Shareholding Pattern — "
                f"Promoter: {shareholding.get('promoter_holding', 'N/A')}%, "
                f"FII: {shareholding.get('fii_holding', 'N/A')}%, "
                f"DII: {shareholding.get('dii_holding', 'N/A')}%"
            )

        # 4. Research Scraping
        scraper = ResearchScraper()
        raw_research_data = scraper.get_research_data(symbol)

        screener = raw_research_data.get('screener', {})
        trendlyne = raw_research_data.get('trendlyne', {})
        pdf_text = raw_research_data.get('investor_presentation_excerpt', '')

        if screener.get('ratios'):
            ratio_count = len(screener['ratios'])
            pros_count = len(screener.get('pros', []))
            cons_count = len(screener.get('cons', []))
            sources_used.append(
                f"✅ Screener.in — {ratio_count} financial ratios, "
                f"{pros_count} positives, {cons_count} risks identified"
            )
        else:
            sources_used.append("⚠️ Screener.in — could not scrape data")

        if trendlyne.get('analyst_consensus') and trendlyne['analyst_consensus'] != 'N/A':
            sources_used.append(
                f"✅ Trendlyne — Analyst consensus: {trendlyne.get('analyst_consensus')}, "
                f"Target: {trendlyne.get('target_price', 'N/A')}"
            )
        else:
            sources_used.append("⚠️ Trendlyne — analyst data unavailable")

        if pdf_text:
            sources_used.append(f"✅ BSE Investor Presentation PDF — {len(pdf_text)} chars extracted")
        else:
            sources_used.append("⚠️ BSE Investor Presentation — not found")

        # Combine all raw data
        full_raw_data = {
            **raw_market_data,
            **raw_news_data,
            **raw_research_data
        }

        # 5. Research Synthesis
        synthesizer = ResearchSynthesizer()
        research_brief = synthesizer.synthesize(full_raw_data)
        sources_used.append("✅ Gemini AI — research brief synthesized")

        # 6. Script Writing
        writer = ScriptWriter()
        script = writer.write_script(research_brief)

        line_count = len([l for l in script.splitlines() if l.startswith(("HOST_A:", "HOST_B:"))])
        if line_count > 10:
            sources_used.append(f"✅ Gemini AI — podcast script generated ({line_count} dialogue lines)")
        else:
            sources_used.append("⚠️ Gemini AI — script generation failed, used fallback")

        # 7. TTS
        tts = TTSEngine()
        segment_paths = await tts.generate_audio_segments(script)
        valid_segments = len([p for p in segment_paths if p])
        sources_used.append(f"✅ Edge TTS — {valid_segments} audio segments rendered")

        # 8. Audio Mixing
        mixer = AudioMixer()
        filename = f"Market_Duel_{symbol}_{datetime.now().strftime('%Y%m%d')}.mp3"
        mp3_path = mixer.mix(segment_paths, script, filename)

        # 9. Publish to GitHub Releases + update RSS feed for Spotify
        mp3_url = ""
        if config.GITHUB_TOKEN and config.GITHUB_REPO:
            publisher = PodcastPublisher()
            mp3_url = publisher.publish(mp3_path, research_brief)
            if mp3_url:
                sources_used.append(f"✅ Published to GitHub Releases — {mp3_url}")
            else:
                sources_used.append("⚠️ GitHub publish failed — check GITHUB_TOKEN secret")
        else:
            sources_used.append("⚠️ GitHub publish skipped — GITHUB_TOKEN/GITHUB_REPO not set")

        # 10. Email (with download link, no attachment)
        sender = EmailSender()
        sender.send_podcast(mp3_path, research_brief, sources_used, mp3_url=mp3_url)

        # 11. Cleanup
        mixer.cleanup(segment_paths)
        selector.save_history(symbol)

        duration = datetime.now() - start_time
        logger.info(f"✅ Pipeline completed successfully in {duration}")
        logger.info("Sources used this run:")
        for s in sources_used:
            logger.info(f"  {s}")

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
