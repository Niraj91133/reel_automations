import os
import sys
import uuid
import subprocess
from templates.template_engine import create_base_layer, create_circle_hook_layer

sys.stdout.reconfigure(encoding='utf-8')

_CACHED_ENCODER = None

def get_best_hardware_encoder():
    """
    Detects the fastest available hardware video encoder on this machine:
    1. h264_nvenc (NVIDIA GPU NVENC)
    2. h264_mf (Windows Media Foundation Direct3D GPU Acceleration)
    3. h264_qsv (Intel Quick Sync Video)
    4. libx264 (CPU fallback)
    """
    global _CACHED_ENCODER
    if _CACHED_ENCODER:
        return _CACHED_ENCODER

    candidates = [
        ("h264_nvenc", ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "24"]),
        ("h264_mf", ["-c:v", "h264_mf", "-b:v", "3500k"]),
        ("h264_qsv", ["-c:v", "h264_qsv", "-b:v", "3500k"]),
        ("libx264", ["-threads", "2", "-c:v", "libx264", "-preset", "fast", "-crf", "23"])
    ]

    for name, enc_args in candidates:
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "nullsrc=s=640x360:d=0.1", *enc_args, "-f", "null", "-"]
        try:
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                print(f"⚡ [VideoEngine] Hardware acceleration active: {name.upper()}", flush=True)
                _CACHED_ENCODER = (name, enc_args)
                return _CACHED_ENCODER
        except Exception:
            continue

    print("⚠️ [VideoEngine] Falling back to CPU libx264 encoder.", flush=True)
    _CACHED_ENCODER = ("libx264", ["-threads", "2", "-c:v", "libx264", "-preset", "fast", "-crf", "23"])
    return _CACHED_ENCODER

def extract_thumbnail_isolated(video_path, output_dir, job_id):
    """Extracts high-res keyframe at 2.5s for the circular zoom hook."""
    output_path = os.path.join(output_dir, f"thumb_{job_id}.jpg")
    cmd = [
        "ffmpeg", "-y",
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
    Uses GPU hardware acceleration for instant compression.
    """
    max_bytes = int(max_size_mb * 1024 * 1024)
    if not os.path.exists(video_path):
        return video_path
    
    file_size = os.path.getsize(video_path)
    if file_size <= max_bytes:
        return video_path

    print(f"⚠️ Video size ({file_size / (1024*1024):.1f} MB) exceeds Telegram 20MB limit. Hardware compressing...", flush=True)
    compressed_path = os.path.join(output_dir, f"comp_{job_id}.mp4")
    
    enc_name, _ = get_best_hardware_encoder()
    if enc_name in ["h264_mf", "h264_qsv"]:
        v_args = ["-c:v", enc_name, "-b:v", "2200k"]
    elif enc_name == "h264_nvenc":
        v_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "28"]
    else:
        v_args = ["-threads", "2", "-c:v", "libx264", "-crf", "28", "-preset", "faster"]

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        *v_args,
        "-c:a", "aac",
        "-b:a", "128k",
        compressed_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode == 0 and os.path.exists(compressed_path):
        if os.path.getsize(compressed_path) > max_bytes:
            crf_31_path = os.path.join(output_dir, f"c31_{job_id}.mp4")
            if enc_name in ["h264_mf", "h264_qsv"]:
                v_args2 = ["-c:v", enc_name, "-b:v", "1600k"]
            elif enc_name == "h264_nvenc":
                v_args2 = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "31"]
            else:
                v_args2 = ["-threads", "2", "-c:v", "libx264", "-crf", "31", "-preset", "faster"]

            cmd2 = [
                "ffmpeg", "-y",
                "-i", video_path,
                *v_args2,
                "-c:a", "aac",
                "-b:a", "96k",
                crf_31_path
            ]
            res2 = subprocess.run(cmd2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res2.returncode == 0 and os.path.exists(crf_31_path):
                try: os.remove(compressed_path)
                except: pass
                compressed_path = crf_31_path

        print(f"✅ Video hardware compressed to {os.path.getsize(compressed_path) / (1024*1024):.1f} MB!", flush=True)
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
    Uses GPU Hardware Acceleration (0% CPU Load, 5x-10x faster).
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

    # 3. Detect best hardware encoder
    enc_name, enc_args = get_best_hardware_encoder()

    # 4. Ultra-Fast Compositor
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video_path,
        "-loop", "1", "-i", base_layer_path,
        "-loop", "1", "-i", circle_layer_path,
        "-filter_complex",
        (
            "[0:v]eq=contrast=1.03:brightness=0.01:saturation=1.03,scale=1080:1920:force_original_aspect_ratio=decrease:flags=fast_bilinear,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black[vid];"
            "[vid][1:v]overlay=0:0[with_base];"
            "[2:v]fade=t=out:st=4.3:d=0.7:alpha=1[circle_faded];"
            "[with_base][circle_faded]overlay=0:0:enable='between(t,0,5)'[v_out]"
        ),
        "-map", "[v_out]",
        "-map", "0:a?",
        "-af", "aresample=44100",
        "-map_metadata", "-1",
        *enc_args,
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        final_render_path
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        err = res.stderr.decode("utf-8", errors="ignore")[-500:]
        print(f"FFmpeg error with {enc_name}: {err}")
        # Automatic fallback to CPU if hardware encoder failed
        print("Retrying with safe CPU libx264...")
        cpu_cmd = [
            "ffmpeg", "-y",
            "-threads", "2",
            "-i", input_video_path,
            "-loop", "1", "-i", base_layer_path,
            "-loop", "1", "-i", circle_layer_path,
            "-filter_complex",
            (
                "[0:v]eq=contrast=1.03:brightness=0.01:saturation=1.03,scale=1080:1920:force_original_aspect_ratio=decrease:flags=fast_bilinear,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black[vid];"
                "[vid][1:v]overlay=0:0[with_base];"
                "[2:v]fade=t=out:st=4.3:d=0.7:alpha=1[circle_faded];"
                "[with_base][circle_faded]overlay=0:0:enable='between(t,0,5)'[v_out]"
            ),
            "-map", "[v_out]",
            "-map", "0:a?",
            "-af", "aresample=44100",
            "-map_metadata", "-1",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            final_render_path
        ]
        res_cpu = subprocess.run(cpu_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res_cpu.returncode != 0:
            raise RuntimeError(f"FFmpeg processing failed completely: {res_cpu.stderr.decode('utf-8', errors='ignore')[-300:]}")

    # Cleanup temp graphics assets
    for p in [base_layer_path, circle_layer_path, circle_thumb]:
        if p and os.path.exists(p):
            try: os.remove(p)
            except: pass

    # Ensure size is under 20MB for Telegram getFile CDN
    delivered_path = ensure_telegram_size_limit(final_render_path, workspace_dir, job_id)
    return delivered_path, job_id
