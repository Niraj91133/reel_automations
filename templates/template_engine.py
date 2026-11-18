import os
import math
import textwrap
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=True):
    """Cross-platform font loader."""
    font_candidates = [
        "arialbd.ttf" if bold else "arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    ]
    for font_path in font_candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            continue
    return ImageFont.load_default()

def wrap_title_strictly_max_2_lines(text, base_font_size, max_width, draw, bold=True):
    """
    Guarantees title NEVER exceeds 2 lines on the video overlay.
    Dynamically adapts font size if needed and strictly limits to max 2 lines.
    """
    clean_text = ' '.join(text.replace('\n', ' ').split())
    words = clean_text.split()
    for f_size in [base_font_size, base_font_size - 4, base_font_size - 8]:
        font = get_font(f_size, bold=bold)
        lines = []
        current = []
        for w in words:
            test_line = ' '.join(current + [w])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current.append(w)
            else:
                if current:
                    lines.append(' '.join(current))
                    current = [w]
                else:
                    lines.append(w)
                    current = []
        if current:
            lines.append(' '.join(current))
        if len(lines) <= 2:
            return '\n'.join(lines), font
            
    font = get_font(base_font_size - 8, bold=bold)
    line1_words = []
    idx = 0
    while idx < len(words):
        test_l1 = ' '.join(line1_words + [words[idx]])
        bbox = draw.textbbox((0, 0), test_l1, font=font)
        if bbox[2] - bbox[0] <= max_width:
            line1_words.append(words[idx])
            idx += 1
        else:
            break
            
    line2_words = []
    while idx < len(words):
        test_l2 = ' '.join(line2_words + [words[idx]])
        bbox = draw.textbbox((0, 0), test_l2, font=font)
        if bbox[2] - bbox[0] <= max_width:
            line2_words.append(words[idx])
            idx += 1
        else:
            break
            
    res = [l for l in [' '.join(line1_words), ' '.join(line2_words)] if l]
    return '\n'.join(res[:2]), font

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

    # 🛡️ UNBREAKABLE MULTI-CHANNEL BRAND INTEGRITY SHIELD:
    # Guarantees authentic colors, tag_text, and logos across all channels
    ch_id = channel_config.get("channel_id", "").lower()
    from core.brand_security_guard import get_guaranteed_brand_settings
    brand_guard = get_guaranteed_brand_settings(ch_id)
    tag_text = brand_guard.get("tag_text", "FEATURED:")
    primary_color = brand_guard.get("primary_color", (225, 29, 72, 255))
    accent_color = brand_guard.get("accent_color", (255, 255, 255, 255))
    display_title = brand_guard.get("top_logo", "official")

    font_logo = get_font(52, bold=True)
    font_tag = get_font(54, bold=True)
    font_pill = get_font(42, bold=True)
    font_title = get_font(54, bold=True)
    font_quote = get_font(34, bold=False)

    # 1. Top Right Channel Branding / Category (Right-aligned with 70px right margin)
    logo_bbox = draw.textbbox((0, 0), display_title, font=font_logo)
    logo_w = logo_bbox[2] - logo_bbox[0]
    draw.text((width - logo_w - 70, 100), display_title, fill="white", font=font_logo)

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

    # 5. Main Title (STRICTLY MAXIMUM 2 LINES - NEVER EXCEEDS 2 LINES)
    wrapped_title, title_font = wrap_title_strictly_max_2_lines(main_title, 54, 770, draw, bold=True)
    title_y = pill_y + pill_height + 26
    draw.multiline_text((tag_x, title_y), wrapped_title, fill="white", font=title_font, spacing=14)
    
    title_bbox = draw.multiline_textbbox((tag_x, title_y), wrapped_title, font=title_font, spacing=14)
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
