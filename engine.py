"""
Maya DIY Shorts — ortak çizim/ses/render motoru.
Her video: HOOK (before/after) -> ANCHOR -> STAKES -> PROCESS A/B/C -> CU1 -> CU2 -> PAYOFF (28 sn, 9:16).
Proje şablonları projects.py içinde; senaryo seçimi generate.py içinde.
"""
import math, random, os, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
DUR = 30.0
NF = int(DUR * FPS)
FY = 1250  # duvar/zemin çizgisi
HERE = os.path.dirname(os.path.abspath(__file__))


def _find_font(names):
    dirs = [os.path.join(HERE, 'fonts'), '/usr/share/fonts/truetype/dejavu', r'C:\Windows\Fonts']
    for n in names:
        for d in dirs:
            p = os.path.join(d, n)
            if os.path.exists(p): return p
    raise FileNotFoundError(names)

FONT = _find_font(['Poppins-SemiBold.ttf', 'DejaVuSans-Bold.ttf', 'arialbd.ttf'])


# ---------------------------------------------------------------- yardımcılar
def H_(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def lerp(a, b, t): return a + (b - a) * t
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t): t = clamp(t); return t * t * (3 - 2 * t)
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 3
def mix(c1, c2, t): return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))
def shade(c, k): return tuple(max(0, min(255, int(v * k))) for v in c[:3])
def bb(p1, p2):
    x0, x1 = sorted((p1[0], p2[0])); y0, y1 = sorted((p1[1], p2[1]))
    return (x0, y0, x1, y1)
def circ(d, c, r, fill, outline=None, width=1):
    d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=fill, outline=outline, width=width)
def limb(d, p1, p2, w, col):
    w = max(1, int(w))
    d.line([p1, p2], fill=col, width=w)
    for p in (p1, p2): circ(d, p, w / 2, col)

_fonts = {}
def font(sz):
    if sz not in _fonts: _fonts[sz] = ImageFont.truetype(FONT, sz)
    return _fonts[sz]

SKIN = H_('F1C3A0'); SKIN_D = H_('D9A27F'); HAIR = H_('B04E28'); HAIR_D = H_('8A3A1C')
OVER = H_('E2A628'); OVER_D = H_('BF8A18'); TEE = H_('F8F6F1'); GLOVE = H_('C4955E')
SHOE = H_('E4D5BA'); INK = H_('3A2A22')

_cache = {}
def reset_cache(): _cache.clear()


# ---------------------------------------------------------------- avatar: MAYA (tüm serilerde sabit)
def draw_maya(img, x, fy, s=1.0, f=1, pose='stand', t=0.0, smile=0.3, arms=None, lean=None):
    """Maya: bakır topuz saç, çil, hardal tulum, beyaz tişört, taba eldiven, kafada şeffaf gözlük."""
    d = ImageDraw.Draw(img, 'RGBA')
    def P(p): return (x + f * p[0] * s, fy + p[1] * s)
    def go(p, a, L):
        r = math.radians(a); return (p[0] + math.sin(r) * L, p[1] + math.cos(r) * L)
    def sc(w): return max(1, int(w * s))

    hipy = -300.0; lean_ = 0.0
    th_b = th_f = sh_b = sh_f = 0.0
    ua_b, fa_b, ua_f, fa_f = -6, 4, 6, 14
    breathe = math.sin(t * 2 * math.pi * 0.4) * 3
    if pose in ('walk', 'carrywalk'):
        ph = t * 2 * math.pi * 1.7
        sw = 26 * math.sin(ph)
        th_f, th_b = sw, -sw
        sh_f = th_f - 30 * max(0.0, -math.cos(ph))
        sh_b = th_b - 30 * max(0.0, math.cos(ph))
        hipy = -300 + 8 * abs(math.cos(ph))
        ua_f, ua_b = -sw * 0.8, sw * 0.8
        fa_f, fa_b = ua_f + 18, ua_b + 18
        if pose == 'carrywalk':
            ua_f = ua_b = 30; fa_f = fa_b = 95
    elif pose == 'carry':
        ua_f = ua_b = 30; fa_f = fa_b = 95
    elif pose == 'setdown':
        k = ease(t)
        ua_f = ua_b = lerp(30, 25, k); fa_f = fa_b = lerp(95, 40, k)
        lean_ = lerp(0, 32, k); hipy = -300 + lerp(0, 45, k)
        th_f = lerp(0, 38, k); sh_f = lerp(0, -8, k); th_b = lerp(0, 8, k); sh_b = lerp(0, -22, k)
        breathe = 0
    elif pose in ('kneel', 'kneel_drill'):
        hipy = -172
        th_b, sh_b = -5, -90
        th_f, sh_f = 80, 0
        lean_ = 28
        if pose == 'kneel':
            ph = t * 2 * math.pi * 2.2
            ua_f = 38 + 14 * math.sin(ph); fa_f = 62 + 14 * math.sin(ph)
            ua_b = 30 + 12 * math.sin(ph + 0.4); fa_b = 58 + 12 * math.sin(ph + 0.4)
        else:
            ua_f, fa_f, ua_b, fa_b = 62, 92, 50, 88
        breathe = 0
    elif pose == 'mug':
        ua_f, fa_f = 12, 150
    if arms: ua_b, fa_b, ua_f, fa_f = arms
    if lean is not None: lean_ = lean

    hip = (0.0, hipy)
    L = 150
    kb = go(hip, th_b, L); fb = go(kb, sh_b, L)
    kf = go(hip, th_f, L); ff = go(kf, sh_f, L)
    lr = math.radians(lean_)
    ax = (math.sin(lr), -math.cos(lr))
    px = (-ax[1], ax[0])
    TL = 215
    sh = (hip[0] + ax[0] * TL, hip[1] + ax[1] * TL + breathe)
    head = (sh[0] + ax[0] * 90, sh[1] + ax[1] * 90)
    shf = (sh[0] + px[0] * 8, sh[1] + px[1] * 8)
    shb = (sh[0] - px[0] * 8, sh[1] - px[1] * 8)
    eb = go(shb, ua_b, 118); hb = go(eb, fa_b, 112)
    ef = go(shf, ua_f, 118); hf = go(ef, fa_f, 112)

    def shoe(fp, col):
        d.ellipse(bb(P((fp[0] - 22, fp[1] - 22)), P((fp[0] + 52, fp[1] + 6))), fill=col)
        d.line([P((fp[0] - 20, fp[1] + 2)), P((fp[0] + 48, fp[1] + 2))], fill=(255, 255, 255), width=sc(6))
    def arm(s0, e, h_, dk):
        k = 0.86 if dk else 1.0
        limb(d, P(s0), P(e), sc(28), shade(SKIN, k))
        limb(d, P(e), P(h_), sc(25), shade(SKIN, k))
        mid = (lerp(s0[0], e[0], 0.45), lerp(s0[1], e[1], 0.45))
        limb(d, P(s0), P(mid), sc(40), shade(TEE, k))
        circ(d, P(h_), 18 * s, shade(GLOVE, k))

    d.ellipse(bb(P((-95, -12)), P((120, 14))), fill=(40, 25, 15, 55))
    limb(d, P(hip), P(kb), sc(46), OVER_D); limb(d, P(kb), P(fb), sc(42), OVER_D)
    shoe(fb, shade(SHOE, 0.88))
    arm(shb, eb, hb, True)
    def Q(pts): return [P(p) for p in pts]
    def at(k, w):
        c = (hip[0] + ax[0] * TL * k, hip[1] + ax[1] * TL * k)
        return [(c[0] - px[0] * w, c[1] - px[1] * w), (c[0] + px[0] * w, c[1] + px[1] * w)]
    a0 = at(0, 54); a4 = at(1.0, 46)
    d.polygon(Q([a0[0], a0[1], a4[1], a4[0]]), fill=TEE)
    circ(d, P(sh), 44 * s, TEE)
    b0 = at(-0.05, 56); b1 = at(0.32, 54); b2 = at(0.30, 40); b3 = at(0.72, 38)
    d.polygon(Q([b0[0], b0[1], b1[1], b1[0]]), fill=OVER)
    d.polygon(Q([b2[0], b2[1], b3[1], b3[0]]), fill=OVER)
    s0 = (sh[0] - px[0] * 30, sh[1] - px[1] * 30); s1 = (sh[0] + px[0] * 30, sh[1] + px[1] * 30)
    d.line(Q([b3[0], s0]), fill=OVER, width=sc(13)); d.line(Q([b3[1], s1]), fill=OVER, width=sc(13))
    for bp in (b3[0], b3[1]): circ(d, P(bp), 6 * s, OVER_D)
    p0 = at(0.44, 17); p1 = at(0.62, 17)
    d.polygon(Q([p0[0], p0[1], p1[1], p1[0]]), fill=OVER_D)
    d.line(Q([b1[0], b1[1]]), fill=OVER_D, width=sc(4))
    limb(d, P(hip), P(kf), sc(46), OVER); limb(d, P(kf), P(ff), sc(42), OVER)
    shoe(ff, SHOE)
    neck_top = (head[0] - ax[0] * 40, head[1] - ax[1] * 40)
    limb(d, P(sh), P(neck_top), sc(30), SKIN_D)
    hx, hy = head
    def HP(dx, dy): return P((hx + dx, hy + dy))
    circ(d, HP(-46, -24), 31 * s, HAIR_D)
    circ(d, HP(-6, -6), 60 * s, HAIR)
    d.ellipse(bb(HP(-36, -44), HP(62, 58)), fill=SKIN)
    d.chord(bb(HP(-66, -68), HP(58, 32)), 180, 360, fill=HAIR)
    d.ellipse(bb(HP(-40, -20), HP(-2, 30)), fill=HAIR)
    d.ellipse(bb(HP(-16, -6), HP(6, 18)), fill=SKIN_D)
    d.rounded_rectangle(bb(HP(-8, -68), HP(52, -46)), radius=int(9 * s),
                        fill=(190, 228, 245, 200), outline=(90, 120, 140), width=sc(3))
    d.ellipse(bb(HP(28, -6), HP(38, 8)), fill=INK)
    d.line([HP(22, -16), HP(42, -20)], fill=HAIR_D, width=sc(4))
    d.ellipse(bb(HP(52, 0), HP(67, 15)), fill=SKIN)
    d.ellipse(bb(HP(26, 12), HP(48, 25)), fill=(240, 140, 130, 90))
    for fx_, fy_ in ((40, 9), (47, 13), (33, 14), (44, 18)):
        circ(d, HP(fx_, fy_), 1.8 * s, (170, 100, 70))
    d.arc(bb(HP(30, 20), HP(54, 34 + smile * 10)), 20, 160, fill=INK, width=sc(3))
    arm(shf, ef, hf, False)
    return {'hf': P(hf), 'hb': P(hb), 'ef': P(ef), 'fa_f': fa_f, 'head': P(head)}

def maya_think(img, x, fy, lt, f=1):
    return draw_maya(img, x, fy, f=f, pose='stand', t=lt, smile=0.1,
                     arms=(-4, 30, 20, 150) if lt > 1.2 else None)


# ---------------------------------------------------------------- aletler
def tool_sander(img, info):
    d = ImageDraw.Draw(img, 'RGBA'); hx, hy = info['hf']
    d.rounded_rectangle((hx - 40, hy + 4, hx + 50, hy + 40), radius=8, fill=H_('E07B2F'))
    d.rectangle((hx - 44, hy + 34, hx + 54, hy + 46), fill=H_('3E3E3E'))
    circ(d, info['hf'], 18, GLOVE)
    return (hx, hy + 40)

def tool_drill(img, info, f=-1, jitter=0.0):
    d = ImageDraw.Draw(img, 'RGBA')
    hx, hy = info['hf'][0] + jitter, info['hf'][1] + jitter
    d.polygon([(hx - f * 30, hy - 30), (hx + f * 70, hy - 30), (hx + f * 70, hy + 5), (hx - f * 30, hy + 5)], fill=H_('E07B2F'))
    d.rectangle(bb((hx - f * 10, hy), (hx + f * 22, hy + 55)), fill=H_('3E3E3E'))
    tip = (hx + f * 120, hy - 12)
    d.line([(hx + f * 70, hy - 12), tip], fill=H_('9A9A9A'), width=8)
    circ(d, (hx, hy), 18, GLOVE)
    return tip

def tool_hammer(img, info, ang):
    d = ImageDraw.Draw(img, 'RGBA')
    hx, hy = info['hf']
    a = math.radians(ang + 25)
    dirx, diry = -math.sin(a), math.cos(a)
    hend = (hx + dirx * 70, hy + diry * 70)
    d.line([info['hf'], hend], fill=H_('A0703F'), width=12)
    px_, py_ = -diry, dirx
    d.line([(hend[0] - px_ * 30, hend[1] - py_ * 30), (hend[0] + px_ * 22, hend[1] + py_ * 22)], fill=H_('4A4A4A'), width=22)
    circ(d, info['hf'], 18, GLOVE)
    return hend

def tool_roller(img, info, col, f=1):
    d = ImageDraw.Draw(img, 'RGBA'); hx, hy = info['hf']
    rx = hx + f * 55
    d.line([(hx, hy), (rx, hy - 40)], fill=H_('777777'), width=7)
    d.rounded_rectangle((rx - 16, hy - 80, rx + 16, hy - 10), radius=12, fill=col, outline=shade(col, 0.8), width=3)
    circ(d, (hx, hy), 18, GLOVE)
    return (rx, hy - 45)


# ---------------------------------------------------------------- ahşap / palet
def grain(d, x0, y0, x1, y1, col, seed, n=4):
    rnd = random.Random(seed)
    for _ in range(n):
        y = rnd.uniform(y0 + 2, y1 - 2)
        d.line([(x0 + rnd.uniform(0, 20), y), (x1 - rnd.uniform(0, 20), y + rnd.uniform(-2, 2))],
               fill=shade(col, rnd.uniform(0.82, 0.92)), width=2)

def draw_pallet(img, cx, by, col, w=440, legs=0, s=1.0):
    d = ImageDraw.Draw(img, 'RGBA')
    dx, dy = 90 * s, -55 * s
    front = shade(col, 0.84); side = shade(col, 0.66); gap = shade(col, 0.38)
    x0, x1 = cx - w * s / 2, cx + w * s / 2
    by2 = by - legs * s
    if legs:
        for lx in (x0 + dx + 14, x1 + dx - 44):
            d.rectangle((lx, by2 + dy - 4, lx + 30 * s, by + dy), fill=shade(col, 0.44))
    d.ellipse((x0 - 10, by - 16, x1 + dx + 10, by + 22), fill=(40, 25, 15, 22 if legs else 60))
    t0 = by2 - 94 * s
    d.polygon([(x1, t0), (x1 + dx, t0 + dy), (x1 + dx, by2 + dy), (x1, by2)], fill=side)
    d.polygon([(x0, t0), (x1, t0), (x1 + dx, t0 + dy), (x0 + dx, t0 + dy)], fill=gap)
    n = 5
    for i in range(n - 1, -1, -1):
        a = i / n; b = a + 0.72 / n
        d.polygon([(x0 + dx * a, t0 + dy * a), (x1 + dx * a, t0 + dy * a),
                   (x1 + dx * b, t0 + dy * b), (x0 + dx * b, t0 + dy * b)], fill=col)
        d.line([(x0 + dx * b + 20, t0 + dy * lerp(a, b, 0.5)), (x1 + dx * b - 30, t0 + dy * lerp(a, b, 0.5))],
               fill=shade(col, 0.9), width=2)
    d.rectangle((x0, by2 - 76 * s, x1, by2 - 16 * s), fill=gap)
    for bx in (x0, cx - 28 * s, x1 - 56 * s):
        d.rectangle((bx, by2 - 76 * s, bx + 56 * s, by2 - 16 * s), fill=shade(col, 0.76))
    d.rectangle((x0, by2 - 16 * s, x1, by2), fill=front)
    d.rectangle((x0, t0, x1, t0 + 18 * s), fill=front)
    d.line([(x0, t0), (x1, t0)], fill=shade(col, 1.12), width=2)
    grain(d, x0, t0, x1, t0 + 18 * s, front, 11, 2)
    grain(d, x0, by2 - 16 * s, x1, by2, front, 12, 2)
    for bx in (x0 + 28 * s, cx, x1 - 28 * s):
        circ(d, (bx, t0 + 9 * s), 2.5 * s, (60, 55, 50))
    if legs:
        for lx in (x0 + 14, x1 - 44):
            d.rectangle((lx, by2, lx + 30 * s, by), fill=shade(col, 0.5))
    return {'t0': t0, 'x0': x0, 'x1': x1, 'dx': dx, 'dy': dy, 'by2': by2}

def draw_panel(img, r, col, shadow=True):
    d = ImageDraw.Draw(img, 'RGBA')
    x0, y0, x1, y1 = r
    if shadow:
        d.polygon([(x1, y0 + 10), (x1 + 26, y0 + 22), (x1 + 26, y1), (x1, y1)], fill=(40, 25, 15, 50))
    d.rectangle(r, fill=shade(col, 0.36))
    for k in (0.04, 0.47, 0.9):
        sx = lerp(x0, x1, k); d.rectangle((sx, y0, sx + (x1 - x0) * 0.06, y1), fill=shade(col, 0.62))
    n = 5; hgt = (y1 - y0) / n
    for i in range(n):
        ya = y0 + i * hgt; yb = ya + hgt * 0.74
        d.rectangle((x0, ya, x1, yb), fill=col)
        d.line([(x0, ya), (x1, ya)], fill=shade(col, 1.1), width=2)
        grain(d, x0, ya, x1, yb, col, 30 + i, 3)
        for k in (0.07, 0.5, 0.93):
            circ(d, (lerp(x0, x1, k), (ya + yb) / 2), 2.5, (60, 55, 50))

def draw_plant_pot(img, x, y, s=1.0, pot=H_('C4693F'), seed=3):
    d = ImageDraw.Draw(img, 'RGBA')
    d.ellipse((x - 80 * s, y - 15 * s, x + 80 * s, y + 15 * s), fill=(40, 25, 15, 60))
    d.polygon([(x - 70 * s, y - 120 * s), (x + 70 * s, y - 120 * s), (x + 50 * s, y), (x - 50 * s, y)], fill=pot)
    d.rectangle((x - 78 * s, y - 130 * s, x + 78 * s, y - 106 * s), fill=shade(pot, 0.88))
    rnd = random.Random(seed)
    for _ in range(26):
        lx, ly = x + rnd.uniform(-80, 80) * s, y + rnd.uniform(-230, -120) * s
        d.ellipse((lx - 22 * s, ly - 14 * s, lx + 22 * s, ly + 14 * s),
                  fill=rnd.choice([H_('5E8C4A'), H_('7BA65A'), H_('4E7A3E')]))
    for vx in (-60, 65):
        for i in range(7):
            vy = y - 110 * s + i * 26 * s
            d.ellipse((x + (vx - 14 + (i % 2) * 10) * s, vy - 9 * s, x + (vx + 14 + (i % 2) * 10) * s, vy + 9 * s),
                      fill=H_('6A9A50'))

def draw_succulent(d, cx, cy, r, ys=0.62):
    cols = [H_('5F8F78'), H_('79A98F'), H_('98C2A8'), H_('BADBC4')]
    for k in range(4):
        rk = r * (1 - k * 0.22); n = 11 - k * 2; off = k * 0.4
        for i in range(n):
            a = off + 2 * math.pi * i / n
            tip = (cx + math.cos(a) * rk, cy + math.sin(a) * rk * ys - k * r * 0.1)
            bl = (cx + math.cos(a - 0.4) * rk * 0.35, cy + math.sin(a - 0.4) * rk * 0.35 * ys - k * r * 0.1)
            br = (cx + math.cos(a + 0.4) * rk * 0.35, cy + math.sin(a + 0.4) * rk * 0.35 * ys - k * r * 0.1)
            d.polygon([bl, tip, br, (cx, cy - k * r * 0.1)], fill=cols[k])
            circ(d, tip, max(1.5, r * 0.035), (214, 140, 140))


# ---------------------------------------------------------------- evcil hayvanlar
def draw_pet_walk(img, pet, x, y, s, t, f=-1):
    d = ImageDraw.Draw(img, 'RGBA')
    C, D, L = pet['col'], pet['dark'], pet['light']
    def P(px_, py_): return (x + f * px_ * s, y + py_ * s)
    ph = t * 2 * math.pi * 3.2
    d.ellipse(bb(P(-110, -8), P(110, 10)), fill=(40, 25, 15, 55))
    if pet['kind'] == 'dog':
        wag = 18 * math.sin(t * 2 * math.pi * 5)
        limb(d, P(-85, -85), P(-125, -135 + wag), 16 * s, D)
        for i, (lx, dk) in enumerate(((-60, True), (50, True), (-40, False), (70, False))):
            sw = 14 * math.sin(ph + (math.pi if (i % 2) else 0))
            limb(d, P(lx, -60), P(lx + sw, 0), 20 * s, D if dk else C)
        d.ellipse(bb(P(-100, -115), P(90, -40)), fill=C)
        d.ellipse(bb(P(-60, -70), P(60, -44)), fill=L)
        circ(d, P(100, -125), 42 * s, C)
        d.ellipse(bb(P(108, -126), P(150, -96)), fill=L)
        circ(d, P(150, -114), 8 * s, INK)
        d.ellipse(bb(P(64, -140), P(92, -86)), fill=D)
        circ(d, P(112, -134), 5 * s, INK)
        d.ellipse(bb(P(124, -100), P(138, -84)), fill=(232, 120, 120))
    else:
        sway = 10 * math.sin(t * 2 * math.pi * 1.2)
        d.line([P(-80, -75), P(-120, -120), P(-112 + sway, -185)], fill=D, width=int(13 * s), joint='curve')
        circ(d, P(-112 + sway, -185), 6.5 * s, D)
        for i, (lx, dk) in enumerate(((-55, True), (45, True), (-35, False), (62, False))):
            sw = 12 * math.sin(ph + (math.pi if (i % 2) else 0))
            limb(d, P(lx, -55), P(lx + sw, 0), 14 * s, D if dk else C)
        d.ellipse(bb(P(-90, -100), P(80, -42)), fill=C)
        if pet.get('stripes'):
            for sx in (-50, -20, 10, 40):
                d.arc(bb(P(sx - 14, -100), P(sx + 14, -60)), 200, 340, fill=D, width=int(5 * s))
        circ(d, P(92, -112), 32 * s, C)
        for ex in (70, 104):
            d.polygon([P(ex - 14, -130), P(ex + 12, -134), P(ex, -162)], fill=C)
            d.polygon([P(ex - 7, -134), P(ex + 6, -136), P(ex, -152)], fill=(235, 160, 160))
        circ(d, P(104, -114), 5 * s, INK)
        circ(d, P(122, -104), 4 * s, (225, 120, 130))
        for wy in (-104, -98):
            d.line([P(118, wy), P(150, wy - 4)], fill=(250, 250, 250, 170), width=2)

def draw_pet_curl(img, pet, x, y, s, t):
    d = ImageDraw.Draw(img, 'RGBA')
    C, D, L = pet['col'], pet['dark'], pet['light']
    br = 1 + 0.03 * math.sin(t * 2 * math.pi * 0.6)
    def P(px_, py_): return (x + px_ * s, y + py_ * s * (br if py_ < 0 else 1))
    if pet['kind'] == 'dog':
        d.ellipse(bb(P(-105, -95), P(105, 0)), fill=C)
        d.ellipse(bb(P(20, -85), P(100, -10)), fill=shade(C, 0.93))
        d.arc(bb(P(-100, -60), P(95, 10)), 20, 170, fill=D, width=int(18 * s))
        circ(d, P(-78, -40), 40 * s, C)
        d.ellipse(bb(P(-128, -42), P(-86, -12)), fill=L)
        circ(d, P(-126, -30), 7 * s, INK)
        d.ellipse(bb(P(-66, -62), P(-40, -12)), fill=D)
        d.arc(bb(P(-100, -54), P(-80, -40)), 0, 180, fill=INK, width=int(3 * s))
        d.ellipse(bb(P(-130, -10), P(-96, 4)), fill=L)
    else:
        d.ellipse(bb(P(-85, -78), P(85, 0)), fill=C)
        if pet.get('stripes'):
            for sx in (-30, 0, 30, 55):
                d.arc(bb(P(sx - 16, -80), P(sx + 16, -40)), 200, 340, fill=D, width=int(5 * s))
        d.arc(bb(P(-95, -45), P(80, 12)), 15, 175, fill=D, width=int(14 * s))
        circ(d, P(-66, -34), 32 * s, C)
        for ex in (-86, -52):
            d.polygon([P(ex - 13, -52), P(ex + 12, -56), P(ex, -86)], fill=C)
            d.polygon([P(ex - 6, -56), P(ex + 5, -58), P(ex, -76)], fill=(235, 160, 160))
        d.arc(bb(P(-86, -40), P(-70, -28)), 0, 180, fill=INK, width=int(3 * s))
        d.arc(bb(P(-62, -40), P(-46, -28)), 0, 180, fill=INK, width=int(3 * s))
        circ(d, P(-66, -20), 4 * s, (225, 120, 130))
        d.ellipse(bb(P(-100, -8), P(-66, 4)), fill=L)


# ---------------------------------------------------------------- oda
PALETTES = {
    'cream':  dict(wall=('EEE7DB', 'E2D8C7'), floor='C79C6E', art=('D98E5F', '7F9A7A'), frame='6B5140'),
    'sage':   dict(wall=('DCE3D2', 'CBD4BF'), floor='BE9468', art=('C9785A', 'E8C07A'), frame='4F5B48'),
    'blush':  dict(wall=('F2DED6', 'E6CBC0'), floor='C29A72', art=('8FA58A', 'D98E5F'), frame='7A5448'),
    'greige': dict(wall=('E5E0D8', 'D4CEC4'), floor='A87C56', art=('5E7A8C', 'D9B26F'), frame='3F3A36'),
    'sky':    dict(wall=('DCE6EE', 'CAD6E0'), floor='C9A37B', art=('E0A458', '8C6E9E'), frame='55606B'),
}

def room(pal, golden=False):
    key = ('room', pal, golden)
    if key in _cache: return _cache[key]
    p = PALETTES[pal]
    img = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(img, 'RGBA')
    wt, wb = H_(p['wall'][0]), H_(p['wall'][1])
    if golden:
        wt, wb = mix(wt, H_('F4CFA0'), 0.55), mix(wb, H_('E6B98A'), 0.55)
    for y in range(FY):
        d.line([(0, y), (W, y)], fill=mix(wt, wb, y / FY))
    d.rectangle((110, 560, 380, 890), fill=H_('FBF8F2'), outline=H_(p['frame']), width=10)
    d.ellipse((170, 640, 300, 770), fill=H_(p['art'][0]))
    d.pieslice((200, 720, 340, 860), 180, 360, fill=H_(p['art'][1]))
    st, sb = (H_('F7B866'), H_('FCE2B0')) if golden else (H_('BFDDF0'), H_('EAF4F8'))
    for y in range(380, 900):
        d.line([(640, y), (960, y)], fill=mix(st, sb, (y - 380) / 520))
    d.rectangle((630, 370, 970, 910), outline=H_('FFFFFF'), width=18)
    d.line([(800, 380), (800, 900)], fill=H_('FFFFFF'), width=12)
    d.line([(640, 640), (960, 640)], fill=H_('FFFFFF'), width=12)
    d.rectangle((610, 905, 990, 928), fill=H_('F7F3EC'))
    fl = H_(p['floor'])
    if golden: fl = mix(fl, H_('D19050'), 0.2)
    for y in range(FY, H):
        d.line([(0, y), (W, y)], fill=shade(fl, lerp(1.04, 0.86, (y - FY) / (H - FY))))
    rnd = random.Random(5)
    yk, k = FY, 0
    while yk < H:
        yn = yk + 26 + k * 9
        d.line([(0, yn), (W, yn)], fill=shade(fl, 0.8), width=2)
        for sx in np.arange(rnd.uniform(0, 300), W, 380 + k * 20):
            d.line([(sx, yk), (sx, yn)], fill=shade(fl, 0.82), width=2)
        yk = yn; k += 1
    d.rectangle((0, FY - 28, W, FY), fill=H_('F4EFE6'))
    d.line([(0, FY - 28), (W, FY - 28)], fill=H_('D8CFBF'), width=3)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    bc = (255, 190, 110) if golden else (255, 255, 245)
    od.polygon([(650, 390), (955, 390), (760, 1520), (250, 1520)], fill=bc + (38 if golden else 26,))
    od.polygon([(430, 1300), (800, 1300), (720, 1560), (240, 1560)], fill=bc + (50 if golden else 34,))
    img = Image.alpha_composite(img.convert('RGBA'), ov.filter(ImageFilter.GaussianBlur(18))).convert('RGB')
    if golden:
        ImageDraw.Draw(img, 'RGBA').rectangle((0, 0, W, H), fill=(255, 150, 60, 20))
    _cache[key] = img
    return img

def _grad(d, y0, y1, c0, c1, x0=0, x1=W):
    for y in range(int(y0), int(y1)):
        d.line([(x0, y), (x1, y)], fill=mix(c0, c1, (y - y0) / max(1, y1 - y0)))

def _warm(img, golden, a=22):
    if golden: ImageDraw.Draw(img, 'RGBA').rectangle((0, 0, W, H), fill=(255, 150, 60, a))
    return img

def _sky(img, golden, y1):
    d = ImageDraw.Draw(img, 'RGBA')
    if golden:
        _grad(d, 0, y1, H_('E9785A'), H_('FBD6A0'))
        glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        circ(ImageDraw.Draw(glow), (790, y1 - 150), 200, (255, 220, 150, 170))
        img.paste(Image.alpha_composite(img.convert('RGBA'), glow.filter(ImageFilter.GaussianBlur(50))).convert('RGB'))
        circ(ImageDraw.Draw(img), (790, y1 - 150), 80, (255, 236, 190))
    else:
        _grad(d, 0, y1, H_('8EC9EE'), H_('E3F3F8'))
        r = random.Random(2)
        for _ in range(5):
            cx, cy = r.uniform(0, W), r.uniform(120, y1 - 300)
            for k in range(4):
                d.ellipse((cx - 90 + k * 45, cy - 30 - (k % 2) * 25, cx + k * 45, cy + 30), fill=(255, 255, 255, 170))

def _tiles(d, col, x_step=150):
    for y in range(FY, H):
        d.line([(0, y), (W, y)], fill=shade(col, lerp(1.04, 0.86, (y - FY) / (H - FY))))
    yk, k = FY, 0
    while yk < H:
        yk += 40 + k * 16; k += 1
        d.line([(0, yk), (W, yk)], fill=shade(col, 0.78), width=3)
    for x in range(-900, W + 900, x_step):
        d.line([(W / 2 + (x - W / 2) * 0.55, FY), (W / 2 + (x - W / 2) * 1.7, H)], fill=shade(col, 0.78), width=3)

def bg_garden(pal, golden):
    img = Image.new('RGB', (W, H)); _sky(img, golden, 920)
    d = ImageDraw.Draw(img, 'RGBA')
    r = random.Random(6)
    greens = [H_('7FA86A'), H_('6A955A'), H_('5C8A4E')]
    for _ in range(28):
        x, rr = r.uniform(-50, W + 50), r.uniform(60, 120)
        c = r.choice(greens); c = mix(c, H_('C98A4B'), 0.25) if golden else c
        circ(d, (x, 900 - r.uniform(0, 80)), rr, c)
    fc = H_('B98A5E') if not golden else H_('B07A4E')
    for i, x in enumerate(range(-10, W + 10, 70)):
        c = shade(fc, 0.92 + (i % 3) * 0.05)
        d.polygon([(x, FY), (x, 910), (x + 32, 880), (x + 64, 910), (x + 64, FY)], fill=c)
        d.line([(x + 64, 905), (x + 64, FY)], fill=shade(fc, 0.6), width=4)
    for y in (980, 1170): d.rectangle((0, y, W, y + 22), fill=shade(fc, 0.78))
    for x in list(range(-40, 330, 70)) + list(range(760, W + 60, 70)):
        circ(d, (x, FY - 30 - r.uniform(0, 40)), r.uniform(50, 80), r.choice(greens))
    for y in range(FY, 1330): d.line([(0, y), (W, y)], fill=mix(H_('7DAA55'), H_('6B9A48'), (y - FY) / 80))
    for _ in range(400):
        x = r.uniform(0, W); y = r.uniform(FY + 4, 1330)
        d.line([(x, y), (x + r.uniform(-4, 4), y - r.uniform(8, 18))], fill=H_('8CBB60'), width=2)
    for y in range(1330, H): d.line([(0, y), (W, y)], fill=shade(H_('CFC6B8'), lerp(1.02, 0.84, (y - 1330) / (H - 1330))))
    yk, k = 1330, 0
    while yk < H:
        yn = yk + 60 + k * 18
        d.line([(0, yn), (W, yn)], fill=H_('A89F92'), width=4)
        for sx in np.arange((k % 2) * 90, W, 180 + k * 12): d.line([(sx, yk), (sx, yn)], fill=H_('A89F92'), width=4)
        yk = yn; k += 1
    d.rectangle((0, 1326, W, 1336), fill=H_('9C9385'))
    return _warm(img, golden)

def bg_balcony(pal, golden):
    img = Image.new('RGB', (W, H)); _sky(img, golden, 1000)
    d = ImageDraw.Draw(img, 'RGBA')
    r = random.Random(4)
    x = -20
    while x < W:
        w = r.uniform(70, 160); top = r.uniform(560, 860)
        bc = H_('6E5A6E') if golden else H_('9FB3C8')
        d.rectangle((x, top, x + w, 1000), fill=shade(bc, r.uniform(0.85, 1.05)))
        for wy in np.arange(top + 20, 990, 34):
            for wx in np.arange(x + 12, x + w - 12, 26):
                if r.random() < 0.55:
                    d.rectangle((wx, wy, wx + 12, wy + 16), fill=H_('FFD27A') if golden and r.random() < 0.6 else shade(bc, 1.2))
        x += w + r.uniform(4, 20)
    d.rectangle((0, 1000, W, FY), fill=H_(PALETTES[pal]['wall'][1]))
    d.rectangle((0, 0, 150, FY), fill=H_(PALETTES[pal]['wall'][0]))
    d.rectangle((130, 0, 152, FY), fill=H_('F4F1EC'))
    tile = {'cream': 'D8CFC3', 'sage': 'C9C0B2', 'blush': 'C98B6B', 'greige': 'B7B1A8', 'sky': 'CFC8BD'}[pal]
    _tiles(d, H_(tile))
    for px in range(150, W + 20, 230):
        d.rectangle((px + 14, 960, px + 230, FY - 10), fill=(255, 255, 255, 45))
        d.line([(px + 60, 980), (px + 20, 1080)], fill=(255, 255, 255, 90), width=6)
        d.rectangle((px, 960, px + 14, FY), fill=H_('4A4A4A'))
    d.rectangle((150, 948, W, 970), fill=H_('5A5A5A'))
    d.rectangle((150, FY - 12, W, FY), fill=H_('5A5A5A'))
    return _warm(img, golden)

def bg_garage(pal, golden):
    img = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(img, 'RGBA')
    wc = H_('C9C5BE')
    _grad(d, 0, FY, shade(wc, 1.03), shade(wc, 0.92))
    for y in range(0, FY, 80):
        d.line([(0, y), (W, y)], fill=shade(wc, 0.85), width=3)
        for x in range((y // 80 % 2) * 80, W, 160): d.line([(x, y), (x, y + 80)], fill=shade(wc, 0.85), width=3)
    d.rectangle((560, 470, 1010, 900), fill=H_('C9A77C'), outline=H_('8E7250'), width=8)
    for y in range(490, 890, 28):
        for x in range(580, 1000, 28): circ(d, (x, y), 3, H_('8E7250'))
    d.rectangle((600, 520, 616, 700), fill=H_('A0703F')); d.rectangle((580, 510, 650, 540), fill=H_('4A4A4A'))
    d.polygon([(700, 520), (860, 520), (860, 560), (700, 640)], fill=H_('9A9A9A')); d.rectangle((860, 515, 900, 570), fill=H_('C8453A'))
    d.rectangle((930, 520, 950, 700), fill=H_('7A7A7A')); circ(d, (940, 520), 22, H_('7A7A7A'))
    circ(d, (720, 780), 42, H_('E8B830')); circ(d, (720, 780), 16, H_('4A4A4A'))
    d.rectangle((800, 740, 980, 760), fill=H_('4A4A4A'))
    d.rectangle((70, 640, 460, 660), fill=H_('6B4A2F'))
    for bx in (100, 420): d.polygon([(bx, 660), (bx + 12, 660), (bx + 12, 700)], fill=H_('4A4A4A'))
    for i, c in enumerate(('C8453A', '2F5D8C', 'E8B830')):
        x = 100 + i * 80
        d.rectangle((x, 560, x + 60, 640), fill=H_(c)); d.ellipse((x, 552, x + 60, 568), fill=shade(H_(c), 1.2))
    d.rectangle((340, 570, 440, 640), fill=H_('C9A06A')); d.line([(340, 600), (440, 600)], fill=H_('A07A48'), width=3)
    d.rectangle((380, 80, 700, 104), fill=H_('F4F4F0'))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((200, 40, 880, 360), fill=(255, 255, 240, 70) if not golden else (255, 190, 110, 90))
    img = Image.alpha_composite(img.convert('RGBA'), glow.filter(ImageFilter.GaussianBlur(50))).convert('RGB')
    d = ImageDraw.Draw(img, 'RGBA')
    fc = H_('A39E97')
    for y in range(FY, H): d.line([(0, y), (W, y)], fill=shade(fc, lerp(1.05, 0.82, (y - FY) / (H - FY))))
    for y in (1420, 1700): d.line([(0, y), (W, y)], fill=shade(fc, 0.75), width=3)
    d.line([(W / 2, FY), (W / 2, H)], fill=shade(fc, 0.75), width=3)
    r = random.Random(8)
    for _ in range(6):
        x, y = r.uniform(100, W - 100), r.uniform(1350, 1850)
        d.ellipse((x - 90, y - 25, x + 90, y + 25), fill=(60, 55, 50, 26))
    d.rectangle((0, FY - 10, W, FY), fill=shade(wc, 0.7))
    return _warm(img, golden, 30)

LOCATIONS = ('living', 'garden', 'balcony', 'garage')
OUTDOOR = ('garden', 'balcony')
def scene_bg(loc, pal, golden=False):
    if loc == 'living': return room(pal, golden)
    key = ('bg', loc, pal, golden)
    if key not in _cache:
        _cache[key] = {'garden': bg_garden, 'balcony': bg_balcony, 'garage': bg_garage}[loc](pal, golden)
    return _cache[key]

def vignette():
    if 'vig' in _cache: return _cache['vig']
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
    a = (np.clip((r - 0.45) / 0.55, 0, 1) ** 1.6 * 120).astype(np.uint8)
    v = Image.new('RGBA', (W, H), (20, 10, 5, 0)); v.putalpha(Image.fromarray(a))
    _cache['vig'] = v
    return v

_mr = random.Random(9)
MOTES = [(_mr.uniform(300, 900), _mr.uniform(500, 1480), _mr.uniform(0, 6.28), _mr.uniform(2, 4.5)) for _ in range(40)]
def draw_motes(img, t, col=(255, 250, 235)):
    d = ImageDraw.Draw(img, 'RGBA')
    for (x, y, ph, r) in MOTES:
        xx = x + 22 * math.sin(t * 0.5 + ph) - (y - 500) * 0.35
        yy = y + 30 * math.sin(t * 0.35 + ph * 2)
        circ(d, (xx, yy), r, col + (int(70 + 60 * math.sin(t * 1.3 + ph * 3)),))

def dust(img, t, origin, rate=45, life=1.1, seed=3, col=(238, 226, 205), spread=1.0):
    d = ImageDraw.Draw(img, 'RGBA')
    n = int(t * rate)
    for k in range(max(0, n - int(life * rate)), n):
        rr = random.Random(seed * 10007 + k)
        age = t - k / rate
        if age < 0 or age > life: continue
        vx = rr.uniform(-140, 140) * spread; vy = rr.uniform(-170, -30) * spread
        x = origin[0] + vx * age; y = origin[1] + vy * age + 60 * age * age
        circ(d, (x, y), rr.uniform(3, 7) * (1 + age * 1.5), col + (int(170 * (1 - age / life)),))

def props_front(img, can_col, label):
    d = ImageDraw.Draw(img, 'RGBA')
    d.ellipse((850, 1760, 1050, 1800), fill=(40, 25, 15, 60))
    d.rounded_rectangle((860, 1690, 1035, 1785), radius=10, fill=H_('C8453A'))
    d.rectangle((860, 1712, 1035, 1722), fill=H_('9E3129'))
    d.rounded_rectangle((915, 1662, 980, 1694), radius=10, outline=H_('3E3E3E'), width=9)
    d.ellipse((60, 1770, 180, 1800), fill=(40, 25, 15, 60))
    d.rectangle((70, 1700, 170, 1785), fill=H_('8C8C8C'))
    d.ellipse((70, 1688, 170, 1712), fill=H_('B0B0B0'))
    d.rectangle((70, 1725, 170, 1765), fill=can_col)
    d.text((120, 1745), label, fill=(250, 245, 235) if sum(can_col) < 450 else (40, 30, 25), font=font(20), anchor='mm')

def zoom(img, z, c):
    if z <= 1.0001: return img
    w, h = W / z, H / z
    x0 = clamp(c[0] - w / 2, 0, W - w); y0 = clamp(c[1] - h / 2, 0, H - h)
    return img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.BILINEAR)


# ---------------------------------------------------------------- yakın planlar
def wood_tex(w, h, base, seed, n=70):
    rnd = random.Random(seed)
    img = Image.new('RGB', (w, h), base); d = ImageDraw.Draw(img)
    for _ in range(n):
        y0 = rnd.uniform(-20, h + 20); amp = rnd.uniform(3, 16); fr = rnd.uniform(0.002, 0.008); ph = rnd.uniform(0, 6.28)
        pts = [(x, y0 + amp * math.sin(x * fr + ph) + 0.5 * amp * math.sin(x * fr * 2.7 + ph * 1.3)) for x in range(-10, w + 30, 20)]
        d.line(pts, fill=shade(base, rnd.uniform(0.8, 0.97)), width=rnd.randint(1, 4))
    for _ in range(2):
        kx, ky = rnd.uniform(100, w - 100), rnd.uniform(40, h - 40)
        for rr in range(4, 40, 7):
            d.ellipse((kx - rr * 2.2, ky - rr, kx + rr * 2.2, ky + rr), outline=shade(base, 0.72), width=2)
    return img.filter(ImageFilter.GaussianBlur(0.8))

SLATS = [(110, 640), (700, 1220), (1280, 1810)]
def boards(base, seed):
    key = ('boards', base, seed)
    if key not in _cache:
        img = Image.new('RGB', (W, H), H_('2B1E17'))
        for i, (a, b) in enumerate(SLATS):
            img.paste(wood_tex(W, b - a, base, seed + i), (0, a))
        _cache[key] = img
    return _cache[key]

def cu_brush(lt, raw_col, fin_col):
    raw = boards(raw_col, 40); st = boards(fin_col, 40)
    frame = raw.copy()
    p = ease(clamp((lt - 0.1) / 2.2))
    bx = lerp(-60, W + 260, p)
    mask = Image.new('L', (W, H), 0); md = ImageDraw.Draw(mask)
    md.rectangle((0, SLATS[0][0], W, SLATS[0][1]), fill=255)
    a, b = SLATS[1]
    md.polygon([(0, a)] + [(bx - 70 + 16 * math.sin(y * 0.03 + lt * 3), y) for y in range(a, b + 1, 20)] + [(0, b)], fill=255)
    frame.paste(st, (0, 0), mask)
    d = ImageDraw.Draw(frame, 'RGBA')
    for k, al in ((260, 18), (160, 26), (70, 40)):
        if bx - 70 <= 0: break
        d.rectangle((max(0, bx - 70 - k), a + 40, bx - 70, b - 40), fill=(255, 245, 225, al))
    y0, y1 = 780, 1140
    d.rounded_rectangle((bx - 60, y0, bx + 6, y1), radius=10, fill=shade(fin_col, 0.7))
    for yy in range(y0 + 15, y1, 22):
        d.line([(bx - 56, yy), (bx + 2, yy + 3)], fill=shade(fin_col, 0.9), width=3)
    d.rectangle((bx - 115, y0 + 20, bx - 58, y1 - 20), fill=H_('B9B9B9'))
    for xx in (bx - 100, bx - 80):
        d.line([(xx, y0 + 22), (xx, y1 - 22)], fill=H_('8F8F8F'), width=4)
    d.polygon([(bx - 115, 860), (bx - 115, 1060), (bx - 580, 1010), (bx - 580, 910)], fill=H_('D6A56B'))
    d.polygon([(bx - 390, 900), (bx - 380, 1060), (bx - 800, 1250), (bx - 820, 1080)], fill=SKIN)
    d.ellipse((bx - 400, 850, bx - 230, 1075), fill=GLOVE)
    for i in range(4):
        d.ellipse((bx - 250 - i * 10, 860 + i * 48, bx - 190 - i * 10, 910 + i * 48), fill=shade(GLOVE, 0.95))
    d.polygon([(bx - 400, 890), (bx - 380, 1070), (bx - 430, 1080), (bx - 450, 880)], fill=shade(GLOVE, 0.85))
    return frame

def concrete(col):
    key = ('conc', col)
    if key not in _cache:
        rng = np.random.default_rng(4)
        n = rng.normal(0, 1, (H // 4, W // 4))
        n = np.array(Image.fromarray(((n * 30) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), dtype=float)
        fine = rng.normal(0, 1, (H, W)) * 6
        base = np.array(col, dtype=float)[None, None, :] * (0.92 + (n[..., None] - 128) / 900) + fine[..., None]
        img = Image.fromarray(base.clip(0, 255).astype(np.uint8))
        d = ImageDraw.Draw(img, 'RGBA'); r = random.Random(8)
        for _ in range(900):
            x, y, rr = r.uniform(0, W), r.uniform(0, H), r.uniform(1.5, 5)
            circ(d, (x, y), rr, shade(col, 0.55) + (150,))
        _cache[key] = img.filter(ImageFilter.GaussianBlur(0.6))
    return _cache[key]

def cu_roller(lt, raw_col, paint_col):
    raw, pt = concrete(raw_col), concrete(paint_col)
    frame = raw.copy()
    p = ease(clamp((lt - 0.1) / 2.2))
    ry = lerp(H + 120, -200, p)
    x0, x1 = 190, 890
    mask = Image.new('L', (W, H), 0); md = ImageDraw.Draw(mask)
    md.rectangle((0, 0, x0 + 10, H), fill=255)
    md.polygon([(x0, H)] + [(x, ry + 58 + 10 * math.sin(x * 0.04)) for x in range(x0, x1 + 1, 20)] + [(x1, H)], fill=255)
    frame.paste(pt, (0, 0), mask)
    d = ImageDraw.Draw(frame, 'RGBA')
    if ry + 60 < H:
        d.rectangle((x0, ry + 60, x1, min(H, ry + 360)), fill=(255, 255, 255, 22))
    d.rectangle((x1 + 20, ry - 10, x1 + 40, ry + 10), fill=H_('9A9A9A'))
    d.line([(x1 + 30, ry), (x1 + 80, ry), (x1 + 80, ry + 320)], fill=H_('9A9A9A'), width=14)
    d.rounded_rectangle((x1 + 55, ry + 300, x1 + 105, ry + 620), radius=22, fill=H_('2F5D8C'))
    d.rounded_rectangle((x0, ry - 62, x1, ry + 62), radius=58, fill=shade(paint_col, 0.9))
    d.rounded_rectangle((x0 + 10, ry - 50, x1 - 10, ry - 18), radius=16, fill=shade(paint_col, 1.12))
    rr = random.Random(int(lt * 10))
    for _ in range(40):
        xx = rr.uniform(x0 + 30, x1 - 30); yy = rr.uniform(ry - 50, ry + 50)
        d.line([(xx, yy), (xx + 6, yy + 3)], fill=shade(paint_col, 0.8), width=2)
    d.polygon([(x1 + 50, ry + 420), (x1 + 110, ry + 380), (W + 60, ry + 700), (W + 60, ry + 820)], fill=SKIN)
    d.ellipse((x1 + 30, ry + 360, x1 + 150, ry + 520), fill=GLOVE)
    return frame

def cu_led(lt, wood_col, led_col):
    key = ('ledbg', wood_col)
    if key not in _cache:
        bg = Image.new('RGB', (W, H), H_('1B1410'))
        d = ImageDraw.Draw(bg)
        for y in range(820, H):
            d.line([(0, y), (W, y)], fill=shade(H_('4A3526'), lerp(0.9, 0.5, (y - 820) / (H - 820))))
        for y in range(900, H, 90):
            d.line([(0, y), (W, y)], fill=H_('2E2119'), width=3)
        bg.paste(wood_tex(W, 330, wood_col, 77), (0, 430))
        d.rectangle((0, 760, W, 792), fill=shade(wood_col, 0.5))
        d.rectangle((60, 792, 130, 1140), fill=shade(wood_col, 0.6)); d.rectangle((950, 792, 1020, 1140), fill=shade(wood_col, 0.6))
        _cache[key] = bg
    gkey = ('ledglow', led_col)
    if gkey not in _cache:
        glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
        gd.ellipse((-100, 700, W + 100, 1350), fill=led_col + (150,))
        gd.rectangle((0, 780, W, 800), fill=mix(led_col, (255, 255, 255), 0.5) + (255,))
        _cache[gkey] = glow.filter(ImageFilter.GaussianBlur(60))
    bg, glow = _cache[key], _cache[gkey]
    lead = lerp(20, W + 40, ease(clamp((lt - 0.15) / 1.4)))
    ramp = np.clip((lead - np.arange(W)) / 260.0, 0, 1)
    m = (np.tile(ramp, (H, 1)) * 255).astype(np.uint8)
    g2 = glow.copy(); g2.putalpha(Image.fromarray(np.minimum(np.array(glow.getchannel('A')), m)))
    frame = Image.alpha_composite(bg.convert('RGBA'), g2)
    d = ImageDraw.Draw(frame, 'RGBA')
    d.rectangle((0, 788, W, 800), fill=H_('DDDDDD'))
    for x in range(40, W, 34):
        if x < lead:
            circ(d, (x, 794), 12, led_col + (90,)); circ(d, (x, 794), 5, mix(led_col, (255, 255, 255), 0.7))
        else:
            circ(d, (x, 794), 5, (120, 110, 100))
    if lt < 1.9:
        hx = min(lead + 30, W + 60); hy = 850 + (0 if lt < 1.6 else (lt - 1.6) * 900)
        d.polygon([(hx - 30, hy + 40), (hx + 50, hy + 30), (hx + 420, hy + 700), (hx + 260, hy + 760)], fill=SKIN)
        d.ellipse((hx - 60, hy - 30, hx + 70, hy + 110), fill=GLOVE)
        d.ellipse((hx - 70, hy - 50, hx - 20, hy + 10), fill=shade(GLOVE, 0.92))
    return frame.convert('RGB')

HOLES = [(110, 520, 510, 1420), (570, 520, 970, 1420)]
def cu_plants(lt, block_col):
    key = ('plantbg', block_col)
    if key not in _cache:
        bg = concrete(block_col).copy()
        d = ImageDraw.Draw(bg, 'RGBA')
        for (x0, y0, x1, y1) in HOLES:
            d.rounded_rectangle((x0, y0, x1, y1), radius=36, fill=(28, 24, 22))
            for i in range(30):
                d.line([(x0 + 20, y0 + 10 + i * 3), (x1 - 20, y0 + 10 + i * 3)], fill=(0, 0, 0, 60 - i * 2))
            d.rounded_rectangle((x0 + 20, y1 - 190, x1 - 20, y1 - 10), radius=26, fill=H_('4A3526'))
            r = random.Random(x0)
            for _ in range(80):
                circ(d, (r.uniform(x0 + 30, x1 - 30), r.uniform(y1 - 180, y1 - 20)), r.uniform(2, 5), H_('36261B'))
        d.rectangle((0, 0, W, 90), fill=shade(block_col, 0.8))
        d.rectangle((0, 1830, W, H), fill=shade(block_col, 0.8))
        _cache[key] = bg
    frame = _cache[key].copy()
    d = ImageDraw.Draw(frame, 'RGBA')
    for i, (x0, y0, x1, y1) in enumerate(HOLES):
        t0 = 0.15 + i * 0.95
        k = clamp((lt - t0) / 0.6)
        if k <= 0: continue
        cx = (x0 + x1) / 2; cy = lerp(y0 - 400, y1 - 230, ease(k))
        draw_succulent(d, cx, cy, 175)
        if k < 1:
            d.polygon([(cx - 40, cy - 120), (cx + 40, cy - 120), (cx + 120, -60), (cx + 20, -60)], fill=SKIN)
            d.ellipse((cx - 70, cy - 200, cx + 70, cy - 60), fill=GLOVE)
        elif lt - t0 - 0.6 < 0.4:
            a = int(200 * (1 - (lt - t0 - 0.6) / 0.4))
            for ang in range(0, 360, 45):
                r1, r2 = 200, 240
                d.line([(cx + math.cos(math.radians(ang)) * r1, cy + math.sin(math.radians(ang)) * r1 * 0.6),
                        (cx + math.cos(math.radians(ang)) * r2, cy + math.sin(math.radians(ang)) * r2 * 0.6)],
                       fill=(255, 250, 220, a), width=5)
    return frame


ROW = 44
def cu_rope(lt, rope_col):
    """Yakın plan: siyah lastik üstüne alttan yukarı halat sarılır."""
    key = ('ropebg', rope_col)
    if key not in _cache:
        rub = concrete(H_('2E2D2F')).copy()
        d = ImageDraw.Draw(rub, 'RGBA')
        for x in range(-400, W + 400, 90):
            d.line([(x, 0), (x + 300, H)], fill=(15, 15, 16, 160), width=26)
        rope = Image.new('RGB', (W, H), shade(rope_col, 0.5))
        rd = ImageDraw.Draw(rope)
        for y in range(H, -ROW, -ROW):
            rd.rounded_rectangle((-20, y - ROW + 3, W + 20, y - 1), radius=18, fill=rope_col)
            rd.line([(0, y - ROW + 10), (W, y - ROW + 10)], fill=shade(rope_col, 1.12), width=4)
            for x in range(-40, W + 40, 18):
                rd.line([(x, y - 3), (x + 16, y - ROW + 5)], fill=shade(rope_col, 0.78), width=3)
        _cache[key] = (rub, rope)
    rub, rope = _cache[key]
    p = ease(clamp((lt - 0.1) / 2.2))
    top = lerp(H - 60, 380, p)
    row_top = H - math.ceil((H - top) / ROW) * ROW
    xf = ((H - top) / ROW % 1) * W
    mask = Image.new('L', (W, H), 0); md = ImageDraw.Draw(mask)
    md.rectangle((0, row_top + ROW, W, H), fill=255)
    md.rectangle((0, row_top, xf, row_top + ROW), fill=255)
    frame = rub.copy(); frame.paste(rope, (0, 0), mask)
    d = ImageDraw.Draw(frame, 'RGBA')
    d.rectangle((0, row_top + ROW - 4, W, row_top + ROW + 8), fill=(0, 0, 0, 60))
    hx, hy = xf, row_top + ROW / 2
    d.line([(hx, hy), (W + 80, hy - 380)], fill=rope_col, width=30)
    d.polygon([(hx + 60, hy + 40), (hx + 150, hy - 10), (W + 200, hy + 500), (W + 60, hy + 600)], fill=SKIN)
    d.ellipse((hx - 40, hy - 80, hx + 120, hy + 70), fill=GLOVE)
    d.ellipse((hx - 60, hy - 30, hx + 10, hy + 40), fill=shade(GLOVE, 0.9))
    return frame

def cu_pour(lt, conc_col, bucket_col):
    """Yakın plan: kovadan kalıba beton dökülür, seviye yükselir."""
    key = ('pourbg', bucket_col)
    if key not in _cache:
        bg = Image.new('RGB', (W, H), H_('3A2C22'))
        d = ImageDraw.Draw(bg)
        for y in range(1400, H, 70): d.line([(0, y), (W, y)], fill=H_('2E231B'), width=3)
        d.polygon([(140, 760), (940, 760), (860, 1820), (220, 1820)], fill=bucket_col)
        d.ellipse((220, 1760, 860, 1880), fill=bucket_col)
        for k in (0.3, 0.6):
            y = lerp(760, 1820, k); x0 = lerp(140, 220, k); x1 = lerp(940, 860, k)
            d.line([(x0, y), (x1, y)], fill=shade(bucket_col, 0.85), width=6)
        d.polygon([(140, 760), (200, 760), (260, 1820), (220, 1820)], fill=shade(bucket_col, 1.12))
        _cache[key] = bg
    frame = _cache[key].copy()
    d = ImageDraw.Draw(frame, 'RGBA')
    rim = (130, 640, 950, 880)
    d.ellipse(rim, fill=(25, 20, 18))
    lvl = lerp(1050, 790, ease(clamp((lt - 0.2) / 2.0)))
    surf = Image.new('L', (W, H), 0)
    ImageDraw.Draw(surf).ellipse((170, lvl - 110, 910, lvl + 110), fill=255)
    inner = Image.new('L', (W, H), 0); ImageDraw.Draw(inner).ellipse((150, 655, 930, 865), fill=255)
    m = Image.fromarray(np.minimum(np.array(surf), np.array(inner)))
    frame.paste(Image.new('RGB', (W, H), conc_col), (0, 0), m)
    d = ImageDraw.Draw(frame, 'RGBA')
    for i in range(3):
        r = ((lt * 1.6 + i / 3) % 1)
        d.ellipse((540 - 60 - 260 * r, lvl - 60 - 20 - 50 * r, 540 + 60 + 260 * r, lvl - 60 + 20 + 50 * r),
                  outline=shade(conc_col, 1.15) + (int(160 * (1 - r)),), width=4)
    d.ellipse(rim, outline=shade(bucket_col, 1.2), width=16)
    if lt < 2.3:
        pts_l = [(470 + 14 * math.sin(y * 0.02 + lt * 8), y) for y in range(-20, int(lvl - 60), 30)]
        pts_r = [(x + 70 + 6 * math.sin(y * 0.03 + lt * 6), y) for x, y in pts_l]
        d.polygon(pts_l + pts_r[::-1], fill=conc_col)
        d.line([(x + 20, y) for x, y in pts_l], fill=shade(conc_col, 1.18) + (180,), width=6)
        r = random.Random(int(lt * 20))
        for _ in range(10):
            circ(d, (505 + r.uniform(-120, 120), lvl - 60 - r.uniform(0, 80)), r.uniform(4, 10), conc_col)
    return frame


# ---------------------------------------------------------------- metin
def text_pill(img, txt, cy, size, alpha=1.0, fg=(255, 255, 255), bgc=(25, 18, 14)):
    """'→' karakterini fonttan bağımsız, çizilmiş okla gösterir."""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    f = font(size)
    parts = txt.split('→')
    aw = int(size * 1.0)
    widths = [d.textlength(p.strip(), font=f) for p in parts]
    total = sum(widths) + (len(parts) - 1) * (aw + size * 0.5)
    scale = min(1.0, (W - 120) / total)
    if scale < 1:
        f = font(int(size * scale)); size = int(size * scale); aw = int(size * 1.0)
        widths = [d.textlength(p.strip(), font=f) for p in parts]
        total = sum(widths) + (len(parts) - 1) * (aw + size * 0.5)
    x = W / 2 - total / 2
    pad = (34, 20)
    d.rounded_rectangle((x - pad[0], cy - size * 0.72 - pad[1] / 2, x + total + pad[0], cy + size * 0.72 + pad[1] / 2),
                        radius=int(size * 0.6), fill=bgc + (205,))
    for i, p in enumerate(parts):
        d.text((x, cy), p.strip(), font=f, fill=fg, anchor='lm')
        x += widths[i]
        if i < len(parts) - 1:
            x += size * 0.25
            y = cy
            d.rectangle((x, y - size * 0.07, x + aw * 0.62, y + size * 0.07), fill=fg)
            d.polygon([(x + aw * 0.55, y - size * 0.24), (x + aw, y), (x + aw * 0.55, y + size * 0.24)], fill=fg)
            x += aw + size * 0.25
    if alpha < 1: lay.putalpha(lay.getchannel('A').point(lambda v: int(v * alpha)))
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')

def tag(img, txt, xy, size=34):
    d = ImageDraw.Draw(img, 'RGBA')
    f = font(size)
    x0, y0, x1, y1 = d.textbbox(xy, txt, font=f)
    d.rounded_rectangle((x0 - 16, y0 - 10, x1 + 16, y1 + 10), radius=14, fill=(255, 255, 255, 215))
    d.text(xy, txt, font=f, fill=(30, 22, 18))


# ---------------------------------------------------------------- kapanış: beğen / abone ol / zil
END0 = 26.4
CLICK_LIKE, CLICK_SUB, CLICK_BELL = 0.8, 1.7, 2.5  # END0'a göre

def icon_like(d, cx, cy, s, col):
    def P(x, y): return (cx + (x - 32) * s, cy + (y - 34) * s)
    d.rounded_rectangle((*P(4, 28), *P(16, 62)), radius=int(3 * s), fill=col)
    d.rounded_rectangle((*P(20, 26), *P(58, 62)), radius=int(8 * s), fill=col)
    d.polygon([P(20, 30), P(30, 4), P(40, 8), P(38, 28)], fill=col)
    circ(d, P(35, 8), 5.5 * s, col)

def icon_bell(d, cx, cy, s, col, ang=0.0):
    def P(x, y):
        x, y = x * s, y * s
        c, sn = math.cos(ang), math.sin(ang)
        return (cx + x * c - (y + 30 * s) * sn, cy + x * sn + (y + 30 * s) * c - 30 * s)
    pts = [P(-28, 18), P(-22, 12), P(-20, -10)] + [P(20 * math.cos(a), -10 - 18 * math.sin(a)) for a in np.linspace(math.pi, 0, 10)] + \
          [P(20, -10), P(22, 12), P(28, 18)]
    d.polygon(pts, fill=col)
    circ(d, P(0, 26), 7 * s, col)
    circ(d, P(0, -30), 4 * s, col)

def cursor(d, x, y, press):
    s = 1.6 * (0.85 if press else 1.0)
    pts = [(0, 0), (0, 34), (9, 26), (15, 40), (21, 37), (15, 24), (27, 24)]
    d.polygon([(x + px * s, y + py * s) for px, py in pts], fill=(255, 255, 255), outline=(20, 20, 20), width=3)

def end_card(img, lt):
    img = img.convert('RGBA')
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    k = ease_out(lt / 0.35)
    cy = 560 - (1 - k) * 120
    d.rounded_rectangle((70, cy - 110, W - 70, cy + 130), radius=40, fill=(20, 14, 10, int(170 * k)))
    liked, subbed, belled = lt >= CLICK_LIKE, lt >= CLICK_SUB, lt >= CLICK_BELL
    # beğen
    lx, bx, sx = 190, 890, 540
    circ(d, (lx, cy - 10), 62, (255, 255, 255, int(255 * k)) if liked else (255, 255, 255, int(40 * k)))
    icon_like(d, lx, cy - 10, 1.35, (235, 70, 90) if liked else (255, 255, 255, int(255 * k)))
    if liked and lt - CLICK_LIKE < 0.6:
        u = (lt - CLICK_LIKE) / 0.6
        d.text((lx + 40, cy - 90 - 60 * u), "+1", font=font(40), fill=(255, 255, 255, int(255 * (1 - u))))
        circ(d, (lx, cy - 10), 62 + 50 * u, None, outline=(255, 255, 255, int(200 * (1 - u))), width=5)
    # abone ol
    sw = 400
    pc = (90, 90, 90) if subbed else (225, 35, 35)
    d.rounded_rectangle((sx - sw / 2, cy - 55, sx + sw / 2, cy + 35), radius=45, fill=pc + (int(255 * k),))
    d.text((sx, cy - 10), "SUBSCRIBED" if subbed else "SUBSCRIBE", font=font(40), fill=(255, 255, 255, int(255 * k)), anchor='mm')
    if subbed and lt - CLICK_SUB < 0.5:
        u = (lt - CLICK_SUB) / 0.5
        d.rounded_rectangle((sx - sw / 2 - 30 * u, cy - 55 - 30 * u, sx + sw / 2 + 30 * u, cy + 35 + 30 * u), radius=60,
                            outline=(255, 255, 255, int(200 * (1 - u))), width=5)
    # zil
    ang = 0.35 * math.sin((lt - CLICK_BELL) * 30) * math.exp(-(lt - CLICK_BELL) * 3) if belled else 0
    circ(d, (bx, cy - 10), 62, (255, 255, 255, int(40 * k)) if not belled else (255, 205, 80, int(255 * k)))
    icon_bell(d, bx, cy - 12, 1.2, (255, 255, 255, int(255 * k)) if not belled else (60, 40, 20))
    if belled and lt - CLICK_BELL < 0.6:
        u = (lt - CLICK_BELL) / 0.6
        for a in (-0.9, -0.5, 0.5, 0.9):
            r1, r2 = 80 + 20 * u, 100 + 25 * u
            d.line([(bx + math.sin(a) * r1, cy - 10 - math.cos(a) * r1), (bx + math.sin(a) * r2, cy - 10 - math.cos(a) * r2)],
                   fill=(255, 220, 120, int(255 * (1 - u))), width=6)
    d.text((W / 2, cy + 90), "New cozy build every day", font=font(34), fill=(255, 240, 220, int(220 * k)), anchor='mm')
    # imleç
    keys = [(0.35, (W + 60, cy + 200)), (CLICK_LIKE - 0.05, (lx + 10, cy + 10)), (CLICK_LIKE + 0.25, (lx + 10, cy + 10)),
            (CLICK_SUB - 0.05, (sx + 60, cy)), (CLICK_SUB + 0.2, (sx + 60, cy)), (CLICK_BELL - 0.05, (bx + 10, cy + 10)),
            (CLICK_BELL + 0.4, (bx + 10, cy + 10)), (CLICK_BELL + 0.9, (W + 80, cy + 260))]
    if lt >= keys[0][0]:
        pos = keys[-1][1]
        for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
            if t0 <= lt < t1:
                u = ease((lt - t0) / (t1 - t0)); pos = (lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u)); break
        press = any(0 <= lt - c < 0.12 for c in (CLICK_LIKE, CLICK_SUB, CLICK_BELL))
        cursor(d, pos[0], pos[1], press)
    return Image.alpha_composite(img, lay).convert('RGB')


# ---------------------------------------------------------------- video akışı
class Video:
    def __init__(self, sc, project):
        self.sc = sc; self.P = project
        reset_cache()

    def wide(self, golden=False):
        return scene_bg(self.sc.get('location', 'living'), self.sc['palette'], golden).copy()

    def front(self, img):
        props_front(img, self.P.can_col, self.P.can_label)

    def seg_anchor(self, lt):
        P = self.P
        img = self.wide(); P.anchor_static(img); draw_motes(img, lt + 2)
        if lt < 2.0:
            mx = lerp(-200, P.anchor_stop_x, ease_out(lt / 2.0) * 0.35 + (lt / 2.0) * 0.65)
            info = draw_maya(img, mx, 1560, pose='carrywalk', t=lt, smile=0.4)
            P.draw_item(img, info['hf'][0] + P.carry_dx, info['hf'][1] + P.carry_dy)
        else:
            k = clamp((lt - 2.0) / 0.7)
            info = draw_maya(img, P.anchor_stop_x, 1560, pose='setdown', t=k, smile=0.4)
            fx, fy_ = P.item_final
            P.draw_item(img, lerp(info['hf'][0] + P.carry_dx, fx, ease(k)), lerp(info['hf'][1] + P.carry_dy, fy_, ease(k)))
            if lt > 2.7:
                dust(img, lt - 2.7, (fx, fy_ - 20), rate=80, life=0.9, seed=1, spread=1.6)
        self.front(img)
        return img

    def seg_stakes(self, lt):
        img = self.wide(); self.P.stakes(img, lt); draw_motes(img, lt + 5)
        self.front(img)
        return zoom(img, lerp(1.0, 1.06, ease(lt / 3)), (540, 1300))

    def seg_proc(self, which, lt):
        img = self.wide(); draw_motes(img, lt + 8)
        getattr(self.P, 'proc_' + which)(img, lt)
        self.front(img)
        return img

    def payoff_bg(self):
        if 'paybg' in _cache: return _cache['paybg']
        sc = self.sc
        img = self.wide(True).convert('RGBA')
        d = ImageDraw.Draw(img, 'RGBA')
        glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
        loc = sc.get('location', 'living')
        if sc['string_lights'] or loc in OUTDOOR:
            base = 250 if loc == 'living' else 330
            pts = [(x, base + 90 * math.sin(math.pi * x / W)) for x in range(0, W + 1, 20)]
            d.line(pts, fill=H_('5A4636'), width=3)
            for x in range(40, W, 80):
                y = base + 90 * math.sin(math.pi * x / W) + 14
                circ(gd, (x, y), 34, (255, 190, 90, 150)); circ(d, (x, y), 9, (255, 236, 180))
        if loc in OUTDOOR:
            d.ellipse((915, 1335, 1005, 1355), fill=(40, 25, 15, 70))
            d.rectangle((922, 1200, 998, 1345), fill=H_('2E2A27'))
            d.rectangle((934, 1215, 986, 1330), fill=H_('FFD9A0'))
            d.polygon([(915, 1200), (1005, 1200), (975, 1170), (945, 1170)], fill=H_('2E2A27'))
            d.arc((940, 1140, 980, 1180), 180, 360, fill=H_('2E2A27'), width=5)
            circ(gd, (960, 1270), 150, (255, 185, 90, 170))
        else:
            d.line([(960, 1330), (960, 860)], fill=H_('3C3027'), width=10)
            d.ellipse((905, 1320, 1015, 1345), fill=H_('3C3027'))
            d.polygon([(900, 870), (1020, 870), (995, 790), (925, 790)], fill=H_('F3E6CC'))
            circ(gd, (960, 880), 170, (255, 185, 90, 150))
        img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(30)))
        d = ImageDraw.Draw(img, 'RGBA')
        rug = H_(sc['rug'])
        d.ellipse((120, 1470, 1000, 1790), fill=rug)
        d.ellipse((160, 1495, 960, 1765), outline=shade(rug, 0.88), width=6)
        ml = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        info = draw_maya(ml, 215, 1360, s=0.82, pose='mug', smile=1.0)
        md = ImageDraw.Draw(ml, 'RGBA')
        hx, hy = info['hf']
        mug = H_(sc['mug'])
        md.rounded_rectangle((hx - 4, hy - 30, hx + 34, hy + 14), radius=6, fill=mug)
        md.arc((hx + 26, hy - 22, hx + 46, hy + 2), 270, 90, fill=mug, width=6)
        img = Image.alpha_composite(img, ml.filter(ImageFilter.GaussianBlur(1.6)))
        if self.P.led_floor:
            lg = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(lg).ellipse(self.P.led_floor, fill=tuple(sc['led']) + (170,))
            img = Image.alpha_composite(img, lg.filter(ImageFilter.GaussianBlur(28)))
        img = img.convert('RGB')
        rest = self.P.payoff_objects(img)
        if self.P.plant_front:
            draw_plant_pot(img, 915, 1740, s=0.95, pot=H_(sc['pot']))
        _cache['paybg'] = (img, rest)
        return _cache['paybg']

    def seg_payoff(self, lt):
        bg, rest = self.payoff_bg()
        img = bg.copy()
        d = ImageDraw.Draw(img, 'RGBA')
        draw_motes(img, lt + 22, col=(255, 225, 170))
        pet = self.sc['pet']
        rx, ry, rs = rest
        if lt < 2.4:
            draw_pet_walk(img, pet, lerp(1260, 780, lt / 2.4), 1690, 1.0, lt)
        elif lt < 3.0:
            k = (lt - 2.4) / 0.6
            x = lerp(780, rx + 20, ease(k)); y = lerp(1690, ry + 8, ease(k)) - 160 * math.sin(math.pi * k)
            draw_pet_walk(img, pet, x, y, lerp(1.0, rs, k), lt)
        else:
            sq = 1 + 0.12 * math.exp(-(lt - 3.0) * 10) * math.cos((lt - 3.0) * 30)
            draw_pet_curl(img, pet, rx, ry + 6, rs * sq, lt)
            if lt > 3.6:
                for i in range(3):
                    zt = lt - 3.6 - i * 0.55
                    if 0 < zt < 1.6:
                        d.text((rx - 90 - i * 6 + zt * 30, ry - 110 - zt * 90), "z", font=font(34 + i * 10),
                               fill=(90, 70, 60, int(220 * (1 - zt / 1.6))))
            if lt > 4.2:
                k = ease_out((lt - 4.2) / 0.5)
                hx, hy, r = rx + 60, ry - 150 - 40 * (lt - 4.2), 22 * k
                col = (235, 90, 110, 230)
                circ(d, (hx - r * 0.55, hy), r * 0.62, col); circ(d, (hx + r * 0.55, hy), r * 0.62, col)
                d.polygon([(hx - r * 1.12, hy + r * 0.15), (hx + r * 1.12, hy + r * 0.15), (hx, hy + r * 1.35)], fill=col)
        return zoom(img, lerp(1.0, 1.12, ease(lt / 7.0)), (560, ry))

    def seg_hook(self, lt):
        if 'hook' not in _cache:
            _cache['hook'] = (self.seg_stakes(1.5).crop((0, 820, W, 1780)),
                              self.seg_payoff(5.2).crop((0, 820, W, 1780)))
        top, bot = _cache['hook']
        img = Image.new('RGB', (W, H), (20, 14, 10))
        img.paste(top, (int(-W * (1 - ease_out(lt / 0.3))), 0))
        img.paste(bot, (int(W * (1 - ease_out((lt - 0.1) / 0.3))), 960))
        ImageDraw.Draw(img).rectangle((0, 954, W, 966), fill=(255, 255, 255))
        if lt > 0.25:
            tag(img, "BEFORE", (840, 60)); tag(img, "AFTER", (870, 1020))
        if lt > 0.35:
            img = text_pill(img, self.sc['hook_text'], 960, 58, alpha=ease((lt - 0.35) / 0.25))
        return img

    def scene(self, t):
        if t < 2: return self.seg_hook(t)
        if t < 5: return self.seg_anchor(t - 2)
        if t < 8: return self.seg_stakes(t - 5)
        if t < 11: return self.seg_proc('a', t - 8)
        if t < 14: return self.seg_proc('b', t - 11)
        if t < 17: return self.seg_proc('c', t - 14)
        if t < 19.5: return self.P.cu1(t - 17)
        if t < 22: return self.P.cu2(t - 19.5)
        return self.seg_payoff(t - 22)

    def frame(self, t):
        img = Image.alpha_composite(self.scene(t).convert('RGBA'), vignette())
        for cut in (2.0, 22.0):
            if cut <= t < cut + 0.2:
                img = Image.alpha_composite(img, Image.new('RGBA', (W, H), (255, 250, 240, int(200 * (1 - (t - cut) / 0.2)))))
        img = img.convert('RGB')
        if t >= 2:
            ImageDraw.Draw(img, 'RGBA').text((44, 70), self.sc['handle'], font=font(34), fill=(255, 255, 255, 180),
                                             stroke_width=2, stroke_fill=(0, 0, 0, 90))
        if t >= 26.0:
            img = text_pill(img, self.sc['cta'], 250, 60, alpha=ease((t - 26.0) / 0.4))
        if t >= END0:
            img = end_card(img, t - END0)
        return img

    def render(self, out_mp4, wav):
        build_audio(self.sc, self.P.sfx(), wav)
        p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                              '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                              '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
                              '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out_mp4],
                             stdin=subprocess.PIPE)
        for i in range(NF):
            p.stdin.write(self.frame(i / FPS).tobytes())
        p.stdin.close()
        if p.wait() != 0: raise RuntimeError('ffmpeg failed')
        self.frame(1.0).save(out_mp4[:-4] + '_thumb.jpg', quality=90)


# ---------------------------------------------------------------- ses (ASMR + lo-fi)
SR = 44100
def build_audio(sc, events, path):
    arng = np.random.default_rng(sc['seed'])
    def tt(dur): return np.arange(int(dur * SR)) / SR
    def noise(dur): return arng.standard_normal(int(dur * SR))
    def band(x, lo, hi):
        n = len(x); X = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
        return np.fft.irfft(X * ((fr >= lo) & (fr <= hi)), n)
    N = int(DUR * SR)
    def place(buf, sig, t0, g=1.0):
        i = int(t0 * SR)
        if i >= len(buf): return
        j = min(len(buf), i + len(sig)); buf[i:j] += sig[:j - i] * g
    def mf(m): return 440 * 2 ** ((m - 69) / 12)
    def ep(freq, dur=1.8):
        t = tt(dur); e = np.minimum(1, t / 0.008) * np.exp(-t / 0.9)
        s = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t) * np.exp(-t / 0.3)
        return s * e * (1 + 0.15 * np.sin(2 * np.pi * 4.5 * t))
    def kick():
        t = tt(0.35); f = 50 + 80 * np.exp(-t / 0.04)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)
    def snare():
        t = tt(0.2); return band(noise(0.2), 1200, 6000) * np.exp(-t / 0.05) * 0.5 + np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04) * 0.3
    def hat():
        t = tt(0.05); return band(noise(0.05), 6000, 16000) * np.exp(-t / 0.012)
    def knock(lo=300, hi=2500, tau=0.03, body=180):
        t = tt(0.3); return band(noise(0.3), lo, hi) * np.exp(-t / tau) + 0.6 * np.sin(2 * np.pi * body * t) * np.exp(-t / 0.06)
    def whoosh(d=0.45):
        t = tt(d); return band(noise(d), 400, 5000) * np.sin(np.pi * t / d) ** 2
    def chime(freq, tau=0.5):
        t = tt(1.2); return np.sin(2 * np.pi * freq * t) * np.exp(-t / tau) * np.minimum(1, t / 0.004)
    def gate(sig, d_):
        t = tt(d_); return sig * np.minimum(1, t / 0.04) * np.minimum(1, (d_ - t) / 0.06)

    mus = np.zeros(N); sfx = np.zeros(N)
    m = sc['music']
    beat = 60 / m['tempo']; bar = 4 * beat
    chords = [[n + m['transpose'] for n in c] for c in m['prog']]
    for b in range(int(DUR / bar) + 1):
        t0 = b * bar; ch = chords[b % 4]
        for i, n in enumerate(ch):
            place(mus, ep(mf(n)), t0 + i * 0.018, 0.16)
            place(mus, ep(mf(n)), t0 + 2.5 * beat + i * 0.018, 0.08)
        place(mus, ep(mf(ch[0] - 12), 2.4), t0, 0.35)
        place(mus, ep(mf(ch[(b * 3) % 4] + 12), 1.2), t0 + 1.5 * beat, 0.07)
        place(mus, ep(mf(ch[(b * 3 + 2) % 4] + 12), 1.2), t0 + 3 * beat, 0.06)
        for k in range(8):
            tb = t0 + k * beat / 2 + (0.06 if k % 2 else 0)
            if not (2.0 <= tb < 21.0 or tb >= 22.8): continue
            place(mus, hat(), tb, 0.07)
            if k in (0, 5): place(mus, kick(), tb, 0.5)
            if k in (2, 6): place(mus, snare(), tb, 0.3)
    t = tt(DUR - 22); pad = np.zeros(len(t))
    for n in chords[0] + [chords[0][0] + 12]:
        for det in (-0.6, 0.6): pad += np.sin(2 * np.pi * (mf(n + 12) + det) * t)
    place(mus, pad * np.minimum(1, t / 1.5) * 0.02, 22.0)
    place(mus, band(noise(1.6), 2000, 8000) * np.linspace(0, 1, int(1.6 * SR)) ** 2, 20.4, 0.12)
    cr = np.zeros(N); idx = arng.random(N) < 0.0004; cr[idx] = arng.uniform(-1, 1, idx.sum())
    mus += band(cr, 1000, 8000) * 0.25 + band(noise(DUR), 2000, 9000)[:N] * 0.004

    # ortak SFX
    place(sfx, whoosh(), 1.75, 0.5); place(sfx, whoosh(), 21.8, 0.5)
    for k in range(5): place(sfx, knock(150, 1500, 0.02, 90), 2.15 + k * 0.29, 0.35)
    # proje SFX
    for ev in events:
        kind = ev[0]
        if kind == 'drop_wood':
            place(sfx, knock(150, 900, 0.08, 55), ev[1], 1.0); place(sfx, knock(800, 2500, 0.03, 120), ev[1] + 0.03, 0.4)
        elif kind == 'drop_heavy':
            place(sfx, knock(80, 700, 0.1, 45), ev[1], 1.1); place(sfx, band(noise(0.3), 300, 3000) * np.exp(-tt(0.3) / 0.05), ev[1], 0.4)
        elif kind == 'knock':
            place(sfx, knock(250, 2200, 0.025, 160), ev[1], ev[2] if len(ev) > 2 else 0.4)
        elif kind == 'sand':
            d_ = ev[2] - ev[1]; t = tt(d_)
            s = band(noise(d_), 1200, 7000) * (0.35 + 0.65 * np.abs(np.sin(2 * np.pi * 1.1 * t)) ** 0.6)
            s += 0.25 * band(np.sign(np.sin(2 * np.pi * 110 * t)), 80, 1200)
            place(sfx, gate(s, d_), ev[1], 0.22)
        elif kind == 'hammer':
            for k in range(ev[3]):
                place(sfx, knock(300, 3000, 0.025, 220), ev[1] + k * ev[2], 0.9)
                place(sfx, chime(1400, 0.05), ev[1] + k * ev[2], 0.05)
        elif kind == 'drill':
            d_ = ev[2] - ev[1]; t = tt(d_)
            f = 60 + 170 * np.minimum(1, t / 0.15)
            saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
            place(sfx, gate(band(saw, 100, 4000) + 0.3 * band(noise(d_), 2000, 6000), d_), ev[1], 0.25)
        elif kind == 'roller':
            d_ = ev[2] - ev[1]; t = tt(d_)
            s = band(noise(d_), 300, 3000) * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 1.6 * t)))
            s += 0.5 * band(noise(d_), 3000, 8000) * (arng.random(len(t)) < 0.02)
            place(sfx, gate(s, d_), ev[1], 0.2)
        elif kind == 'brush':
            d_ = ev[2] - ev[1]; t = tt(d_)
            place(sfx, band(noise(d_), 2500, 9000) * np.sin(np.pi * t / d_) ** 0.5, ev[1], 0.16)
        elif kind == 'led':
            place(sfx, band(noise(0.02), 3000, 10000) * np.exp(-tt(0.02) / 0.003), ev[1], 0.9)
            for k, n in enumerate((84, 88, 91, 96)):
                place(sfx, chime(mf(n)), ev[1] + 0.3 + k * 0.33, 0.07)
        elif kind == 'pour':
            d_ = ev[2] - ev[1]; t = tt(d_)
            glug = 0.55 + 0.45 * np.sin(2 * np.pi * 6.5 * t + 3 * np.sin(2 * np.pi * 0.9 * t))
            place(sfx, gate(band(noise(d_), 120, 1400) * glug + 0.2 * band(noise(d_), 1400, 4000), d_), ev[1], 0.3)
        elif kind == 'scrub':
            d_ = ev[2] - ev[1]; t = tt(d_)
            s = band(noise(d_), 800, 6000) * (0.3 + 0.7 * np.abs(np.sin(2 * np.pi * 2.2 * t)))
            s += 0.4 * band(noise(d_), 4000, 12000) * (arng.random(len(t)) < 0.01)
            place(sfx, gate(s, d_), ev[1], 0.18)
        elif kind == 'plant':
            place(sfx, band(noise(0.35), 500, 4000) * np.exp(-tt(0.35) / 0.1), ev[1], 0.3)
            place(sfx, chime(mf(96), 0.3), ev[1] + 0.05, 0.06)
    # pet
    for k in range(12):
        place(sfx, band(noise(0.05), 1500, 5000) * np.exp(-tt(0.05) / 0.008), 22.15 + k * 0.19, 0.12)
    place(sfx, band(noise(0.4), 100, 800) * np.exp(-tt(0.4) / 0.1), 25.0, 0.6)
    if sc['pet']['kind'] == 'dog':
        t = tt(0.9); place(sfx, band(noise(0.9), 200, 1200) * np.sin(np.pi * t / 0.9) ** 2 * np.exp(-t), 25.9, 0.35)
    else:
        t = tt(2.0); place(sfx, band(noise(2.0), 60, 400) * (0.5 + 0.5 * np.sin(2 * np.pi * 24 * t)) * np.sin(np.pi * t / 2.0), 25.6, 0.5)
    for k, n in enumerate((91, 96, 100)):
        place(sfx, chime(mf(n), 0.35), 26.2 + k * 0.08, 0.06)
    # kapanış: beğen / abone / zil
    click = band(noise(0.03), 2000, 9000) * np.exp(-tt(0.03) / 0.004)
    for c in (CLICK_LIKE, CLICK_SUB, CLICK_BELL):
        place(sfx, click, END0 + c, 0.8)
    place(sfx, chime(mf(88), 0.12) + chime(mf(95), 0.1), END0 + CLICK_LIKE + 0.02, 0.1)
    place(sfx, chime(mf(84), 0.15) + chime(mf(91), 0.15), END0 + CLICK_SUB + 0.02, 0.1)
    for k in range(4):
        place(sfx, chime(1320, 0.4) + 0.5 * chime(1760, 0.3), END0 + CLICK_BELL + 0.03 + k * 0.09, 0.08 * (1 - k * 0.2))

    mixd = mus * 0.55 + sfx * 0.9
    mixd *= 0.89 / np.max(np.abs(mixd))
    fade = int(0.5 * SR); mixd[-fade:] *= np.linspace(1, 0, fade)
    dl = int(0.008 * SR)
    R = np.concatenate([np.zeros(dl), mixd[:-dl]]) * 0.3 + mixd * 0.7
    st = (np.stack([mixd, R], 1) * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
