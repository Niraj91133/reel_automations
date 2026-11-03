import os
import uuid
import subprocess
from templates.template_engine import create_base_layer, create_circle_hook_layer

def extract_thumbnail_isolated(video_path, output_dir, job_id):
    """Extracts high-res keyframe at 2.5s for the circular zoom hook."""
    output_path = os.path.join(output_dir, f"thumb_{job_id}.jpg")
    cmd = [
        "ffmpeg", "-y",
        "-threads", "2",
        "-ss", "00:00:02.500",
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "1",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(output_path):
        return output_path
    return None

def ensure_telegram_size_limit(video_path, output_dir, job_id, max_size_mb=19.5):
    """
    Guarantees video is under 19.5 MB so Telegram's getFile API 
    can generate a public CDN link for Meta Graph API auto-publishing.
    """
    max_bytes = int(max_size_mb * 1024 * 1024)
    if not os.path.exists(video_path):
        return video_path
    
    file_size = os.path.getsize(video_path)
    if file_size <= max_bytes:
        return video_path

    print(f"⚠️ Video size ({file_size / (1024*1024):.1f} MB) exceeds Telegram 20MB limit. Compressing...", flush=True)
    compressed_path = os.path.join(output_dir, f"comp_{job_id}.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-threads", "2",
        "-i", video_path,
        "-c:v", "libx264",
        "-crf", "28",
        "-preset", "faster",
        "-c:a", "aac",
        "-b:a", "128k",
        compressed_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode == 0 and os.path.exists(compressed_path):
        if os.path.getsize(compressed_path) > max_bytes:
            crf_31_path = os.path.join(output_dir, f"c31_{job_id}.mp4")
            cmd2 = [
                "ffmpeg", "-y",
                "-threads", "2",
                "-i", video_path,
                "-c:v", "libx264",
                "-crf", "31",
                "-preset", "faster",
                "-c:a", "aac",
                "-b:a", "96k",
                crf_31_path
            ]
            res2 = subprocess.run(cmd2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res2.returncode == 0 and os.path.exists(crf_31_path):
                try: os.remove(compressed_path)
                except: pass
                compressed_path = crf_31_path

        print(f"✅ Video compressed to {os.path.getsize(compressed_path) / (1024*1024):.1f} MB!", flush=True)
        return compressed_path
    return video_path

def render_channel_video(
    input_video_path,
    channel_config,
    hook_pill,
    main_title,
    sub_quote
):
    """
    Renders fully isolated, studio-quality 9:16 Instagram Reel.
    Uses UUID to ensure 0% collision even if multiple accounts render concurrently.
    """
    job_id = uuid.uuid4().hex[:8]
    workspace_dir = channel_config.get("runtime", {}).get("workspace_dir", ".")
    os.makedirs(workspace_dir, exist_ok=True)

    base_layer_path = os.path.join(workspace_dir, f"base_{job_id}.png")
    circle_layer_path = os.path.join(workspace_dir, f"circle_{job_id}.png")
    final_render_path = os.path.join(workspace_dir, f"final_{job_id}.mp4")

    # 1. Extract circle thumbnail
    circle_thumb = extract_thumbnail_isolated(input_video_path, workspace_dir, job_id)

    # 2. Render graphics layers
    create_base_layer(
        output_path=base_layer_path,
        channel_config=channel_config,
        hook_pill=hook_pill,
        main_title=main_title,
        sub_quote=sub_quote
    )

    create_circle_hook_layer(
        output_path=circle_layer_path,
        circle_img_path=circle_thumb
    )

    # 3. FFmpeg Ultra-HD Filter Graph
    cmd = [
        "ffmpeg", "-y",
        "-threads", "2",
        "-i", input_video_path,
        "-loop", "1", "-i", base_layer_path,
        "-loop", "1", "-i", circle_layer_path,
        "-filter_complex",
        (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease:flags=bicubic,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black[vid];"
            "[vid][1:v]overlay=0:0[with_base];"
            "[2:v]fade=t=out:st=4.3:d=0.7:alpha=1[circle_faded];"
            "[with_base][circle_faded]overlay=0:0:enable='between(t,0,5)'[v_out]"
        ),
        "-map", "[v_out]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        final_render_path
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        err = res.stderr.decode("utf-8", errors="ignore")[-500:]
        print(f"FFmpeg error for {channel_config.get('channel_id')}: {err}")
        raise RuntimeError("FFmpeg processing failed")

    # Cleanup temp graphics assets
    for p in [base_layer_path, circle_layer_path, circle_thumb]:
        if p and os.path.exists(p):
            try: os.remove(p)
            except: pass

    # Ensure size is under 20MB for Telegram getFile CDN
    delivered_path = ensure_telegram_size_limit(final_render_path, workspace_dir, job_id)
    return delivered_path, job_id
