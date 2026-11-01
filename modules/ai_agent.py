import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx

from database import db
from modules.trend_hunter import TrendHunter
from modules.downloader import downloader
from modules.video_processor import processor
from modules.ai_captioner import captioner
from modules.instagram_poster import poster
from modules.instagram_manager import insta_manager

logger = logging.getLogger("AIAgent")
logging.basicConfig(level=logging.INFO)

class ExecutiveAIAgent:
    """
    Autonomous Chief Content & Growth Officer:
    - Analyzes content trends & audience behavior.
    - Manages the Instagram handle (profile, comments, engagement).
    - Makes strategic autonomous decisions.
    - Interacts conversationally with the user.
    """

    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.trend_hunter = TrendHunter()

    def run_autonomous_cycle(self) -> Dict[str, Any]:
        """
        Complete 100% Sovereign AI Agent Thought & Action Cycle:
        1. Autonomously optimizes profile / bio if needed.
        2. Engages audience (auto-likes & auto-replies to comments).
        3. Replenishes content queue (hunting, downloading, FFmpeg 9:16 processing, AI hooks).
        4. Autonomously publishes the top ready Reel if posting slot is available.
        5. Logs full strategic reasoning into database.
        """
        db.add_log("INFO", "AIAgent", "🧠 Autonomous Agent Cycle: Executing zero-permission sovereign management...")

        actions_taken = []

        # 1. Autonomous Profile Management & Optimization
        if insta_manager.is_ready():
            bio_res = insta_manager.autonomous_profile_optimization()
            if bio_res.get("status") == "bio_updated":
                actions_taken.append("Optimized Instagram bio with high-converting viral comedy hook.")

            # 2. Audience Comment Auto-Engagement
            engagement_res = insta_manager.engage_audience_and_reply_comments(max_reels=5, max_replies_per_reel=4)
            if engagement_res.get("replies_count", 0) > 0:
                actions_taken.append(f"Auto-replied to {engagement_res['replies_count']} fan comments on recent Reels.")

        # 3. Content Queue Evaluation & Replenishment
        ready_videos = db.get_queue(status="ready", limit=10)

        if len(ready_videos) < 4:
            db.add_log("INFO", "AIAgent", f"Ready queue low ({len(ready_videos)} ready). Autonomous trend hunter dispatched...")
            new_discovered = self.trend_hunter.discover_viral_videos()

            # Autonomously process top candidates
            for candidate in new_discovered[:3]:
                vid_id = candidate.get("id")
                if vid_id:
                    downloader.download_clean_video(vid_id)
                    processor.process_for_reels(vid_id)
                    captioner.generate_caption(vid_id)
            if new_discovered:
                actions_taken.append(f"Discovered {len(new_discovered)} global viral clips and auto-processed top 3 candidates.")

        # 4. Autonomous Reel Publishing (Hands-free, Zero Permission)
        from modules.scheduler import pipeline
        if pipeline.is_autonomous_active():
            posts_today = pipeline.count_posts_today()
            max_daily = int(db.get_setting("max_daily_posts", 3))

            if posts_today < max_daily:
                next_vid = db.get_next_ready_video()
                if next_vid:
                    db.add_log("INFO", "AIAgent", f"Autonomous decision: Publishing Reel #{next_vid['id']} (Virality: {next_vid.get('virality_score')})...")
                    post_res = poster.post_reel(next_vid["id"])
                    if post_res.get("success"):
                        actions_taken.append(f"Published Reel https://www.instagram.com/reel/{post_res.get('code')}/")

        # 5. Formulate Strategic Decision Log
        reasoning = (
            f"Autonomous Sovereign Cycle executed. Profile managed, queue replenished ({len(ready_videos)} ready), "
            f"and audience engaged. Operating 100% hands-free with zero manual approval needed."
        )
        impact = f"Actions: {'; '.join(actions_taken) if actions_taken else 'Account active, audience monitored, and ready for next peak slot.'}"

        db.add_agent_decision(
            action_type="SOVEREIGN_AI_CYCLE",
            reasoning=reasoning,
            impact=impact
        )
        db.add_log("SUCCESS", "AIAgent", f"🧠 Sovereign cycle complete: {impact}")

        return {
            "status": "success",
            "actions": actions_taken,
            "reasoning": reasoning
        }

    def process_chat(self, user_message: str) -> str:
        """
        Handles natural language interaction with the user from the Web Dashboard.
        Capable of executing actions (triggering post, syncing comments, changing strategy)
        or providing briefings.
        """
        # Save user message to chat history
        db.add_chat_message("user", user_message)
        clean_msg = user_message.lower().strip()

        response = ""

        # Command Dispatcher
        if any(w in clean_msg for w in ["post", "publish", "upload"]) and any(w in clean_msg for w in ["now", "immediate", "next"]):
            # Trigger immediate post
            from modules.scheduler import pipeline
            res = pipeline.post_next_ready_video()
            if res.get("success"):
                response = f"🚀 Executed! I have successfully published the highest-ranking Reel to your Instagram: [View Reel](https://www.instagram.com/reel/{res.get('code')}/)"
            else:
                response = f"⚠️ Post attempt status: {res.get('message') or res.get('status')}. Check the dashboard logs for details."

        elif any(w in clean_msg for w in ["comment", "reply", "audience", "engage"]):
            # Trigger comment engagement
            res = insta_manager.engage_audience_and_reply_comments(max_reels=5, max_replies_per_reel=4)
            response = f"💬 Engagement cycle executed! I inspected your recent Reels and posted {res.get('replies_count', 0)} witty replies and liked {res.get('liked_count', 0)} comments to boost your algorithm reach."

        elif any(w in clean_msg for w in ["trend", "discover", "hunt", "find", "search"]):
            # Trigger trend hunting
            new_vids = self.trend_hunter.discover_viral_videos()
            response = f"⚡ Global trend hunter dispatched! I analyzed feeds from US, UK, and Australia and discovered {len(new_vids)} fresh viral videos that Indian audiences haven't seen. They are now in your processing queue."

        elif any(w in clean_msg for w in ["growth", "stat", "performance", "metric", "report", "briefing"]):
            # Generate executive growth briefing
            stats = db.get_dashboard_stats()
            profile = insta_manager.get_profile_details()
            username = profile.get("username", "Not connected")
            followers = profile.get("followers", 0)

            response = (
                f"📊 **Executive Growth Briefing**\n\n"
                f"• **Instagram Account:** @{username} ({followers:,} followers)\n"
                f"• **Total Viral Videos Discovered:** {stats.get('total_discovered', 0)}\n"
                f"• **Reels Ready to Post:** {stats.get('ready_count', 0)}\n"
                f"• **Reels Published:** {stats.get('posted_count', 0)}\n"
                f"• **Tracked Engagement:** {stats.get('total_insta_views', 0):,} views | {stats.get('total_insta_likes', 0):,} likes\n\n"
                f"💡 **Recommendation:** Peak engagement windows in India are 12:30 PM, 6:00 PM, and 9:00 PM IST. "
                f"Keep autonomous mode active for hands-free pacing."
            )

        elif any(w in clean_msg for w in ["bio", "profile", "caption"]):
            # Suggest high-converting bios
            response = (
                "✨ Here are 3 high-converting viral bio concepts tailored for your page:\n\n"
                "**Option 1 (Curiosity/Arbitrage):**\n"
                "Global humor you haven't seen yet 🌎😂\n"
                "Curating the internet's most unhinged memes 🍿\n"
                "Daily laughs at 12:30 & 9:00 PM IST 👇\n\n"
                "**Option 2 (Relatable Comedy):**\n"
                "Laughing through the chaos 💀✨\n"
                "Tag your squad in the comments ⬇️\n"
                "New viral reels every single day 🚀\n\n"
                "**Option 3 (Minimal & Punchy):**\n"
                "The algorithm brought you here for a reason 😂\n"
                "100% uncut global entertainment 🍿\n"
                "Hit Follow for daily dopamine hits ❤️"
            )

        else:
            # Smart conversational assistance
            stats = db.get_dashboard_stats()
            profile = insta_manager.get_profile_details()
            username = profile.get("username", "connected account")

            response = (
                f"👋 I'm your **AI Instagram Director** managing @{username}.\n\n"
                f"Right now I am monitoring your content pipeline ({stats.get('ready_count', 0)} reels ready, {stats.get('posted_count', 0)} published). "
                f"Here are a few commands you can tell me:\n"
                f"• *'Post next reel now'* — Instantly uploads our top video\n"
                f"• *'Reply to comments'* — Auto-replies with witty humor to your recent Reels\n"
                f"• *'Discover trending memes'* — Hunts fresh US/UK comedy\n"
                f"• *'Give me a growth briefing'* — Summarizes performance metrics and strategy\n"
                f"• *'Suggest a viral bio'* — Generates high-converting bio hooks"
            )

        # Save agent response to chat history
        db.add_chat_message("agent", response)
        return response

ai_agent = ExecutiveAIAgent()
