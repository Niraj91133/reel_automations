"""
Channel Concurrency Lock Manager:
Ensures multiple processes (dispatcher, backfill daemon, story poster)
never attempt concurrent Instagram API operations on the same channel simultaneously.
"""

import os
import time
from contextlib import contextmanager

LOCK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "databases", "locks")

os.makedirs(LOCK_DIR, exist_ok=True)

def is_channel_locked(channel_id, max_age_seconds=180):
    lock_file = os.path.join(LOCK_DIR, f"{channel_id}.lock")
    if not os.path.exists(lock_file):
        return False
    try:
        mtime = os.path.getmtime(lock_file)
        if time.time() - mtime > max_age_seconds:
            # Stale lock, safely break
            os.remove(lock_file)
            return False
        return True
    except:
        return False

@contextmanager
def channel_lock(channel_id, timeout=60):
    lock_file = os.path.join(LOCK_DIR, f"{channel_id}.lock")
    start = time.time()
    
    while is_channel_locked(channel_id):
        if time.time() - start > timeout:
            # Break stale lock
            try: os.remove(lock_file)
            except: pass
            break
        time.sleep(1.0)

    try:
        with open(lock_file, "w") as f:
            f.write(str(os.getpid()))
        yield
    finally:
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except:
            pass
