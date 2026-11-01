import re
import json
import logging
import httpx
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("GrowthIntelligence")
logging.basicConfig(level=logging.INFO)

# ========================================================
# 🎯 Niche Persona Configuration: Relatable Comedy & Twists
# ========================================================
TARGET_NICHE = {
    "name": "Relatable Global Comedy & Unexpected Twists",
    "target_audience": "Indian Gen-Z & Millennials (18-34)",
    "content_pillars": [
        "relatable_life",      # Relatable work, college, family & social situations
        "unexpected_twists",   # Subverted expectations within first 5 seconds
        "savage_humor",        # Witty comebacks, intrusive thoughts winning
        "universal_fails"      # Physical comedy, zero-language barrier moments
    ],
    "negative_keywords": [
        "biden", "trump", "politics", "congress", "senate", "election",
        "crypto", "forex", "trading", "investment",
        "nsfw", "gore", "violence", "tragedy",
        "follow for follow", "sub4sub", "tiktok dance"
    ]
}

# 25+ Scored Hook Formulas (based on open-source Instagram Agent Skill)
VIRAL_HOOK_PATTERNS = {
    "curiosity_subversion": [
        "Wait for the ending... I genuinely can't breathe 💀😭",
        "I was NOT prepared for what happened at the 5-second mark 😭💀",
        "Tell me this didn't just actually happen 😂💀",
        "Watch till the end or you'll regret it 😭👇",
        "The way this ended took 5 years off my life 💀🤣"
    ],
    "universal_relatability": [
        "We have all lived this exact situation and survived 💀😭",
        "Why is this so offensively relatable though? 😭💀",
        "Every single friend group has one person who does this 👇😂",
        "Never felt so called out by a 15-second video 💀",
        "This is literally me on a Monday morning 😭"
    ],
    "savage_boldness": [
        "Bro really did not hesitate for a single second 🤣",
        "Nah bro really let his intrusive thoughts win 💀😂",
        "The sheer confidence in this clip is illegal 💀",
        "Never let bro cook ever again 💀😭",
        "Bro woke up and chose pure chaos 🤣"
    ],
    "dm_share_triggers": [
        "Send this to your best friend without saying anything 😭👇",
        "Tag that one friend who needs to see this right now 😂💀",
        "Don't let your group chat see this 💀🤣",
        "If your friend does this, you owe them lunch 😂👇"
    ]
}

class GrowthIntelligence:
    """
    SOTA Autonomous Instagram Growth Engine:
    - Niche Alignment & Trend Filtering.
    - Algorithmic DM Shareability Multipliers.
    - AI Psychological Hook Generation via Free LLM.
    - Audience Interest Modeling.
    """

    def __init__(self):
        self.pollinations_url = "https://text.pollinations.ai/"

    def _query_free_llm(self, prompt: str, timeout: float = 20.0) -> Optional[str]:
        """Queries the free Pollinations AI engine with fallback to None."""
        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.post(
                    self.pollinations_url,
                    json={
                        "messages": [
                            {"role": "system", "content": "You are an elite Instagram Reels Growth Strategist. Reply strictly with valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "model": "openai",
                        "jsonMode": True
                    }
                )
                if res.status_code == 200:
                    return res.text
        except Exception as e:
            logger.warning(f"Free LLM API non-responsive: {e}. Using deterministic growth heuristics.")
        return None

    def evaluate_video(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Multi-Dimensional Evaluation:
        1. Negative keyword exclusion.
        2. Shareability & DM spread ratio.
        3. Completion rate duration factor.
        4. Free LLM Niche & Virality Rating.
        """
        title = (video_data.get("original_title") or "").strip()
        views = max(int(video_data.get("views") or 0), 1)
        likes = int(video_data.get("likes") or 0)
        comments = int(video_data.get("comments") or 0)
        shares = int(video_data.get("shares") or 0)
        duration = int(video_data.get("duration") or 20)

        # 1. Instant Disqualification: Negative Keywords
        lower_title = title.lower()
        for bad_word in TARGET_NICHE["negative_keywords"]:
            if bad_word in lower_title:
                return {
                    "verdict": "REJECTED",
                    "niche_score": 1.0,
                    "growth_score": 0.0,
                    "reasoning": f"Disqualified: Contains blacklisted off-niche term '{bad_word}'."
                }

        # 2. Algorithmic Signals
        share_ratio = (shares / views) * 100
        comment_ratio = (comments / views) * 100

        # Optimal Reels Duration Curve: 12-32s is peak loop completion
        duration_multiplier = 1.0
        if 10 <= duration <= 30:
            duration_multiplier = 1.3  # Sweet spot for high completion rate
        elif duration > 50:
            duration_multiplier = 0.75 # Lower completion rate penalty

        # Shareability Factor (Instagram Reels #1 distribution signal)
        share_score = min(share_ratio * 25.0, 40.0) # Up to 40 pts
        comment_score = min(comment_ratio * 35.0, 25.0) # Up to 25 pts

        # Base algorithmic score (out of 100)
        base_algorithmic_score = (share_score + comment_score) * duration_multiplier

        # 3. LLM Niche & Hook Synthesis
        llm_prompt = f"""
Evaluate this viral short video for an Indian Instagram audience seeking Relatable Comedy & Unexpected Humor:
Title: "{title}"
Metrics: {views:,} views, {likes:,} likes, {comments:,} comments, {shares:,} shares | Duration: {duration}s

Provide JSON:
{{
  "niche_fit": <score from 1.0 to 10.0>,
  "sub_niche": "relatable_life" | "unexpected_twists" | "savage_humor" | "universal_fails" | "other",
  "verdict": "APPROVED" | "REJECTED",
  "hook": "<a one-sentence high-curiosity hook that stops the scroll>",
  "reasoning": "<why this video will get shared in Instagram DMs>"
}}
"""
        llm_response = self._query_free_llm(llm_prompt)
        parsed_llm = None
        if llm_response:
            try:
                parsed_llm = json.loads(llm_response)
            except Exception:
                pass

        if parsed_llm and isinstance(parsed_llm, dict):
            niche_fit = float(parsed_llm.get("niche_fit", 7.5))
            sub_niche = parsed_llm.get("sub_niche", "relatable_life")
            verdict = parsed_llm.get("verdict", "APPROVED")
            hook = parsed_llm.get("hook")
            reasoning = parsed_llm.get("reasoning", "High relatability and shareability.")
        else:
            # Deterministic Heuristic Fallback
            niche_fit = 8.5
            sub_niche = "unexpected_twists" if "end" in lower_title or "wait" in lower_title else "relatable_life"
            verdict = "APPROVED"
            
            # Select hook based on patterns
            category = "curiosity_subversion" if sub_niche == "unexpected_twists" else "universal_relatability"
            import random
            hook = random.choice(VIRAL_HOOK_PATTERNS[category])
            reasoning = f"Heuristic analysis: High DM share ratio ({share_ratio:.2f}%) and optimal {duration}s loop duration."

        final_growth_score = round(base_algorithmic_score + (niche_fit * 3.5), 2)

        return {
            "verdict": verdict,
            "niche_score": niche_fit,
            "sub_niche": sub_niche,
            "growth_score": final_growth_score,
            "share_ratio": round(share_ratio, 2),
            "hook": hook,
            "reasoning": reasoning
        }

    def select_smartest_video(self, candidate_videos: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Compares all ready videos in the queue, runs multi-factor growth evaluation,
        and selects the single best candidate with the highest virality & niche fit.
        """
        if not candidate_videos:
            return None

        evaluated = []
        for vid in candidate_videos:
            eval_res = self.evaluate_video(vid)
            if eval_res.get("verdict") == "APPROVED":
                evaluated.append({
                    "video": vid,
                    "evaluation": eval_res,
                    "score": eval_res.get("growth_score", 0.0)
                })

        if not evaluated:
            # If all were rejected, fallback to the one with highest shares
            return sorted(candidate_videos, key=lambda v: int(v.get("shares") or 0), reverse=True)[0]

        # Sort by final growth score descending
        evaluated.sort(key=lambda x: x["score"], reverse=True)
        winner = evaluated[0]
        
        # Attach the tailored AI hook and rationale
        win_vid = winner["video"]
        win_vid["ai_selected_hook"] = winner["evaluation"]["hook"]
        win_vid["ai_growth_reasoning"] = (
            f"Selected over {len(candidate_videos)} candidates: "
            f"Top growth score ({winner['score']} pts), sub-niche '{winner['evaluation']['sub_niche']}', "
            f"DM share rate: {winner['evaluation']['share_ratio']}%. "
            f"Rationale: {winner['evaluation']['reasoning']}"
        )
        return win_vid

    def craft_viral_caption(self, original_title: str, hook: str) -> str:
        """
        Constructs an Instagram caption engineered for high comments and DM sends.
        Complies with Instagram's 5-hashtag cap and strips AI slop using ig-human.
        """
        from modules.skills_bridge import skills_bridge
        clean_title = re.sub(r'#\w+|@\w+', '', original_title or '').strip()
        
        caption_lines = [
            f"{hook}",
            "",
            f"💭 {clean_title}" if clean_title else "",
            "",
            "👇 Tag that one friend who needs to see this 😂",
            "Follow @1lucky_24 for your daily dose of laughs! 🚀",
            "",
            "#reelsindia #trending #viralmemes #funnyreels #explorepage"
        ]
        raw_caption = "\n".join([line for line in caption_lines if line is not None])
        
        # Humanize: strip any invisible watermarks or AI slop
        humanized = skills_bridge.humanize(raw_caption)
        return humanized.get("clean_text", raw_caption)

    def research_niche_trends(self, niche: str = "Relatable Comedy & Unexpected Twists") -> Dict[str, Any]:
        """
        Deep trend intelligence for Instagram Reels targeting Indian Gen-Z & Millennials.
        Combines algorithmic metrics with audience psychology.
        """
        # Try free LLM for fresh perspective
        llm_prompt = f"""
Provide a high-level trend intelligence report for Instagram Reels in 2026:
Niche: {niche}
Audience: Indian Gen-Z (18-28) & Global Comedy lovers
Include:
1. Top 3 viral content formats right now
2. Peak audio style & pacing
3. DM-share psychological triggers
4. Winning hashtag sets for Indian Explore reach
Reply strictly in JSON:
{{
  "trending_formats": ["format 1", "format 2", "format 3"],
  "audio_strategy": "text",
  "share_triggers": ["trigger 1", "trigger 2"],
  "recommended_hashtags": ["#tag1", "#tag2", "#tag3"]
}}
"""
        res = self._query_free_llm(llm_prompt)
        parsed = None
        if res:
            try:
                parsed = json.loads(res)
            except Exception:
                pass

        if not parsed or not isinstance(parsed, dict):
            parsed = {
                "trending_formats": [
                    "Subverted Expectation: 4-second build-up followed by an absurd sudden twist",
                    "Intrusive Thoughts Won: Highlighting the unspoken chaos of daily life",
                    "Universal Language Fails: Physical humor with zero dialogue needed to go global"
                ],
                "audio_strategy": "Fast-paced punchy comedy soundbites or 130+ BPM upbeat phonk/synth loops",
                "share_triggers": [
                    "Friend group call-outs ('Tag that friend who is literally like this')",
                    "Relatability shock ('I feel personally attacked by this clip')"
                ],
                "recommended_hashtags": [
                    "#reelsindia", "#viralreels", "#relatablecomedy", "#unexpected", "#memesdaily", "#instacomedy", "#explorepage"
                ]
            }

        return {
            "niche": niche,
            "target_demographic": "Indian Gen-Z & Young Millennials (Tier 1 & Tier 2 mobile audience)",
            "retention_sweet_spot": "12 to 24 seconds (achieves >90% loop completion rate)",
            "formats": parsed.get("trending_formats", []),
            "audio_strategy": parsed.get("audio_strategy", ""),
            "share_triggers": parsed.get("share_triggers", []),
            "hashtags": parsed.get("recommended_hashtags", [])
        }

    def generate_viral_hooks(self, topic: str = "", count: int = 5) -> List[Dict[str, str]]:
        """
        Generates psychologically engineered, scroll-stopping 3-second hooks.
        Classified by psychological trigger.
        """
        import random
        hooks = []

        all_categories = list(VIRAL_HOOK_PATTERNS.keys())
        for i in range(count):
            cat = all_categories[i % len(all_categories)]
            formula = random.choice(VIRAL_HOOK_PATTERNS[cat])
            
            category_names = {
                "curiosity_subversion": "Curiosity Gap (High Watch Time)",
                "universal_relatability": "Relatability Anchor (Comment Spiker)",
                "savage_boldness": "Pattern Interrupt (Scroll Stopper)",
                "dm_share_triggers": "DM Share Catalyst (Algorithm Multiplier)"
            }

            hooks.append({
                "hook_text": formula,
                "category": category_names.get(cat, "Viral Catalyst"),
                "visual_direction": "Cut directly into motion at 0.0s. Add bold high-contrast yellow/white subtitle on upper-third screen."
            })

        return hooks

    def consult_ai_director(self, user_query: str, username: str = "1lucky_24", context_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Conversational AI Growth Director:
        Answers any Instagram growth, strategy, optimization, or content question
        using the Free LLM, with fallback to expert growth heuristics.
        """
        context_str = ""
        if context_info:
            context_str = f"Account @{username} Stats: {context_info.get('followers', 0)} followers, {context_info.get('posts', 0)} posts. Pipeline: {context_info.get('ready', 0)} ready reels."

        prompt = f"""
You are the elite AI Instagram Growth Director managing the account @{username}.
Niche: Global Relatable Comedy & Unexpected Humor for Indian Gen-Z.
{context_str}

User Question/Instruction: "{user_query}"

Respond as a confident, knowledgeable, charismatic Growth Director:
- Be clear, direct, and actionable.
- Use bullet points, bold key points, and strategic emojis.
- If the user writes in Hindi or Hinglish, reply warmly in Hinglish or English with Hinglish understanding.
- Do NOT output robot disclaimers. Give real strategies, hook suggestions, or account guidance.
"""
        # Call Free LLM with snappy timeout
        try:
            with httpx.Client(timeout=7.0) as client:
                res = client.post(
                    self.pollinations_url,
                    json={
                        "messages": [
                            {"role": "system", "content": "You are an elite Instagram Growth Director and Reel Strategist. Be concise, punchy, and highly strategic."},
                            {"role": "user", "content": prompt}
                        ],
                        "model": "openai"
                    }
                )
                if res.status_code == 200 and len(res.text.strip()) > 30:
                    return res.text.strip()
        except Exception as e:
            logger.warning(f"Pollinations query timeout or error: {e}")

        # Deterministic Strategic Fallback
        return (
            f"🧠 **AI Director Strategic Analysis for @{username}**\n\n"
            f"Here is your growth gameplan for '{user_query}':\n\n"
            f"1. **Viral Retention Rule:** The first 1.8 seconds determine if Instagram shows your Reel to 100 people or 100,000. Start mid-action, never with a static title screen.\n"
            f"2. **The DM-Share Multiplier:** Instagram's #1 ranking factor in 2026 is Send-to-Friend (DMs). When a user sends a Reel to a friend via DM, the algorithm grants a 4x viral weight.\n"
            f"3. **Optimal Video Duration:** Keep clips strictly between 12 to 24 seconds so the average viewer loops the video 1.5x before scrolling.\n"
            f"4. **Posting Cadence:** Schedule your 3 daily drops at **12:30 PM (lunch break)**, **6:00 PM (commute)**, and **9:00 PM (night scrolling peak)** IST.\n\n"
            f"💡 *Tip: You can ask me to 'Audit profile', 'Generate viral hooks', 'Research trends', or 'Post next reel' anytime!*"
        )

growth_intel = GrowthIntelligence()

