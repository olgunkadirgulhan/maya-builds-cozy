"""Maya Builds Cozy Shorts pipeline. Bir çalıştırma = bir video (VIDEOS_PER_RUN ile değişir).

    senaryo seç (şablon + mekân + renk + hayvan + müzik) -> render -> YouTube'a yükle -> kaydet

Env
  YT_PRIVACY      public | private | unlisted | off   (varsayılan: YT_* secrets varsa private, yoksa off)
  VIDEOS_PER_RUN  varsayılan 1
  MAX_PER_DAY     varsayılan 3 (UTC gün, published.csv'den sayılır)
  YT_CHANNEL_ID   token bu kanala ait olmalı
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN

Yerel test (yüklemesiz):  python run.py --no-upload
Yüklemesi başarısız olan senaryo queue/<id>.json'a yazılır, sonraki çalıştırmada aynen yeniden render edilip yüklenir.
"""
import argparse, csv, json, os, sys, traceback
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import generate  # noqa: E402

PUBLISHED = HERE / 'published.csv'
QUEUE = HERE / 'queue'
OUT = HERE / 'output'
FIELDS = ['id', 'date_utc', 'video_id', 'privacy', 'template', 'location', 'title']


def log(msg): print(f'[run] {msg}', flush=True)

def gh_annotation(level, msg):
    print(f'::{level}::{msg}' if os.environ.get('GITHUB_ACTIONS') else f'[run] {level.upper()}: {msg}', flush=True)

def published_rows():
    if not PUBLISHED.exists(): return []
    with PUBLISHED.open(newline='', encoding='utf-8') as f: return list(csv.DictReader(f))

def uploaded_today():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    return sum(1 for r in published_rows() if r['date_utc'].startswith(today))

def record(meta, video_id, privacy):
    new = not PUBLISHED.exists()
    with PUBLISHED.open('a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new: w.writeheader()
        w.writerow({'id': meta['id'], 'date_utc': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M'),
                    'video_id': video_id, 'privacy': privacy, 'template': meta['template'],
                    'location': meta['location'], 'title': meta['title']})

def enqueue(meta, error, qpath=None):
    """Kuyruktan gelen iş yine başarısız olursa aynı dosya güncellenir (kopya oluşmaz)."""
    QUEUE.mkdir(exist_ok=True)
    p = qpath or QUEUE / f"{meta['id']}.json"
    prev = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    sc = json.loads((Path(meta['dir']) / 'scenario.json').read_text(encoding='utf-8'))
    p.write_text(json.dumps({'scenario': sc, 'attempts': prev.get('attempts', 0) + 1,
                             'last_error': str(error)[:500]}, indent=2), encoding='utf-8')
    log(f"queued {meta['id']} for retry")

def privacy_mode(no_upload):
    import upload
    if no_upload: return 'off'
    if not upload.configured():
        gh_annotation('warning', 'YouTube secrets missing: render only. Run auth_setup.py to connect the channel.')
        return 'off'
    mode = (os.environ.get('YT_PRIVACY') or '').strip().lower()
    if mode not in ('public', 'private', 'unlisted', 'off'):
        mode = 'private' if upload.configured() else 'off'
    return mode

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-upload', action='store_true')
    args = ap.parse_args()
    import upload

    mode = privacy_mode(args.no_upload)
    per_run = int(os.environ.get('VIDEOS_PER_RUN') or 1)
    max_per_day = int(os.environ.get('MAX_PER_DAY') or 3)
    log(f'upload mode: {mode}')

    if mode != 'off':
        room = max_per_day - uploaded_today()
        if room <= 0:
            log(f'daily cap of {max_per_day} reached, nothing to do'); return
        per_run = min(per_run, room)
        try:
            log(f'channel check ok: {upload.check_channel()}')
        except Exception as e:
            gh_annotation('error', f'channel check failed, nothing uploaded: {e}'); raise SystemExit(1)

    locked = []
    if mode == 'public':
        recent = [r['video_id'] for r in published_rows() if r['privacy'] == 'public'][-10:]
        try:
            locked = upload.locked_videos(recent)
        except Exception as e:
            log(f'public check skipped: {e}')
        if locked:
            gh_annotation('error', 'YouTube made public uploads private (likely needs the API audit): '
                          + ', '.join(f'{v} ({why})' for v, why in locked))

    hist = generate.load(generate.HIST, [])
    QUEUE.mkdir(exist_ok=True)
    jobs = [(p, json.loads(p.read_text(encoding='utf-8'))['scenario']) for p in sorted(QUEUE.glob('*.json'))][:per_run]
    jobs += [(None, None)] * (per_run - len(jobs))

    failed = False
    for qpath, sc in jobs:
        try:
            meta = generate.make(OUT, hist, sc=sc)
        except Exception as e:
            traceback.print_exc(); gh_annotation('error', f'render failed: {e}'); failed = True; continue
        log(f"rendered {meta['id']} | {meta['title']}")
        if mode == 'off':
            log('upload skipped (mode off)'); continue
        try:
            vid = upload.upload(Path(meta['dir']) / 'video.mp4', meta['title'], meta['description'], meta['yt_tags'], mode)
        except upload.QuotaError as e:
            enqueue(meta, e, qpath); gh_annotation('warning', 'YouTube quota reached, video queued for the next run.'); break
        except Exception as e:
            traceback.print_exc(); enqueue(meta, e, qpath); gh_annotation('error', f"upload failed for {meta['id']}: {e}")
            failed = True; continue
        record(meta, vid, mode)
        if qpath: qpath.unlink(missing_ok=True)
        log(f'uploaded https://youtube.com/shorts/{vid} ({mode})')

    sys.exit(1 if failed or locked else 0)


if __name__ == '__main__':
    main()
