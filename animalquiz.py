"""Guess the Animal by its Shadow (2026-11-11; Evolution Of Everythingg kanalının yeni konsepti — evolution medyanı 54).
Kaynak fikir: aynı hafta Marble'daki "tahmin et" formatı 57 → 6.9K medyana çıktı; burada konu ve görünüm farklı (kanallar benzemesin):
gün batımı zemini, siyah gölge, 2x2 şık, cevapta renkli hayvan. 6 tur, kolay → zor. Görseller: Noto Color Emoji (SIL OFL).
    python animalquiz.py --dry-run | --auto
"""
import os, random, sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw
import shortkit as K

HERE = Path(__file__).resolve().parent
LOG = HERE / 'state' / 'animal_published.csv'
OUT = HERE / 'out' / 'animal'
DRY = '--dry-run' in sys.argv
N_Q, THINK, SHOW = 6, 3.0, 1.8
INTRO, OUTRO = 1.4, 3.0
SUN, GREEN, DARK = (255, 196, 70), (70, 200, 110), (25, 16, 40)
# seviye: 1 belirgin gölge → 3 zor; tek kod noktalı emoji (ZWJ yok)
TIERS = {
    1: {'🐘': 'Elephant', '🦒': 'Giraffe', '🦘': 'Kangaroo', '🐪': 'Camel', '🐧': 'Penguin', '🦀': 'Crab', '🐢': 'Turtle',
        '🐙': 'Octopus', '🦋': 'Butterfly', '🐌': 'Snail', '🦕': 'Dinosaur', '🐇': 'Rabbit', '🦈': 'Shark', '🐓': 'Rooster'},
    2: {'🦏': 'Rhino', '🦛': 'Hippo', '🐊': 'Crocodile', '🦩': 'Flamingo', '🦉': 'Owl', '🦇': 'Bat', '🦞': 'Lobster',
        '🐿': 'Squirrel', '🦌': 'Deer', '🐐': 'Goat', '🦢': 'Swan', '🦜': 'Parrot', '🐬': 'Dolphin', '🦂': 'Scorpion', '🐫': 'Bactrian Camel'},
    3: {'🦥': 'Sloth', '🦦': 'Otter', '🦨': 'Skunk', '🦡': 'Badger', '🦔': 'Hedgehog', '🦙': 'Llama', '🦚': 'Peacock', '🦤': 'Dodo',
        '🦭': 'Seal', '🦫': 'Beaver', '🦬': 'Bison', '🦣': 'Mammoth', '🐡': 'Pufferfish', '🦑': 'Squid', '🦎': 'Lizard'},
}
LEVEL = [1, 1, 2, 2, 3, 3]


def shadow(ch, size):
    e = K.emoji_img(ch, size); a = e.split()[3]
    s = Image.new('RGBA', e.size, DARK + (255,)); s.putalpha(a); return e, s


def make_quiz(rnd, recent):
    qs, used = [], set()
    for lv in LEVEL:
        pool = [c for c in TIERS[lv] if c not in used and c not in recent and K.emoji_ok(c)] or [c for c in TIERS[lv] if c not in used]
        c = rnd.choice(pool); used.add(c)
        wrong = [n for t in TIERS.values() for k, n in t.items() if k != c and n != TIERS[lv][c]]
        wrong = [n for n in wrong if n.split()[-1] != TIERS[lv][c].split()[-1]]   # "Camel" ile "Bactrian Camel" aynı turda olmasın
        opts = rnd.sample(wrong, 3) + [TIERS[lv][c]]; rnd.shuffle(opts)
        qs.append(dict(emoji=c, name=TIERS[lv][c], opts=opts, level=lv))
    return qs


def frame_fn(p):
    qs = p['qs']; seg = THINK + SHOW; total = INTRO + N_Q * seg + OUTRO
    bg = K.gradient((250, 140, 70), (70, 30, 110), False)

    def f(T):
        img = bg.copy(); d = ImageDraw.Draw(img)
        d.ellipse([K.W / 2 - 330, 420, K.W / 2 + 330, 1080], fill=SUN + (255,))
        if T < INTRO:
            u = K.ease(T / 0.5)
            K.text(d, (K.W / 2, 1250), 'GUESS THE ANIMAL', int(110 * u) + 1, max_w=K.W - 80)
            K.text(d, (K.W / 2, 1390), 'BY ITS SHADOW', int(90 * u) + 1, fill=SUN)
            K.text(d, (K.W / 2, 1520), f"6 ROUNDS · #{p['n']}", int(64 * u) + 1)
            return img
        if T >= INTRO + N_Q * seg:
            u = K.ease((T - INTRO - N_Q * seg) / 0.5)
            K.text(d, (K.W / 2, 1250), 'HOW MANY DID', int(100 * u) + 1)
            K.text(d, (K.W / 2, 1380), 'YOU GET?', int(110 * u) + 1, fill=SUN)
            K.text(d, (K.W / 2, 1520), 'COMMENT YOUR SCORE', int(70 * u) + 1)
            return img
        i = int((T - INTRO) // seg); lt = T - INTRO - i * seg; q = qs[i]; show = lt >= THINK
        K.text(d, (K.W / 2, 150), f'ROUND {i + 1}/{N_Q}', 64)
        K.text(d, (K.W / 2, 240), ('EASY', 'MEDIUM', 'HARD')[q['level'] - 1], 54, fill=SUN)
        pop = K.ease(lt / 0.35); col, sh = shadow(q['emoji'], 460)
        im = col if show else sh
        if show and lt - THINK < 0.4:   # gölgeden renge yumuşak geçiş
            im = Image.blend(sh, col, (lt - THINK) / 0.4)
        sz = int(460 * (0.85 + 0.15 * pop)); im = im.resize((max(1, int(im.width * sz / 460)), max(1, int(im.height * sz / 460))))
        img.alpha_composite(im, (int(K.W / 2 - im.width / 2), int(750 - im.height / 2)))
        for j, o in enumerate(q['opts']):
            x0 = 70 + (j % 2) * (K.W - 140) // 2 + 10; y0 = 1180 + (j // 2) * 230
            ok = show and o == q['name']
            d.rounded_rectangle([x0, y0, x0 + (K.W - 140) // 2 - 20, y0 + 200], radius=36,
                                fill=(GREEN if ok else (255, 255, 255) if not show else (150, 140, 160)) + (255,))
            K.text(d, (x0 + (K.W - 140) // 4 - 10, y0 + 100), o.upper(), 58, fill=(255, 255, 255) if ok else DARK,
                   stroke=DARK if ok else (255, 255, 255), max_w=(K.W - 140) // 2 - 70)
        if not show:
            frac = max(0.0, 1 - lt / THINK)
            d.rounded_rectangle([90, 1700, K.W - 90, 1746], radius=23, fill=(255, 255, 255, 110))
            d.rounded_rectangle([90, 1700, 90 + max(46, (K.W - 180) * frac), 1746], radius=23, fill=SUN)
        return img
    events = [(INTRO + i * seg, 'new') for i in range(N_Q)] + [(INTRO + i * seg + s, 'tick') for i in range(N_Q) for s in (1, 2)]
    events += [(INTRO + i * seg + THINK, 'ding') for i in range(N_Q)] + [(INTRO + N_Q * seg, 'end')]
    return f, total, events


HOOK = ['Guess the Animal by Its Shadow', 'Can You Name These 6 Animal Shadows?', 'Shadow Quiz: Which Animal Is This?',
        'Only Animal Experts Get All 6', 'Name the Animal From Its Silhouette', 'Animal Shadow Challenge', 'Guess the Animal in 3 Seconds',
        'Which Animal Casts This Shadow?']
TAIL = ['🐾', '🦒', '(Easy → Hard)', '| Animal Quiz', '🌅', '— 6 Rounds']


def main():
    a = sys.argv[1:]
    if '--auto' in a and K.today_count(LOG) >= int(os.environ.get('PER_DAY') or 3):
        print('bugünkü sayı doldu'); return
    rows = K.rows(LOG); n = len(rows) + 1; rnd = random.Random()
    recent = {c for r in rows[-4:] for c in r['topic_id'].split(':', 1)[-1].split('|')}
    qs = make_quiz(rnd, recent); tid = 'an:' + '|'.join(q['emoji'] for q in qs)
    seen = {K.tkey(r['title']) for r in rows}
    opts = [f'{h} {t} #{n}' for h in HOOK for t in TAIL]; rnd.shuffle(opts)
    title = next((o for o in opts if K.tkey(o) not in seen), opts[0])
    desc = ('Guess the animal from its shadow before the answer appears! 6 rounds, easy to hard.\n\n'
            + '\n'.join(f"{i + 1}. {q['name']}" for i, q in enumerate(qs))
            + '\n\nComment your score! New quiz every day 👇\n\nImages: Noto Color Emoji by Google (SIL Open Font License).\n\n'
            '#shorts #quiz #animals #guesstheanimal #animalquiz')
    tags = ['guess the animal', 'animal quiz', 'shadow quiz', 'animals', 'quiz', 'brain test', 'shorts']
    p = dict(qs=qs, n=n, seed=rnd.randrange(10 ** 6)); f, total, events = frame_fn(p)
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
    print(f'[animal] #{n} {title} | {[q["name"] for q in qs]}', flush=True)
    mp4 = K.render(f, total, events, p['seed'], OUT / f'an_{stamp}.mp4')
    if DRY: print('  [dry-run]', mp4); return
    pa = K.publish_at(['15:30', '18:30', '21:00'], K.today_count(LOG))
    vid = K.upload(mp4, title + ' #shorts', desc, tags, pa, category='27')
    K.record(LOG, tid, vid, title, pa)
    print(f'  ✓ https://youtu.be/{vid} ({pa})')


if __name__ == '__main__':
    main()
