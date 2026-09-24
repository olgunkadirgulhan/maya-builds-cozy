"""Kanal görselleri: branding/banner.png (2560x1440), profile.png (800x800), watermark.png (150x150).
    python branding.py
"""
import os
from PIL import Image, ImageDraw, ImageFilter
from engine import (H_, mix, shade, circ, draw_maya, draw_pallet, draw_pet_curl, draw_succulent, draw_plant_pot, font)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'branding')
WARM_T, WARM_B = H_('F6D9B4'), H_('EBBE8C')
FLOOR = H_('C9955F')
CAT = dict(kind='cat', col=H_('E39A4B'), dark=H_('C47A2E'), light=H_('F6D2A6'), stripes=True)


def gradient(w, h, top, bot):
    img = Image.new('RGB', (w, h)); d = ImageDraw.Draw(img)
    for y in range(h): d.line([(0, y), (w, y)], fill=mix(top, bot, y / h))
    return img

def string_lights(img, y0, sag, step=110):
    w = img.width
    glow = Image.new('RGBA', img.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    d = ImageDraw.Draw(img, 'RGBA')
    import math
    pts = [(x, y0 + sag * math.sin(math.pi * x / w)) for x in range(0, w + 1, 20)]
    d.line(pts, fill=H_('5A4636'), width=4)
    for x in range(step // 2, w, step):
        y = y0 + sag * math.sin(math.pi * x / w) + 16
        circ(gd, (x, y), 40, (255, 190, 90, 150)); circ(d, (x, y), 11, (255, 236, 180))
    return Image.alpha_composite(img.convert('RGBA'), glow.filter(ImageFilter.GaussianBlur(14))).convert('RGB')

def banner():
    W, H = 2560, 1440
    img = gradient(W, H, WARM_T, WARM_B)
    d = ImageDraw.Draw(img)
    for y in range(930, H): d.line([(0, y), (W, y)], fill=shade(FLOOR, 1.05 - (y - 930) / 1400))
    for y in range(960, H, 46): d.line([(0, y), (W, y)], fill=shade(FLOOR, 0.82), width=3)
    d.rectangle((0, 906, W, 932), fill=H_('F4EFE6'))
    img = string_lights(img, 400, 70)
    # sağ taraf: bitmiş palet yatak + kedi (güvenli alan: x 507..2053, y 508..931)
    g = draw_pallet(img, 1830, 925, H_('7B4A2A'), w=300, legs=24, s=0.7)
    d = ImageDraw.Draw(img, 'RGBA')
    d.rounded_rectangle((g['x0'] + 6, g['t0'] - 24, g['x1'] - 4, g['t0'] + 8), radius=14, fill=H_('EFE3CF'))
    draw_pet_curl(img, CAT, 1850, g['t0'] - 18, 0.7, 0)
    draw_plant_pot(img, 2010, 928, s=0.55, pot=H_('C4693F'))
    # sol: Maya
    info = draw_maya(img, 600, 925, s=0.6, pose='mug', smile=1.0)
    hx, hy = info['hf']
    d = ImageDraw.Draw(img, 'RGBA')
    d.rounded_rectangle((hx - 3, hy - 19, hx + 21, hy + 9), radius=4, fill=H_('D0674A'))
    # yazılar
    d.text((1240, 640), "Maya Builds Cozy", font=font(112), fill=H_('3A2A22'), anchor='mm')
    f = font(46)
    left, right = "Junk", "cozy.  A new DIY build every day."
    wl, wr = d.textlength(left, font=f), d.textlength(right, font=f)
    total = wl + 90 + wr; x = 1240 - total / 2
    d.text((x, 752), left, font=f, fill=H_('7A4A2E'), anchor='lm')
    ax = x + wl + 22
    d.rectangle((ax, 748, ax + 32, 756), fill=H_('7A4A2E'))
    d.polygon([(ax + 28, 738), (ax + 48, 752), (ax + 28, 766)], fill=H_('7A4A2E'))
    d.text((x + wl + 90, 752), right, font=f, fill=H_('7A4A2E'), anchor='lm')
    d.rounded_rectangle((1040, 820, 1440, 884), radius=32, fill=H_('E2A628'))
    d.text((1240, 852), "BEFORE  /  AFTER", font=font(34), fill=H_('3A2A22'), anchor='mm')
    return img

def profile(size=800):
    img = gradient(size, size, H_('F8E2C4'), H_('E9B98A'))
    img = string_lights(img, 90, 30, step=130)
    d = ImageDraw.Draw(img, 'RGBA')
    circ(d, (size / 2, size * 0.47), size * 0.36, (255, 255, 255, 60))
    draw_maya(img, size * 0.46, size * 2.23, s=2.35 * size / 800, pose='stand', smile=1.0)
    return img

def watermark():
    img = profile(600)
    m = Image.new('L', img.size, 0); ImageDraw.Draw(m).ellipse((0, 0, 599, 599), fill=255)
    out = Image.new('RGBA', img.size, (0, 0, 0, 0)); out.paste(img, (0, 0), m)
    return out.resize((150, 150), Image.LANCZOS)

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    banner().save(os.path.join(OUT, 'banner.png'))
    profile().save(os.path.join(OUT, 'profile.png'))
    watermark().save(os.path.join(OUT, 'watermark.png'))
    print('branding/ hazır')
