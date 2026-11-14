#!/usr/bin/env python3
"""driftwood - an endless landscape drifting through your terminal.

space pause   +/- speed   t skip time   q quit
"""
import math, os, random, sys, time

WINDOWS = os.name == "nt"
if WINDOWS:
    import msvcrt
else:
    import select, termios, tty

# ---------- noise ----------
def hsh(n):
    n = (n * 374761393 + 668265263) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0

def vnoise(x, seed):
    i = math.floor(x); f = x - i
    f = f * f * (3 - 2 * f)
    a = hsh(i + seed * 7919); b = hsh(i + 1 + seed * 7919)
    return a + (b - a) * f

def fbm(x, seed, oct=3):
    v, amp, tot = 0.0, 1.0, 0.0
    for o in range(oct):
        v += vnoise(x, seed + o * 31) * amp
        tot += amp; x *= 2.03; amp *= 0.5
    return v / tot

# ---------- colour ----------
def mix(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)

def scale(c, s):
    return (c[0] * s, c[1] * s, c[2] * s)

def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)

# time of day keyframes: t, zenith, horizon, light
KEYS = [
    (0.00, (6, 8, 24),     (22, 26, 58),    0.16),
    (0.21, (12, 14, 40),   (40, 36, 80),    0.18),
    (0.25, (40, 50, 110),  (235, 130, 95),  0.45),
    (0.30, (70, 120, 200), (250, 190, 140), 0.85),
    (0.38, (60, 130, 215), (165, 205, 240), 1.00),
    (0.62, (60, 130, 215), (165, 205, 240), 1.00),
    (0.70, (70, 80, 160),  (250, 150, 90),  0.80),
    (0.75, (45, 40, 100),  (230, 100, 85),  0.45),
    (0.80, (14, 14, 42),   (60, 40, 85),    0.20),
    (1.00, (6, 8, 24),     (22, 26, 58),    0.16),
]

def sky_at(t):
    for k in range(len(KEYS) - 1):
        a, b = KEYS[k], KEYS[k + 1]
        if a[0] <= t <= b[0]:
            u = smooth(0, 1, (t - a[0]) / (b[0] - a[0]))
            return mix(a[1], b[1], u), mix(a[2], b[2], u), a[3] + (b[3] - a[3]) * u
    return KEYS[0][1], KEYS[0][2], KEYS[0][3]

LAYERS = [  # base colour, fog, parallax speed, base height, amplitude, noise freq
    ((120, 135, 175), 0.62, 0.04, 0.20, 0.34, 0.017),
    ((85, 105, 145),  0.45, 0.10, 0.14, 0.26, 0.027),
    ((55, 78, 105),   0.28, 0.22, 0.08, 0.19, 0.040),
    ((32, 52, 62),    0.14, 0.45, 0.04, 0.12, 0.060),
]
FRONT = (14, 20, 22)

# ---------- terminal ----------
class Term:
    def __enter__(self):
        if WINDOWS:
            os.system("")  # turn on ANSI colour escape codes in the Windows console
            sys.stdout.reconfigure(encoding="utf-8")
        else:
            self.fd = sys.stdin.fileno()
            self.old = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        sys.stdout.write("\x1b[?1049h\x1b[?25l\x1b[2J")
        return self
    def __exit__(self, *a):
        if not WINDOWS:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)
        sys.stdout.write("\x1b[0m\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()
    def keys(self):
        out = ""
        if WINDOWS:
            while msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("\x00", "\xe0"):  # arrow/function key prefix: skip the next code
                    msvcrt.getwch(); continue
                out += ch
            return out
        while select.select([sys.stdin], [], [], 0)[0]:
            ch = os.read(self.fd, 32).decode(errors="ignore")
            if not ch: break
            out += ch
        return out

# ---------- scene ----------
class World:
    def __init__(self):
        self.seed = random.randint(0, 9999)
        self.x = 0.0          # world scroll position
        self.tod = 0.27       # start at sunrise
        self.speed = 1.0
        self.paused = False
        self.meteors = []
        self.clock = 0.0

    def update(self, dt):
        if self.paused: return
        self.clock += dt
        self.x += 14.0 * dt * self.speed
        self.tod = (self.tod + dt * self.speed / 120.0) % 1.0
        night = 1 - smooth(0.15, 0.45, sky_at(self.tod)[2])
        if night > 0.6 and random.random() < dt * 0.25:
            self.meteors.append([random.random(), random.random() * 0.35, 0.0])
        for m in self.meteors: m[2] += dt * 1.6
        self.meteors = [m for m in self.meteors if m[2] < 1.0]

    def render(self, W, H):
        zen, hor, light = sky_at(self.tod)
        night = 1 - smooth(0.15, 0.45, light)
        wl = int(H * 0.76)                      # waterline
        rows = [[None] * W for _ in range(H)]

        # sky
        for y in range(wl):
            c = mix(zen, hor, (y / wl) ** 1.6)
            row = rows[y]
            for x in range(W): row[x] = c

        # sun & moon
        def body(phase, radius, col, glow):
            if not (0 <= phase <= 1): return
            cx = W * (0.08 + 0.84 * phase)
            cy = wl - math.sin(math.pi * phase) ** 0.6 * wl * 0.92
            r2g = (radius * 5) ** 2
            for y in range(max(0, int(cy - radius * 5)), min(wl, int(cy + radius * 5) + 1)):
                row = rows[y]
                for x in range(max(0, int(cx - radius * 5)), min(W, int(cx + radius * 5) + 1)):
                    d2 = (x - cx) ** 2 + ((y - cy) * 1.0) ** 2
                    if d2 <= radius * radius:
                        row[x] = col
                    elif d2 < r2g:
                        g = (1 - math.sqrt(d2) / (radius * 5)) ** 2 * glow
                        row[x] = mix(row[x], col, g)
        body((self.tod - 0.25) / 0.5, max(2.0, H * 0.035), (255, 232, 180), 0.55)
        body(((self.tod + 0.5) % 1.0 - 0.25) / 0.5, max(1.6, H * 0.028), (225, 230, 245), 0.25 * night)

        # stars
        if night > 0.02:
            sx = int(self.x * 0.02)
            for i in range(W * wl // 55):
                px = int(hsh(i * 3 + self.seed) * (W + 40)) - sx % (W + 40)
                px %= W
                py = int(hsh(i * 3 + 1 + self.seed) ** 1.4 * wl * 0.85)
                tw = 0.55 + 0.45 * math.sin(self.clock * (1 + hsh(i * 3 + 2) * 3) + i)
                b = night * tw * (0.4 + 0.6 * hsh(i * 7 + 5))
                if py < wl and rows[py][px] is not None:
                    rows[py][px] = mix(rows[py][px], (235, 235, 255), b)

        # meteors
        for mx, my, life in self.meteors:
            for k in range(10):
                px = int((mx + life * 0.3) * W) - k
                py = int((my + life * 0.18) * wl) - k // 2
                if 0 <= px < W and 0 <= py < wl:
                    rows[py][px] = mix(rows[py][px], (255, 255, 240), (1 - k / 10) * (1 - life) * night)

        # mountain layers
        for li, (base, fog, spd, bh, amp, freq) in enumerate(LAYERS):
            col = mix(scale(base, 0.25 + 0.75 * light), hor, fog * (0.5 + 0.5 * light))
            off = self.x * spd
            for x in range(W):
                n = fbm((x + off) * freq, self.seed + li * 101, 5)
                top = int(wl - (bh + amp * n ** 1.8 * 1.5) * H)
                for y in range(max(0, top), wl):
                    rows[y][x] = col
                # snowy caps on the far ridge
                if li == 0 and n > 0.62 and 0 <= top < wl:
                    rows[top][x] = mix(col, (240, 245, 255), 0.5 * light + 0.1)

        # front shoreline with pines
        fcol = mix(FRONT, hor, 0.06)
        off = self.x
        ground = wl - max(1, H // 40)
        for x in range(W):
            wx = x + off
            top = ground - fbm(wx * 0.08, self.seed + 900) * 2
            cell = math.floor(wx / 6)
            for c in (cell - 1, cell, cell + 1):
                if hsh(c * 13 + self.seed) > 0.45:
                    cx = c * 6 + 3 + hsh(c * 17) * 2
                    th = H * (0.10 + 0.14 * hsh(c * 29 + 3))
                    d = abs(wx - cx)
                    hw = th * 0.22
                    if d < hw:
                        # layered pine: sawtooth edge
                        prof = 1 - d / hw
                        t2 = ground - th * prof
                        t2 += (prof * th) % 3 * 0.6
                        top = min(top, t2)
                    if d < 0.7:
                        top = min(top, ground - th * 0.2)
            for y in range(max(0, int(top)), wl):
                rows[y][x] = fcol

        # water: reflection with ripples
        water = mix(zen, (10, 30, 45), 0.55)
        for y in range(wl, H):
            depth = (y - wl) / max(1, H - wl)
            src = wl - 1 - (y - wl)
            if src < 0: src = 0
            ripple = math.sin(y * 1.3 - self.clock * 2.2) * (0.6 + depth * 2.5)
            srow = rows[src]
            row = rows[y]
            k = 0.86 - depth * 0.35
            for x in range(W):
                sxp = int(x + ripple + math.sin(x * 0.15 + self.clock) * depth)
                if sxp < 0: sxp = 0
                elif sxp >= W: sxp = W - 1
                row[x] = mix(water, srow[sxp], k)
        return rows

def frame(rows, W, Hc):
    out = ["\x1b[H"]
    lf = lb = None
    for cy in range(Hc):
        top, bot = rows[cy * 2], rows[cy * 2 + 1]
        for x in range(W):
            a = top[x]; b = bot[x]
            f = (int(a[0]), int(a[1]), int(a[2]))
            g = (int(b[0]), int(b[1]), int(b[2]))
            if f != lf:
                out.append("\x1b[38;2;%d;%d;%dm" % f); lf = f
            if g != lb:
                out.append("\x1b[48;2;%d;%d;%dm" % g); lb = g
            out.append("▀")
        if cy < Hc - 1:
            out.append("\x1b[0m\r\n"); lf = lb = None
    return "".join(out)

def hud(world, W, Hc, show_help):
    s = "\x1b[0m"
    if world.paused:
        s += "\x1b[1;3H\x1b[38;2;249;226;175m paused \x1b[0m"
    if show_help:
        msg = " space pause   +/- speed   t skip time   q quit "
        s += "\x1b[%d;%dH\x1b[38;2;108;112;134m%s\x1b[0m" % (Hc, max(1, (W - len(msg)) // 2), msg)
    return s

def main():
    world = World()
    start = time.time()
    with Term() as term:
        last = time.time()
        while True:
            k = term.keys()
            if "q" in k or "\x1b" == k: break
            if " " in k: world.paused = not world.paused
            if "+" in k or "=" in k: world.speed = min(16, world.speed * 2)
            if "-" in k: world.speed = max(0.25, world.speed / 2)
            if "t" in k: world.tod = (world.tod + 0.125) % 1.0
            now = time.time(); dt = min(0.2, now - last); last = now
            world.update(dt)
            cols, lines = os.get_terminal_size()
            W, Hc = cols, lines
            rows = world.render(W, Hc * 2)
            sys.stdout.write(frame(rows, W, Hc) + hud(world, W, Hc, now - start < 8))
            sys.stdout.flush()
            spare = 1 / 24 - (time.time() - now)
            if spare > 0: time.sleep(spare)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
