"""
Research Scraper
Scrapes Screener.in, Trendlyne, and BSE investor presentations (PDFs)
"""

import requests
from bs4 import BeautifulSoup
import logging
import os
import re
import fitz  # PyMuPDF
import config

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


class ResearchScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    # ── Screener.in ───────────────────────────────────────────────────────────

    def scrape_screener(self, symbol: str) -> dict:
        """Scrape key ratios, pros, cons, and quarterly results from Screener.in"""
        try:
            url = f"https://www.screener.in/company/{symbol}/consolidated/"
            resp = self.session.get(url, timeout=15)

            # Some symbols don't have consolidated view — fallback to standalone
            if resp.status_code == 404:
                url = f"https://www.screener.in/company/{symbol}/"
                resp = self.session.get(url, timeout=15)

            if resp.status_code != 200:
                logger.warning(f"Screener returned {resp.status_code} for {symbol}")
                return {}

            soup = BeautifulSoup(resp.content, "lxml")

            ratios = self._parse_screener_ratios(soup)
            pros, cons = self._parse_screener_pros_cons(soup)
            quarterly = self._parse_screener_quarterly(soup)
            peer_comparison = self._parse_screener_peers(soup)

            return {
                "ratios": ratios,
                "pros": pros,
                "cons": cons,
                "quarterly_results": quarterly,
                "peer_comparison": peer_comparison,
            }

        except Exception as e:
            logger.error(f"Screener scrape failed for {symbol}: {e}")
            return {}

    def _parse_screener_ratios(self, soup) -> dict:
        ratios = {}
        try:
            ratio_list = soup.find("ul", id="top-ratios")
            if ratio_list:
                for li in ratio_list.find_all("li"):
                    name_tag = li.find("span", class_="name")
                    value_tag = li.find("span", class_="number")
                    if name_tag and value_tag:
                        ratios[name_tag.get_text(strip=True)] = value_tag.get_text(strip=True)
        except Exception as e:
            logger.warning(f"Screener ratio parse error: {e}")
        return ratios

    def _parse_screener_pros_cons(self, soup):
        pros, cons = [], []
        try:
            analysis = soup.find("section", id="analysis")
            if analysis:
                pros_div = analysis.find("div", class_="pros")
                if pros_div:
                    pros = [li.get_text(strip=True) for li in pros_div.find_all("li")]
                cons_div = analysis.find("div", class_="cons")
                if cons_div:
                    cons = [li.get_text(strip=True) for li in cons_div.find_all("li")]
        except Exception as e:
            logger.warning(f"Screener pros/cons parse error: {e}")
        return pros, cons

    def _parse_screener_quarterly(self, soup) -> list:
        """Extract last 4 quarters of revenue/profit"""
        results = []
        try:
            section = soup.find("section", id="quarters")
            if section:
                table = section.find("table")
                if table:
                    headers = [th.get_text(strip=True) for th in table.find_all("th")]
                    for row in table.find_all("tr")[1:5]:  # Last 4 rows
                        cells = [td.get_text(strip=True) for td in row.find_all("td")]
                        if cells:
                            results.append(dict(zip(headers, cells)))
        except Exception as e:
            logger.warning(f"Screener quarterly parse error: {e}")
        return results

    def _parse_screener_peers(self, soup) -> list:
        """Extract peer comparison table"""
        peers = []
        try:
            section = soup.find("section", id="peers")
            if section:
                table = section.find("table")
                if table:
                    headers = [th.get_text(strip=True) for th in table.find_all("th")]
                    for row in table.find_all("tr")[1:6]:  # Top 5 peers
                        cells = [td.get_text(strip=True) for td in row.find_all("td")]
                        if cells:
                            peers.append(dict(zip(headers, cells)))
        except Exception as e:
            logger.warning(f"Screener peers parse error: {e}")
        return peers

    # ── Trendlyne ─────────────────────────────────────────────────────────────

    def scrape_trendlyne(self, symbol: str) -> dict:
        """Scrape analyst consensus, target price, and DVM score from Trendlyne"""
        try:
            url = f"https://trendlyne.com/equity/stock-screener/analyze/{symbol}/"
            resp = self.session.get(url, timeout=15)

            if resp.status_code != 200:
                logger.warning(f"Trendlyne returned {resp.status_code} for {symbol}")
                return self._trendlyne_fallback(symbol)

            soup = BeautifulSoup(resp.content, "lxml")

            result = {}

            # Analyst consensus
            consensus_tag = soup.find("span", class_=re.compile(r"analyst.*consensus|consensus.*rating", re.I))
            if consensus_tag:
                result["analyst_consensus"] = consensus_tag.get_text(strip=True)

            # Target price
            target_tag = soup.find(string=re.compile(r"Target Price|target price"))
            if target_tag:
                parent = target_tag.find_parent()
                if parent:
                    result["target_price"] = parent.get_text(strip=True)

            # DVM score (Trendlyne's proprietary quality score)
            dvm_tag = soup.find("div", class_=re.compile(r"dvm|DVM", re.I))
            if dvm_tag:
                result["dvm_score"] = dvm_tag.get_text(strip=True)

            # If we got nothing useful, try the API endpoint
            if not result:
                result = self._trendlyne_fallback(symbol)

            return result

        except Exception as e:
            logger.error(f"Trendlyne scrape failed for {symbol}: {e}")
            return self._trendlyne_fallback(symbol)

    def _trendlyne_fallback(self, symbol: str) -> dict:
        """Try Trendlyne's lighter summary endpoint as fallback"""
        try:
            url = f"https://trendlyne.com/equity/{symbol}/stock-fundamental-analysis/"
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "lxml")
                text = soup.get_text(separator=" ", strip=True)

                result = {}

                # Regex extract Buy/Sell/Hold consensus
                m = re.search(r"(Strong Buy|Buy|Hold|Sell|Strong Sell)", text)
                if m:
                    result["analyst_consensus"] = m.group(1)

                # Regex extract target price
                m = re.search(r"Target\s*Price[:\s₹]*([0-9,]+)", text)
                if m:
                    result["target_price"] = f"₹{m.group(1)}"

                return result
        except Exception as e:
            logger.warning(f"Trendlyne fallback failed for {symbol}: {e}")

        return {"analyst_consensus": "N/A", "target_price": "N/A"}

    # ── BSE Investor Presentations (PDF) ─────────────────────────────────────

    def download_bse_pdf(self, symbol: str) -> str:
        """
        Find and extract text from the most recent investor presentation PDF on BSE.
        Returns extracted text (up to 3000 chars) or empty string.
        """
        try:
            # Search BSE announcements for investor presentations
            bse_code = self._get_bse_code(symbol)
            if not bse_code:
                logger.warning(f"Could not find BSE code for {symbol}")
                return ""

            url = (
                f"https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
                f"?pageno=1&strCat=-1&strPrevDate=&strScrip={bse_code}"
                f"&strSearch=P&strToDate=&strType=C&subcategory=-1"
            )
            resp = self.session.get(url, timeout=10, headers={
                **HEADERS,
                "Referer": "https://www.bseindia.com/",
                "Origin": "https://www.bseindia.com",
            })

            if resp.status_code != 200:
                return ""

            data = resp.json()
            announcements = data.get("Table", [])

            # Find investor presentations or annual reports
            keywords = ["investor presentation", "annual report", "earnings presentation", "quarterly presentation"]
            pdf_url = None

            for ann in announcements[:20]:
                subject = ann.get("NEWSSUB", "").lower()
                attachment = ann.get("ATTACHMENTNAME", "")
                if any(kw in subject for kw in keywords) and attachment:
                    pdf_url = f"https://www.bseindia.com/xml-data/corpfiling/AttachHis/{attachment}"
                    break

            if not pdf_url:
                logger.info(f"No investor presentation PDF found for {symbol} on BSE")
                return ""

            # Download and extract PDF text
            pdf_resp = self.session.get(pdf_url, timeout=20)
            if pdf_resp.status_code != 200:
                return ""

            # Save temp PDF and extract text
            temp_path = os.path.join(config.TEMP_DIR, f"{symbol}_presentation.pdf")
            with open(temp_path, "wb") as f:
                f.write(pdf_resp.content)

            text = self._extract_pdf_text(temp_path)

            # Cleanup
            try:
                os.remove(temp_path)
            except Exception:
                pass

            return text[:3000]  # Cap at 3000 chars

        except Exception as e:
            logger.error(f"BSE PDF download failed for {symbol}: {e}")
            return ""

    def _get_bse_code(self, symbol: str) -> str:
        """Map NSE symbol to BSE scrip code"""
        try:
            url = f"https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w?Group=&Scripcode=&industry=&segment=Equity&status=Active"
            # Use NSE-BSE mapping via search
            search_url = f"https://api.bseindia.com/BseIndiaAPI/api/MktCapData/w?flag=1&ast=E&atype=Q&scrip={symbol}"
            resp = self.session.get(search_url, timeout=10, headers={
                **HEADERS,
                "Referer": "https://www.bseindia.com/",
            })
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list) and len(data) > 0:
                    return str(data[0].get("SCRIP_CD", ""))
        except Exception as e:
            logger.warning(f"BSE code lookup failed for {symbol}: {e}")
        return ""

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            text_parts = []
            for page_num in range(min(10, len(doc))):  # First 10 pages
                page = doc[page_num]
                text_parts.append(page.get_text())
            doc.close()
            return "\n".join(text_parts).strip()
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            return ""

    # ── Master method ─────────────────────────────────────────────────────────

    def get_research_data(self, symbol: str) -> dict:
        logger.info(f"Scraping research data for {symbol}...")

        screener = self.scrape_screener(symbol)
        trendlyne = self.scrape_trendlyne(symbol)
        pdf_text = self.download_bse_pdf(symbol)

        return {
            "screener": screener,
            "trendlyne": trendlyne,
            "investor_presentation_excerpt": pdf_text,
        }
