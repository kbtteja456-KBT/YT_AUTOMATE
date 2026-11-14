from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

thumb_path = Path("media_storage/thumbnails/educational_ep3.jpg")
thumb_path.parent.mkdir(parents=True, exist_ok=True)

img = Image.new("RGB", (1080, 1920), (10, 12, 16))
draw = ImageDraw.Draw(img)

# Blueprint grid
for y in range(0, 1920, 80):
    draw.line([(0, y), (1080, y)], fill=(18, 24, 34), width=1)
for x in range(0, 1080, 80):
    draw.line([(x, 0), (x, 1920)], fill=(18, 24, 34), width=1)

# Badge
draw.rounded_rectangle([100, 200, 980, 360], radius=30, fill=(255, 215, 0))
try:
    font_badge = ImageFont.truetype("arialbd.ttf", 64)
    font_title = ImageFont.truetype("arialbd.ttf", 84)
    font_sub = ImageFont.truetype("arialbd.ttf", 52)
except Exception:
    font_badge = font_title = font_sub = ImageFont.load_default()

draw.text((540, 280), "EPISODE 3: USER INPUT", fill=(10, 12, 16), font=font_badge, anchor="mm")
draw.text((540, 520), "input() vs int()", fill=(56, 189, 248), font=font_title, anchor="mm")
draw.text((540, 660), "Why Code Fails Without Casting!", fill=(255, 255, 255), font=font_sub, anchor="mm")

# Code box preview
draw.rounded_rectangle([100, 820, 980, 1400], radius=24, fill=(18, 22, 30), outline=(56, 189, 248), width=4)
draw.text((140, 900), "age = input('Age: ')   # '20'", fill=(250, 204, 21), font=font_sub)
draw.text((140, 1020), "# CRASH: '20' + 1 ❌", fill=(239, 68, 68), font=font_sub)
draw.text((140, 1140), "age = int(age)        # 20", fill=(34, 197, 94), font=font_sub)
draw.text((140, 1260), "print(age + 1) -> 21  ✅", fill=(56, 189, 248), font=font_sub)

# Bottom Callout
draw.rounded_rectangle([100, 1560, 980, 1720], radius=30, fill=(34, 197, 94))
draw.text((540, 1640), "MASTER PYTHON IN 50s! ⚡", fill=(10, 12, 16), font=font_badge, anchor="mm")

img.save(thumb_path, "JPEG", quality=95)
print("SUCCESS: Created thumbnail:", thumb_path, "Size:", thumb_path.stat().st_size)

