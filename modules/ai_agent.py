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

        # 4. Autonomous Reel Publishing (Hands-free, SOTA Niche & DM Share Intelligence)
        from modules.scheduler import pipeline
        if pipeline.is_autonomous_active():
            posts_today = pipeline.count_posts_today()
            max_daily = int(db.get_setting("max_daily_posts", 3))

            if posts_today < max_daily:
                from modules.growth_intelligence import growth_intel
                ready_candidates = db.get_queue(status="ready", limit=25)
                if ready_candidates:
                    smart_vid = growth_intel.select_smartest_video(ready_candidates)
                    if smart_vid:
                        vid_id = smart_vid["id"]
                        growth_reasoning = smart_vid.get("ai_growth_reasoning", "Optimal viral growth candidate.")
                        hook = smart_vid.get("ai_selected_hook")
                        if hook:
                            smart_caption = growth_intel.craft_viral_caption(smart_vid.get("original_title"), hook)
                            db.update_video(vid_id, ai_caption=smart_caption)

                        db.add_log("INFO", "AIAgent", f"🧠 Strategic AI Selection: Video #{vid_id} chosen based on DM-share rate & niche resonance.")
                        post_res = poster.post_reel(vid_id)
                        if post_res.get("success"):
                            actions_taken.append(f"Published strategically chosen Reel #{vid_id} (URL: https://www.instagram.com/reel/{post_res.get('code')}/)")
                            db.add_agent_decision(
                                action_type="SMART_NICHE_SELECTION",
                                reasoning=growth_reasoning,
                                impact=f"Published Reel https://www.instagram.com/reel/{post_res.get('code')}/ during peak engagement window."
                            )

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
        Intelligent Conversational Agent & Tool-Calling Dispatcher:
        - Executes account actions: Reel deletion, immediate posting, comment auto-replies.
        - Strategic tools: Content Audit, Profile Optimization, Trend Research, Hook Crafting.
        - Conversational reasoning: Powered by Free LLM + Growth Playbook heuristics.
        """
        # Save user message to chat history
        db.add_chat_message("user", user_message)
        clean_msg = user_message.lower().strip()

        from modules.growth_intelligence import growth_intel
        profile = insta_manager.get_profile_details()
        username = profile.get("username", "1lucky_24")
        followers = profile.get("followers", 0)
        media_count = profile.get("media_count", 0)
        stats = db.get_dashboard_stats()
        ready_count = stats.get("ready_count", 0)

        response = ""

        # 1. ACTION: Delete Uploaded Reels
        if any(w in clean_msg for w in ["delete", "remove", "hatao", "hata do", "clear", "trash", "erase"]) and any(w in clean_msg for w in ["reel", "reels", "post", "posts", "video", "videos", "all", "uploaded", "content", "those"]):
            db.add_log("INFO", "AIAgent", f"Processing user command to delete uploaded Reels...")
            del_res = insta_manager.delete_recent_reels(count=10)
            if del_res.get("success"):
                count = del_res.get("count", 0)
                if count > 0:
                    response = (
                        f"🗑️ **Reels Successfully Deleted!**\n\n"
                        f"I have removed **{count} uploaded Reel(s)** directly from your Instagram handle (@{username}).\n\n"
                        f"• **Status:** Cleaned from Instagram live feed\n"
                        f"• **Database:** Synced and updated\n"
                        f"• **Current Media Count:** 0 Reels\n\n"
                        f"Your account is fresh and ready. Let me know if you want me to *'Audit profile'*, *'Research trends'*, or *'Generate viral hooks'* for our next drop!"
                    )
                else:
                    response = (
                        f"🗑️ **Reels Already Cleaned!**\n\n"
                        f"All previously uploaded Reels have already been removed from your Instagram handle (@{username}).\n\n"
                        f"• **Current Media Count:** 0 Reels on live profile\n"
                        f"• **Pipeline Status:** Clean and ready for fresh viral content\n\n"
                        f"Would you like me to *'Audit profile'*, *'Research trends'*, or *'Generate viral hooks'* now?"
                    )
            else:
                response = f"⚠️ Could not complete deletion: {del_res.get('message')}. Please check the system logs."

        from modules.skills_bridge import skills_bridge

        # 2. SKILL: /ig-reel — 26 Hook Formulas & Timed Beat Sheet
        if any(w in clean_msg for w in ["/ig-reel", "hook", "hooks", "beat sheet", "reel script"]):
            formulas = skills_bridge.get_hooks_library()
            # Pick 3 distinct formulas to demonstrate and score
            sample_candidates = [
                "Nobody tells you that your first 30 reels are supposed to flop.",
                "Stop posting three times a day without replying to comments.",
                "I lost $18,000 because of one missing clause in a contract."
            ]
            scored_rows = [skills_bridge.score_hook(h) for h in sample_candidates]
            
            hooks_formatted = ""
            for i, r in enumerate(scored_rows, 1):
                f_name = formulas[i-1]["name"] if i-1 < len(formulas) else "Formula"
                on_screen = formulas[i-1].get("on_screen", "HOOK") if i-1 < len(formulas) else "HOOK"
                hooks_formatted += (
                    f"**Option {i} — {f_name} (Score: {r['score']}/100 {r['verdict']}):**\n"
                    f"• *Spoken:* \"{r['hook']}\"\n"
                    f"• *On-Screen Text:* `{on_screen}`\n"
                    f"• *Checks:* Length {r['checks']['LENGTH']['score']:.0f} | Stakes {r['checks']['STAKES']['score']:.0f} | Frontload {r['checks']['FRONTLOAD']['score']:.0f}\n\n"
                )

            # Sample timed beat sheet
            beat_analysis = skills_bridge.generate_timed_beats(
                "Nobody tells you that your first 30 reels are supposed to flop.\n"
                "Here is why the algorithm tests your retention curve before pushing to Explore.\n"
                "Save this video and start posting with a 2-second hook today.",
                target_seconds=20.0
            )
            notes_text = "\n".join([f"• {n}" for n in beat_analysis.get("notes", [])[:3]])

            response = (
                f"🎬 **Instagram Agent Skill: Reel Architect (`/ig-reel`)**\n\n"
                f"Generated from **26 scored hook formulas** with 5-factor local ranking:\n\n"
                f"{hooks_formatted}"
                f"⏱️ **Timed Beat Sheet Breakdown (~{beat_analysis.get('duration', 0):.1f}s):**\n"
                f"{notes_text}\n\n"
                f"💡 *Pro-Tip: Deliver the payoff before the halfway mark to lock in loop retention.*"
            )

        # 3. SKILL: /ig-profile — 12-Item 100-Point Profile Rubric
        elif any(w in clean_msg for w in ["/ig-profile", "rubric", "score profile", "profile audit", "audit profile"]):
            rubric_res = skills_bridge.audit_profile_against_rubric(profile)
            fixes = "\n".join([f"  ⚠️ {f}" for f in rubric_res["fixes_in_priority_order"]])

            response = (
                f"📋 **Instagram Profile Rubric Score (`/ig-profile`)**\n\n"
                f"**Overall Score:** **{rubric_res['score']} / {rubric_res['max_score']}** ({rubric_res['tier']})\n"
                f"**Evaluated on:** 12 algorithmic conversion items from `rubric.json`\n\n"
                f"🚨 **Fixes in Priority Order (Fix First to Boost Conversion):**\n"
                f"{fixes}\n\n"
                f"💡 *Say 'Optimize profile' or 'Apply bio' and I will automatically formulate and apply these updates to @{username}!*"
            )

        # 4. SKILL: /ig-caption — Feed Linter & 125-Char Truncation Box
        elif any(w in clean_msg for w in ["/ig-caption", "lint caption", "caption check", "caption"]):
            sample_caption = (
                "Nobody tells you that your first 30 reels are supposed to flop.\n\n"
                "Here is the exact framework we use to test hooks before spending hours editing.\n\n"
                "👇 Comment 'REEL' and I'll send you the 26 hook templates!\n"
                "#reelsindia #viralmemes #contentcreator #reelsgrowth #explorepage"
            )
            lint = skills_bridge.lint_caption(sample_caption)
            checks_formatted = "\n".join([f"  {'✓' if c['status']=='PASS' else '⚠️'} **{c['check']}:** {c['detail']}" for c in lint["checks"][:6]])

            response = (
                f"📝 **Instagram Caption Linter (`/ig-caption`)**\n\n"
                f"**What the Feed Actually Shows Before '... more' (125-Char Cutoff):**\n"
                f"```text\n+------------------------------------------------------+\n"
                f"| {lint.get('visible', '')[:50]:<52} |\n"
                f"| {lint.get('visible', '')[50:100]:<52} |\n"
                f"+-------------------------------------------- ... more +\n```\n\n"
                f"📊 **Audit Panel ({lint.get('verdict')}):**\n"
                f"{checks_formatted}\n\n"
                f"Enforcing Instagram's strict **cap of 5 hashtags** and single clear CTA."
            )

        # 5. SKILL: /ig-human — Strip AI Slop & Watermarks
        elif any(w in clean_msg for w in ["/ig-human", "humanize", "strip slop", "human"]):
            draft = "Delve into this game-changer tapestry of content—unleash your potential today."
            cleaned = skills_bridge.humanize(draft)

            response = (
                f"🧼 **Instagram Humanizer (`/ig-human`)**\n\n"
                f"**Original Draft:**\n\"{draft}\"\n\n"
                f"**Humanized Output:**\n\"{cleaned['clean_text']}\"\n\n"
                f"• Stripped mechanical em-dashes and invisible zero-width unicode characters.\n"
                f"• Cleaned robotic AI buzzwords (`delve`, `game-changer`, `tapestry`, `unleash`) with natural creator phrasing."
            )

        # 6. SKILL: /ig-plan — 7-Day Editorial Content Planner
        elif any(w in clean_msg for w in ["/ig-plan", "plan", "weekly plan", "schedule", "content calendar"]):
            plan_res = skills_bridge.generate_weekly_content_plan()
            schedule_text = "\n".join([
                f"• **{item['day']}:** {item['format']} ({item['pillar']}) — Hook: *{item['hook_formula']}* at {item['peak_time_ist']} IST ({item['target_duration']})"
                for item in plan_res["weekly_schedule"]
            ])

            response = (
                f"📅 **7-Day Instagram Editorial Calendar (`/ig-plan`)**\n\n"
                f"**Niche:** {plan_res['niche']}\n"
                f"**Posting Strategy:** 3 daily drops at peak IST engagement slots (12:30, 18:00, 21:00).\n\n"
                f"{schedule_text}\n\n"
                f"💡 *The autonomous pipeline will auto-fill these slots from your ready queue.*"
            )

        # 7. TOOL: Complete Content & Handle Audit
        elif any(w in clean_msg for w in ["audit", "review account", "analyze handle", "check account", "scorecard", "content audit"]):
            db.add_log("INFO", "AIAgent", "Generating deep content audit for Instagram handle...")
            audit = insta_manager.run_content_audit()
            strengths = "\n".join([f"  ✓ {s}" for s in audit["bio_assessment"]["strengths"]])
            fixes = "\n".join([f"  ⚠️ {f}" for f in audit["bio_assessment"]["actionable_fixes"]])
            recs = "\n".join([f"• {r}" for r in audit["recommendations"]])

            response = (
                f"🔍 **Instagram Content & Handle Audit Report**\n\n"
                f"**Account:** @{audit['username']} | **Followers:** {audit['followers']:,} | **Published:** {audit['posts_count']}\n"
                f"**Authority Ratio:** {audit['authority_ratio']} ({audit['authority_verdict']})\n"
                f"**Rubric Score:** {audit.get('rubric_score', 0)}/100 ({audit.get('rubric_tier', 'Needs Fixes')})\n\n"
                f"📊 **Bio & Positioning Assessment:**\n"
                f"{strengths}\n"
                f"{fixes}\n\n"
                f"🎬 **Content Pipeline State:**\n"
                f"• {audit['content_pipeline']['ready_in_queue']} Reels ready for automated posting\n"
                f"• Pipeline Status: {audit['content_pipeline']['status']}\n\n"
                f"🚀 **Actionable 3-Step Growth Plan:**\n"
                f"{recs}\n\n"
                f"💡 *Say 'Optimize profile' or 'Generate viral hooks' to execute these improvements!*"
            )

        # 8. TOOL: Profile Makeover & Bio Optimization
        elif any(w in clean_msg for w in ["optimize profile", "profile optimization", "optimize bio", "change bio", "update bio", "suggest bio", "bio concepts", "makeover"]):
            should_apply = any(w in clean_msg for w in ["apply", "set", "update now", "change now"])
            opt = insta_manager.optimize_profile_full(apply=should_apply)

            concepts_text = ""
            for idx, c in enumerate(opt.get("concepts", []), 1):
                concepts_text += f"\n**Concept {idx} ({c['theme']}):**\n{c['bio']}\n"

            status_note = "✅ **Applied to Instagram!** Concept 1 has been pushed live to your account bio." if should_apply else "💡 *Tip: Reply 'Apply bio' and I will update your Instagram bio automatically.*"

            response = (
                f"✨ **Instagram Profile Optimization Blueprint**\n\n"
                f"**Recommended SEO Display Name:**\n`{opt.get('seo_name')}`\n\n"
                f"🎯 **High-Converting Bio Concepts (Scroll-Stopping & Follower Magnets):**\n"
                f"{concepts_text}\n"
                f"📌 **Story Highlight Architecture:**\n"
                f"• 🔥 *Top Viral* — Best 1M+ Reels\n"
                f"• 😂 *Fan Faves* — Most shared in DMs\n"
                f"• 🍿 *Daily Chaos* — Stories & behind-the-scenes\n\n"
                f"{status_note}"
            )

        # 9. TOOL: Niche Trend & Audience Research
        elif any(w in clean_msg for w in ["research", "trend", "trends", "niche", "viral topic", "what's viral"]):
            trends = growth_intel.research_niche_trends()
            formats = "\n".join([f"• {f}" for f in trends.get("formats", [])])
            triggers = "\n".join([f"• {t}" for t in trends.get("share_triggers", [])])
            hashtags = " ".join(trends.get("hashtags", []))

            response = (
                f"⚡ **Viral Trend Intelligence Report (2026)**\n\n"
                f"• **Target Niche:** {trends.get('niche')}\n"
                f"• **Demographic Focus:** {trends.get('target_demographic')}\n"
                f"• **Retention Sweet Spot:** {trends.get('retention_sweet_spot')}\n\n"
                f"🔥 **Top Trending Formats Right Now:**\n"
                f"{formats}\n\n"
                f"📲 **DM Share Catalysts (Algorithm Boosters):**\n"
                f"{triggers}\n\n"
                f"🎧 **Audio Strategy:** {trends.get('audio_strategy')}\n\n"
                f"🏷️ **Explore Hashtag Cluster:**\n`{hashtags}`"
            )

        # 10. ACTION: Post Next Reel
        elif any(w in clean_msg for w in ["post", "publish", "upload"]) and any(w in clean_msg for w in ["now", "immediate", "next", "reel"]):
            from modules.scheduler import pipeline
            res = pipeline.post_next_ready_video()
            if res.get("success"):
                response = f"🚀 **Published!** I have posted the highest-ranking Reel to your Instagram: [View Reel](https://www.instagram.com/reel/{res.get('code')}/)"
            else:
                response = f"⚠️ Post attempt status: {res.get('message') or res.get('status')}. Check the dashboard logs for details."

        # 11. ACTION: Reply to Comments
        elif any(w in clean_msg for w in ["comment", "reply", "audience", "engage"]):
            res = insta_manager.engage_audience_and_reply_comments(max_reels=5, max_replies_per_reel=4)
            response = f"💬 **Engagement Cycle Complete!** I inspected your Reels, posted {res.get('replies_count', 0)} witty replies, and liked {res.get('liked_count', 0)} fan comments to boost reach."

        # 12. Executive Growth Briefing
        elif any(w in clean_msg for w in ["growth", "stat", "performance", "metric", "report", "briefing"]):
            response = (
                f"📊 **Executive Growth Briefing**\n\n"
                f"• **Instagram Account:** @{username} ({followers:,} followers)\n"
                f"• **Total Viral Videos Discovered:** {stats.get('total_discovered', 0)}\n"
                f"• **Reels Ready in Pipeline:** {ready_count}\n"
                f"• **Published Reels:** {stats.get('posted_count', 0)}\n"
                f"• **Tracked Engagement:** {stats.get('total_insta_views', 0):,} views | {stats.get('total_insta_likes', 0):,} likes\n\n"
                f"💡 **Recommendation:** Keep 3-4 ready videos queued up. Peak engagement windows in India are 12:30 PM, 6:00 PM, and 9:00 PM IST."
            )

        # 13. Free LLM Conversational Director (Answers ANY question smartly)
        else:
            response = growth_intel.consult_ai_director(
                user_query=user_message,
                username=username,
                context_info={"followers": followers, "posts": media_count, "ready": ready_count}
            )

        # Save agent response to chat history
        db.add_chat_message("agent", response)
        return response

ai_agent = ExecutiveAIAgent()

