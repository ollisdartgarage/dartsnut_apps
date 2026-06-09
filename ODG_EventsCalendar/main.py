import time
import json
import os
import math
from datetime import date
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from pydartsnut import Dartsnut

# ── Config ────────────────────────────────────────────────────────────────────
JSON_PATH    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "events.json")
REFRESH_SEC  = 3600
PAGE_DUR     = 3.0        # 3 sec per page → 5 pages = 15 sec total
WM_KEYWORDS  = ["world darts championship", "darts-wm", "dart-wm"]

# ── Colours ───────────────────────────────────────────────────────────────────
BG        = (0,   0,   0)
WHITE     = (255, 255, 255)
YELLOW    = (255, 215,   0)
GOLD      = (255, 190,   0)
GOLD_DIM  = (160, 120,   0)
ORANGE    = (255, 140,   0)
GREEN     = ( 50, 205,  50)
RED       = (220,  40,  40)
GREY      = (120, 120, 120)
LGREY     = (190, 190, 190)
PDC_COL   = ( 30, 120, 255)
WDF_COL   = ( 30, 180,  80)
LIVE_COL  = (220,  40,  40)
HDR_BG    = ( 10,  10,  60)
DIV       = ( 40,  40,  40)   # divider line between two events

W, H      = 128, 128
HDR_H     = 13            # top header strip
EVENT_H   = (H - HDR_H) // 2   # ~57px per event block

# ── Fonts ─────────────────────────────────────────────────────────────────────
def load_font(paths, size):
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

BOLD = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","C:/Windows/Fonts/arialbd.ttf"]
REG  = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","C:/Windows/Fonts/arial.ttf"]

F11B = load_font(BOLD,11)
F10B = load_font(BOLD,10)
F9B  = load_font(BOLD, 9)
F8B  = load_font(BOLD, 8)
F7B  = load_font(BOLD, 7)
F7   = load_font(REG,  7)
F6B  = load_font(BOLD, 6)
F6   = load_font(REG,  6)

MONTHS_EN   = ["","Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]
MONTHS_FULL = ["","January","February","March","April","May","June",
               "July","August","September","October","November","December"]

# ── Helpers ───────────────────────────────────────────────────────────────────
def is_wm(ev):
    return any(k in ev["name"].lower() for k in WM_KEYWORDS) and ev["org"] == "PDC"

def load_assets():
    d = os.path.dirname(os.path.abspath(__file__))
    assets = {}
    for name, fname in [("trophy","trophy.png"),("bg","wm_bg_128.png")]:
        try:
            assets[name] = Image.open(os.path.join(d, fname)).convert("RGBA")
        except Exception:
            assets[name] = None
    return assets

def load_events(show_pdc=True, show_wdf=True):
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        today = date.today()
        return [e for e in d.get("events", [])
                if date.fromisoformat(e["date_end"]) >= today
                and not (e["org"]=="PDC" and not show_pdc)
                and not (e["org"]=="WDF" and not show_wdf)]
    except Exception as ex:
        print(f"[ODG] {ex}")
        return []

def fmt_date(s, e):
    sd, ed = date.fromisoformat(s), date.fromisoformat(e)
    if sd == ed:             return f"{sd.day:02d} {MONTHS_EN[sd.month]}"
    if sd.month == ed.month: return f"{sd.day:02d}-{ed.day:02d} {MONTHS_EN[sd.month]}"
    return f"{sd.day:02d} {MONTHS_EN[sd.month]} – {ed.day:02d} {MONTHS_EN[ed.month]}"

def days_status(s_str, e_str):
    sd, ed, t = date.fromisoformat(s_str), date.fromisoformat(e_str), date.today()
    if t > ed:   return None, None
    if t >= sd:  return 0, "LIVE"
    days = (sd - t).days
    return days, f"{days}d"

ABBREV = [
    ("Players Championship", "Pl. Championship"),
]

def shorten(name, max_len):
    for p in ["PDC ","WDF "]:
        if name.startswith(p): name = name[len(p):]
    for full, short in ABBREV:
        if full in name:
            name = name.replace(full, short)
            break
    return name[:max_len]

def shorten_loc(loc, max_len):
    return loc.split(",")[0].strip()[:max_len]

# ── Header ────────────────────────────────────────────────────────────────────
def draw_header(draw, label, page_cur, page_tot):
    draw.rectangle([(0,0),(W-1,HDR_H-1)], fill=HDR_BG)
    draw.text((3,2), label, font=F7B, fill=YELLOW)
    pg  = f"{page_cur}/{page_tot}"
    pgw = int(draw.textlength(pg, font=F6B))
    draw.text((W-pgw-2, 3), pg, font=F6B, fill=LGREY)

# ── Single event block ────────────────────────────────────────────────────────
def draw_event_block(draw, ev, y, bg_col=None):
    """Draw one event in a 128 × EVENT_H block starting at y."""
    if bg_col:
        draw.rectangle([(0,y),(W-1,y+EVENT_H-1)], fill=bg_col)

    days, status = days_status(ev["date_start"], ev["date_end"])

    # ── Row 1: Banderole ─────────────────────────────────────────────────────
    BAND_H = 14
    r1y = y + 5

    # full white banderole background
    BAND_H = 15
    r1y = y + 4

    draw.rectangle([(0, r1y),(W-1, r1y+BAND_H-1)], fill=WHITE)

    # PDC / WDF badge
    bc = PDC_COL if ev["org"] == "PDC" else WDF_COL
    bw = int(draw.textlength(ev["org"], font=F9B)) + 8
    draw.rectangle([(0, r1y),(bw, r1y+BAND_H-1)], fill=bc)
    draw.text((4, r1y+2), ev["org"], font=F9B, fill=WHITE)

    # date in black on white
    date_str = fmt_date(ev["date_start"], ev["date_end"])
    draw.text((bw+5, r1y+2), date_str, font=F9B, fill=BG)

    # countdown right-aligned — red if within 30 days, black otherwise
    if status == "LIVE":
        sc, st = LIVE_COL, "● LIVE"
    elif status:
        sc = RED if (days or 999) <= 30 else (0,0,0)
        st = f"{days}d"
    else:
        sc, st = BG, ""
    if st:
        sw = int(draw.textlength(st, font=F9B))
        draw.text((W-sw-4, r1y+2), st, font=F9B, fill=sc)

    # ── Row 2: Event name BIG ────────────────────────────────────────────────
    r2y = r1y + BAND_H + 3
    name = shorten(ev["name"], 25)
    draw.text((3, r2y), name, font=F10B, fill=WHITE)

    # ── Row 3: Location ───────────────────────────────────────────────────────
    r3y = r2y + 18
    loc = shorten_loc(ev.get("location",""), 22)
    if loc:
        draw.text((3, r3y), loc, font=F8B, fill=LGREY)

# ── Two-event page ────────────────────────────────────────────────────────────
def render_events_page(ev1, ev2, page_cur, page_tot, header_label):
    img  = Image.new("RGB",(W,H),BG)
    draw = ImageDraw.Draw(img)

    draw_header(draw, header_label, page_cur, page_tot)

    # top event block
    draw_event_block(draw, ev1, HDR_H, bg_col=(12,12,30))

    # divider
    div_y = HDR_H + EVENT_H
    draw.line([(0,div_y),(W-1,div_y)], fill=DIV, width=1)

    # bottom event block
    if ev2:
        draw_event_block(draw, ev2, div_y + 1, bg_col=(5,5,20))
    else:
        # empty bottom half
        draw.rectangle([(0,div_y+1),(W-1,H-1)], fill=(5,5,20))
        draw.text((3, div_y+20), "Stay tuned...", font=F8B, fill=(50,50,80))

    return img

# ── WM Countdown page ─────────────────────────────────────────────────────────
def render_wm_page(wm_ev, page_cur, page_tot, assets, anim_t):
    img  = Image.new("RGB",(W,H),BG)

    # dark bg image
    bg = assets.get("bg")
    if bg:
        overlay = Image.new("RGBA", bg.size, (0,0,0,200))
        comp = Image.alpha_composite(bg, overlay).convert("RGB")
        img.paste(comp,(0,0))

    draw = ImageDraw.Draw(img)

    # ── Header ────────────────────────────────────────────────────────────────
    draw_header(draw, "WC LONDON", page_cur, page_tot)

    days, status = days_status(wm_ev["date_start"], wm_ev["date_end"])

    # ── Banderole — same as event pages ──────────────────────────────────────
    BAND_H = 15
    r1y    = HDR_H + 3
    draw.rectangle([(0, r1y),(W-1, r1y+BAND_H-1)], fill=WHITE)

    # PDC badge
    bw = int(draw.textlength("PDC", font=F9B)) + 8
    draw.rectangle([(0, r1y),(bw, r1y+BAND_H-1)], fill=PDC_COL)
    draw.text((4, r1y+2), "PDC", font=F9B, fill=WHITE)

    # date range — compact, no extra spaces
    sd = date.fromisoformat(wm_ev["date_start"])
    ed = date.fromisoformat(wm_ev["date_end"])
    date_str = f"{sd.day} {MONTHS_EN[sd.month]}-{ed.day} {MONTHS_EN[ed.month]}"
    draw.text((bw+5, r1y+2), date_str, font=F8B, fill=BG)

    # countdown
    if status == "LIVE":
        sc, st = LIVE_COL, "● LIVE"
    elif days is not None:
        sc = RED if days <= 30 else (0,0,0)
        st = f"{days}d"
    else:
        sc, st = BG, ""
    if st:
        sw = int(draw.textlength(st, font=F9B))
        draw.text((W-sw-4, r1y+2), st, font=F9B, fill=sc)

    # ── WORLD DARTS CHAMPIONSHIP — big gold ───────────────────────────────────
    ty0 = r1y + BAND_H + 5
    draw.text((3, ty0),    "WORLD",        font=F11B, fill=GOLD)
    draw.text((3, ty0+14), "DARTS",        font=F11B, fill=GOLD)
    draw.text((3, ty0+28), "CHAMPIONSHIP", font=F9B,  fill=GOLD_DIM)

    # ── Venue ─────────────────────────────────────────────────────────────────
    draw.text((3, ty0+42), "Alexandra Palace", font=F9B, fill=LGREY)
    draw.text((3, ty0+54), "London",            font=F8B, fill=GREY)

    # ── Trophy animation — right side ─────────────────────────────────────────
    trophy = assets.get("trophy")
    if trophy:
        glow    = 0.85 + 0.3 * math.sin(anim_t * 1.5)
        t_enh   = ImageEnhance.Brightness(trophy).enhance(glow)
        FOOTER_H = 0
        body_h   = H - (r1y + BAND_H) - FOOTER_H
        t_h      = trophy.size[1]
        ty       = r1y + BAND_H + (body_h - t_h) // 2
        tx       = W - trophy.size[0] - 4
        img_rgba = img.convert("RGBA")
        img_rgba.paste(t_enh, (tx, ty), t_enh)
        img  = img_rgba.convert("RGB")
        draw = ImageDraw.Draw(img)
        for offset in [0, t_h//3, (t_h*2)//3]:
            sy = int(((anim_t * 25 + offset) % t_h)) + ty
            if ty <= sy <= ty + t_h:
                rel  = (sy - ty) / t_h
                fade = int(255 * math.sin(rel * math.pi))
                draw.line([(tx,sy),(tx+trophy.size[0],sy)],
                          fill=(fade, int(fade*0.95), int(fade*0.7)), width=1)

    return img

# ── No data screen ────────────────────────────────────────────────────────────
def render_no_data(draw):
    img  = Image.new("RGB",(W,H),BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0,0),(W-1,HDR_H-1)], fill=HDR_BG)
    draw.text((3,2), "DARTS EVENTS", font=F7B, fill=YELLOW)
    draw.text((8,55), "No events.json found", font=F6, fill=GREY)
    return img

# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    dn       = Dartsnut()
    assets   = load_assets()
    params   = dn.widget_params if hasattr(dn,'widget_params') else {}
    show_pdc = params.get("show_pdc", True)
    show_wdf = params.get("show_wdf", True)

    events     = []
    last_load  = 0
    page_idx   = 0
    page_start = time.time()
    anim_t     = 0.0

    while dn.running:
        now     = time.time()
        elapsed = now - page_start
        anim_t += 0.05

        # reload data
        if now - last_load >= REFRESH_SEC or not events:
            fresh = load_events(show_pdc, show_wdf)
            if fresh: events = fresh
            last_load = now

        if not events:
            img = render_no_data(ImageDraw.Draw(Image.new("RGB",(W,H),BG)))
            dn.update_frame_buffer(img)
            time.sleep(1)
            continue

        # split: WM excluded, regular events only
        regular    = [e for e in events if not is_wm(e)]

        # pair up regular events
        pairs = [(regular[i], regular[i+1] if i+1 < len(regular) else None)
                 for i in range(0, min(len(regular), 10), 2)]   # max 5 pages

        total_pages = len(pairs)

        if elapsed >= PAGE_DUR:
            page_idx   = (page_idx + 1) % total_pages
            page_start = now
            elapsed    = 0

        ev1, ev2 = pairs[page_idx]
        m = date.fromisoformat(ev1["date_start"]).month
        y = date.fromisoformat(ev1["date_start"]).year
        label = f"{MONTHS_EN[m].upper()} {y}"
        frame = render_events_page(ev1, ev2, page_idx+1, total_pages, label)

        dn.update_frame_buffer(frame)
        time.sleep(0.05)

if __name__ == "__main__":
    main()
