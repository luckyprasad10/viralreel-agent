import os
import subprocess
import logging
from pathlib import Path
from typing import Optional
import imageio_ffmpeg
from config import PROCESSED_DIR, SPEED_MODIFIER, COLOR_FILTER_TWEAK, NORMALIZE_AUDIO
from database import db

logger = logging.getLogger("VideoProcessor")
logging.basicConfig(level=logging.INFO)

class VideoProcessor:
    def __init__(self, output_dir: Path = PROCESSED_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    def process_for_reels(self, video_id: int) -> Optional[str]:
        """
        Processes downloaded video:
        1. Resizes & pads to vertical 9:16 (1080x1920) if necessary.
        2. Applies 1.02x speed factor to alter video & audio hash (anti-duplicate).
        3. Subtle color grading enhancement (contrast/saturation bump for Instagram).
        4. Strips original metadata to make it appear 100% original.
        """
        video = db.get_video(video_id)
        if not video:
            db.add_log("ERROR", "Processor", f"Video {video_id} not found.")
            return None

        raw_path = video.get("raw_video_path")
        if not raw_path or not Path(raw_path).exists():
            db.add_log("ERROR", "Processor", f"Raw video path missing for video {video_id}")
            return None

        tiktok_id = video["tiktok_id"]
        output_path = self.output_dir / f"{tiktok_id}_insta.mp4"

        # If already processed and exists, reuse
        if output_path.exists() and output_path.stat().st_size > 50_000:
            db.update_video(video_id, processed_video_path=str(output_path), status="ready")
            return str(output_path)

        db.add_log("INFO", "Processor", f"Processing {tiktok_id} for Instagram Reels...")

        # Build FFmpeg filter chain
        # 1. Video filters: speed, color grade, 1080x1920 scale with centered pad
        vf_parts = [
            f"setpts=PTS/{SPEED_MODIFIER}",
            "scale=1080:1920:force_original_aspect_ratio=decrease",
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
        ]
        if COLOR_FILTER_TWEAK:
            vf_parts.append("eq=contrast=1.03:brightness=0.01:saturation=1.05")

        video_filter = ",".join(vf_parts)

        # 2. Audio filters: tempo match + audio normalization
        af_parts = [f"atempo={SPEED_MODIFIER}"]
        if NORMALIZE_AUDIO:
            af_parts.append("loudnorm=I=-16:TP=-1.5:LRA=11")
        audio_filter = ",".join(af_parts)

        cmd = [
            self.ffmpeg_exe,
            "-y",                     # Overwrite output
            "-i", str(raw_path),
            "-vf", video_filter,
            "-af", audio_filter,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-map_metadata", "-1",     # Strip original metadata
            "-movflags", "+faststart", # Enable streaming playback
            str(output_path)
        ]

        try:
            # Run FFmpeg
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            if process.returncode == 0 and output_path.exists() and output_path.stat().st_size > 50_000:
                db.update_video(
                    video_id,
                    processed_video_path=str(output_path),
                    status="ready"
                )
                db.add_log("SUCCESS", "Processor", f"Processed video ready for Reel: {output_path.name}")
                return str(output_path)
            else:
                err_snippet = process.stderr[-300:] if process.stderr else "Unknown FFmpeg error"
                db.add_log("ERROR", "Processor", f"FFmpeg failed for {tiktok_id}: {err_snippet}")
                db.update_video(video_id, status="failed", error_message=f"FFmpeg error: {err_snippet}")
                return None

        except Exception as e:
            db.add_log("ERROR", "Processor", f"Exception processing {tiktok_id}: {e}")
            db.update_video(video_id, status="failed", error_message=str(e))
            return None

processor = VideoProcessor()
