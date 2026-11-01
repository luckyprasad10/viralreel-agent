# 🚀 ViralReel AI - Autonomous TikTok to Instagram Reels Agent

An autonomous AI pipeline that discovers trending TikTok videos from global regions (US, UK, Australia) that Indian audiences haven't seen, downloads clean HD videos without watermarks, applies anti-duplicate video transformations, generates high-converting viral hooks, and automatically publishes them as Instagram Reels during peak Indian audience hours.

---

## 🌟 Key Features

1. **Global Trend Arbitrage (Unseen in India)**:
   - TikTok is banned in India; this bot capitalizes on this content vacuum by sourcing top viral entertainment, comedy, and memes from US, UK, and AU feeds.
   - Built-in ISP-block bypass via TikWM & custom user-agent routing (works smoothly inside India without needing a VPN).

2. **Virality Scoring Algorithm**:
   - Scores videos based on engagement velocity:
     $$\text{Virality Score} = \frac{\text{likes} \times 1.5 + \text{comments} \times 2.5 + \text{shares} \times 3.5}{\max(\text{views}, 1)} \times 100$$
   - Prioritizes content with high shareability and debate value over raw passive views.

3. **Anti-Duplicate & Anti-Copyright Engine (FFmpeg)**:
   - **Aspect Ratio Normalization**: Converts to vertical 9:16 (1080x1920) with optimal padding.
   - **Subtle 1.02x Speed Boost**: Modifies both video and audio frequencies, completely altering content hashes so Instagram's algorithm treats it as 100% original content.
   - **Dynamic Color Grading**: Subtle contrast (+3%) and saturation (+5%) enhancement tailored for mobile OLED screens.
   - **Metadata Stripping**: Clears all original TikTok identifiers.

4. **AI Caption & Viral Hook Engine**:
   - Automatically generates psychological curiosity hooks ("Wait for the ending... 😂💀", "Nah bro thought he was slick 🤣").
   - Adds engaging Indian-audience friendly CTAs and targeted hashtags (`#reelsindia #trendingmemes #funnyreels #explorepage`).

5. **Direct Instagram Automation (No Facebook Developer App Required)**:
   - Connects directly to any Instagram account (Personal, Creator, or Business).
   - Session persistence (`insta_session.json`): Log in once with password/2FA, and subsequent operations are 100% hands-free.

6. **Smart Peak-Hour Scheduler**:
   - Posts automatically during Indian peak engagement windows:
     - 🌞 **12:30 PM IST** (Lunch break)
     - 🌆 **06:00 PM IST** (Evening commute)
     - 🌙 **09:00 PM IST** (Prime nighttime entertainment)
   - Configurable daily post limit (default 3 reels/day) to prevent rate-limits.

7. **Ultra-Modern Glassmorphic Control Dashboard**:
   - Toggle between **100% Autonomous Mode** and **Manual Approval Mode** anytime.
   - Live queue viewer with video previews, virality badges, and one-click "Post Now".
   - Real-time live log stream.

---

## 📁 Project Structure

```
TikTok to Insta automation/
├── .venv/                   # Python virtual environment
├── data/
│   ├── downloads/          # Clean downloaded TikTok videos
│   ├── processed/          # 9:16 FFmpeg anti-duplicate processed Reels
│   ├── sessions/           # Saved Instagram login sessions
│   └── viral_bot.db        # SQLite database (videos, queue, metrics, logs)
├── database/
│   ├── __init__.py
│   └── models.py           # SQLite manager with indexing & analytics tables
├── modules/
│   ├── __init__.py
│   ├── trend_hunter.py     # Global trend discovery & virality scoring
│   ├── downloader.py       # HD clean video downloader with yt-dlp fallback
│   ├── video_processor.py  # FFmpeg anti-duplicate & 9:16 vertical engine
│   ├── ai_captioner.py     # High-retention hooks & targeted hashtags
│   ├── instagram_poster.py # Direct session Reel publisher
│   ├── analytics_tracker.py# Track views, likes, and engagement
│   └── scheduler.py        # Background orchestrator & IST peak poster
├── static/
│   ├── css/dashboard.css   # Dark-mode glassmorphic styling
│   └── js/app.js           # Real-time Web dashboard logic
├── templates/
│   └── index.html          # Web Control Center
├── app.py                  # FastAPI server & REST API
├── run.py                  # Main launcher script
└── requirements.txt
```

---

## 🚀 How to Run

### 1. Launch the Server & Control Dashboard
In the terminal, run:
```powershell
.\.venv\Scripts\python.exe run.py
```
Open your browser and navigate to:
```
http://localhost:8000
```

### 2. Connect Your Instagram Account
- On the dashboard, click **"Connect Instagram"** in the top right.
- Enter your username & password (and 2FA code if enabled).
- Once logged in, your session is saved in `data/sessions/insta_session.json` and you will not be prompted again.

### 3. Choose Your Operational Mode
- **100% Autonomous Mode (Default)**: The bot continuously discovers trending videos, processes them, and publishes at peak IST hours without human intervention.
- **Manual Mode**: Turn off the switch to review discovered videos in the queue, watch the 9:16 preview, and approve with a single click.
