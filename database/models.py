import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from config import DB_PATH

class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database tables with indexes."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Videos Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tiktok_id TEXT UNIQUE NOT NULL,
                tiktok_url TEXT,
                author TEXT,
                original_title TEXT,
                region TEXT,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                duration INTEGER DEFAULT 0,
                virality_score REAL DEFAULT 0.0,
                cover_url TEXT,
                raw_video_path TEXT,
                processed_video_path TEXT,
                status TEXT DEFAULT 'discovered',
                ai_caption TEXT,
                ai_hashtags TEXT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                scheduled_at TIMESTAMP,
                posted_at TIMESTAMP,
                insta_media_id TEXT,
                insta_code TEXT,
                error_message TEXT
            )
            """)

            # Analytics Logs Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER,
                insta_code TEXT,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                reach INTEGER DEFAULT 0,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(id)
            )
            """)

            # System Logs Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT,
                module TEXT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # AI Agent Strategic Decisions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT,
                reasoning TEXT,
                impact TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Comment Interactions Table (Handles engagement & auto-replies)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS comment_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id TEXT UNIQUE,
                media_id TEXT,
                user_handle TEXT,
                comment_text TEXT,
                reply_text TEXT,
                liked INTEGER DEFAULT 0,
                replied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Agent Chat History Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Bot Settings Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """)

            # Create Indexes for fast querying
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_tiktok_id ON videos(tiktok_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_virality ON videos(virality_score DESC)")

            conn.commit()

    def add_video(self, video_data: Dict[str, Any]) -> Optional[int]:
        """Insert a newly discovered video if not already exists."""
        sql = """
        INSERT OR IGNORE INTO videos (
            tiktok_id, tiktok_url, author, original_title, region,
            views, likes, comments, shares, duration, virality_score,
            cover_url, status, discovered_at
        ) VALUES (
            :tiktok_id, :tiktok_url, :author, :original_title, :region,
            :views, :likes, :comments, :shares, :duration, :virality_score,
            :cover_url, :status, CURRENT_TIMESTAMP
        )
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, video_data)
                conn.commit()
                return cursor.lastrowid if cursor.rowcount > 0 else None
        except Exception as e:
            self.add_log("ERROR", "Database", f"Error adding video {video_data.get('tiktok_id')}: {e}")
            return None

    def update_video(self, video_id: int, **kwargs) -> bool:
        """Update any fields on a video record."""
        if not kwargs:
            return False
        set_clauses = [f"{k} = :{k}" for k in kwargs.keys()]
        kwargs["video_id"] = video_id
        sql = f"UPDATE videos SET {', '.join(set_clauses)} WHERE id = :video_id"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, kwargs)
            conn.commit()
            return cursor.rowcount > 0

    def get_video(self, video_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_video_by_tiktok_id(self, tiktok_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM videos WHERE tiktok_id = ?", (tiktok_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_queue(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch videos by status, ordered by virality score."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute(
                    "SELECT * FROM videos WHERE status = ? ORDER BY virality_score DESC, discovered_at DESC LIMIT ?",
                    (status, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM videos ORDER BY discovered_at DESC LIMIT ?",
                    (limit,)
                )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_published_videos(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM videos WHERE status = 'posted' ORDER BY posted_at DESC LIMIT ?",
                (limit,)
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_next_ready_video(self) -> Optional[Dict[str, Any]]:
        """Fetch the highest scoring processed video ready to post."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM videos 
                WHERE status IN ('processed', 'ready', 'approved') 
                  AND processed_video_path IS NOT NULL 
                ORDER BY virality_score DESC, discovered_at ASC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Aggregate stats for the live dashboard."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_discovered,
                    SUM(CASE WHEN status = 'discovered' THEN 1 ELSE 0 END) as discovered_count,
                    SUM(CASE WHEN status = 'processed' OR status = 'ready' THEN 1 ELSE 0 END) as ready_count,
                    SUM(CASE WHEN status = 'posted' THEN 1 ELSE 0 END) as posted_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                    AVG(virality_score) as avg_virality
                FROM videos
            """)
            stats = dict(cursor.fetchone() or {})
            
            cursor.execute("SELECT SUM(views), SUM(likes), SUM(comments) FROM analytics_logs")
            analytics = cursor.fetchone()
            stats["total_insta_views"] = analytics[0] or 0
            stats["total_insta_likes"] = analytics[1] or 0
            stats["total_insta_comments"] = analytics[2] or 0

            return stats

    def add_log(self, level: str, module: str, message: str):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO system_logs (level, module, message) VALUES (?, ?, ?)",
                    (level.upper(), module, message)
                )
                conn.commit()
        except Exception:
            pass

    def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM system_logs ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            return [dict(r) for r in cursor.fetchall()]

    def add_agent_decision(self, action_type: str, reasoning: str, impact: str = ""):
        """Log an autonomous strategic decision made by the AI Agent."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO agent_decisions (action_type, reasoning, impact) VALUES (?, ?, ?)",
                    (action_type, reasoning, impact)
                )
                conn.commit()
        except Exception as e:
            self.add_log("ERROR", "Database", f"Error logging agent decision: {e}")

    def get_agent_decisions(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM agent_decisions ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            return [dict(r) for r in cursor.fetchall()]

    def record_comment_interaction(self, comment_id: str, media_id: str, user_handle: str, comment_text: str, reply_text: str = "", liked: int = 1) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO comment_interactions (comment_id, media_id, user_handle, comment_text, reply_text, liked)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (comment_id, media_id, user_handle, comment_text, reply_text, liked))
                conn.commit()
                return True
        except Exception as e:
            self.add_log("ERROR", "Database", f"Error recording comment interaction: {e}")
            return False

    def is_comment_replied(self, comment_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM comment_interactions WHERE comment_id = ?", (comment_id,))
            return cursor.fetchone() is not None

    def get_recent_comment_interactions(self, limit: int = 25) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM comment_interactions ORDER BY replied_at DESC LIMIT ?",
                (limit,)
            )
            return [dict(r) for r in cursor.fetchall()]

    def add_chat_message(self, role: str, message: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO agent_chats (role, message) VALUES (?, ?)",
                (role, message)
            )
            conn.commit()

    def get_chat_history(self, limit: int = 30) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM (SELECT * FROM agent_chats ORDER BY timestamp DESC LIMIT ?) ORDER BY timestamp ASC",
                (limit,)
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_setting(self, key: str, default: Any = None) -> Any:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM bot_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except Exception:
                    return row[0]
            return default

    def set_setting(self, key: str, value: Any):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            val_str = json.dumps(value) if isinstance(value, (dict, list, bool, int, float)) else str(value)
            cursor.execute(
                "INSERT INTO bot_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, val_str)
            )
            conn.commit()

# Singleton DB instance
db = DatabaseManager()
