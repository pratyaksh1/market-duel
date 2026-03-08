"""
News Fetcher
Pulls recent news from NewsAPI + live NSE corporate announcements
"""

import requests
import logging
import time
import config
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NewsFetcher:
    def __init__(self):
        self.api_key = config.NEWS_API_KEY
        self.nse_session = requests.Session()
        self.nse_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com",
        }
        self._warmup_nse()

    def _warmup_nse(self):
        """NSE requires a homepage visit to set session cookies"""
        try:
            self.nse_session.get(
                "https://www.nseindia.com",
                headers=self.nse_headers,
                timeout=10
            )
            time.sleep(1)
        except Exception as e:
            logger.warning(f"NSE warmup failed: {e}")

    # ── NewsAPI ───────────────────────────────────────────────────────────────

    def fetch_latest_news(self, company_name: str) -> list:
        """Fetch last 7 days of news from NewsAPI"""
        if not self.api_key:
            logger.warning("NEWS_API_KEY not set — skipping NewsAPI fetch")
            return []

        try:
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": f'"{company_name}" stock India',
                    "from": from_date,
                    "sortBy": "relevancy",
                    "language": "en",
                    "pageSize": 10,
                    "apiKey": self.api_key,
                },
                timeout=10,
            )

            if resp.status_code != 200:
                logger.warning(f"NewsAPI returned {resp.status_code}: {resp.text[:200]}")
                return []

            articles = resp.json().get("articles", [])
            return [
                {
                    "title": a.get("title", ""),
                    "description": a.get("description", ""),
                    "source": a.get("source", {}).get("name", ""),
                    "url": a.get("url", ""),
                    "published_at": a.get("publishedAt", ""),
                }
                for a in articles
                if a.get("title") and "[Removed]" not in a.get("title", "")
            ]
        except Exception as e:
            logger.error(f"NewsAPI fetch failed for {company_name}: {e}")
            return []

    # ── NSE Corporate Announcements ───────────────────────────────────────────

    def fetch_corporate_announcements(self, symbol: str) -> list:
        """Fetch official NSE corporate announcements (earnings, AGM, board meetings, etc.)"""
        try:
            url = (
                "https://www.nseindia.com/api/corporate-announcements"
                f"?index=equities&symbol={symbol}"
            )
            resp = self.nse_session.get(url, headers=self.nse_headers, timeout=10)

            if resp.status_code != 200:
                logger.warning(f"NSE announcements returned {resp.status_code} for {symbol}")
                return self._fetch_bse_announcements(symbol)

            data = resp.json()
            announcements = data if isinstance(data, list) else []

            return [
                {
                    "subject": a.get("subject", ""),
                    "date": a.get("an_dt", ""),
                    "description": a.get("desc", ""),
                }
                for a in announcements[:10]
                if a.get("subject")
            ]

        except Exception as e:
            logger.error(f"NSE announcements fetch failed for {symbol}: {e}")
            return self._fetch_bse_announcements(symbol)

    def _fetch_bse_announcements(self, symbol: str) -> list:
        """BSE fallback for corporate announcements"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.bseindia.com/",
            }
            # BSE announcements search by company name
            url = (
                f"https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
                f"?pageno=1&strCat=-1&strPrevDate=&strScrip=&strSearch=P"
                f"&strToDate=&strType=C&subcategory=-1"
            )
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("Table", [])[:10]
                return [
                    {
                        "subject": item.get("NEWSSUB", ""),
                        "date": item.get("NEWS_DT", ""),
                        "description": item.get("HEADLINE", ""),
                    }
                    for item in items
                    if item.get("NEWSSUB")
                ]
        except Exception as e:
            logger.warning(f"BSE announcements fallback failed: {e}")
        return []

    # ── NSE Shareholding Pattern ──────────────────────────────────────────────

    def fetch_shareholding(self, symbol: str) -> dict:
        """Fetch latest shareholding pattern from NSE"""
        try:
            url = f"https://www.nseindia.com/api/corporate-share-holdings-equities?symbol={symbol}&industry=&isin="
            resp = self.nse_session.get(url, headers=self.nse_headers, timeout=10)

            if resp.status_code == 200:
                data = resp.json()
                records = data.get("data", [])
                if records:
                    latest = records[0]  # Most recent quarter
                    return {
                        "promoter_holding": latest.get("promoter", "N/A"),
                        "fii_holding": latest.get("fii", "N/A"),
                        "dii_holding": latest.get("dii", "N/A"),
                        "public_holding": latest.get("public", "N/A"),
                        "period": latest.get("date", "N/A"),
                    }
        except Exception as e:
            logger.warning(f"Shareholding fetch failed for {symbol}: {e}")
        return {}

    # ── Master method ─────────────────────────────────────────────────────────

    def get_all_news(self, symbol: str, company_name: str) -> dict:
        logger.info(f"Fetching news and announcements for {company_name}...")

        news = self.fetch_latest_news(company_name)
        announcements = self.fetch_corporate_announcements(symbol)
        shareholding = self.fetch_shareholding(symbol)

        logger.info(
            f"Got {len(news)} news articles, "
            f"{len(announcements)} announcements for {symbol}"
        )

        return {
            "news_articles": news,
            "announcements": announcements,
            "shareholding_pattern": shareholding,
        }
