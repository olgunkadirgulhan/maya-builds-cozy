"""Kanal kurulumu (tekrar çalıştırılabilir): açıklama, anahtar kelimeler, banner, filigran, fragman,
oynatma listeleri, ana sayfa bölümleri. Aynı onayla yeni (tam yetkili) token'ı GitHub Secrets'a yazar.

    python branding.py                                   # görseller
    python channel_setup.py --repo <kullanıcı>/<repo>    # tarayıcıda Maya Builds Cozy'yi seç

Profil fotoğrafı API ile değiştirilemez: branding/profile.png'yi YouTube Studio > Customization > Branding'den yükle.
"""
import argparse, csv, json, subprocess, sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from upload import SCOPES  # noqa: E402

PLAYLISTS_FILE = HERE / 'playlists.json'
BRAND = HERE / 'branding'

DESCRIPTION = """Junk → cozy, one build at a time.

Maya turns old pallets, cinder blocks, tires, crates, ladders and buckets into cozy, Pinterest-worthy pieces, and there is always a dog or cat waiting to claim the finished build.

A new before & after DIY Short every day:
🪵 Pallet pet beds
🧱 Cinder block benches
🛞 Rope tire ottomans
📦 Crate bookshelves
🪜 Ladder plant shelves
🪴 Concrete planters

Budget materials, satisfying ASMR build sounds and cozy reveals, in the living room, backyard, balcony and garage.

Subscribe and tell Maya what to build next in the comments 👇

Animated DIY inspiration. When you build your own, follow tool safety and product instructions."""

KEYWORDS = ('DIY "before and after" "DIY home decor" "budget DIY" upcycling "pallet projects" "cinder block" '
            '"DIY furniture" "room makeover" "cozy home" "balcony ideas" "backyard ideas" "garage makeover" '
            '"pet bed" "cat bed" "dog bed" "concrete planters" "satisfying" "home decor ideas" "Maya Builds Cozy"')

PLAYLISTS = {
    'pallet_bed': ('Pallet Pet Beds', 'Old pallets turned into cozy dog and cat beds, from raw wood to the first nap.'),
    'block_bench': ('Cinder Block Builds', 'Grey cinder blocks turned into benches with succulents in every hole.'),
    'crate_shelf': ('Crate Shelves', 'Old wooden crates stacked, stained and lit up into cozy bookshelves.'),
    'tire_ottoman': ('Tire & Rope Upcycles', 'Junk tires wrapped in rope and topped with wood: cozy ottomans and poufs.'),
    'ladder_shelf': ('Ladder Plant Shelves', 'Dusty old ladders turned into glowing plant and book shelves.'),
    'concrete_planters': ('Concrete Planters', 'Old buckets as molds, a bag of concrete, and designer planters.'),
    'loc_living': ('Cozy Living Room Builds', 'Every build that ends up in the living room.'),
    'loc_garden': ('Backyard Builds', 'Backyard and patio makeovers, sunset included.'),
    'loc_balcony': ('Balcony Makeovers', 'Small balcony, big cozy: city-view builds.'),
    'loc_garage': ('Garage Projects', 'Builds straight out of the garage workshop.'),
}
SECTIONS = ['pallet_bed', 'block_bench', 'tire_ottoman', 'crate_shelf', 'ladder_shelf', 'concrete_planters']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', help='yeni token GitHub Secrets’a yazılsın (owner/name)')
    a = ap.parse_args()

    flow = InstalledAppFlow.from_client_secrets_file(str(HERE / 'client_secret.json'), SCOPES)
    creds = flow.run_local_server(port=0, prompt='consent select_account', access_type='offline')
    yt = build('youtube', 'v3', credentials=creds, cache_discovery=False)
    ch = yt.channels().list(part='id,snippet', mine=True).execute()['items'][0]
    cid, title = ch['id'], ch['snippet']['title']
    print(f'kanal: {title} ({cid})')
    if 'maya builds cozy' not in title.lower():
        sys.exit('Bu Maya Builds Cozy değil; hiçbir şey değiştirilmedi. Tekrar çalıştır ve doğru kanalı seç.')

    if a.repo:
        for k, v in {'YT_REFRESH_TOKEN': creds.refresh_token, 'YT_CLIENT_ID': creds.client_id,
                     'YT_CLIENT_SECRET': creds.client_secret, 'YT_CHANNEL_ID': cid}.items():
            subprocess.run(['gh', 'secret', 'set', k, '--repo', a.repo], input=v, text=True, check=True)
        print('GitHub secrets güncellendi (tam yetkili token)')

    banner = yt.channelBanners().insert(media_body=MediaFileUpload(str(BRAND / 'banner.png'), mimetype='image/png')).execute()
    published = list(csv.DictReader((HERE / 'published.csv').open(encoding='utf-8'))) if (HERE / 'published.csv').exists() else []
    channel = {'title': title, 'description': DESCRIPTION, 'keywords': KEYWORDS, 'country': 'US', 'defaultLanguage': 'en'}
    if published:
        channel['unsubscribedTrailer'] = published[0]['video_id']
    yt.channels().update(part='brandingSettings', body={'id': cid, 'brandingSettings': {
        'channel': channel, 'image': {'bannerExternalUrl': banner['url']}}}).execute()
    print('açıklama, anahtar kelimeler, ülke/dil, banner' + (', fragman' if published else '') + ' ayarlandı')

    try:
        yt.watermarks().set(channelId=cid, body={'timing': {'type': 'offsetFromStart', 'offsetMs': 0}, 'position': {
            'type': 'corner', 'cornerPosition': 'topRight'}},
            media_body=MediaFileUpload(str(BRAND / 'watermark.png'), mimetype='image/png')).execute()
        print('filigran (abone ol düğmesi) ayarlandı')
    except Exception as e:
        print(f'filigran atlandı: {str(e)[:160]}')

    existing = {p['snippet']['title']: p['id'] for p in
                yt.playlists().list(part='snippet', mine=True, maxResults=50).execute().get('items', [])}
    ids = json.loads(PLAYLISTS_FILE.read_text(encoding='utf-8')) if PLAYLISTS_FILE.exists() else {}
    for key, (ptitle, pdesc) in PLAYLISTS.items():
        if key in ids: continue
        if ptitle in existing:
            ids[key] = existing[ptitle]; continue
        p = yt.playlists().insert(part='snippet,status', body={
            'snippet': {'title': ptitle, 'description': pdesc + '\n\nSubscribe to Maya Builds Cozy for a new build every day.',
                        'defaultLanguage': 'en'},
            'status': {'privacyStatus': 'public'}}).execute()
        ids[key] = p['id']; print(f'oynatma listesi: {ptitle}')
    PLAYLISTS_FILE.write_text(json.dumps(ids, indent=2) + '\n', encoding='utf-8')

    for row in published:  # daha önce yüklenenleri de listelere ekle
        for key in (row['template'], 'loc_' + row['location']):
            try:
                yt.playlistItems().insert(part='snippet', body={'snippet': {'playlistId': ids[key], 'resourceId': {
                    'kind': 'youtube#video', 'videoId': row['video_id']}}}).execute()
            except Exception as e:
                print(f"liste ekleme atlandı ({key}): {str(e)[:120]}")

    have = yt.channelSections().list(part='snippet,contentDetails', mine=True).execute().get('items', [])
    have = {(s['snippet']['type'], tuple(s.get('contentDetails', {}).get('playlists', []))) for s in have}
    wanted = [('recentUploads', ()), ('popularUploads', ())] + [('singlePlaylist', (ids[k],)) for k in SECTIONS]
    for pos, (stype, pls) in enumerate(wanted):
        if (stype, pls) in have: continue
        body = {'snippet': {'type': stype, 'position': pos}}
        if pls: body['contentDetails'] = {'playlists': list(pls)}
        try:
            yt.channelSections().insert(part='snippet,contentDetails', body=body).execute()
            print(f'ana sayfa bölümü: {stype} {pls}')
        except Exception as e:
            print(f'ana sayfa bölümü atlandı ({stype}): {str(e)[:120]}')
    print('\nProfil fotoğrafı: branding/profile.png -> YouTube Studio > Customization > Branding > Picture')


if __name__ == '__main__':
    main()
