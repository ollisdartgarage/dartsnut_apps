import time
import json
import os
from datetime import date
from PIL import Image, ImageDraw, ImageFont
from pydartsnut import Dartsnut

# ── Config ────────────────────────────────────────────────────────────────────
JSON_PATH    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "events.json")
REFRESH_SEC  = 3600
PAGE_DUR     = 3.0        # 3 sec per page → 5 pages = 15 sec total

# ── Colours ───────────────────────────────────────────────────────────────────
BG        = (0,   0,   0)
WHITE     = (255, 255, 255)
YELLOW    = (255, 215,   0)
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

F10B = load_font(BOLD,10)
F9B  = load_font(BOLD, 9)
F8B  = load_font(BOLD, 8)
F7B  = load_font(BOLD, 7)
F6B  = load_font(BOLD, 6)
F6   = load_font(REG,  6)

MONTHS_EN = ["","Jan","Feb","Mar","Apr","May","Jun",
             "Jul","Aug","Sep","Oct","Nov","Dec"]

# ── Helpers ───────────────────────────────────────────────────────────────────
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
        draw.rectangle([(0,div_y+1),(W-1,H-1)], fill=(5,5,20))
        draw.text((3, div_y+20), "Stay tuned...", font=F8B, fill=(50,50,80))

    return img

# ── No data screen ────────────────────────────────────────────────────────────
def render_no_data():
    img  = Image.new("RGB",(W,H),BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0,0),(W-1,HDR_H-1)], fill=HDR_BG)
    draw.text((3,2), "DARTS EVENTS", font=F7B, fill=YELLOW)
    draw.text((8,55), "No events.json found", font=F6, fill=GREY)
    return img

# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    dn       = Dartsnut()
    params   = dn.widget_params if hasattr(dn,'widget_params') else {}
    show_pdc = params.get("show_pdc", "true") != "false"
    show_wdf = params.get("show_wdf", "true") != "false"

    events     = []
    last_load  = 0
    page_idx   = 0
    page_start = time.time()

    while dn.running:
        now     = time.time()
        elapsed = now - page_start

        # reload data
        if now - last_load >= REFRESH_SEC or not events:
            fresh = load_events(show_pdc, show_wdf)
            if fresh: events = fresh
            last_load = now

        if not events:
            dn.update_frame_buffer(render_no_data())
            time.sleep(1)
            continue

        # pair up events
        pairs = [(events[i], events[i+1] if i+1 < len(events) else None)
                 for i in range(0, min(len(events), 10), 2)]   # max 5 pages

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
