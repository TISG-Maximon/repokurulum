---
name: video-seslendirme
description: Gerçekçi (Gemini/Veo klipli) veya tasarım sahneli adım adım anlatım / müşteri rehberi / eğitim videosu üretir (dikey 1080x1920, marka tasarımlı sahneler, Türkçe Microsoft Emel seslendirmesi, konuşmaya senkron sabit altyazı, siyahsız geçişler) ya da hazır sessiz bir videoya seslendirme ve altyazı ekler. "video yap", "rehber videosu", "adım adım anlat", "seslendir", "videoya ses/altyazı ekle", "reels/shorts" isteklerinde kullan.
---
<!-- repokurulum: bu dosya Repo Kurulum tarafindan yonetilir; guncellemede yenilenir. Kendine gore degistireceksen bu satiri sil. -->

# Video seslendirme ve rehber videosu

Araç: `~/.claude/skills/video-seslendirme/seslendir.py` (`uv run --script` ile çalışır, bağımlılığını kendi kurar).
Gerekenler: ffmpeg, uv, Edge veya Chrome (görsel üretimi için). Ses: internet varsa edge-tts (Microsoft Emel), yoksa Piper.

Komutlar (kısaltma: `VS="uv run --script $HOME/.claude/skills/video-seslendirme/seslendir.py"`):

| Komut | Ne yapar |
|---|---|
| `$VS gorsel <klasor>/senaryo.json` | Sahne görsellerini üretir (`gorseller/`, toplu bakış `gorseller.png`). Ses yok, hızlı önizleme. |
| `$VS olustur <klasor>/senaryo.json` | Görseller + seslendirme + altyazı → video. |
| `$VS analiz <video.mp4>` | Hazır video: sahneleri ve siyah geçişleri bulur, `sahneler.json` taslağı ve sahne kareleri üretir. |
| `$VS uret <klasor>/sahneler.json` | Hazır videoya seslendirme + altyazı; siyah geçişleri atar, sahneleri anlatıma göre uzatır. |
| `$VS istemler <klasor>/senaryo.json` | Gerçekçi `klip` sahneleri için Gemini (Veo) istem listesi: `veo-istemleri.md`. |
| `$VS klipler <klasor>/senaryo.json` | İndirilen klipleri listeler, her biri için 6 karelik `klipler/kontrol_XX.png` üretir. |
| `$VS dene "metin"` | Tek cümlenin telaffuzunu dener (`deneme.mp3`). |

Çıktılar (proje klasöründe): `<ad>.mp4` (seslendirmeli), `<ad>-altyazili.mp4`, `<ad>.srt`, `kontrol.png`.

## İş akışı A — Sıfırdan video (konu, adımlar, ekran görüntüleri)

1. **Topla:** Konu, hedef kitle, adımlar, varsa gerçek ekran görüntüleri, marka (varsayılan Teknik İSG). Eksik ve belirleyici bir bilgi varsa TEK seferde sor; yoksa varsayılanla ilerle.
2. **Proje klasörü:** `~/ClaudeProjeler/videolar/<kisa-ad>/`. `ornek-senaryo.json` dosyasını bu klasöre `senaryo.json` olarak kopyala ve sahneleri yaz.
3. **Senaryo kuralları:**
   - Akış: `kapak` → (gerekirse `liste` "kim ne yapar") → (ön koşul için `uyari`) → `adim` sahneleri → (tekrar/uyarı) → `kapanis`.
   - Her sahnede bir fikir. `metin` = konuşma ve altyazı: doğal, sıcak, konuşma dili; 1–2 kısa cümle (6–16 kelime). Ekrandaki başlıkla aynı şeyi söylesin ama okumasın, tamamlasın.
   - Başlık kısa (2–5 kelime); `aciklama` tek satır; `**vurgu**` sarı yazar, `\n` satır böler.
   - Aynı adımın alt aşamaları aynı `adim` etiketini kullanır (ilerleme çubuğu adım numarasına göre dolar).
   - Kısaltmalar `telaffuz` sözlüğüne: `İSG→İ Se Ge`, `T.C.→Te Ce`, `SGK→Se Ge Ka`. Sayıyı yanlış okuyabilecekse yazıyla yaz ("%5" → "yüzde beş").
   - **Süre: WhatsApp durum / Instagram hikaye için en fazla 60 sn; hedef 45–58 sn** (bir sahne ≈ konuşma + 0,7 sn). 12–15 sahne, toplam konuşma ~50 sn ≈ 110–125 kelime. Uzunsa önce metni kısalt, sahne birleştir; araç da otomatik olarak boşlukları kısaltır, hızı en fazla +%10 artırır, yine sığmazsa sahne sınırından `-bolum1/-bolum2` diye böler (son çare).
4. **Ekran görseli:**
   - Kullanıcı gerçek ekran görüntüsü verdiyse `ekran_gorsel` kullan. Önce ilgili bölümü kırp (`ffmpeg -i ss.png -vf crop=G:Y:X:Y kirpik.png`); kişisel veriyi (TC no, ad, telefon) mutlaka karart veya temsili veriye çevir.
   - Yoksa `ekran_html` ile temsili ekran çiz ve köşeye "Temsili ekran" yaz. Hazır sınıflar: `pencere`, `pbas` (üst çubuk, `marka` kırmızı yazı), `pgovde` + `yan` (sol menü, seçili öğe `sec`) + `sag`, `alan` (giriş kutusu), `dugme` (`mavi`/`kirmizi`/`sari`), `hedef` (tıklanacak yeri sarı çerçeveyle işaretler, her ekranda bir tane), `table.t` (satır `yesil`/`mavi`/`kirmizi`), `not`.
5. **Önizle:** `$VS gorsel senaryo.json` çalıştır ve `gorseller.png`'yi (gerekirse tek tek `gorseller/sahne_XX.png`) Read ile AÇ. Kontrol et: taşan metin, boş alan, yanlış vurgu, hedef işaretinin yeri, Türkçe karakterler. Sorun varsa düzelt ve tekrarla.
6. **Üret:** `$VS olustur senaryo.json`. Çıktıdaki sahne sürelerine bak.
7. **Doğrula:** `kontrol.png`'yi aç: altyazı sabit yerde mi, içeriğin üstüne biniyor mu (binerse `altyazi.y_orani` değerini değiştir, hikayede 0,74–0,79), siyah ara 0 mı. Gerekirse `ffmpeg -ss <sn> -i <ad>-altyazili.mp4 -frames:v 1 kare.png` ile tek kare al.
8. **Teslim:** Dosya yollarını ver. Sesi dinleyemediğini, telaffuzu (özellikle kısaltmalar ve özel adlar) kullanıcının kontrol etmesi gerektiğini söyle. Düzeltme isterse sadece ilgili `metin`/`telaffuz` alanını değiştirip `olustur`'u tekrar çalıştır.

## İş akışı D — Kısa tanıtım / farkındalık videosu (hikaye anlatımı, çizimli)

Örnek: "Kapı çaldı → panik → 'alt tarafı iki vana' → bantlı boru → kaza olursa → imza sizin → uzmana bırakın". Şablonlar: `ornekler/tanitim-*.json` (site tesisatı, yürüyen merdiven, yangın tesisatı).

- Sahne türü `cizim`:
  - `baslik`: kısa, vurucu, `**vurgu**` ile.
  - `cizim`: düz, sade SVG (viewBox `0 0 600 520`). Renkler: `var(--v)` vurgu, `var(--k)` kırmızı, koyu `#1d3048`, açık `#e8eef6`.
  - Her sahnede tek bir nesne olsun (kapı, vana, manometre, kalkan, kontrol listesi…).
- Akış (8–10 sahne + `kapanis`, 20–35 sn):
  1. Merak uyandıran giriş
  2. Sorun
  3. Gizli risk
  4. Sonuç ("kaza olursa…")
  5. Sorumluluk
  6. Çözüm (uzman / periyodik kontrol)
  7. Kapanış (site + telefon)
- Konuya göre vurgu rengi (`marka.renk_vurgu`): tesisat/su yeşil `#22c55e`, mekanik/asansör sarı `#f6b420`, yangın kırmızı `#ef4444`.
- `metin`: başlığı tekrar etmeden doğal konuşma, kısa ("Oysa boru bantla tamir edilmiş."). Hız `+6%`.
- Var olan bir videonun "görselini ve sesini değiştir" isteğinde:
  1. Önce kareleri çıkar: `ffmpeg -i v.mp4 -vf fps=1,crop=iw:ih/3:0:0,tile=10x3 metin.png`.
  2. Ekrandaki metni sırasıyla oku.
  3. Aynı mesajı yeni çizimlerle bu türde yeniden kur. Orijinal görselleri kopyalama.
- `hareket`: `yakinlas` (varsayılan, hafif yakınlaşma) veya `yok`.

## İş akışı C — Gerçekçi video (pano ölçümü, yangın dolabı muayenesi gibi)

Gerçek kişi ve ekipman görüntüsü Gemini uygulamasındaki **Veo** ile üretilir. Kullanıcının Google AI Pro aboneliği var: günlük kotalı, 8 sn klipler. API yok; klipleri kullanıcı elle üretir. Claude Gemini'yi tarayıcıyla otomatik kullanmaz.

1. Senaryoyu A'daki gibi yaz; `ornek-gercekci.json` şablonunu kullan. Gerçek görüntü gereken sahneler `"tur": "klip"`; kapak, uyarı ve kapanış tasarım sahnesi kalır. 4–6 klip yeterli (kota).
2. Her `klip` sahnesine:
   - `"klip": "klipler/sahne_XX.mp4"`
   - `"adim"`, `"baslik"`, `"aciklama"` (videonun üstüne marka şeridi olarak biner)
   - `"veo_istemi"`: **İngilizce** istem. Şunları yaz: dikey 9:16 ve gerçekçi; kişinin rolü; **doğru KKD**'nin tamamı (baret, gözlük, uygun eldiven, iş kıyafeti); ekipman ve tek bir net eylem; kamera (yakın, sabit); ışık. Sonuna "No on-screen text, no logos, no talking." ekle. Sayı veya gösterge değeri isteme (yapay zekâ yanlış yazar).
   - Prosedür, mevzuata ve iyi uygulamaya uygun olmalı (enerji kesme/kilitleme, yetkili kişi, doğru ölçüm aleti). Emin değilsen istemi genel tut ve ayrıntıyı seslendirmede doğru anlat.
3. `$VS istemler senaryo.json` çalıştır. Kullanıcıya `veo-istemleri.md` yolunu ver: istemleri Gemini > Video'ya yapıştıracak, klipleri belirtilen adla `klipler/` klasörüne koyacak.
4. Kullanıcı "klipler hazır" deyince `$VS klipler senaryo.json` çalıştır ve her `kontrol_XX.png`'yi Read ile **mutlaka** incele:
   - Yanlış veya eksik KKD
   - Tehlikeli ya da yanlış uygulama (enerjili panoda eldivensiz çalışma, yanlış alet)
   - Bozuk el, yüz veya alet; anlamsız yazı ya da logo
   Sorunlu klip için düzeltilmiş istem yaz ve yeniden ürettir. **İSG içeriğinde yanlış uygulama gösteren klibi asla kullanma.**
5. `$VS olustur senaryo.json`. Klip ayarları:
   - Yatay klip dikeye bulanık arka planla uyarlanır (`doldur`: `otomatik` / `kirp` / `bulanik`).
   - Kısa klip en fazla %35 yavaşlatılır, sonra son karede durur.
   - `klip_bas` / `klip_son` ile kırpılır.
   - Klibin sesi kapalıdır; ortam sesi için `klip_ses: 0.15`.
   - Klibi olmayan sahnede tasarım görseli kullanılır ve UYARI yazılır.
6. Teslimde şunu söyle: Gemini videolarında görünür Veo filigranı ve SynthID olabilir. Instagram yapay zekâ içeriğini "AI bilgisi" olarak etiketleyebilir. İçerik temsilîdir; gerçek ölçüm görüntüsü değildir.

## İş akışı B — Hazır videoya seslendirme ve altyazı

1. `$VS analiz <video>` → `<video>-seslendirme/sahneler.json` ve `sahneler/sahne_XX.png`, `genel.png`.
2. Sahne karelerini Read ile aç, ekrandaki yazıyı oku. Yanlış bölünmüş sahneleri birleştir/ayır (`bas`/`son`), gereksiz olanlara `"atla": true` yaz.
3. Her sahneye `metin` yaz (kurallar A.3 ile aynı). Kullanıcı zaman damgalı metin verdiyse sahnelere eşle ve akıcı hale getir; anlamı değiştirme.
4. `$VS uret <klasor>/sahneler.json`. Siyah geçişler atılır, sahneler 0,3 sn yumuşak geçişle birleşir, her sahne kendi anlatımı kadar sürer.
5. Doğrula ve teslim et (A.7–A.8).

## Paylaşım biçimi: hikaye / durum (varsayılan)

- `platform: "hikaye"` (varsayılan): 1080x1920, 30 fps, H.264 + AAC, en fazla 60 sn (`hedef_sure_sn`: 58). Çıktı satırında `Hikaye/durum: UYGUN` görünmeli.
- Güvenli alan: üstteki ~250 px (profil, ilerleme çubuğu) ve alttaki ~340 px (yanıt kutusu) boş bırakılır; şablon logo, içerik ve altyazıyı buna göre yerleştirir. Hazır videoda (iş akışı B) üst ve alt bölge orijinal tasarıma bağlıdır; önemli yazı orada kalıyorsa kullanıcıya söyle.
- Yatay/normal video için `platform: "normal"` ve `hedef_sure_sn: 0` (sınır yok).

## Ayarlar (`senaryo.json` / `sahneler.json`)

- `ses`: `tr-TR-EmelNeural` (kadın, varsayılan) veya `tr-TR-AhmetNeural` (erkek). `hiz`: `+4%` (doğal); en fazla `+12%`, daha hızlı yapma, metni kısalt.
- `motor`: `edge` (internet, en doğal). Metin gizli/kurum içiyse `piper` (çevrimdışı, `piper_ses`: `tr_TR-dfki-medium` (yoksa klasördeki başka Türkçe ses)).
- `altyazi`: `yazi_tipi` (Arial), `boyut_orani` (0,026 = 50 px / 1920), `y_orani` (hikayede 0,765, hazır videoda 0,78), `max_karakter` (40).
- `marka`: `ad`, `logo` (png yolu), `site`, `eposta`, `renk_arka1`, `renk_arka2`, `renk_vurgu`, `renk_kirmizi`. Boşsa Teknik İSG.
- `boyut`: `[1080, 1920]` dikey; yatay için `[1920, 1080]` (o zaman `y_orani` ~0,86).

## Yapma

- edge-tts metni Microsoft'a gönderir: kişisel veya gizli bilgiyi seslendirmeye koyma (gerekirse `piper`).
- Ücretli servis (ElevenLabs, HeyGen Voice, Veo API) kullanma; kullanıcı açıkça istemedikçe başka TTS deneme. Gerçekçi klip yalnızca kullanıcının kendi Gemini (Google AI Pro) kotasıyla, elle üretilir.
- Gerçek kişilerin adını, TC numarasını ya da telefonunu ekranda gösterme; temsili veri kullan.
- Remotion tabanlı araçlarla şirket videosu yapma (lisans ücretli).
