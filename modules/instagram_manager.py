import logging
import random
from typing import Dict, Any, List, Optional
from modules.instagram_poster import poster
from database import db

logger = logging.getLogger("InstagramManager")
logging.basicConfig(level=logging.INFO)

# Witty, viral, human-like replies for comment engagement
ENGAGING_REPLIES = [
    "Bro literally! 😭😂 Wait till you see tomorrow's drop!",
    "Nah for real though 😂💀",
    "Haha glad it made you laugh! Follow for more daily chaos ❤️",
    "Bro noticed the best detail 🤣💀",
    "I was not ready for that ending either 😭",
    "Tag your squad, they need to see this right now 😂👇",
    "Drop a ❤️ if we should make a part 2!",
    "Bro is speaking pure facts 💀",
    "Haha 100%! More viral clips coming your way 🚀",
    "I'm still wheezing over this 🤣💀"
]

class InstagramManager:
    def __init__(self):
        self.poster = poster
        self._cached_profile = None
        self._cached_time = 0

    def is_ready(self) -> bool:
        return self.poster.is_authenticated or self.poster.load_session()

    def get_profile_details(self, force: bool = False) -> Dict[str, Any]:
        """
        Fetches live profile metrics: followers, following, posts, bio, profile picture.
        Uses 5-minute cache to avoid Instagram rate limits.
        """
        import time
        now = time.time()
        if not force and self._cached_profile and (now - self._cached_time < 300):
            return self._cached_profile

        if not self.is_ready():
            return {
                "connected": False,
                "username": "Not Connected",
                "followers": 0,
                "following": 0,
                "media_count": 0,
                "biography": "Connect your Instagram account to enable AI profile management."
            }

        try:
            client = self.poster.client
            user_id = client.user_id
            user_info = client.user_info(user_id)

            data = {
                "connected": True,
                "username": user_info.username,
                "full_name": user_info.full_name or user_info.username,
                "followers": user_info.follower_count,
                "following": user_info.following_count,
                "media_count": user_info.media_count,
                "biography": user_info.biography,
                "profile_pic_url": str(user_info.profile_pic_url or ""),
                "is_verified": getattr(user_info, "is_verified", False)
            }
            self._cached_profile = data
            self._cached_time = now
            db.add_log("INFO", "InstagramManager", f"Synced profile for @{user_info.username}: {user_info.follower_count:,} followers")
            return data

        except Exception as e:
            if self._cached_profile:
                return self._cached_profile
            db.add_log("WARN", "InstagramManager", f"Failed fetching profile metrics: {e}")
            return {"connected": False, "error": str(e)}

    def update_profile_bio(self, new_bio: str) -> bool:
        """Directly updates the Instagram biography."""
        if not self.is_ready():
            return False
        try:
            client = self.poster.client
            success = client.account_set_biography(new_bio)
            if success:
                # Invalidate cache so UI refreshes immediately
                self._cached_profile = None
                db.add_log("SUCCESS", "InstagramManager", f"AI updated Instagram bio to: \"{new_bio.replace(chr(10), ' ')}\"")
                return True
        except Exception as e:
            db.add_log("ERROR", "InstagramManager", f"Failed to update bio: {e}")
        return False

    def autonomous_profile_optimization(self) -> Dict[str, Any]:
        """
        AI Agent checks if the bio needs improvement and updates it autonomously
        without waiting for user permission.
        """
        profile = self.get_profile_details()
        if not profile.get("connected"):
            return {"status": "unauthenticated"}

        current_bio = (profile.get("biography") or "").strip()

        # If bio is empty or too short, set a high-converting viral theme bio
        if len(current_bio) < 5:
            viral_bios = [
                "Daily dose of viral comedy 🌎🍿\nUnseen clips & unhinged memes 😂\nFollow for daily dopamine hits 🚀",
                "Curating the internet's most viral laughs 🍿\nTikTok's best clips unseen in India 🇮🇳✨\nNew drops daily at 12:30 & 9:00 PM 👇",
                "Laughing through the chaos 💀✨\n100% pure uncut global entertainment 😂\nHit Follow for your daily smile ❤️"
            ]
            chosen_bio = random.choice(viral_bios)
            updated = self.update_profile_bio(chosen_bio)
            if updated:
                db.add_agent_decision(
                    action_type="BIO_OPTIMIZED",
                    reasoning="Detected empty/unoptimized profile bio. Formulated a high-retention viral comedy bio to boost profile-visit to follow conversion rate.",
                    impact=f"Set bio: {chosen_bio.replace(chr(10), ' ')}"
                )
                return {"status": "bio_updated", "bio": chosen_bio}

        return {"status": "bio_optimal"}

    def engage_audience_and_reply_comments(self, max_reels: int = 5, max_replies_per_reel: int = 4) -> Dict[str, Any]:
        """
        Scans published Reels for fresh comments:
        1. Likes user comments (triggers notification, pulls viewer back to the reel).
        2. Crafts witty/engaging AI replies.
        3. Posts replies directly to build community and spike Instagram engagement algorithms.
        """
        if not self.is_ready():
            return {"status": "unauthenticated", "replies_count": 0}

        published = db.get_published_videos(limit=max_reels)
        if not published:
            return {"status": "no_reels", "replies_count": 0}

        client = self.poster.client
        replied_count = 0
        liked_count = 0

        for reel in published:
            media_id = reel.get("insta_media_id")
            if not media_id:
                continue

            try:
                # Fetch recent comments
                comments = client.media_comments(media_id)
                reel_replies = 0

                for comment in comments:
                    comment_id = str(comment.pk)
                    comment_text = comment.text
                    user_handle = comment.user.username

                    # Skip if our own comment or already replied
                    if user_handle == client.username or db.is_comment_replied(comment_id):
                        continue

                    # 1. Like the comment
                    try:
                        client.comment_like(comment_id)
                        liked_count += 1
                    except Exception:
                        pass

                    # 2. Pick a contextual, funny reply
                    reply_text = self._craft_comment_reply(comment_text)

                    # 3. Post reply
                    try:
                        client.comment_reply(comment_id, reply_text)
                        reel_replies += 1
                        replied_count += 1

                        db.record_comment_interaction(
                            comment_id=comment_id,
                            media_id=str(media_id),
                            user_handle=user_handle,
                            comment_text=comment_text,
                            reply_text=reply_text,
                            liked=1
                        )
                        db.add_log("SUCCESS", "CommentEngine", f"Replied to @{user_handle} on Reel {reel.get('insta_code')}: \"{reply_text}\"")

                        if reel_replies >= max_replies_per_reel:
                            break
                    except Exception as err:
                        db.add_log("WARN", "CommentEngine", f"Could not reply to comment {comment_id}: {err}")

            except Exception as e:
                db.add_log("WARN", "CommentEngine", f"Could not load comments for reel {media_id}: {e}")

        summary = f"Audience engagement cycle: {replied_count} replies posted, {liked_count} comments liked."
        db.add_log("INFO", "InstagramManager", summary)
        return {"status": "success", "replies_count": replied_count, "liked_count": liked_count}

    def _craft_comment_reply(self, comment_text: str) -> str:
        """Crafts a high-vibe response tailored to comment sentiment."""
        lower = comment_text.lower()
        if any(w in lower for w in ["ending", "end", "khatam", "aakhri"]):
            return "Bro the ending caught me completely off guard too 💀😂"
        if any(w in lower for w in ["part 2", "pt 2", "more", "next"]):
            return "Part 2 dropping soon! Drop a follow so you don't miss it 🔥"
        if any(w in lower for w in ["relatable", "me", "literally me", "same", "fr"]):
            return "We are all living the same life honestly 😭💀"
        if any(w in lower for w in ["song", "music", "audio"]):
            return "Such a banger audio haha! Save this reel so you don't lose it 🎶"
        
        return random.choice(ENGAGING_REPLIES)

insta_manager = InstagramManager()
