import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import logging
import config
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self):
        self.sender = config.GMAIL_SENDER
        self.password = config.GMAIL_APP_PASSWORD
        self.recipient = config.RECIPIENT_EMAIL

    def send_podcast(self, mp3_path, research_brief, sources_used=None, mp3_url=None):
        if not all([self.sender, self.password, self.recipient]):
            logger.warning("Email credentials missing. Skipping email delivery.")
            return

        company = research_brief.get('company_name', 'Unknown')
        symbol = research_brief.get('symbol', 'Unknown')
        date_str = datetime.now().strftime('%d %b %Y')
        subject = f"🎙️ Market Duel: {company} ({symbol}) — {date_str}"

        msg = MIMEMultipart()
        msg['From'] = self.sender
        msg['To'] = self.recipient
        msg['Subject'] = subject

        html = self._build_html(
            company, symbol, date_str,
            research_brief, sources_used or [],
            mp3_url
        )
        msg.attach(MIMEText(html, 'html'))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.sender, self.password)
                server.send_message(msg)
            logger.info("Email sent successfully!")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def _build_html(self, company, symbol, date_str, brief, sources_used, mp3_url):
        positives_html = "".join(f"<li>{p}</li>" for p in brief.get('key_positives', []))
        risks_html = "".join(f"<li>{r}</li>" for r in brief.get('key_risks', []))
        sources_html = "".join(
            f'<li style="margin-bottom:4px;">{s}</li>'
            for s in sources_used
        )

        # Listen button — shows download link if published, fallback message if not
        if mp3_url:
            listen_block = f"""
    <div style="text-align:center; margin: 24px 0;">
      <a href="{mp3_url}"
         style="background:#1DB954; color:white; padding:14px 32px;
                border-radius:30px; text-decoration:none; font-size:16px;
                font-weight:bold; display:inline-block;">
        ▶ Download &amp; Listen
      </a>
      <p style="color:#aaa; font-size:12px; margin-top:10px;">
        Direct MP3 link — open in any podcast app or browser
      </p>
    </div>"""
        else:
            listen_block = """
    <div style="background:#fff3cd; padding:12px; border-radius:6px; margin:16px 0; font-size:13px; color:#856404;">
      ⚠️ Audio upload failed today — check GitHub Actions for the MP3 artifact.
    </div>"""

        return f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 640px; margin: 0 auto; color: #333;">

  <div style="background: #1a1a2e; color: white; padding: 24px 20px; border-radius: 8px 8px 0 0;">
    <h1 style="margin: 0; font-size: 22px;">🎙️ Market Duel</h1>
    <p style="margin: 6px 0 0; opacity: 0.7; font-size: 14px;">{date_str} — Daily Stock Analysis Podcast</p>
  </div>

  <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; border: 1px solid #eee;">

    <h2 style="color: #1a1a2e; margin-top: 0;">
      {company}
      <span style="color: #888; font-size: 16px; font-weight: normal;">({symbol})</span>
    </h2>
    <p style="color: #555;">{brief.get('company_overview', '')}</p>

    {listen_block}

    <div style="background: white; padding: 14px; border-radius: 6px; margin: 16px 0; border-left: 4px solid #3498db;">
      <strong>💰 Current Price:</strong> {brief.get('current_price', 'N/A')}<br>
      <strong>📊 Valuation:</strong> {brief.get('valuation_snapshot', 'N/A')}<br>
      <strong>📈 Recent Performance:</strong> {brief.get('recent_performance', 'N/A')}
    </div>

    <table style="width: 100%; border-collapse: separate; border-spacing: 8px; margin: 16px 0;">
      <tr>
        <td style="width:50%; vertical-align:top; padding:14px; background:#e8f8f5; border-radius:8px;">
          <h3 style="color:#16a085; margin-top:0;">🐂 Bull Case (Priya)</h3>
          <p style="color:#555; font-size:14px; margin:0;">{brief.get('bull_thesis', 'N/A')}</p>
        </td>
        <td style="width:50%; vertical-align:top; padding:14px; background:#fdf2f2; border-radius:8px;">
          <h3 style="color:#c0392b; margin-top:0;">🐻 Bear Case (Rahul)</h3>
          <p style="color:#555; font-size:14px; margin:0;">{brief.get('bear_thesis', 'N/A')}</p>
        </td>
      </tr>
    </table>

    <h3 style="border-bottom: 2px solid #eee; padding-bottom: 6px;">✅ Key Positives</h3>
    <ul style="font-size:14px; color:#444;">{positives_html}</ul>

    <h3 style="border-bottom: 2px solid #eee; padding-bottom: 6px;">⚠️ Key Risks</h3>
    <ul style="font-size:14px; color:#444;">{risks_html}</ul>

    <div style="background:white; padding:14px; border-radius:6px; margin:16px 0; border-left:4px solid #9b59b6;">
      <strong>📌 Recent Catalysts:</strong> {brief.get('recent_catalysts', 'N/A')}<br><br>
      <strong>🏦 Analyst Sentiment:</strong> {brief.get('analyst_sentiment', 'N/A')}<br><br>
      <strong>🔍 Key Metrics to Watch:</strong> {brief.get('key_metrics_to_watch', 'N/A')}<br><br>
      <strong>📅 Upcoming Events:</strong> {brief.get('upcoming_events', 'N/A')}
    </div>

    <h3 style="border-bottom: 2px solid #eee; padding-bottom: 6px;">📚 Data Sources Used Today</h3>
    <ul style="font-size:13px; color:#555; background:white; padding:14px 14px 14px 30px; border-radius:6px;">
      {sources_html}
    </ul>

    <div style="background:#fff3cd; padding:12px; border-radius:6px; margin-top:16px; font-size:12px; color:#856404;">
      ⚠️ <strong>Disclaimer:</strong> This podcast is for informational purposes only and does not
      constitute investment advice. Always do your own research before making investment decisions.
    </div>

  </div>
</body>
</html>"""
