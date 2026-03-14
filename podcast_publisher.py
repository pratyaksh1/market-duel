"""
Podcast Publisher
Uploads MP3 to GitHub Releases and updates the RSS feed on GitHub Pages.
Spotify, Apple Podcasts, and Google Podcasts all read the RSS feed automatically.
"""

import os
import json
import requests
import logging
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # e.g. "pratyaksh1/market-duel"
GITHUB_PAGES_BRANCH = "gh-pages"
FEED_FILE = "feed.xml"

PODCAST_TITLE = "Market Duel"
PODCAST_DESCRIPTION = "Daily bull vs bear debate on one Indian stock. Two AI hosts, Priya and Rahul, debate the fundamentals, valuation, and catalysts every weekday morning."
PODCAST_AUTHOR = "Market Duel AI"
PODCAST_EMAIL = os.getenv("GMAIL_SENDER", "podcast@marketduel.ai")
PODCAST_LANGUAGE = "en-in"
PODCAST_CATEGORY = "Business"


class PodcastPublisher:
    def __init__(self):
        self.token = GITHUB_TOKEN
        self.repo = GITHUB_REPO
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.api_base = f"https://api.github.com/repos/{self.repo}"
        self.pages_url = f"https://{self.repo.split('/')[0]}.github.io/{self.repo.split('/')[1]}"

    # ── Step 1: Upload MP3 to GitHub Releases ────────────────────────────────

    def upload_to_github_releases(self, mp3_path: str, symbol: str, date_str: str) -> str:
        """
        Creates a GitHub Release and uploads the MP3 as an asset.
        Returns the public download URL of the MP3.
        """
        if not self.token or not self.repo:
            logger.error("GITHUB_TOKEN or GITHUB_REPO not set — cannot publish")
            return ""

        tag = f"episode-{symbol.lower()}-{date_str}"
        release_name = f"Market Duel: {symbol} — {date_str}"
        filename = os.path.basename(mp3_path)

        # 1. Create the release
        logger.info(f"Creating GitHub Release: {release_name}")
        release_resp = requests.post(
            f"{self.api_base}/releases",
            headers=self.headers,
            json={
                "tag_name": tag,
                "name": release_name,
                "body": f"Daily Market Duel episode for {symbol} on {date_str}",
                "draft": False,
                "prerelease": False,
            }
        )

        if release_resp.status_code not in (200, 201):
            logger.error(f"Failed to create release: {release_resp.text[:300]}")
            return ""

        release_data = release_resp.json()
        upload_url = release_data["upload_url"].replace("{?name,label}", "")
        release_id = release_data["id"]

        # 2. Upload MP3 as release asset
        logger.info(f"Uploading MP3 to release: {filename}")
        with open(mp3_path, "rb") as f:
            mp3_data = f.read()

        asset_resp = requests.post(
            f"{upload_url}?name={filename}",
            headers={
                **self.headers,
                "Content-Type": "audio/mpeg",
            },
            data=mp3_data
        )

        if asset_resp.status_code not in (200, 201):
            logger.error(f"Failed to upload MP3 asset: {asset_resp.text[:300]}")
            return ""

        mp3_url = asset_resp.json()["browser_download_url"]
        logger.info(f"MP3 uploaded successfully: {mp3_url}")
        return mp3_url

    # ── Step 2: Update RSS feed.xml on GitHub Pages ───────────────────────────

    def update_rss_feed(self, mp3_url: str, mp3_path: str, research_brief: dict, date_str: str):
        """
        Fetches current feed.xml from gh-pages branch,
        prepends new episode, and pushes updated feed back.
        """
        if not mp3_url:
            logger.error("No MP3 URL — skipping RSS feed update")
            return

        company = research_brief.get("company_name", "Unknown")
        symbol = research_brief.get("symbol", "Unknown")
        bull_thesis = research_brief.get("bull_thesis", "")
        bear_thesis = research_brief.get("bear_thesis", "")
        mp3_size = os.path.getsize(mp3_path)

        # Episode details
        episode_title = f"{company} ({symbol}) — Bull vs Bear | {date_str}"
        episode_description = (
            f"Today's Market Duel covers {company} ({symbol}). "
            f"Bull case: {bull_thesis[:200]}... "
            f"Bear case: {bear_thesis[:200]}..."
        )
        pub_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

        # Fetch existing feed from gh-pages (or create fresh)
        existing_items_xml = self._fetch_existing_feed_items()

        # Build new episode XML block
        new_item = f"""
  <item>
    <title>{self._escape_xml(episode_title)}</title>
    <description>{self._escape_xml(episode_description)}</description>
    <enclosure url="{mp3_url}" length="{mp3_size}" type="audio/mpeg"/>
    <guid isPermaLink="false">{mp3_url}</guid>
    <pubDate>{pub_date}</pubDate>
    <itunes:duration>{self._get_duration(mp3_path)}</itunes:duration>
    <itunes:explicit>false</itunes:explicit>
  </item>"""

        # Prepend new episode to existing items (newest first)
        all_items = new_item + existing_items_xml

        # Build full feed
        feed_xml = self._build_full_feed(all_items)

        # Push to gh-pages branch
        self._push_feed_to_github(feed_xml)
        logger.info(f"RSS feed updated with new episode: {episode_title}")

    def _fetch_existing_feed_items(self) -> str:
        """Fetch existing episode items from gh-pages feed.xml"""
        try:
            url = f"{self.api_base}/contents/{FEED_FILE}?ref={GITHUB_PAGES_BRANCH}"
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 200:
                import base64
                content = base64.b64decode(resp.json()["content"]).decode("utf-8")
                # Extract just the <item> blocks
                items_start = content.find("<item>")
                items_end = content.rfind("</item>") + len("</item>")
                if items_start != -1 and items_end > items_start:
                    return "\n" + content[items_start:items_end]
        except Exception as e:
            logger.warning(f"Could not fetch existing feed: {e}")
        return ""

    def _build_full_feed(self, items_xml: str) -> str:
        """Build the complete RSS feed XML"""
        feed_url = f"{self.pages_url}/{FEED_FILE}"
        now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
  xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{PODCAST_TITLE}</title>
    <description>{PODCAST_DESCRIPTION}</description>
    <link>{self.pages_url}</link>
    <language>{PODCAST_LANGUAGE}</language>
    <lastBuildDate>{now}</lastBuildDate>
    <itunes:author>{PODCAST_AUTHOR}</itunes:author>
    <itunes:email>{PODCAST_EMAIL}</itunes:email>
    <itunes:category text="{PODCAST_CATEGORY}"/>
    <itunes:explicit>false</itunes:explicit>
    <itunes:image href="{self.pages_url}/cover.jpg"/>
    <atom:link href="{feed_url}" rel="self" type="application/rss+xml" xmlns:atom="http://www.w3.org/2005/Atom"/>
{items_xml}
  </channel>
</rss>"""

    def _push_feed_to_github(self, feed_xml: str):
        """Push updated feed.xml to the gh-pages branch"""
        import base64

        encoded = base64.b64encode(feed_xml.encode("utf-8")).decode("utf-8")

        # Check if file already exists (need its SHA to update)
        sha = None
        check_resp = requests.get(
            f"{self.api_base}/contents/{FEED_FILE}?ref={GITHUB_PAGES_BRANCH}",
            headers=self.headers
        )
        if check_resp.status_code == 200:
            sha = check_resp.json().get("sha")

        payload = {
            "message": f"Update RSS feed — {datetime.now().strftime('%Y-%m-%d')}",
            "content": encoded,
            "branch": GITHUB_PAGES_BRANCH,
        }
        if sha:
            payload["sha"] = sha  # Required when updating existing file

        push_resp = requests.put(
            f"{self.api_base}/contents/{FEED_FILE}",
            headers=self.headers,
            json=payload
        )

        if push_resp.status_code in (200, 201):
            logger.info("feed.xml pushed to gh-pages successfully")
        else:
            logger.error(f"Failed to push feed.xml: {push_resp.text[:300]}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_duration(self, mp3_path: str) -> str:
        """Get MP3 duration in HH:MM:SS format for iTunes"""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(mp3_path)
            total_seconds = int(len(audio) / 1000)
            h = total_seconds // 3600
            m = (total_seconds % 3600) // 60
            s = total_seconds % 60
            return f"{h:02d}:{m:02d}:{s:02d}"
        except Exception:
            return "00:30:00"  # fallback estimate

    def _escape_xml(self, text: str) -> str:
        """Escape special characters for XML"""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))

    # ── Master publish method ─────────────────────────────────────────────────

    def publish(self, mp3_path: str, research_brief: dict) -> str:
        """
        Full publish flow:
        1. Upload MP3 to GitHub Releases
        2. Update RSS feed on GitHub Pages
        Returns the Spotify-ready RSS feed URL
        """
        symbol = research_brief.get("symbol", "UNKNOWN")
        date_str = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Publishing episode for {symbol}...")

        # Step 1 — Upload MP3
        mp3_url = self.upload_to_github_releases(mp3_path, symbol, date_str)

        if not mp3_url:
            logger.error("MP3 upload failed — episode not published")
            return ""

        # Step 2 — Update RSS feed
        self.update_rss_feed(mp3_url, mp3_path, research_brief, date_str)

        feed_url = f"{self.pages_url}/{FEED_FILE}"
        logger.info(f"Episode published! RSS feed: {feed_url}")
        return mp3_url
