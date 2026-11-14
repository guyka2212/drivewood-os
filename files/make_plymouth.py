"""Builds the 'driftwood' Plymouth theme: the logo's pixel blocks drift in from the
water and assemble themselves, then shimmer. No progress bar."""
import os, random
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "plymouth", "driftwood"); os.makedirs(OUT, exist_ok=True)

FONT = {
 "D": ["###.", "#..#", "#..#", "#..#", "#..#", "#..#", "###."],
 "R": ["###.", "#..#", "#..#", "###.", "#.#.", "#..#", "#..#"],
 "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
 "F": ["####", "#...", "#...", "###.", "#...", "#...", "#..."],
 "T": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", ".#."],
 "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
 "O": [".##.", "#..#", "#..#", "#..#", "#..#", "#..#", ".##."],
}
EMBLEM = ["......mm.", ".....mmm.", "......mm.", "...p.....", "..ppp..p.",
          ".ppppprpp", "rrrrprrrr", "rrrrrrrrr", "wwwwwwwww"]
COLORS = {"m": (244, 236, 221), "p": (159, 196, 138), "r": (127, 159, 217), "w": (242, 169, 122)}
CIDX = {"m": 0, "p": 1, "r": 2, "w": 3}

blocks = []  # (x, y, colour index)
for y, row in enumerate(EMBLEM):
    for x, ch in enumerate(row):
        if ch != ".": blocks.append((x, y, CIDX[ch]))
x0 = 12
for c in "DRIFTWOOD":
    g = FONT[c]
    for y in range(7):
        for x, ch in enumerate(g[y]):
            if ch == "#": blocks.append((x0 + x, y + 1, 3))
    x0 += len(g[0]) + 1
GW, GH = x0 - 1, 9

for name, idx in CIDX.items():
    Image.new("RGB", (32, 32), COLORS[name]).save(os.path.join(OUT, f"block{idx}.png"))

rnd = random.Random(42)
data = []
for i, (x, y, c) in enumerate(blocks):
    # start scattered below and to the sides, as if washing up out of the water
    ox = rnd.uniform(-22, 22)
    oy = rnd.uniform(6, 22) * (1 if rnd.random() < 0.8 else -0.6)
    delay = x / GW * 0.9 + rnd.uniform(0, 0.35)
    data.append(f"bx[{i}]={x}; by[{i}]={y}; bc[{i}]={c}; ox[{i}]={ox:.2f}; oy[{i}]={oy:.2f}; dl[{i}]={delay:.3f};")

script = f"""# Driftwood Plymouth theme: the logo assembles itself out of drifting blocks.
Window.SetBackgroundTopColor(0.078, 0.086, 0.122);
Window.SetBackgroundBottomColor(0.102, 0.110, 0.165);

global.N = {len(blocks)};
global.GW = {GW};
global.GH = {GH};
global.DUR = 1.1;
{chr(10).join(data)}

base[0] = Image("block0.png");
base[1] = Image("block1.png");
base[2] = Image("block2.png");
base[3] = Image("block3.png");
spr = [];
scaled = [];
global.layout_width = 0;
global.layout_height = 0;
global.frame = 0;

tag.image = Image.Text("drifting in", 0.49, 0.50, 0.56, 1, "Cantarell 13");
tag.sprite = Sprite(tag.image);
tag.sprite.SetOpacity(0);

pw.sprite = Sprite();
pw.sprite.SetOpacity(0);

fun layout() {{
  global.layout_width = Window.GetWidth();
  global.layout_height = Window.GetHeight();
  s = Math.Int(global.layout_width * 0.55 / global.GW);
  if (s < 4) s = 4;
  if (s > 24) s = 24;
  global.S = s;
  global.lx = Math.Int(global.layout_width / 2 - global.GW * s / 2);
  global.ly = Math.Int(global.layout_height / 2 - global.GH * s / 2);
  for (c = 0; c < 4; c++) scaled[c] = base[c].Scale(s, s);
  for (i = 0; i < global.N; i++) {{
    if (!spr[i]) spr[i] = Sprite();
    spr[i].SetImage(scaled[bc[i]]);
  }}
  tag.sprite.SetPosition(global.layout_width / 2 - tag.image.GetWidth() / 2, global.ly + global.GH * s + 3 * s, 10);
}}

fun refresh_callback() {{
  if (Window.GetWidth() != global.layout_width || Window.GetHeight() != global.layout_height) layout();
  global.frame++;
  t = global.frame / 50.0;
  s = global.S;
  for (i = 0; i < global.N; i++) {{
    p = (t - dl[i]) / global.DUR;
    if (p < 0) p = 0;
    if (p > 1) p = 1;
    q = 1 - p;
    e = 1 - q * q * q;
    tx = global.lx + bx[i] * s;
    ty = global.ly + by[i] * s;
    sx = tx + ox[i] * s;
    sy = ty + oy[i] * s;
    spr[i].SetPosition(sx + (tx - sx) * e, sy + (ty - sy) * e, 5);
    if (p >= 1) op = 0.84 + 0.16 * Math.Sin(t * 2.2 - bx[i] * 0.35);
    else {{
      op = p * 1.6;
      if (op > 1) op = 1;
    }}
    spr[i].SetOpacity(op);
  }}
  if (t > 2.4) {{
    a = (t - 2.4) / 0.8;
    if (a > 1) a = 1;
    tag.sprite.SetOpacity(a * (0.7 + 0.3 * Math.Sin(t * 1.5)));
  }}
}}
Plymouth.SetRefreshFunction(refresh_callback);

# Disk-unlock prompt, in case the disk is ever encrypted
fun display_password_callback(prompt, bullets) {{
  dots = "";
  for (i = 0; i < bullets && i < 24; i++) dots = dots + "*";
  pw.image = Image.Text(prompt + "  " + dots, 0.90, 0.86, 0.80, 1, "Cantarell 14");
  pw.sprite.SetImage(pw.image);
  pw.sprite.SetPosition(global.layout_width / 2 - pw.image.GetWidth() / 2, global.ly + global.GH * global.S + 6 * global.S, 20);
  pw.sprite.SetOpacity(1);
  tag.sprite.SetOpacity(0);
}}
fun display_normal_callback() {{
  pw.sprite.SetOpacity(0);
}}
Plymouth.SetDisplayPasswordFunction(display_password_callback);
Plymouth.SetDisplayNormalFunction(display_normal_callback);

message_sprite = Sprite();
message_sprite.SetPosition(10, 10, 10000);
fun display_message_callback(text) {{
  message_sprite.SetImage(Image.Text(text, 0.49, 0.50, 0.56));
  message_sprite.SetOpacity(1);
}}
fun hide_message_callback(text) {{
  message_sprite.SetOpacity(0);
}}
Plymouth.SetDisplayMessageFunction(display_message_callback);
Plymouth.SetHideMessageFunction(hide_message_callback);

layout();
"""
open(os.path.join(OUT, "driftwood.script"), "w", newline="\n").write(script)
open(os.path.join(OUT, "driftwood.plymouth"), "w", newline="\n").write("""[Plymouth Theme]
Name=Driftwood
Description=The Driftwood logo assembles itself out of drifting blocks.
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/driftwood
ScriptFile=/usr/share/plymouth/themes/driftwood/driftwood.script
ConsoleLogBackgroundColor=0x14161f
MonospaceFont=Cantarell 11
Font=Cantarell 11
""")

# preview: the same maths as the script, rendered at a few moments in time
import math
rnd = random.Random(42)
params = []
for (x, y, c) in blocks:
    ox = rnd.uniform(-22, 22); oy = rnd.uniform(6, 22) * (1 if rnd.random() < 0.8 else -0.6)
    params.append((x, y, c, ox, oy, x / GW * 0.9 + rnd.uniform(0, 0.35)))
S, W, H = 6, 640, 240
moments = (0.3, 0.8, 1.3, 1.8, 2.6)
strip = Image.new("RGB", (W, H * len(moments)), (20, 22, 31))
for k, t in enumerate(moments):
    lx, ly = W // 2 - GW * S // 2, H // 2 - GH * S // 2
    for x, y, c, ox, oy, dl in params:
        p = min(1, max(0, (t - dl) / 1.1)); e = 1 - (1 - p) ** 3
        tx, ty = lx + x * S, ly + y * S
        px, py = tx + ox * S + (tx - (tx + ox * S)) * e, ty + oy * S + (ty - (ty + oy * S)) * e
        op = 0.84 + 0.16 * math.sin(t * 2.2 - x * 0.35) if p >= 1 else min(1, p * 1.6)
        col = tuple(int(20 + (v - 20) * op) for v in list(COLORS.values())[c])
        for dx in range(S):
            for dy in range(S):
                X, Y = int(px) + dx, int(py) + dy + k * H
                if 0 <= X < W and k * H <= Y < (k + 1) * H: strip.putpixel((X, Y), col)
strip.save(os.path.join(HERE, "os", "splash-preview.png"))
print("blocks:", len(blocks), "grid", GW, "x", GH)
