from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

WHITE, BLUE, RED, BLACK = "#FFFFFF", "#0039A6", "#D52B1E", "#000000"

lines = [
    ("РОССИЯ", WHITE),
    ("ПУТИН",  BLUE),
    ("ПОБЕДА", RED),
]

W, H = 1920, 1080

canvas = Image.new("RGB", (W, H), BLACK)
draw = ImageDraw.Draw(canvas)

font = ImageFont.load_default()
for name in ("arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf",
             "LiberationSans-Bold.ttf", "Roboto-Bold.ttf"):
    try:
        font = ImageFont.truetype(name, 260)   # крупный под Full HD
        break
    except OSError:
        pass

line_height = H // len(lines)
for i, (text, color) in enumerate(lines):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (W - tw) // 2 - bbox[0]
    y = i * line_height + (line_height - th) // 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=color)

out = Path(__file__).parent / "wallpaper_1920x1080.png"
canvas.save(out)
print("Сохранено:", out.resolve())