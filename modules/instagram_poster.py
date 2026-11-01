import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired, ChallengeRequired, TwoFactorRequired, BadPassword
)
from config import INSTA_USERNAME, INSTA_PASSWORD, INSTA_SESSION_FILE
from database import db

logger = logging.getLogger("InstagramPoster")
logging.basicConfig(level=logging.INFO)

class InstagramPoster:
    def __init__(self, session_file: Path = INSTA_SESSION_FILE):
        self.session_file = session_file
        self.client = Client()
        self.client.delay_range = [2, 5]  # Human-like delay between calls
        self.is_authenticated = False

    def load_session(self) -> bool:
        """Attempts to restore previous session from disk or environment variable."""
        if self.is_authenticated:
            return True

        # 1. Check if session is passed via environment variable (ideal for cloud containers)
        session_env = os.getenv("INSTA_SESSION_DATA")
        if session_env:
            try:
                settings_dict = json.loads(session_env)
                self.client.set_settings(settings_dict)
                self.is_authenticated = bool(self.client.user_id)
                if self.is_authenticated:
                    return True
            except Exception as e:
                db.add_log("WARN", "Instagram", f"Failed loading session from INSTA_SESSION_DATA: {e}")

        # 2. Check disk file
        if self.session_file.exists():
            try:
                self.client.load_settings(str(self.session_file))
                self.is_authenticated = bool(self.client.user_id)
                if self.is_authenticated:
                    return True
            except Exception as e:
                db.add_log("WARN", "Instagram", f"Session expired or invalid: {e}. Re-login needed.")
                self.is_authenticated = False
        return False

    def login(self, username: Optional[str] = None, password: Optional[str] = None, verification_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Authenticates with Instagram.
        Supports 2FA verification code if required.
        """
        user = username or os.getenv("INSTA_USERNAME") or INSTA_USERNAME
        pwd = password or os.getenv("INSTA_PASSWORD") or INSTA_PASSWORD

        if not user or not pwd:
            msg = "Instagram username or password not configured."
            db.add_log("ERROR", "Instagram", msg)
            return {"success": False, "status": "missing_credentials", "message": msg}

        # Try existing session first
        if not verification_code and self.load_session():
            return {"success": True, "status": "authenticated", "message": "Logged in via saved session"}

        try:
            db.add_log("INFO", "Instagram", f"Attempting login for user: {user}")
            if verification_code:
                # 2FA code passed
                self.client.login(user, pwd, verification_code=verification_code)
            else:
                self.client.login(user, pwd)

            # Save session for future hands-free usage
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            self.client.dump_settings(str(self.session_file))
            self.is_authenticated = True
            db.add_log("SUCCESS", "Instagram", f"Logged in successfully as {user}. Session saved.")
            return {"success": True, "status": "authenticated", "message": f"Logged in as {user}"}

        except TwoFactorRequired:
            db.add_log("WARN", "Instagram", "2-Factor Authentication required. Enter code in Dashboard.")
            return {"success": False, "status": "2fa_required", "message": "2FA code needed"}

        except ChallengeRequired:
            db.add_log("WARN", "Instagram", "Instagram challenge/checkpoint required. Please verify in app.")
            return {"success": False, "status": "challenge_required", "message": "Challenge required"}

        except BadPassword:
            db.add_log("ERROR", "Instagram", "Invalid password provided.")
            return {"success": False, "status": "bad_password", "message": "Invalid password"}

        except Exception as e:
            db.add_log("ERROR", "Instagram", f"Login failed: {e}")
            return {"success": False, "status": "error", "message": str(e)}

    def post_reel(self, video_id: int) -> Dict[str, Any]:
        """
        Uploads the processed video as an Instagram Reel.
        Updates video status in database upon completion.
        """
        video = db.get_video(video_id)
        if not video:
            return {"success": False, "message": f"Video {video_id} not found"}

        video_path = video.get("processed_video_path")
        if not video_path or not Path(video_path).exists():
            return {"success": False, "message": "Processed video file missing"}

        caption = video.get("ai_caption") or video.get("original_title") or "Viral Reel 😂 #reels"

        # Ensure logged in
        if not self.is_authenticated and not self.load_session():
            login_result = self.login()
            if not login_result.get("success"):
                return login_result

        try:
            db.add_log("INFO", "Instagram", f"Uploading Reel for video {video_id} ({Path(video_path).name})...")

            # Upload video as Instagram Reel (Clip)
            media = self.client.clip_upload(
                path=Path(video_path),
                caption=caption
            )

            media_id = str(media.pk)
            insta_code = str(media.code)

            db.update_video(
                video_id,
                status="posted",
                insta_media_id=media_id,
                insta_code=insta_code,
                posted_at=db.get_connection().execute("SELECT CURRENT_TIMESTAMP").fetchone()[0]
            )

            reel_url = f"https://www.instagram.com/reel/{insta_code}/"
            db.add_log("SUCCESS", "Instagram", f"Reel successfully published! URL: {reel_url}")

            return {
                "success": True,
                "media_id": media_id,
                "code": insta_code,
                "url": reel_url
            }

        except Exception as e:
            err_msg = str(e)
            db.add_log("ERROR", "Instagram", f"Reel upload failed for video {video_id}: {err_msg}")
            db.update_video(video_id, status="failed", error_message=err_msg)
            return {"success": False, "message": err_msg}

poster = InstagramPoster()
