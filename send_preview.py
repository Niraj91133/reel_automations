from generate_template import create_base_layer, create_circle_hook_layer
from PIL import Image
import requests

create_base_layer(
    output_path="temp_b.png",
    hook_pill="Stop Working Harder",
    main_title="How Smart Founders\nScale Output 10x Faster",
    sub_quote='"Leverage is not about working more hours, it is about building smarter systems that run themselves."'
)
create_circle_hook_layer(output_path="temp_c.png")

# Combine
b = Image.open("temp_b.png")
c = Image.open("temp_c.png")
b.paste(c, (0, 0), c)
b.save("preview_arrow_subtitle.png")

# Send to Telegram
token = "8149202459:AAGRZBE4uZY7UXUV4HySazIuc-M5V2hHK8A"
chat_id = "711598335"
url = f"https://api.telegram.org/bot{token}/sendPhoto"
with open("preview_arrow_subtitle.png", "rb") as f:
    r = requests.post(
        url,
        data={"chat_id": chat_id, "caption": "🎨 CHECK NEW ARROW & SUBTITLE:\n1. Subtitle strictly wrapped in 2 lines inside Instagram Safe Zone\n2. Authentic Curved Pointer Arrow with sharp arrowhead"},
        files={"photo": f}
    )
print("Telegram preview sent:", r.status_code)
