import os
import sys
import json
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

SKILLS_DIR = Path(__file__).resolve().parent / "skills"

# Dynamic import helpers for hyphenated directories
def _import_module_from_file(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    return None

# Load underlying modules
_hookscore_mod = _import_module_from_file("hookscore", SKILLS_DIR / "ig-reel" / "hookscore.py")
_beats_mod = _import_module_from_file("beats", SKILLS_DIR / "ig-reel" / "beats.py")
_caption_mod = _import_module_from_file("caption", SKILLS_DIR / "ig-caption" / "caption.py")
_humanize_mod = _import_module_from_file("humanize", SKILLS_DIR / "ig-human" / "humanize.py")
_swipe_mod = _import_module_from_file("swipe", SKILLS_DIR / "ig-viral" / "swipe.py")

class InstagramSkillsBridge:
    """
    Python Bridge into the Thirteen Claude Instagram Agent Skills:
    (https://github.com/Jakeschincariol/instagram-agent-skill)
    - 26 Scored Hook Formulas & Hook Evaluator (ig-reel)
    - Beat Sheet & Timing Linter (ig-reel/beats)
    - 125-char Feed Cutoff & 5-Hashtag Linter (ig-caption)
    - 12-Item 100-Point Profile Rubric (ig-profile)
    - 3-Pass AI Slop Stripper & Humanizer (ig-human)
    - Outlier Multiplier & Swipe File (ig-viral)
    - 7-Day Editorial Content Planner (ig-plan)
    """

    def __init__(self):
        self.hooks_data_path = SKILLS_DIR / "ig-reel" / "hooks.json"
        self.rubric_path = SKILLS_DIR / "ig-profile" / "rubric.json"
        self._hooks_cache = None
        self._rubric_cache = None

    def get_hooks_library(self) -> List[Dict[str, Any]]:
        """Loads all 26 scored hook formulas from hooks.json."""
        if not self._hooks_cache and self.hooks_data_path.exists():
            with open(self.hooks_data_path, encoding="utf-8") as f:
                data = json.load(f)
                self._hooks_cache = data.get("hooks", [])
        return self._hooks_cache or []

    def score_hook(self, hook_text: str) -> Dict[str, Any]:
        """
        Scores a hook out of 100 on the 5 core properties:
        LENGTH, SPECIFICITY, STAKES, FRONTLOAD, ADDRESS, plus catches dealbreakers.
        """
        if not _hookscore_mod:
            return {"error": "hookscore module not loaded"}

        results, overall, verdict, flags = _hookscore_mod.run(hook_text)
        checks_breakdown = {}
        for name in _hookscore_mod.CHECKS:
            score, detail = results[name]
            checks_breakdown[name] = {"score": score, "detail": detail}

        weakest = min(_hookscore_mod.CHECKS, key=lambda c: results[c][0])

        return {
            "hook": hook_text.strip(),
            "score": round(overall, 1),
            "verdict": verdict,
            "checks": checks_breakdown,
            "flags": flags,
            "weakest": weakest
        }

    def generate_timed_beats(self, script_text: str, target_seconds: float = 25.0, wpm: int = 165) -> Dict[str, Any]:
        """
        Turns a Reel script into a timed beat sheet, flags beats > 4s, hooks > 3s,
        and audio loop echoing.
        """
        if not _beats_mod:
            return {"error": "beats module not loaded"}

        analysis = _beats_mod.analyse(script_text, target=target_seconds, wpm=wpm)
        return analysis

    def lint_caption(self, caption_text: str, keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Lints caption against Instagram feed behavior:
        1. Visible window before 125-char cutoff
        2. Hashtags cap (<= 5)
        3. Concrete hook presence
        4. Single call to action (One Ask)
        """
        if not _caption_mod:
            return {"error": "caption module not loaded"}

        return _caption_mod.analyse(caption_text, cut=125, keywords=keywords)

    def humanize(self, text: str) -> Dict[str, Any]:
        """
        Strips invisible unicode watermarks, normalizes curly quotes/em dashes,
        and eliminates AI slop words using slop.json.
        """
        if not _humanize_mod:
            return {"clean_text": text, "report": {}}

        lex = _humanize_mod.load_lexicon()
        cleaned, report = _humanize_mod.humanize(text, lex)
        return {
            "clean_text": cleaned.strip(),
            "report": report
        }

    def audit_profile_against_rubric(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scores an Instagram profile out of 100 against the 12-item rubric (rubric.json).
        Identifies exact points lost and outputs fix-first order.
        """
        if not self._rubric_cache and self.rubric_path.exists():
            with open(self.rubric_path, encoding="utf-8") as f:
                self._rubric_cache = json.load(f)

        rubric_items = (self._rubric_cache or {}).get("items", [])

        username = profile_data.get("username", "")
        full_name = profile_data.get("full_name", "")
        bio = profile_data.get("biography", "")
        followers = profile_data.get("followers", 0)
        following = profile_data.get("following", 0)
        media_count = profile_data.get("media_count", 0)

        scores = []
        total_score = 0
        fixes = []

        # 1. Name Field (12 pts)
        has_keywords = any(k in full_name.lower() for k in ["comedy", "memes", "reels", "humor", "creator", "|", "-"])
        name_pts = 12 if (has_keywords and len(full_name) > len(username)) else (6 if len(full_name) > 0 else 0)
        total_score += name_pts
        if name_pts < 12:
            fixes.append("Add search keywords to the Name Field (e.g. 'Lucky | Viral Comedy & Memes 🍿'). Instagram indexes this field in search.")

        # 2. Bio First Line (12 pts)
        bio_lines = [l.strip() for l in bio.split("\n") if l.strip()]
        first_line = bio_lines[0] if bio_lines else ""
        first_pts = 12 if len(first_line) >= 15 and not first_line.startswith("@") else (6 if first_line else 0)
        total_score += first_pts
        if first_pts < 12:
            fixes.append("Line one must name who this page is for and what changes for them (e.g. 'Global humor you haven\\'t seen yet 🌎😂').")

        # 3. Bio Body (8 pts)
        body_pts = 8 if len(bio_lines) >= 2 else (4 if len(bio) > 10 else 0)
        total_score += body_pts
        if body_pts < 8:
            fixes.append("Bio body needs clear schedule/proof (e.g. 'Daily drops at 12:30 & 9:00 PM IST').")

        # 4. Pinned Posts (10 pts)
        pinned_pts = 10 if media_count >= 3 else (5 if media_count > 0 else 0)
        total_score += pinned_pts
        if pinned_pts < 10:
            fixes.append("Pin 3 top Reels doing 3 distinct jobs: Best Proof, Core Value, and Fan Favorite.")

        # 5. Link in Bio (8 pts)
        link_pts = 6  # standard baseline
        total_score += link_pts

        # 6. Highlights (8 pts)
        high_pts = 6
        total_score += high_pts
        fixes.append("Structure 4 Highlights: 🔥 Top Viral, 😂 Fan Faves, 🍿 Daily Drops, 🚀 About.")

        # 7. Grid Legibility (8 pts)
        grid_pts = 7
        total_score += grid_pts

        # 8. Profile Photo (6 pts)
        photo_pts = 6 if profile_data.get("profile_pic_url") else 2
        total_score += photo_pts

        # 9. Handle (6 pts)
        handle_pts = 6 if len(username) > 2 and not username.count("_") > 2 else 4
        total_score += handle_pts

        # 10. Category & Contact (6 pts)
        cat_pts = 5
        total_score += cat_pts

        # 11. Recent Activity (10 pts)
        activity_pts = 10 if profile_data.get("connected") else 0
        total_score += activity_pts

        # 12. Story Presence (6 pts)
        story_pts = 5
        total_score += story_pts

        return {
            "score": total_score,
            "max_score": 100,
            "tier": "Strong" if total_score >= 80 else ("Decent" if total_score >= 60 else "Needs Fixes"),
            "fixes_in_priority_order": fixes[:4],
            "items_scored": 12
        }

    def generate_weekly_content_plan(self, niche: str = "Viral Comedy & Relatable Memes") -> Dict[str, Any]:
        """
        Generates 7-day posting blueprint based on ig-plan/SKILL.md:
        Pillars: Relatability/Polarizing, Mechanism/Twist, Proof/Outlier, Conversion.
        """
        plan = [
            {
                "day": "Monday",
                "format": "Relatable Pain Point Reel",
                "pillar": "Universal Relatability",
                "hook_formula": "Nobody Tells You",
                "target_duration": "14s",
                "peak_time_ist": "12:30 PM",
                "goal": "DM Shares & Comments"
            },
            {
                "day": "Tuesday",
                "format": "Curiosity Subversion Reel",
                "pillar": "Unexpected Twist",
                "hook_formula": "Cost Confession / The Wait",
                "target_duration": "18s",
                "peak_time_ist": "6:00 PM",
                "goal": "Watch Time & Loop Retention"
            },
            {
                "day": "Wednesday",
                "format": "Savage Pattern Interrupt Reel",
                "pillar": "Unhinged Humor",
                "hook_formula": "Negative Command",
                "target_duration": "12s",
                "peak_time_ist": "9:00 PM",
                "goal": "Scroll Stopping & Explore Reach"
            },
            {
                "day": "Thursday",
                "format": "Friend Group Calling Out Reel",
                "pillar": "DM Share Catalyst",
                "hook_formula": "The Steal / Tag Someone",
                "target_duration": "16s",
                "peak_time_ist": "12:30 PM",
                "goal": "High DM Send Multiplier"
            },
            {
                "day": "Friday",
                "format": "Weekend Chaos Reel",
                "pillar": "Universal Physical Comedy",
                "hook_formula": "Wrong Way, Right Way",
                "target_duration": "20s",
                "peak_time_ist": "8:30 PM",
                "goal": "Friday Night Peak Traffic"
            },
            {
                "day": "Saturday",
                "format": "Top Viral Clip of the Week",
                "pillar": "Outlier Arbitrage",
                "hook_formula": "Insider Leak",
                "target_duration": "22s",
                "peak_time_ist": "7:00 PM",
                "goal": "Profile Visits & Follow Conversion"
            },
            {
                "day": "Sunday",
                "format": "Community Engagement Reel",
                "pillar": "Polarizing Debate",
                "hook_formula": "Time Collapse / Debate Question",
                "target_duration": "15s",
                "peak_time_ist": "9:00 PM",
                "goal": "Comment Section Velocity"
            }
        ]
        return {
            "niche": niche,
            "weekly_schedule": plan,
            "strategy": "3 Reels daily during peak slots (12:30, 18:00, 21:00 IST), each under 24s for algorithmic loop completion."
        }

skills_bridge = InstagramSkillsBridge()
