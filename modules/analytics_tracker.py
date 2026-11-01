import logging
from typing import Dict, Any, List
from modules.instagram_poster import poster
from database import db

logger = logging.getLogger("AnalyticsTracker")
logging.basicConfig(level=logging.INFO)

class AnalyticsTracker:
    def __init__(self):
        self.poster = poster

    def sync_post_analytics(self) -> Dict[str, Any]:
        """
        Polls Instagram for performance data (views, likes, comments)
        of all posted Reels and logs snapshots.
        """
        posted_videos = db.get_published_videos(limit=30)
        if not posted_videos:
            return {"status": "no_videos", "updated": 0}

        if not self.poster.is_authenticated and not self.poster.load_session():
            db.add_log("WARN", "Analytics", "Instagram session not active. Skipping analytics sync.")
            return {"status": "unauthenticated", "updated": 0}

        updated_count = 0
        for vid in posted_videos:
            media_id = vid.get("insta_media_id")
            insta_code = vid.get("insta_code")
            if not media_id:
                continue

            try:
                media_info = self.poster.client.media_info(media_id)
                views = getattr(media_info, "view_count", 0) or getattr(media_info, "play_count", 0) or 0
                likes = getattr(media_info, "like_count", 0) or 0
                comments = getattr(media_info, "comment_count", 0) or 0

                # Record snapshot in analytics_logs
                with db.get_connection() as conn:
                    conn.execute("""
                        INSERT INTO analytics_logs (video_id, insta_code, views, likes, comments)
                        VALUES (?, ?, ?, ?, ?)
                    """, (vid["id"], insta_code, views, likes, comments))
                    conn.commit()

                updated_count += 1
            except Exception as e:
                db.add_log("WARN", "Analytics", f"Could not fetch metrics for reel {insta_code}: {e}")

        db.add_log("INFO", "Analytics", f"Analytics sync completed. Updated {updated_count} reels.")
        return {"status": "success", "updated": updated_count}

    def get_summary_insights(self) -> Dict[str, Any]:
        """Calculates performance trends and best engagement metrics."""
        stats = db.get_dashboard_stats()
        return {
            "total_reels": stats.get("posted_count", 0),
            "total_views": stats.get("total_insta_views", 0),
            "total_likes": stats.get("total_insta_likes", 0),
            "total_comments": stats.get("total_insta_comments", 0),
        }

tracker = AnalyticsTracker()
