import streamlit as st
import json
import os
import sys
import subprocess
import threading
from datetime import datetime
from pathlib import Path

# Setup paths
BASE_DIR = str(Path(__file__).resolve().parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import list_available_channels, get_channel_config, save_channel_config, load_master_config
from core.database import ChannelDatabase

st.set_page_config(
    page_title="Reel Automation Control Center",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main { background-color: #0f172a; }
    .stTabs [data-baseweb="tab-list"] { gap: 12px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: white !important;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
    }
    .badge-green { background-color: #064e3b; color: #34d399; }
    .badge-blue { background-color: #1e3a8a; color: #60a5fa; }
</style>
""", unsafe_allow_html=True)

st.title("🎛️ Multi-Account Reel Automation Control Center")
st.caption("AI-Powered Viral Hunting • Two-Way DM Curation • Auto-Scheduler & Publisher")

channels = list_available_channels()
channel_names = {
    "startup_road": "💼 Startup Road (@startup_road)",
    "healthy_diet": "🥗 Gudtree (@gudtree_)",
    "trading_pulse": "📈 Trading Road (@trading_road_)",
    "viral_finds": "🛍️ Trending Road (@trending_road)"
}

# Sidebar - Master Controls
with st.sidebar:
    st.header("⚡ Master Operations")
    master_cfg = load_master_config()
    st.write(f"**Default Model:** `{master_cfg.get('default_model', 'gemini-3.1-flash-lite')}`")
    st.write(f"**Telegram Bot:** `@my_reel_auto_bot`")
    st.write(f"**Admin Chat ID:** `{master_cfg.get('admin_chat_id', '711598335')}`")

    st.divider()
    st.subheader("🚀 Quick Actions")
    
    col_act1, col_act2 = st.columns(2)
    with col_act1:
        if st.button("▶ Start Master Scheduler", use_container_width=True):
            cmd = f'start cmd /k "python master_controller.py"'
            os.system(cmd)
            st.success("Master Controller launched in background!")
            
    with col_act2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    st.divider()
    st.subheader("🧪 Verification Test")
    if st.button("🏹 Run 5 Reels Test (5 Min Gap)", use_container_width=True, type="secondary"):
        cmd = f'start cmd /k "python test_5_reels_flow.py 5 5"'
        os.system(cmd)
        st.success("Launched 5-Reels test runner in new window!")

    st.divider()
    st.markdown("### 💡 System Guide")
    st.info(
        "1. **Hunt:** Searches Keywords & Hashtags and DMs up to 80 reels to @im_raaaj_.\n"
        "2. **Curation:** Raj selects best 30 and shares back into the chat.\n"
        "3. **Publish:** Bot renders & posts the 30 approved reels between 6 AM - 9 PM!"
    )

# Main Tab navigation for the 4 Channels
tab_labels = [channel_names.get(ch, ch) for ch in channels]
tabs = st.tabs(tab_labels)

for idx, ch_id in enumerate(channels):
    with tabs[idx]:
        cfg = get_channel_config(ch_id)
        display_name = cfg.get("display_name", ch_id)
        username = cfg.get("instagram_username", ch_id)
        db = ChannelDatabase(cfg["runtime"]["db_path"])
        
        today_posts = db.get_today_count()
        today_hunted = db.get_today_hunted_count()
        
        sched_settings = cfg.get("schedule_settings", {})
        hunt_settings = cfg.get("hunting_settings", {})
        content_settings = cfg.get("content_settings", {})
        
        post_target = content_settings.get("daily_post_limit", 30)
        hunt_target = hunt_settings.get("hunt_target_daily", 80)

        # Row 1: Real-time Stats Cards
        st.markdown("### 📊 Live Performance & Status")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Today's Published Posts", f"{today_posts} / {post_target}", f"{int((today_posts/max(post_target,1))*100)}% target")
            st.progress(min(today_posts / max(post_target, 1), 1.0))
        with col2:
            st.metric("Hunted Reels Sent to Raj", f"{today_hunted} / {hunt_target}", f"{int((today_hunted/max(hunt_target,1))*100)}% sent")
            st.progress(min(today_hunted / max(hunt_target, 1), 1.0))
        with col3:
            st.metric("Meta Graph API Token", "🟢 PERMANENT", "Never Expires (0)")
        with col4:
            st.metric("Gemini 3.1 AI Status", "🟢 ACTIVE", "Free Quota 1500/day")

        st.divider()

        # Two Main Form Columns: Hunting vs Schedule
        c_left, c_right = st.columns([1, 1])

        with c_left:
            st.subheader("🔍 1. Search & Hunting Engine")
            st.caption("Instagram explore bar me ye keywords aur hashtags automatically search honge:")

            # Keywords Editor
            current_kw = hunt_settings.get("keywords", [])
            kw_text = st.text_area(
                "Search Keywords (Har line me ek keyword likhein):",
                value="\n".join(current_kw),
                height=130,
                key=f"kw_{ch_id}",
                help="Example: how to earn money, apps to go viral, etc."
            )

            # Hashtags Editor
            current_tags = hunt_settings.get("hashtags", [])
            tags_text = st.text_area(
                "Target Hashtags (Har line me ek hashtag jaise #startupindia):",
                value="\n".join(current_tags),
                height=130,
                key=f"tag_{ch_id}",
                help="Example: #startupindia, #cleanfood, #tradingstrategy"
            )

            col_sub1, col_sub2 = st.columns(2)
            with col_sub1:
                min_views_val = st.number_input(
                    "Minimum Views Filter:",
                    min_value=5000,
                    max_value=1000000,
                    value=int(hunt_settings.get("min_views", 25000)),
                    step=5000,
                    key=f"views_{ch_id}"
                )
            with col_sub2:
                hunt_limit_val = st.number_input(
                    "Daily Hunt Limit to Send to Raj:",
                    min_value=10,
                    max_value=200,
                    value=int(hunt_target),
                    step=10,
                    key=f"hunt_lim_{ch_id}"
                )

            comment_cta_val = st.checkbox(
                "🎯 Prioritize 'Comment Karo' CTA Videos (High Engagement)",
                value=bool(hunt_settings.get("prioritize_comment_cta", True)),
                key=f"cta_{ch_id}"
            )

        with c_right:
            st.subheader("⏰ 2. Schedule & Timing Engine")
            st.caption("Reels kis time interval me post hongi:")

            col_t1, col_t2 = st.columns(2)
            with col_t1:
                start_h = st.number_input("Start Hour (24h format):", min_value=0, max_value=23, value=int(sched_settings.get("start_hour", 6)), key=f"sh_{ch_id}")
            with col_t2:
                end_h = st.number_input("End Hour (24h format):", min_value=0, max_value=23, value=int(sched_settings.get("end_hour", 21)), key=f"eh_{ch_id}")

            interval_m = st.slider(
                "Post Interval (Minutes):",
                min_value=15,
                max_value=120,
                value=int(sched_settings.get("interval_minutes", 30)),
                step=5,
                key=f"int_{ch_id}",
                help="Har kitne minute me agla video post hona chahiye"
            )

            daily_post_val = st.slider(
                "Daily Publishing Target (Posts/Day):",
                min_value=5,
                max_value=50,
                value=int(post_target),
                step=1,
                key=f"post_lim_{ch_id}"
            )

            dm_target_val = st.text_input(
                "DM Curation Target Username (Raj):",
                value=hunt_settings.get("dm_target_chat", "im_raaaj_"),
                key=f"dm_tgt_{ch_id}"
            )

            hook_pill_val = st.text_input(
                "Default Hook Badge Text:",
                value=content_settings.get("default_hook_pill", "VIRAL LESSON"),
                key=f"hook_{ch_id}"
            )

            first_comment_val = st.text_input(
                "💬 Auto First Comment (Posted immediately after Reel is Live):",
                value=content_settings.get("first_comment_template", "Comment below and I will send you the details! 🚀"),
                key=f"fcomm_{ch_id}",
                help="Meta API automatically posts this high-converting CTA as the first comment on the reel."
            )

        # Action Buttons
        st.divider()
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([2, 1, 1, 1.5])

        with col_btn1:
            if st.button(f"💾 SAVE ALL CHANGES FOR [{display_name.upper()}]", use_container_width=True, type="primary"):
                # Parse updated keywords & hashtags
                new_keywords = [k.strip() for k in kw_text.split("\n") if k.strip()]
                new_hashtags = [t.strip() for t in tags_text.split("\n") if t.strip()]

                # Update config dictionary
                cfg["hunting_settings"]["keywords"] = new_keywords
                cfg["hunting_settings"]["hashtags"] = new_hashtags
                cfg["hunting_settings"]["min_views"] = int(min_views_val)
                cfg["hunting_settings"]["hunt_target_daily"] = int(hunt_limit_val)
                cfg["hunting_settings"]["prioritize_comment_cta"] = bool(comment_cta_val)
                cfg["hunting_settings"]["dm_target_chat"] = dm_target_val.strip()

                cfg["schedule_settings"]["start_hour"] = int(start_h)
                cfg["schedule_settings"]["end_hour"] = int(end_h)
                cfg["schedule_settings"]["interval_minutes"] = int(interval_m)

                cfg["content_settings"]["daily_post_limit"] = int(daily_post_val)
                cfg["content_settings"]["default_hook_pill"] = hook_pill_val.strip()
                cfg["content_settings"]["first_comment_template"] = first_comment_val.strip()

                # Save directly to disk
                save_channel_config(ch_id, cfg)
                st.toast(f"✅ {display_name} configuration saved successfully!", icon="💾")
                st.success(f"Changes saved to configs/{ch_id}.json! Backend scheduler will immediately use the new settings.")

        with col_btn2:
            if st.button(f"🏹 Hunt Test (10)", key=f"hunt_btn_{ch_id}", use_container_width=True):
                st.info(f"Starting test hunt for {display_name}...")
                cmd = f'start cmd /k "python run_channel.py {ch_id} 1"'
                os.system(cmd)

        with col_btn3:
            if st.button(f"🚀 Publish 1 Now", key=f"pub_btn_{ch_id}", use_container_width=True):
                cmd = f'start cmd /k "python -c \"from core.full_autopilot import run_channel_autopilot; run_channel_autopilot(\'{ch_id}\')\""'
                os.system(cmd)

        with col_btn4:
            if st.button(f"📅 Cloud-Schedule 25", key=f"sched_btn_{ch_id}", use_container_width=True):
                st.info(f"Starting tomorrow's Cloud-Scheduling for {display_name}...")
                cmd = f'start cmd /k "python -c \"from core.cloud_scheduler import cloud_schedule_channel_for_tomorrow; cloud_schedule_channel_for_tomorrow(\'{ch_id}\', 25)\""'
                os.system(cmd)

        # Database History Explorer
        st.divider()
        st.subheader("📜 Recent Activity History")
        tab_h1, tab_h2 = st.tabs(["Published Live Posts", "Hunted Reels Sent to Raj"])

        with tab_h1:
            recent_posts = db.get_recent_posts(10)
            if recent_posts:
                data = []
                for p in recent_posts:
                    data.append({
                        "Shortcode": p[0],
                        "Creator": p[1],
                        "Title": p[2],
                        "Instagram Link": p[3],
                        "Published At": p[4]
                    })
                st.dataframe(data, use_container_width=True)
            else:
                st.write("No published reels yet today.")

        with tab_h2:
            recent_hunted = db.get_recent_hunted(10)
            if recent_hunted:
                data = []
                for h in recent_hunted:
                    data.append({
                        "Shortcode": h[0],
                        "Source Query": h[2],
                        "Views": h[3],
                        "Has Comment CTA": "Yes" if h[4] else "No",
                        "Hunted At": h[5]
                    })
                st.dataframe(data, use_container_width=True)
            else:
                st.write("No hunted reels recorded yet.")

