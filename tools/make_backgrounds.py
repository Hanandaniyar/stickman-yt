"""Menggambar latar flat-vector 1920x1080 untuk lib/backgrounds (jalankan: uv run python tools/make_backgrounds.py).

Aturan gaya: warna lembut, kontras rendah (stickman hitam + Fluent Emoji tetap menonjol), tanpa teks/merek,
lantai/garis tanah di y=840, tidak ada detail penting di 200 px bawah (subtitle).
Lapisan: <g id="base"> (langit/dinding/lantai, diam), <g id="far">, <g id="mid">, <g id="near"> (paralaks).
Semua id lain diawali nama latar (mis. "kitchen-sky").
"""
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "lib" / "backgrounds"
GROUND = 840
L, R = -240, 2160  # lebar lapisan dengan cadangan paralaks

# palet lembut
SKY_T, SKY_B = "#CFE4F1", "#EEF4F1"
WALL, WALL2 = "#F4ECDF", "#EADFCB"
FLOOR, FLOOR2 = "#E4D6C0", "#DDCDB3"
WHITE = "#FBF9F5"
GLASS = "#E3EFF6"
STEEL, STEEL2 = "#D4D9DF", "#C3CAD2"
GREEN, GREEN2, GREEN3 = "#C7DFBA", "#B3D2A4", "#9EC48F"
TRUNK = "#CDB396"
MUSTARD, CORAL, TEAL, LAV, BLUE, PINK = "#F1D893", "#EFC0AE", "#B5DCD5", "#D6CFEA", "#BFD3EA", "#F2CFD6"
SHADOW = "#00000010"


def f(v):
    return f"{v:g}" if isinstance(v, (int, float)) else str(v)


def rect(x, y, w, h, fill, rx=0, op=None, extra=""):
    o = f' opacity="{op}"' if op is not None else ""
    r = f' rx="{f(rx)}"' if rx else ""
    return f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}"{r} fill="{fill}"{o}{extra}/>'


def circ(cx, cy, r, fill, op=None):
    o = f' opacity="{op}"' if op is not None else ""
    return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}"{o}/>'


def ell(cx, cy, rx, ry, fill, op=None):
    o = f' opacity="{op}"' if op is not None else ""
    return f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(rx)}" ry="{f(ry)}" fill="{fill}"{o}/>'


def path(d, fill="none", stroke=None, sw=None, op=None, cap="round"):
    s = f' stroke="{stroke}" stroke-width="{f(sw)}" stroke-linecap="{cap}" stroke-linejoin="round"' if stroke else ""
    o = f' opacity="{op}"' if op is not None else ""
    return f'<path d="{d}" fill="{fill}"{s}{o}/>'


def line(x1, y1, x2, y2, stroke, sw, op=None):
    return path(f"M{f(x1)} {f(y1)} L{f(x2)} {f(y2)}", stroke=stroke, sw=sw, op=op)


def grad(gid, stops, vertical=True):
    xy = 'x1="0" y1="0" x2="0" y2="1"' if vertical else 'x1="0" y1="0" x2="1" y2="0"'
    st = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<linearGradient id="{gid}" {xy}>{st}</linearGradient>'


def rgrad(gid, stops, cx=0.5, cy=0.5, r=0.6):
    st = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}">{st}</radialGradient>'


def svg(name, defs, base, far, mid, near):
    j = "\n    ".join
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">\n'
        f'  <defs>\n    {j(defs)}\n  </defs>\n'
        f'  <g id="base">\n    {j(base)}\n  </g>\n'
        f'  <g id="far">\n    {j(far)}\n  </g>\n'
        f'  <g id="mid">\n    {j(mid)}\n  </g>\n'
        f'  <g id="near">\n    {j(near)}\n  </g>\n'
        f'</svg>\n'
    )


def sky_base(name, top=SKY_T, bot=SKY_B, ground=FLOOR, ground2=None):
    defs = [grad(f"{name}-sky", [(0, top), (1, bot)]),
            grad(f"{name}-ground", [(0, ground), (1, ground2 or ground)])]
    base = [rect(-400, -200, 2720, GROUND + 200, f"url(#{name}-sky)"),
            rect(-400, GROUND, 2720, 1080 - GROUND + 200, f"url(#{name}-ground)")]
    return defs, base


def wall_base(name, wall=WALL, wall2=WALL2, floor=FLOOR, floor2=FLOOR2, skirting=True):
    defs = [grad(f"{name}-wall", [(0, wall), (1, wall2)]), grad(f"{name}-floor", [(0, floor), (1, floor2)])]
    base = [rect(-400, -200, 2720, GROUND + 200, f"url(#{name}-wall)"),
            rect(-400, GROUND, 2720, 1080 - GROUND + 200, f"url(#{name}-floor)")]
    if skirting:
        base.append(rect(-400, GROUND - 22, 2720, 22, WHITE))
        base.append(rect(-400, GROUND, 2720, 6, SHADOW))
    return defs, base


def cloud(x, y, s=1.0, fill=WHITE, op=0.9):
    return (f'<g opacity="{op}">' + ell(x, y, 90 * s, 34 * s, fill) + circ(x - 40 * s, y - 18 * s, 36 * s, fill)
            + circ(x + 20 * s, y - 34 * s, 46 * s, fill) + circ(x + 62 * s, y - 10 * s, 30 * s, fill) + "</g>")


def windows(x, y, w, h, cols, rows, fill=GLASS, gap=14, pad=18, lit=None, rng=None, litc="#FBEFC9"):
    out = []
    cw = (w - 2 * pad - (cols - 1) * gap) / cols
    ch = (h - 2 * pad - (rows - 1) * gap) / rows
    for r in range(rows):
        for c in range(cols):
            col = fill
            if lit and rng and rng.random() < lit:
                col = litc
            out.append(rect(x + pad + c * (cw + gap), y + pad + r * (ch + gap), cw, ch, col, rx=3))
    return "".join(out)


def tree(x, base_y, h=260, r=95, c1=GREEN2, c2=GREEN3):
    return (rect(x - 11, base_y - h * 0.55, 22, h * 0.55, TRUNK, rx=8)
            + circ(x, base_y - h * 0.62, r, c1) + circ(x - r * 0.55, base_y - h * 0.5, r * 0.62, c1)
            + circ(x + r * 0.5, base_y - h * 0.52, r * 0.66, c2) + circ(x + r * 0.15, base_y - h * 0.8, r * 0.55, c2, 0.8))


def pine(x, base_y, h=200, c=GREEN3):
    return rect(x - 6, base_y - 40, 12, 40, TRUNK) + path(
        f"M{x} {base_y - h} L{x + h * 0.32} {base_y - 30} L{x - h * 0.32} {base_y - 30} Z", fill=c)


def plant(x, base_y, s=1.0, pot=CORAL):
    leaves = "".join(ell(x + dx * s, base_y - 120 * s + dy * s, 22 * s, 58 * s, c)
                     .replace("/>", f' transform="rotate({rot} {f(x + dx * s)} {f(base_y - 120 * s + dy * s)})"/>')
                     for dx, dy, rot, c in [(-28, 10, -30, GREEN2), (26, 8, 32, GREEN2), (0, -12, 0, GREEN3),
                                            (-12, 20, -12, GREEN3), (14, 22, 14, GREEN)])
    return leaves + path(f"M{x - 42 * s} {base_y - 74 * s} L{x + 42 * s} {base_y - 74 * s} L{x + 32 * s} {base_y} "
                         f"L{x - 32 * s} {base_y} Z", fill=pot)


def lamp_post(x, top=430):
    return (rect(x - 7, top, 14, GROUND - top, "#BFC6CE", rx=6) + rect(x - 22, GROUND - 16, 44, 16, "#B5BCC5", rx=4)
            + path(f"M{x} {top + 10} Q{x} {top - 30} {x + 50} {top - 30}", stroke="#BFC6CE", sw=10)
            + ell(x + 62, top - 22, 28, 12, "#B5BCC5") + ell(x + 62, top - 12, 18, 6, "#FBEFC9"))


def car_shape(x, y, w, col, glass=GLASS, flip=False):
    """Mobil sederhana, roda menyentuh y."""
    h = w * 0.36
    s = -1 if flip else 1
    cx = x + w / 2

    def X(v):
        return cx + s * (v - 0.5) * w

    body = (f"M{X(0.02)} {y - h * 0.28} L{X(0.04)} {y - h * 0.62} L{X(0.22)} {y - h * 0.7} L{X(0.36)} {y - h}"
            f" L{X(0.7)} {y - h} L{X(0.84)} {y - h * 0.68} L{X(0.97)} {y - h * 0.6} L{X(0.99)} {y - h * 0.28} Z")
    win = (f"M{X(0.27)} {y - h * 0.68} L{X(0.38)} {y - h * 0.92} L{X(0.52)} {y - h * 0.92} L{X(0.52)} {y - h * 0.68} Z"
           f" M{X(0.56)} {y - h * 0.68} L{X(0.56)} {y - h * 0.92} L{X(0.68)} {y - h * 0.92} L{X(0.79)} {y - h * 0.68} Z")
    return (ell(cx, y + 2, w * 0.5, 9, SHADOW) + path(body, fill=col) + path(win, fill=glass)
            + circ(X(0.24), y - h * 0.22, h * 0.24, "#8E959D") + circ(X(0.24), y - h * 0.22, h * 0.11, "#D8DCE0")
            + circ(X(0.78), y - h * 0.22, h * 0.24, "#8E959D") + circ(X(0.78), y - h * 0.22, h * 0.11, "#D8DCE0")
            + rect(X(0.93) - (8 if s > 0 else 0), y - h * 0.55, 8, h * 0.1, "#FBEFC9"))


def wall_clock(x, y, r=46):
    return (circ(x, y, r + 6, "#D9CDBB") + circ(x, y, r, WHITE) + line(x, y, x, y - r * 0.6, "#B7AC9C", 6)
            + line(x, y, x + r * 0.45, y + r * 0.2, "#B7AC9C", 6) + circ(x, y, 5, "#B7AC9C"))


def frame_art(x, y, w, h, colors, kind=0):
    inner = rect(x + 12, y + 12, w - 24, h - 24, colors[0])
    if kind == 0:
        inner += circ(x + w * 0.62, y + h * 0.38, min(w, h) * 0.16, colors[1]) + path(
            f"M{x + 12} {y + h - 12} L{x + w * 0.35} {y + h * 0.5} L{x + w * 0.6} {y + h - 12} Z", fill=colors[2])
    else:
        inner += rect(x + w * 0.2, y + h * 0.25, w * 0.3, h * 0.5, colors[1]) + circ(x + w * 0.66, y + h * 0.55, min(w, h) * 0.18, colors[2])
    return rect(x, y, w, h, "#D9CDBB", rx=4) + inner


def bunting(x1, x2, y, n, colors, sag=40):
    out = [path(f"M{x1} {y} Q{(x1 + x2) / 2} {y + sag * 2} {x2} {y}", stroke="#C9BFAF", sw=3)]
    for i in range(n):
        t = (i + 0.5) / n
        px = x1 + (x2 - x1) * t
        py = y + sag * 2 * 2 * t * (1 - t)
        out.append(path(f"M{px - 22} {py} L{px + 22} {py} L{px} {py + 44} Z", fill=colors[i % len(colors)]))
    return "".join(out)


# ---------------------------------------------------------------- latar

def street():
    n = "street"
    rng = random.Random(1)
    defs, base = sky_base(n, ground="#E7E2D9", ground2="#DCD6CB")
    base.append(rect(-400, GROUND, 2720, 10, "#D3CCC0"))
    far = [cloud(300, 150, 1.1), cloud(1500, 110, 0.9), cloud(980, 210, 0.7, op=0.7)]
    x = L
    for w, h in [(220, 380), (160, 520), (260, 300), (180, 460), (240, 560), (200, 340), (280, 480), (180, 400), (260, 520), (220, 360), (240, 300)]:
        far.append(rect(x, GROUND - 260 - h, w, h + 260, "#DCE6EE"))
        x += w + 10
    mid = []
    shops = [(L, 340, 470, "#EAD9C6", CORAL), (110, 380, 560, "#DCE3EC", TEAL), (500, 330, 430, "#F0E2CD", MUSTARD),
             (840, 400, 600, "#E3DCEB", LAV), (1250, 340, 480, "#DDE8DB", CORAL), (1600, 360, 540, "#EFDCD3", BLUE),
             (1970, 300, 450, "#E1E6EE", MUSTARD)]
    for x, w, h, col, aw in shops:
        top = GROUND - h
        mid.append(rect(x, top, w - 6, h, col))
        mid.append(rect(x - 6, top - 14, w + 6, 18, "#00000012"))
        mid.append(windows(x + 10, top + 20, w - 26, h - 300, max(2, w // 120), max(1, (h - 300) // 110), rng=rng, lit=0.2))
        # etalase + kanopi
        sy = GROUND - 250
        mid.append(rect(x + 20, sy + 60, w - 46, 170, GLASS, rx=4))
        mid.append(rect(x + w * 0.55, sy + 70, 70, 160, "#CDBBA6", rx=3))
        stripes = "".join(rect(x + 10 + i * (w - 26) / 6, sy, (w - 26) / 12, 46, WHITE, op=0.7) for i in range(6))
        mid.append(path(f"M{x + 6} {sy} L{x + w - 12} {sy} L{x + w - 2} {sy + 46} L{x - 4} {sy + 46} Z", fill=aw) + stripes)
        mid.append(rect(x + 30, sy - 50, w * 0.45, 30, WHITE, rx=6, op=0.85))  # papan nama kosong
    near = [lamp_post(150, 420), lamp_post(1780, 420),
            tree(1080, GROUND, 250, 80), rect(1040, GROUND - 26, 80, 26, "#C9B8A3", rx=4),
            rect(560, GROUND - 70, 26, 70, "#E4A595", rx=8) + rect(552, GROUND - 76, 42, 14, "#E4A595", rx=6),
            rect(-120, GROUND - 120, 150, 120, "#B9C9D6", rx=10)]
    return n, svg(n, defs, base, far, mid, near)


def city_skyline():
    n = "city-skyline"
    rng = random.Random(2)
    defs, base = sky_base(n, top="#F6DDCB", bot="#DDE9F2", ground="#E2D8CA", ground2="#D9CDBC")
    defs.append(rgrad(f"{n}-sun", [(0, "#FCEFD2"), (1, "#FCEFD200")], r=0.5))
    base.append(circ(1460, 300, 260, f"url(#{n}-sun)"))
    base.append(circ(1460, 300, 90, "#FBE8C4"))
    far = [cloud(400, 180, 1.2, op=0.75), cloud(1100, 120, 0.8, op=0.6)]
    x = L
    while x < R:
        w = rng.choice([90, 120, 140, 170]); h = rng.choice([260, 320, 380, 440, 500])
        far.append(rect(x, GROUND - 120 - h, w, h + 120, "#E6DCE6"))
        if rng.random() < 0.3:
            far.append(path(f"M{x + w / 2} {GROUND - 120 - h - 60} L{x + w / 2} {GROUND - 120 - h}", stroke="#E6DCE6", sw=6))
        x += w + rng.choice([0, 20, 40])
    mid = []
    x = L + 40
    cols = ["#CFDAE6", "#D8D3E3", "#D3DFDA", "#DCD4CB", "#CBD6E4"]
    while x < R:
        w = rng.choice([150, 180, 220, 260]); h = rng.choice([420, 520, 600, 660, 560])
        top = GROUND - 80 - h
        c = rng.choice(cols)
        mid.append(rect(x, top, w, h + 80, c))
        mid.append(windows(x, top + 10, w, h - 40, max(2, w // 60), max(3, h // 70), fill="#E9F0F6", gap=10, pad=16, lit=0.12, rng=rng))
        if rng.random() < 0.4:
            mid.append(path(f"M{x + 10} {top} L{x + w / 2} {top - 70} L{x + w - 10} {top} Z", fill=c))
        x += w + rng.choice([30, 60, 90])
    near = [rect(L, GROUND - 120, R - L, 16, "#D2C6B6", rx=6),
            "".join(rect(x, GROUND - 110, 10, 110, "#D2C6B6") for x in range(L, R, 70)),
            rect(L, GROUND - 40, R - L, 40, "#DCD0BF"),
            plant(120, GROUND - 40, 1.0, "#E3C2A8"), plant(1800, GROUND - 40, 1.1, "#C8D5E3")]
    return n, svg(n, defs, base, far, mid, near)


def store_checkout():
    n = "store-checkout"
    defs, base = wall_base(n, wall="#F3EEE4", wall2="#EAE1D1", floor="#E6DED2", floor2="#DDD3C4")
    base.append(rect(-400, 0, 2720, 120, "#E3EDE6"))
    far = []
    for sx in (-60, 560, 1180, 1800):
        far.append(rect(sx, 260, 520, 560, "#E6DCCB", rx=6))
        for sh in range(4):
            y = 300 + sh * 130
            far.append(rect(sx + 14, y + 100, 492, 12, "#D6C9B4"))
            px = sx + 24
            for i, c in enumerate([CORAL, MUSTARD, TEAL, LAV, BLUE, PINK, GREEN]):
                w = 50 + (i * 17 + sh * 11) % 30
                hh = 60 + (i * 23 + sh * 7) % 36
                if px + w > sx + 500:
                    break
                far.append(rect(px, y + 100 - hh, w, hh, c, rx=4, op=0.85))
                px += w + 12
    mid = ["".join(rect(x, 150, 260, 26, "#FFFFFF", rx=13, op=0.9) for x in (200, 860, 1520)),
           line(1430, 0, 1430, 210, "#CFC4B3", 4) + line(1590, 0, 1590, 210, "#CFC4B3", 4)
           + rect(1400, 210, 220, 110, "#DCEBE0", rx=14) + circ(1510, 265, 34, WHITE)]
    cx = 1040
    near = [
        rect(cx, 600, 860, 240, "#D9CBB6", rx=8), rect(cx - 10, 580, 880, 30, "#E8DCC9", rx=8),
        rect(cx + 30, 590, 480, 16, "#8F969E", rx=8), "".join(rect(cx + 40 + i * 46, 592, 8, 12, "#A7AEB6") for i in range(10)),
        rect(cx + 600, 470, 18, 120, "#B9C0C8") + rect(cx + 540, 400, 150, 100, "#C9D3DE", rx=10) + rect(cx + 556, 414, 118, 70, "#E7F1F7", rx=6),
        rect(cx + 720, 520, 110, 70, "#C2C9D1", rx=8) + rect(cx + 736, 532, 78, 22, "#DDE7EE", rx=4),
        rect(cx + 120, 660, 200, 120, "#CFBFA8", rx=6),
        rect(-80, 640, 300, 200, "#CBD9C9", rx=10) + rect(-70, 600, 280, 50, "#DCE7D9", rx=10),
    ]
    return n, svg(n, defs, base, far, mid, near)


def supermarket():
    n = "supermarket"
    defs, base = wall_base(n, wall="#F2F0EA", wall2="#E9E5DB", floor="#E9E4DA", floor2="#DED7CB", skirting=False)
    base.append(rect(-400, 0, 2720, 110, "#DDEBE2"))
    base.append("".join(line(x, GROUND, x - 40, 1080, "#D6CEC0", 3, op=0.6) for x in range(-200, 2300, 240)))
    far = ["".join(rect(x, 40, 220, 18, WHITE, rx=9) + rect(x + 10, 58, 200, 8, "#FFF6DC") for x in range(-100, 2200, 420)),
           "".join(rect(x, 140, 300, 60, "#E5D8C2", rx=10, op=0.9) for x in (160, 1460))]
    mid = []
    for sx, w in ((-200, 760), (620, 680), (1360, 800)):
        mid.append(rect(sx, 250, w, GROUND - 250, "#E3D7C3", rx=6))
        mid.append(rect(sx, 230, w, 30, "#D8E6DB", rx=6))
        for sh in range(5):
            y = 280 + sh * 110
            mid.append(rect(sx + 10, y + 90, w - 20, 14, "#D2C3AB"))
            px, k = sx + 22, 0
            while px < sx + w - 60:
                c = [CORAL, MUSTARD, TEAL, LAV, BLUE, PINK, GREEN, "#F3E3C3"][(k * 3 + sh * 5 + sx // 7) % 8]
                bw = [38, 52, 44, 60, 34][(k + sh) % 5]
                bh = [56, 76, 64, 84, 48][(k * 2 + sh) % 5]
                if sh == 4:
                    bh = min(bh, 70)
                mid.append(rect(px, y + 90 - bh, bw, bh, c, rx=5, op=0.9))
                px += bw + 8
                k += 1
            mid.append("".join(rect(sx + 40 + i * 150, y + 92, 40, 10, WHITE) for i in range(int((w - 40) / 150))))
    near = [  # carrito
        "<g>" + path(f"M1700 {GROUND - 260} L1740 {GROUND - 260} L1770 {GROUND - 90} L1890 {GROUND - 90} L1910 {GROUND - 200} L1750 {GROUND - 200}",
                     stroke="#B9C0C8", sw=10) + rect(1755, GROUND - 200, 150, 105, "#C9D1DA", op=0.5)
        + circ(1785, GROUND - 22, 18, "#9AA2AB") + circ(1880, GROUND - 22, 18, "#9AA2AB")
        + line(1775, GROUND - 90, 1785, GROUND - 40, "#B9C0C8", 8) + line(1880, GROUND - 90, 1880, GROUND - 40, "#B9C0C8", 8) + "</g>",
        rect(-160, GROUND - 160, 260, 160, "#E9C9B2", rx=10) + "".join(circ(-120 + i * 52, GROUND - 170, 26, c) for i, c in enumerate([CORAL, MUSTARD, "#F3B79F", GREEN2, MUSTARD]))]
    return n, svg(n, defs, base, far, mid, near)


def kitchen():
    n = "kitchen"
    defs, base = wall_base(n, wall="#F5EEE2", wall2="#EFE5D4", floor="#E3D4BE", floor2="#D8C7AD", skirting=False)
    defs.append(grad(f"{n}-win", [(0, "#CFE4F1"), (1, "#EEF4F1")]))
    far = [rect(-300, 520, 2500, 120, "#EAF1EE")]  # backsplash
    far.append("".join(line(x, 520, x, 640, "#DDE7E3", 3) for x in range(-300, 2200, 80))
               + "".join(line(-300, y, 2200, y, "#DDE7E3", 3) for y in (560, 600)))
    far.append(rect(760, 150, 400, 300, "#E9DCC6", rx=8) + rect(780, 170, 360, 260, f"url(#{n}-win)", rx=4)
               + line(960, 170, 960, 430, "#E9DCC6", 12) + line(780, 300, 1140, 300, "#E9DCC6", 12)
               + cloud(880, 230, 0.4, op=0.9) + tree(1080, 430, 120, 40))
    far.append(path("M740 150 Q760 300 800 450 L740 450 Z", fill="#F2C9B8") + path("M1180 150 Q1160 300 1120 450 L1180 450 Z", fill="#F2C9B8")
               + rect(730, 138, 460, 16, "#D9C7AE", rx=8))
    mid = ["".join(rect(x, 140, 250, 300, "#E7D8C1", rx=8) + rect(x + 16, 156, 218, 268, "#EEE2CF", rx=6)
                   + rect(x + 110, 380, 30, 10, "#CBB89C", rx=5) for x in (-160, 110, 1220, 1490, 1760)),
           rect(-300, 640, 2500, 22, "#D7C3A6", rx=6),  # meja dapur
           "".join(rect(x, 662, 260, GROUND - 662, "#E9DBC4") + rect(x + 14, 676, 232, GROUND - 690, "#EFE4D2", rx=6)
                   + rect(x + 105, 700, 50, 10, "#CBB89C", rx=5) for x in range(-300, 2200, 270)),
           # kompor + panci
           rect(1300, 630, 300, 14, "#B8BFC7", rx=6) + rect(1360, 560, 150, 74, "#C5CDD5", rx=10) + rect(1340, 552, 190, 14, "#B3BBC4", rx=6),
           # kulkas
           rect(-120, 220, 300, GROUND - 220, "#DCE5EC", rx=18) + line(-120, 470, 180, 470, "#C9D3DC", 6)
           + rect(140, 300, 14, 120, "#BFC8D1", rx=7) + rect(140, 520, 14, 160, "#BFC8D1", rx=7)]
    near = [plant(1000, 640, 0.6, "#E9C9B2"), rect(560, 590, 120, 50, "#F1D893", rx=20) + circ(590, 590, 18, "#EFC0AE") + circ(630, 586, 16, GREEN2),
            path("M1880 0 L1880 120", stroke="#CDBFA9", sw=4) + plant(1880, 240, 0.7, "#D6CFEA")]
    return n, svg(n, defs, base, far, mid, near)


def living_room():
    n = "living-room"
    defs, base = wall_base(n, wall="#EFE7F0", wall2="#E7DCE6", floor="#E4D2BC", floor2="#D9C4AA")
    defs.append(grad(f"{n}-win", [(0, "#CFE4F1"), (1, "#F1F2EA")]))
    far = [rect(1290, 170, 420, 460, "#E3D3DE", rx=8) + rect(1310, 190, 380, 420, f"url(#{n}-win)", rx=4)
           + cloud(1420, 280, 0.45) + tree(1600, 610, 200, 70) + line(1500, 190, 1500, 610, "#E3D3DE", 12),
           path("M1260 150 Q1290 400 1250 660 L1310 660 Q1330 400 1300 150 Z", fill="#D9C7E4")
           + path("M1740 150 Q1710 400 1750 660 L1690 660 Q1670 400 1700 150 Z", fill="#D9C7E4")
           + rect(1240, 140, 520, 14, "#CDB9C8", rx=7),
           frame_art(240, 200, 260, 200, ["#F6EEE2", CORAL, TEAL], 0), frame_art(540, 250, 160, 210, ["#F3F0E8", MUSTARD, BLUE], 1),
           frame_art(740, 210, 200, 150, ["#F1EDE6", LAV, GREEN2], 0)]
    mid = [  # sofa
        rect(170, 560, 820, 170, "#C9D7E6", rx=36) + rect(130, 640, 120, 170, "#BCCCDE", rx=40) + rect(910, 640, 120, 170, "#BCCCDE", rx=40)
        + rect(220, 690, 760, 120, "#C3D2E3", rx=24) + rect(240, 600, 220, 110, "#F1D893", rx=24, op=0.9) + rect(740, 600, 200, 110, "#EFC0AE", rx=24, op=0.9)
        + rect(190, 810, 20, 30, "#B6A58F") + rect(950, 810, 20, 30, "#B6A58F"),
        # lampu berdiri
        line(1110, 360, 1110, GROUND, "#BFB3A3", 8) + path("M1060 360 L1160 360 L1140 280 L1080 280 Z", fill="#F6E3B8") + ell(1110, GROUND - 4, 46, 10, "#BFB3A3"),
        # rak
        rect(1820, 380, 260, 460, "#E3D2BE", rx=6) + "".join(rect(1830, y, 240, 10, "#D2BEA6") for y in (480, 590, 700))
        + "".join(rect(1840 + i * 34, 420 + (i % 2) * 10, 26, 60 - (i % 2) * 10, c, rx=3) for i, c in enumerate([CORAL, TEAL, MUSTARD, LAV, BLUE]))]
    near = [ell(700, GROUND + 22, 520, 34, "#E9C9B2", op=0.6), plant(1220, GROUND, 1.1, "#E3C2A8"), plant(-60, GROUND, 1.3, "#C8D5E3")]
    return n, svg(n, defs, base, far, mid, near)


def office():
    n = "office"
    rng = random.Random(7)
    defs, base = wall_base(n, wall="#EEF1F4", wall2="#E3E8EE", floor="#DDE1E4", floor2="#D2D7DB")
    defs.append(grad(f"{n}-win", [(0, "#D4E6F2"), (1, "#EEF4F6")]))
    far = [rect(-100, 120, 1260, 520, f"url(#{n}-win)")]
    x = -100
    while x < 1160:
        w = rng.choice([100, 130, 160]); h = rng.choice([180, 240, 300, 360])
        far.append(rect(x, 640 - h, w, h, rng.choice(["#D6E0EA", "#DCE3EC", "#D1DBE6"])))
        far.append(windows(x, 640 - h, w, h, max(2, w // 50), max(2, h // 60), fill="#E7EEF5", gap=8, pad=10))
        x += w + 20
    far.append("".join(rect(x, 110, 22, 540, "#D3DAE2") for x in range(-110, 1200, 320)) + rect(-120, 100, 1300, 24, "#D3DAE2")
               + rect(-120, 630, 1300, 24, "#D3DAE2"))
    mid = [rect(1300, 170, 520, 300, WHITE, rx=10) + rect(1290, 160, 540, 320, "#D5DCE4", rx=12, op=0.5)
           + path("M1350 420 L1460 360 L1560 390 L1700 260", stroke="#A9D2BC", sw=10) + circ(1700, 260, 12, "#A9D2BC")
           + rect(1350, 220, 140, 14, "#D5DCE4", rx=7) + rect(1350, 250, 90, 14, "#D5DCE4", rx=7),
           wall_clock(1220, 230, 44),
           # meja dan monitor
           rect(-60, 640, 760, 24, "#D9CBB6", rx=8) + rect(-30, 664, 24, GROUND - 664, "#C9BBA6") + rect(650, 664, 24, GROUND - 664, "#C9BBA6")
           + rect(120, 470, 280, 170, "#C6CED8", rx=10) + rect(136, 486, 248, 136, "#E4EEF6", rx=6) + rect(245, 640, 30, 0.1, "#000")
           + rect(240, 610, 40, 30, "#B9C1CB") + rect(470, 590, 120, 50, "#E8DCC8", rx=6) + rect(480, 560, 30, 30, CORAL, rx=6),
           # kursi
           rect(260, 650, 170, 30, "#B9C6D6", rx=12) + rect(320, 680, 16, 120, "#AEB8C4") + rect(270, 800, 120, 12, "#AEB8C4", rx=6)]
    near = [plant(1880, GROUND, 1.2, "#E3C2A8"), rect(1460, 560, 260, GROUND - 560, "#E2E6EA", rx=8)
            + "".join(rect(1470, y, 240, 80, "#D8DDE2", rx=6) + rect(1570, y + 34, 40, 10, "#C2C9D1", rx=5) for y in (580, 676, 772 - 20))]
    return n, svg(n, defs, base, far, mid, near)


def bank_hall():
    n = "bank-hall"
    defs, base = wall_base(n, wall="#F3EDE2", wall2="#EADFCD", floor="#E9E2D6", floor2="#DCD2C2", skirting=False)
    base.append("".join(path(f"M{x} {GROUND} L{x + 60} {GROUND} L{x + 30 + (x - 900) * 0.25} 1080 L{x + (x - 900) * 0.25} 1080 Z", fill="#E0D8CA", op=0.5)
                        for x in range(-200, 2200, 240)))
    far = [rect(-300, 60, 2500, 40, "#E5D8C2"), rect(-300, 100, 2500, 14, "#DCCDB4"),
           # pintu brankas
           circ(1640, 400, 190, "#D9DEE3") + circ(1640, 400, 160, "#E7EAEE") + circ(1640, 400, 60, "#CDD3DA")
           + "".join(line(1640, 400, 1640 + 100 * c, 400 + 100 * s, "#CDD3DA", 14) for c, s in ((1, 0), (-1, 0), (0, 1), (0, -1)))
           + "".join(circ(1640 + 175 * c, 400 + 175 * s, 10, "#C3CAD2") for c, s in ((0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7)))]
    mid = []
    for x in (-120, 360, 1140, 1980):
        mid.append(rect(x - 20, 120, 160, 30, "#E3D6C1", rx=4) + rect(x, 150, 120, GROUND - 190, "#EFE6D7")
                   + "".join(rect(x + 14 + i * 26, 160, 12, GROUND - 210, "#E5DACA", rx=6) for i in range(4))
                   + rect(x - 20, GROUND - 50, 160, 50, "#E3D6C1", rx=4))
    # loket teller
    mid.append(rect(560, 560, 500, GROUND - 560, "#D9C7AB", rx=8) + rect(545, 540, 530, 30, "#E6D7BF", rx=8)
               + rect(575, 330, 220, 210, "#E4EEF3", op=0.8) + rect(825, 330, 220, 210, "#E4EEF3", op=0.8)
               + rect(560, 316, 500, 18, "#CDBEA6", rx=6) + rect(800, 316, 20, 224, "#CDBEA6")
               + rect(640, 640, 340, 120, "#CDB99B", rx=6) + circ(810, 700, 26, "#E6D7BF"))
    mid.append("".join(line(x, 0, x, 120, "#D6C8B2", 3) + path(f"M{x - 50} 170 L{x + 50} 170 L{x + 30} 120 L{x - 30} 120 Z", fill="#F4E2B6")
                       for x in (270, 1360)))
    near = [rect(1340, GROUND - 60, 30, 60, "#C9B48F") + rect(1520, GROUND - 60, 30, 60, "#C9B48F") + path(f"M1355 {GROUND - 60} Q1445 {GROUND - 10} 1535 {GROUND - 60}", stroke="#D98F86", sw=8),
            plant(110, GROUND, 1.2, "#D9C7AB")]
    return n, svg(n, defs, base, far, mid, near)


def car_dealership():
    n = "car-dealership"
    defs, base = wall_base(n, wall="#EEF2F4", wall2="#E6ECEF", floor="#ECEDEE", floor2="#DEE1E3", skirting=False)
    defs.append(grad(f"{n}-glass", [(0, "#D2E6F2"), (1, "#EAF3F2")]))
    far = [rect(-300, 140, 2500, 620, f"url(#{n}-glass)"), tree(160, 760, 280, 100), tree(700, 760, 230, 80, GREEN, GREEN2),
           tree(1500, 760, 300, 105), pine(1180, 760, 220), cloud(420, 260, 0.8), cloud(1300, 220, 0.6, op=0.8),
           rect(-300, 700, 2500, 60, "#DCE6DC")]
    mid = ["".join(rect(x, 120, 26, 650, "#D7DEE4") for x in range(-260, 2200, 380)) + rect(-300, 110, 2500, 30, "#D2D9E0")
           + rect(-300, 760, 2500, 26, "#D2D9E0"),
           bunting(-100, 960, 150, 9, [CORAL, MUSTARD, TEAL, LAV, BLUE]), bunting(960, 2020, 150, 9, [MUSTARD, TEAL, CORAL, BLUE, LAV]),
           ell(130, GROUND - 4, 250, 20, "#DADDE1") + car_shape(-80, GROUND - 14, 420, "#E8C6BB"),
           ell(1790, GROUND - 4, 250, 20, "#DADDE1") + car_shape(1580, GROUND - 14, 420, "#C6D6E8", flip=True)]
    near = ["".join(path(f"M{x} {GROUND - 330} Q{x - 16} {GROUND - 180} {x + 6} {GROUND - 30}", stroke="#CFC6BA", sw=3)
                    + ell(x, GROUND - 366, 28, 35, c) for x, c in ((520, CORAL), (560, MUSTARD), (600, TEAL), (1320, LAV), (1360, PINK), (1400, MUSTARD)))
            + rect(500, GROUND - 30, 120, 30, "#D4D9DE", rx=6) + rect(1300, GROUND - 30, 120, 30, "#D4D9DE", rx=6)]
    return n, svg(n, defs, base, far, mid, near)


def highway():
    n = "highway"
    defs, base = sky_base(n, top="#CBE2F0", bot="#EEF3EC", ground="#C9CDD2", ground2="#BFC4CA")
    base.append(rect(-400, GROUND + 26, 2720, 6, "#E7E3D6"))
    far = [cloud(260, 160, 1.0), cloud(1180, 120, 1.2, op=0.8), cloud(1740, 220, 0.7),
           path("M-260 620 Q200 420 640 600 Q1000 450 1400 590 Q1800 440 2200 600 L2200 760 L-260 760 Z", fill="#D3E3CF"),
           path("M-260 700 Q300 560 900 690 Q1400 580 2200 690 L2200 780 L-260 780 Z", fill="#C3DABB")]
    mid = [rect(-300, 760, 2500, 80, "#D6DAD0"),
           # gerbang rambu (hijau lembut, tanpa tulisan)
           rect(420, 300, 20, 460, "#B9C0C8") + rect(1480, 300, 20, 460, "#B9C0C8") + rect(420, 300, 1080, 18, "#B9C0C8")
           + rect(560, 330, 360, 150, "#A9CDB7", rx=10) + rect(1000, 330, 360, 150, "#A9CDB7", rx=10)
           + "".join(rect(600 + k * 440, 370, 200, 16, "#D7EADF", rx=8) + rect(600 + k * 440, 410, 140, 16, "#D7EADF", rx=8) for k in range(2))
           + path("M830 440 L870 440 M850 420 L870 440 L850 460", stroke="#D7EADF", sw=8)
           + path("M1270 440 L1310 440 M1290 420 L1310 440 L1290 460", stroke="#D7EADF", sw=8),
           car_shape(60, 790, 220, "#E3C3B4") + car_shape(1700, 790, 200, "#C4D3E6", flip=True)]
    near = [rect(-300, GROUND - 70, 2500, 26, "#D3D7DC", rx=8) + "".join(rect(x, GROUND - 60, 14, 60, "#C3C9D0") for x in range(-260, 2200, 200)),
            "".join(rect(x, GROUND + 12, 120, 10, "#F1EEE3", rx=5) for x in range(-200, 2200, 260))]
    return n, svg(n, defs, base, far, mid, near)


def data_center():
    n = "data-center"
    rng = random.Random(11)
    defs, base = wall_base(n, wall="#E7ECF2", wall2="#DCE3EC", floor="#DDE3EA", floor2="#D0D8E1", skirting=False)
    base.append("".join(line(x, GROUND, x + (x - 960) * 0.3, 1080, "#CBD4DE", 3, op=0.7) for x in range(-200, 2200, 160)))
    far = [rect(-300, 60, 2500, 24, "#D3DBE5"), "".join(rect(x, 84, 16, 80, "#D3DBE5") for x in range(-260, 2200, 300)),
           rect(-300, 160, 2500, 30, "#CBD5E0", rx=6),
           "".join(rect(x, 200, 160, 14, "#F3F6FA", rx=7) for x in range(-200, 2200, 360))]
    mid = []
    for i, x in enumerate(range(-200, 2200, 230)):
        if 760 < x < 1000:
            continue
        mid.append(rect(x, 300, 200, GROUND - 300, "#D2DAE4", rx=8) + rect(x + 12, 316, 176, GROUND - 330, "#C8D1DC", rx=4))
        for k in range(10):
            y = 330 + k * 48
            mid.append(rect(x + 22, y, 156, 36, "#DEE5ED", rx=4))
            for j in range(3):
                c = rng.choice(["#9ED7B5", "#9EC8E8", "#DDE4EC", "#9ED7B5", "#F3D58E"])
                mid.append(circ(x + 150 - j * 16, y + 18, 4.5, c))
            mid.append(rect(x + 34, y + 14, 60, 8, "#CDD5DF", rx=4))
    near = [path("M-300 250 Q300 290 900 250 T2200 250", stroke="#B9CBE0", sw=10), path("M-300 270 Q500 310 1100 268 T2200 272", stroke="#C9D9C7", sw=8)]
    return n, svg(n, defs, base, far, mid, near)


def factory():
    n = "factory"
    defs, base = wall_base(n, wall="#EFEAE2", wall2="#E4DDD1", floor="#DCD7CF", floor2="#D1CBC1", skirting=False)
    base.append(rect(-400, GROUND + 28, 2720, 14, "#E9D38E", op=0.6))
    far = ["".join(path(f"M{x} 260 L{x + 200} 80 L{x + 200} 260 Z", fill="#E2E9EF") + rect(x + 120, 120, 70, 130, "#DCE9F1")
                   for x in range(-300, 2200, 240)),
           rect(-300, 260, 2500, 20, "#D6CDBE"),
           "".join(path(f"M{x} 280 L{x + 120} 380 L{x + 240} 280", stroke="#D6CDBE", sw=8) for x in range(-300, 2200, 240)),
           path("M-300 420 L2200 420", stroke="#D4C3A8", sw=22) + path("M-300 460 L2200 460", stroke="#C9D6DE", sw=14)
           + "".join(rect(x, 405, 20, 70, "#C9BCA6", rx=4) for x in range(-200, 2200, 400))]
    gear = lambda cx, cy, r, c: circ(cx, cy, r, c) + "".join(  # noqa: E731
        rect(cx - r * 0.18, cy - r * 1.22, r * 0.36, r * 0.5, c, rx=4).replace("/>", f' transform="rotate({a} {cx} {cy})"/>') for a in range(0, 360, 45)) + circ(cx, cy, r * 0.4, "#EFEAE2")
    mid = [gear(1620, 300, 70, "#DCCFB9"), gear(1730, 380, 44, "#E3D3B7"),
           # lengan robot
           rect(240, 700, 140, GROUND - 700, "#E2C78E", rx=10) + path("M310 700 L380 520 L560 470", stroke="#EBCB8B", sw=46)
           + circ(310, 700, 34, "#D9B978") + circ(380, 520, 28, "#D9B978") + path("M560 470 L600 440 M560 470 L606 500", stroke="#BFA16A", sw=16),
           # tangki
           rect(1440, 470, 200, GROUND - 470, "#D4DDE5", rx=30) + rect(1660, 520, 200, GROUND - 520, "#DCE2E8", rx=30)
           + path("M1640 560 L1660 560", stroke="#C3CAD2", sw=16)]
    belt_y = 700
    near = [rect(-300, belt_y, 1500, 40, "#B9C0C8", rx=20) + "".join(circ(x, belt_y + 20, 14, "#9EA6AF") for x in range(-260, 1200, 70))
            + "".join(rect(x, belt_y + 40, 18, GROUND - belt_y - 40, "#C3CAD2") for x in (-100, 400, 900))
            + "".join(rect(x, belt_y - 76, 90, 76, "#E3C9A1", rx=4) + rect(x + 36, belt_y - 76, 18, 76, "#D6B98D") for x in (-120, 200, 520, 840))]
    return n, svg(n, defs, base, far, mid, near)


def park():
    n = "park"
    defs, base = sky_base(n, top="#C9E2F2", bot="#F1F5EA", ground="#C9DFB9", ground2="#BBD5A8")
    base.append(circ(1650, 170, 70, "#FBEDC4"))
    far = [cloud(300, 170, 1.2), cloud(1020, 120, 0.9), cloud(1400, 260, 0.6, op=0.8),
           path("M-260 640 Q300 480 820 620 Q1300 500 1700 610 Q1950 560 2200 620 L2200 840 L-260 840 Z", fill="#D7E8CB"),
           "".join(pine(x, 650 + (x % 3) * 10, 130, "#BCD7AE") for x in range(-200, 2200, 170))]
    mid = [path("M-260 760 Q500 690 1100 760 Q1600 810 2200 750 L2200 840 L-260 840 Z", fill="#C3DCB2"),
           tree(220, GROUND - 20, 380, 130), tree(1560, GROUND - 10, 420, 140, GREEN2, GREEN3), tree(1900, GROUND - 40, 300, 100, GREEN, GREEN2),
           path(f"M700 {GROUND} Q900 780 1260 770 L1340 770 Q1000 790 880 {GROUND} Z", fill="#E9DFC9")]
    near = [  # bangku
        rect(1100, GROUND - 120, 300, 22, "#D6B48F", rx=6) + rect(1100, GROUND - 170, 300, 18, "#D6B48F", rx=6)
        + rect(1120, GROUND - 100, 16, 100, "#B49572") + rect(1364, GROUND - 100, 16, 100, "#B49572"),
        lamp_post(-60, 440), "".join(ell(x, GROUND - 20, 80, 50, GREEN3) + ell(x + 60, GROUND - 30, 60, 46, GREEN2) for x in (560, 1990)),
        "".join(circ(x, GROUND - 10, 7, c) for x, c in ((480, PINK), (520, MUSTARD), (650, PINK), (1460, MUSTARD), (1500, LAV)))]
    return n, svg(n, defs, base, far, mid, near)


def classroom():
    n = "classroom"
    defs, base = wall_base(n, wall="#F1EEDF", wall2="#E7E2CE", floor="#E1D2B9", floor2="#D6C4A6")
    base.append(rect(-400, 560, 2720, 18, "#E2DAC2"))
    far = [wall_clock(1660, 150, 44),
           frame_art(1560, 290, 200, 240, ["#F7F3E8", TEAL, MUSTARD], 1),
           frame_art(-40, 260, 200, 260, ["#F7F3E8", CORAL, GREEN2], 0),
           "".join(rect(1820, 300 + i * 70, 220, 50, c, rx=8, op=0.8) for i, c in enumerate([BLUE, PINK, GREEN, MUSTARD]))]
    mid = [rect(250, 120, 1220, 560, "#CFC2A8", rx=14) + rect(266, 136, 1188, 528, "#FBFBF7", rx=8)
           + path("M330 560 L520 470 L700 500 L900 360 L1080 400", stroke="#E9E4DA", sw=8)
           + rect(300, 664, 1120, 18, "#C9BBA0", rx=6) + rect(520, 652, 60, 14, "#9EC8E8", rx=4) + rect(600, 652, 60, 14, CORAL, rx=4) + rect(680, 652, 40, 18, WHITE, rx=4)]
    near = [rect(1540, 650, 400, 24, "#D4B791", rx=8) + rect(1560, 674, 22, GROUND - 674, "#C2A47E") + rect(1900, 674, 22, GROUND - 674, "#C2A47E")
            + rect(1640, 590, 90, 60, "#E7DDCA", rx=4) + circ(1800, 615, 28, CORAL) + rect(1797, 580, 6, 12, "#9C7C5A"),
            "".join(rect(x, 600, 150, 20, "#D4B791", rx=6) + rect(x + 10, 620, 14, GROUND - 620, "#C2A47E") + rect(x + 126, 620, 14, GROUND - 620, "#C2A47E")
                    for x in (-200, 40))]
    return n, svg(n, defs, base, far, mid, near)


def paper_grid():
    n = "paper-grid"
    defs = [rgrad(f"{n}-vig", [(0, "#FBF8F1"), (1, "#F1EADC")], r=0.75)]
    base = [rect(-400, -200, 2720, 1480, f"url(#{n}-vig)")]
    far = ["".join(line(x, -200, x, 1280, "#E6E1F0", 2) for x in range(-240, 2200, 40))
           + "".join(line(-300, y, 2200, y, "#E6E1F0", 2) for y in range(-160, 1280, 40))]
    mid = ["".join(line(x, -200, x, 1280, "#D3CCE6", 3) for x in range(-240, 2200, 200))
           + "".join(line(-300, y, 2200, y, "#D3CCE6", 3) for y in range(40, 1280, 200)),
           line(-300, GROUND, 2200, GROUND, "#C7BFDC", 5)]
    near = [rect(-300, -200, 210, 1480, "#F4E3E3", op=0.6) + line(150, -200, 150, 1280, "#EBB9B9", 4),
            path("M1750 60 L1750 170 Q1750 200 1780 200 Q1810 200 1810 170 L1810 40 Q1810 10 1840 10 Q1870 10 1870 40 L1870 190",
                 stroke="#C9CED6", sw=8)]
    return n, svg(n, defs, base, far, mid, near)


def studio():
    n = "studio"
    defs = [rgrad(f"{n}-wall", [(0, "#FBF7EF"), (0.6, "#F2EADC"), (1, "#E6DAC6")], cy=0.45, r=0.75),
            grad(f"{n}-floor", [(0, "#E9DFCE"), (1, "#DDCFB9")]),
            rgrad(f"{n}-spot", [(0, "#FFFFFF"), (1, "#FFFFFF00")], r=0.5)]
    base = [rect(-400, -200, 2720, GROUND + 200, f"url(#{n}-wall)"),
            rect(-400, GROUND, 2720, 440, f"url(#{n}-floor)"),
            path(f"M-400 {GROUND - 30} Q960 {GROUND + 30} 2320 {GROUND - 30} L2320 {GROUND + 20} L-400 {GROUND + 20} Z", fill="#EDE4D5", op=0.7)]
    far = [ell(960, 380, 700, 420, f"url(#{n}-spot)", op=0.7),
           circ(250, 260, 140, "#F3E7D2", op=0.7), circ(1700, 300, 180, "#EFE6EE", op=0.6), circ(1560, 760, 90, "#E8EFE6", op=0.6)]
    mid = [ell(960, GROUND + 6, 520, 30, "#00000012"), path("M-100 120 Q200 40 420 140", stroke="#EADBC4", sw=10, op=0.7),
           path("M1500 150 Q1760 60 2040 180", stroke="#E3DCE8", sw=10, op=0.7)]
    near = ['<g opacity="0.55">' + "".join(circ(x, y, r, c) for x, y, r, c in
                                             ((160, 600, 10, MUSTARD), (1780, 560, 12, CORAL), (1680, 180, 8, TEAL), (300, 120, 7, LAV), (1100, 110, 6, MUSTARD))) + "</g>"]
    return n, svg(n, defs, base, far, mid, near)


ALL = [street, city_skyline, store_checkout, supermarket, kitchen, living_room, office, bank_hall,
       car_dealership, highway, data_center, factory, park, classroom, paper_grid, studio]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for fn in ALL:
        name, text = fn()
        (OUT / f"{name}.svg").write_text(text)
        print(name, len(text))


if __name__ == "__main__":
    main()
