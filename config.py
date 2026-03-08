import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Email Settings
GMAIL_SENDER = os.getenv("GMAIL_SENDER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

# TTS Settings
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_HOST_A_VOICE_ID = os.getenv("ELEVENLABS_HOST_A_VOICE_ID")
ELEVENLABS_HOST_B_VOICE_ID = os.getenv("ELEVENLABS_HOST_B_VOICE_ID")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(OUTPUT_DIR, "temp")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
WATCHLIST_FILE = os.path.join(BASE_DIR, "watchlist.json")

# Ensure directories exist
os.makedirs(TEMP_DIR, exist_ok=True)

# Podcast Settings
HOST_A_NAME = "Priya"
HOST_B_NAME = "Rahul"
EDGE_TTS_VOICE_A = "en-IN-NeerjaNeural"
EDGE_TTS_VOICE_B = "en-IN-PrabhatNeural"
