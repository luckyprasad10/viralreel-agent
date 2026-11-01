import os
import random
import re
from typing import Dict, Tuple
from database import db

# High-retention hooks proven to boost Reels watch time and comments
VIRAL_HOOKS = [
    "Wait for the end... I can't breathe 💀😭",
    "Nah bro really thought he was slick 😂",
    "I wasn't expecting that ending at all 😭💀",
    "Bro let his intrusive thoughts win 🤣",
    "Tag that one friend who is literally like this 👇💀",
    "This had me laughing for 10 minutes straight 🤣",
    "Why is this so relatable though? 😭💀",
    "The sheer confidence in this clip 💀😂",
    "Bro really did not hesitate 🤣",
    "Tell me this didn't just happen 😂💀",
    "Send this to someone who needs a good laugh today 🤣👇",
    "I was not prepared for what happened next 💀",
]

CALL_TO_ACTIONS = [
    "Double tap if this made you laugh! ❤️ Follow for daily laughs!",
    "Tag your best friend who needs to see this 😂👇",
    "Drop a '💀' if you weren't expecting that ending!",
    "Share with your group chat right now 😭",
    "Follow for more viral clips every single day! 🚀",
]

TARGET_HASHTAGS = [
    "#reels",
    "#reelsindia",
    "#trending",
    "#viralmemes",
    "#funnyreels",
    "#comedy",
    "#memesdaily",
    "#explorepage",
    "#foryou",
    "#instafunny",
    "#relatable",
    "#laughter",
    "#explore",
    "#viralvideos",
    "#comedyreels",
    "#hilarious"
]

class AICaptioner:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")

    def clean_text(self, text: str) -> str:
        """Strips existing hashtags and clean formatting."""
        if not text:
            return ""
        # Remove existing #hashtags and @mentions
        text = re.sub(r'#\w+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def generate_caption(self, video_id: int) -> Tuple[str, str]:
        """
        Generates an optimized Instagram caption with hook, context, CTA, and hashtags.
        Updates the video in the database.
        """
        video = db.get_video(video_id)
        if not video:
            return "", ""

        original_title = self.clean_text(video.get("original_title", ""))
        hook = random.choice(VIRAL_HOOKS)
        cta = random.choice(CALL_TO_ACTIONS)

        # Select 8-12 balanced hashtags
        selected_hashtags = random.sample(TARGET_HASHTAGS, min(10, len(TARGET_HASHTAGS)))
        hashtags_str = " ".join(selected_hashtags)

        # Build full Instagram caption
        caption_lines = [hook]
        if original_title and len(original_title) > 3:
            caption_lines.append(f"\n{original_title}")
        caption_lines.append(f"\n{cta}")
        caption_lines.append("\n.\n.\n.")
        caption_lines.append(hashtags_str)

        full_caption = "\n".join(caption_lines)

        db.update_video(
            video_id,
            ai_caption=full_caption,
            ai_hashtags=hashtags_str
        )
        db.add_log("INFO", "AICaptioner", f"Generated viral caption for video {video_id}")
        return full_caption, hashtags_str

captioner = AICaptioner()
