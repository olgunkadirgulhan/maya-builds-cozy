"""
Senaryo seçici + render. Her video: şablon + mekân + renk + evcil hayvan + müzik + metin rastgele,
history.json'daki kombinasyonlar tekrar edilmez; art arda aynı şablon ya da aynı mekân gelmez.

  python generate.py                       -> 1 video (output/<id>/)
  python generate.py --count 3             -> 3 farklı video
  python generate.py --template block_bench --location garden --seed 42
  python generate.py --preview 1,9,20,27   -> sadece önizleme PNG'leri
"""
import argparse, csv, datetime, json, os, random, re
from engine import Video, PALETTES, H_
from projects import TEMPLATES

HERE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(HERE, 'history.json')
CONFIG = os.path.join(HERE, 'config.json')

PETS = {
    'dog': [dict(name='golden', col='D9A35B', dark='B7813F', light='F0CD92'),
            dict(name='chocolate', col='8B5A3C', dark='6A4029', light='B98A68'),
            dict(name='black', col='3B3532', dark='241F1D', light='6A605A'),
            dict(name='cream', col='EFDCC0', dark='D2B893', light='FFF3E0'),
            dict(name='grey', col='9C9A98', dark='7A7876', light='C8C6C4')],
    'cat': [dict(name='orange tabby', col='E39A4B', dark='C47A2E', light='F6D2A6', stripes=True),
            dict(name='grey tabby', col='9A9FA6', dark='777C83', light='D5D8DC', stripes=True),
            dict(name='black', col='3A3636', dark='242121', light='5A5454'),
            dict(name='white', col='F4F1EC', dark='D9D3CA', light='FFFFFF')],
}
FINISHES = [('walnut', '7B4A2A'), ('honey oak', 'B7793F'), ('espresso', '4E3226'), ('charcoal', '4A4440'), ('teak', '9A5B32')]
PAINTS = [('terracotta', 'C8704F'), ('sage', '8FA58A'), ('charcoal', '4B4E52'), ('dusty blue', '7F9BB0'),
          ('blush', 'D9A5A0'), ('cream', 'E9E2D3'), ('mustard', 'D4A537')]
ROPES = [('jute', 'C9A97A'), ('cotton', 'EDE6D6'), ('sage cotton', 'A9B8A0'), ('terracotta', 'C07A5A')]
BUCKET_COLS = ['E8833A', 'EDEDED', '3F6FB5', 'D94A3D']
CUSHIONS = ['EFE3CF', 'E5D3B3', '9DB08C', 'C98B6B', 'D9A441', 'D8A7A0', '3F4E6B', 'F4EBDB']
LEDS = [(255, 200, 110), (255, 170, 70), (255, 140, 170), (225, 235, 255)]
RUGS = ['EFE5D3', 'E3D2B5', 'C9D2BD', 'EBD3C9', 'D8DDE3']
POTS = ['C4693F', 'E8DFCF', '3F3A36', 'B98A68']
MUGS = ['D0674A', '3F4E6B', 'F4EBDB', '7F9A7A']
PROGS = [[[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]],
         [[50, 53, 57, 60], [55, 59, 62, 65], [48, 52, 55, 59], [57, 60, 64, 67]],
         [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 65]],
         [[52, 55, 59, 62], [57, 60, 64, 67], [50, 53, 57, 60], [55, 59, 62, 65]]]
CTAS = ["Would you build this?", "Rate this build 1-10", "Worth the weekend?", "Tag someone who'd build this",
        "Before or after?", "Which step was your favorite?", "Should I build this next?"]
BASE_TAGS = ['#homedecor', '#diyproject', '#budgetdiy', '#roommakeover', '#upcycling', '#diyhomedecor',
             '#satisfying', '#homeproject', '#cozyhome']
PET_TAGS = {'dog': ['#dogsofyoutube', '#doglover', '#dogbed'], 'cat': ['#catsofyoutube', '#catlover', '#catbed']}
LOC = {  # mekân -> (açıklamadaki ad, hashtag havuzu)
    'living': ('living room', ['#livingroomdecor', '#cozycorner', '#interiordesign']),
    'garden': ('backyard', ['#backyardideas', '#gardenideas', '#patiodecor']),
    'balcony': ('balcony', ['#balconyideas', '#smallbalcony', '#balconygarden']),
    'garage': ('garage', ['#garagemakeover', '#workshop', '#garageideas']),
}


def load(p, default):
    try:
        with open(p, encoding='utf-8-sig') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_hist(hist):
    with open(HIST, 'w', encoding='utf-8') as f: json.dump(hist, f, ensure_ascii=False, indent=2)

WEIGHTS = {'tire_ottoman': 6.0, 'ladder_shelf': 3.0, 'pallet_bed': 1.5}

def pick_template(rng, hist, forced=None):
    if forced: return forced
    keys = list(TEMPLATES)
    # 2026-10-10: tam sıra yerine ağırlıklı; en çok izlenenler (lastik ~1.000+, merdiven ~1.000) daha sık gelir,
    # son 3 videonun şablonu yine gelmez (çeşitlilik)
    recent = [h['template'] for h in hist[-3:]]
    pool = [k for k in keys if k not in recent] or keys
    return rng.choices(pool, weights=[WEIGHTS.get(k, 1.0) for k in pool])[0]

def pick_location(rng, T, hist, forced=None):
    if forced: return forced
    last = [h.get('location') for h in hist[-2:]]
    return rng.choice([l for l in T.locations if l not in last] or T.locations)

def build(rng, seed, template, cfg, hist, location=None):
    T = TEMPLATES[template]
    used = {h['combo'] for h in hist}
    last_pet = hist[-1].get('pet') if hist else None
    for _ in range(80):
        kinds = [k for k in T.pets if k != last_pet] or T.pets
        pet_kind = rng.choice(kinds)
        pet = dict(rng.choice(PETS[pet_kind]), kind=pet_kind)
        finish, paint, rope = rng.choice(FINISHES), rng.choice(PAINTS), rng.choice(ROPES)
        palette = rng.choice(list(PALETTES))
        loc = pick_location(rng, T, hist, location)
        extra = {'block_bench': paint[0], 'concrete_planters': paint[0], 'tire_ottoman': rope[0]}.get(template, '-')
        combo = f"{template}|{loc}|{pet_kind}:{pet['name']}|{finish[0]}|{extra}|{palette}"
        if combo not in used: break
    for k in ('col', 'dark', 'light'): pet[k] = H_(pet[k])
    cush = rng.sample(CUSHIONS, 3)
    sc = dict(seed=seed, template=template, combo=combo, location=loc, palette=palette, pet=pet, finish=finish,
              paint=paint, rope=rope, bucket=rng.choice(BUCKET_COLS), cushion=cush[0], pillows=cush[1:],
              led=rng.choice(LEDS), rug=rng.choice(RUGS), pot=rng.choice(POTS), mug=rng.choice(MUGS),
              string_lights=rng.random() < 0.7, handle=cfg.get('handle', '@mayabuildscozy'),
              music=dict(prog=rng.choice(PROGS), tempo=rng.randint(76, 92), transpose=rng.randint(-2, 2)),
              cta=rng.choice(CTAS))
    loc_name, loc_tags = LOC[loc]
    fill = dict(pet=pet_kind, Pet=pet_kind.capitalize(), paint=paint[0], Paint=paint[0].title(),
                Place=loc_name.title(), Finish=finish[0].title(), Rope=rope[0].title())
    sc['hook_text'] = rng.choice(T.HOOKS).format(**fill)
    # Yapı çeşitliliği (para kazanma: "aynı durum, aynı sonuç" şablon sinyali olmasın):
    # 3 farklı açılış, bitişlerin bir kısmında evcil hayvan yok (önce/sonra karşılaştırması)
    last = hist[-1] if hist else {}
    sc['hook_style'] = rng.choice([h for h in ('split', 'guess', 'budget') if h != last.get('hook_style')])
    sc['payoff_style'] = 'reveal' if (last.get('payoff_style') == 'pet' and rng.random() < 0.6) else \
        ('pet' if last.get('payoff_style') == 'reveal' else rng.choice(['pet', 'reveal']))
    with_pet = sc['payoff_style'] == 'pet'
    # Kanalda kullanılmış başlık tekrar edilmez (history + published.csv; kuyruktan tekrar yükleme dahil)
    used_titles = {h.get('title') for h in hist}
    pub = os.path.join(HERE, 'published.csv')
    if os.path.exists(pub):
        with open(pub, newline='', encoding='utf-8') as f: used_titles |= {r.get('title') for r in csv.DictReader(f)}
    def third_person(t):  # çizim karakter: "I built" yerine "Maya built"
        t = re.sub(r"\bI (Turned|Built|Made|Used)\b", r"Maya \1", t)
        return re.sub(r"\bMy\b", "Maya's", t)
    pool = [t for t in T.TITLES if with_pet or '{Pet}' not in t and '{pet}' not in t] or T.TITLES
    titles = [f"{third_person(t.format(**fill))} #diy #shorts"[:100] for t in pool]
    title = rng.choice([t for t in titles if t not in used_titles] or titles)
    tags = ['#shorts', '#diy', '#beforeandafter'] + rng.sample(T.TAGS, 3) + rng.sample(loc_tags, 2) + \
           (rng.sample(PET_TAGS[pet_kind], 1) if with_pet else []) + rng.sample(BASE_TAGS, 3)
    sc['title'] = title
    sc['hashtags'] = tags
    sc['description'] = "\n".join([
        sc['hook_text'] + f" ({loc_name} edition).",
        T.PAYOFF.format(**fill) if with_pet else f"Same {loc_name}, completely new corner.",
        "",
        f"Finish: {finish[0]}" + (f" · Paint: {paint[0]}" if extra == paint[0] else "") +
        (f" · Rope: {rope[0]}" if template == 'tire_ottoman' else "") + (f" · Resident: {pet['name']} {pet_kind}" if with_pet else ""),
        "",
        sc['cta'] + " 👇",
        "New cozy build every day. Subscribe to Maya Builds Cozy!",
        "",
        " ".join(tags),
    ])
    sc['yt_tags'] = list(dict.fromkeys([t.lstrip('#') for t in tags] +
                                       ['home decor', 'before and after', 'maya builds cozy', loc_name]))
    return sc

def restore(sc):
    """JSON'dan gelen senaryodaki renk listelerini PIL'in beklediği tuple'lara çevirir."""
    sc = dict(sc)
    sc['pet'] = dict(sc['pet'], **{k: tuple(sc['pet'][k]) for k in ('col', 'dark', 'light')})
    sc['led'] = tuple(sc['led'])
    return sc

def make(out_root, hist, seed=None, template=None, location=None, record=True, sc=None):
    """Bir video üretir; meta sözlüğünü döndürür (meta['dir'] = klasör). sc verilirse o senaryo aynen render edilir."""
    if sc is None:
        cfg = load(CONFIG, {})
        seed = seed if seed is not None else random.SystemRandom().randint(1, 10 ** 9)
        rng = random.Random(seed)
        template = pick_template(rng, hist, template)
        sc = build(rng, seed, template, cfg, hist, location)
    else:
        sc, record = restore(sc), False
        seed, template = sc['seed'], sc['template']
    vid = f"{datetime.datetime.now(datetime.timezone.utc):%Y%m%d-%H%M}-{template}-{seed % 100000:05d}"
    od = os.path.join(out_root, vid); os.makedirs(od, exist_ok=True)
    with open(os.path.join(od, 'scenario.json'), 'w', encoding='utf-8') as f: json.dump(sc, f, ensure_ascii=False)
    mp4, wav = os.path.join(od, 'video.mp4'), os.path.join(od, 'audio.wav')
    Video(sc, TEMPLATES[template](sc)).render(mp4, wav)
    os.remove(wav)
    meta = {k: sc[k] for k in ('title', 'description', 'yt_tags', 'hashtags', 'hook_text', 'cta', 'template',
                               'location', 'seed', 'combo')}
    meta.update(id=vid, dir=od, pet=sc['pet']['kind'])
    with open(os.path.join(od, 'meta.json'), 'w', encoding='utf-8') as f: json.dump(meta, f, ensure_ascii=False, indent=2)
    if record:
        hist.append(dict(id=vid, template=template, location=sc['location'], pet=sc['pet']['kind'], combo=sc['combo'],
                         title=sc['title'], hook_style=sc.get('hook_style'), payoff_style=sc.get('payoff_style'), date=f"{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d}"))
        save_hist(hist)
    return meta

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--count', type=int, default=1)
    ap.add_argument('--out', default=os.path.join(HERE, 'output'))
    ap.add_argument('--template', choices=list(TEMPLATES))
    ap.add_argument('--location', choices=['living', 'garden', 'balcony', 'garage'])
    ap.add_argument('--seed', type=int)
    ap.add_argument('--preview', help='virgülle saniyeler; video yerine PNG')
    a = ap.parse_args()
    hist = load(HIST, [])
    for i in range(a.count):
        seed = a.seed + i if a.seed is not None else None
        if a.preview:
            cfg = load(CONFIG, {})
            s = seed if seed is not None else random.SystemRandom().randint(1, 10 ** 9)
            rng = random.Random(s)
            t = pick_template(rng, hist, a.template)
            sc = build(rng, s, t, cfg, hist, a.location)
            od = os.path.join(a.out, f"{t}-{sc['location']}-{s % 100000:05d}"); os.makedirs(od, exist_ok=True)
            v = Video(sc, TEMPLATES[t](sc))
            for x in a.preview.split(','):
                v.frame(float(x)).save(os.path.join(od, f"f_{x}.png"))
            print(od); continue
        meta = make(a.out, hist, seed, a.template, a.location)
        print('OK', meta['dir'], '|', meta['title'])

if __name__ == '__main__':
    main()
