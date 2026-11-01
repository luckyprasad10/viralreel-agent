import os
import shutil
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import certifi

# Fix Windows libcurl unicode path issue with emoji in workspace directory
try:
    temp_ca = Path(tempfile.gettempdir()) / "cacert.pem"
    if not temp_ca.exists() or temp_ca.stat().st_size == 0:
        shutil.copyfile(certifi.where(), temp_ca)
    os.environ["CURL_CA_BUNDLE"] = str(temp_ca)
    os.environ["SSL_CERT_FILE"] = str(temp_ca)
except Exception:
    pass

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DOWNLOADS_DIR = DATA_DIR / "downloads"
PROCESSED_DIR = DATA_DIR / "processed"
SESSIONS_DIR = DATA_DIR / "sessions"
DB_PATH = DATA_DIR / "viral_bot.db"

# Ensure runtime directories exist
for path in [DATA_DIR, DOWNLOADS_DIR, PROCESSED_DIR, SESSIONS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Instagram Credentials
INSTA_USERNAME = os.getenv("INSTA_USERNAME", "")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD", "")
INSTA_SESSION_FILE = SESSIONS_DIR / "insta_session.json"

# Autonomous Mode & Scheduling
AUTONOMOUS_MODE = os.getenv("AUTONOMOUS_MODE", "true").lower() == "true"
MAX_DAILY_POSTS = int(os.getenv("MAX_DAILY_POSTS", "3"))
PEAK_POSTING_HOURS_IST = ["12:30", "18:00", "21:00"]  # High engagement slots in India

# Trend Discovery Settings (Comedy / Entertainment / Memes)
TARGET_REGIONS = ["US", "GB", "AU"]  # Western viral content unseen in India
SEARCH_KEYWORDS = [
    "comedy",
    "funny memes",
    "viral comedy",
    "hilarious moments",
    "relatable humor",
    "unexpected memes",
    "standup comedy clips"
]

# Virality Filter Criteria
MIN_VIEWS = int(os.getenv("MIN_VIEWS", "50000"))
MIN_LIKES = int(os.getenv("MIN_LIKES", "8000"))
MIN_VIRALITY_RATIO = float(os.getenv("MIN_VIRALITY_RATIO", "0.08"))  # 8% likes-to-views ratio
MIN_DURATION = 8     # Minimum seconds
MAX_DURATION = 60    # Maximum seconds for Reel virality

# Video Processing (Anti-Duplicate Engine)
SPEED_MODIFIER = 1.02      # 2% speed increase (imperceptible to human ear, changes audio/video hashes)
COLOR_FILTER_TWEAK = True  # Subtle contrast/brightness bump to defeat Instagram duplicate deduplication
NORMALIZE_AUDIO = True

# Server Configuration
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "7860"))
