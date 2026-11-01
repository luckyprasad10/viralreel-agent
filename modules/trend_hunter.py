import httpx
import logging
import time
from typing import List, Dict, Any, Optional
from config import (
    TARGET_REGIONS, MIN_VIEWS, MIN_LIKES, MIN_VIRALITY_RATIO,
    MIN_DURATION, MAX_DURATION
)
from database import db

logger = logging.getLogger("TrendHunter")
logging.basicConfig(level=logging.INFO)

try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.tikwm.com/"
}

class TrendHunter:
    def __init__(self, regions: Optional[List[str]] = None):
        self.regions = regions or TARGET_REGIONS or ["US", "GB", "AU", "CA"]
        self.base_url = "https://www.tikwm.com/api/feed/list"

    def calculate_virality_score(self, views: int, likes: int, comments: int, shares: int) -> float:
        """
        Virality score formula:
        Gives high weight to shares (spreadability) and comments (high debate/engagement).
        """
        if views <= 0:
            return 0.0
        weighted_interactions = (likes * 1.5) + (comments * 2.5) + (shares * 3.5)
        score = (weighted_interactions / views) * 100
        return round(score, 2)

    def fetch_feed(self, region: str) -> List[Dict[str, Any]]:
        """Fetch viral feed for a given country code with Cloudflare bypass."""
        url = f"{self.base_url}?region={region}"

        # 1. Primary: curl_cffi with Chrome TLS impersonation (bypasses Cloudflare 403 on cloud IPs)
        if HAS_CURL_CFFI:
            try:
                res = cffi_requests.get(url, impersonate="chrome120", timeout=20, headers=HEADERS)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("code") == 0 and "data" in data:
                        return data["data"]
                else:
                    db.add_log("WARN", "TrendHunter", f"curl_cffi fetch for {region} returned {res.status_code}")
            except Exception as e:
                db.add_log("WARN", "TrendHunter", f"curl_cffi exception for {region}: {e}")

        # 2. Fallback: standard httpx
        try:
            with httpx.Client(timeout=20, headers=HEADERS) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == 0 and "data" in data:
                        return data["data"]
                else:
                    db.add_log("WARN", "TrendHunter", f"Feed fetch failed for region {region} (HTTP {response.status_code})")
        except Exception as e:
            db.add_log("ERROR", "TrendHunter", f"Exception fetching {region} feed: {e}")
        return []

    def discover_viral_videos(self) -> List[Dict[str, Any]]:
        """
        Scrapes trending feeds across all target regions, applies virality filters,
        and saves new candidates to the database.
        """
        discovered = []
        db.add_log("INFO", "TrendHunter", f"Starting trend discovery across regions: {', '.join(self.regions)}")

        for region in self.regions:
            videos = self.fetch_feed(region)
            for v in videos:
                tiktok_id = str(v.get("video_id") or "")
                if not tiktok_id:
                    continue

                # Check if already in database
                if db.get_video_by_tiktok_id(tiktok_id):
                    continue

                # Exclude ads
                if v.get("is_ad"):
                    continue

                views = int(v.get("play_count") or 0)
                likes = int(v.get("digg_count") or 0)
                comments = int(v.get("comment_count") or 0)
                shares = int(v.get("share_count") or 0)
                duration = int(v.get("duration") or 0)

                # Duration check (if duration is reported by API)
                if duration > 0 and (duration < MIN_DURATION or duration > MAX_DURATION):
                    continue

                virality_score = self.calculate_virality_score(views, likes, comments, shares)
                like_ratio = likes / max(views, 1)

                # Filter condition: High virality score OR high engagement ratio
                is_viral = (views >= MIN_VIEWS and likes >= MIN_LIKES) or (virality_score >= 12.0 and likes >= 3000)

                if is_viral:
                    author_data = v.get("author") or {}
                    author_name = author_data.get("unique_id") or author_data.get("nickname") or "unknown"
                    title = v.get("title") or ""
                    cover_url = v.get("cover") or v.get("origin_cover") or ""
                    play_url = v.get("play") or ""

                    video_record = {
                        "tiktok_id": tiktok_id,
                        "tiktok_url": f"https://www.tiktok.com/@{author_name}/video/{tiktok_id}",
                        "author": author_name,
                        "original_title": title,
                        "region": region,
                        "views": views,
                        "likes": likes,
                        "comments": comments,
                        "shares": shares,
                        "duration": duration,
                        "virality_score": virality_score,
                        "cover_url": cover_url,
                        "status": "discovered"
                    }

                    row_id = db.add_video(video_record)
                    if row_id:
                        video_record["id"] = row_id
                        video_record["play_url"] = play_url
                        discovered.append(video_record)

            time.sleep(1)  # Respectful pacing between regions

        db.add_log("INFO", "TrendHunter", f"Discovery finished. Found {len(discovered)} new high-viral videos.")
        return discovered

if __name__ == "__main__":
    hunter = TrendHunter()
    results = hunter.discover_viral_videos()
    print(f"Total discovered: {len(results)}")
    for r in results[:3]:
        print(f"ID: {r['tiktok_id']} | Virality: {r['virality_score']} | Views: {r['views']} | Title: {r['original_title'][:40]}")
