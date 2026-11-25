"""Build the deck as a native PowerPoint file: real text, real titles, vector shapes.

Usage: python make_pptx.py            (after build.py has written data.json)
Only the two product screenshots (dashboard and Google Sheet) are pictures; everything else is shapes and text.
Layout is drawn on a 1920x1080 grid (1 px = 6350 EMU = 0.5 pt).
"""
import json, math
from pathlib import Path
from PIL import ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

HERE = Path(__file__).parent
D = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
FONTS = next((d for d in (Path.home() / "AppData/Local/Microsoft/Windows/Fonts", Path("C:/Windows/Fonts")) if (d / "Inter-Bold.ttf").exists()), None)
if FONTS is None:
    raise SystemExit("Inter-Regular.ttf / Inter-Bold.ttf not found; install Inter to measure text")
_fc = {}


def font(size, bold=False):
    key = (round(size, 1), bold)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(str(FONTS / ("Inter-Bold.ttf" if bold else "Inter-Regular.ttf")), max(1, round(size)))
    return _fc[key]


def measure(text, size, bold=False):
    return font(size, bold).getlength(text)


def wrap(text, size, width, bold=False):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if measure(t, size, bold) <= width or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    return lines


E = lambda v: Emu(int(round(v * 6350)))
rgb = lambda h: RGBColor.from_string(h.lstrip("#").upper())
fmt = lambda n: f"{int(n):,}"
pct = lambda a, b: round(100 * a / b)

LIGHT = dict(bg="FFFFFF", tx="37352F", tx2="787774", tx3="A19F9A", div="EDEDEC", side="F8F8F7", hov="EFEFEE", call="F1F1EF", blue="2383E2")
DARK = dict(bg="191919", tx="E3E2E0", tx2="9B9A97", tx3="6F6E69", div="2F2F2F", side="202020", hov="2C2C2C", call="262626", blue="529CCA")
TAGS = {"gray": ("E9E9E7", "5F5E5B"), "green": ("DBEDDB", "2B593F"), "blue": ("D3E5EF", "28456C"), "yellow": ("FDECC8", "6C4B13"),
        "purple": ("E8DEEE", "492F64"), "red": ("FFE2DD", "73251B"), "orange": ("FADEC9", "6C3A0F")}
DTAGS = {"gray": ("373737", "D4D4D4"), "green": ("2B593F", "DBEDDB"), "blue": ("28456C", "D3E5EF"), "yellow": ("6C4B13", "FDECC8"), "orange": ("6C3A0F", "FADEC9")}
BAND = {"Call now": "green", "Call this week": "yellow", "Nurture": "gray"}
LAB = {"ready_to_buy": "green", "evaluating": "blue", "not_now": "yellow", "wrong_contact": "purple", "not_interested": "gray"}
PAGES = [("Overview", "target", "2383E2"), ("The problem", "alert", "E03E3E"), ("What paying teams share", "chart", "2383E2"),
         ("Scoring rules", "list", "2383E2"), ("Does it work", "check", "0F7B6C"), ("Reply labels", "mail", "9065B0"),
         ("Ranked call list", "table", "0F7B6C"), ("Dashboard", "monitor", "2383E2"), ("Live demo", "play", "2383E2"),
         ("Key insights", "bulb", "DFAB01"), ("What's next", "flag", "0F7B6C")]
SRC = f"Source: Q3 2026 Flagged Free Workspaces with Conversion Outcomes, {fmt(D['total'])} accounts."


class Slide:
    def __init__(self, prs, layout, dark=False):
        self.s = prs.slides.add_slide(prs.slide_layouts[layout])
        self.c = DARK if dark else LIGHT
        self.dark = dark
        self.sh = self.s.shapes
        bg = self.s.background.fill; bg.solid(); bg.fore_color.rgb = rgb(self.c["bg"])

    # ---- primitives -------------------------------------------------------
    def rect(self, x, y, w, h, fill=None, line=None, radius=0, lw=1):
        shp = self.sh.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, E(x), E(y), E(w), E(h))
        if radius:
            shp.adjustments[0] = min(0.5, radius / min(w, h))
        if fill:
            shp.fill.solid(); shp.fill.fore_color.rgb = rgb(fill)
        else:
            shp.fill.background()
        if line:
            shp.line.color.rgb = rgb(line); shp.line.width = Pt(lw * 0.5)
        else:
            shp.line.fill.background()
        shp.shadow.inherit = False
        return shp

    def oval(self, cx, cy, r, fill=None, line=None, lw=1):
        shp = self.sh.add_shape(MSO_SHAPE.OVAL, E(cx - r), E(cy - r), E(2 * r), E(2 * r))
        if fill:
            shp.fill.solid(); shp.fill.fore_color.rgb = rgb(fill)
        else:
            shp.fill.background()
        if line:
            shp.line.color.rgb = rgb(line); shp.line.width = Pt(lw * 0.5)
        else:
            shp.line.fill.background()
        shp.shadow.inherit = False
        return shp

    def line(self, x1, y1, x2, y2, color, lw=1):
        c = self.sh.add_connector(MSO_CONNECTOR.STRAIGHT, E(x1), E(y1), E(x2), E(y2))
        c.line.color.rgb = rgb(color); c.line.width = Pt(lw * 0.5)
        return c

    def poly(self, pts, color, lw=1, closed=False, fill=None):
        """Polyline or polygon in px."""
        b = self.sh.build_freeform(E(pts[0][0]), E(pts[0][1]), scale=1.0)
        b.add_line_segments([(E(x), E(y)) for x, y in pts[1:]], close=closed)
        shp = b.convert_to_shape()
        if fill:
            shp.fill.solid(); shp.fill.fore_color.rgb = rgb(fill)
        else:
            shp.fill.background()
        if color:
            shp.line.color.rgb = rgb(color); shp.line.width = Pt(lw * 0.5)
        else:
            shp.line.fill.background()
        shp.shadow.inherit = False
        return shp

    def text(self, x, y, w, h, runs, size=22, color=None, bold=False, align="l", spacing=1.25, anchor="t", font_name="Inter"):
        """runs: str, or list of paragraphs, each a list of (text, {opts}) or a str."""
        n_par = 1 if isinstance(runs, str) else len(runs)
        need = max(size, max((o.get("size", size) for para in ([runs] if isinstance(runs, str) else runs) for seg in ([para] if isinstance(para, str) else para) for o in [seg[1] if isinstance(seg, tuple) else {}]), default=size))
        need = need * 1.42 * (len(wrap(runs, size, w, bold)) if isinstance(runs, str) else n_par)
        if h < need:
            y -= (need - h) / 2 if anchor == "m" else (need - h if anchor == "b" else 0)
            h = need
        tb = self.sh.add_textbox(E(x), E(y), E(w), E(h))
        tf = tb.text_frame
        tf.word_wrap = True; tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
        paras = [runs] if isinstance(runs, str) else runs
        for i, para in enumerate(paras):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
            p.line_spacing = spacing
            for seg in ([para] if isinstance(para, str) else para):
                t, o = (seg, {}) if isinstance(seg, str) else seg
                r = p.add_run(); r.text = t
                f = r.font; f.name = o.get("font", font_name); f.size = Pt(o.get("size", size) * 0.5)
                f.bold = o.get("bold", bold); f.color.rgb = rgb(o.get("color", color or self.c["tx"]))
                if o.get("strike"):
                    r._r.get_or_add_rPr().set("strike", "sngStrike")
                if o.get("link"):
                    r.hyperlink.address = o["link"]
        return tb

    def tag(self, x, y, label, kind="gray", size=19, dot=False):
        bgc, fg = (DTAGS if self.dark else TAGS)[kind]
        h = size * 1.5
        tw = measure(label, size) + (size * 0.9 if dot else 0)
        w = tw + size * 1.05
        self.rect(x, y, w, h, fill=bgc, radius=size * 0.32)
        tx = x + size * 0.52
        if dot:
            self.oval(tx + size * 0.24, y + h / 2, size * 0.22, fill=fg)
            tx += size * 0.9
        self.text(tx, y, tw + 8, h, label, size=size, color=fg, anchor="m", spacing=1.0)
        return w

    # ---- icons, drawn on a 24-unit grid -------------------------------------
    def icon(self, kind, x, y, size, color, lw=1.7):
        s = size / 24
        P = lambda *pts: [(x + a * s, y + b * s) for a, b in pts]
        L = lambda a, b, c, d: self.line(x + a * s, y + b * s, x + c * s, y + d * s, color, lw * s)
        O = lambda cx, cy, r, fill=None: self.oval(x + cx * s, y + cy * s, r * s, fill=fill, line=None if fill else color, lw=lw * s)
        R = lambda a, b, w, h, rad=2: self.rect(x + a * s, y + b * s, w * s, h * s, line=color, lw=lw * s, radius=rad * s)
        W = lambda pts, closed=False: self.poly(P(*pts), color, lw * s, closed)
        if kind == "target": O(12, 12, 9); O(12, 12, 5); O(12, 12, 1.4, fill=color)
        elif kind == "alert": W([(12, 3), (21.5, 20), (2.5, 20)], True); L(12, 9.5, 12, 14); O(12, 17, 0.9, fill=color)
        elif kind == "chart": W([(4, 4), (4, 20), (20, 20)]); L(8, 16, 8, 12); L(12, 16, 12, 8); L(16, 16, 16, 10)
        elif kind == "list":
            for yy in (6, 12, 18): O(4.5, yy, 1.1, fill=color); L(9, yy, 20, yy)
        elif kind == "check": O(12, 12, 9); W([(8, 12.5), (10.7, 15.2), (16.5, 9.3)])
        elif kind == "mail": R(3, 5, 18, 14); W([(3.6, 6.2), (12, 13), (20.4, 6.2)])
        elif kind in ("table", "sheet"): R(3, 4, 18, 16); L(3, 10, 21, 10); L(3, 15, 21, 15); L(10, 4, 10, 20)
        elif kind == "monitor": R(3, 4, 18, 12); L(8, 20, 16, 20); L(12, 16, 12, 20)
        elif kind == "play": O(12, 12, 9); W([(10, 8.5), (15.5, 12), (10, 15.5)], True)
        elif kind == "bulb": O(12, 9.5, 6); L(9.5, 15, 9.5, 17.5); L(14.5, 15, 14.5, 17.5); L(9, 18.2, 15, 18.2); L(10, 21, 14, 21)
        elif kind == "flag": L(5, 21, 5, 4); W([(5, 4), (16, 4), (14, 8), (16, 12), (5, 12)])
        elif kind == "search": O(11, 11, 6.5); L(15.8, 15.8, 20, 20)
        elif kind == "home": W([(4, 11), (12, 4), (20, 11), (20, 20), (4, 20)], True)
        elif kind == "inbox": W([(4, 13), (6.5, 5), (17.5, 5), (20, 13), (20, 19), (4, 19)], True); W([(4, 13), (9, 13), (10, 15), (14, 15), (15, 13), (20, 13)])
        elif kind == "people": O(9, 8, 3.5); W([(3, 20), (4.2, 16.6), (9, 14.2), (13.8, 16.6), (15, 20)]); W([(16, 4.6), (18.6, 6.3), (18.6, 9.7), (16, 11.4)])
        elif kind == "cal": R(3, 5, 18, 16); L(3, 10, 21, 10); L(8, 3, 8, 7); L(16, 3, 16, 7)
        elif kind == "hash": L(5, 9, 19, 9); L(5, 15, 19, 15); L(10, 4, 8, 20); L(16, 4, 14, 20)
        elif kind == "status": O(12, 12, 8); O(12, 12, 3, fill=color)
        elif kind == "board": R(3, 4, 5, 16, 1.5); R(10, 4, 5, 10, 1.5); R(17, 4, 4, 13, 1.5)
        elif kind == "link": R(2.5, 8.5, 11, 7, 3.5); R(10.5, 8.5, 11, 7, 3.5)
        elif kind == "filter": L(4, 6, 20, 6); L(7, 12, 17, 12); L(10, 18, 14, 18)
        elif kind == "aa": self.text(x, y, size * 1.6, size, "Aa", size=size * 0.8, color=color, bold=True, anchor="m")

    def callout(self, x, y, w, h, icon, icolor, paras, size=21, pad=24):
        self.rect(x, y, w, h, fill=self.c["call"], radius=10)
        self.icon(icon, x + pad, y + pad - 2, size * 1.5, icolor)
        self.text(x + pad + size * 2.2, y + pad - 3, w - pad * 2 - size * 2.2, h - pad, paras, size=size, spacing=1.35)

    def dots(self, x, y, w, order, color_of, r_frac=0.33):
        """1,200 accounts as a 48-column dot grid; one vector shape per colour."""
        cols, step = 48, w / 48
        groups = {}
        for g in D["grid"]:
            i = g[order]
            groups.setdefault(color_of(g), []).append((x + (i % cols) * step + step / 2, y + (i // cols) * step + step / 2))
        r = step * r_frac
        ring = [(math.cos(2 * math.pi * k / 12), math.sin(2 * math.pi * k / 12)) for k in range(12)]
        for colr, centres in groups.items():
            first = centres[0]
            b = self.sh.build_freeform(E(first[0] + r), E(first[1]), scale=1.0)
            for j, (cx, cy) in enumerate(centres):
                if j:
                    b.move_to(E(cx + r), E(cy))
                b.add_line_segments([(E(cx + r * a), E(cy + r * bb)) for a, bb in ring[1:]], close=True)
            shp = b.convert_to_shape()
            shp.fill.solid(); shp.fill.fore_color.rgb = rgb(colr); shp.line.fill.background(); shp.shadow.inherit = False
        return y + math.ceil(len(D["grid"]) / cols) * step

    def picture(self, path, x, y, w, h, crop_bottom_to=None):
        pic = self.sh.add_picture(str(path), E(x), E(y), E(w))
        natural_h = pic.height / 6350
        if h < natural_h:
            pic.crop_bottom = 1 - h / natural_h
            pic.height = E(h)
        return pic

    def title(self, text, x, y, w, size=70, color=None, lines=None):
        ph = self.s.shapes.title
        ph.left, ph.top, ph.width = E(x), E(y), E(w)
        n = lines or len(wrap(text, size, w, bold=True))
        ph.height = E(n * size * 1.25 + 16)
        tf = ph.text_frame; tf.clear(); tf.word_wrap = True; tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.TOP
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT; p.line_spacing = 1.06
        r = p.add_run(); r.text = text
        r.font.name = "Inter"; r.font.size = Pt(size * 0.5); r.font.bold = True; r.font.color.rgb = rgb(color or self.c["tx"])
        return y + n * size * 1.12

    # ---- Notion page frame ------------------------------------------------------
    def frame(self, k, title, src=None, title_size=70):
        c = self.c
        name, icon, color = PAGES[k]
        self.rect(0, 0, 330, 1080, fill=c["side"])
        self.line(330, 0, 330, 1080, c["div"])
        self.rect(26, 27, 30, 30, fill="37352F" if not self.dark else "FFFFFF", radius=7)
        self.text(26, 27, 30, 30, "S", size=16, bold=True, color="FFFFFF" if not self.dark else "191919", align="c", anchor="m", spacing=1)
        self.text(68, 27, 250, 30, "Sales Development", size=20, bold=True, anchor="m", spacing=1)
        y = 82
        for nm, ic in (("Search", "search"), ("Home", "home"), ("Inbox", "inbox")):
            self.icon(ic, 26, y + 8, 20, c["tx2"], 1.7)
            self.text(60, y, 250, 36, nm, size=19, color=c["tx2"], anchor="m", spacing=1); y += 38
        self.text(26, y + 14, 280, 24, "Q3 2026 call list", size=15, bold=True, color=c["tx3"], anchor="m", spacing=1); y += 46
        for j, (nm, ic, col) in enumerate(PAGES):
            if j == k:
                self.rect(14, y, 302, 38, fill=c["hov"], radius=8)
            self.icon(ic, 26, y + 9, 20, col if j == k else c["tx2"], 1.7)
            self.text(60, y, 250, 38, nm, size=19, bold=(j == k), color=c["tx"] if j == k else c["tx2"], anchor="m", spacing=1)
            y += 40
        self.rect(14, 980, 302, 80, fill=c["side"], line=c["div"], radius=12)
        self.icon("monitor", 30, 1004, 30, color, 1.7)
        self.text(74, 994, 230, 56, [[("Live dashboard", {"bold": True})], [("goofturtle.github.io", {"color": c["tx2"], "size": 16})]],
                  size=17, spacing=1.15)
        # top bar
        crumb = [("Sales Development", {}), ("  /  ", {"color": c["tx3"]}), ("Q3 2026 call list", {}), ("  /  ", {"color": c["tx3"]}), (name, {})]
        self.text(356, 14, 1000, 30, [crumb], size=18, anchor="m", spacing=1)
        self.text(1560, 14, 170, 30, "Edited 25 Nov", size=18, color=c["tx2"], anchor="m", spacing=1, align="r")
        self.rect(1748, 12, 82, 34, line=c["div"], radius=8)
        self.text(1748, 12, 82, 34, "Share", size=18, align="c", anchor="m", spacing=1)
        # page icon + title
        self.icon(icon, 440, 104, 88, color, 1.6)
        bottom = self.title(title, 440, 236, 1370, title_size)
        if src:
            self.text(440, 1036, 1370, 24, src, size=15, color=c["tx3"], spacing=1.1)
        return bottom + 36

    def notes(self, text):
        self.s.notes_slide.notes_text_frame.text = text


def dbbar(sl, x, y, w, views, right=None, new=False):
    c = sl.c
    vx = x
    for j, (nm, ic) in enumerate(views):
        tw = measure(nm, 19) + 48
        if j == 0:
            sl.rect(vx, y, tw, 34, fill=c["hov"], radius=8)
        sl.icon(ic, vx + 12, y + 8, 18, c["tx"] if j == 0 else c["tx2"], 1.7)
        sl.text(vx + 38, y, tw, 34, nm, size=19, color=c["tx"] if j == 0 else c["tx2"], anchor="m", spacing=1)
        vx += tw + 10
    rx = x + w
    if new:
        sl.rect(rx - 70, y, 70, 34, fill="2383E2", radius=7)
        sl.text(rx - 70, y, 70, 34, "New", size=18, bold=True, color="FFFFFF", align="c", anchor="m", spacing=1)
        rx -= 86
    if right:
        sl.text(rx - 900, y, 900, 34, right, size=18, color=c["tx2"], align="r", anchor="m", spacing=1)
    sl.line(x, y + 46, x + w, y + 46, c["div"])
    return y + 56


prs = Presentation()
prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
SHOTS = HERE / "shots"
B = {b["band"]: b for b in D["bands"]}
cn = B["Call now"]

# ================= 0. title slide =================
sl = Slide(prs, 0, dark=True)
ph_title, ph_sub = sl.s.placeholders[0], sl.s.placeholders[1]
sl.text(120, 250, 900, 30, "SALES DEVELOPMENT  ·  Q3 2026", size=20, bold=True, color="9B9A97", spacing=1)
sl.title("Who to call first", 120, 300, 820, size=150, color="FFFFFF", lines=2)
ph_sub.left, ph_sub.top, ph_sub.width, ph_sub.height = E(120), E(660), E(760), E(120)
tf = ph_sub.text_frame; tf.clear(); tf.word_wrap = True
tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT; p.line_spacing = 1.3
r = p.add_run(); r.text = f"{fmt(D['total'])} flagged free workspaces, scored and ranked so reps call the teams most ready to buy."
r.font.name = "Inter"; r.font.size = Pt(15); r.font.color.rgb = rgb("9B9A97")
sl.line(120, 870, 900, 870, "2F2F2F")
for j, (n, lab, col) in enumerate([(fmt(D["total"]), "flagged workspaces", "FFFFFF"), (str(D["paid"]), "already paying", "FFFFFF"),
                                    (str(D["freeBands"]["Call now"]), "free teams to call now", "529CCA")]):
    sl.text(120 + j * 270, 895, 260, 60, n, size=54, bold=True, color=col, spacing=1)
    sl.text(120 + j * 270, 960, 260, 30, lab, size=19, color="9B9A97", spacing=1)
gy = sl.dots(1000, 250, 820, "r", lambda g: "4AA3F0" if (g["r"] < cn["n"] and not g["p"]) else ("2A4A66" if g["p"] else "2C2C2C"))
for j, (col, lab) in enumerate([("4AA3F0", f"{D['freeBands']['Call now']} free teams to call now"), ("2A4A66", "Already paying"), (None, "Every dot is one account, ranked by score")]):
    xx = 1000 + [0, 300, 500][j]
    if col:
        sl.oval(xx + 7, gy + 30, 7, fill=col)
    sl.text(xx + (22 if col else 0), gy + 17, 330, 28, lab, size=17, color="9B9A97", anchor="m", spacing=1)
sl.notes(f"We flagged {fmt(D['total'])} free Notion workspaces in Q3. This deck shows how we decided which ones reps should call first, and the tools reps will use on {D['freeBands']['Call now']} free teams in Call now.")

# ================= 1. overview =================
sl = Slide(prs, 5)
y = sl.frame(0, f"{D['freeBands']['Call now']} free teams to call now, out of {fmt(D['total'])} flagged")
props = [("people", "Team", "Sales Development"), ("status", "Status", None), ("cal", "Demo", "15 December 2026"), ("hash", "Flagged workspaces", fmt(D["total"]))]
for j, (ic, k, v) in enumerate(props):
    yy = y + j * 44
    sl.icon(ic, 440, yy + 8, 20, LIGHT["tx2"], 1.7)
    sl.text(472, yy, 220, 36, k, size=21, color=LIGHT["tx2"], anchor="m", spacing=1)
    if v:
        sl.text(700, yy, 600, 36, v, size=21, anchor="m", spacing=1)
    else:
        sl.tag(700, yy + 3, "Ready for demo", "green", 19, dot=True)
y += 4 * 44 + 26
sl.line(440, y, 1810, y, LIGHT["div"]); y += 34
stats = [(fmt(D["total"]), "flagged free workspaces", "37352F"), (str(D["paid"]), "already paying, don't pitch", "37352F"),
         (fmt(D["labeled"]), "email replies labeled by intent", "37352F"), (str(D["freeBands"]["Call now"]), "free teams to call now", "2383E2")]
cw = (1370 - 3 * 22) / 4
for j, (n, lab, col) in enumerate(stats):
    x = 440 + j * (cw + 22)
    sl.rect(x, y, cw, 210, fill=LIGHT["call"], radius=10)
    sl.text(x + 28, y + 30, cw - 56, 100, n, size=92, bold=True, color=col, spacing=1)
    sl.text(x + 28, y + 140, cw - 56, 50, lab, size=21, color=LIGHT["tx2"], spacing=1.2)
sl.notes(f"The short version: {fmt(D['total'])} flagged workspaces, {D['paid']} already paying, {fmt(D['labeled'])} human replies labeled, and {D['freeBands']['Call now']} free teams that look most like buyers.")

# ================= 2. problem =================
sl = Slide(prs, 5)
y = sl.frame(1, f"{fmt(D['total'])} flagged. Only {D['paid']} became paying teams.", src=SRC + " Rep brief for the 15 December demo.")
sl.text(440, y + 10, 480, 220, f"{round(D['paidPct'])}%", size=230, bold=True, color="2383E2", spacing=0.9)
sl.text(440, y + 270, 460, 90, f"{D['paid']} of {fmt(D['total'])} converted in Q3. {D['paidCompanyShare']}% used a company email domain.", size=24, spacing=1.35)
sl.callout(440, y + 380, 470, 150, "alert", "E03E3E", [[("Student workspaces look busiest, ", {"bold": True}), (f"but {D['schoolsPaid']} of the {D['schools']} paid. Reps had been calling them first (rep brief).", {})]], size=19)
gx, gw = 990, 820
sl.rect(gx, y, gw, 520, line=LIGHT["div"], radius=10)
gy = sl.dots(gx + 34, y + 30, gw - 68, "a", lambda g: "2383E2" if g["p"] else "E3E2E0")
for j, (col, lab) in enumerate([("2383E2", f"Paying ({D['paid']})"), ("E3E2E0", f"Still free ({fmt(D['total'] - D['paid'])})"), (None, "One dot per workspace, in account-ID order")]):
    xx = gx + 34 + [0, 190, 420][j]
    if col:
        sl.oval(xx + 7, gy + 26, 7, fill=col)
    sl.text(xx + (22 if col else 0), gy + 13, 360, 26, lab, size=17, color=LIGHT["tx2"], anchor="m", spacing=1)
sl.notes(f"Only {round(D['paidPct'])}% of flagged workspaces paid, and they were spread all through the list. Student workspaces looked busiest, but {D['schoolsPaid']} of the {D['schools']} paid.")

# ================= 3. signals =================
sl = Slide(prs, 5)
top = D["signals"][0]
y = sl.frame(2, f"Paying teams are {round(top['ratio'])}× bigger and use Notion more deeply",
             src=f"{SRC} Company-domain accounts only: {D['companyPaid']} paying vs {D['companyFree']} still free. Average per workspace.")
y = dbbar(sl, 440, y, 1370, [("Chart", "chart"), ("Table", "table")])
sl.rect(1380, y - 45, 14, 14, fill="2383E2", radius=3); sl.text(1402, y - 52, 150, 28, "Paying teams", size=17, color=LIGHT["tx2"], anchor="m", spacing=1)
sl.rect(1560, y - 45, 14, 14, fill="D3D1CB", radius=3); sl.text(1582, y - 52, 120, 28, "Still free", size=17, color=LIGHT["tx2"], anchor="m", spacing=1)
row_h = 88
for j, s in enumerate(D["signals"]):
    yy = y + j * row_h
    m = max(s["paid"], s["free"])
    sl.text(440, yy, 330, row_h, s["label"], size=23, anchor="m", spacing=1.1)
    bw = 760
    sl.rect(790, yy + 22, bw * s["paid"] / m, 18, fill="2383E2", radius=4)
    sl.text(790 + bw * s["paid"] / m + 12, yy + 18, 120, 26, f"{s['paid']}", size=18, bold=True, anchor="m", spacing=1)
    fw = max(8, bw * s["free"] / m)
    sl.rect(790, yy + 48, fw, 18, fill="D3D1CB", radius=4)
    sl.text(790 + fw + 12, yy + 44, 120, 26, f"{s['free']}", size=18, color=LIGHT["tx2"], anchor="m", spacing=1)
    sl.text(1640, yy, 170, row_h, f"{s['ratio']}×", size=50, bold=True, color="2383E2", align="r", anchor="m", spacing=1)
    if j < len(D["signals"]) - 1:
        sl.line(440, yy + row_h, 1810, yy + row_h, LIGHT["div"])
sl.notes(f"Comparing company accounts only, paying teams have about {top['ratio']} times the company seats, {D['signals'][1]['ratio']} times the teamspaces and {D['signals'][2]['ratio']} times the integrations. These became the scoring signals.")

# ================= 4. rules =================
sl = Slide(prs, 5)
y = sl.frame(3, f"Six signals, {sum(r['max'] for r in D['rules'])} points")
y = dbbar(sl, 440, y - 8, 1370, [("All signals", "table"), ("Caps", "list")], new=True)
cols = [(440, 470, "Signal"), (910, 770, "Points for each range"), (1680, 130, "Max")]
for x, w, h in cols:
    sl.text(x + 14, y, w - 28, 40, h, size=18, color=LIGHT["tx2"], anchor="m", spacing=1, align="r" if h == "Max" else "l")
sl.line(440, y + 40, 1810, y + 40, LIGHT["div"])
ry = y + 40
for r in D["rules"]:
    sl.text(454, ry, 440, 54, r["signal"], size=21, bold=True, anchor="m", spacing=1)
    tx = 924
    for a, pts in r["ranges"]:
        tx += sl.tag(tx, ry + 12, f"{a} · {pts}", "blue" if pts else "gray", 17) + 7
    sl.text(1694, ry, 102, 54, str(r["max"]), size=21, bold=True, align="r", anchor="m", spacing=1)
    ry += 54
    sl.line(440, ry, 1810, ry, LIGHT["div"])
sl.line(910, y, 910, ry, LIGHT["div"]); sl.line(1680, y, 1680, ry, LIGHT["div"])
cy = ry + 26
sl.callout(440, cy, 676, 118, "alert", "E03E3E", [[("Schools are capped at 20. ", {"bold": True}), (f"University and K-12 workspaces have the most active users (median {int(D['schoolWauMedian'])}), but {D['schoolsPaid']} of the {D['schools']} paid.", {})]], size=19)
sl.callout(1134, cy, 676, 118, "bulb", "DFAB01", [[("Student sign-ups earn nothing. ", {"bold": True}), ("Size is measured in company seats, not total members, so a campus can't look like a company.", {})]], size=19)
sl.notes(f"Six signals from the data, worth {sum(r['max'] for r in D['rules'])} points in total. Company seats carry the most weight. Schools are capped at 20 because their activity comes from students, not a team that buys.")

# ================= 5. proof (dark) =================
sl = Slide(prs, 5, dark=True)
y = sl.frame(4, f"{pct(cn['paid'], cn['n'])}% of Call now accounts are already paying teams", src=SRC)
gy = sl.dots(440, y + 6, 800, "r", lambda g: "529CCA" if g["p"] else "333333")
for j, (col, lab) in enumerate([("529CCA", "Paying"), ("333333", "Still free"), (None, f"Same {fmt(D['total'])} workspaces, sorted by score")]):
    xx = 440 + [0, 120, 260][j]
    if col:
        sl.oval(xx + 7, gy + 26, 7, fill=col)
    sl.text(xx + (22 if col else 0), gy + 13, 420, 26, lab, size=17, color=DARK["tx2"], anchor="m", spacing=1)
rx, ry = 1300, y
for k, (b, rng) in enumerate([("Call now", "80–100"), ("Call this week", "50–79"), ("Nurture", "0–49")]):
    bb = B[b]
    sl.line(rx, ry, 1810, ry, DARK["div"])
    sl.tag(rx, ry + 26, b, BAND[b], 19, dot=True)
    sl.text(rx, ry + 66, 330, 30, f"Score {rng} · {fmt(bb['n'])} accounts", size=18, color=DARK["tx2"], spacing=1)
    big = f"{pct(bb['paid'], bb['n'])}%" if bb["n"] >= 20 else f"{bb['paid']} of {bb['n']}"
    sl.text(1560, ry + 14, 250, 100, big, size=96 if k == 0 else 66, bold=True, color="529CCA" if k == 0 else "E3E2E0", align="r", anchor="m", spacing=1)
    ry += 124
sl.callout(rx, ry + 10, 510, 120, "alert", "FFA344", f"The rules were set on these same {D['paid']} paying accounts, so this is a best case. The real test is Q4.", size=18)
sl.notes(f"Sorted by score, the paying teams pile up at the top: {cn['paid']} of the {cn['n']} Call now accounts already pay, against {B['Nurture']['paid']} of {fmt(B['Nurture']['n'])} in Nurture. Caveat: the rules were built on this same data.")

# ================= 6. board =================
sl = Slide(prs, 5)
y = sl.frame(5, f"{fmt(D['labeled'])} email replies labeled by buying intent")
y = dbbar(sl, 440, y - 8, 1370, [("Board", "board"), ("Table", "table")],
          right=f"{D['autoReplies']} auto-replies held for a person  ·  {D['optOuts']} opt-outs flagged for suppression", new=True)
sl.rect(426, y, 1398, 1000 - y, fill="FBFBFA")
colw, gap = (1370 - 4 * 16) / 5, 16
for j, col in enumerate(D["board"]):
    x = 440 + j * (colw + gap)
    w = sl.tag(x, y + 14, col["name"], LAB[col["key"]], 18, dot=True)
    sl.text(x + w + 10, y + 14, 80, 27, str(col["n"]), size=18, bold=True, color=LIGHT["tx2"], anchor="m", spacing=1)
    cy = y + 58
    for t, conf in zip(col["examples"], col["conf"]):
        lines = wrap(f"“{t}”", 18, colw - 34)
        h = len(lines) * 18 * 1.42 + 66
        sl.rect(x, cy, colw, h, fill="FFFFFF", line="E3E2E0", radius=10)
        sl.text(x + 16, cy + 14, colw - 30, len(lines) * 26 + 8, f"“{t}”", size=18, spacing=1.3)
        sl.tag(x + 16, cy + h - 38, f"confidence: {conf}", "gray" if conf == "high" else "orange", 14)
        cy += h + 10
    sl.text(x + 6, cy + 4, 120, 26, "+ New", size=17, color=LIGHT["tx3"], spacing=1)
sl.notes(f"{fmt(D['labeled'])} human replies got one of the team's five labels. {D['autoReplies']} auto-replies wait for a real answer, and {D['optOuts']} opt-outs are flagged so those addresses can be suppressed before anyone calls. The cards are real replies.")

# ================= 7. sheet =================
sl = Slide(prs, 5)
y = sl.frame(6, "One ranked list, live in Google Sheets")
x = 440
for b in ["Call now", "Call this week", "Nurture"]:
    n = fmt(D["freeBands"][b]); nw = measure(n, 50, True)
    sl.text(x, y - 14, nw + 10, 60, n, size=50, bold=True, anchor="m", spacing=1)
    x += nw + 18
    x += sl.tag(x, y + 1, b, BAND[b], 19, dot=True) + 40
n = str(D["paid"]); nw = measure(n, 50, True)
sl.text(x, y - 14, nw + 10, 60, n, size=50, bold=True, anchor="m", spacing=1); x += nw + 18
sl.tag(x, y + 1, "Already paying", "orange", 19, dot=True)
ey = y + 66
sl.rect(440, ey, 1480, 1080 - ey + 20, fill="FFFFFF", line=LIGHT["div"], radius=10)
sl.icon("sheet", 460, ey + 14, 22, "0F9D58", 1.8)
sl.text(494, ey + 8, 900, 34, "Q3 2026 Ranked Call List v3  ·  Google Sheets", size=18, color=LIGHT["tx2"], anchor="m", spacing=1)
sl.line(440, ey + 50, 1920, ey + 50, LIGHT["div"])
sl.picture(SHOTS / "sheet.png", 441, ey + 51, 1479, 1080 - ey - 51)
sl.notes(f"All {fmt(D['total'])} workspaces in one Google Sheet, ranked by score, with a one-line reason a rep can read out. The counts are free accounts only. The {D['paid']} paying accounts keep their rank but are marked Yes, so nobody pitches them.")

# ================= 8. dashboard =================
sl = Slide(prs, 5)
y = sl.frame(7, "Reps type an account and see its rank")
sl.rect(440, y, 880, 600, fill="FFFFFF", line=LIGHT["div"], radius=10)
sl.picture(SHOTS / "dash-paying.png", 441, y + 1, 878, 598)
sl.text(440, y + 610, 880, 26, "Paying account ACC-10070, flagged before anyone dials", size=16, color=LIGHT["tx3"], spacing=1)
feats = [("sheet", "0F7B6C", "Reads the Google Sheet live", "No number is typed into the page"), ("aa", "2383E2", "Forgives messy input", "Stray spaces and lower case still match"),
         ("flag", "D9730D", "Flags paying accounts", "Shows “Already paying” before a call"), ("people", "9065B0", "Free teams come first", "Customers are hidden from the call order")]
for j, (ic, col, t, dsc) in enumerate(feats):
    fy = y + j * 150
    sl.callout(1360, fy, 450, 132, ic, col, [[(t, {"bold": True, "size": 22})], [(dsc, {"color": LIGHT["tx2"]})]], size=19)
sl.notes("The dashboard reads the sheet live. A rep types or picks an account and sees rank, score, band and reason. Paying accounts are flagged before anyone dials.")

# ================= 9. live demo (dark) =================
sl = Slide(prs, 5, dark=True)
y = sl.frame(8, "Try it live", title_size=96)
url = "https://" + D["dashboardUrl"] + "/"
sl.rect(440, y, 1300, 210, fill="202020", line=DARK["div"], radius=12)
sl.text(470, y + 26, 880, 34, "Q3 call list", size=26, bold=True, spacing=1)
sl.text(470, y + 70, 880, 70, f"Look up any of the {fmt(D['total'])} flagged workspaces and see its rank, score, band and reason, read live from Google Sheets.", size=20, color=DARK["tx2"], spacing=1.35)
sl.icon("link", 470, y + 158, 20, DARK["tx"], 1.8)
sl.text(500, y + 150, 840, 34, D["dashboardUrl"], size=18, anchor="m", spacing=1)
sl.picture(SHOTS / "dash-free.png", 1380, y + 1, 359, 208)
hy = y + 260
sl.icon("aa", 440, hy, 34, "529CCA")
sl.text(500, hy - 4, 600, 44, "Try typing", size=34, bold=True, anchor="m", spacing=1)
tf_ = D["topFree"]
chips = [(tf_["account_id"], f"rank {tf_['rank']}, top free team"), ("ACC-10070", "already paying"), ("acc-10918", "lower case still works"), ("ACC-11347", "not in the list")]
cx = 440
for code, dsc in chips:
    cw_ = measure(code, 20) * 1.05 + 24
    sl.rect(cx, hy + 62, cw_, 38, fill="3A3836", radius=6)
    sl.text(cx, hy + 62, cw_, 38, code, size=20, color="FF7369", align="c", anchor="m", spacing=1, font_name="Consolas")
    dw = measure(dsc, 19) + 10
    sl.text(cx + cw_ + 12, hy + 62, dw, 38, dsc, size=19, color=DARK["tx2"], anchor="m", spacing=1)
    cx += cw_ + 12 + dw + 34
sl.callout(440, hy + 140, 1300, 84, "check", "4DAB9A", f"{D['lookupsPassed']} of {D['lookupsTotal']} rep lookups from the demo brief passed when checked by hand in the browser, including IDs with a stray space.", size=20)
sl.notes(f"Open the dashboard and try these four. {tf_['account_id']} is the top free team at rank {tf_['rank']}. ACC-10070 shows the paying flag. Lower case still works, and an unknown ID says it has no score.")

# ================= 10. insights (dark) =================
sl = Slide(prs, 5, dark=True)
y = sl.frame(9, "What building it taught us", src=f"{SRC} Q3 2026 Outbound Email Reply Export, {D['replies']} replies.")
cards = [(D["membersTop60Paid"], "of 60", "Size means company seats, not members", (f"The 60 workspaces with the most members were all schools, and {D['membersTop60Paid']} paid. " if D["membersTop60Schools"] == 60 else f"The 60 workspaces with the most members include {D['membersTop60Schools']} schools; {D['membersTop60Paid']} paid. ") + f"The 60 with the most seats include {D['seatsTop60Paid']} paying teams.", "people", "529CCA"),
         (D["top100Paid"], "of 100", "The best-scoring accounts already pay", f"{D['top100Paid']} of the top 100 by score were already customers, so the call list hides them and starts with a free team.", "flag", "FFA344"),
         (D["replyIdAgree"], f"of {D['replies']}", "Reply data can't be joined yet", f"The reply export agrees with the account list on domain type for only {D['replyIdAgree']} of {D['replies']} replies, so labels stay out of the score.", "mail", "9A6DD7")]
cw = (1370 - 2 * 22) / 3
for j, (n, of, h, para, ic, col) in enumerate(cards):
    x = 440 + j * (cw + 22)
    sl.rect(x, y, cw, 540, fill=DARK["call"], radius=12)
    sl.icon(ic, x + 34, y + 34, 34, col)
    nw = measure(str(n), 120, True)
    sl.text(x + 34, y + 96, nw + 20, 130, str(n), size=120, bold=True, color=col, anchor="b", spacing=0.9)
    sl.text(x + 44 + nw, y + 96, 200, 120, of, size=34, bold=True, color=DARK["tx2"], anchor="b", spacing=1)
    sl.text(x + 34, y + 252, cw - 68, 80, h, size=29, bold=True, spacing=1.15)
    sl.text(x + 34, y + 345, cw - 68, 180, para, size=20, color=DARK["tx2"], spacing=1.45)
sl.notes(f"Three lessons. Measure size with seats, not members. {D['top100Paid']} of our top 100 scorers were already customers, so we hide them (the cut at rank 100 falls inside a {D['rank100Ties']}-way tie at score {D['score100th']}). And the reply file's account IDs don't match yet, so reply labels stay out of the score.")

# ================= 11. next steps =================
sl = Slide(prs, 5)
y = sl.frame(10, "Ready for the 15 December demo", src="Dates from the rep lookup brief: demo 15 December 2026, Monday queue from 21 December.")
groups = [("Now", "green", [("Dashboard and Google Sheet are live", 1), (f"{D['lookupsPassed']} of {D['lookupsTotal']} rep lookups pass (checked by hand)", 1), ("Paying accounts hidden from the call order", 1), ("Monday queue starts 21 December", 0)]),
          ("Before reps dial", "yellow", [(f"Suppress the {D['optOuts']} opt-outs by email address", 0), ("Fix account IDs in the reply export", 0), ("Add reply labels to the score", 0)]),
          ("Q4", "blue", [("Score Q4's flagged workspaces", 0), ("Compare scores with who actually pays", 0), ("Adjust the point bands if needed", 0)])]
cw = (1370 - 2 * 48) / 3
for j, (name, kind, items) in enumerate(groups):
    x = 440 + j * (cw + 48)
    sl.tag(x, y + 10, name, kind, 22, dot=True)
    ty = y + 70
    for t, done in items:
        lines = wrap(t, 23, cw - 44)
        if done:
            sl.rect(x, ty + 5, 26, 26, fill="2383E2", radius=4)
            sl.poly([(x + 6, ty + 18), (x + 11, ty + 24), (x + 21, ty + 11)], "FFFFFF", 3)
        else:
            sl.rect(x, ty + 5, 26, 26, line=LIGHT["tx2"], lw=2, radius=4)
        sl.text(x + 42, ty, cw - 44, len(lines) * 34 + 6, [[(t, {"color": LIGHT["tx3"] if done else LIGHT["tx"], "strike": bool(done)})]], size=23, spacing=1.3)
        ty += len(lines) * 34 + 16
sl.callout(440, 860, 1300, 84, "link", "2383E2", [[("Dashboard: ", {}), (D["dashboardUrl"], {"bold": True, "link": url})]], size=22)
sl.notes(f"The list and dashboard are ready for the demo. Before reps dial, suppress the {D['optOuts']} opt-outs by email and fix the reply IDs. In Q4, score the new flagged workspaces and test the rules against who actually pays.")

titles = [s.shapes.title.text_frame.text if s.shapes.title else "" for s in prs.slides]
if not all(t.strip() for t in titles):
    raise SystemExit(f"a slide is missing its title: {titles}")
dest = HERE / "Who to Call First - Q3 2026 call list.pptx"
prs.save(dest)
pics = sum(1 for s in prs.slides for sh in s.shapes if sh.shape_type == 13)
shapes = sum(len(s.shapes) for s in prs.slides)
print(dest.name, f"{dest.stat().st_size / 1e6:.1f} MB,", len(prs.slides), "slides,", shapes, "shapes,", pics, "pictures")
for k, t in enumerate(titles, 1):
    print(f"  {k:2}. {t!r}")
