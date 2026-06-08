import time
import math
import os
from datetime import date
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from pydartsnut import Dartsnut

# ── Config ────────────────────────────────────────────────────────────────────
WM_START  = "2026-12-10"
WM_END    = "2027-01-03"
TEST_LIVE = False    # set to False for normal countdown mode

# ── Colours — consistent with ODG EventsCalendar ─────────────────────────────
BG       = (0,   0,   0)
WHITE    = (255, 255, 255)
YELLOW   = (255, 215,   0)
GOLD     = (255, 190,   0)
GOLD_DIM = (160, 120,   0)
RED      = (220,  40,  40)
GREY     = (120, 120, 120)
LGREY    = (190, 190, 190)
PDC_COL  = ( 30, 120, 255)
LIVE_COL = (220,  40,  40)
HDR_BG   = ( 10,  10,  60)

W, H     = 128, 128
HDR_H    = 13
BAND_H   = 15

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

F32B = load_font(BOLD, 32)
F11B = load_font(BOLD, 11)
F10B = load_font(BOLD, 10)
F9B  = load_font(BOLD,  9)
F8B  = load_font(BOLD,  8)
F7B  = load_font(BOLD,  7)
F6B  = load_font(BOLD,  6)
F6   = load_font(REG,   6)

MONTHS_EN = ["","Jan","Feb","Mar","Apr","May","Jun",
             "Jul","Aug","Sep","Oct","Nov","Dec"]

# ── Assets ────────────────────────────────────────────────────────────────────
def load_assets():
    d = os.path.dirname(os.path.abspath(__file__))
    assets = {}
    for name, fname in [("trophy","trophy.png"),("bg","wm_bg_128.png")]:
        try:
            assets[name] = Image.open(os.path.join(d, fname)).convert("RGBA")
        except Exception:
            assets[name] = None
    return assets

# ── Logic ─────────────────────────────────────────────────────────────────────
def days_status():
    if TEST_LIVE:
        return 0, "LIVE"
    sd = date.fromisoformat(WM_START)
    ed = date.fromisoformat(WM_END)
    t  = date.today()
    if t > ed:   return None, None
    if t >= sd:  return 0, "LIVE"
    return (sd - t).days, "countdown"

# ── Renderer ──────────────────────────────────────────────────────────────────
def render(assets, anim_t):
    img  = Image.new("RGB", (W, H), BG)

    # dark bg image
    bg = assets.get("bg")
    if bg:
        overlay = Image.new("RGBA", bg.size, (0,0,0,200))
        comp = Image.alpha_composite(bg, overlay).convert("RGB")
        img.paste(comp, (0,0))

    draw = ImageDraw.Draw(img)
    days, status = days_status()

    # ── Header ────────────────────────────────────────────────────────────────
    draw.rectangle([(0,0),(W-1,HDR_H-1)], fill=HDR_BG)
    draw.text((3,2), "WC LONDON", font=F8B, fill=YELLOW)
    pg  = "PDC 2026"
    pgw = int(draw.textlength(pg, font=F6B))
    draw.text((W-pgw-2, 3), pg, font=F6B, fill=LGREY)

    # ── Banderole — same style as EventsCalendar ──────────────────────────────
    r1y = HDR_H + 3
    draw.rectangle([(0,r1y),(W-1,r1y+BAND_H-1)], fill=WHITE)
    bw = int(draw.textlength("PDC", font=F9B)) + 8
    draw.rectangle([(0,r1y),(bw,r1y+BAND_H-1)], fill=PDC_COL)
    draw.text((4,r1y+2), "PDC", font=F9B, fill=WHITE)

    sd = date.fromisoformat(WM_START)
    ed = date.fromisoformat(WM_END)
    date_str = f"{sd.day} {MONTHS_EN[sd.month]}-{ed.day} {MONTHS_EN[ed.month]}"
    draw.text((bw+5, r1y+2), date_str, font=F8B, fill=BG)

    # show LIVE in banderole when live, otherwise clean
    if status == "LIVE":
        sw = int(draw.textlength("● LIVE", font=F9B))
        draw.text((W-sw-4, r1y+2), "● LIVE", font=F9B, fill=LIVE_COL)
    # no countdown shown — displayed prominently below

    # ── Body layout start ─────────────────────────────────────────────────────
    ty0 = r1y + BAND_H + 4

    # ── Trophy as large centered background ──────────────────────────────────
    trophy = assets.get("trophy")
    body_top = r1y + BAND_H
    body_h   = H - body_top

    if trophy:
        # scale trophy to fill body height
        t_orig_w, t_orig_h = trophy.size
        scale    = body_h / t_orig_h
        t_new_w  = int(t_orig_w * scale)
        t_new_h  = body_h
        t_scaled = trophy.resize((t_new_w, t_new_h), Image.LANCZOS)

        # center horizontally
        tx = (W - t_new_w) // 2
        ty = body_top

        # pulsing glow only — no shimmer lines
        glow = 0.22 + 0.08 * math.sin(anim_t * 1.5)
        darkened = ImageEnhance.Brightness(t_scaled).enhance(glow)

        img_rgba = img.convert("RGBA")
        img_rgba.paste(darkened, (tx, ty), darkened)
        img  = img_rgba.convert("RGB")
        draw = ImageDraw.Draw(img)

    # ── WORLD DARTS CHAMPIONSHIP — redrawn over trophy bg ─────────────────────
    draw.text((3, ty0),    "WORLD",        font=F11B, fill=GOLD)
    draw.text((3, ty0+14), "DARTS",        font=F11B, fill=GOLD)
    draw.text((3, ty0+28), "CHAMPIONSHIPS", font=F9B,  fill=GOLD_DIM)

    # ── Venue left ────────────────────────────────────────────────────────────
    draw.text((3, ty0+44), "Alexandra",  font=F9B, fill=LGREY)
    draw.text((3, ty0+55), "Palace",     font=F9B, fill=LGREY)
    draw.text((3, ty0+67), "London",     font=F8B, fill=GREY)

    # ── Big countdown right-aligned ───────────────────────────────────────────
    if status == "LIVE":
        # red pulsing bottom bar
        pulse = int(40 + 20 * math.sin(anim_t * 2))
        draw.rectangle([(0,H-22),(W-1,H-1)], fill=(pulse+60, 5, 5))
        lw = int(draw.textlength("● LIVE NOW", font=F10B))
        draw.text(((W-lw)//2, H-19), "● LIVE NOW", font=F10B, fill=LIVE_COL)
    elif days is not None:
        cd_str = str(days)
        cd_col = RED if days <= 30 else GOLD
        cdw    = int(draw.textlength(cd_str, font=F32B))
        # right-aligned number
        num_x = W - cdw - 2
        draw.text((num_x, ty0+38), cd_str, font=F32B, fill=cd_col)
        # DAYS TO GO below number, right-aligned
        dw = int(draw.textlength("DAYS TO GO", font=F7B))
        draw.text((W - dw - 2, ty0+72), "DAYS TO GO", font=F7B, fill=LGREY)

    return img

# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    dn     = Dartsnut()
    assets = load_assets()
    anim_t = 0.0

    while dn.running:
        anim_t += 0.05
        dn.update_frame_buffer(render(assets, anim_t))
        time.sleep(0.05)

if __name__ == "__main__":
    main()
