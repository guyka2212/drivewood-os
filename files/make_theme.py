"""Builds the Driftwood Omarchy theme: wallpapers (rendered with the driftwood engine),
preview images and branding ASCII art."""
import os, sys, math
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "driftwood"))
import driftwood as dw

OUT = os.path.join(HERE, "driftwood")
os.makedirs(os.path.join(OUT, "backgrounds"), exist_ok=True)

GW, GH, SCALE = 320, 200, 8          # pixel grid -> 2560x1600

def render(tod, x, seed, clock=3.0, meteors=()):
    w = dw.World()
    w.seed, w.x, w.tod, w.clock = seed, x, tod, clock
    w.meteors = [list(m) for m in meteors]
    rows = w.render(GW, GH)
    img = Image.new("RGB", (GW, GH))
    img.putdata([(int(c[0]), int(c[1]), int(c[2])) for row in rows for c in row])
    return img.resize((GW * SCALE, GH * SCALE), Image.NEAREST)

SEED, X = 4242, 1830.0
scenes = [
    ("1-dawn.png",  0.272, ()),
    ("2-noon.png",  0.50,  ()),
    ("3-dusk.png",  0.735, ()),
    ("4-night.png", 0.02,  [(0.18, 0.08, 0.35), (0.62, 0.20, 0.55)]),
]
imgs = {}
for name, tod, met in scenes:
    img = render(tod, X, SEED, meteors=met)
    img.save(os.path.join(OUT, "backgrounds", name), optimize=True)
    imgs[name] = img
    print("wrote", name)

imgs["3-dusk.png"].resize((1280, 800), Image.NEAREST).save(os.path.join(OUT, "preview.png"))
imgs["4-night.png"].save(os.path.join(OUT, "unlock.png"), optimize=True)
imgs["4-night.png"].resize((1280, 800), Image.NEAREST).save(os.path.join(OUT, "preview-unlock.png"))

# ---------- branding: block-letter DRIFTWOOD for the screensaver ----------
FONT = {
 "D": ["###.", "#..#", "#..#", "#..#", "#..#", "#..#", "###."],
 "R": ["###.", "#..#", "#..#", "###.", "#.#.", "#..#", "#..#"],
 "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
 "F": ["####", "#...", "#...", "###.", "#...", "#...", "#..."],
 "T": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", ".#."],
 "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
 "V": ["#...#", "#...#", "#...#", "#...#", ".#.#.", ".#.#.", "..#.."],
 "E": ["###", "#..", "#..", "##.", "#..", "#..", "###"],
 "O": [".##.", "#..#", "#..#", "#..#", "#..#", "#..#", ".##."],
}
def banner(word):
    lines = []
    for r in range(7):
        lines.append("  ".join("".join("██" if ch == "#" else "  " for ch in FONT[c][r]) for c in word).rstrip())
    return "\n".join(lines) + "\n"
open(os.path.join(HERE, "screensaver.txt"), "w", encoding="utf-8").write(banner("DRIVEWOOD"))

# ---------- branding: little mountain lake logo for about / fastfetch ----------
LW, LH = 54, 26                       # 54 cols x 13 text rows (half blocks)
m = Image.new("1", (LW, LH), 0)
d = ImageDraw.Draw(m)
d.ellipse((38, 2, 44, 8), fill=1)                                   # moon
d.polygon([(0, 17), (10, 7), (16, 11), (24, 4), (34, 13), (40, 9), (53, 17)], fill=1)  # ridge
for cx, h in [(4, 8), (9, 11), (14, 7), (40, 10), (45, 7), (49, 12)]:  # pines
    d.polygon([(cx - 3, 18), (cx, 18 - h), (cx + 3, 18)], fill=1)
d.rectangle((0, 18, LW - 1, 18), fill=1)                            # shore
for y in range(20, LH, 2):                                          # ripples
    off = (y * 7) % 11
    for x in range(off, LW, 11):
        d.line((x, y, x + 5, y), fill=1)
px = m.load()
out = []
for r in range(LH // 2):
    s = ""
    for x in range(LW):
        a, b = px[x, r * 2], px[x, r * 2 + 1]
        s += "█" if a and b else "▀" if a else "▄" if b else " "
    out.append(s.rstrip())
open(os.path.join(HERE, "about.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print(banner("DRIVEWOOD")); print("\n".join(out))
