import os
import textwrap
import math
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=True):
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

def create_politics_base_layer(
    output_path="politics_base_layer.png",
    width=1080,
    height=1920,
    hook_pill="Bharat Ki Awaz",
    main_title="Badi Khabar: Sansad Me\nNetaon Ke Beech Zabardast Behas",
    sub_quote='"Desh ki janta sab dekh rahi hai aur faisla karegi"'
):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_logo = get_font(56, bold=True)
    font_tag = get_font(56, bold=True)
    font_pill = get_font(44, bold=True)
    font_title = get_font(56, bold=True)
    font_quote = get_font(36, bold=False)

    # 1. Top Right Logo: 'India' (As requested)
    draw.text((width - 240, 100), "India", fill="white", font=font_logo)

    # 2. Smooth Gradient Top Fade (220px fade)
    bg_start_y = height - 900
    fade_height = 220
    for y in range(fade_height):
        alpha = int(255 * (y / fade_height))
        draw.line([(0, bg_start_y + y), (width, bg_start_y + y)], fill=(0, 0, 0, alpha))
    draw.rectangle([0, bg_start_y + fade_height, width, height], fill=(0, 0, 0, 255))

    # BHAGWA / SAFFRON COLOR: #FF671F / RGB(255, 103, 31)
    BHAGWA = (255, 103, 31, 255)

    # 3. POLITICS Box (Safe Zone Left: 70px)
    tag_x = 70
    tag_y = bg_start_y + fade_height - 20
    tag_text = "POLITICS:"
    bbox = draw.textbbox((tag_x, tag_y), tag_text, font=font_tag)

    # 3D Bhagwa accent block
    draw.rectangle([tag_x - 14, tag_y + 12, bbox[2] + 28, bbox[3] + 18], fill=BHAGWA)
    # White tag box
    draw.rectangle([tag_x - 18, tag_y - 8, bbox[2] + 18, bbox[3] + 8], fill="white")
    draw.text((tag_x, tag_y), tag_text, fill="black", font=font_tag)

    # 4. Bhagwa (Orange) Pill Banner
    pill_y = tag_y + 96
    pill_bbox = draw.textbbox((tag_x, pill_y), hook_pill, font=font_pill)
    pill_width = min(pill_bbox[2] - pill_bbox[0] + 44, 780)
    pill_height = pill_bbox[3] - pill_bbox[1] + 22
    draw.rounded_rectangle(
        [tag_x - 12, pill_y - 8, tag_x - 12 + pill_width, pill_y - 8 + pill_height],
        radius=14,
        fill=BHAGWA
    )
    draw.text((tag_x + 10, pill_y - 2), hook_pill, fill="white", font=font_pill)

    # 5. Main Title (Auto-wrapped strictly to 770px safe zone)
    wrapped_title = wrap_text_to_width(main_title.replace("\n", " "), font_title, 770, draw)
    title_y = pill_y + pill_height + 26
    draw.multiline_text((tag_x, title_y), wrapped_title, fill="white", font=font_title, spacing=14)
    
    title_bbox = draw.multiline_textbbox((tag_x, title_y), wrapped_title, font=font_title, spacing=14)
    title_height = title_bbox[3] - title_bbox[1]

    # 6. Sub Quote (Auto-wrapped within 770px safe zone)
    clean_quote = sub_quote.strip()
    if not clean_quote.startswith('"'):
        clean_quote = f'"{clean_quote}"'
    wrapped_quote = wrap_text_to_width(clean_quote, font_quote, 770, draw)
    
    quote_y = title_y + title_height + 22
    draw.multiline_text((tag_x, quote_y), wrapped_quote, fill=(225, 225, 225, 255), font=font_quote, spacing=10)

    img.save(output_path, "PNG")
    print("Politics base layer generated:", output_path)

def create_politics_circle_layer(
    output_path="politics_circle_layer.png",
    width=1080,
    height=1920,
    circle_img_path=None
):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    circle_center_x = 760
    circle_center_y = height - 900 + 40
    circle_radius = 175

    if circle_img_path and os.path.exists(circle_img_path):
        c_img = Image.open(circle_img_path).convert("RGBA")
    else:
        c_img = Image.new("RGBA", (circle_radius * 2, circle_radius * 2), (255, 103, 31, 255))

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

    # 10px White Border
    draw.ellipse(
        (circle_center_x - circle_radius, circle_center_y - circle_radius,
         circle_center_x + circle_radius, circle_center_y + circle_radius),
        outline="white",
        width=10
    )

    # Curved Bezier Arrow pointing to circle
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
    print("Politics circle layer generated:", output_path)

if __name__ == '__main__':
    create_politics_base_layer()
    create_politics_circle_layer()
