# 🎙️ Market Duel: Automated Indian Stock Podcast

Market Duel is a production-ready automated pipeline that generates a daily 30-minute stock analysis podcast focused on the Indian markets (NSE/BSE). It features two AI hosts, Priya (Bull) and Rahul (Bear), debating a selected stock using real-time data.

## 🚀 How it Works
1. **Selection**: Picks a stock from your watchlist or NSE top movers.
2. **Data**: Fetches prices (NSE), news (NewsAPI), financials (Screener), and analyst ratings (Trendlyne).
3. **Synthesis**: Gemini 1.5 Flash analyzes the data into a research brief.
4. **Script**: Gemini writes a 4500-word conversational script.
5. **Audio**: Edge TTS (free) or ElevenLabs generates high-quality voices.
6. **Delivery**: Stitches the audio and emails the MP3 to your inbox.

---

## 🚀 GitHub Setup & Automation

To get this running automatically every morning:

1. **Create a Repo**: Create a new repository on GitHub.
2. **Push Code**:
   ```bash
   git init
   git add .
   git commit -m "Initial setup"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```
3. **Add Secrets**: Go to **Settings > Secrets and variables > Actions** and add:
   - `GEMINI_API_KEY`
   - `NEWS_API_KEY`
   - `GMAIL_SENDER`
   - `GMAIL_APP_PASSWORD`
   - `RECIPIENT_EMAIL`
4. **Enable Actions**: The workflow is in `.github/workflows/daily_podcast.yml`. It will run at 8:00 AM IST daily. You can also trigger it manually from the **Actions** tab.

---

## 🛠️ Setup Instructions

### 1. Get Your API Keys
* **Gemini API Key**: Go to [Google AI Studio](https://aistudio.google.com/) and create a free API key.
* **NewsAPI Key**: Register at [newsapi.org](https://newsapi.org/) for a free key.
* **Gmail App Password**: 
  1. Enable 2FA on your Google Account.
  2. Go to [App Passwords](https://myaccount.google.com/apppasswords).
  3. Create a new app password for "Mail".

### 2. Configure GitHub Secrets
If running via GitHub Actions (recommended), add these to **Settings > Secrets and variables > Actions**:
* `GEMINI_API_KEY`
* `NEWS_API_KEY`
* `GMAIL_SENDER`
* `GMAIL_APP_PASSWORD`
* `RECIPIENT_EMAIL`

### 3. Local Development
1. Clone the repo.
2. Install [FFmpeg](https://ffmpeg.org/download.html) (required for audio mixing).
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file based on `.env.example`.
5. Run the pipeline:
   ```bash
   python main.py
   ```

---

## 📁 File Structure
* `main.py`: The orchestrator.
* `company_selector.py`: Handles stock rotation logic.
* `data_fetcher.py`: NSE/BSE and YFinance data.
* `news_fetcher.py`: NewsAPI integration.
* `research_scraper.py`: Web scraping for Screener.in.
* `research_synthesizer.py`: Gemini data analysis logic.
* `script_writer.py`: Gemini dialogue generation.
* `tts_engine.py`: Audio generation (Edge TTS/ElevenLabs).
* `audio_mixer.py`: Pydub stitching and normalization.
* `email_sender.py`: SMTP delivery with HTML formatting.

## ⚖️ Disclaimer
This project is for educational and informational purposes only. It does not constitute financial advice. Always perform your own research before investing.
