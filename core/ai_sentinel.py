"""
core/ai_sentinel.py
===================
Autonomous SRE & Predictive Sentinel AI Bot for 6-Channel Instagram Pipeline.

Capabilities:
1. Deep Telemetry Gathering (Meta Graph API, Gemini Keys, Buffers, SQLite Databases, Disk, Process Watchdog).
2. Gemini AI Deep Reasoning & Predictive Failure Analysis (Forecasting buffer runouts, API rate limits, pacing bottlenecks).
3. Instant Telegram Dispatch (Detailed Executive Health Audit delivered directly to user's Telegram).
4. Persistent Audit History (Tracks system reliability trends over time).
"""

import os
import sys
import time
import json
import glob
import sqlite3
import shutil
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from google import genai
from core.config_manager import get_channel_config
from core.telegram_hub import TelegramHub

DEFAULT_TELEGRAM_BOT_TOKEN = "8149202459:AAGRZBE4uZY7UXUV4HySazIuc-M5V2hHK8A"
DEFAULT_TELEGRAM_CHAT_ID = "711598335"

ACTIVE_CHANNELS = [
    ("thestartup_street", "🚀 Startup Road", "@startup_road"),
    ("healthy_diet", "🥗 Gud Tree", "@gudtree_"),
    ("theloan_road", "💳 The Loan Road", "@the_loan_road"),
    ("trading_road24", "📊 Trading Road 24", "@trading_road24"),
    ("marketing_road24", "📱 Marketing Road 24", "@marketing_road24"),
    ("viral_finds", "🛍️ Trending Road", "@trending_road")
]

class SentinelBot:
    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token or DEFAULT_TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or DEFAULT_TELEGRAM_CHAT_ID
        self.hub = TelegramHub(self.bot_token, self.chat_id)
        self.audit_log_file = BASE_DIR / "databases" / "sentinel_audit_history.jsonl"
        self.audit_log_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_ist_time(self):
        """Returns current Indian Standard Time as formatted string."""
        ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        return ist_now.strftime("%Y-%m-%d %I:%M:%S %p IST")

    # ==========================================
    # 1. LIVE TELEMETRY COLLECTION
    # ==========================================
    def collect_telemetry(self):
        """Gathers granular real-time telemetry from every tier of the pipeline."""
        print("🔍 [Sentinel AI] Gathering full pipeline telemetry...")
        telemetry = {
            "timestamp_ist": self._get_ist_time(),
            "channels": {},
            "system": {},
            "dispatcher_active": False,
            "recent_log_anomalies": []
        }

        # Check running processes
        try:
            import psutil
            for p in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmd = p.info.get('cmdline') or []
                cmd_str = " ".join(cmd)
                if "run_all_4channels_tomorrow_dispatcher.py" in cmd_str:
                    telemetry["dispatcher_active"] = True
                    telemetry["dispatcher_pid"] = p.info.get('pid')
                    break
        except Exception as e:
            telemetry["dispatcher_active"] = "unknown"

        # Check Disk & Cache Space
        try:
            total, used, free = shutil.disk_usage("C:/")
            telemetry["system"]["disk_free_gb"] = round(free / (1024**3), 2)
            telemetry["system"]["disk_total_gb"] = round(total / (1024**3), 2)
            
            cache_dir = Path("C:/reel_cache")
            if cache_dir.exists():
                cache_size = sum(f.stat().st_size for f in cache_dir.glob('**/*') if f.is_file())
                telemetry["system"]["reel_cache_mb"] = round(cache_size / (1024**2), 2)
            else:
                telemetry["system"]["reel_cache_mb"] = 0
        except Exception as e:
            telemetry["system"]["disk_error"] = str(e)

        # Audit Each Channel
        for ch_id, display_name, handle in ACTIVE_CHANNELS:
            ch_telemetry = {
                "display_name": display_name,
                "handle": handle,
                "meta_token_status": "UNKNOWN",
                "gemini_api_status": "UNKNOWN",
                "gemini_latency_ms": 0,
                "ready_buffer_count": 0,
                "predicted_buffer_lifespan_hours": 0.0,
                "today_posts_count": 0,
                "last_post_time_ist": "None",
                "minutes_since_last_post": 9999
            }

            try:
                cfg = get_channel_config(ch_id)
                creds = cfg.get("credentials", {})
                ig_id = creds.get("instagram_account_id", "")
                page_token = creds.get("page_access_token", "")
                gemini_key = creds.get("gemini_api_key", "")
                db_path = cfg.get("runtime", {}).get("db_path", "")
                ws_dir = cfg.get("runtime", {}).get("workspace_dir", "")

                # 1. Meta Graph API Ping
                if ig_id and page_token:
                    meta_url = f"https://graph.facebook.com/v21.0/{ig_id}?fields=username,media_count&access_token={page_token}"
                    t0 = time.time()
                    try:
                        req = urllib.request.Request(meta_url)
                        with urllib.request.urlopen(req, timeout=8) as resp:
                            if resp.status == 200:
                                ch_telemetry["meta_token_status"] = "ACTIVE_HEALTHY"
                            else:
                                ch_telemetry["meta_token_status"] = f"HTTP_{resp.status}"
                    except urllib.error.HTTPError as he:
                        ch_telemetry["meta_token_status"] = f"ERROR_{he.code}"
                    except Exception as e_meta:
                        ch_telemetry["meta_token_status"] = f"NET_ERR_{type(e_meta).__name__}"
                    ch_telemetry["meta_latency_ms"] = round((time.time() - t0) * 1000)

                # 2. Dedicated Gemini API Key Ping
                if gemini_key:
                    t0 = time.time()
                    try:
                        client = genai.Client(api_key=gemini_key)
                        res = client.models.generate_content(
                            model="gemini-3.1-flash-lite",
                            contents="1"
                        )
                        if res and res.text:
                            ch_telemetry["gemini_api_status"] = "ACTIVE_HEALTHY"
                    except Exception as e_g:
                        ch_telemetry["gemini_api_status"] = f"FAILED: {str(e_g)[:60]}"
                    ch_telemetry["gemini_latency_ms"] = round((time.time() - t0) * 1000)

                # 3. Buffer & Queue Inventory (Burn rate calculation)
                q_dir = Path(ws_dir) / "tomorrow_reels"
                if q_dir.exists():
                    ready_vids = list(q_dir.glob("ready_*.mp4"))
                    ch_telemetry["ready_buffer_count"] = len(ready_vids)
                    # Each reel posts roughly every 30 minutes (0.5 hours)
                    ch_telemetry["predicted_buffer_lifespan_hours"] = round(len(ready_vids) * 0.5, 1)

                # 4. History Database Stats
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    c = conn.cursor()
                    c.execute("SELECT count(*) FROM processed_reels WHERE created_at LIKE ?", (f"{datetime.utcnow().strftime('%Y-%m-%d')}%",))
                    ch_telemetry["today_posts_count"] = c.fetchone()[0]
                    c.execute("SELECT created_at FROM processed_reels ORDER BY id DESC LIMIT 1")
                    last_row = c.fetchone()
                    conn.close()
                    if last_row and last_row[0]:
                        try:
                            last_utc = datetime.strptime(last_row[0], "%Y-%m-%d %H:%M:%S")
                            last_ist = last_utc + timedelta(hours=5, minutes=30)
                            ch_telemetry["last_post_time_ist"] = last_ist.strftime("%I:%M %p")
                            diff_sec = (datetime.utcnow() - last_utc).total_seconds()
                            ch_telemetry["minutes_since_last_post"] = round(diff_sec / 60, 1)
                        except:
                            pass

            except Exception as e_ch:
                ch_telemetry["audit_error"] = str(e_ch)

            telemetry["channels"][ch_id] = ch_telemetry

        # 5. Scan recent dispatcher logs for anomalies
        task_logs = list(Path(BASE_DIR).glob(".gemini/antigravity/brain/*/tasks/task-*.log"))
        if not task_logs:
            # Fallback search in task folder
            task_logs = sorted(Path("C:/Users/DHEERAJ/.gemini/antigravity/brain").glob("*/.system_generated/tasks/task-*.log"), key=os.path.getmtime, reverse=True)

        if task_logs:
            try:
                latest_log = task_logs[0]
                with open(latest_log, "r", encoding="utf-8", errors="ignore") as lf:
                    lines = lf.readlines()[-60:]
                for l in lines:
                    if any(err_word in l for err_word in ["REJECTED", "ERROR", "Failed", "Exception", "SSL", "Timeout"]):
                        telemetry["recent_log_anomalies"].append(l.strip()[:100])
            except:
                pass

        return telemetry

    # ==========================================
    # 2. GEMINI AI PREDICTIVE REASONING ENGINE
    # ==========================================
    def run_ai_predictive_audit(self, telemetry):
        """Passes full telemetry to Gemini AI for SRE analysis, prediction, and scoring."""
        print("🧠 [Sentinel AI] Running Gemini AI predictive reasoning & diagnostic model...")
        
        system_prompt = """You are Sentinel AI — the autonomous Chief Site Reliability Engineer (SRE) and Predictive Architect for an enterprise 6-channel automated Instagram media company.

Your job is to perform a deep forensic analysis of the live system telemetry, identify hidden risks, PREDICT what will fail or bottleneck in the next 1 to 12 hours, calculate the overall Health Score (0-100), and write a razor-sharp executive audit report in engaging Hinglish.

CRITICAL PREDICTIVE AUDIT DIRECTIVES:
1. OVERALL SYSTEM HEALTH SCORE:
   - Calculate an exact score out of 100 based on:
     * Meta API status (25 pts)
     * Gemini API keys validity (25 pts)
     * Ready Buffer lifespan & depletion rate (25 pts)
     * Dispatcher process & posting pacing (25 pts)
   - Assign a Status: 🟢 STABLE & OPTIMAL (85-100) | 🟡 CAUTION NEEDED (60-84) | 🔴 CRITICAL INTERVENTION (0-59)

2. 🔮 PREDICTIVE RISK FORECAST (LOOK AHEAD 1-12 HOURS):
   - Exactly identify which channel's buffer will run out first and in how many hours/minutes.
   - Predict if any channel is lagging behind its 30-reels/day target (currently running 7:00 AM - 10:00 PM).
   - Check if any Gemini API key latency is abnormal or failing.
   - Forecast potential Meta API rate limits or spam traps.

3. 🔍 LOG ANOMALIES & SENSING:
   - Analyze recent log warnings (e.g. non-Hindi audio rejections, timeouts, fallbacks).
   - Tell what it means in practical terms.

4. 🛠️ PRIORITIZED ACTIONS / RECOMMENDATIONS:
   - Bulleted, actionable steps for the operator or autonomous systems (e.g. replenish buffer for channel X, monitor key Y).

5. CHANNEL-BY-CHANNEL METRICS SNAPSHOT:
   - Concise bullet list for all 6 channels: Name, Posted Today / 30, Buffer Count, Token & Gemini Status.

FORMATTING REQUIREMENTS:
- Write in ultra-clean, professional, engaging Hinglish with emojis.
- Perfect for reading on a mobile Telegram screen (bold headers, clean bullet points, no giant unformatted code blocks).
"""

        primary_key = os.environ.get("STARTUP_GEMINI_KEY") or os.environ.get("GEMINI_API_KEY", "")
        client = genai.Client(api_key=primary_key)

        prompt = f"""
LIVE SYSTEM TELEMETRY SNAPSHOT ({telemetry['timestamp_ist']}):
```json
{json.dumps(telemetry, indent=2)}
```

Generate the complete Predictive SRE Health Audit Report now.
"""

        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=[system_prompt, prompt]
            )
            report_text = response.text.strip()
            return report_text
        except Exception as e:
            fallback_report = f"""
🚨 <b>[SENTINEL AI FALLBACK DIAGNOSTIC]</b>
<b>Time:</b> {telemetry['timestamp_ist']}
<b>Dispatcher Active:</b> {telemetry['dispatcher_active']}
<b>Disk Free:</b> {telemetry['system'].get('disk_free_gb')} GB

⚠️ <i>AI Reasoning Engine encountered an error: {e}</i>
<b>Raw Status:</b>
- Channels active: {len(telemetry['channels'])}
- Processed: Telemetry collected successfully.
"""
            return fallback_report

    # ==========================================
    # 3. DISPATCH & REPORTING
    # ==========================================
    def execute_audit(self, notify_telegram=True):
        """Full end-to-end execution: Collect Telemetry -> Run AI Diagnosis -> Send to Telegram."""
        telemetry = self.collect_telemetry()
        ai_report = self.run_ai_predictive_audit(telemetry)

        # 1. Print to console
        print("\n" + "=" * 65)
        print("🤖 SENTINEL AI EXECUTIVE AUDIT REPORT")
        print("=" * 65)
        print(ai_report)
        print("=" * 65 + "\n")

        # 2. Persist audit to history
        try:
            with open(self.audit_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "timestamp": telemetry["timestamp_ist"],
                    "telemetry": telemetry,
                    "report_summary": ai_report[:300]
                }) + "\n")
        except:
            pass

        # 3. Send to Telegram
        if notify_telegram and self.hub:
            print(f"📲 [Sentinel AI] Dispatching report to Telegram ({self.chat_id})...")
            # Wrap in HTML header
            header = f"🛡️ <b>SENTINEL AI • LIVE PIPELINE AUDIT</b>\n<i>Autonomous System Reliability & Prediction</i>\n\n"
            full_msg = header + ai_report
            # Truncate if exceeds Telegram 4096 character limit
            if len(full_msg) > 4000:
                chunks = [full_msg[i:i+3900] for i in range(0, len(full_msg), 3900)]
                for chunk in chunks:
                    self.hub.send_message(chunk, parse_mode="HTML")
            else:
                self.hub.send_message(full_msg, parse_mode="HTML")
            print("✅ Telegram notification delivered successfully!")

        return ai_report

if __name__ == '__main__':
    sentinel = SentinelBot()
    sentinel.execute_audit(notify_telegram=True)
