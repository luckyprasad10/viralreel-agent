import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from config import AUTONOMOUS_MODE, MAX_DAILY_POSTS, PEAK_POSTING_HOURS_IST
from database import db
from modules.trend_hunter import TrendHunter
from modules.downloader import downloader
from modules.video_processor import processor
from modules.ai_captioner import captioner
from modules.instagram_poster import poster
from modules.analytics_tracker import tracker

logger = logging.getLogger("Scheduler")
logging.basicConfig(level=logging.INFO)

class AutomationPipeline:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.trend_hunter = TrendHunter()
        self.is_running = False

    def is_autonomous_active(self) -> bool:
        """Check if autonomous mode is enabled in DB settings or config."""
        setting = db.get_setting("autonomous_mode", None)
        if setting is not None:
            return bool(setting)
        return AUTONOMOUS_MODE

    def count_posts_today(self) -> int:
        """Count number of Reels posted today."""
        today_str = date.today().isoformat()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM videos WHERE status = 'posted' AND date(posted_at) = ?",
                (today_str,)
            )
            res = cursor.fetchone()
            return res[0] if res else 0

    def prepare_video_pipeline(self, video_id: int) -> bool:
        """
        Executes download, video re-encoding, and AI captioning for a single video.
        """
        try:
            # 1. Download
            raw_path = downloader.download_clean_video(video_id)
            if not raw_path:
                return False

            # 2. FFmpeg processing
            proc_path = processor.process_for_reels(video_id)
            if not proc_path:
                return False

            # 3. AI Caption generation
            captioner.generate_caption(video_id)

            db.add_log("SUCCESS", "Pipeline", f"Video {video_id} successfully prepared and ready to post.")
            return True
        except Exception as e:
            db.add_log("ERROR", "Pipeline", f"Pipeline failed on video {video_id}: {e}")
            return False

    def run_discovery_and_preparation(self) -> int:
        """
        Finds trending TikToks and automatically prepares them.
        """
        db.add_log("INFO", "Pipeline", "Starting autonomous trend hunting cycle...")
        discovered = self.trend_hunter.discover_viral_videos()

        prepared_count = 0
        # Automatically download and process top candidates
        for vid in discovered[:5]:  # Process up to 5 top fresh candidates
            vid_id = vid.get("id")
            if vid_id and self.prepare_video_pipeline(vid_id):
                prepared_count += 1

        db.add_log("INFO", "Pipeline", f"Cycle completed. Discovered {len(discovered)}, prepared {prepared_count} new ready Reels.")
        return prepared_count

    def post_next_ready_video(self) -> Dict[str, Any]:
        """
        Picks the highest scoring ready video and publishes it to Instagram.
        """
        posts_today = self.count_posts_today()
        max_posts = int(db.get_setting("max_daily_posts", MAX_DAILY_POSTS))

        if posts_today >= max_posts:
            msg = f"Daily posting limit reached ({posts_today}/{max_posts}). Skipping."
            db.add_log("INFO", "Publisher", msg)
            return {"status": "limit_reached", "message": msg}

        next_video = db.get_next_ready_video()
        if not next_video:
            msg = "No ready video available in queue to post."
            db.add_log("INFO", "Publisher", msg)
            return {"status": "queue_empty", "message": msg}

        video_id = next_video["id"]
        db.add_log("INFO", "Publisher", f"Publishing next viral reel (ID: {video_id}, Virality: {next_video.get('virality_score')})...")
        result = poster.post_reel(video_id)
        return result

    def autonomous_tick(self):
        """
        Scheduled heartbeat:
        1. Checks if it's peak time or if queue is low.
        2. Discovers & processes content if needed.
        3. If autonomous mode is ON, posts the next ready video.
        """
        try:
            # Check how many ready videos we have
            ready_queue = db.get_queue(status="ready", limit=5)
            if len(ready_queue) < 3:
                db.add_log("INFO", "Heartbeat", "Ready queue low. Triggering discovery...")
                self.run_discovery_and_preparation()

            # If autonomous posting is enabled
            if self.is_autonomous_active():
                self.post_next_ready_video()

        except Exception as e:
            db.add_log("ERROR", "Heartbeat", f"Error during autonomous tick: {e}")

    def start(self):
        """Starts the background APScheduler."""
        if self.is_running:
            return

        # 1. Autonomous tick every 2 hours
        self.scheduler.add_job(
            self.autonomous_tick,
            "interval",
            hours=2,
            id="autonomous_tick",
            replace_existing=True
        )

        # 2. AI Executive Agent Cycle (every 45 minutes)
        from modules.ai_agent import ai_agent
        self.scheduler.add_job(
            ai_agent.run_autonomous_cycle,
            "interval",
            minutes=45,
            id="ai_agent_cycle",
            replace_existing=True
        )

        # 3. Daily peak hour posts (IST slots: 12:30, 18:00, 21:00)
        # 12:30 IST is 07:00 UTC
        self.scheduler.add_job(
            self.post_next_ready_video,
            "cron",
            hour=7,
            minute=0,
            id="peak_slot_noon",
            replace_existing=True
        )
        # 18:00 IST is 12:30 UTC
        self.scheduler.add_job(
            self.post_next_ready_video,
            "cron",
            hour=12,
            minute=30,
            id="peak_slot_evening",
            replace_existing=True
        )
        # 21:00 IST is 15:30 UTC
        self.scheduler.add_job(
            self.post_next_ready_video,
            "cron",
            hour=15,
            minute=30,
            id="peak_slot_night",
            replace_existing=True
        )

        # 3. Analytics sync every 4 hours
        self.scheduler.add_job(
            tracker.sync_post_analytics,
            "interval",
            hours=4,
            id="analytics_sync",
            replace_existing=True
        )

        self.scheduler.start()
        self.is_running = True
        db.add_log("SUCCESS", "Scheduler", "Background autonomous scheduler started successfully.")

    def stop(self):
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            db.add_log("INFO", "Scheduler", "Scheduler stopped.")

pipeline = AutomationPipeline()
