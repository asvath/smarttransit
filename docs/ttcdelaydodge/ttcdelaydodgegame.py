import math, random, sys, os, array, json, asyncio

import pygame

import json as _json
try:
    import urllib.request as _url
except Exception:
    _url = None

# ---------- Platform detection (desktop vs web) ----------
WEB = sys.platform in ("wasi", "emscripten")
if WEB:
    from platform import window
    import js

# ---------- Global leaderboard API ----------
GLOBAL_API_URL = "https://leaderboard-api.ashaasvathaman.workers.dev"

WIDTH, HEIGHT = 960, 600
FPS = 60

COL_BG_TOP = (10, 12, 18)
COL_BG_BOTTOM = (15, 17, 26)
COL_TEXT = (230, 235, 255)
COL_TEXT_DIM = (170, 178, 210)
COL_ACCENT = (255, 211, 29)
COL_RED = (200, 40, 50)

COL_BALLAST = (40, 43, 55)
COL_TIE = (78, 70, 60)
COL_TIE_SH = (58, 52, 45)
COL_RAIL_TOP = (210, 215, 230)
COL_RAIL_SIDE = (120, 130, 160)

TRAIN_SPEED_Y = 9.8
TRAIN_SMOOTHING = 0.22

OBSTACLE_SPAWN_EASY = (800, 1200)
OBSTACLE_SPEED = (5.8, 9.2)
BOOST_SPAWN_EVERY = (3000, 4600)
BOOST_SPEED = (5.4, 7.6)

ANNOUNCEMENT_EVERY = (4500, 8000)

HIGHSCORE_FILE = "delay_dodge_highscore.txt"
LEADERBOARD_FILE = "delay_dodge_leaderboard.csv"

TRACK_Y = int(HEIGHT * 0.60)
TRACK_BAND = 240
TRACK_TOP = TRACK_Y - TRACK_BAND // 2
TRACK_BOTTOM = TRACK_Y + TRACK_BAND // 2
RAIL_SPREAD = 120
TIE_GAP_BASE = 88

DELAY_MINUTES = {
    "Signal": 6,
    "Cone": 5,
    "Disorderly": 8,
    "Fire": 12,
    "Raccoon": 16,
}

PRESTO_INVULN_MS = 2000

HIGHSCORE_KEY = "delay_dodge_highscore"
LEADERBOARD_KEY = "delay_dodge_leaderboard"  # local web fallback

# --- Highscore name ---
HIGHSCORE_NAME_FILE = "delay_dodge_highscore_name.txt"
HIGHSCORE_NAME_KEY = "delay_dodge_highscore_name"


def load_highscore_name():
    try:
        if WEB:
            val = window.localStorage.getItem(HIGHSCORE_NAME_KEY)
            return val or ""
        else:
            if os.path.exists(HIGHSCORE_NAME_FILE):
                with open(HIGHSCORE_NAME_FILE, "r", encoding="utf-8") as f:
                    return f.read().strip()
    except Exception:
        pass
    return ""


def save_highscore_name(name):
    try:
        name = (name or "Player").strip() or "Player"
        if WEB:
            window.localStorage.setItem(HIGHSCORE_NAME_KEY, name)
        else:
            with open(HIGHSCORE_NAME_FILE, "w", encoding="utf-8") as f:
                f.write(name)
    except Exception:
        pass


def lerp(a, b, t): return a + (b - a) * t
def clamp(v, lo, hi): return max(lo, min(hi, v))


def draw_vertical_gradient(surf, top_color, bottom_color):
    h = surf.get_height()
    for y in range(h):
        t = y / (h - 1)
        col = (int(lerp(top_color[0], bottom_color[0], t)),
               int(lerp(top_color[1], bottom_color[1], t)),
               int(lerp(top_color[2], bottom_color[2], t)))
        pygame.draw.line(surf, col, (0, y), (surf.get_width(), y))


def draw_rounded_rect(surf, rect, color, radius=8):
    pygame.draw.rect(surf, color, rect, border_radius=radius)


# ---------- Highscore: web localStorage or desktop file ----------
def load_highscore():
    try:
        if WEB:
            val = window.localStorage.getItem(HIGHSCORE_KEY)
            return int(val) if val else 0
        else:
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
                    return int(float(f.read().strip()))
    except Exception:
        pass
    return 0


def save_highscore(score):
    try:
        score = int(score)
        if WEB:
            window.localStorage.setItem(HIGHSCORE_KEY, str(score))
        else:
            with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
                f.write(str(score))
    except Exception:
        pass


# ---------- Leaderboard (global via API if configured, else local fallback) ----------
def _js_obj(py_dict):
    """Convert a Python dict into a real JavaScript object."""
    return window.JSON.parse(_json.dumps(py_dict))


async def _api_get_top():
    """Return top leaderboard entries (safe for both desktop & web)."""
    url = f"{GLOBAL_API_URL}/leaderboard"
    try:
        if WEB:
            opts = to_js({"method": "GET", "mode": "cors", "cache": "no-store"})
            resp = await js.fetch(url, opts)
            if not resp.ok:
                txt = await resp.text()
                js.console.error("Leaderboard GET failed:", resp.status, txt)
                return None

            data = await resp.json()
        else:
            with _url.urlopen(url, timeout=5) as r:
                data = json.loads(r.read().decode("utf-8"))

        top = sorted(
            [(d.get("name", "Player"), int(d.get("score", 0))) for d in data],
            key=lambda x: x[1],
            reverse=True,
        )
        return top[:20]

    except Exception as e:
        if WEB:
            js.console.error("Leaderboard GET exception:", str(e))
        else:
            print("Leaderboard GET exception:", e)
        return None


async def _api_post_score(name, score):
    """Submit a score to the global leaderboard."""
    url = f"{GLOBAL_API_URL}/leaderboard"
    payload = {"name": (name or "Player").strip() or "Player", "score": int(score)}
    try:
        if WEB:
            js.window.tempPostBody = json.dumps(payload)
            fetch_code = """
            (function() {
                return {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: window.tempPostBody
                };
            })()
            """
            opts = js.eval(fetch_code)
            resp = await js.fetch(url, opts)
            del js.window.tempPostBody
            return bool(resp and resp.ok)
        else:
            data = json.dumps(payload).encode("utf-8")
            req = _url.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with _url.urlopen(req, timeout=5) as r:
                return 200 <= r.status < 300
    except Exception as e:
        if WEB:
            js.console.error("POST score exception:", str(e))
        else:
            print("POST score exception:", e)
        return False


# --- Minimal desktop fallback for local leaderboard (CSV file) ---
def _read_leaderboard_desktop():
    rows = []
    try:
        if os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    # name,score
                    if "," in line:
                        name, score_s = line.split(",", 1)
                        try:
                            rows.append((name, int(float(score_s))))
                        except Exception:
                            pass
    except Exception:
        pass
    return rows


def _write_leaderboard_desktop(rows):
    # rows: list[(name, score)]
    try:
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            for name, score in rows:
                f.write(f"{name},{int(score)}\n")
    except Exception:
        pass


def append_leaderboard_local(name, score):
    name = (name or "Player").strip() or "Player"
    score = int(score)
    if WEB:
        try:
            raw = window.localStorage.getItem(LEADERBOARD_KEY)
            data = json.loads(raw) if raw else []
            data.append({"name": name, "score": score})
            data = sorted(data, key=lambda x: x["score"], reverse=True)[:20]
            window.localStorage.setItem(LEADERBOARD_KEY, json.dumps(data))
        except Exception:
            pass
    else:
        rows = _read_leaderboard_desktop()
        rows.append((name, score))
        rows = sorted(rows, key=lambda x: x[1], reverse=True)[:20]
        _write_leaderboard_desktop(rows)


def read_leaderboard_top_local(n=5):
    if WEB:
        try:
            raw = window.localStorage.getItem(LEADERBOARD_KEY)
            data = json.loads(raw) if raw else []
            data = sorted(data, key=lambda x: x["score"], reverse=True)
            return [(d["name"], int(d["score"])) for d in data[:n]]
        except Exception:
            return []
    else:
        rows = _read_leaderboard_desktop()
        rows.sort(key=lambda x: x[1], reverse=True)
        return rows[:n]


def generate_tone(frequency=440, duration_ms=120, volume=0.5, sample_rate=22050):
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = array.array("h")
    amp = int(32767 * volume)
    for i in range(n_samples):
        t = i / sample_rate
        decay = max(0.0, 1.0 - i / n_samples)
        val = int(amp * math.sin(2 * math.pi * frequency * t) * (0.6 + 0.4 * decay))
        buf.append(val)
    return pygame.mixer.Sound(buffer=buf.tobytes())


def init_sounds():
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=256)
    except Exception as e:
        print(f"Audio unavailable: {e}")
        return None
    try:
        sounds = {
            "hit": generate_tone(180, 160, 0.6),
            "boost": generate_tone(880, 120, 0.5),
            "menu": generate_tone(600, 80, 0.4),
            "start": generate_tone(520, 130, 0.5),
            "station": generate_tone(990, 180, 0.55),
            "patty": generate_tone(740, 140, 0.55),
            "coffee": generate_tone(660, 120, 0.55),
            "celebrate": generate_tone(1040, 220, 0.6),
        }
        return sounds
    except Exception as e:
        print(f"Sound generation failed: {e}")
        return None


class Train:
    def __init__(self):
        self.x = WIDTH * 0.18
        self.y = TRACK_Y
        self.target_y = self.y
        self.w = 140
        self.h = 64
        self.bob_phase = 0.0
        self.invuln_timer = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h)

    def update(self, dt, keys):
        if keys[pygame.K_UP]:    self.target_y -= TRAIN_SPEED_Y
        if keys[pygame.K_DOWN]:  self.target_y += TRAIN_SPEED_Y
        self.target_y = clamp(self.target_y, TRACK_TOP + 10, TRACK_BOTTOM - 10)
        self.y += (self.target_y - self.y) * TRAIN_SMOOTHING
        self.bob_phase += dt * 0.003
        self.y += math.sin(self.bob_phase * 2.0) * 0.2
        if self.invuln_timer > 0: self.invuln_timer -= dt

    def grant_invuln(self, ms):
        self.invuln_timer = max(self.invuln_timer, ms)

    def hit_flash(self):
        pass

    def draw(self, surf):
        r = self.rect
        base_grey = (150, 150, 160)
        flick_grey = (180, 180, 190)
        body_col = flick_grey if (self.invuln_timer > 0 and (self.invuln_timer // 50) % 2 == 0) else base_grey
        draw_rounded_rect(surf, r, body_col, radius=12)
        roof = pygame.Rect(r.x, r.y - 8, r.w, 12)
        draw_rounded_rect(surf, roof, (230, 230, 240), radius=8)
        win_w, win_h, gap = 26, 24, 10
        start_x = r.x + 16
        y = r.y + 12
        for i in range(4):
            wrec = pygame.Rect(start_x + i * (win_w + gap), y, win_w, win_h)
            draw_rounded_rect(surf, wrec, (140, 170, 210), radius=6)
        pygame.draw.circle(surf, (255, 255, 220), (r.right + 10, r.centery - 10), 6)
        bar = pygame.Rect(r.x + 10, r.bottom - 14, r.w - 20, 8)
        draw_rounded_rect(surf, bar, COL_RED, radius=4)
        if self.invuln_timer > 0:
            shield_alpha = 120
            shield_surf = pygame.Surface((r.w + 44, r.h + 44), pygame.SRCALPHA)
            pygame.draw.ellipse(shield_surf, (140, 220, 255, shield_alpha), (0, 0, r.w + 44, r.h + 44), width=8)
            surf.blit(shield_surf, (r.x - 22, r.y - 22))
            frac = max(0.0, min(1.0, self.invuln_timer / PRESTO_INVULN_MS))
            arc_rect = pygame.Rect(r.x - 26, r.y - 26, r.w + 52, r.h + 52)
            start_angle = -math.pi / 2
            end_angle = start_angle + 2 * math.pi * frac
            pygame.draw.arc(surf, (180, 240, 255), arc_rect, start_angle, end_angle, 4)


class Tunnel:
    def __init__(self):
        self.offset = 0.0
        self.ballast_noise = [
            (random.randint(0, WIDTH), random.randint(TRACK_TOP, TRACK_BOTTOM))
            for _ in range(220)
        ]

    def update(self, dt, difficulty=1.0):
        speed = 300 * difficulty
        self.offset = (self.offset + speed * dt / 1000) % TIE_GAP_BASE

    def draw(self, surf):
        draw_vertical_gradient(surf, COL_BG_TOP, COL_BG_BOTTOM)
        ballast_rect = pygame.Rect(0, TRACK_TOP, WIDTH, TRACK_BOTTOM - TRACK_TOP)
        pygame.draw.rect(surf, COL_BALLAST, ballast_rect)
        for i, (x0, y0) in enumerate(self.ballast_noise):
            x = (x0 - self.offset * 1.2) % WIDTH
            shade = 35 + (i % 3) * 8
            pygame.draw.circle(surf, (shade, shade + 2, shade + 6), (int(x), int(y0)), 1)
        tie_gap = TIE_GAP_BASE
        start_x = -int(self.offset)
        for x in range(start_x, WIDTH + tie_gap, tie_gap):
            t = (WIDTH - x) / WIDTH
            thickness = int(lerp(6, 12, t))
            y1, y2 = TRACK_TOP, TRACK_BOTTOM
            pygame.draw.line(surf, COL_TIE_SH, (x + 2, y1), (x + 2, y2), thickness)
            pygame.draw.line(surf, COL_TIE, (x, y1), (x, y2), thickness)
        y_top = TRACK_Y - RAIL_SPREAD
        y_bot = TRACK_Y + RAIL_SPREAD
        pygame.draw.line(surf, COL_RAIL_SIDE, (0, y_top + 2), (WIDTH, y_top + 2), 6)
        pygame.draw.line(surf, COL_RAIL_SIDE, (0, y_bot + 2), (WIDTH, y_bot + 2), 6)
        pygame.draw.line(surf, COL_RAIL_TOP, (0, y_top), (WIDTH, y_top), 4)
        pygame.draw.line(surf, COL_RAIL_TOP, (0, y_bot), (WIDTH, y_bot), 4)


HAZARD_TYPES = ["Signal", "Fire", "Raccoon", "Disorderly", "Cone"]
HAZARD_WEIGHTS = [0.32, 0.20, 0.10, 0.24, 0.14]


class Hazard:
    def __init__(self, kind, difficulty=1.0):
        self.kind = kind
        self.x = WIDTH + 40
        margin = 22
        self.y = random.randint(TRACK_TOP + margin, TRACK_BOTTOM - margin)
        base_speed = random.uniform(*OBSTACLE_SPEED)
        self.vx = -(base_speed * (0.95 + 0.60 * (difficulty - 1.0)))
        self.alive = True
        self.phase = random.random() * math.tau
        self.size = {"Signal": 22, "Fire": 28, "Raccoon": 28, "Disorderly": 30, "Cone": 26}[kind]

    @property
    def rect(self):
        s = self.size
        return pygame.Rect(int(self.x - s), int(self.y - s), s * 2, s * 2)

    def update(self, dt):
        self.x += self.vx
        self.phase += dt * 0.004
        if self.kind in ('Disorderly', 'Raccoon', 'Cone'):
            self.y += math.sin(self.phase * 1.2) * 0.35
            self.y = clamp(self.y, TRACK_TOP + 18, TRACK_BOTTOM - 18)
        if self.x < -80: self.alive = False

    def draw(self, surf):
        if self.kind == "Signal":
            post = pygame.Rect(int(self.x - 4), int(self.y - 18), 8, 44)
            draw_rounded_rect(surf, post, (70, 80, 120), radius=3)
            pygame.draw.circle(surf, (255, 70, 80), (int(self.x), int(self.y - 4)), 10)
        elif self.kind == "Fire":
            cx, cy = int(self.x), int(self.y)
            flick = (math.sin(self.phase * 5) + 1) * 0.5
            pygame.draw.polygon(surf, (245, 100 + int(100 * flick), 50),
                                [(cx, cy - 24), (cx + 12, cy - 8), (cx + 6, cy), (cx, cy + 18), (cx - 6, cy),
                                 (cx - 12, cy - 8)])
            pygame.draw.polygon(surf, (255, 170, 60),
                                [(cx, cy - 16), (cx + 8, cy - 4), (cx + 3, cy + 6), (cx, cy + 10), (cx - 3, cy + 6),
                                 (cx - 8, cy - 4)])
            pygame.draw.polygon(surf, (255, 235, 140),
                                [(cx, cy - 10), (cx + 5, cy - 1), (cx, cy + 6), (cx - 5, cy - 1)])
            if random.random() < 0.3:
                pygame.draw.circle(surf, (255, 200, 120),
                                   (cx + random.randint(-10, 10), cy - 28 - random.randint(0, 6)), 2)
        elif self.kind == "Raccoon":
            cx, cy = int(self.x), int(self.y)
            pygame.draw.circle(surf, (120, 120, 120), (cx, cy), 18)
            pygame.draw.ellipse(surf, (60, 60, 70), (cx - 16, cy - 10, 32, 16))
            pygame.draw.circle(surf, (240, 240, 255), (cx - 7, cy - 3), 4)
            pygame.draw.circle(surf, (240, 240, 255), (cx + 7, cy - 3), 4)
            pygame.draw.circle(surf, (30, 30, 40), (cx - 7, cy - 3), 1)
            pygame.draw.circle(surf, (30, 30, 40), (cx + 7, cy - 3), 1)
            pygame.draw.circle(surf, (30, 30, 40), (cx, cy + 2), 2)
            pygame.draw.circle(surf, (120, 120, 120), (cx + 22, cy + 8), 7)
            pygame.draw.line(surf, (60, 60, 70), (cx + 18, cy + 8), (cx + 26, cy + 8), 3)
        elif self.kind == "Disorderly":
            use_green = random.random() < 0.5
            base_col = (90, 210, 120) if use_green else (170, 120, 210)
            cx, cy = int(self.x), int(self.y)
            blob = pygame.Surface((50, 46), pygame.SRCALPHA)
            pygame.draw.ellipse(blob, base_col, (2, 8, 46, 28))
            pygame.draw.circle(blob, base_col, (14, 14), 10)
            pygame.draw.circle(blob, base_col, (36, 14), 10)
            pygame.draw.circle(blob, (250, 250, 255), (18, 16), 5)
            pygame.draw.circle(blob, (250, 250, 255), (32, 16), 5)
            pygame.draw.circle(blob, (30, 30, 40), (18, 16), 2)
            pygame.draw.circle(blob, (30, 30, 40), (32, 16), 2)
            pygame.draw.rect(blob, (30, 30, 40), (21, 27, 8, 3), border_radius=1)
            pygame.draw.polygon(blob, (240, 240, 255), [(23, 30), (25, 27), (27, 30)])
            surf.blit(blob, (cx - 25, cy - 20))
        elif self.kind == "Cone":
            cx, cy = int(self.x), int(self.y)
            pygame.draw.polygon(surf, (235, 120, 40), [(cx, cy - 22), (cx + 14, cy + 14), (cx - 14, cy + 14)])
            pygame.draw.rect(surf, (255, 240, 210), (cx - 10, cy + 2, 20, 5), border_radius=2)
            pygame.draw.rect(surf, (210, 110, 40), (cx - 14, cy + 14, 28, 6), border_radius=2)


class Boost:
    def __init__(self, difficulty=1.0):
        self.x = WIDTH + 40
        margin = 22
        self.y = random.randint(TRACK_TOP + margin, TRACK_BOTTOM - margin)
        self.w, self.h = 36, 24
        base_speed = random.uniform(*BOOST_SPEED)
        self.vx = -(base_speed * (0.92 + 0.50 * (difficulty - 1.0)))
        self.alive = True
        self.phase = random.random() * math.tau

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h)

    def update(self, dt):
        self.x += self.vx
        self.phase += dt * 0.004
        self.y += math.sin(self.phase) * 0.3
        if self.x < -60: self.alive = False

    def draw(self, surf):
        r = self.rect
        draw_rounded_rect(surf, r, (40, 150, 90), radius=5)
        stripe = pygame.Rect(r.x + 4, r.y + 6, r.w - 8, 6)
        draw_rounded_rect(surf, stripe, (235, 255, 245), radius=3)
        for i in range(4):
            pygame.draw.rect(surf, (15, 40, 25), (r.x + 6 + i * 7, r.y + 14, 5, 3), border_radius=1)


class Bonus:
    def __init__(self, difficulty=1.0):
        self.x = WIDTH + 40
        margin = 22
        self.y = random.randint(TRACK_TOP + margin, TRACK_BOTTOM - margin)
        self.w, self.h = 24, 28
        base_speed = random.uniform(5.6, 8.2)
        self.vx = -(base_speed * (0.90 + 0.45 * (difficulty - 1.0)))
        self.alive = True
        self.phase = random.random() * math.tau

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h)

    def update(self, dt):
        self.x += self.vx
        self.phase += dt * 0.004
        self.y += math.sin(self.phase * 1.3) * 0.25
        if self.x < -60: self.alive = False

    def draw(self, surf):
        r = self.rect
        cup = pygame.Rect(r.x + 3, r.y + 6, r.w - 6, r.h - 10)
        # FIX: use surf as first arg; rect as second — no get_rect() on pygame.Rect
        draw_rounded_rect(surf, cup, (245, 245, 252), radius=6)
        pygame.draw.rect(surf, (185, 190, 210), (cup.x, cup.bottom - 6, cup.w, 6), border_radius=3)
        pygame.draw.rect(surf, (90, 95, 120), (r.x + 2, r.y + 2, r.w - 4, 7), border_radius=3)
        sleeve = pygame.Rect(r.x + 4, r.y + 12, r.w - 8, 10)
        pygame.draw.rect(surf, (210, 170, 90), sleeve, border_radius=4)
        pygame.draw.circle(surf, (235, 200, 120), sleeve.center, 4)
        sx = r.centerx
        for i in range(3):
            pygame.draw.circle(surf, (230, 235, 255), (sx - 3 + i * 3, r.y - 2 - i * 4), 1)


class Patty:
    def __init__(self, difficulty=1.0):
        self.x = WIDTH + 40
        margin = 22
        self.y = random.randint(TRACK_TOP + margin, TRACK_BOTTOM - margin)
        self.w, self.h = 30, 20
        base_speed = random.uniform(5.6, 8.2)
        self.vx = -(base_speed * (0.90 + 0.45 * (difficulty - 1.0)))
        self.alive = True
        self.phase = random.random() * math.tau

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h)

    def update(self, dt):
        self.x += self.vx
        self.phase += dt * 0.004
        self.y += math.sin(self.phase * 1.0) * 0.28
        if self.x < -60: self.alive = False

    def draw(self, surf):
        r = self.rect
        body = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.ellipse(body, (240, 190, 70), (0, 0, r.w, r.h))
        pygame.draw.ellipse(body, (200, 150, 50), (2, 2, r.w-4, r.h-4), width=2)
        for i in range(2):
            pygame.draw.circle(body, (255, 230, 150), (r.w//2 + (i*2-1)*3, 2), 1)
        surf.blit(body, (r.x, r.y))


class Station:
    def __init__(self, difficulty=1.0):
        self.x = WIDTH + 40
        margin = 22
        self.y = random.randint(TRACK_TOP + margin, TRACK_BOTTOM - margin)
        self.w, self.h = 60, 26
        base_speed = random.uniform(5.2, 7.0)
        self.vx = -(base_speed * (0.92 + 0.45 * (difficulty - 1.0)))
        self.alive = True
        self.phase = random.random() * math.tau

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h)

    def update(self, dt):
        self.x += self.vx
        self.phase += dt * 0.004
        self.y += math.sin(self.phase * 1.1) * 0.25
        if self.x < -80: self.alive = False

    def draw(self, surf):
        r = self.rect
        draw_rounded_rect(surf, r, (70, 110, 210), radius=6)
        txt = pygame.font.SysFont("Inter,Helvetica,Arial", 16, bold=True).render("STN", True, (255, 255, 255))
        surf.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2))


ANNOUNCEMENTS = [
    "Attention customers: signal problems ahead.",
    "We apologize for delays due to an earlier incident.",
    "Fire alarm at the next station - expect delays.",
    "Track intrusion reported. Please stand back from the platform edge.",
    "Residual delays along the line."
]


class Announcement:
    def __init__(self, text, ttl=2200):
        self.text = text
        self.ttl = ttl

    def update(self, dt): self.ttl -= dt

    def draw(self, surf, font, y=16):
        if self.ttl <= 0: return
        t = max(0.0, min(1.0, self.ttl / 2200))
        alpha = int(255 * (t ** 1.5))
        msg = font.render(self.text, True, COL_TEXT)
        pad = 12
        box = pygame.Surface((msg.get_width() + pad * 2, msg.get_height() + pad * 2), pygame.SRCALPHA)
        draw_rounded_rect(box, box.get_rect(), (35, 40, 65, alpha), radius=10)
        box.blit(msg, (pad, pad))
        x = WIDTH // 2 - box.get_width() // 2
        surf.blit(box, (x, y))


class Game:
    def __init__(self):
        print("Initializing Game object...")
        pygame.init()
        pygame.display.set_caption("TTC Delay Dodge")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        print(f"Screen created: {self.screen.get_size()}")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Inter,Helvetica,Arial", 22)
        self.font_small = pygame.font.SysFont("Inter,Helvetica,Arial", 18)
        self.font_big = pygame.font.SysFont("Inter,Helvetica,Arial", 38, bold=True)

        self.sounds = init_sounds()

        self.tunnel = Tunnel()
        self.train = Train()
        self.hazards = []
        self.boosts = []
        self.bonuses = []
        self.patties = []
        self.announcements = []
        self.stations = []

        self.delay_seconds = 0
        self.on_time_seconds = 0.0
        self.elapsed_ms = 0
        self.game_over = False
        self.paused = False
        self.flash_timer = 0

        self.highscore = load_highscore()
        self.highscore_name = load_highscore_name()  # load local name sidecar
        self.state = "menu"
        self.player_name = ""
        self.show_legend = True
        self.legend_mandatory = True
        self.legend_shown_once = False

        now = pygame.time.get_ticks()
        self.next_hazard_at = now + random.randint(*OBSTACLE_SPAWN_EASY)
        self.next_boost_at = now + random.randint(*BOOST_SPAWN_EVERY)
        self.next_bonus_at = now + random.randint(4500, 7000)
        self.next_patty_at = now + random.randint(6500, 9000)
        self.next_station_at = now + random.randint(20000, 30000)
        self.next_announce_at = now + random.randint(*ANNOUNCEMENT_EVERY)

        self.legend_close_rect = None
        self.legend_pos = (12, 12)

        self.just_got_new_hs = False

        self.global_top_cache = None
        self.global_top_last_ms = 0
        self.fetching_top = False

        # --- MOBILE TAP DETECTION (tap+lift to start/restart) ---
        # Use normalized finger coords (0..1); 0.02 ~ ~12px on 600px height.
        self.touch_down = None  # (finger_id, x_norm, y_norm, t_ms)
        self.TAP_MAX_DIST_NORM = 0.02
        self.TAP_MAX_MS = 350

    # --- MOBILE-ONLY: prompt for name using browser prompt on the name screen ---
    def mobile_prompt_name(self):
        if not WEB:
            return
        try:
            default = self.player_name or self.highscore_name or "Player"
            nm = window.prompt("Enter your name:", default)
            if nm:
                self.player_name = nm.strip()[:18]
                save_highscore_name(self.player_name)
        except Exception:
            pass

    def reset(self):
        hs = self.highscore
        hsname = self.highscore_name
        name = self.player_name
        self.__init__()
        self.highscore = hs
        self.highscore_name = hsname
        self.player_name = name
        self.state = "menu"
        self.show_legend = False
        self.legend_mandatory = False

    def difficulty(self):
        seconds = self.elapsed_ms / 1000.0
        return 1.05 + 0.28 * (seconds // 10)

    def spawn_hazard(self):
        kind = random.choices(HAZARD_TYPES, weights=HAZARD_WEIGHTS, k=1)[0]
        self.hazards.append(Hazard(kind, difficulty=self.difficulty()))

    def spawn_boost(self): self.boosts.append(Boost(difficulty=self.difficulty()))
    def spawn_bonus(self): self.bonuses.append(Bonus(difficulty=self.difficulty()))
    def spawn_patty(self): self.patties.append(Patty(difficulty=self.difficulty()))
    def spawn_station(self): self.stations.append(Station(difficulty=self.difficulty()))

    def pickup_station(self):
        if self.delay_seconds > 0:
            if self.sounds: self.sounds["station"].play()
            self.delay_seconds = max(0, self.delay_seconds - 10)
            self.announcements.append(Announcement("Station checkpoint (-10 min delay)", ttl=2000))

    def spawn_announcement(self):
        self.announcements.append(Announcement(random.choice(ANNOUNCEMENTS)))

    def hit_hazard(self, kind):
        if self.sounds: self.sounds["hit"].play()
        self.train.hit_flash()
        add = DELAY_MINUTES.get(kind, 5)
        self.delay_seconds += add
        self.flash_timer = 140
        cause = {
            "Signal": "signal problem",
            "Fire": "fire",
            "Raccoon": "track intrusion (raccoon)",
            "Disorderly": "disorderly patron",
            "Cone": "work zone cone",
        }.get(kind, "incident")
        self.announcements.append(Announcement(f"Delay: {cause}", ttl=2000))

    def pickup_boost(self):
        if self.sounds: self.sounds["boost"].play()
        self.train.grant_invuln(PRESTO_INVULN_MS)
        self.announcements.append(Announcement(f"PRESTO: invulnerable for {PRESTO_INVULN_MS // 1000}s.", ttl=2000))

    def pickup_bonus(self):
        if self.sounds: self.sounds["coffee"].play()
        self.on_time_seconds += 6.0
        self.announcements.append(Announcement("+6 Coffee!", ttl=1600))

    def pickup_patty(self):
        if self.sounds: self.sounds["patty"].play()
        self.on_time_seconds += 10.0
        self.announcements.append(Announcement("+10 Jamaican Patty!", ttl=1600))

    async def maybe_refresh_global_top(self, force=False):
        now = pygame.time.get_ticks()
        if not force and (now - self.global_top_last_ms) < 5000:
            return
        if self.fetching_top:
            return

        self.fetching_top = True
        try:
            top = await _api_get_top()  # await, no run_until_complete
            if top is not None:
                self.global_top_cache = top[:20]
                self.global_top_last_ms = now
                if self.global_top_cache:  # mirror #1 into fallback for HUD
                    top_nm, top_sc = self.global_top_cache[0]
                    self.highscore = int(top_sc)
                    self.highscore_name = top_nm
            else:
                # keep None so the run loop can retry
                self.global_top_cache = None
        finally:
            self.fetching_top = False

    async def submit_global_score(self, name, score):
        ok = await _api_post_score(name, score)
        self.global_top_cache = None

    def update(self, dt):
        if self.state != "playing" or self.game_over or self.paused:
            return
        keys = pygame.key.get_pressed()
        self.elapsed_ms += dt
        diff = self.difficulty()
        self.tunnel.update(dt, difficulty=diff)
        self.train.update(dt, keys)
        now = pygame.time.get_ticks()
        if now >= self.next_hazard_at:
            self.spawn_hazard()
            if diff >= 2.0 and random.random() < 0.35:
                self.spawn_hazard()
            base_min, base_max = OBSTACLE_SPAWN_EASY
            scale = max(0.44, 1.0 - 0.20 * (diff - 1.0))
            self.next_hazard_at = now + random.randint(int(base_min * scale), int(base_max * scale))
        if now >= self.next_boost_at:
            self.spawn_boost()
            base_min, base_max = BOOST_SPAWN_EVERY
            scale = max(0.72, 1.0 - 0.10 * (diff - 1.0))
            self.next_boost_at = now + random.randint(int(base_min * scale), int(base_max * scale))
        if now >= self.next_bonus_at:
            self.spawn_bonus()
            gap = random.randint(5500, 8500)
            self.next_bonus_at = now + int(gap * max(0.8, 1.0 - 0.08 * (diff - 1.0)))
        if now >= self.next_patty_at:
            self.spawn_patty()
            gap = random.randint(7000, 10000)
            self.next_patty_at = now + int(gap * max(0.85, 1.0 - 0.08 * (diff - 1.0)))
        if now >= self.next_station_at and self.delay_seconds >= 10:
            self.spawn_station()
            gap = random.randint(20000, 30000)
            self.next_station_at = now + int(gap * max(0.8, 1.0 - 0.06 * (diff - 1.0)))
        if now >= self.next_announce_at:
            self.spawn_announcement()
            self.next_announce_at = now + random.randint(*ANNOUNCEMENT_EVERY)
        for h in self.hazards: h.update(dt)
        self.hazards = [h for h in self.hazards if h.alive]
        for b in self.boosts: b.update(dt)
        self.boosts = [b for b in self.boosts if b.alive]
        for bn in self.bonuses: bn.update(dt)
        self.bonuses = [bn for bn in self.bonuses if bn.alive]
        for pt in self.patties: pt.update(dt)
        self.patties = [pt for pt in self.patties if pt.alive]
        for st in self.stations: st.update(dt)
        self.stations = [st for st in self.stations if st.alive]
        tr = self.train.rect
        if self.train.invuln_timer <= 0:
            for h in self.hazards:
                if tr.colliderect(h.rect):
                    h.alive = False
                    self.hit_hazard(h.kind)
                    break
        for b in self.boosts:
            if tr.colliderect(b.rect):
                b.alive = False
                self.pickup_boost()
        for bn in self.bonuses:
            if tr.colliderect(bn.rect):
                bn.alive = False
                self.pickup_bonus()
        for pt in self.patties:
            if tr.colliderect(pt.rect):
                pt.alive = False
                self.pickup_patty()
        for st in self.stations:
            if tr.colliderect(st.rect):
                st.alive = False
                self.pickup_station()
        self.on_time_seconds += (dt / 1000.0)
        if self.delay_seconds >= 60:
            self.game_over = True
            self.state = "gameover"
            self.announcements.append(Announcement("Service suspended due to delays.", ttl=2600))
            score_int = int(self.on_time_seconds)

            # Always submit (so the board stays current even if you didn't hit #1)
            if GLOBAL_API_URL:
                asyncio.create_task(self.submit_global_score(self.player_name or "Player", score_int))
            else:
                append_leaderboard_local(self.player_name, score_int)

            # Compare against the cached global top to decide the banner/sound
            global_best = 0
            if self.global_top_cache:
                _, global_best = self.global_top_cache[0]  # (name, score)

            if score_int > global_best:  # if ties should count as a record
                self.just_got_new_hs = True
                if self.sounds and "celebrate" in self.sounds:
                    self.sounds["celebrate"].play()

            self.highscore = score_int
            self.highscore_name = self.player_name or "Player"
            save_highscore(self.highscore)
            save_highscore_name(self.highscore_name)

            # Refresh for the next screen
            asyncio.create_task(self.maybe_refresh_global_top(force=True))
        if self.flash_timer > 0: self.flash_timer -= dt
        for a in self.announcements: a.update(dt)
        self.announcements = [a for a in self.announcements if a.ttl > 0]

    def draw_hud(self):
        pad = 12
        bar_h = 76
        hud = pygame.Surface((WIDTH, bar_h), pygame.SRCALPHA)
        draw_rounded_rect(hud, hud.get_rect(), (25, 28, 46, 230), radius=0)

        # Score
        score = max(0, int(self.on_time_seconds))
        score_text = self.font.render(f"Score: {score}", True, COL_TEXT)
        hud.blit(score_text, (pad, 12))

        # Delay
        dm = int(self.delay_seconds)
        delay_col = COL_TEXT if dm == 0 else (255, 155, 165) if dm < 30 else (255, 90, 110)
        dm_text = self.font.render(f"Delay: {dm} min", True, delay_col)
        hud.blit(dm_text, (WIDTH // 2 - dm_text.get_width() // 2, 12))

        # High score with name: prefer GLOBAL if available; else local
        disp_score, disp_name = self.highscore, getattr(self, "highscore_name", "")
        if GLOBAL_API_URL and self.global_top_cache:
            top_nm, top_sc = self.global_top_cache[0]
            disp_score, disp_name = int(top_sc), top_nm

        hs_label = f"High score: {disp_score}"
        if disp_name:
            hs_label += f" ({disp_name})"
        hs = self.font.render(hs_label, True, COL_TEXT_DIM)
        hud.blit(hs, (pad, 44))

        self.screen.blit(hud, (0, 0))

    def draw_legend_tile(self):
        box_w, box_h = 460, 560
        pad = 12
        tile = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        draw_rounded_rect(tile, tile.get_rect(), (25, 28, 46, 210), radius=12)
        title = self.font.render("Legend & Controls", True, COL_TEXT)
        tile.blit(title, (pad, pad))
        close_rect = pygame.Rect(box_w - 28, pad, 20, 20)
        draw_rounded_rect(tile, close_rect, (180, 50, 60), radius=6)
        x_txt = self.font_small.render("X", True, (255, 255, 255))
        tile.blit(x_txt, (box_w - 24, pad + 1))
        self.legend_close_rect = pygame.Rect(self.legend_pos[0] + close_rect.x,
                                             self.legend_pos[1] + close_rect.y,
                                             close_rect.w, close_rect.h)
        y = pad + 40
        ordered = sorted(DELAY_MINUTES.items(), key=lambda kv: kv[1])
        for kind, mins in ordered:
            dummy = Hazard(kind); dummy.x, dummy.y = 26, y + 20; dummy.draw(tile)
            label_map = {
                "Signal":     f"Signal problem: +{mins} min delay",
                "Fire":       f"Fire/Alarm: +{mins} min delay",
                "Raccoon":    f"Track intrusion (raccoon): +{mins} min delay",
                "Disorderly": f"Disorderly patron: +{mins} min delay",
                "Cone":       f"Work zone cone: +{mins} min delay",
            }
            tile.blit(self.font_small.render(label_map[kind], True, COL_TEXT), (52, y + 10))
            y += 42
        station = Station(); station.x, station.y = 26, y + 20; station.draw(tile)
        tile.blit(self.font_small.render("Station checkpoint: -10 min delay", True, COL_TEXT), (52, y + 10)); y += 44
        boost = Boost(); boost.x, boost.y = 26, y + 20; boost.draw(tile)
        tile.blit(self.font_small.render("PRESTO: brief invulnerability", True, COL_ACCENT), (52, y + 10)); y += 42
        coffee = Bonus(); coffee.x, coffee.y = 26, y + 20; coffee.draw(tile)
        tile.blit(self.font_small.render("Coffee: +6 score", True, COL_TEXT), (52, y + 10)); y += 42
        patty = Patty(); patty.x, patty.y = 26, y + 20; patty.draw(tile)
        tile.blit(self.font_small.render("Jamaican Patty: +10 score", True, COL_TEXT), (52, y + 10)); y += 42
        tile.blit(self.font_small.render("Up/Down move • P pause • R restart • K legend", True, COL_TEXT_DIM), (pad, box_h - 28))
        self.screen.blit(tile, self.legend_pos)

    def draw_name_entry(self):
        center = (WIDTH // 2, HEIGHT // 2)
        msg = self.font_big.render("Enter your name", True, COL_TEXT)
        self.screen.blit(msg, msg.get_rect(center=(center[0], center[1] - 90)))
        box_w = 460
        box = pygame.Surface((box_w, 56), pygame.SRCALPHA)
        draw_rounded_rect(box, box.get_rect(), (25, 28, 46, 220), radius=10)
        text = self.font_big.render(self.player_name or " ", True, COL_TEXT)
        box.blit(text, (16, 8))
        self.screen.blit(box, (center[0] - box_w // 2, center[1] - 46))

        top = []
        if GLOBAL_API_URL and self.global_top_cache is not None:
            top = self.global_top_cache[:5]
            header = "Global Top Scores"
        else:
            top = read_leaderboard_top_local(5)
            header = "Top Scores"

        y = center[1] + 40
        base_x = center[0] + box_w // 4
        self.screen.blit(self.font.render(header, True, COL_TEXT), (base_x, y))
        y += 28
        if top:
            for nm, sc in top:
                line = self.font_small.render(f"{nm}: {sc}", True, COL_TEXT_DIM)
                self.screen.blit(line, (base_x, y))
                y += 22
        else:
            self.screen.blit(self.font_small.render("No scores yet - be the first!", True, COL_TEXT_DIM), (base_x, y))

        sig = self.font_small.render("Asha Asvathaman", True, COL_TEXT_DIM)
        self.screen.blit(sig, (WIDTH - 12 - sig.get_width(), HEIGHT - 12 - sig.get_height()))

    def draw_menu(self):
        center = (WIDTH // 2, HEIGHT // 2)
        title = self.font_big.render("TTC Delay Dodge", True, COL_TEXT)
        self.screen.blit(title, title.get_rect(center=(center[0], TRACK_TOP - 40)))
        y0 = TRACK_TOP + 40
        lines = [
            ("Dodge TTC delays and survive as long as you can!", COL_TEXT),
            ("• Hazards add delay minutes", COL_TEXT_DIM),
            ("• Station checkpoint reduces delay minutes", COL_TEXT),
            ("• PRESTO cards grant brief invulnerability", COL_ACCENT),
            ("• Collect coffee and Jamaican patties to increase score", COL_TEXT_DIM),
            ("• 60 min accumulated delay = Service Suspended", COL_TEXT_DIM),
        ]
        for i, (txt, col) in enumerate(lines):
            surf = self.font.render(txt, True, col)
            self.screen.blit(surf, surf.get_rect(center=(center[0], y0 + i * 30)))
        sub = self.font.render("Press Enter to start   •   K to toggle legend", True, COL_TEXT_DIM)
        below = TRACK_BOTTOM + 24
        self.screen.blit(sub, sub.get_rect(center=(center[0], below)))

        # --- MOBILE MENU INSTRUCTION ---
        if WEB:
            mobile_sub = self.font.render("Mobile: Tap to start • Drag to move the train", True, COL_TEXT_DIM)
            self.screen.blit(mobile_sub, mobile_sub.get_rect(center=(center[0], below + 32)))

        sig = self.font_small.render("Asha Asvathaman", True, COL_TEXT_DIM)
        self.screen.blit(sig, (WIDTH - 12 - sig.get_width(), HEIGHT - 12 - sig.get_height()))
        if (self.state == "menu" and (self.legend_mandatory or self.show_legend)):
            self.draw_legend_tile()

    def draw_overlay(self):
        center = (WIDTH // 2, HEIGHT // 2)
        if self.paused and self.state == "playing":
            msg = self.font_big.render("Paused", True, COL_TEXT)
            sub = self.font.render("Press P to resume", True, COL_TEXT_DIM)
            self.screen.blit(msg, msg.get_rect(center=(center[0], center[1] - 14)))
            self.screen.blit(sub, sub.get_rect(center=(center[0], center[1] + 22)))
        if self.state == "gameover":
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((10, 10, 16, 170))
            self.screen.blit(shade, (0, 0))
            msg = self.font_big.render("Service Suspended", True, COL_TEXT)
            sub = self.font.render("Press R to restart", True, COL_TEXT_DIM)
            self.screen.blit(msg, msg.get_rect(center=(center[0], center[1] - 14)))
            self.screen.blit(sub, sub.get_rect(center=(center[0], center[1] + 24)))

            # --- MOBILE GAME OVER INSTRUCTION ---
            if WEB:
                mobile_sub = self.font.render("Mobile: Tap to restart", True, COL_TEXT_DIM)
                self.screen.blit(mobile_sub, mobile_sub.get_rect(center=(center[0], center[1] + 52)))

            if self.just_got_new_hs:
                t = pygame.time.get_ticks()
                blink_on = (t // 160) % 2 == 0
                base_col_1 = (255, 236, 140)
                base_col_2 = (255, 216, 80)
                title_col = base_col_1 if blink_on else base_col_2
                title = self.font_big.render("New High Score!", True, title_col)
                self.screen.blit(title, title.get_rect(center=(center[0], center[1] - 92)))

                rng = random.Random(t // 60)
                for _ in range(28):
                    sx = rng.randint(center[0] - 240, center[0] + 240)
                    sy = rng.randint(center[1] - 200, center[1] + 10)
                    r = rng.randint(2, 5)
                    a = 180 + rng.randint(-60, 40)
                    spark = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(spark, (255, 230, 140, a), (r + 1, r + 1), r)
                    self.screen.blit(spark, (sx, sy))
                    if rng.random() < 0.35:
                        size = r + 3
                        cx, cy = sx + r + 1, sy + r + 1
                        pygame.draw.line(self.screen, (255, 240, 180), (cx - size, cy), (cx + size, cy), 1)
                        pygame.draw.line(self.screen, (255, 240, 180), (cx, cy - size), (cx, cy + size), 1)

            sig = self.font_small.render("Asha Asvathaman", True, COL_TEXT_DIM)
            self.screen.blit(sig, (WIDTH - 12 - sig.get_width(), HEIGHT - 12 - sig.get_height()))

    def draw(self):
        try:
            self.tunnel.draw(self.screen)
            if self.flash_timer > 0:
                alpha = int(120 * (self.flash_timer / 140))
                flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                flash.fill((*COL_RED, alpha))
                self.screen.blit(flash, (0, 0))
            if self.state == "playing":
                for h in self.hazards: h.draw(self.screen)
                for b in self.boosts:  b.draw(self.screen)
                for bn in self.bonuses: bn.draw(self.screen)
                for pt in self.patties: pt.draw(self.screen)
                for st in self.stations: st.draw(self.screen)
            self.train.draw(self.screen)
            self.draw_hud()
            y = 16
            for a in self.announcements[-2:]:
                a.draw(self.screen, self.font, y=y);
                y += 46
            if self.state == "name":
                self.draw_name_entry()
            elif self.state == "menu":
                self.draw_menu()
            self.draw_overlay()

            if self.state == "playing":
                sig = self.font_small.render("Asha Asvathaman", True, COL_TEXT_DIM)
                self.screen.blit(sig, (WIDTH - 12 - sig.get_width(), HEIGHT - 12 - sig.get_height()))
        except Exception as e:
            print(f"Draw error: {e}")
            import traceback
            traceback.print_exc()

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # --- MOBILE: smooth vertical control (tap or drag anywhere on screen) ---
            if WEB and e.type in (pygame.FINGERDOWN, pygame.FINGERMOTION):
                self.train.target_y = TRACK_TOP + e.y * (TRACK_BOTTOM - TRACK_TOP)

            # --- MOBILE: record touch down for tap detection ---
            if WEB and hasattr(pygame, "FINGERDOWN") and e.type == pygame.FINGERDOWN:
                self.touch_down = (getattr(e, "finger_id", 0), e.x, e.y, pygame.time.get_ticks())

            # --- MOBILE: tap to close legend, enter game, submit name+start, restart ---
            if WEB and hasattr(pygame, "FINGERUP") and e.type == pygame.FINGERUP:
                is_tap = False
                if self.touch_down is not None:
                    fid0, x0, y0, t0 = self.touch_down
                    dt = pygame.time.get_ticks() - t0
                    dx = e.x - x0
                    dy = e.y - y0
                    dist = math.hypot(dx, dy)
                    if dist <= self.TAP_MAX_DIST_NORM and dt <= self.TAP_MAX_MS:
                        is_tap = True
                # Reset touch_down regardless
                self.touch_down = None

                if not is_tap:
                    # Drag/swipe: ignore any state changes
                    continue

                if self.state in ("menu", "name"):
                    # If legend is visible, a tap closes it; else proceed
                    if self.show_legend:
                        self.show_legend = False
                        if self.state == "menu":
                            self.legend_mandatory = False
                            self.legend_shown_once = True
                    else:
                        if self.state == "menu":
                            if self.player_name.strip():
                                if self.sounds: self.sounds["start"].play()
                                self.state = "playing"
                                self.legend_mandatory = False
                            else:
                                if self.sounds: self.sounds["menu"].play()
                                self.state = "name"
                        elif self.state == "name":
                            # --- MOBILE-ONLY: browser prompt for name before starting ---
                            self.mobile_prompt_name()
                            if self.sounds: self.sounds["start"].play()
                            if not self.player_name.strip():
                                self.player_name = "Player"
                            self.state = "playing"
                            self.legend_mandatory = False
                elif self.state == "gameover":
                    if self.sounds: self.sounds["menu"].play()
                    self.reset()

            # Mouse: click X to close legend OR top/bottom to move (desktop unchanged)
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.show_legend and self.legend_close_rect and self.legend_close_rect.collidepoint(e.pos):
                    self.show_legend = False
                    if self.state == "menu":
                        self.legend_mandatory = False
                        self.legend_shown_once = True
                else:
                    _, h = self.screen.get_size()
                    if e.pos[1] < h * 0.5:
                        self.train.target_y -= TRAIN_SPEED_Y * 10
                    else:
                        self.train.target_y += TRAIN_SPEED_Y * 10

            # Keyboard (unchanged)
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if e.key == pygame.K_k and self.state in ("menu", "playing"):
                    self.show_legend = not self.show_legend

                if self.state == "name":
                    if e.key == pygame.K_RETURN:
                        if self.sounds: self.sounds["start"].play()
                        if not self.player_name.strip():
                            self.player_name = "Player"
                        self.state = "playing"
                        self.show_legend = False
                        self.legend_mandatory = False
                    elif e.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    else:
                        ch = e.unicode
                        if ch and (ch.isalnum() or ch in " -_."):
                            if len(self.player_name) < 18:
                                self.player_name += ch

                elif self.state == "menu":
                    if e.key == pygame.K_RETURN:
                        if self.show_legend:
                            if self.sounds: self.sounds["menu"].play()
                            self.show_legend = False
                            self.legend_mandatory = False
                            self.legend_shown_once = True
                        else:
                            if self.player_name.strip():
                                if self.sounds: self.sounds["start"].play()
                                self.state = "playing"
                            else:
                                if self.sounds: self.sounds["menu"].play()
                                self.state = "name"

                elif self.state == "playing":
                    if e.key == pygame.K_p and not self.game_over:
                        self.paused = not self.paused

                elif self.state == "gameover":
                    if e.key == pygame.K_r:
                        if self.sounds: self.sounds["menu"].play()
                        self.reset()

    async def run(self):
        print("Game starting...")
        print(f"Screen size: {self.screen.get_size()}")
        print(f"Initial state: {self.state}")

        if GLOBAL_API_URL:
            try:
                print("Fetching global leaderboard...")
                await self.maybe_refresh_global_top(force=True)
                print("Global leaderboard fetched!")
            except Exception as e:
                print("Initial leaderboard fetch failed:", e)

        frame_count = 0
        while True:
            dt = self.clock.tick(FPS)

            if frame_count < 5:
                print(f"Frame {frame_count}: dt={dt}, state={self.state}")
            frame_count += 1

            self.handle_events()
            self.update(dt)
            if GLOBAL_API_URL and (self.state in ("menu", "name", "gameover")):
                if self.global_top_cache is None and not self.fetching_top:
                    asyncio.create_task(self.maybe_refresh_global_top(force=True))

            self.draw()
            pygame.display.flip()
            await asyncio.sleep(0)


if __name__ == "__main__":
    print("=== STARTING TTC DELAY DODGE ===")
    print(f"Platform: {sys.platform}")
    print(f"WEB mode: {WEB}")
    try:
        game = Game()
        print("Game object created successfully")
        asyncio.run(game.run())
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

