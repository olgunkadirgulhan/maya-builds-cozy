# AI DIY Dönüşüm Videosu Üretici — @inna_frame Formatı

> Amaç: @inna_frame tarzı **sessiz, AI ile üretilmiş "ham malzeme → şık sonuç" DIY dönüşüm videoları** için senaryo üretmek ve videoyu uçtan uca yapmak.
> Bu dosya hem **LLM'e verilecek sistem promptu** hem de **üretim el kitabı** olarak kullanılabilir.

---

## 0. Format Analizi (referans hesaptan çıkarılanlar)

| Unsur | Gözlem |
|---|---|
| Niş | AI ile "space transformation" + DIY: palet, briket (cinder block), beton döküm, dal, ahşap |
| Karakter | Her videoda aynı kadın karakter, **iş kıyafeti/tulum + baret estetiği** ("👷‍♀️ Dream it. Frame it. Build it.") — sabit görsel çapa |
| Ses | Konuşma yok. ASMR işçilik sesleri + trend/lo-fi müzik |
| Yapı | **4 vuruş:** Çapa (karakter mekâna girer) → Ham malzeme/yarım iş → Metodik yapım → Kullanımda/stilize reveal |
| Kamera | Yapım = **sabit geniş plan (aynı açı)**, finiş = **yakın plan** (boya, vernik, LED, doku), reveal = **tek hareketli plan** (yavaş dolly/pan) |
| Reveal | "Kontrast" üzerine kurulu: gri→sıcak, kaba→cozy, mat→ışıltılı |
| Konu tipi | Ucuz ham malzeme + ev/bahçe objesi + duygusal kicker (köpek nişe yatar, kahve köşesi kullanılır) |
| Monetizasyon | Bio linki → "AI video nasıl yapılır" rehberleri/affiliate |

**Tipik projeler:** köpek nişli palet yatak, briket basamak, briket antre bankı, beton el + taş kaplı takı standı, palet kahve köşesi, lateks eldivenle beton el kuş yemliği/şelale, tekerlekli palet mutfak adası, betona gömülü dal takı standı.

---

## 1. Karakter Kartı (kendi orijinal karakterin — kopya değil)

Referans hesabın karakterini birebir kopyalama; aynı **rolü** oynayan kendi karakterini kur. Tüm promptlarda bu blok AYNEN kullanılır.

```
CHARACTER_BLOCK:
"MAYA" — a woman in her late 20s, shoulder-length copper-auburn hair in a low messy bun,
light freckles, athletic build. Wears a mustard-yellow work overall over a white fitted tee,
tan leather work gloves, clear safety glasses pushed up on head, beige canvas sneakers.
Calm, focused expression. Same outfit in every scene.
```

**Kurallar**
- 1 adet **karakter referans sayfası** üret (ön / 3/4 / yan / tam boy, nötr arka plan) → tüm keyframe'lerde referans görsel olarak ver.
- Kıyafet ve saç asla değişmez (seri tanınırlığı = hesap kimliği).
- Yüz yakın planından kaçın; karakter "işçi eller + silüet" olarak var olur, odak iş üzerindedir.

---

## 2. Senaryo Üretici — LLM Sistem Promptu

Aşağıdaki bloğu Claude / Ollama / GPT'ye sistem promptu olarak ver. Girdi: `{adet}` ve opsiyonel `{kategori}`.

```
You are a scriptwriter for silent, AI-generated DIY transformation shorts (9:16, 20–35s).
Every video follows EXACTLY this 4-beat structure and camera grammar:

BEAT 1 – ANCHOR (0–3s): CHARACTER_BLOCK walks into the space / stands next to raw materials.
BEAT 2 – STAKES (3–7s): raw, cheap, ugly material or unfinished build clearly visible.
BEAT 3 – PROCESS (7–22s): 4–6 readable build steps, SAME static wide angle for all steps,
         then 1–2 close-ups ONLY for finishing (paint, stain, sealing, LED, rhinestones, moss).
BEAT 4 – PAYOFF (22–30s): one slow camera move revealing the finished, styled object IN USE
         (pet sleeps in it, coffee poured, plants placed, candles lit) + an emotional kicker.

Rules:
- Materials must be cheap/industrial: pallets, cinder blocks, concrete, rebar, PVC pipe,
  tree branches, tires, crates, bricks, gravel, epoxy, rope, old doors/windows.
- Result must be cozy / luxurious / Pinterest-worthy. Maximize raw→finished CONTRAST.
- Physically plausible steps (no magic). No dialogue, no text needed to understand.
- Each idea must have a one-sentence payoff ("the cat curls up inside the glowing nook").

Output JSON array, each item:
{
 "id": "",
 "title": "",
 "hook_caption": "",            // max 8 words, on-screen text for first 2s (optional)
 "location": "",                // backyard, garage, living room, balcony...
 "raw_materials": [],
 "contrast": "raw texture → finished texture",
 "payoff_sentence": "",
 "shots": [
   {"n":1,"beat":"ANCHOR","duration_s":3,"camera":"static wide","action":"","keyframe_prompt":"","motion_prompt":""},
   ... 8–10 shots total
 ],
 "sfx": [],                     // ASMR: saw, drill, trowel scraping, paint roller...
 "music_mood": "",
 "caption": "",                 // IG/TikTok caption, 1–2 lines + CTA
 "hashtags": []                 // 8–12
}
Generate {adet} ideas in category {kategori}. No duplicates of previous titles: {gecmis_basliklar}.
```

---

## 3. Hazır Senaryo Havuzu (30 fikir)

**Evcil hayvan**
1. Briket + ahşap tabla kedi tırmanma kulesi, sisal ip sarılı
2. Eski lastikten köpek yatağı — içi yastık, dışı boyalı
3. Palet köpek kulübesi, yeşil çatı (sukulent)
4. Beton döküm kedi mama kasesi seti, altın kenar
5. Merdiven altına gömme köpek odası, LED + minder

**Bahçe / dış mekan**
6. Briket + çam tahtası ateş çukuru oturma alanı
7. Palet dikey bitki duvarı + damla sulama
8. Beton basamak taşları, içine yaprak baskısı
9. Lastik + halat sallanan oturak
10. Briket ızgara/BBQ istasyonu
11. Eski kapıdan bahçe bankı
12. PVC boru + bez gölgelik pergola

**İç mekan mobilya**
13. Tekerlekli palet kahve sehpası, epoksi dolgu
14. Briket TV ünitesi, üstü meşe tabla
15. Beton lavabo tezgahı (banyo)
16. Kasa (crate) kitaplık duvarı
17. Palet yatak başlığı + gömme okuma lambası
18. Eski pencere çerçevesinden duvar vitrini

**Dekor / küçük obje (hızlı üretim, yüksek viral)**
19. Lateks eldivenle beton el mumluk
20. Beton küre saksılar, bakır boya
21. Kök/dal + epoksi nehir sehpa
22. Beton harf (baş harf) bookend
23. Dal + beton tabanlı mücevher ağacı, beyaz boya
24. Taş kaplı beton kafatası/obje (rhinestone)
25. Cam şişelerden LED avize

**Büyük dönüşüm (en yüksek izlenme)**
26. Balkon → kahve köşesi (palet bar + asma sandalye)
27. Garaj köşesi → mini spor alanı
28. Bahçe köşesi → konteyner ofis girişi
29. Merdiven altı → kitap okuma nişi
30. Boş duvar → gömme akvaryum + beton çerçeve

---

## 4. Tam Örnek Senaryo (üretime hazır)

**Başlık:** Briket Kedi Kulesi
**Kontrast:** gri kaba briket → sıcak ahşap + sisal + bitkili cozy köşe
**Payoff:** Kedi en üst kata çıkıp güneşte kıvrılır.
**Süre:** ~28 sn, 9:16

| # | Vuruş | Süre | Kamera | Aksiyon |
|---|---|---|---|---|
| 1 | ANCHOR | 3s | statik geniş | Maya elinde el arabasıyla boş salon köşesine girer |
| 2 | STAKES | 3s | statik geniş (aynı açı) | Yerde 8 briket, ham çam tahtaları, sisal ip rulosu |
| 3 | PROCESS | 3s | statik geniş | Briketleri 3 kademeli merdiven şeklinde dizer |
| 4 | PROCESS | 3s | statik geniş | Kademelerin üstüne tahtaları yapıştırır |
| 5 | PROCESS | 3s | statik geniş | Dikey briket sütununa sisal ip sarar |
| 6 | FINISH | 2.5s | yakın plan | Tahtalara bal rengi vernik fırçası |
| 7 | FINISH | 2.5s | yakın plan | Briketlere sıcak kum rengi boya rulosu |
| 8 | FINISH | 2s | yakın plan | Kademelere minder ve sarkan pothos bitkisi |
| 9 | PAYOFF | 6s | yavaş dolly-in | Güneşli köşe; turuncu tekir kedi basamakları çıkıp en üstte kıvrılır, Maya arka planda gülümser |

**Keyframe promptları (görsel model — karakter referans görseli EKLİ)**

```
SHOT 1:
Vertical 9:16 photo, empty bright living-room corner with oak floor and white wall,
[CHARACTER_BLOCK] entering from left pushing a wheelbarrow of grey cinder blocks,
static wide shot, eye level, soft morning window light, photorealistic, 35mm.

SHOT 2 (same camera position):
Same living-room corner, same camera angle, eight rough grey cinder blocks on the floor,
stack of raw pine boards, a roll of natural sisal rope, no people, photorealistic.

SHOT 3:
Same corner, same angle, [CHARACTER_BLOCK] kneeling, arranging cinder blocks into a
three-level staircase shape against the wall, photorealistic.

SHOT 4:
Same corner, same angle, cinder-block staircase now topped with pine boards,
[CHARACTER_BLOCK] pressing a board down with construction adhesive tube nearby.

SHOT 5:
Same corner, same angle, a vertical cinder-block column wrapped tightly in sisal rope,
[CHARACTER_BLOCK] finishing the last wrap.

SHOT 6:
Extreme close-up, gloved hand brushing honey-colored varnish onto pine board,
wet glossy streak, shallow depth of field, macro texture.

SHOT 7:
Close-up, paint roller applying warm sand-beige paint over rough cinder block surface,
half painted half raw, visible texture contrast.

SHOT 8:
Close-up, hands placing a linen cushion on the top level, a trailing pothos plant
hanging over the edge.

SHOT 9 (REVEAL):
Finished cozy cat tower in the sunlit corner: sand-beige painted blocks, varnished
pine steps, sisal-wrapped column, cushions, pothos plants, warm golden-hour light,
an orange tabby cat curled on the top cushion, [CHARACTER_BLOCK] softly smiling
in the soft-focus background, Pinterest interior style, photorealistic.
```

**Hareket promptları (image-to-video, ilk kare + son kare modu)**

```
SHOT 1: The woman walks in from the left pushing the wheelbarrow, stops. Static camera.
SHOT 3: Timelapse-like fast motion, she stacks blocks one by one into steps. Static camera.
SHOT 4: She lays boards and presses them down. Static camera, slight speed-ramp.
SHOT 5: Rope wraps around the column quickly, hands moving in circles. Static camera.
SHOT 6: Brush slides slowly, varnish spreads and shines. Macro, very slow.
SHOT 7: Roller moves up, color covers raw texture. Slow.
SHOT 8: Cushion is placed, plant leaves sway gently.
SHOT 9: Slow cinematic dolly-in. The cat climbs the steps and curls up on top, tail wraps. Warm light flicker.
```

**SFX:** blok sürtme, yapıştırıcı tabancası, ip gerilme, fırça, rulo, kedi mırlaması
**Müzik:** soft lo-fi / acoustic, reveal'da hafif swell
**Caption:** `8 cinder blocks → my cat's favorite spot 🐈 Would you build this?`
**Hashtag:** `#diy #cattower #cinderblock #homedecor #aivideo #diyhomedecor #catsoftiktok #roommakeover #budgetdiy #aiart`

---

## 5. Üretim Pipeline'ı

> Not: Referans hesabın kullandığı araçlar doğrulanmış değil. Aşağıdakiler bu çıktıyı üretebilen tipik zincir.

```
[1] Senaryo JSON (LLM)
      ↓
[2] Karakter referans sayfası (1 kez)
      ↓
[3] Keyframe görselleri (her shot için) — referans görsel + CHARACTER_BLOCK
      • Tutarlılık için: bir önceki shot'ı da referans olarak ver ("same camera, same room")
      ↓
[4] Image-to-video (tercihen first-frame + last-frame modu)
      • Shot N'in son karesi = Shot N+1'in ilk karesi → akıcı süreklilik
      • 5 sn klipler, 2–3 varyasyon üret, en iyisini seç
      ↓
[5] Kurgu: hızlandırma (speed ramp), SFX, müzik, ilk 2 sn hook text
      ↓
[6] Upscale + 1080x1920 export → paylaşım
```

| Adım | Seçenekler |
|---|---|
| Senaryo | Claude / Ollama (lokal) |
| Keyframe + tutarlılık | Nano Banana (Gemini image edit), Flux Kontext, Midjourney (omni-reference), Seedream |
| Görselden video | Kling (start/end frame), Veo 3, Seedance, Hailuo, Runway |
| Toplu arayüz | Higgsfield / Freepik / Krea (birden fazla modeli tek yerden) |
| Kurgu | CapCut veya **Remotion** (otomatik) |
| SFX | ElevenLabs SFX, Freesound, CapCut kütüphanesi |
| Upscale | Topaz Video / model içi upscale |

**Tutarlılık hileleri**
- Yapım shotlarında **aynı arka plan görselini** baz al, sadece nesneyi ve karakterin pozunu değiştir (image edit, sıfırdan üretme).
- Işık, saat, zemin, duvar rengi tüm shotlarda sabit yazılsın.
- Negatif: `no text, no watermark, no extra fingers, no morphing tools, no outfit change`.
- Yüz bozulmasını azaltmak için karakteri çoğunlukla 3/4 arkadan veya elleriyle göster.

---

## 6. Kurgu Şablonu (9:16, ~28 sn)

```
00.0–02.0  Hook: en kontrastlı kare (ham malzeme + son hali split veya flash-forward) + 5–8 kelime text
02.0–07.0  Anchor + stakes
07.0–19.0  Process — her step 2–3 sn, speed ramp, beat'e kesme
19.0–22.0  Finish close-up'lar (yavaş)
22.0–28.0  Reveal — tek hareketli plan, müzik swell, emotional kicker
Loop:      Son kareyi ilk kareye yakın bitir → izlenme tekrarı artar
```

---

## 7. n8n Otomasyonu (4 video/hafta → ölçeklenebilir)

```
Cron (Pzt 09:00)
 → LLM node: Bölüm 2 promptu, adet=4, gecmis_basliklar = Google Sheet'ten
 → Sheet'e yaz (id, title, status=script)
 → Loop shots:
     → Image API (keyframe, referans görsel URL'si ile) → Drive'a kaydet
     → Video API (start frame = shot N, end frame = shot N+1) → poll → indir
 → Remotion render (shots + sfx + music + hook text JSON'dan)
 → Telegram: önizleme + "Onayla / Yeniden üret" butonu
 → Onay → YT Shorts / TikTok / IG Reels upload + caption/hashtag
 → Sheet status=posted
```

**Maliyet kontrolü:** keyframe'leri önce ucuz modelle üret, sadece onaylanan senaryoda video üret. Reveal shot'ına en iyi (pahalı) modeli, process shotlarına ucuz modeli kullan.

---

## 8. Yayın Checklist

- [ ] Karakter kıyafeti tüm shotlarda aynı
- [ ] Yapım shotları aynı açıdan
- [ ] Reveal'da nesne **kullanımda** (hayvan / kahve / bitki / ışık)
- [ ] İlk 2 sn'de kontrast görünüyor
- [ ] Platform AI etiketi açık (IG/TikTok "AI generated" label)
- [ ] Caption'da soru/CTA ("Would you build this?")
- [ ] Bio linki: rehber / prompt paketi / affiliate
