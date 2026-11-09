import os
import math
import textwrap
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=True):
    """Cross-platform font loader with universal Hindi and Latin support."""
    font_candidates = [
        "C:/Windows/Fonts/Nirmala.ttc",
        "C:/Windows/Fonts/mangalb.ttf" if bold else "C:/Windows/Fonts/mangal.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    ]
    for font_path in font_candidates:
        try:
            if font_path.endswith(".ttc"):
                return ImageFont.truetype(font_path, size, index=1 if bold else 0)
            return ImageFont.truetype(font_path, size)
        except Exception:
            continue
    return ImageFont.load_default()

def wrap_text_to_width(text, font, max_width, draw):
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
    if current_line:
        lines.append(" ".join(current_line))
    return "\n".join(lines)

def create_base_layer(
    output_path,
    channel_config,
    hook_pill="Key Takeaway",
    main_title="Main Headline",
    sub_quote="Punchline Quote",
    width=1080,
    height=1920
):
    """
    Renders customizable 9:16 layout based on the channel's niche settings and colors.
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    content_settings = channel_config.get("content_settings", {})
    tag_text = content_settings.get("tag_text", "FEATURED:")
    primary_color = tuple(content_settings.get("theme_color_primary", [225, 29, 72, 255]))
    accent_color = tuple(content_settings.get("theme_color_accent", [255, 255, 255, 255]))

    font_logo = get_font(52, bold=True)
    font_tag = get_font(54, bold=True)
    font_pill = get_font(42, bold=True)
    font_title = get_font(54, bold=True)
    font_quote = get_font(34, bold=False)

    # 1. Top Right Channel Branding / Category (Right-aligned with 70px safe margin)
    display_title = channel_config.get("display_name", "Official").lower()[:18]
    logo_bbox = draw.textbbox((0, 0), display_title, font=font_logo)
    logo_w = logo_bbox[2] - logo_bbox[0]
    draw.text((max(width - 70 - logo_w, width - 400), 100), display_title, fill="white", font=font_logo)

    # 2. Smooth Gradient Top Fade (220px fade)
    bg_start_y = height - 900
    fade_height = 220
    for y in range(fade_height):
        alpha = int(255 * (y / fade_height))
        draw.line([(0, bg_start_y + y), (width, bg_start_y + y)], fill=(0, 0, 0, alpha))
    draw.rectangle([0, bg_start_y + fade_height, width, height], fill=(0, 0, 0, 255))

    # 3. Dynamic Tag Box (Safe Zone Left: 70px)
    tag_x = 70
    tag_y = bg_start_y + fade_height - 20
    bbox = draw.textbbox((tag_x, tag_y), tag_text, font=font_tag)

    # 3D accent block behind tag
    draw.rectangle([tag_x - 14, tag_y + 12, bbox[2] + 28, bbox[3] + 18], fill=primary_color)
    # White tag box
    draw.rectangle([tag_x - 18, tag_y - 8, bbox[2] + 18, bbox[3] + 8], fill="white")
    draw.text((tag_x, tag_y), tag_text, fill="black", font=font_tag)

    # 4. Color Pill Banner
    pill_y = tag_y + 96
    pill_bbox = draw.textbbox((tag_x, pill_y), hook_pill, font=font_pill)
    pill_width = min(pill_bbox[2] - pill_bbox[0] + 44, 780)
    pill_height = pill_bbox[3] - pill_bbox[1] + 22
    draw.rounded_rectangle(
        [tag_x - 12, pill_y - 8, tag_x - 12 + pill_width, pill_y - 8 + pill_height],
        radius=14,
        fill=primary_color
    )
    draw.text((tag_x + 10, pill_y - 2), hook_pill, fill="white", font=font_pill)

    # 5. Main Title (Auto-wrapped strictly to 770px)
    wrapped_title = wrap_text_to_width(main_title.replace("\n", " "), font_title, 770, draw)
    title_y = pill_y + pill_height + 26
    draw.multiline_text((tag_x, title_y), wrapped_title, fill="white", font=font_title, spacing=14)
    
    title_bbox = draw.multiline_textbbox((tag_x, title_y), wrapped_title, font=font_title, spacing=14)
    title_height = title_bbox[3] - title_bbox[1]

    # 6. Sub Quote (Auto-wrapped within 770px)
    clean_quote = sub_quote.strip()
    if not clean_quote.startswith('"'):
        clean_quote = f'"{clean_quote}"'
    wrapped_quote = wrap_text_to_width(clean_quote, font_quote, 770, draw)
    
    quote_y = title_y + title_height + 22
    draw.multiline_text((tag_x, quote_y), wrapped_quote, fill=(220, 220, 220, 255), font=font_quote, spacing=10)

    img.save(output_path, "PNG")
    return output_path

def create_circle_hook_layer(
    output_path,
    circle_img_path=None,
    border_color="white",
    width=1080,
    height=1920
):
    """
    Renders high-res circular zoom thumbnail with curved pointer arrow.
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    circle_center_x = 760
    circle_center_y = height - 900 + 40
    circle_radius = 175

    if circle_img_path and os.path.exists(circle_img_path):
        try:
            c_img = Image.open(circle_img_path).convert("RGBA")
        except:
            c_img = Image.new("RGBA", (circle_radius * 2, circle_radius * 2), (225, 29, 72, 255))
    else:
        c_img = Image.new("RGBA", (circle_radius * 2, circle_radius * 2), (225, 29, 72, 255))

    w, h = c_img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    c_img = c_img.crop((left, top, left + min_dim, top + min_dim))
    c_img = c_img.resize((circle_radius * 2, circle_radius * 2), Image.Resampling.LANCZOS)

    mask = Image.new("L", (circle_radius * 2, circle_radius * 2), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, circle_radius * 2, circle_radius * 2), fill=255)
    img.paste(c_img, (circle_center_x - circle_radius, circle_center_y - circle_radius), mask)

    # Border
    draw.ellipse(
        (circle_center_x - circle_radius, circle_center_y - circle_radius,
         circle_center_x + circle_radius, circle_center_y + circle_radius),
        outline=border_color,
        width=10
    )

    # Curved Arrow (Bezier)
    p0 = (380, height - 715)
    p1 = (430, height - 830)
    p2 = (565, circle_center_y + 60)

    curve_points = []
    for t in [i / 50.0 for i in range(51)]:
        bx = (1 - t)**2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
        by = (1 - t)**2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
        curve_points.append((bx, by))

    for i in range(len(curve_points) - 1):
        draw.line([curve_points[i], curve_points[i+1]], fill="white", width=9)

    dx = curve_points[-1][0] - curve_points[-5][0]
    dy = curve_points[-1][1] - curve_points[-5][1]
    angle = math.atan2(dy, dx)

    arrow_size = 32
    tip = curve_points[-1]
    left_wing = (
        tip[0] - arrow_size * math.cos(angle - math.pi / 6),
        tip[1] - arrow_size * math.sin(angle - math.pi / 6)
    )
    right_wing = (
        tip[0] - arrow_size * math.cos(angle + math.pi / 6),
        tip[1] - arrow_size * math.sin(angle + math.pi / 6)
    )

    draw.polygon([tip, left_wing, (tip[0] - arrow_size * 0.6 * math.cos(angle), tip[1] - arrow_size * 0.6 * math.sin(angle)), right_wing], fill="white")

    img.save(output_path, "PNG")
    return output_path
