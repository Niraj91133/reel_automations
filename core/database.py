import sqlite3
import os
from datetime import datetime

class ChannelDatabase:
    """
    Isolated, thread-safe SQLite database manager for each channel.
    Operates with Write-Ahead Logging (WAL) mode to prevent lock contention.
    Tracks both Published Reels and Hunted Reels sent to Raj for review.
    """
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS processed_reels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        shortcode TEXT UNIQUE,
                        username TEXT,
                        title TEXT,
                        permalink TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS hunted_reels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        shortcode TEXT UNIQUE,
                        creator TEXT,
                        source_query TEXT,
                        views_text TEXT,
                        has_comment_cta INTEGER DEFAULT 0,
                        sent_to_raj INTEGER DEFAULT 0,
                        approved_by_raj INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS processed_stories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        slot_index INTEGER,
                        date_str TEXT,
                        title TEXT,
                        media_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(slot_index, date_str)
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS rejected_reels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        shortcode TEXT UNIQUE,
                        reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        finally:
            conn.close()

    def is_reel_processed(self, shortcode):
        if not shortcode:
            return False
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM processed_reels WHERE shortcode = ?", (shortcode,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def is_reel_hunted(self, shortcode):
        if not shortcode:
            return False
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM hunted_reels WHERE shortcode = ?", (shortcode,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def mark_reel_hunted(self, shortcode, creator="", source_query="", views_text="", has_comment_cta=0, sent_to_raj=1):
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO hunted_reels 
                    (shortcode, creator, source_query, views_text, has_comment_cta, sent_to_raj, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (shortcode, creator or "", source_query or "", views_text or "", int(has_comment_cta), int(sent_to_raj))
                )
            return True
        except Exception as e:
            print(f"Error marking hunted reel {shortcode}: {e}")
            return False
        finally:
            conn.close()

    def mark_reel_approved(self, shortcode):
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("UPDATE hunted_reels SET approved_by_raj = 1 WHERE shortcode = ?", (shortcode,))
            return True
        except:
            return False
        finally:
            conn.close()

    def mark_reel_processed(self, shortcode, username, title, permalink=None):
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO processed_reels (shortcode, username, title, permalink, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (shortcode, username or "creator", title or "", permalink or "")
                )
            return True
        except Exception as e:
            print(f"Error marking reel {shortcode} in DB: {e}")
            return False
        finally:
            conn.close()

    def get_today_count(self):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            today_prefix = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "SELECT COUNT(*) FROM processed_reels WHERE created_at LIKE ?",
                (f"{today_prefix}%",)
            )
            return cursor.fetchone()[0]
        except:
            return 0
        finally:
            conn.close()

    def get_today_hunted_count(self):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            today_prefix = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "SELECT COUNT(*) FROM hunted_reels WHERE created_at LIKE ? AND sent_to_raj = 1",
                (f"{today_prefix}%",)
            )
            return cursor.fetchone()[0]
        except:
            return 0
        finally:
            conn.close()

    def get_recent_posts(self, limit=10):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT shortcode, username, title, permalink, created_at FROM processed_reels ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return cursor.fetchall()
        finally:
            conn.close()

    def get_last_post_datetime(self):
        """Returns the UTC datetime of the most recently published reel, or None."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT created_at FROM processed_reels ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row and row[0]:
                from datetime import timezone
                try:
                    return datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                except Exception:
                    pass
            return None
        finally:
            conn.close()

    def get_recent_hunted(self, limit=10):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT shortcode, creator, source_query, views_text, has_comment_cta, created_at FROM hunted_reels ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return cursor.fetchall()
        finally:
            conn.close()

    def is_reel_rejected(self, shortcode):
        if not shortcode:
            return False
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM rejected_reels WHERE shortcode = ?", (shortcode,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def mark_reel_rejected(self, shortcode, reason="gatekeeper_rejection"):
        if not shortcode:
            return False
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO rejected_reels (shortcode, reason, created_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (shortcode, reason)
                )
            return True
        except:
            return False
        finally:
            conn.close()

    def get_unprocessed_hunted_reels(self, limit=10):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT shortcode, creator, views_text 
                FROM hunted_reels 
                WHERE shortcode NOT IN (SELECT shortcode FROM processed_reels)
                  AND shortcode NOT IN (SELECT shortcode FROM rejected_reels)
                ORDER BY has_comment_cta DESC, id DESC 
                LIMIT ?
                """,
                (limit,)
            )
            return cursor.fetchall()
        finally:
            conn.close()

    def is_story_processed(self, slot_index: int, date_str: str) -> bool:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM processed_stories WHERE slot_index = ? AND date_str = ?", (slot_index, date_str))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def mark_story_processed(self, slot_index: int, date_str: str, title: str = "", media_id: str = ""):
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO processed_stories (slot_index, date_str, title, media_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (slot_index, date_str, title, media_id)
                )
        finally:
            conn.close()

    def get_stories_posted_today_count(self, date_str: str) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM processed_stories WHERE date_str = ?", (date_str,))
            row = cursor.fetchone()
            return row[0] if row else 0
        finally:
            conn.close()
