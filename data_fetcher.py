import requests
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.nseindia.com/"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._warmup()

    def _warmup(self):
        """NSE requires a visit to the home page to set cookies."""
        try:
            self.session.get("https://www.nseindia.com/", timeout=10)
        except Exception as e:
            logger.error(f"NSE Warmup failed: {e}")

    def fetch_nse_data(self, symbol):
        """Fetch price and basic info from NSE."""
        try:
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "price_info": data.get("priceInfo", {}),
                    "metadata": data.get("metadata", {}),
                    "security_info": data.get("securityInfo", {}),
                }
        except Exception as e:
            logger.error(f"Error fetching NSE data for {symbol}: {e}")
        return {}

    def fetch_financials(self, symbol):
        """Fetch basic financials (can be expanded)."""
        # In a production app, you might use yfinance as a reliable fallback for Indian stocks
        import yfinance as yf
        try:
            ticker = f"{symbol}.NS"
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                "pe_ratio": info.get("trailingPE"),
                "market_cap": info.get("marketCap"),
                "dividend_yield": info.get("dividendYield"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "revenue_growth": info.get("revenueGrowth"),
                "profit_margins": info.get("profitMargins"),
                "ebitda": info.get("ebitda"),
            }
        except Exception as e:
            logger.error(f"Error fetching financials for {symbol}: {e}")
        return {}

    def get_all_data(self, symbol):
        logger.info(f"Fetching data for {symbol}...")
        nse_data = self.fetch_nse_data(symbol)
        financials = self.fetch_financials(symbol)
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "nse": nse_data,
            "financials": financials
        }
