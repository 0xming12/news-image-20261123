#!/usr/bin/env python3
"""Render the news-image-20261123 front page (1024x1024 PNG) with PIL.

Build tooling only: the submitted repo's main.ts copies the entry.png this
script produces. Deterministic: same fonts, same data, same PIL version ->
identical bytes. Run twice and compare sha256 before shipping.
"""
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))

W, H = 1024, 1024
PAPER = (248, 244, 234)
INK = (20, 28, 46)
NAVY = (15, 31, 61)
NAVY2 = (24, 46, 88)
RED = (176, 30, 40)
TEAL = (14, 122, 107)
BLUE = (31, 95, 168)
ORANGE = (201, 106, 30)
GREEN = (46, 125, 50)
BROWN = (141, 90, 43)
PURPLE = (106, 74, 158)
GOLD = (217, 164, 65)
GREY = (90, 96, 110)
LIGHT = (226, 232, 238)
TAN = (217, 201, 163)
TAN_D = (198, 178, 134)
WHITE = (255, 255, 255)
CREAM = (246, 241, 230)

F_DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F_DEJAVU_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
F_SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
F_SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
F_LIB = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
F_LIB_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def tw(draw, text, f):
    """Pixel width of text in font f."""
    b = draw.textbbox((0, 0), text, font=f)
    return b[2] - b[0]


def th(f):
    b = f.getbbox("Ag")
    return b[3] - b[1]


def wrap(draw, text, f, max_w):
    """Greedy word wrap to a list of lines fitting max_w."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if tw(draw, trial, f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_lines(draw, lines, x, y, f, fill, leading=None):
    """Draw lines top-left anchored; return y after last line."""
    if leading is None:
        leading = int(th(f) * 1.28)
    for ln in lines:
        draw.text((x, y), ln, font=f, fill=fill)
        y += leading
    return y


def pill(draw, x, y, text, f, bg, fg=WHITE, pad_x=5, h=13):
    """Small rounded date pill; returns width used."""
    w = tw(draw, text, f) + 2 * pad_x
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=bg)
    draw.text((x + pad_x, y + (h - th(f)) // 2 - 1), text, font=f, fill=fg)
    return w


def num_badge(draw, cx, cy, n, r, bg, f):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=bg)
    t = str(n)
    draw.text((cx - tw(draw, t, f) / 2, cy - th(f) / 2 - 1), t, font=f, fill=WHITE)


# ---------------------------------------------------------------- map
def load_land():
    with open(os.path.join(_HERE, "..", "countries.geo.json"), encoding="utf-8") as fh:
        gj = json.load(fh)
    polys = []
    for feat in gj["features"]:
        g = feat["geometry"]
        if g["type"] == "Polygon":
            polys.append(g["coordinates"])
        elif g["type"] == "MultiPolygon":
            polys.extend(g["coordinates"])
    return polys


def draw_map(draw, x0, y0, w, h, pins):
    """Equirectangular world map; pins = list of (lon, lat, n, color)."""
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(220, 232, 238))
    lon0, lon1 = -180.0, 180.0
    lat0, lat1 = -56.0, 78.0  # Antarctica cut off
    placed = []

    def proj(lon, lat):
        px = x0 + (lon - lon0) / (lon1 - lon0) * w
        py = y0 + (lat1 - lat) / (lat1 - lat0) * h
        return px, py

    for poly in load_land():
        for ring in poly:
            pts = [proj(lon, lat) for lon, lat in ring]
            if len(pts) >= 3:
                draw.polygon(pts, fill=TAN, outline=TAN_D)
    # graticule
    for lon in range(-150, 181, 30):
        px, _ = proj(lon, 0)
        draw.line([(px, y0), (px, y0 + h)], fill=(200, 214, 222), width=1)
    for lat in range(-45, 76, 15):
        _, py = proj(0, lat)
        draw.line([(x0, py), (x0 + w, py)], fill=(200, 214, 222), width=1)
    for lon, lat, n, color in pins:
        px, py = proj(lon, lat)
        # resolve collisions: nudge the bubble, keep a leader line to the spot
        cx, cy = px, py
        for dx, dy in [(0, 0), (13, -12), (-13, -12), (13, 12), (-13, 12),
                       (0, -17), (17, 0), (-17, 0), (0, 17)]:
            tx = min(max(px + dx, x0 + 9), x0 + w - 9)
            ty = min(max(py + dy, y0 + 9), y0 + h - 9)
            if all((tx - ox) ** 2 + (ty - oy) ** 2 >= 17 ** 2 for ox, oy in placed):
                cx, cy = tx, ty
                break
        placed.append((cx, cy))
        if (cx, cy) != (px, py):
            draw.line([(px, py), (cx, cy)], fill=(90, 96, 110), width=1)
        r = 8
        draw.ellipse([cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1], fill=WHITE)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        f = font(F_DEJAVU_B, 9)
        t = str(n)
        draw.text((cx - tw(draw, t, f) / 2, cy - 5), t, font=f, fill=WHITE)
    return proj


# ------------------------------------------------------- lead illustrations
def ill_climate(draw, x0, y0, w, h):
    """COP31: globe ringed by flag dots on deep teal."""
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(13, 74, 66))
    cx, cy, r = x0 + w // 2, y0 + h // 2 + 6, 34
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(46, 148, 132))
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(180, 225, 215), width=2)
    for k in range(5):
        yy = cy - r + (2 * r * k) // 4
        half = int(math.sqrt(max(r * r - (yy - cy) ** 2, 0)))
        draw.arc([cx - half, yy - 3, cx + half, yy + 3], 0, 360, fill=(180, 225, 215), width=1)
    draw.line([(cx, cy - r), (cx, cy + r)], fill=(180, 225, 215), width=1)
    draw.arc([cx - 12, cy - r, cx + 12, cy + r], 90, 270, fill=(180, 225, 215), width=1)
    draw.arc([cx - 12, cy - r, cx + 12, cy + r], 270, 90, fill=(180, 225, 215), width=1)
    flag_cols = [(176, 30, 40), (217, 164, 65), (31, 95, 168), (46, 125, 50),
                 (201, 106, 30), (106, 74, 158), (220, 220, 220), (14, 122, 107),
                 (176, 30, 40), (31, 95, 168), (217, 164, 65), (46, 125, 50)]
    for i, c in enumerate(flag_cols):
        ang = 2 * math.pi * i / len(flag_cols) - math.pi / 2
        px = cx + int(52 * math.cos(ang))
        py = cy + int(44 * math.sin(ang))
        draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=c, outline=WHITE, width=1)
    draw.text((x0 + 8, y0 + h - 20), "NO DEAL", font=font(F_DEJAVU_B, 11), fill=GOLD)


def ill_hormuz(draw, x0, y0, w, h):
    """Strait of Hormuz: tankers on dark water under missile arcs."""
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(16, 24, 48))
    for i in range(4):
        yy = y0 + 14 + i * 9
        draw.line([(x0 + 10, yy), (x0 + w - 10, yy)], fill=(52, 68, 96), width=1)
    # missile arcs (low, flat trajectories)
    for sx, ex, apex in [(x0 + 20, x0 + 120, 12), (x0 + 90, x0 + 200, 8), (x0 + 150, x0 + 235, 14)]:
        pts = []
        for t in range(21):
            u = t / 20.0
            px = sx + (ex - sx) * u
            py = y0 + h - 46 - apex * 4 * u * (1 - u) * 1.4
            pts.append((px, py))
        draw.line(pts, fill=(232, 140, 60), width=2)
        draw.ellipse([ex - 2, pts[-1][1] - 2, ex + 2, pts[-1][1] + 2], fill=(255, 200, 90))
    # sea
    draw.rectangle([x0, y0 + h - 34, x0 + w, y0 + h], fill=(24, 58, 92))
    draw.line([(x0, y0 + h - 34), (x0 + w, y0 + h - 34)], fill=(120, 170, 210), width=1)
    # tankers
    for tx, twd in [(x0 + 18, 52), (x0 + 96, 44), (x0 + 168, 58)]:
        ty = y0 + h - 30
        draw.rectangle([tx, ty, tx + twd, ty + 12], fill=(30, 32, 40))
        draw.rectangle([tx + twd - 14, ty - 9, tx + twd - 4, ty], fill=(200, 200, 200))
        draw.rectangle([tx, ty + 12, tx + twd, ty + 15], fill=(176, 30, 40))


def ill_nato(draw, x0, y0, w, h):
    """Poland missiles: trails over a skyline, compass star."""
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(30, 44, 72))
    # skyline
    base = y0 + h - 26
    for bx, bw, bh in [(0, 26, 22), (30, 18, 34), (52, 30, 16), (86, 16, 28),
                       (106, 26, 20), (136, 20, 36), (160, 30, 14), (194, 24, 26), (222, 20, 18)]:
        draw.rectangle([x0 + bx, base - bh, x0 + bx + bw, base], fill=(12, 20, 38))
        for wy in range(base - bh + 4, base - 2, 7):
            for wx in range(x0 + bx + 4, x0 + bx + bw - 3, 7):
                draw.rectangle([wx, wy, wx + 2, wy + 3], fill=(217, 164, 65))
    # missile trails
    for sx, ex, apex in [(x0 + 30, x0 + 90, 30), (x0 + 110, x0 + 170, 22), (x0 + 180, x0 + 230, 34)]:
        pts = []
        for t in range(21):
            u = t / 20.0
            px = sx + (ex - sx) * u
            py = base - 12 - apex * 4 * u * (1 - u) * 1.6
            pts.append((px, py))
        draw.line(pts, fill=(255, 255, 255), width=2)
        draw.ellipse([ex - 2, pts[-1][1] - 2, ex + 2, pts[-1][1] + 2], fill=(255, 220, 120))
    # compass star
    cx, cy = x0 + w - 26, y0 + 24
    star = []
    for i in range(8):
        ang = math.pi * i / 4 - math.pi / 2
        rr = 13 if i % 2 == 0 else 5
        star.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.polygon(star, fill=(140, 190, 230))
    draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=NAVY)


def ill_merkury(draw, x0, y0, w, h):
    """Benghazi: sinking corvette, blast, drone boats."""
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(14, 42, 74))
    for i in range(3):
        yy = y0 + 16 + i * 10
        draw.line([(x0 + 8, yy), (x0 + w - 8, yy)], fill=(44, 84, 124), width=1)
    sea_y = y0 + h - 40
    draw.rectangle([x0, sea_y, x0 + w, y0 + h], fill=(18, 68, 108))
    # blast
    bx, by = x0 + w // 2 + 18, sea_y - 26
    burst = []
    for i in range(16):
        ang = math.pi * i / 8
        rr = 26 if i % 2 == 0 else 12
        burst.append((bx + rr * math.cos(ang), by + rr * math.sin(ang)))
    draw.polygon(burst, fill=(232, 140, 60))
    draw.polygon(burst, outline=(255, 200, 90), width=2)
    for dx, dy, r in [(-16, -14, 7), (6, -20, 9), (22, -6, 6)]:
        draw.ellipse([bx + dx - r, by + dy - r, bx + dx + r, by + dy + r], fill=(120, 120, 130))
    # listing ship
    hx, hy = x0 + 26, sea_y - 2
    hull = [(hx, hy), (hx + 108, hy - 14), (hx + 128, hy - 6), (hx + 118, hy + 12), (hx + 8, hy + 12)]
    draw.polygon(hull, fill=(24, 26, 34))
    draw.rectangle([hx + 52, hy - 26, hx + 78, hy - 12], fill=(24, 26, 34))
    draw.rectangle([hx + 60, hy - 38, hx + 66, hy - 26], fill=(24, 26, 34))
    # drone boats
    for dx in [x0 + 150, x0 + 196]:
        dy = sea_y + 16
        draw.polygon([(dx, dy), (dx + 18, dy + 4), (dx, dy + 8)], fill=(220, 220, 220))
        draw.line([(dx, dy + 10), (dx + 26, dy + 12)], fill=(255, 255, 255), width=1)

# ------------------------------------------------------------------ data
# (headline: 1 line in region columns, <=36 chars; summary: <=3 lines,
#  <=95 chars. Leads: headline <=2 lines, summary <=126 chars.
#  Markets/sports: headline 1 line, summary 1 line.)
LEADS = [
    dict(tag="GLOBAL CLIMATE", date="22 NOV", color=TEAL, ill="climate",
         pin=(30.7, 36.9), pin_n=1,
         headline="COP31 Collapses in Antalya",
         summary="Longest-ever UN climate talks end with no deal as the EU and others reject a text that never names fossil fuels."),
    dict(tag="MIDDLE EAST", date="23 NOV", color=RED, ill="hormuz",
         pin=(56.5, 26.5), pin_n=2,
         headline="Iran Widens the War: Tankers Hit in Hormuz",
         summary="At least three tankers are attacked in the Strait of Hormuz; Iranian missiles hit a civilian site in Bahrain and US positions."),
    dict(tag="EUROPE", date="23 NOV", color=BLUE, ill="nato",
         pin=(4.35, 50.85), pin_n=3,
         headline="NATO Meets in Emergency Over Poland Missiles",
         summary="NATO's council meets in Brussels after three Russian Kh-101 missiles crashed in south-east Poland on Friday."),
    dict(tag="AFRICA · LIBYA", date="23 NOV", color=BROWN, ill="merkury",
         pin=(20.1, 32.1), pin_n=4,
         headline="Ukraine Sinks Russian Warship off Libya",
         summary="Seven sea drones sink the corvette Merkury at Benghazi and hit the arms ship MV Angara, 2,400 km away."),
]

MARKETS = [
    ("Nvidia Reinstates Huang as CEO",
     "Shares jump 31% premarket on the reversal.", "23 Nov"),
    ("Wall Street Rebounds After AI Rout",
     "Futures rally after Friday's sell-off put the S&P in correction.", "23 Nov"),
    ("CrowdStrike to Buy Zscaler for $43.9B",
     "Rivals combine in an all-stock deal; Zscaler jumps 17%.", "23 Nov"),
    ("Bitcoin Tops $61,000; Gold Near $3,600",
     "Crypto and bullion bounce with stocks as risk appetite returns.", "23 Nov"),
]

SPORTS = [
    ("NZ Hold India to Draw; Australia Up to 2nd",
     "NZ's rearguard saves the Wellington Test; Australia up to 2nd.", "22 Nov"),
    ("Giddey's 22-Assist Triple-Double in Vain",
     "Giddey posts 23-14-22, a historic line, but Chicago fall in OT.", "22 Nov"),
    ("Cowboys 51, Titans 30 — a First",
     "Prescott's five TDs power the NFL's first 51-30 final.", "22 Nov"),
]

# (n, headline, summary, date, pin lon/lat or None)
COLUMNS = [
    ("MIDDLE EAST & GULF", RED, [
        (12, "Iran Strike Hits Bahrain Site",
         "Missiles hit a civilian industrial site, hurting two; air defences intercept the rest.", "21 Nov", (50.6, 26.2)),
        (13, "Gaza Truck Strike Kills 3",
         "Israeli strike on a truck kills three; Eisenkot calls settler arson 'Jewish terrorism'.", "22 Nov", (34.45, 31.5)),
        (14, "US to Train Syrian Forces",
         "Washington weighs a first training mission since rebels took power in Damascus in 2024.", "23 Nov", None),
        (15, "Gulf Stocks Rise on Diplomacy",
         "Saudi, Qatar and Dubai indexes climb as diplomacy steadies markets after days of strikes.", "23 Nov", None),
        (16, "Red Sea Talks at Aswan Forum",
         "Egypt, Sudan and Eritrea say Red Sea security is for littoral states, warning on foreign build-up.", "21 Nov", None),
    ]),
    ("EUROPE", BLUE, [
        (17, "Freighter Ablaze in Baltic",
         "The Sparta II catches fire and drifts into Finnish waters after a suspected Ukrainian attack.", "22 Nov", (20.0, 58.0)),
        (18, "Denmark Expels Attaché",
         "Copenhagen blames Russian intelligence for a plot to kill US-Ukrainian rapper Kyivstoner.", "20 Nov", (12.57, 55.68)),
        (19, "Puigdemont Free to Return",
         "The Supreme Court shelves the case against the Catalan ex-leader after nearly a decade in exile.", "23 Nov", (-3.7, 40.4)),
        (20, "Drone Strike: 14 Missing",
         "A Russian drone partly destroys a block near Kyiv; nine are out, others may be trapped.", "22 Nov", (30.5, 50.45)),
        (21, "Kryvyi Rih Strikes Kill Two",
         "Overnight attacks kill a child and a young woman and damage 25 apartment blocks and a hospital.", "21 Nov", (33.4, 47.9)),
    ]),
    ("THE AMERICAS", ORANGE, [
        (22, "Democrats' 258-Seat House Win",
         "Their biggest House majority since 1992 sets up a test of Trump's oversight limits.", "23 Nov", (-77.0, 38.9)),
        (23, "'El Chapo Isidro' Captured",
         "Troops arrest cartel chief Meza Flores in Sinaloa; the FBI most-wanted man had a $5m bounty.", "20 Nov", (-107.4, 24.8)),
        (24, "Penny's 232-Year Run Ends",
         "Trump signs the Common Cents Act, ending penny production; cash rounds to the nearest 5 cents.", "20 Nov", None),
        (25, "Delta Delays 1,600+ Flights",
         "A systems failure snarls Atlanta as Thanksgiving travel starts; half of Delta's flights run late.", "22 Nov", None),
        (26, "US Growth Hits Four-Month Low",
         "S&P Global's flash PMI slips to 54.6 as high prices curb orders; activity stays above trend.", "23 Nov", None),
        (27, "Braskem Agrees Creditor Deal",
         "The petrochemical firm reaches agreement on an out-of-court restructuring plan, sources say.", "23 Nov", (-46.6, -23.5)),
    ]),
    ("ASIA-PACIFIC", GREEN, [
        (28, "Indonesia Fire: 24 Dead",
         "The toll is confirmed Monday after a blaze tore through a Banten confectionery plant on Saturday.", "23 Nov", (106.8, -6.2)),
        (29, "Seoul Minister Quits",
         "Education chief Choi quits after last-minute anti-cheating rules sowed chaos at the entrance exam.", "22 Nov", (127.0, 37.5)),
        (30, "Asian Chip Stocks Slide",
         "Kospi closes down 3.3%, Samsung -3.1% and SK Hynix -2.5%, as doubts over AI spending spread.", "23 Nov", None),
        (31, "Hasina to Be Jailed on Return",
         "Bangladesh says it will arrest and jail the ex-premier if she comes back from exile.", "23 Nov", (90.4, 23.8)),
        (32, "Nvidia Affair Tied to Spies",
         "Alice Huang kept contact with Chinese intelligence during her affair with Huang, NYT reports.", "23 Nov", None),
        (33, "Wong Warns on China Rivalry",
         "Australia's foreign minister says great-power competition is making the world more dangerous.", "23 Nov", (174.8, -41.3)),
    ]),
    ("AFRICA", BROWN, [
        (34, "Congo Halts Cobalt Exports",
         "The world's top producer suspends exports from 30 November to tackle oversupply and weak prices.", "23 Nov", (15.3, -4.3)),
        (35, "Kenya, DR Congo Restore Ties",
         "Ruto and Tshisekedi agree to restore full diplomatic ties after nearly three years of tension.", "22 Nov", None),
        (36, "Ethiopia Polio Drive for 11M",
         "A nationwide vaccination campaign aims to protect more than 11 million children.", "23 Nov", None),
        (37, "Sudan Strikes Kill Civilians",
         "Drone strikes kill at least four, including a child, and damage a UN building in Khartoum.", "23 Nov", None),
    ]),
]

TIMELINE = [
    ("FRI 20 NOV", "Penny signed · 'El Chapo' held · Denmark expels"),
    ("SAT 21 NOV", "Indonesia fire · Kryvyi Rih hit · Bahrain struck"),
    ("SUN 22 NOV", "COP31 collapses · Merkury sunk · Delta outage"),
    ("MON 23 NOV", "NATO meets · Nvidia back · Markets rebound"),
]

FOOTER = [
    ("3 MISSILES", "Kh-101s over Poland"),
    ("$43.9B", "CrowdStrike–Zscaler deal"),
    ("+31%", "Nvidia on Huang's return"),
    ("24 DEAD", "Indonesia factory fire"),
    ("258 SEATS", "Democrats' House haul"),
    ("37 STORIES", "7 regions · 23 Nov 2026"),
]

SOURCES_LINE = "Sources: Reuters · AP · CNN · Wall Street Journal · Al Jazeera · ABC Australia · S&P Global · ICC · PANA · SANA"
TOTAL_STORIES = 4 + len(MARKETS) + len(SPORTS) + sum(len(c[2]) for c in COLUMNS)


# ------------------------------------------------------------------ layout
def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    f_title = font(F_SERIF_B, 46)
    f_mast_l = font(F_DEJAVU_B, 12)
    f_mast_s = font(F_DEJAVU_B, 10)
    f_banner = font(F_DEJAVU_B, 17)
    f_banner_s = font(F_DEJAVU_B, 10)
    f_tag = font(F_DEJAVU_B, 10)
    f_lead_h = font(F_DEJAVU_B, 14)
    f_lead_b = font(F_DEJAVU, 11)
    f_sec = font(F_DEJAVU_B, 10)
    f_h = font(F_LIB_B, 11)
    f_b = font(F_LIB, 10)
    f_ms_h = font(F_DEJAVU_B, 11)
    f_ms_b = font(F_DEJAVU, 10)
    f_sp_h = font(F_DEJAVU_B, 11)
    f_sp_b = font(F_DEJAVU, 9)
    f_pill = font(F_DEJAVU_B, 8)
    f_tl = font(F_DEJAVU_B, 10)
    f_tlb = font(F_DEJAVU, 9)
    f_foot_n = font(F_DEJAVU_B, 19)
    f_foot_l = font(F_DEJAVU, 9)
    f_src = font(F_DEJAVU, 9)

    # --- masthead
    d.rectangle([0, 0, W, 4], fill=RED)
    d.line([(8, 66), (1016, 66)], fill=INK, width=1)
    d.text((8, 14), "ONE DAY IN WORLD NEWS", font=f_mast_l, fill=RED)
    d.text((8, 34), f"7 REGIONS · {TOTAL_STORIES} UNIQUE DATED STORIES", font=f_mast_s, fill=NAVY)
    title = "THE WORLD TODAY"
    d.text(((W - tw(d, title, f_title)) / 2, 8), title, font=f_title, fill=NAVY)
    r1 = "ILLUSTRATED GLOBAL BROADSHEET"
    r2 = "ALL EVENTS · 23 NOV 2026"
    d.text((1016 - tw(d, r1, f_mast_s), 16), r1, font=f_mast_s, fill=NAVY)
    d.text((1016 - tw(d, r2, f_mast_s), 34), r2, font=f_mast_s, fill=GREY)

    # --- navy date banner
    d.rectangle([8, 68, 1016, 100], fill=NAVY)
    d.rounded_rectangle([14, 74, 132, 94], radius=3, fill=RED)
    d.text((20, 78), "MONDAY EDITION", font=f_banner_s, fill=WHITE)
    bt = "MONDAY, 23 NOVEMBER 2026"
    d.text(((W - tw(d, bt, f_banner)) / 2, 74), bt, font=f_banner, fill=WHITE)
    cities = "ANTALYA · HORMUZ · BRUSSELS · BENGHAZI · NEW YORK"
    d.text((1016 - tw(d, cities, f_banner_s) - 8, 79), cities, font=f_banner_s, fill=GOLD)

    # --- lead cards
    cw, gap = 247, 6
    for i, lead in enumerate(LEADS):
        x0 = 8 + i * (cw + gap)
        x1 = x0 + cw
        d.rectangle([x0, 104, x1, 328], fill=WHITE, outline=(200, 200, 190), width=1)
        ill = {"climate": ill_climate, "hormuz": ill_hormuz,
               "nato": ill_nato, "merkury": ill_merkury}[lead["ill"]]
        ill(d, x0 + 1, 105, cw - 2, 100)
        d.rectangle([x0 + 1, 205, x1 - 1, 223], fill=lead["color"])
        tag = f"{lead['tag']} · {lead['date']}"
        d.text((x0 + 8, 209), tag, font=f_tag, fill=WHITE)
        hl = wrap(d, lead["headline"], f_lead_h, cw - 16)
        y = draw_lines(d, hl[:2], x0 + 8, 228, f_lead_h, INK, leading=17)
        bl = wrap(d, lead["summary"], f_lead_b, cw - 16)
        draw_lines(d, bl[:3], x0 + 8, y + 3, f_lead_b, (40, 44, 58), leading=13)
        if len(hl) > 2 or len(bl) > 3:
            print(f"WARN lead {i+1}: headline {len(hl)} lines / summary {len(bl)} lines")

    # --- timeline strip
    d.rectangle([8, 332, 1016, 362], fill=(238, 232, 216), outline=(200, 200, 190), width=1)
    col_w = (1008 - 24) / 4
    for i, (day, beats) in enumerate(TIMELINE):
        cx = 16 + i * col_w
        d.text((cx, 336), day, font=f_tl, fill=RED)
        d.text((cx, 349), beats, font=f_tlb, fill=INK)

    # --- map panel
    d.rectangle([8, 366, 612, 556], fill=WHITE, outline=(200, 200, 190), width=1)
    d.rectangle([8, 366, 612, 384], fill=NAVY)
    d.text((16, 370), "GLOBAL DISPATCH MAP · 19 HOTSPOTS", font=f_sec, fill=WHITE)
    pins = []
    for lead in LEADS:
        pins.append((lead["pin"][0], lead["pin"][1], lead["pin_n"], lead["color"]))
    region_of = {}
    for name, color, stories in COLUMNS:
        for (n, _h, _s, _dt, pin) in stories:
            region_of[n] = color
            if pin:
                pins.append((pin[0], pin[1], n, color))
    pins.sort(key=lambda p: p[2])
    assert len(pins) == 19, f"pins={len(pins)}"
    draw_map(d, 9, 385, 602, 132, pins)
    # legend
    lx = 16
    ly = 524
    for label, color in [("Climate", TEAL), ("Mideast", RED), ("Europe", BLUE),
                         ("Americas", ORANGE), ("Asia-Pacific", GREEN),
                         ("Africa", BROWN), ("Sports", PURPLE)]:
        d.ellipse([lx, ly + 2, lx + 8, ly + 10], fill=color)
        d.text((lx + 12, ly), label, font=f_src, fill=INK)
        lx += 12 + tw(d, label, f_src) + 14
    d.text((612 - tw(d, "Numbers match story numbers", f_src) - 8, ly),
           "Numbers match story numbers", font=f_src, fill=GREY)

    # --- markets + sports (right column)
    rx0, rx1 = 618, 1016
    d.rectangle([rx0, 366, rx1, 480], fill=WHITE, outline=(200, 200, 190), width=1)
    d.rectangle([rx0, 366, rx1, 384], fill=NAVY)
    d.text((rx0 + 8, 370), "GLOBAL MARKETS · TECH — 4 STORIES", font=f_sec, fill=WHITE)
    y = 388
    for headline, summary, date in MARKETS:
        hl = wrap(d, headline, f_ms_h, rx1 - rx0 - 16)
        d.text((rx0 + 8, y), hl[0], font=f_ms_h, fill=INK)
        d.text((rx0 + 8, y + 13), summary, font=f_ms_b, fill=(40, 44, 58))
        pw = pill(d, rx1 - tw(d, date, f_pill) - 10 - 8, y, date, f_pill, RED)
        y += 23
        if len(hl) > 1 or tw(d, summary, f_ms_b) + 6 + pw > rx1 - rx0 - 16:
            print(f"WARN market: {headline!r} wraps/overflows")
    d.rectangle([rx0, 486, rx1, 556], fill=WHITE, outline=(200, 200, 190), width=1)
    d.rectangle([rx0, 486, rx1, 502], fill=NAVY)
    d.text((rx0 + 8, 490), "OCEANIA & SPORTS — 3 STORIES", font=f_sec, fill=WHITE)
    y = 506
    for headline, summary, date in SPORTS:
        hl = wrap(d, headline, f_sp_h, rx1 - rx0 - 16)
        d.text((rx0 + 8, y), hl[0], font=f_sp_h, fill=INK)
        d.text((rx0 + 8, y + 12), summary, font=f_sp_b, fill=(40, 44, 58))
        pw = pill(d, rx1 - tw(d, date, f_pill) - 10 - 8, y, date, f_pill, PURPLE)
        y += 17
        if len(hl) > 1 or tw(d, summary, f_sp_b) + 6 + pw > rx1 - rx0 - 16:
            print(f"WARN sport: {headline!r} wraps/overflows")

    # --- region grid
    grid_y0, grid_y1 = 562, 952
    col_w2 = (1008 - 4 * 6) / 5
    for ci, (name, color, stories) in enumerate(COLUMNS):
        x0 = 8 + ci * (col_w2 + 6)
        x1 = x0 + col_w2
        d.rectangle([x0, grid_y0, x1, grid_y0 + 20], fill=color)
        hdr = f"{name} — {len(stories)} STORIES"
        d.text((x0 + 6, grid_y0 + 4), hdr, font=f_sec, fill=WHITE)
        n = len(stories)
        slots = n + 1 if name == "AFRICA" else n
        slot = (grid_y1 - grid_y0 - 20) / slots
        for si, (num, headline, summary, date, _pin) in enumerate(stories):
            sy = grid_y0 + 20 + si * slot
            # badge
            num_badge(d, x0 + 9, sy + 8, num, 8, color, font(F_DEJAVU_B, 8))
            tx = x0 + 21
            twd = x1 - tx - 4
            hl = wrap(d, headline, f_h, twd)
            yy = draw_lines(d, hl[:1], tx, sy + 1, f_h, INK, leading=13)
            bl = wrap(d, summary, f_b, twd)
            last_y = yy + 1 + (len(bl[:3]) - 1) * 12
            draw_lines(d, bl[:3], tx, yy + 1, f_b, (40, 44, 58), leading=12)
            # date pill: inline after the last summary line when it fits
            pw = tw(d, date, f_pill) + 10
            last_w = tw(d, bl[-1] if bl else "", f_b) if bl else 0
            if len(bl) <= 3 and last_w + 6 + pw <= twd:
                pill(d, tx + last_w + 6, last_y, date, f_pill, RED)
            else:
                pill(d, tx, last_y + 13, date, f_pill, RED)
            if len(hl) > 1 or len(bl) > 3:
                print(f"WARN story {num}: headline {len(hl)} lines / summary {len(bl)} lines")
        if name == "AFRICA":
            # brief box fills the 5th slot under the 4 stories
            by = grid_y0 + 20 + 4 * slot + 3
            d.rounded_rectangle([x0, by, x1, grid_y1 - 2], radius=4,
                                fill=(238, 232, 216), outline=(200, 200, 190))
            d.text((x0 + 6, by + 4), "AFRICA IN BRIEF", font=f_sec, fill=BROWN)
            brief = ["DRC is the world's No. 1 cobalt producer.",
                     "Polio drive targets 11M+ children.",
                     "Kenya–DRC ties restored after ~3 years."]
            yy = by + 20
            for line in brief:
                for ln in wrap(d, "· " + line, f_b, x1 - x0 - 12):
                    d.text((x0 + 6, yy), ln, font=f_b, fill=INK)
                    yy += 12

    # --- sources + footer
    d.text(((W - tw(d, SOURCES_LINE, f_src)) / 2, 954), SOURCES_LINE, font=f_src, fill=GREY)
    d.rectangle([8, 966, 1016, 1014], fill=NAVY)
    fw = 1008 / 6
    for i, (num, label) in enumerate(FOOTER):
        cx = 8 + i * fw
        d.text((cx + (fw - tw(d, num, f_foot_n)) / 2, 972), num, font=f_foot_n, fill=GOLD)
        d.text((cx + (fw - tw(d, label, f_foot_l)) / 2, 996), label, font=f_foot_l, fill=WHITE)
        if i:
            d.line([(cx, 972), (cx, 1008)], fill=(60, 76, 110), width=1)

    img.save("entry.png", "PNG", optimize=True)
    print("saved entry.png")


if __name__ == "__main__":
    main()
