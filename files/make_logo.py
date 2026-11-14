"""Driftwood wordmark (replaces the OMARCHY logo on the boot splash and lock screen)."""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
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
# emblem: moon over a pine-topped ridge, 9 wide x 9 tall
EMBLEM = [
 "......mm.",
 ".....mmm.",
 "......mm.",
 "...p.....",
 "..ppp..p.",
 ".ppppprpp",
 "rrrrprrrr",
 "rrrrrrrrr",
 "wwwwwwwww",
]
COL = {"m": (244, 236, 221), "p": (159, 196, 138), "r": (127, 159, 217), "w": (242, 169, 122)}
PEACH = (242, 169, 122)

word = "DRIVEWOOD"
gw = sum(len(FONT[c][0]) for c in word) + (len(word) - 1)
GW, GH = 9 + 3 + gw, 9
grid = Image.new("RGBA", (GW, GH), (0, 0, 0, 0)); px = grid.load()
for y, row in enumerate(EMBLEM):
    for x, ch in enumerate(row):
        if ch != ".": px[x, y] = COL[ch] + (255,)
x0 = 12
for c in word:
    g = FONT[c]
    for y in range(7):
        for x, ch in enumerate(g[y]):
            if ch == "#": px[x0 + x, y + 1] = PEACH + (255,)
    x0 += len(g[0]) + 1

scale = min(760 // GW, 188 // GH)
big = grid.resize((GW * scale, GH * scale), Image.NEAREST)
out = Image.new("RGBA", (800, 188), (0, 0, 0, 0))
out.paste(big, ((800 - big.width) // 2, (188 - big.height) // 2))
out.save(os.path.join(HERE, "driftwood", "unlock.png"))
prev = Image.new("RGB", (800, 188), (20, 22, 31)); prev.paste(out, (0, 0), out)
prev.save(os.path.join(HERE, "os", "logo-preview.png"))
print("logo", out.size, "scale", scale)
