import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import httpx
from config import DOWNLOADS_DIR
from database import db

logger = logging.getLogger("Downloader")
logging.basicConfig(level=logging.INFO)

try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.tikwm.com/"
}

class VideoDownloader:
    def __init__(self, output_dir: Path = DOWNLOADS_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fetch_video_info(self, tiktok_url: str) -> Optional[Dict[str, Any]]:
        """Query TikWM API to get clean HD no-watermark video stream URL."""
        api_url = f"https://www.tikwm.com/api/?url={tiktok_url}"
        if HAS_CURL_CFFI:
            try:
                res = cffi_requests.get(api_url, impersonate="chrome120", timeout=20, headers=HEADERS)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("code") == 0 and "data" in data:
                        return data["data"]
            except Exception as e:
                db.add_log("WARN", "Downloader", f"curl_cffi fetch notice for {tiktok_url}: {e}")

        try:
            with httpx.Client(timeout=20, headers=HEADERS) as client:
                res = client.get(api_url)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("code") == 0 and "data" in data:
                        return data["data"]
        except Exception as e:
            db.add_log("ERROR", "Downloader", f"Failed fetching info for {tiktok_url}: {e}")
        return None

    def download_clean_video(self, video_id: int) -> Optional[str]:
        """
        Downloads the video without watermark to local disk.
        Updates DB with raw_video_path and status='downloaded'.
        """
        video = db.get_video(video_id)
        if not video:
            db.add_log("ERROR", "Downloader", f"Video ID {video_id} not found in database.")
            return None

        tiktok_id = video["tiktok_id"]
        tiktok_url = video["tiktok_url"]
        target_path = self.output_dir / f"{tiktok_id}.mp4"

        # Check if already downloaded
        if target_path.exists() and target_path.stat().st_size > 100_000:
            db.update_video(video_id, raw_video_path=str(target_path), status="downloaded")
            return str(target_path)

        db.add_log("INFO", "Downloader", f"Starting clean download for video: {tiktok_id}")

        # 1. Fetch clean play URL
        info = self.fetch_video_info(tiktok_url)
        play_url = None
        if info:
            play_url = info.get("hdplay") or info.get("play")

        if not play_url:
            db.add_log("WARN", "Downloader", f"No direct play URL found for {tiktok_id}. Attempting yt-dlp fallback...")
            return self._download_with_ytdlp(video_id, tiktok_url, target_path)

        # 2. Stream download video chunks
        try:
            with httpx.Client(timeout=40, headers=HEADERS, follow_redirects=True) as client:
                with client.stream("GET", play_url) as response:
                    if response.status_code != 200:
                        db.add_log("ERROR", "Downloader", f"Stream returned HTTP {response.status_code}")
                        return self._download_with_ytdlp(video_id, tiktok_url, target_path)

                    with open(target_path, "wb") as f:
                        for chunk in response.iter_bytes(chunk_size=65536):
                            if chunk:
                                f.write(chunk)

            if target_path.exists() and target_path.stat().st_size > 50_000:
                db.update_video(video_id, raw_video_path=str(target_path), status="downloaded")
                db.add_log("SUCCESS", "Downloader", f"Downloaded clean video: {tiktok_id} ({round(target_path.stat().st_size / (1024*1024), 2)} MB)")
                return str(target_path)
            else:
                db.add_log("WARN", "Downloader", f"File size too small for {tiktok_id}. Trying yt-dlp fallback...")
                return self._download_with_ytdlp(video_id, tiktok_url, target_path)

        except Exception as e:
            db.add_log("ERROR", "Downloader", f"Download exception for {tiktok_id}: {e}")
            return self._download_with_ytdlp(video_id, tiktok_url, target_path)

    def _download_with_ytdlp(self, video_id: int, tiktok_url: str, target_path: Path) -> Optional[str]:
        """Fallback downloader using yt-dlp."""
        try:
            import yt_dlp
            ydl_opts = {
                'outtmpl': str(target_path),
                'format': 'bestvideo+bestaudio/best',
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([tiktok_url])

            if target_path.exists() and target_path.stat().st_size > 50_000:
                db.update_video(video_id, raw_video_path=str(target_path), status="downloaded")
                db.add_log("SUCCESS", "Downloader", f"yt-dlp successfully downloaded: {target_path.name}")
                return str(target_path)
        except Exception as e:
            db.add_log("ERROR", "Downloader", f"yt-dlp download failed: {e}")
            db.update_video(video_id, status="failed", error_message=str(e))
        return None

downloader = VideoDownloader()
