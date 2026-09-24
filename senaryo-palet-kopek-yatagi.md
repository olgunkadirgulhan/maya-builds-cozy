# Senaryo: 2 Eski Palet → Köpek Rüya Yatağı (Maya serisi)

**Kontrast:** gri, kaba palet → ceviz vernikli, LED'li, minderli, sıcak köşe
**Payoff:** Golden retriever yatağa atlar, kıvrılıp uyur, Maya arkada elinde kahveyle gülümser.
**Süre:** 28 sn, 9:16 · **Animasyon sürümü:** `output/maya_palet_kopek_yatagi.mp4` (`python make_video.py`)

| # | Vuruş | Zaman | Kamera | Aksiyon |
|---|---|---|---|---|
| 0 | HOOK | 0–2s | split | Üstte BEFORE (ham paletler), altta AFTER (köpek yatakta), yazı: "2 old pallets → dog's dream bed" |
| 1 | ANCHOR | 2–5s | statik geniş | Maya elinde gri paletle salona girer, yere bırakır (toz bulutu) |
| 2 | STAKES | 5–8s | statik geniş (aynı açı), hafif push-in | Yerde kirli palet, duvara yaslı ikinci palet; Maya düşünceli bakar |
| 3 | PROCESS | 8–11s | statik geniş | Diz çöküp zımparalar, palet grinden açık çam rengine döner |
| 4 | PROCESS | 11–12s | statik geniş | İkinci paleti sırtlık olarak arkaya taşır (jump-cut) |
| 5 | PROCESS | 12–14s | statik geniş | Sırtlığı çekiçle çakar |
| 6 | PROCESS | 14–17s | statik geniş | Matkapla kısa ayaklar takar, yatak yükselir |
| 7 | FINISH | 17–19.5s | yakın plan | Eldivenli el, ceviz renkli verniği fırçalar (yarısı ham, yarısı koyu) |
| 8 | FINISH | 19.5–22s | yakın plan | Alt kenara LED şerit bastırılır, ışıklar sırayla yanar |
| 9 | PAYOFF | 22–28s | yavaş dolly-in | Golden hour, halı, bitki, lamba; köpek gelir, atlar, kıvrılır, zzz + kalp; "Would you build this?" |

## Keyframe promptları (karakter referans görseli EKLİ, `[CHARACTER_BLOCK]` = MAYA bloğu)

```
SHOT 1: Vertical 9:16 photo, bright living-room corner, oak floor, cream wall, framed abstract art,
white window on right, [CHARACTER_BLOCK] walking in from left carrying a grey weathered wooden pallet,
static wide shot, eye level, soft morning window light, photorealistic, 35mm.

SHOT 2 (same camera position): same room, one dirty grey pallet on the floor, a second pallet leaning
against the wall, red toolbox and a can of wood stain in front, [CHARACTER_BLOCK] standing left, hand on chin.

SHOT 3: same corner, same angle, [CHARACTER_BLOCK] kneeling, sanding the pallet with an orange orbital
sander, fine wood dust in the sunbeam, half of the pallet already pale fresh pine.

SHOT 4: same corner, same angle, second sanded pallet now standing upright behind the first as a
headboard, [CHARACTER_BLOCK] hammering it in place from the right side.

SHOT 5: same corner, same angle, the bed frame raised on four short wooden legs,
[CHARACTER_BLOCK] kneeling with a cordless drill at the front leg.

SHOT 6: Extreme close-up top-down, gloved hand brushing dark walnut stain onto pale pine slats,
top slat already dark, middle slat half stained with a wet glossy edge, bottom slat raw, macro texture.

SHOT 7: Close-up under the bed edge in a dim room, gloved hand pressing a warm-white LED strip,
LEDs lighting up one by one, warm glow spilling onto dark floorboards.

SHOT 8 (REVEAL): same room at golden hour, walnut-stained pallet dog bed on short legs with LED glow
underneath, cream cushion, sage and terracotta pillows, round cream rug, trailing pothos in terracotta pot,
floor lamp, string lights; a golden retriever curled up asleep on the cushion;
[CHARACTER_BLOCK] holding a coffee mug, softly smiling in the soft-focus background. Pinterest interior, photorealistic.
```

**Negatif:** `no text, no watermark, no extra fingers, no morphing tools, no outfit change`

## Hareket promptları (image-to-video, ilk kare + son kare)

```
SHOT 1: She walks in from the left carrying the pallet, lowers it to the floor, small dust puff. Static camera.
SHOT 3: Sander moves back and forth, dust rises, grey wood turns pale. Static camera, slight speed-ramp.
SHOT 4: She lifts the second pallet upright and hammers it, quick jump cuts. Static camera.
SHOT 5: Drill spins, wood chips fly, bed rises on legs. Static camera.
SHOT 6: Brush slides slowly left to right, stain spreads and shines. Macro, very slow.
SHOT 7: LED strip lights up sequentially left to right, glow blooms. Slow.
SHOT 8: Slow cinematic dolly-in. Dog trots in from the right, hops onto the cushion, circles and curls up, sighs. Warm light flicker.
```

**SFX:** ayak sesi, palet düşme, zımpara, tahta tıkırtısı, çekiç, matkap, fırça, LED klik ve çınlama, pati sesi, köpek iç çekişi
**Müzik:** soft lo-fi (84 BPM, Fmaj7–Em7–Dm7–Cmaj7), reveal'da pad swell
**Caption:** `2 old pallets → my dog's new favorite spot 🐕 Would you build this?`
**Hashtag:** `#diy #palletbed #dogbed #palletproject #homedecor #aivideo #diyhomedecor #dogsoftiktok #budgetdiy #roommakeover`
