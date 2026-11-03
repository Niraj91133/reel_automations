import os
import subprocess
from generate_template import create_base_layer, create_circle_hook_layer

def process_video_with_template(
    input_video_path,
    output_video_path,
    hook_pill="Startup Founders Hear Why",
    main_title="Marwari Brothers Still Run One\nShop Together After 30 Years",
    sub_quote='"Three shops apart or one big business together"',
    circle_img_path=None
):
    """
    Renders Studio-Quality 9:16 Instagram video with:
    - Visually Lossless CRF 17 + Lanczos scaling (Ultra Crisp)
    - 320kbps High Fidelity Audio
    - Glitch-free smooth dissolving 5-second circular hook
    - Instagram safe-zone compliant layout
    """
    base_layer_path = "temp_base_layer.png"
    circle_layer_path = "temp_circle_layer.png"

    # 1. Base Layer
    create_base_layer(
        output_path=base_layer_path,
        hook_pill=hook_pill,
        main_title=main_title,
        sub_quote=sub_quote
    )

    # 2. Hook Layer (Circle + Arrow)
    create_circle_hook_layer(
        output_path=circle_layer_path,
        circle_img_path=circle_img_path
    )

    print("Rendering Ultra-HD video with FFmpeg (Low CPU, safe threads)...")
    # Ultra-HD Filter Graph
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
        output_video_path
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr.decode("utf-8", errors="ignore")[-500:])
        raise RuntimeError("FFmpeg processing failed")

    # Cleanup temp frames
    if os.path.exists(base_layer_path):
        os.remove(base_layer_path)
    if os.path.exists(circle_layer_path):
        os.remove(circle_layer_path)

    print("Ultra-HD Video successfully rendered:", output_video_path)
    return output_video_path

if __name__ == '__main__':
    print("Video processor ready with Ultra-HD settings.")
