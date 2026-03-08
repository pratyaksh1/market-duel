import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
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

    def send_podcast(self, mp3_path, research_brief):
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

        # HTML Body
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2c3e50;">Market Duel: Daily Analysis</h2>
            <p>Today we dive deep into <strong>{company} ({symbol})</strong>.</p>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 50%; vertical-align: top; padding: 10px; background: #e8f8f5; border-radius: 8px;">
                        <h3 style="color: #16a085;">The Bull Case (Priya)</h3>
                        <p>{research_brief.get('bull_thesis', 'N/A')}</p>
                    </td>
                    <td style="width: 50%; vertical-align: top; padding: 10px; background: #fdf2f2; border-radius: 8px;">
                        <h3 style="color: #c0392b;">The Bear Case (Rahul)</h3>
                        <p>{research_brief.get('bear_thesis', 'N/A')}</p>
                    </td>
                </tr>
            </table>

            <div style="margin-top: 20px;">
                <h3 style="border-bottom: 2px solid #eee;">Key Highlights</h3>
                <ul>
                    {"".join([f"<li>{p}</li>" for p in research_brief.get('key_positives', [])])}
                </ul>
                
                <h3 style="border-bottom: 2px solid #eee;">Key Risks</h3>
                <ul>
                    {"".join([f"<li>{r}</li>" for r in research_brief.get('key_risks', [])])}
                </ul>
            </div>

            <div style="margin-top: 20px; padding: 15px; background: #f9f9f9; border-left: 4px solid #3498db;">
                <p><strong>Current Price:</strong> {research_brief.get('current_price', 'N/A')}</p>
                <p><strong>Valuation:</strong> {research_brief.get('valuation_snapshot', 'N/A')}</p>
                <p><strong>Recent Catalysts:</strong> {research_brief.get('recent_catalysts', 'N/A')}</p>
            </div>

            <p style="font-size: 12px; color: #7f8c8d; margin-top: 30px;">
                <em>Disclaimer: This podcast is for informational purposes only and does not constitute investment advice. Please consult with a financial advisor before making any investment decisions.</em>
            </p>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html'))

        # Attachment
        try:
            with open(mp3_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {os.path.basename(mp3_path)}",
                )
                msg.attach(part)
        except Exception as e:
            logger.error(f"Failed to attach MP3: {e}")

        # Send
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.sender, self.password)
                server.send_message(msg)
            logger.info("Email sent successfully!")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
