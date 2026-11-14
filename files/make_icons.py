"""App icons for Driftwood (a tiny pixel landscape) and Tidepool (particle creatures)."""
import os, sys, math, random
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "driftwood"))
import driftwood as dw
OUT = os.path.join(HERE, "os"); os.makedirs(OUT, exist_ok=True)
S = 256

def rounded(img, r=56):
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1), r, fill=255)
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0)); out.paste(img, (0, 0), mask)
    return out

# Driftwood: the dusk scene rendered on a 32x32 grid, scaled up crisp
G = 32
img = Image.new("RGB", (G, G)); d = ImageDraw.Draw(img)
_mix = dw.mix
dw = type("dw", (), {"mix": staticmethod(lambda a, b, t: tuple(int(v) for v in _mix(a, b, t)))})
for y in range(20):                                    # dusk sky gradient
    d.line((0, y, G, y), fill=dw.mix((52, 48, 120), (242, 150, 110), (y / 19) ** 1.3))
d.ellipse((12, 10, 21, 19), fill=(255, 214, 150))     # setting sun, in the valley
d.polygon([(-3, 20), (7, 8), (17, 20)], fill=(92, 66, 104))            # left peak
d.polygon([(15, 20), (25, 9), (37, 20)], fill=(70, 52, 84))            # right peak
d.rectangle((0, 19, G, 20), fill=(22, 24, 30))                          # shoreline
for cx, h in [(3, 9), (7, 12), (11, 7), (27, 10), (30, 6)]:            # pines
    d.polygon([(cx - 2, 20), (cx, 20 - h), (cx + 2, 20)], fill=(18, 22, 26))
for y in range(21, G):                                 # lake reflecting the sky
    d.line((0, y, G, y), fill=dw.mix((40, 40, 80), (20, 22, 36), (y - 21) / 10))
for x0, y0, ln in [(16, 22, 9), (19, 24, 5), (4, 26, 6), (21, 27, 7), (9, 29, 5)]:
    d.line((x0, y0, x0 + ln, y0), fill=(242, 169, 122))  # sun glints on the water
rounded(img.resize((S, S), Image.NEAREST)).save(os.path.join(OUT, "driftwood.png"))

# Tidepool: dark pool with a few glowing rings of particles
random.seed(7)
img = Image.new("RGB", (S, S), (11, 13, 18)); d = ImageDraw.Draw(img)
pal = [(243, 139, 168), (166, 227, 161), (137, 180, 250), (249, 226, 175), (203, 166, 247), (148, 226, 213)]
for cx, cy, rad, col in [(92, 96, 44, 1), (170, 150, 52, 0), (88, 186, 26, 2), (186, 66, 22, 3)]:
    for k in range(int(rad * 0.9)):
        a = random.random() * math.tau; rr = rad * (0.75 + 0.25 * random.random())
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        d.rectangle((x - 3, y - 3, x + 3, y + 3), fill=pal[col])
    for k in range(int(rad * 0.4)):
        a = random.random() * math.tau; rr = rad * 0.35 * random.random()
        d.rectangle((cx + math.cos(a) * rr - 3, cy + math.sin(a) * rr - 3, cx + math.cos(a) * rr + 3, cy + math.sin(a) * rr + 3), fill=pal[(col + 2) % 6])
glow = img.filter(ImageFilter.GaussianBlur(6))
img = Image.blend(img, glow, 0.35)
rounded(img).save(os.path.join(OUT, "tidepool.png"))
print("icons written")
