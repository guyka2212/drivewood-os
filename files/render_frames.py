"""Replay the recorded screensaver (ttfx matrix) output and render each frame to PNG
for the Plymouth boot screen."""
import os, re, sys
from PIL import Image, ImageDraw, ImageFont

RAW = sys.argv[1]
OUT = sys.argv[2]
COLS, ROWS = 110, 18
CW, CH = 10, 20                      # cell size in pixels -> 1100 x 360 frames
STEP = int(sys.argv[3]) if len(sys.argv) > 3 else 2   # keep every Nth frame

os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    if f.endswith(".png"): os.remove(os.path.join(OUT, f))

font = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 20)
raw = open(RAW, "rb").read().decode("utf-8", "replace")
frames = re.split(r"\x1b\[\d+A", raw)
token = re.compile(r"\x1b\[([0-9;]*)m|\x1b\[\?\d+[hl]|\x1b[78]|(\n)|(.)", re.S)

def parse(chunk):
    grid = [[None] * COLS for _ in range(ROWS)]
    r = c = 0
    color = None
    for m in token.finditer(chunk):
        sgr, nl, ch = m.group(1), m.group(2), m.group(3)
        if sgr is not None:
            parts = sgr.split(";")
            if len(parts) >= 5 and parts[0] == "38" and parts[1] == "2":
                color = tuple(int(p) for p in parts[2:5])
            elif sgr in ("0", ""):
                color = None
        elif nl:
            r += 1; c = 0
        elif ch is not None:
            if r < ROWS and c < COLS and ch != " ":
                grid[r][c] = (ch, color or (230, 220, 203))
            c += 1
    return grid

grids = [parse(f) for f in frames if f.strip()]
blocks = [sum(1 for row in g for cell in row if cell and cell[0] == "█") for g in grids]
others = [sum(1 for row in g for cell in row if cell and cell[0] != "█") for g in grids]
full = max(blocks)
formed = next(i for i, b in enumerate(blocks) if b == full and others[i] == 0) if full else len(grids) - 1
print(f"frames={len(grids)} banner_blocks={full} fully_formed_at={formed}")

# keep everything up to a short hold after the word has formed and finished its colour sweep
settle = formed
while settle + 1 < len(grids) and grids[settle + 1] != grids[settle]:
    settle += 1
end = min(len(grids), settle + 15)
print(f"colour settles at {settle}, keeping 0..{end - 1}")

n = 0
for i in range(0, end, STEP):
    img = Image.new("RGB", (COLS * CW, ROWS * CH), (0, 0, 0))
    d = ImageDraw.Draw(img)
    for r, row in enumerate(grids[i]):
        for c, cell in enumerate(row):
            if not cell: continue
            ch, col = cell
            x, y = c * CW, r * CH
            if ch == "█":
                d.rectangle((x, y, x + CW - 1, y + CH - 1), fill=col)
            else:
                d.text((x, y), ch, font=font, fill=col)
    img.quantize(colors=128, dither=Image.Dither.NONE).save(os.path.join(OUT, f"f{n:03d}.png"), optimize=True)
    n += 1
print("written", n, "frames")
