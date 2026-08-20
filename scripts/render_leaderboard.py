"""
Renders the SALES LEADERBOARD PNG from the team/member data structure
produced by parse_hierarchy_grid.py. Same visual design as the manual
sales-leaderboard-daily skill; fonts are bundled in assets/fonts so this
doesn't depend on whatever fonts happen to be on the GitHub Actions runner.
"""
import os

import math

from PIL import Image, ImageDraw, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
BOLD = os.path.join(_HERE, "..", "assets", "fonts", "LiberationSans-Bold.ttf")
REG = os.path.join(_HERE, "..", "assets", "fonts", "LiberationSans-Regular.ttf")


def f(path, size):
    return ImageFont.truetype(path, size)


BG = "#f7f7f8"
W = 1080
PAD = 34
TRI = "#f59022"
ELI = "#e0303a"
GREEN = "#1a9c4c"
GREY = "#6b7280"


def _star_points(cx, cy, r_outer, r_inner, rotation_deg=-90):
    points = []
    for i in range(10):
        angle = math.radians(rotation_deg + i * 36)
        r = r_outer if i % 2 == 0 else r_inner
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return points


def render(data, out_path):
    def team_h(t):
        return 26 + 132 + len(t["members"]) * 78

    H = PAD + 150 + sum(team_h(t) for t in data["teams"]) + 70 + PAD
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    def center(txt, y, font, fill, cx=W // 2):
        w = d.textlength(txt, font=font)
        d.text((cx - w / 2, y), txt, font=font, fill=fill)

    center("SALES LEADERBOARD", PAD, f(BOLD, 62), "#1f2937")
    center(data["subtitle"], PAD + 78, f(BOLD, 26), "#64748b")
    d.polygon(_star_points(W - PAD - 22, PAD + 20, 26, 11), fill="#f0c020")
    center(data["date"], PAD + 114, f(REG, 19), "#94a3b8")

    y = PAD + 158
    BADGE = {1: "#f0c020", 2: "#c9ced6", 3: "#b06a28"}

    for t in data["teams"]:
        color = TRI if t["color"] == "tri" else ELI
        d.rounded_rectangle([PAD, y, W - PAD, y + 118], 18, fill=color)
        center(t["name"], y + 12, f(BOLD, 40), "#ffffff")
        center("TEAM TOTAL: ${:,.2f}".format(t["total"]), y + 58, f(BOLD, 24), "#ffffff")
        center("AVG $/WO: ${:,.2f}".format(t["avg_wo"]), y + 87, f(BOLD, 21), "#ffffff")
        y += 140
        mx = max([m["rev"] for m in t["members"]] + [0.01])
        for i, m in enumerate(t["members"], 1):
            d.rounded_rectangle([PAD, y, W - PAD, y + 68], 16, fill="#ffffff")
            bx = PAD + 18
            d.ellipse([bx, y + 15, bx + 38, y + 53], fill=BADGE.get(i, "#e5e7eb"))
            rt = str(i)
            rw = d.textlength(rt, font=f(BOLD, 20))
            d.text((bx + 19 - rw / 2, y + 23), rt, font=f(BOLD, 20),
                    fill="#374151" if i > 3 else "#ffffff")
            nx = bx + 56
            if m.get("office"):
                d.text((nx, y + 14), m["name"], font=f(BOLD, 21), fill="#1f2937")
                d.text((nx, y + 42), m["office"], font=f(BOLD, 15), fill="#9ca3af")
            else:
                d.text((nx, y + 24), m["name"], font=f(BOLD, 21), fill="#1f2937")
            tx0, tx1 = nx + 260, W - PAD - 175
            ty = y + 27
            d.rounded_rectangle([tx0, ty, tx1, ty + 16], 8, fill="#eceef1")
            frac = m["rev"] / mx
            if frac > 0:
                fw = max(16, (tx1 - tx0) * frac)
                d.rounded_rectangle([tx0, ty, tx0 + fw, ty + 16], 8, fill=color)
            amt = "${:,.2f}".format(m["rev"])
            aw = d.textlength(amt, font=f(BOLD, 22))
            d.text((W - PAD - 20 - aw, y + 22), amt, font=f(BOLD, 22),
                    fill=GREY if m["rev"] == 0 else GREEN)
            y += 78
        y += 10

    center("Ranked by Net Revenue • Keep grinding!", y + 12, f(BOLD, 19), "#94a3b8")
    img.save(out_path)
    return out_path
