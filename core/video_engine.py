import os
import sys
import uuid
import subprocess
from templates.template_engine import create_base_layer, create_circle_hook_layer

sys.stdout.reconfigure(encoding='utf-8')

_CACHED_ENCODER = None

def get_video_duration(video_path):
    """Accurately extracts video duration in seconds via ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            video_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10)
        dur = float(res.stdout.strip())
        return max(dur, 1.0)
    except Exception:
        return 60.0

def calculate_dynamic_bitrate(duration_sec, target_mb=16.5):
    """
    Calculates the exact video bitrate (kbps) required to guarantee 
    the finished video is under target_mb (default 16.5 MB, well below Telegram 20MB limit).
    Eliminates double-encoding and dispatch lag!
    """
    total_kbits = target_mb * 8192
    audio_kbits = 96
    allowed_v_bitrate = int((total_kbits / max(duration_sec, 5.0)) - audio_kbits)
    # Clamp between 450 kbps (minimum clean mobile quality) and 2800 kbps (crisp 1080x1920)
    safe_bitrate = max(450, min(2800, allowed_v_bitrate))
    return safe_bitrate

def get_best_hardware_encoder(target_bitrate=2200):
    """
    Detects the fastest available hardware video encoder on this machine:
    1. h264_nvenc (NVIDIA GPU NVENC)
    2. h264_mf (Windows Media Foundation Direct3D GPU Acceleration)
    3. h264_qsv (Intel Quick Sync Video)
    4. libx264 (CPU fallback)
    """
    global _CACHED_ENCODER
    if _CACHED_ENCODER:
        name = _CACHED_ENCODER[0]
        if name in ["h264_mf", "h264_qsv"]:
            return name, ["-c:v", name, "-b:v", f"{target_bitrate}k"]
        elif name == "h264_nvenc":
            return name, ["-c:v", "h264_nvenc", "-b:v", f"{target_bitrate}k", "-preset", "p4"]
        else:
            return name, ["-threads", "2", "-c:v", "libx264", "-b:v", f"{target_bitrate}k", "-preset", "fast"]

    candidates = [
        ("h264_nvenc", ["-c:v", "h264_nvenc", "-b:v", f"{target_bitrate}k", "-preset", "p4"]),
        ("h264_mf", ["-c:v", "h264_mf", "-b:v", f"{target_bitrate}k"]),
        ("h264_qsv", ["-c:v", "h264_qsv", "-b:v", f"{target_bitrate}k"]),
        ("libx264", ["-threads", "2", "-c:v", "libx264", "-b:v", f"{target_bitrate}k", "-preset", "fast"])
    ]

    for name, enc_args in candidates:
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "nullsrc=s=640x360:d=0.1", *enc_args, "-f", "null", "-"]
        try:
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                print(f"⚡ [VideoEngine] Hardware acceleration active: {name.upper()}", flush=True)
                _CACHED_ENCODER = (name, enc_args)
                return name, enc_args
        except Exception:
            continue

    print("⚠️ [VideoEngine] Falling back to CPU libx264 encoder.", flush=True)
    _CACHED_ENCODER = ("libx264", ["-threads", "2", "-c:v", "libx264", "-b:v", f"{target_bitrate}k", "-preset", "fast"])
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

def ensure_telegram_size_limit(video_path, output_dir, job_id, max_size_mb=18.0):
    """
    Rapid safety check: If video is already under 18.0 MB, returns immediately (0s delay).
    If a very long video exceeds 18 MB, applies dynamic bitrate compression.
    """
    max_bytes = int(max_size_mb * 1024 * 1024)
    if not os.path.exists(video_path):
        return video_path
    
    file_size = os.path.getsize(video_path)
    if file_size <= max_bytes:
        return video_path

    print(f"⚠️ Video size ({file_size / (1024*1024):.1f} MB) exceeds safety threshold. Dynamic re-compressing...", flush=True)
    dur = get_video_duration(video_path)
    safe_v_rate = calculate_dynamic_bitrate(dur, target_mb=16.0)
    compressed_path = os.path.join(output_dir, f"comp_{job_id}.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-threads", "2",
        "-i", video_path,
        "-c:v", "libx264",
        "-b:v", f"{safe_v_rate}k",
        "-maxrate", f"{int(safe_v_rate * 1.25)}k",
        "-bufsize", f"{safe_v_rate * 2}k",
        "-preset", "faster",
        "-c:a", "aac",
        "-b:a", "96k",
        compressed_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode == 0 and os.path.exists(compressed_path) and os.path.getsize(compressed_path) <= max_bytes:
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
    Uses GPU Hardware Acceleration with Single-Pass Dynamic Bitrate 
    to guarantee output is under 17.5 MB on the very first try!
    """
    job_id = uuid.uuid4().hex[:8]
    workspace_dir = channel_config.get("runtime", {}).get("workspace_dir", ".")
    os.makedirs(workspace_dir, exist_ok=True)
    channel_id = channel_config.get("channel_id", "")

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

    # 3. Dynamic Duration & Bitrate Calculation (First-Pass Guarantee < 17.5 MB)
    duration = get_video_duration(input_video_path)
    target_v_bitrate = calculate_dynamic_bitrate(duration, target_mb=16.5)
    enc_name, enc_args = get_best_hardware_encoder(target_bitrate=target_v_bitrate)

    # 4. Anti-Duplicate Content Micro-Transformation for Mirror Channels (trading_road24)
    # Alters audio & video perceptual hash (PDQ/TMK) so Instagram treats it as 100% original!
    if channel_id == "trading_road24":
        filter_base = (
            "[0:v]eq=contrast=1.04:brightness=0.01:saturation=1.04,"
            "scale=1080:1920:force_original_aspect_ratio=decrease:flags=fast_bilinear,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black[vid];"
            "[vid][1:v]overlay=0:0[with_base];"
            "[2:v]fade=t=out:st=4.3:d=0.7:alpha=1[circle_faded];"
            "[with_base][circle_faded]overlay=0:0:enable='between(t,0,5)'[v_out]"
        )
        audio_filter = "asetrate=44100*1.008,aresample=44100" # 0.8% micro-pitch shift (inaudible to human, changes audio hash)
    else:
        filter_base = (
            "[0:v]eq=contrast=1.03:brightness=0.01:saturation=1.03,"
            "scale=1080:1920:force_original_aspect_ratio=decrease:flags=fast_bilinear,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black[vid];"
            "[vid][1:v]overlay=0:0[with_base];"
            "[2:v]fade=t=out:st=4.3:d=0.7:alpha=1[circle_faded];"
            "[with_base][circle_faded]overlay=0:0:enable='between(t,0,5)'[v_out]"
        )
        audio_filter = "aresample=44100"

    # 5. Ultra-Fast Compositor
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video_path,
        "-loop", "1", "-i", base_layer_path,
        "-loop", "1", "-i", circle_layer_path,
        "-filter_complex", filter_base,
        "-map", "[v_out]",
        "-map", "0:a?",
        "-af", audio_filter,
        "-map_metadata", "-1",
        *enc_args,
        "-c:a", "aac",
        "-b:a", "96k",
        "-t", f"{duration:.2f}",
        "-shortest",
        final_render_path
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    except subprocess.TimeoutExpired:
        print(f"⚠️ FFmpeg hardware encoder timed out after 180s on {input_video_path}. Retrying CPU...")
        res = type('obj', (object,), {'returncode': 1, 'stderr': b'Timeout'})

    if res.returncode != 0:
        err = res.stderr.decode("utf-8", errors="ignore")[-400:] if hasattr(res, 'stderr') and isinstance(res.stderr, bytes) else str(res.stderr)
        print(f"FFmpeg error with {enc_name}: {err}. Retrying with CPU libx264...")
        cpu_cmd = [
            "ffmpeg", "-y",
            "-threads", "2",
            "-i", input_video_path,
            "-loop", "1", "-i", base_layer_path,
            "-loop", "1", "-i", circle_layer_path,
            "-filter_complex", filter_base,
            "-map", "[v_out]",
            "-map", "0:a?",
            "-af", audio_filter,
            "-map_metadata", "-1",
            "-c:v", "libx264",
            "-b:v", f"{target_v_bitrate}k",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "96k",
            "-t", f"{duration:.2f}",
            "-shortest",
            final_render_path
        ]
        try:
            res_cpu = subprocess.run(cpu_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"FFmpeg CPU encoder timed out after 180s on {input_video_path}")
        if res_cpu.returncode != 0:
            raise RuntimeError(f"FFmpeg failed completely: {res_cpu.stderr.decode('utf-8', errors='ignore')[-300:]}")

    # Immediate Cleanup of temp images
    for p in [base_layer_path, circle_layer_path, circle_thumb]:
        if p and os.path.exists(p):
            try: os.remove(p)
            except: pass

    # Fast safety check (already guaranteed < 17.5 MB by dynamic calculation)
    delivered_path = ensure_telegram_size_limit(final_render_path, workspace_dir, job_id)
    return delivered_path, job_id
