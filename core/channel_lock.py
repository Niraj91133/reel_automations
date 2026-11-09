"""
Channel Concurrency Lock Manager:
Ensures multiple processes (dispatcher, backfill daemon, story poster)
never attempt concurrent Instagram API operations on the same channel simultaneously.
Auto-cleans stale locks if the locking process is dead.
"""

import os
import time
from contextlib import contextmanager

LOCK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "databases", "locks")
os.makedirs(LOCK_DIR, exist_ok=True)

def is_pid_alive(pid):
    """Checks if a process with given PID is actively running on Windows."""
    if pid <= 0:
        return False
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        SYNCHRONIZE = 0x00100000
        process = kernel32.OpenProcess(SYNCHRONIZE, 0, pid)
        if process != 0:
            kernel32.CloseHandle(process)
            return True
        return False
    except Exception:
        return True

def is_channel_locked(channel_id, max_age_seconds=120):
    lock_file = os.path.join(LOCK_DIR, f"{channel_id}.lock")
    if not os.path.exists(lock_file):
        return False
    try:
        # 1. Check PID liveness
        with open(lock_file, "r") as f:
            content = f.read().strip()
        if content.isdigit():
            pid = int(content)
            if not is_pid_alive(pid):
                try: os.remove(lock_file)
                except: pass
                return False

        # 2. Check age
        mtime = os.path.getmtime(lock_file)
        if time.time() - mtime > max_age_seconds:
            try: os.remove(lock_file)
            except: pass
            return False

        return True
    except Exception:
        return False

@contextmanager
def channel_lock(channel_id, timeout=20):
    lock_file = os.path.join(LOCK_DIR, f"{channel_id}.lock")
    start = time.time()
    
    while is_channel_locked(channel_id):
        if time.time() - start > timeout:
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
