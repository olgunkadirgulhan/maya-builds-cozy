"""
Proje şablonları. Her şablon aynı 28 sn iskeleti doldurur:
anchor_static / draw_item (Maya'nın taşıdığı parça) / stakes / proc_a / proc_b / proc_c / cu1 / cu2 / payoff_objects / sfx
Yeni fikir eklemek = buraya yeni bir sınıf yazıp TEMPLATES'e eklemek.
"""
import math, random
from PIL import Image, ImageDraw
from engine import (H_, lerp, clamp, ease, mix, shade, circ, draw_maya, maya_think, tool_sander, tool_drill,
                    tool_hammer, tool_roller, draw_pallet, draw_panel, draw_plant_pot, draw_succulent, dust,
                    cu_brush, cu_roller, cu_led, cu_plants, cu_rope, cu_pour, grain, font)
import numpy as np

RAW = H_('8E877D'); SANDED = H_('D9C29C')


def draw_cushion(img, x0, x1, t0, dx, dy, main, pillows):
    d = ImageDraw.Draw(img, 'RGBA')
    main = H_(main)
    top = [(x0 + 8, t0 - 30), (x1 - 8, t0 - 30), (x1 + dx - 18, t0 + dy - 26), (x0 + dx + 4, t0 + dy - 26)]
    d.rounded_rectangle((x0, t0 - 34, x1, t0 + 12), radius=22, fill=shade(main, 0.94))
    d.polygon(top, fill=main)
    d.line([(x0 + 20, t0 - 30), (x1 - 20, t0 - 30)], fill=shade(main, 0.85), width=3)
    d.ellipse((x1 - 110 + dx * 0.6, t0 + dy - 80, x1 + dx * 0.9, t0 + dy - 8), fill=H_(pillows[0]))
    d.ellipse((x0 + dx * 0.4, t0 + dy - 72, x0 + dx * 0.4 + 120, t0 + dy - 10), fill=H_(pillows[1]))


# ================================================================ 1) PALET YATAK
class PalletBed:
    key = 'pallet_bed'
    locations = ['living', 'balcony', 'garden', 'garage']
    pets = ['dog', 'cat']
    plant_front = True
    anchor_stop_x, carry_dx, carry_dy = 250, 160, 90
    LEAN_R = (600, 1020, 1040, 1262)
    CX, BY = 500, 1580
    item_final = (500, 1580)
    HAM0, HAMP = 12.1, 0.35
    DRILL = [(14.3, 15.3), (15.7, 16.6)]

    def __init__(self, sc):
        self.sc = sc
        self.fin = H_(sc['finish'][1])
        self.can_col, self.can_label = self.fin, 'STAIN'
        self.led_floor = (230, 1510, 900, 1660)

    def back_rect(self, legs): return (370, 1191 - legs, 810, 1431 - legs)
    def draw_item(self, img, cx, by): draw_pallet(img, cx, by, RAW)
    def anchor_static(self, img): draw_panel(img, self.LEAN_R, RAW)

    def stakes(self, img, lt):
        draw_panel(img, self.LEAN_R, RAW)
        draw_pallet(img, self.CX, self.BY, RAW)
        maya_think(img, 150, 1590, lt)
        if lt < 0.6: dust(img, lt + 0.3, (self.CX, self.BY - 20), rate=80, life=0.9, seed=1, spread=1.6)

    def proc_a(self, img, lt):
        draw_panel(img, self.LEAN_R, RAW)
        draw_pallet(img, self.CX, self.BY, mix(RAW, SANDED, ease(lt / 2.8)))
        info = draw_maya(img, 130, 1580, pose='kneel', t=lt, smile=0.2)
        dust(img, lt, tool_sander(img, info), rate=50, life=1.0, seed=7)

    def proc_b(self, img, lt):
        if lt < 1.0:
            r = tuple(lerp(a, b, ease(0.35 + lt * 0.5)) for a, b in zip(self.LEAN_R, self.back_rect(0)))
            draw_pallet(img, self.CX, self.BY, SANDED)
            draw_panel(img, r, SANDED, shadow=False)
            draw_maya(img, min(r[2] + 150, 940), 1600, f=-1, pose='carry', t=lt, smile=0.3)
            return
        t = 11 + lt
        draw_panel(img, self.back_rect(0), SANDED, shadow=False)
        draw_pallet(img, self.CX, self.BY, SANDED)
        u = ((t - self.HAM0) % self.HAMP) / self.HAMP if t >= self.HAM0 else 0.6
        ang = lerp(40, 165, ease(u / 0.7)) if u < 0.7 else lerp(165, 40, (u - 0.7) / 0.3)
        info = draw_maya(img, 960, 1600, f=-1, pose='stand', t=lt, smile=0.2, arms=(95, 100, ang, ang + 25), lean=6)
        hend = tool_hammer(img, info, ang)
        if u < 0.12 and t >= self.HAM0:
            circ(ImageDraw.Draw(img, 'RGBA'), hend, 28, (255, 240, 200, 110))

    def proc_c(self, img, lt):
        t = 14 + lt
        drilling = any(a <= t < b for a, b in self.DRILL)
        legs = 36 if lt > 0.2 else 0
        draw_panel(img, self.back_rect(legs), SANDED, shadow=False)
        draw_pallet(img, self.CX, self.BY, SANDED, legs=legs)
        info = draw_maya(img, 960, 1590, f=-1, pose='kneel_drill', t=lt, smile=0.2)
        j = random.Random(int(t * 60)).uniform(-3, 3) if drilling else 0
        tip = tool_drill(img, info, f=-1, jitter=j)
        if drilling:
            dust(img, (t - 14.3) % 1.0, tip, rate=60, life=0.7, seed=int(t) + 20, col=(230, 205, 160), spread=0.8)

    def cu1(self, lt): return cu_brush(lt, SANDED, self.fin)
    def cu2(self, lt): return cu_led(lt, self.fin, tuple(self.sc['led']))

    def payoff_objects(self, img):
        draw_panel(img, self.back_rect(36), self.fin, shadow=False)
        g = draw_pallet(img, self.CX, self.BY, self.fin, legs=36)
        ImageDraw.Draw(img).line([(g['x0'] + 10, self.BY - 34), (g['x1'] - 10, self.BY - 34)],
                                 fill=mix(tuple(self.sc['led']), (255, 255, 255), 0.5), width=4)
        draw_cushion(img, g['x0'] + 10, g['x1'] - 8, g['t0'], g['dx'], g['dy'], self.sc['cushion'], self.sc['pillows'])
        return (self.CX + 50, g['t0'] - 26, 0.88 if self.sc['pet']['kind'] == 'dog' else 1.0)

    def sfx(self):
        return [('drop_wood', 4.72), ('sand', 8.0, 11.0), ('knock', 11.05), ('knock', 11.35),
                ('hammer', self.HAM0, self.HAMP, 6)] + [('drill', a, b) for a, b in self.DRILL] + \
               [('brush', 17.15, 19.35), ('led', 19.6)]

    HOOKS = ["2 old pallets → {pet}'s dream bed", "Free pallets → cozy {pet} bed", "2 pallets → {pet} heaven"]
    TITLES = ["2 Old Pallets → My {Pet}'s Dream Bed", "I Turned Free Pallets Into a Cozy {Pet} Bed",
              "Pallet {Pet} Bed With LED Glow", "From Trash Pallets to {Pet} Bed Glow-Up"]
    PAYOFF = "The {pet} claimed it in 3 seconds."
    TAGS = ['#palletproject', '#palletfurniture', '#palletbed', '#woodworking', '#reclaimedwood', '#petbed']


# ================================================================ 2) BRİKET BANK
BW, BH, BDX, BDY = 170, 80, 70, -44
RAWB = H_('9A9A96')
SLOTS = [(200, 1590), (200, 1510), (200, 1430), (650, 1590), (650, 1510), (650, 1430)]
PILE_B = [(160, 1630), (350, 1635), (255, 1555), (560, 1640), (455, 1560)]
SX0, SX1, SEAT = 180, 875, 1350

def draw_block(img, x0, by, col, seed=0, plants=False, shadow=False):
    d = ImageDraw.Draw(img, 'RGBA')
    if shadow: d.ellipse((x0 - 10, by - 12, x0 + BW + BDX + 10, by + 16), fill=(40, 25, 15, 60))
    d.polygon([(x0 + BW, by - BH), (x0 + BW + BDX, by - BH + BDY), (x0 + BW + BDX, by + BDY), (x0 + BW, by)], fill=shade(col, 0.72))
    d.polygon([(x0, by - BH), (x0 + BW, by - BH), (x0 + BW + BDX, by - BH + BDY), (x0 + BDX, by - BH + BDY)], fill=shade(col, 1.08))
    d.rectangle((x0, by - BH, x0 + BW, by), fill=col)
    d.line([(x0, by - BH), (x0 + BW, by - BH)], fill=shade(col, 1.18), width=2)
    r = random.Random(seed)
    for _ in range(26):
        circ(d, (r.uniform(x0 + 4, x0 + BW - 4), r.uniform(by - BH + 4, by - 4)), r.uniform(1, 2.6),
             shade(col, r.choice([0.78, 1.14])))
    for hx0 in (x0 + 16, x0 + 94):
        d.rectangle((hx0, by - BH + 14, hx0 + 60, by - 14), fill=shade(col, 0.3))
        d.rectangle((hx0, by - BH + 14, hx0 + 60, by - BH + 24), fill=shade(col, 0.18))
        if plants:
            draw_succulent(d, hx0 + 30, by - 26, 30, ys=0.55)

def draw_beams_lean(img, col):
    d = ImageDraw.Draw(img, 'RGBA')
    for i in range(3):
        bx, tx = 800 + i * 50, 745 + i * 50
        d.polygon([(bx, 1262), (bx + 38, 1262), (tx + 38, 880), (tx, 880)], fill=shade(col, 1 - i * 0.06))
        d.line([(bx + 38, 1262), (tx + 38, 880)], fill=shade(col, 0.7), width=3)

def draw_seat(img, n, col):
    d = ImageDraw.Draw(img, 'RGBA')
    present = [2, 1, 0][:n]
    for i in (2, 1, 0):
        if i not in present: continue
        a, b = i / 3, (i + 1) / 3
        ox, oy = BDX * a, BDY * a; ox2, oy2 = BDX * b, BDY * b
        top = SEAT - 36
        d.polygon([(SX0 + ox, top + oy), (SX1 + ox, top + oy), (SX1 + ox2, top + oy2), (SX0 + ox2, top + oy2)], fill=col)
        d.polygon([(SX1 + ox, top + oy), (SX1 + ox2, top + oy2), (SX1 + ox2, SEAT + oy2), (SX1 + ox, SEAT + oy)], fill=shade(col, 0.7))
        d.rectangle((SX0 + ox, top + oy, SX1 + ox, SEAT + oy), fill=shade(col, 0.85))
        d.line([(SX0 + ox, top + oy), (SX1 + ox, top + oy)], fill=shade(col, 1.15), width=2)
        grain(d, SX0 + ox, top + oy, SX1 + ox, SEAT + oy, shade(col, 0.85), 60 + i, 3)

class BlockBench:
    key = 'block_bench'
    locations = ['garden', 'balcony', 'living']
    pets = ['dog', 'cat']
    plant_front = True
    led_floor = None
    anchor_stop_x, carry_dx, carry_dy = 330, 55, 45
    item_final = (455 + BW / 2, 1560)
    PLACE = [0.0, 0.45, 1.0, 1.55, 2.1, 2.6]
    DRILL = [(15.3, 16.0), (16.3, 16.9)]

    def __init__(self, sc):
        self.sc = sc
        self.paint = H_(sc['paint'][1]); self.fin = H_(sc['finish'][1])
        self.can_col, self.can_label = self.paint, 'PAINT'
        self.beam_raw = H_('B8A488')

    def draw_item(self, img, cx, by): draw_block(img, cx - BW / 2, by, RAWB, seed=99)
    def anchor_static(self, img):
        draw_beams_lean(img, self.beam_raw)
        for i, (x0, by) in enumerate(PILE_B[:4]): draw_block(img, x0, by, RAWB, seed=i, shadow=by > 1600)

    def stakes(self, img, lt):
        draw_beams_lean(img, self.beam_raw)
        for i, (x0, by) in enumerate(PILE_B): draw_block(img, x0, by, RAWB, seed=i if i < 4 else 99, shadow=by > 1600)
        maya_think(img, 90, 1600, lt)

    def proc_a(self, img, lt):
        draw_beams_lean(img, self.beam_raw)
        n = sum(1 for p in self.PLACE if p <= lt)
        for i, (x0, by) in enumerate(SLOTS[:n]):
            draw_block(img, x0, by, RAWB, seed=i, shadow=by == 1590)
            if 0 <= lt - self.PLACE[i] < 0.5:
                dust(img, lt - self.PLACE[i], (x0 + BW / 2, by), rate=70, life=0.5, seed=i + 3, spread=1.3)
        if n < 6:
            left = SLOTS[n][0] == 200
            f = 1 if left else -1
            info = draw_maya(img, 60 if left else 1010, 1600, f=f, pose='carry', t=lt, smile=0.3)
            draw_block(img, info['hf'][0] + f * 40 - BW / 2, info['hf'][1] + 45, RAWB, seed=99)
            circ(ImageDraw.Draw(img, 'RGBA'), info['hf'], 18, H_('C4955E'))

    def proc_b(self, img, lt):
        draw_beams_lean(img, self.beam_raw)
        kl, kr = ease(lt / 1.4), ease((lt - 1.5) / 1.4)
        for i, (x0, by) in enumerate(SLOTS):
            draw_block(img, x0, by, mix(RAWB, self.paint, kl if x0 == 200 else kr), seed=i, shadow=by == 1590)
        left = lt < 1.5
        f = 1 if left else -1
        ph = lt * 2 * math.pi * 1.6
        info = draw_maya(img, 20 if left else 1030, 1600, f=f, pose='kneel', t=lt, smile=0.3,
                         arms=(40, 60, 70 + 18 * math.sin(ph), 95 + 22 * math.sin(ph)))
        tool_roller(img, info, self.paint, f=f)

    def proc_c(self, img, lt):
        t = 14 + lt
        for i, (x0, by) in enumerate(SLOTS): draw_block(img, x0, by, self.paint, seed=i, shadow=by == 1590)
        if lt < 1.0:
            draw_seat(img, 1, self.fin)
            info = draw_maya(img, 1000, 1600, f=-1, pose='carry', t=lt, smile=0.3)
            d = ImageDraw.Draw(img, 'RGBA'); hx, hy = info['hf']
            d.rectangle((hx - 520, hy - 20, hx + 40, hy + 16), fill=self.fin)
            d.rectangle((hx - 520, hy - 20, hx + 40, hy - 12), fill=shade(self.fin, 1.15))
            circ(d, info['hf'], 18, H_('C4955E'))
            return
        draw_seat(img, 3, self.fin)
        drilling = any(a <= t < b for a, b in self.DRILL)
        info = draw_maya(img, 1010, 1590, f=-1, pose='kneel_drill', t=lt, smile=0.2)
        j = random.Random(int(t * 60)).uniform(-3, 3) if drilling else 0
        tip = tool_drill(img, info, f=-1, jitter=j)
        if drilling:
            dust(img, (t - 15.3) % 1.0, tip, rate=60, life=0.7, seed=int(t) + 20, col=(230, 205, 160), spread=0.8)

    def cu1(self, lt): return cu_roller(lt, RAWB, self.paint)
    def cu2(self, lt): return cu_plants(lt, self.paint)

    def payoff_objects(self, img):
        for i, (x0, by) in enumerate(SLOTS):
            draw_block(img, x0, by, self.paint, seed=i, plants=by < 1590, shadow=by == 1590)
        draw_seat(img, 3, self.fin)
        draw_cushion(img, SX0 + 12, SX1 - 12, SEAT - 36, BDX, BDY, self.sc['cushion'], self.sc['pillows'])
        return (560, SEAT - 76, 0.8 if self.sc['pet']['kind'] == 'dog' else 0.95)

    def sfx(self):
        return [('drop_heavy', 4.72)] + [('drop_heavy', 8.0 + p) for p in self.PLACE] + \
               [('roller', 11.0, 14.0), ('knock', 14.05), ('drop_wood', 14.95)] + \
               [('drill', a, b) for a, b in self.DRILL] + \
               [('roller', 17.1, 19.4), ('plant', 19.5 + 0.75), ('plant', 19.5 + 1.7)]

    HOOKS = ["6 cinder blocks → cozy bench", "Grey blocks → {paint} bench", "$15 of cinder blocks → Pinterest bench"]
    TITLES = ["6 Cinder Blocks → Cozy Succulent Bench", "Cheap Cinder Blocks Into a Pinterest Bench",
              "Grey Blocks → {Paint} Bench Glow-Up", "I Built a Bench From Cinder Blocks ({Pet} Approved)"]
    PAYOFF = "Succulents in every hole, and the {pet} took the best seat."
    TAGS = ['#cinderblock', '#cinderblockbench', '#concretediy', '#succulents', '#gardenideas', '#benchdiy']


# ================================================================ 3) KASA RAF
CW, CH, CDX, CDY = 200, 150, 55, -35
RAWC = H_('A39A8C'); SANDC = H_('DCC7A3')
GRID = [(340, 1590), (560, 1590), (340, 1440), (560, 1440), (340, 1290), (560, 1290)]
PILE_C = [(130, 1630), (360, 1635), (600, 1640), (245, 1480), (470, 1485)]
BOOKS = ['3F4E6B', 'C98B6B', 'E8D9B5', '7F9A7A', 'B04E28', 'D9A441', '5A4636']

def draw_crate(img, x0, by, col, contents=None, led=None, shadow=False):
    d = ImageDraw.Draw(img, 'RGBA')
    if shadow: d.ellipse((x0 - 10, by - 12, x0 + CW + CDX + 10, by + 16), fill=(40, 25, 15, 60))
    side = [(x0 + CW, by - CH), (x0 + CW + CDX, by - CH + CDY), (x0 + CW + CDX, by + CDY), (x0 + CW, by)]
    d.polygon(side, fill=shade(col, 0.72))
    for k in (0.33, 0.66):
        d.line([(x0 + CW, by - CH + CH * k), (x0 + CW + CDX, by - CH + CDY + CH * k)], fill=shade(col, 0.45), width=4)
    d.rounded_rectangle((x0 + CW + 14, by - CH + CDY * 0.3 + 18, x0 + CW + CDX - 12, by - CH + CDY * 0.7 + 34), radius=6, fill=shade(col, 0.35))
    d.polygon([(x0, by - CH), (x0 + CW, by - CH), (x0 + CW + CDX, by - CH + CDY), (x0 + CDX, by - CH + CDY)], fill=shade(col, 1.08))
    d.rectangle((x0, by - CH, x0 + CW, by), fill=col)
    d.rectangle((x0 + 14, by - CH + 14, x0 + CW - 14, by - 14), fill=shade(col, 0.42))
    for j in range(3):
        ya = by - CH + 14 + j * (CH - 28) / 3
        d.rectangle((x0 + 14, ya + 4, x0 + CW - 14, ya + (CH - 28) / 3 - 6), fill=shade(col, 0.6))
    d.polygon([(x0 + 14, by - CH + 14), (x0 + 32, by - CH + 28), (x0 + 32, by - 32), (x0 + 14, by - 14)], fill=shade(col, 0.52))
    d.rectangle((x0 + 14, by - 34, x0 + CW - 14, by - 14), fill=shade(col, 0.7))
    d.line([(x0, by - CH), (x0 + CW, by - CH)], fill=shade(col, 1.15), width=2)
    grain(d, x0, by - CH, x0 + CW, by - CH + 14, col, int(x0 + by), 2)
    grain(d, x0, by - 14, x0 + CW, by, col, int(x0 + by) + 1, 2)
    if led:
        for k, a in ((26, 40), (14, 80), (5, 200)):
            d.rectangle((x0 + 18, by - CH + 16, x0 + CW - 18, by - CH + 16 + k), fill=tuple(led) + (a,))
        d.polygon([(x0 + 30, by - CH + 20), (x0 + CW - 30, by - CH + 20), (x0 + CW - 16, by - 34), (x0 + 16, by - 34)],
                  fill=tuple(led) + (35,))
    if contents == 'books':
        x = x0 + 36
        r = random.Random(x0 + by)
        while x < x0 + CW - 40:
            w = r.randint(14, 24); h = r.randint(70, 100)
            d.rectangle((x, by - 34 - h, x + w, by - 34), fill=H_(r.choice(BOOKS)))
            d.line([(x + 3, by - 34 - h + 12), (x + w - 3, by - 34 - h + 12)], fill=(255, 255, 255, 120), width=2)
            x += w + 2
    elif contents == 'plant':
        draw_plant_pot(img, x0 + CW / 2, by - 34, s=0.45, pot=H_('E8DFCF'), seed=int(x0))
    elif contents == 'candle':
        for cx_, h in ((x0 + 70, 60), (x0 + 120, 42)):
            d.rounded_rectangle((cx_ - 20, by - 34 - h, cx_ + 20, by - 34), radius=6, fill=H_('F4EBDB'))
            circ(d, (cx_, by - 44 - h), 16, (255, 190, 90, 90)); d.ellipse((cx_ - 5, by - 54 - h, cx_ + 5, by - 36 - h), fill=H_('FFD27A'))

class CrateShelf:
    key = 'crate_shelf'
    locations = ['living', 'garage', 'balcony']
    pets = ['cat']
    plant_front = True
    led_floor = None
    anchor_stop_x, carry_dx, carry_dy = 270, 90, 80
    item_final = (470 + CW / 2, 1485)
    PLACE = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]
    DRILL = [(14.3, 15.1), (15.6, 16.5)]

    def __init__(self, sc):
        self.sc = sc
        self.fin = H_(sc['finish'][1])
        self.can_col, self.can_label = self.fin, 'STAIN'

    def draw_item(self, img, cx, by): draw_crate(img, cx - CW / 2, by, RAWC)
    def pile(self, img, col, n=5):
        for i, (x0, by) in enumerate(PILE_C[:n]): draw_crate(img, x0, by, col, shadow=by > 1600)
    def anchor_static(self, img): self.pile(img, RAWC, 4)

    def stakes(self, img, lt):
        self.pile(img, RAWC)
        maya_think(img, 950, 1600, lt, f=-1)

    def proc_a(self, img, lt):
        self.pile(img, mix(RAWC, SANDC, ease(lt / 2.8)))
        info = draw_maya(img, 1010, 1600, f=-1, pose='kneel', t=lt, smile=0.2)
        dust(img, lt, tool_sander(img, info), rate=50, life=1.0, seed=7)

    def proc_b(self, img, lt):
        n = sum(1 for p in self.PLACE if p <= lt)
        for i, (x0, by) in enumerate(GRID[:n]):
            draw_crate(img, x0, by, SANDC, shadow=by == 1590)
            if 0 <= lt - self.PLACE[i] < 0.4:
                dust(img, lt - self.PLACE[i], (x0 + CW / 2, by), rate=60, life=0.4, seed=i + 5, spread=1.2)
        if n < 6:
            left = GRID[n][0] == 340
            f = 1 if left else -1
            info = draw_maya(img, 150 if left else 990, 1600, f=f, pose='carry', t=lt, smile=0.3)
            draw_crate(img, info['hf'][0] + f * 70 - CW / 2, info['hf'][1] + 75, SANDC)
            circ(ImageDraw.Draw(img, 'RGBA'), info['hf'], 18, H_('C4955E'))

    def proc_c(self, img, lt):
        t = 14 + lt
        for x0, by in GRID: draw_crate(img, x0, by, SANDC, shadow=by == 1590)
        drilling = any(a <= t < b for a, b in self.DRILL)
        info = draw_maya(img, 1000, 1600, f=-1, pose='kneel_drill', t=lt, smile=0.2)
        j = random.Random(int(t * 60)).uniform(-3, 3) if drilling else 0
        tip = tool_drill(img, info, f=-1, jitter=j)
        if drilling:
            dust(img, (t - 14.3) % 1.0, tip, rate=60, life=0.7, seed=int(t) + 20, col=(230, 205, 160), spread=0.8)

    def cu1(self, lt): return cu_brush(lt, SANDC, self.fin)
    def cu2(self, lt): return cu_led(lt, self.fin, tuple(self.sc['led']))

    def payoff_objects(self, img):
        contents = ['books', None, 'plant', 'books', 'candle', 'books']
        for (x0, by), c in zip(GRID, contents):
            draw_crate(img, x0, by, self.fin, contents=c, led=self.sc['led'], shadow=by == 1590)
        draw_plant_pot(img, 360 + 90, 1140 - 18, s=0.55, pot=H_(self.sc['pot']), seed=11)
        d = ImageDraw.Draw(img, 'RGBA')
        d.rectangle((600, 1030, 690, 1122), fill=H_('3F3A36')); d.rectangle((610, 1040, 680, 1112), fill=H_('E8DFCF'))
        circ(d, (645, 1070), 18, H_(self.sc['pillows'][0]))
        return (560 + CW / 2 + 6, 1590 - 34, 0.78)

    def sfx(self):
        return [('drop_wood', 4.72), ('sand', 8.0, 11.0)] + [('knock', 11.0 + p, 0.7) for p in self.PLACE] + \
               [('drill', a, b) for a, b in self.DRILL] + [('brush', 17.15, 19.35), ('led', 19.6)]

    HOOKS = ["6 old crates → dream shelf", "Market crates → cozy bookshelf", "6 crates → {pet}'s favorite shelf"]
    TITLES = ["6 Old Crates → Dream Bookshelf", "Wooden Crates Into a Cozy Shelf (Cat Approved)",
              "Crate Shelf Glow-Up With Hidden LEDs", "I Turned Old Crates Into a Bookshelf"]
    PAYOFF = "The {pet} moved into the bottom cubby immediately."
    TAGS = ['#woodencrates', '#crateshelf', '#shelfideas', '#smallspaceideas', '#bookshelf', '#upcycledfurniture']


# ================================================================ 4) LASTİK PUF
TRX, TRY, TBAND = 170, 50, 80
DIRTY = H_('5E5850'); CLEAN = H_('2B2B2D')

def draw_tire(img, cx, by, col, rope=0.0, rope_col=None, shadow=False):
    d = ImageDraw.Draw(img, 'RGBA')
    rx, ry, band = TRX, TRY, TBAND
    cb = by - ry; ct = cb - band
    if shadow: d.ellipse((cx - rx - 12, by - ry * 0.6, cx + rx + 12, by + 14), fill=(40, 25, 15, 60))
    d.ellipse((cx - rx, cb - ry, cx + rx, cb + ry), fill=shade(col, 0.85))
    d.rectangle((cx - rx, ct, cx + rx, cb), fill=col)
    for a in np.linspace(0.15, math.pi - 0.15, 14):
        x = cx + rx * math.cos(a); off = ry * math.sin(a)
        d.line([(x, ct + off + 6), (x, cb + off - 6)], fill=shade(col, 0.7), width=5)
    if rope > 0:
        rows = int(band / 12) + 1
        for i in range(int(rows * rope + 0.999)):
            yc = cb - i * 12
            d.arc((cx - rx - 2, yc - ry - 2, cx + rx + 2, yc + ry + 2), 0, 180,
                  fill=rope_col if i % 2 == 0 else shade(rope_col, 0.88), width=13)
    d.ellipse((cx - rx, ct - ry, cx + rx, ct + ry), fill=shade(col, 1.25))
    d.ellipse((cx - rx * 0.55, ct - ry * 0.55, cx + rx * 0.55, ct + ry * 0.55), fill=shade(col, 0.35))
    return ct

def draw_disc(img, cx, cy, rx, col, cushion=None):
    d = ImageDraw.Draw(img, 'RGBA'); ry = rx * 0.3
    d.ellipse((cx - rx, cy - ry + 8, cx + rx, cy + ry + 8), fill=shade(col, 0.7))
    d.rectangle((cx - rx, cy, cx + rx, cy + 8), fill=shade(col, 0.7))
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=col)
    for k in (0.3, 0.55, 0.8):
        d.arc((cx - rx * k, cy - ry * k, cx + rx * k, cy + ry * k), 200, 340, fill=shade(col, 0.85), width=2)
    if cushion:
        c = H_(cushion); y = cy - 22
        d.ellipse((cx - rx + 10, y - ry + 18, cx + rx - 10, y + ry + 18), fill=shade(c, 0.88))
        d.rectangle((cx - rx + 10, y, cx + rx - 10, y + 18), fill=shade(c, 0.88))
        d.ellipse((cx - rx + 10, y - ry + 4, cx + rx - 10, y + ry + 4), fill=c)
        d.ellipse((cx - rx + 30, y - ry + 14, cx + rx - 30, y + ry - 6), outline=shade(c, 0.85), width=3)
        return y - 10
    return cy

class TireOttoman:
    key = 'tire_ottoman'
    locations = ['garage', 'balcony', 'living', 'garden']
    pets = ['dog', 'cat']
    plant_front = True
    led_floor = None
    anchor_stop_x, carry_dx, carry_dy = 260, 120, 110
    CX, BY = 520, 1610
    PILE = [(360, 1625), (640, 1640)]
    item_final = (640, 1640)
    DRILL = [(12.4, 13.2), (13.5, 14.0)]

    def __init__(self, sc):
        self.sc = sc
        self.fin = H_(sc['finish'][1]); self.rope = H_(sc['rope'][1])
        self.can_col, self.can_label = self.fin, 'STAIN'

    def props(self, img, disc_col=SANDED):
        d = ImageDraw.Draw(img, 'RGBA')
        d.ellipse((800, 930, 1010, 1262), fill=shade(disc_col, 0.8))
        d.ellipse((812, 936, 1004, 1252), fill=disc_col)
        d.ellipse((50, 1700, 250, 1740), fill=(40, 25, 15, 60))
        for k in range(6):
            d.ellipse((60 + k * 12, 1640 + k * 5, 240 - k * 12, 1720 - k * 5), outline=shade(self.rope, 1 - k * 0.05), width=11)

    def draw_item(self, img, cx, by): draw_tire(img, cx, by, DIRTY)
    def anchor_static(self, img):
        self.props(img); draw_tire(img, *self.PILE[0], DIRTY, shadow=True)

    def stakes(self, img, lt):
        self.props(img)
        for p in self.PILE: draw_tire(img, *p, DIRTY, shadow=True)
        maya_think(img, 950, 1600, lt, f=-1)

    def proc_a(self, img, lt):
        self.props(img)
        col = mix(DIRTY, CLEAN, ease(lt / 2.8))
        for p in self.PILE: draw_tire(img, *p, col, shadow=True)
        ph = lt * 2 * math.pi * 2.2
        info = draw_maya(img, 100, 1600, pose='kneel', t=lt, smile=0.3,
                         arms=(15, 25, 20 + 10 * math.sin(ph), 30 + 12 * math.sin(ph)))
        d = ImageDraw.Draw(img, 'RGBA'); hx, hy = info['hf']
        d.rounded_rectangle((hx - 36, hy + 2, hx + 40, hy + 40), radius=10, fill=H_('F2C94C'))
        circ(d, info['hf'], 18, H_('C4955E'))
        dust(img, lt, (hx, hy + 30), rate=40, life=1.3, seed=12, col=(255, 255, 255), spread=0.6)

    def proc_b(self, img, lt):
        self.props(img)
        draw_tire(img, self.CX, self.BY, CLEAN, shadow=True)
        if lt < 1.2:
            info = draw_maya(img, 930, 1600, f=-1, pose='carry', t=lt, smile=0.3)
            draw_tire(img, info['hf'][0] - 120, info['hf'][1] + 110, CLEAN)
            circ(ImageDraw.Draw(img, 'RGBA'), info['hf'], 18, H_('C4955E'))
            return
        ct = draw_tire(img, self.CX, self.BY - TBAND, CLEAN)
        draw_disc(img, self.CX, ct - 6, TRX + 14, SANDED)
        t = 11 + lt
        drilling = any(a <= t < b for a, b in self.DRILL)
        info = draw_maya(img, 930, 1590, f=-1, pose='kneel_drill', t=lt, smile=0.2, arms=(50, 88, 40, 70))
        j = random.Random(int(t * 60)).uniform(-3, 3) if drilling else 0
        tip = tool_drill(img, info, f=-1, jitter=j)
        if drilling: dust(img, (t - 12.4) % 1.0, tip, rate=60, life=0.7, seed=int(t) + 20, col=(230, 205, 160), spread=0.8)

    def proc_c(self, img, lt):
        self.props(img)
        p = ease(lt / 2.9)
        draw_tire(img, self.CX, self.BY, CLEAN, rope=clamp(p * 2), rope_col=self.rope, shadow=True)
        ct = draw_tire(img, self.CX, self.BY - TBAND, CLEAN, rope=clamp(p * 2 - 1), rope_col=self.rope)
        draw_disc(img, self.CX, ct - 6, TRX + 14, SANDED)
        ph = lt * 2 * math.pi * 1.8
        info = draw_maya(img, 930, 1600, f=-1, pose='kneel', t=lt, smile=0.3,
                         arms=(45, 75, 45 + 20 * math.sin(ph), 75 + 20 * math.cos(ph)))
        wy = self.BY - TRY - p * 2 * TBAND + TRY * 0.9
        ImageDraw.Draw(img, 'RGBA').line([info['hf'], (self.CX + TRX * 0.7, wy)], fill=self.rope, width=8)

    def cu1(self, lt): return cu_rope(lt, self.rope)
    def cu2(self, lt): return cu_brush(lt, SANDED, self.fin)

    def payoff_objects(self, img):
        draw_tire(img, self.CX, self.BY, CLEAN, rope=1, rope_col=self.rope, shadow=True)
        ct = draw_tire(img, self.CX, self.BY - TBAND, CLEAN, rope=1, rope_col=self.rope)
        top = draw_disc(img, self.CX, ct - 6, TRX + 14, self.fin, cushion=self.sc['cushion'])
        return (self.CX, top + 8, 0.72 if self.sc['pet']['kind'] == 'dog' else 0.9)

    def sfx(self):
        return [('drop_heavy', 4.72), ('scrub', 8.0, 11.0), ('knock', 11.1), ('drop_heavy', 12.2)] + \
               [('drill', a, b) for a, b in self.DRILL] + [('brush', 14.2, 16.9), ('brush', 17.1, 19.4), ('brush', 19.6, 21.8)]

    HOOKS = ["2 old tires → cozy rope pouf", "Junk tires → Pinterest ottoman", "Free tires → {pet}'s new throne"]
    TITLES = ["2 Old Tires → Cozy Rope Ottoman", "I Turned Junk Tires Into a Pinterest Pouf",
              "Tire + Rope = My {Pet}'s New Favorite Seat", "Old Tire Ottoman Glow-Up"]
    PAYOFF = "The {pet} fell asleep on it before the glue dried."
    TAGS = ['#tirecraft', '#upcycledtires', '#ropecraft', '#ottoman', '#poufdiy', '#recycledcrafts']


# ================================================================ 5) MERDİVEN RAF
LB, LT = 1600, 640
RUNGS = [0.08, 0.2, 0.34, 0.47, 0.6, 0.74, 0.88]
PLANKS = [0.2, 0.47, 0.74]
def rail_x(side, y):
    f = (LB - y) / (LB - LT)
    return lerp(330, 395, f) if side == 'l' else lerp(690, 645, f)
def ly(f): return LB - (LB - LT) * f

def draw_ladder(img, col, planks=0, plank_col=None, led=None):
    d = ImageDraw.Draw(img, 'RGBA')
    d.polygon([(700, 1600), (720, 1600), (690, 640), (665, 640)], fill=(40, 25, 15, 40))
    for f in RUNGS:
        y = ly(f); d.rectangle((rail_x('l', y), y - 9, rail_x('r', y), y + 9), fill=shade(col, 0.82))
    for side in ('l', 'r'):
        xb, xt = rail_x(side, LB), rail_x(side, LT)
        d.polygon([(xb - 17, LB), (xb + 17, LB), (xt + 14, LT), (xt - 14, LT)], fill=col)
        d.line([(xb - 17, LB), (xt - 14, LT)], fill=shade(col, 1.15), width=3)
        circ(d, (xt, LT), 14, col)
    pc = plank_col or col
    for f in PLANKS[:planks]:
        y = ly(f); x0, x1 = rail_x('l', y) - 45, rail_x('r', y) + 45
        d.polygon([(x0, y - 22), (x1, y - 22), (x1 + 35, y - 52), (x0 + 35, y - 52)], fill=pc)
        d.rectangle((x0, y - 22, x1, y), fill=shade(pc, 0.82))
        grain(d, x0, y - 22, x1, y, shade(pc, 0.82), int(y), 2)
        if led:
            for k, a in ((30, 40), (14, 90), (4, 220)):
                d.rectangle((x0 + 10, y, x1 - 10, y + k), fill=tuple(led) + (a,))

def draw_plank_stack(img, cx, by, col):
    d = ImageDraw.Draw(img, 'RGBA')
    d.ellipse((cx - 230, by - 12, cx + 250, by + 14), fill=(40, 25, 15, 60))
    for i in range(3):
        y = by - i * 22
        d.polygon([(cx - 210, y - 22), (cx + 210, y - 22), (cx + 240, y - 44), (cx - 180, y - 44)], fill=col)
        d.rectangle((cx - 210, y - 22, cx + 210, y), fill=shade(col, 0.82 - i * 0.03))

class LadderShelf:
    key = 'ladder_shelf'
    locations = ['living', 'balcony', 'garden']
    pets = ['cat']
    plant_front = True
    led_floor = None
    anchor_stop_x, carry_dx, carry_dy = 300, 110, 70
    item_final = (560, 1720)
    HAM0, HAMP = 11.25, 0.3
    DRILL = [(14.3, 15.1), (15.6, 16.5)]

    def __init__(self, sc):
        self.sc = sc
        self.fin = H_(sc['finish'][1])
        self.can_col, self.can_label = self.fin, 'STAIN'

    def draw_item(self, img, cx, by): draw_plank_stack(img, cx, by, RAW)
    def anchor_static(self, img): draw_ladder(img, RAW)

    def stakes(self, img, lt):
        draw_ladder(img, RAW); draw_plank_stack(img, *self.item_final, RAW)
        maya_think(img, 130, 1600, lt)

    def proc_a(self, img, lt):
        col = mix(RAW, SANDED, ease(lt / 2.8))
        draw_ladder(img, col); draw_plank_stack(img, *self.item_final, col)
        ph = lt * 2 * math.pi * 2.2
        info = draw_maya(img, 150, 1600, pose='stand', t=lt, smile=0.2,
                         arms=(40, 70, 62 + 10 * math.sin(ph), 58 + 12 * math.sin(ph)), lean=8)
        dust(img, lt, tool_sander(img, info), rate=50, life=1.0, seed=7)

    def proc_b(self, img, lt):
        t = 11 + lt
        n = 1 + (lt > 1.0) + (lt > 2.0)
        draw_ladder(img, SANDED, planks=n)
        u = ((t - self.HAM0) % self.HAMP) / self.HAMP if t >= self.HAM0 else 0.6
        ang = lerp(40, 165, ease(u / 0.7)) if u < 0.7 else lerp(165, 40, (u - 0.7) / 0.3)
        info = draw_maya(img, 900, 1600, f=-1, pose='stand', t=lt, smile=0.2, arms=(95, 100, ang, ang + 25), lean=6)
        hend = tool_hammer(img, info, ang)
        if u < 0.12 and t >= self.HAM0: circ(ImageDraw.Draw(img, 'RGBA'), hend, 28, (255, 240, 200, 110))

    def proc_c(self, img, lt):
        t = 14 + lt
        draw_ladder(img, SANDED, planks=3)
        drilling = any(a <= t < b for a, b in self.DRILL)
        info = draw_maya(img, 930, 1600, f=-1, pose='kneel_drill', t=lt, smile=0.2)
        j = random.Random(int(t * 60)).uniform(-3, 3) if drilling else 0
        tip = tool_drill(img, info, f=-1, jitter=j)
        if drilling: dust(img, (t - 14.3) % 1.0, tip, rate=60, life=0.7, seed=int(t) + 20, col=(230, 205, 160), spread=0.8)

    def cu1(self, lt): return cu_brush(lt, SANDED, self.fin)
    def cu2(self, lt): return cu_led(lt, self.fin, tuple(self.sc['led']))

    def payoff_objects(self, img):
        led = self.sc['led']
        draw_ladder(img, self.fin, planks=3, led=led)
        d = ImageDraw.Draw(img, 'RGBA')
        for side in ('l', 'r'):
            for k in range(12):
                y = lerp(LB - 40, LT + 30, k / 11); x = rail_x(side, y) + (10 if k % 2 else -10)
                circ(d, (x, y), 14, tuple(led) + (70,)); circ(d, (x, y), 5, (255, 240, 200))
        y1, y2 = ly(0.47) - 22, ly(0.74) - 22
        draw_succulent(d, 440, y1 - 30, 34, ys=0.6)
        d.rounded_rectangle((410, y1 - 34, 470, y1), radius=6, fill=H_(self.sc['pot']))
        draw_succulent(d, 440, y1 - 40, 30, ys=0.6)
        x = 540; r = random.Random(4)
        for _ in range(5):
            w = r.randint(16, 22); h = r.randint(60, 84)
            d.rectangle((x, y1 - h, x + w, y1), fill=H_(r.choice(BOOKS))); x += w + 2
        draw_plant_pot(img, 470, y2, s=0.42, pot=H_(self.sc['pot']), seed=21)
        d.rounded_rectangle((575, y2 - 50, 615, y2), radius=6, fill=H_('F4EBDB'))
        circ(d, (595, y2 - 62), 18, (255, 190, 90, 110)); d.ellipse((590, y2 - 70, 600, y2 - 52), fill=H_('FFD27A'))
        y0 = ly(0.2) - 22
        c = H_(self.sc['cushion'])
        d.rounded_rectangle((rail_x('l', y0) - 25, y0 - 36, rail_x('r', y0) + 50, y0 + 4), radius=16, fill=c)
        return (515, y0 - 30, 0.82)

    def sfx(self):
        return [('drop_wood', 4.72), ('sand', 8.0, 11.0), ('knock', 11.05), ('hammer', self.HAM0, self.HAMP, 9)] + \
               [('drill', a, b) for a, b in self.DRILL] + [('brush', 17.15, 19.35), ('led', 19.6)]

    HOOKS = ["Old ladder → cozy plant shelf", "$0 ladder → Pinterest shelf", "Dusty ladder → {pet}'s lookout"]
    TITLES = ["Old Ladder → Cozy Plant Shelf", "I Turned a Dusty Ladder Into a Plant Shelf",
              "Ladder Shelf Glow-Up With Hidden LEDs", "Free Ladder → {Pet}-Approved Plant Shelf"]
    PAYOFF = "The {pet} claimed the bottom shelf."
    TAGS = ['#laddershelf', '#plantshelf', '#plantlover', '#reclaimedwood', '#shelfideas', '#upcycledfurniture']


# ================================================================ 6) BETON SAKSI
CONC = H_('A7A39C')
BUCKETS = [(420, 1640, 150, 170), (620, 1650, 130, 150), (800, 1660, 110, 125)]

def draw_bucket(img, cx, by, w, h, col, fill=0.0):
    d = ImageDraw.Draw(img, 'RGBA'); ry = w * 0.18
    d.ellipse((cx - w * 0.5, by - 10, cx + w * 0.5, by + 16), fill=(40, 25, 15, 60))
    d.ellipse((cx - w * 0.41, by - ry * 0.8, cx + w * 0.41, by + ry * 0.8), fill=shade(col, 0.9))
    d.polygon([(cx - w / 2, by - h), (cx + w / 2, by - h), (cx + w * 0.41, by), (cx - w * 0.41, by)], fill=col)
    d.line([(cx - w * 0.46, by - h * 0.7), (cx + w * 0.46, by - h * 0.7)], fill=shade(col, 0.85), width=4)
    d.ellipse((cx - w / 2, by - h - ry, cx + w / 2, by - h + ry), fill=shade(col, 0.35))
    if fill > 0:
        k = (1 - fill) * ry * 0.9
        d.ellipse((cx - w / 2 + 8, by - h - ry + 6 + k, cx + w / 2 - 8, by - h + ry - 6), fill=CONC)
    d.ellipse((cx - w / 2, by - h - ry, cx + w / 2, by - h + ry), outline=shade(col, 1.15), width=6)
    d.arc((cx - w / 2 - 4, by - h - ry - 40, cx + w / 2 + 4, by - h + ry + 10), 180, 360, fill=(90, 90, 90), width=4)

def draw_tub(img, cx, by, w, full=False, stir=None):
    d = ImageDraw.Draw(img, 'RGBA'); ry = w * 0.2
    d.ellipse((cx - w / 2 - 10, by - 14, cx + w / 2 + 10, by + 16), fill=(40, 25, 15, 60))
    d.ellipse((cx - w * 0.44, by - ry * 0.6, cx + w * 0.44, by + ry * 0.6), fill=H_('222222'))
    d.polygon([(cx - w / 2, by - 70), (cx + w / 2, by - 70), (cx + w * 0.44, by), (cx - w * 0.44, by)], fill=H_('2C2C2C'))
    d.ellipse((cx - w / 2, by - 70 - ry, cx + w / 2, by - 70 + ry), fill=H_('151515'))
    if full:
        d.ellipse((cx - w / 2 + 12, by - 70 - ry + 10, cx + w / 2 - 12, by - 70 + ry - 8), fill=CONC)
        if stir is not None:
            for i in range(3):
                a = stir * 4 + i * 2.1
                r = w * (0.12 + i * 0.08)
                d.arc((cx - r, by - 70 - r * 0.35, cx + r, by - 70 + r * 0.35), math.degrees(a), math.degrees(a) + 120,
                      fill=shade(CONC, 0.8), width=4)
    d.ellipse((cx - w / 2, by - 70 - ry, cx + w / 2, by - 70 + ry), outline=H_('3A3A3A'), width=7)

def draw_bag(img, cx, by, opened=False):
    d = ImageDraw.Draw(img, 'RGBA')
    d.ellipse((cx - 125, by - 12, cx + 125, by + 14), fill=(40, 25, 15, 60))
    h = 70 if opened else 110
    d.rounded_rectangle((cx - 115, by - h, cx + 115, by), radius=18, fill=H_('C9AE84'))
    d.rectangle((cx - 115, by - h * 0.62, cx + 115, by - h * 0.28), fill=H_('E8DFCF'))
    d.text((cx, by - h * 0.45), "CONCRETE", font=font(24), fill=H_('3F3A36'), anchor='mm')
    if opened: d.ellipse((cx - 60, by - h - 14, cx + 60, by - h + 10), fill=H_('BDB8B0'))

def draw_planter(img, cx, by, w, h, col, band=None, plant=None, seed=0):
    d = ImageDraw.Draw(img, 'RGBA'); ry = w * 0.18
    d.ellipse((cx - w / 2 - 12, by - 10, cx + w / 2 + 12, by + 18), fill=(40, 25, 15, 60))
    bc = band or col
    d.ellipse((cx - w / 2, by - ry, cx + w / 2, by + ry), fill=shade(bc, 0.85))
    d.rectangle((cx - w / 2, by - h, cx + w / 2, by), fill=col)
    if band: d.rectangle((cx - w / 2, by - h * 0.45, cx + w / 2, by), fill=band)
    r = random.Random(seed)
    for _ in range(int(w / 3)):
        circ(d, (r.uniform(cx - w / 2 + 4, cx + w / 2 - 4), r.uniform(by - h + 6, by - 4)), r.uniform(1, 2.4), shade(col, 0.7))
    d.line([(cx - w / 2 + 6, by - h), (cx - w / 2 + 6, by)], fill=shade(col, 1.12), width=6)
    d.ellipse((cx - w / 2, by - h - ry, cx + w / 2, by - h + ry), fill=shade(col, 1.12))
    d.ellipse((cx - w / 2 + 12, by - h - ry + 8, cx + w / 2 - 12, by - h + ry - 8), fill=H_('4A3526'))
    soil = by - h
    if plant == 'snake':
        for off, hh, lean in ((-40, 230, -30), (-12, 300, -6), (14, 270, 18), (38, 210, 36), (0, 180, 4)):
            pts = [(cx + off - 11, soil), (cx + off + 11, soil), (cx + off + lean, soil - hh)]
            d.polygon(pts, fill=H_('3F6B3A')); d.line([pts[0], pts[2]], fill=H_('C9C46A'), width=3)
            for k in (0.3, 0.55, 0.8):
                yk = soil - hh * k; d.line([(cx + off + lean * k - 6, yk), (cx + off + lean * k + 6, yk - 4)], fill=H_('5E8C4A'), width=3)
    elif plant == 'succ':
        draw_succulent(d, cx, soil - 6, w * 0.45, ys=0.55)
    elif plant == 'pothos':
        for _ in range(18):
            lx, ly_ = cx + r.uniform(-w * 0.55, w * 0.55), soil + r.uniform(-80, 5)
            d.ellipse((lx - 18, ly_ - 12, lx + 18, ly_ + 12), fill=r.choice([H_('5E8C4A'), H_('7BA65A'), H_('4E7A3E')]))
        for vx in (-w * 0.45, w * 0.48):
            for i in range(6):
                vy = soil + 8 + i * 24
                d.ellipse((cx + vx - 12 + (i % 2) * 8, vy - 8, cx + vx + 12 + (i % 2) * 8, vy + 8), fill=H_('6A9A50'))

class ConcretePlanters:
    key = 'concrete_planters'
    locations = ['balcony', 'garden', 'living']
    pets = ['dog', 'cat']
    plant_front = False
    led_floor = None
    anchor_stop_x, carry_dx, carry_dy = 360, 150, 60
    item_final = (760, 1745)
    TUB = (330, 1640, 300)
    POURS = [(11.05, 11.95), (12.05, 12.95), (13.05, 13.95)]

    def __init__(self, sc):
        self.sc = sc
        self.paint = H_(sc['paint'][1]); self.bucket = H_(sc['bucket'])
        self.can_col, self.can_label = self.paint, 'PAINT'

    def buckets(self, img, fills=(0, 0, 0)):
        for (cx, by, w, h), f in zip(BUCKETS, fills): draw_bucket(img, cx, by, w, h, self.bucket, f)
    def draw_item(self, img, cx, by): draw_bag(img, cx, by)
    def anchor_static(self, img):
        self.buckets(img); draw_tub(img, *self.TUB)

    def stakes(self, img, lt):
        self.buckets(img)
        maya_think(img, 90, 1600, lt)
        draw_tub(img, *self.TUB); draw_bag(img, *self.item_final)

    def proc_a(self, img, lt):
        self.buckets(img)
        ph = lt * 2 * math.pi * 1.4
        info = draw_maya(img, 90, 1600, pose='kneel', t=lt, smile=0.3,
                         arms=(10, 18, 15 + 10 * math.sin(ph), 20 + 12 * math.cos(ph)))
        draw_tub(img, *self.TUB, full=True, stir=lt)
        draw_bag(img, *self.item_final, opened=True)
        d = ImageDraw.Draw(img, 'RGBA'); hx, hy = info['hf']
        d.line([(hx, hy), (hx + 30, hy + 90)], fill=H_('8A6A48'), width=10)
        circ(d, info['hf'], 18, H_('C4955E'))
        if lt < 1.2: dust(img, lt, (330, 1560), rate=60, life=1.0, seed=2, col=(200, 196, 188), spread=1.2)

    def proc_b(self, img, lt):
        i = min(2, int(lt))
        fills = [clamp(lt - k) for k in range(3)]
        self.buckets(img, fills)
        cx, by, w, h = BUCKETS[i]
        info = draw_maya(img, cx - 250, 1600, pose='carry', t=lt, smile=0.3, arms=(30, 95, 45, 110), lean=10)
        d = ImageDraw.Draw(img, 'RGBA'); hx, hy = info['hf']
        d.ellipse((hx - 20, hy - 60, hx + 170, hy + 10), fill=H_('2C2C2C'))
        d.ellipse((hx + 110, hy - 50, hx + 175, hy), fill=CONC)
        if fills[i] < 1:
            top = by - h - w * 0.1
            wob = 5 * math.sin(lt * 20)
            d.polygon([(hx + 135, hy - 22), (hx + 178, hy - 22), (cx + 20 + wob, top), (cx - 20 + wob, top)], fill=shade(CONC, 0.92))
            d.line([(hx + 150, hy - 20), (cx - 6 + wob, top)], fill=shade(CONC, 1.15), width=5)
            r = random.Random(int(lt * 20))
            for _ in range(6):
                circ(d, (cx + r.uniform(-40, 40), top - r.uniform(0, 30)), r.uniform(3, 7), CONC)
        circ(d, info['hf'], 18, H_('C4955E'))

    def proc_c(self, img, lt):
        for k, (cx, by, w, h) in enumerate(BUCKETS):
            draw_planter(img, cx, by, w * 0.95, h * 0.95, CONC, seed=k)
        info = draw_maya(img, 1010, 1600, f=-1, pose='kneel', t=lt, smile=0.2)
        dust(img, lt, tool_sander(img, info), rate=50, life=1.0, seed=9, col=(205, 200, 192))

    def cu1(self, lt): return cu_pour(lt, CONC, self.bucket)
    def cu2(self, lt): return cu_roller(lt, CONC, self.paint)

    def payoff_objects(self, img):
        draw_planter(img, 300, 1560, 200, 240, CONC, band=self.paint, plant='snake', seed=1)
        draw_planter(img, 560, 1470, 120, 130, CONC, band=self.paint, plant='succ', seed=2)
        draw_planter(img, 800, 1560, 160, 180, CONC, band=self.paint, plant='pothos', seed=3)
        d = ImageDraw.Draw(img, 'RGBA')
        c = H_(self.sc['cushion'])
        d.ellipse((380, 1650, 740, 1760), fill=shade(c, 0.85))
        d.rectangle((380, 1680, 740, 1705), fill=shade(c, 0.85))
        d.ellipse((380, 1625, 740, 1735), fill=c)
        d.ellipse((420, 1640, 700, 1720), outline=shade(c, 0.85), width=4)
        return (560, 1690, 0.8 if self.sc['pet']['kind'] == 'dog' else 0.95)

    def sfx(self):
        return [('drop_heavy', 4.72), ('scrub', 8.0, 11.0)] + [('pour', a, b) for a, b in self.POURS] + \
               [('sand', 14.2, 16.8), ('pour', 17.2, 19.3), ('roller', 19.6, 21.8)]

    HOOKS = ["Old buckets → concrete planters", "$5 of concrete → designer planters", "Buckets + concrete → plant heaven"]
    TITLES = ["Old Buckets → Designer Concrete Planters", "DIY Concrete Planters That Look Expensive",
              "I Made Concrete Planters With Old Buckets", "Concrete Planters Glow-Up ({Paint} Dip)"]
    PAYOFF = "Three planters, one very relaxed {pet}."
    TAGS = ['#concreteplanter', '#concretediy', '#plantlover', '#houseplants', '#planterdiy', '#cementcraft']


TEMPLATES = {c.key: c for c in (PalletBed, BlockBench, CrateShelf, TireOttoman, LadderShelf, ConcretePlanters)}
