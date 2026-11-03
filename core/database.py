import sqlite3
import os
from datetime import datetime

class ChannelDatabase:
    """
    Isolated, thread-safe SQLite database manager for each channel.
    Operates with Write-Ahead Logging (WAL) mode to prevent lock contention.
    """
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        # WAL mode allows concurrent readers and writers without lock errors
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
        finally:
            conn.close()

    def is_reel_processed(self, shortcode):
        if not shortcode:
            return False
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM processed_reels WHERE shortcode = ?", (shortcode,))
            row = cursor.fetchone()
            return row is not None
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
            count = cursor.fetchone()[0]
            return count
        except:
            return 0
        finally:
            conn.close()

    def get_recent_posts(self, limit=5):
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
