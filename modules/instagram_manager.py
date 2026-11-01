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

    def delete_recent_reels(self, count: int = 10) -> Dict[str, Any]:
        """
        Deletes the most recently uploaded Reels from Instagram
        and updates the database status to 'deleted'.
        """
        if not self.is_ready():
            return {"success": False, "count": 0, "message": "Instagram account not authenticated."}

        try:
            client = self.poster.client
            user_id = client.user_id
            medias = client.user_medias(user_id, amount=count)

            deleted_items = []
            for media in medias:
                pk = str(media.pk)
                code = getattr(media, "code", "")
                try:
                    success = client.media_delete(media.pk)
                    if success:
                        deleted_items.append({"pk": pk, "code": code})
                        # Update DB
                        with db.get_connection() as conn:
                            conn.execute("UPDATE videos SET status = 'deleted' WHERE insta_media_id = ?", (pk,))
                except Exception as del_err:
                    logger.warning(f"Failed deleting media {pk}: {del_err}")

            # Clear cached profile so dashboard updates immediately
            self._cached_profile = None

            db.add_agent_decision(
                action_type="USER_COMMAND_DELETE_REELS",
                reasoning=f"User instructed to delete uploaded Reels. Successfully removed {len(deleted_items)} medias from Instagram.",
                impact=f"Deleted {len(deleted_items)} Reels. Account media count updated."
            )
            db.add_log("SUCCESS", "InstagramManager", f"Deleted {len(deleted_items)} reels from Instagram account upon command.")

            return {
                "success": True,
                "count": len(deleted_items),
                "deleted": deleted_items,
                "message": f"Successfully deleted {len(deleted_items)} uploaded reel(s) from @{client.username}."
            }

        except Exception as e:
            db.add_log("ERROR", "InstagramManager", f"Delete reels failed: {e}")
            return {"success": False, "count": 0, "message": str(e)}

    def run_content_audit(self) -> Dict[str, Any]:
        """
        Comprehensive Content & Profile Audit for Instagram Growth:
        - Authority ratio (followers vs following)
        - Bio conversion effectiveness
        - Niche alignment & retention potential
        - Actionable 3-step growth blueprint
        """
        profile = self.get_profile_details(force=True)
        stats = db.get_dashboard_stats()

        followers = profile.get("followers", 0)
        following = profile.get("following", 0)
        media_count = profile.get("media_count", 0)
        bio = profile.get("biography", "")
        username = profile.get("username", "account")

        # 1. Authority Score
        ratio = round(followers / max(following, 1), 2)
        if ratio > 2.0:
            authority = "High Authority (Creator/Influencer ratio)"
        elif ratio >= 0.8:
            authority = "Balanced (Growing community)"
        else:
            authority = "Developing (Following exceeds followers; consider trimming non-active follows)"

        # 2. Bio Conversion Analysis
        bio_strengths = []
        bio_fixes = []
        if len(bio) < 15:
            bio_fixes.append("Bio is too sparse; lacks a clear niche proposition.")
        if not any(char in bio for char in ["👇", "⬇️", "link", "follow"]):
            bio_fixes.append("Missing a direct Call-To-Action (CTA) encouraging profile visitors to follow.")
        if any(emoji in bio for emoji in ["😂", "💀", "🍿", "🌎", "🔥", "✨"]):
            bio_strengths.append("Uses engaging emojis to set a high-energy comedy tone.")
        if "daily" in bio.lower() or "pm" in bio.lower():
            bio_strengths.append("Sets clear posting frequency expectations for followers.")

        # 3. Content Pipeline State
        ready_reels = stats.get("ready_count", 0)
        discovered = stats.get("total_discovered", 0)

        # 4. 12-Item Rubric Score (from instagram-agent-skill ig-profile)
        from modules.skills_bridge import skills_bridge
        rubric_audit = skills_bridge.audit_profile_against_rubric(profile)

        audit_report = {
            "username": username,
            "followers": followers,
            "following": following,
            "posts_count": media_count,
            "authority_ratio": ratio,
            "authority_verdict": authority,
            "rubric_score": rubric_audit.get("score", 0),
            "rubric_tier": rubric_audit.get("tier", "Needs Fixes"),
            "rubric_fixes": rubric_audit.get("fixes_in_priority_order", []),
            "bio_assessment": {
                "current_bio": bio,
                "strengths": bio_strengths or ["Active handle"],
                "actionable_fixes": bio_fixes or ["Bio has solid foundation"]
            },
            "content_pipeline": {
                "ready_in_queue": ready_reels,
                "total_scouted": discovered,
                "status": "Healthy" if ready_reels >= 3 else "Needs replenishment"
            },
            "recommendations": [
                "1. Focus 100% on 12-25 second Reels with an unexpected twist in the first 3 seconds.",
                "2. Schedule posts during peak Indian mobile engagement slots: 12:30 PM, 6:00 PM, and 9:00 PM IST.",
                "3. Use pinned comments with polarizing questions to trigger debate in comment section."
            ]
        }
        return audit_report

    def optimize_profile_full(self, apply: bool = False) -> Dict[str, Any]:
        """
        Generates complete profile makeover: SEO display name, 3 high-converting bios,
        and story highlight structures.
        """
        profile = self.get_profile_details()
        username = profile.get("username", "creator")

        seo_name = f"{profile.get('full_name') or username} | Viral Comedy & Memes 🍿"

        bio_concepts = [
            {
                "theme": "Curiosity & Arbitrage (Highest Follower Conversion)",
                "bio": "Global humor you haven't seen yet 🌎😂\nCurating the internet's most unhinged memes 🍿\nDaily drops at 12:30 & 9:00 PM IST 👇\nHit Follow for daily dopamine hits ❤️"
            },
            {
                "theme": "Pure Relatability & DM Shares",
                "bio": "Laughing through the chaos 💀✨\n100% pure uncut viral entertainment 🍿\nTag your squad in the comments ⬇️\nDaily laughs guaranteed 🚀"
            },
            {
                "theme": "Bold & Minimal",
                "bio": "The algorithm brought you here for a reason 😂\nTop 1% viral comedy clips worldwide 🌎\nNever a dull moment 👇\nJoin the chaos ❤️"
            }
        ]

        if apply and self.is_ready():
            best_bio = bio_concepts[0]["bio"]
            self.update_profile_bio(best_bio)
            return {
                "status": "applied",
                "seo_name": seo_name,
                "applied_bio": best_bio,
                "concepts": bio_concepts
            }

        return {
            "status": "ready",
            "seo_name": seo_name,
            "concepts": bio_concepts,
            "highlight_pillars": [
                "🔥 Top Viral (Best performing 1M+ Reels)",
                "😂 Fan Faves (Most commented clips)",
                "🍿 Daily Chaos (Behind the scenes / Stories)"
            ]
        }

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
            res = self.optimize_profile_full(apply=True)
            if res.get("status") == "applied":
                db.add_agent_decision(
                    action_type="BIO_OPTIMIZED",
                    reasoning="Detected empty/unoptimized profile bio. Applied a high-retention viral comedy bio to maximize profile-visit to follow conversion rate.",
                    impact=f"Set bio: {res.get('applied_bio', '').replace(chr(10), ' ')}"
                )
                return {"status": "bio_updated", "bio": res.get("applied_bio")}

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
