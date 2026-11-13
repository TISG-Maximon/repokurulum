---
name: video-seslendirme
description: Adım adım anlatım / müşteri rehberi / eğitim videosu üretir (dikey 1080x1920, marka tasarımlı sahneler, Türkçe Microsoft Emel seslendirmesi, konuşmaya senkron sabit altyazı, siyahsız geçişler) ya da hazır sessiz bir videoya seslendirme ve altyazı ekler. "video yap", "rehber videosu", "adım adım anlat", "seslendir", "videoya ses/altyazı ekle", "reels/shorts" isteklerinde kullan.
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
   - Toplam hedef: 45–75 sn (bir sahne ≈ konuşma + 0,8 sn).
4. **Ekran görseli:**
   - Kullanıcı gerçek ekran görüntüsü verdiyse `ekran_gorsel` kullan. Önce ilgili bölümü kırp (`ffmpeg -i ss.png -vf crop=G:Y:X:Y kirpik.png`); kişisel veriyi (TC no, ad, telefon) mutlaka karart veya temsili veriye çevir.
   - Yoksa `ekran_html` ile temsili ekran çiz ve köşeye "Temsili ekran" yaz. Hazır sınıflar: `pencere`, `pbas` (üst çubuk, `marka` kırmızı yazı), `pgovde` + `yan` (sol menü, seçili öğe `sec`) + `sag`, `alan` (giriş kutusu), `dugme` (`mavi`/`kirmizi`/`sari`), `hedef` (tıklanacak yeri sarı çerçeveyle işaretler, her ekranda bir tane), `table.t` (satır `yesil`/`mavi`/`kirmizi`), `not`.
5. **Önizle:** `$VS gorsel senaryo.json` çalıştır ve `gorseller.png`'yi (gerekirse tek tek `gorseller/sahne_XX.png`) Read ile AÇ. Kontrol et: taşan metin, boş alan, yanlış vurgu, hedef işaretinin yeri, Türkçe karakterler. Sorun varsa düzelt ve tekrarla.
6. **Üret:** `$VS olustur senaryo.json`. Çıktıdaki sahne sürelerine bak.
7. **Doğrula:** `kontrol.png`'yi aç: altyazı sabit yerde mi, içeriğin üstüne biniyor mu (binerse `altyazi.y_orani` değerini değiştir, 0,78–0,84), siyah ara 0 mı. Gerekirse `ffmpeg -ss <sn> -i <ad>-altyazili.mp4 -frames:v 1 kare.png` ile tek kare al.
8. **Teslim:** Dosya yollarını ver. Sesi dinleyemediğini, telaffuzu (özellikle kısaltmalar ve özel adlar) kullanıcının kontrol etmesi gerektiğini söyle. Düzeltme isterse sadece ilgili `metin`/`telaffuz` alanını değiştirip `olustur`'u tekrar çalıştır.

## İş akışı B — Hazır videoya seslendirme ve altyazı

1. `$VS analiz <video>` → `<video>-seslendirme/sahneler.json` ve `sahneler/sahne_XX.png`, `genel.png`.
2. Sahne karelerini Read ile aç, ekrandaki yazıyı oku. Yanlış bölünmüş sahneleri birleştir/ayır (`bas`/`son`), gereksiz olanlara `"atla": true` yaz.
3. Her sahneye `metin` yaz (kurallar A.3 ile aynı). Kullanıcı zaman damgalı metin verdiyse sahnelere eşle ve akıcı hale getir; anlamı değiştirme.
4. `$VS uret <klasor>/sahneler.json`. Siyah geçişler atılır, sahneler 0,3 sn yumuşak geçişle birleşir, her sahne kendi anlatımı kadar sürer.
5. Doğrula ve teslim et (A.7–A.8).

## Ayarlar (`senaryo.json` / `sahneler.json`)

- `ses`: `tr-TR-EmelNeural` (kadın, varsayılan) veya `tr-TR-AhmetNeural` (erkek). `hiz`: `+4%` (doğal); en fazla `+12%`, daha hızlı yapma, metni kısalt.
- `motor`: `edge` (internet, en doğal). Metin gizli/kurum içiyse `piper` (çevrimdışı, `piper_ses`: `tr_TR-fahrettin-medium` / `tr_TR-dfki-medium` / `tr_TR-fettah-medium`).
- `altyazi`: `yazi_tipi` (Arial), `boyut_orani` (0,026 = 50 px / 1920), `y_orani` (0,80), `max_karakter` (40).
- `marka`: `ad`, `logo` (png yolu), `site`, `eposta`, `renk_arka1`, `renk_arka2`, `renk_vurgu`, `renk_kirmizi`. Boşsa Teknik İSG.
- `boyut`: `[1080, 1920]` dikey; yatay için `[1920, 1080]` (o zaman `y_orani` ~0,86).

## Yapma

- edge-tts metni Microsoft'a gönderir: kişisel veya gizli bilgiyi seslendirmeye koyma (gerekirse `piper`).
- Ücretli servis (ElevenLabs, HeyGen Voice) kullanma; kullanıcı açıkça istemedikçe başka TTS deneme.
- Gerçek kişilerin adını, TC numarasını ya da telefonunu ekranda gösterme; temsili veri kullan.
- Remotion tabanlı araçlarla şirket videosu yapma (lisans ücretli).
