import sqlite3
import os

DB_PATH = "reels_history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_reels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shortcode TEXT UNIQUE,
            username TEXT,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_reel_processed(shortcode):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM processed_reels WHERE shortcode = ?", (shortcode,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def mark_reel_processed(shortcode, username, title):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO processed_reels (shortcode, username, title) VALUES (?, ?, ?)",
            (shortcode, username, title)
        )
        conn.commit()
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
