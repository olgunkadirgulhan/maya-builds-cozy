"""Evolution of... Shorts (2026-11-07; Maya Builds Cozy kanalının yeni konsepti).
Trend taraması: "evolution of" son 30 gün Shorts medyanı 1.4M, 37 kanal 100K+.
Her video bir konu (telefonlar, arabalar, oyun konsolları...): 6 tarihli adım, her adımda yıl + kısa gerçek bilgi + bir sayı.
Konular Gemini'den gelir, İKİNCİ geçişte doğrulanır (şüpheli adım atılır) → state/evo_bank.json. Marka/model adı yok (genel tarih).
    python evolution.py --dry-run
    python evolution.py --auto
"""
import json, os, random, re, sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import ImageDraw
import shortkit as K

HERE = Path(__file__).resolve().parent
BANK = HERE / 'state' / 'evo_bank.json'
LOG = HERE / 'state' / 'evo_published.csv'
OUT = HERE / 'out' / 'evo'
DRY = '--dry-run' in sys.argv
INTRO, STEP, OUTRO = 1.6, 3.2, 3.0
COLS = [(255, 120, 80), (255, 170, 60), (250, 210, 70), (120, 200, 120), (80, 170, 230), (150, 120, 230), (230, 110, 170)]
BANNED = re.compile(r'\b(war|weapon|gun|bomb|kill|death|nazi|religio|politic|alcohol|cigarette|drug)\w*', re.I)


def load_bank():
    return json.loads(BANK.read_text(encoding='utf-8')) if BANK.exists() else []


def used():
    return {r['topic_id'].split(':', 1)[-1] for r in K.rows(LOG)}


def refill(min_unused=20, n=12):
    bank = load_bank(); u = used()
    if sum(t['id'] not in u for t in bank) >= min_unused or not os.environ.get('GEMINI_API_KEY'):
        return bank
    have = sorted(t['topic'] for t in bank)
    prompt = f"""Create {n} NEW "Evolution of ..." topics for a YouTube Shorts channel (family-friendly, everyday things and technology:
phones, cars, computers, cameras, game consoles, music players, bicycles, airplanes, light bulbs, TVs, sneakers, money, toothbrushes, etc.).
Each topic: 6 steps in chronological order. Each step: a year (or decade like 1980), a SHORT true fact (max 46 chars) about what changed,
and a short stat (max 14 chars, e.g. "1.1 kg", "4 MB", "30 km/h") that is accurate and commonly cited. No brand or product names,
no people names. Only well-established facts with round numbers. Skip topics already done: {json.dumps(have, ensure_ascii=False)}
Each topic gets ONE single emoji (no ZWJ). Return JSON list of
{{"topic": "Mobile Phones", "emoji": "📱", "steps": [{{"year": 1973, "fact": "...", "stat": "..."}}, ...]}}"""
    try:
        res = K.gemini_json(prompt)
    except SystemExit as e:
        print(e); return bank
    cand = []
    for t in res if isinstance(res, list) else []:
        try:
            steps = [dict(year=int(s['year']), fact=str(s['fact']).strip(), stat=str(s['stat']).strip()) for s in t['steps']]
            topic, em = str(t['topic']).strip().title()[:30], str(t['emoji']).strip()
        except Exception:  # noqa: BLE001
            continue
        if topic in have or len(steps) < 5 or not K.emoji_ok(em) or BANNED.search(topic + json.dumps(steps)): continue
        steps = sorted(steps, key=lambda s: s['year'])
        if any(not (3 <= len(s['fact']) <= 52 and 1 <= len(s['stat']) <= 16) for s in steps): continue
        cand.append(dict(topic=topic, emoji=em, steps=steps))
    if not cand: return bank
    flat = [dict(t=i, s=j, topic=c['topic'], year=s['year'], fact=s['fact'], stat=s['stat']) for i, c in enumerate(cand) for j, s in enumerate(c['steps'])]
    try:
        chk = K.gemini_json('You are a strict fact checker. For each item decide if the fact AND the stat are accurate for that '
                            'year and topic (rounded numbers are fine). If unsure, mark false. Items: '
                            + json.dumps(flat, ensure_ascii=False) + '\nReturn JSON list of {"t": int, "s": int, "ok": true|false}.', temp=0.0)
        ok = {(r['t'], r['s']) for r in chk if r.get('ok') is True}
    except SystemExit:
        return bank
    nid = max([int(t['id'][1:]) for t in bank] + [0])
    for i, c in enumerate(cand):
        c['steps'] = [s for j, s in enumerate(c['steps']) if (i, j) in ok][:6]
        if len(c['steps']) >= 5:
            nid += 1; bank.append(dict(id=f't{nid}', **c))
    BANK.parent.mkdir(parents=True, exist_ok=True)
    BANK.write_text(json.dumps(bank, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'banka: {len(bank)} konu', flush=True)
    return bank


def frame_fn(t):
    steps = t['steps']; n = len(steps); total = INTRO + n * STEP + OUTRO

    def f(T):
        img = K.gradient((25, 35, 70), (10, 15, 35), False).copy(); d = ImageDraw.Draw(img)
        K.text(d, (K.W / 2, 150), 'EVOLUTION OF', 70, fill=(255, 220, 60))
        K.text(d, (K.W / 2, 250), t['topic'].upper(), 96, max_w=K.W - 120)
        if T < INTRO:
            u = K.ease(T / 0.6)
            e = K.emoji_img(t['emoji'], int(420 * u) + 1); img.alpha_composite(e, (int(K.W / 2 - e.width / 2), int(950 - e.height / 2)))
            K.text(d, (K.W / 2, 1380), f"{steps[0]['year']} TO {steps[-1]['year']}", int(90 * u) + 1)
            return img
        if T >= INTRO + n * STEP:
            u = K.ease((T - INTRO - n * STEP) / 0.5)
            K.text(d, (K.W / 2, 800), 'WHAT SHOULD', int(100 * u) + 1)
            K.text(d, (K.W / 2, 930), 'EVOLVE NEXT?', int(110 * u) + 1, fill=(255, 220, 60))
            K.text(d, (K.W / 2, 1090), 'COMMENT BELOW', int(70 * u) + 1)
            return img
        i = int((T - INTRO) // STEP); lt = T - INTRO - i * STEP; s = steps[i]; pop = K.ease(lt / 0.4); col = COLS[i % len(COLS)]
        # zaman çizelgesi
        y = 1700; d.line([(110, y), (K.W - 110, y)], fill=(255, 255, 255, 90), width=8)
        for j in range(n):
            x = 110 + (K.W - 220) * j / (n - 1); r = 22 if j == i else 13
            d.ellipse([x - r, y - r, x + r, y + r], fill=(COLS[j % len(COLS)] if j <= i else (90, 95, 120)))
        K.text(d, (K.W / 2, 470), str(s['year']), int(200 * pop) + 1, fill=col)
        sc = 0.55 + 0.45 * (i + 1) / n   # emoji her adımda biraz büyür: ilerleme hissi
        e = K.emoji_img(t['emoji'], int(330 * sc * pop) + 1); img.alpha_composite(e, (int(K.W / 2 - e.width / 2), int(860 - e.height / 2)))
        d.rounded_rectangle([90, 1130, K.W - 90, 1560], radius=44, fill=(255, 255, 255, 235))
        K.text_block(d, K.W / 2, 1270, s['fact'].upper(), 66, K.W - 240, fill=(34, 24, 60), stroke=(255, 255, 255))
        K.text(d, (K.W / 2, 1450), s['stat'].upper(), 96, fill=col, stroke=(34, 24, 60))
        return img
    events = [(INTRO + i * STEP, 'new') for i in range(n)] + [(INTRO + n * STEP, 'end')]
    return f, total, events


TITLES = ['Evolution of {t} ({a}–{b}) {e}', 'The Evolution of {t} {e} {a} to {b}', 'How {t} Changed: {a} → {b} {e}',
          '{t}: {a} vs {b} (Full Evolution) {e}']


def main():
    a = sys.argv[1:]
    if '--auto' in a and K.today_count(LOG) >= int(os.environ.get('PER_DAY') or 2):
        print('bugünkü sayı doldu'); return
    bank = refill(); u = used(); pool = [t for t in bank if t['id'] not in u]
    if not pool: raise SystemExit('konu bankası boş (GEMINI_API_KEY?)')
    rnd = random.Random(); t = rnd.choice(pool)
    st = t['steps']; seen = {K.tkey(r['title']) for r in K.rows(LOG)}
    opts = [x.format(t=t['topic'], e=t['emoji'], a=st[0]['year'], b=st[-1]['year']) for x in TITLES]; rnd.shuffle(opts)
    title = next(o for o in opts if K.tkey(o) not in seen)
    desc = (f"The evolution of {t['topic'].lower()} from {st[0]['year']} to {st[-1]['year']}:\n\n"
            + '\n'.join(f"{s['year']}: {s['fact']} ({s['stat']})" for s in st)
            + '\n\nNumbers are rounded, commonly cited figures. What should evolve next? Comment below 👇\n\n'
            'Emoji: Noto Color Emoji by Google (SIL Open Font License).\n\n#shorts #evolution #history #technology #thenandnow')
    tags = ['evolution of', 'evolution', 'history', 'then and now', 'technology', t['topic'].lower(), 'shorts']
    f, total, events = frame_fn(t)
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
    print(f'[evo] {t["id"]} {title}', flush=True)
    mp4 = K.render(f, total, events, rnd.randrange(10 ** 6), OUT / f'evo_{stamp}.mp4')
    if DRY: print('  [dry-run]', mp4); return
    pa = K.publish_at(['16:00', '19:30'], K.today_count(LOG))
    vid = K.upload(mp4, title + ' #shorts', desc, tags, pa, category='27')
    K.record(LOG, 'evo:' + t['id'], vid, title, pa)
    print(f'  ✓ https://youtu.be/{vid} ({pa})')


if __name__ == '__main__':
    main()
