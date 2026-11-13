# Araç seçim kuralları

Kurallar kurulum setup'ının içinde, her bileşenin kendi kaydında durur (`installer/bilesenler.json` → `kurallar`). Yeni bir araç eklendiğinde ne işe yaradığı ve hangi ihtiyaçta kaçıncı sırada deneneceği de orada yazılır.

Kurulum uygulaması **hiçbir dosyaya yazmaz**. Metni sen alırsın:

1. Kurulum penceresinde **Kurallari Kopyala**'ya bas. Yalnızca **o PC'de kurulu** araçların kuralları panoya kopyalanır.
2. `C:\Users\<sen>\.claude\CLAUDE.md` dosyasını aç, eski "Araç seçim kuralları" bölümünü sil, **Ctrl+V** ile yapıştır, kaydet.
3. Claude'u yeniden aç.

Komut satırından da alabilirsin:
```powershell
& "$env:LOCALAPPDATA\RepoKurulum\app\installer\RepoKurulum.ps1" -Kurallar | Set-Clipboard
```
(`-TumKurallar` kurulu olmayanlar dahil hepsini verir.)

## Yeni bir araç eklerken
`bilesenler.json`'da bileşene bir `kurallar` alanı ekle:
```json
"kurallar": [ { "ihtiyac": "arama", "oncelik": 2, "arac": "ornek", "metin": "Tek cümlelik amaç",
                "ne_zaman": ["koşul 1", "koşul 2"], "ne_zaman_degil": ["..."],
                "nasil": ["verimli kullanım adımı"], "dogrula": "sonucun doğruluğu nasıl kontrol edilir" } ]
```
`ihtiyac` değerleri: `dokuman` (Kütüphane / framework / API dokümanı), `arama` (Web araması ve güncel bilgi), `sayfa` (Bilinen bir URL'nin içeriğini okumak), `tarayici` (Tarayıcıda etkileşim (tıklama, form, giriş, ekran görüntüsü)), `belge` (Yerel belge okuma (PDF, Word, Excel, PowerPoint, resim)), `kaynak` (Çok sayıda kaynağı analiz etmek, kaynaklı özet / podcast / slayt), `proje` (Üzerinde çalıştığın projenin kodunu anlamak), `dis-repo` (Başka bir repoyu incelemek), `github` (GitHub işlemleri (issue, PR, inceleme, Actions)), `dusunme` (Karmaşık, çok adımlı problem), `is-akisi` (Geliştirme iş akışı), `uygulama` (Var olan bir uygulamaya benzer ürün yapmak), `video` (Video ve animasyon üretmek), `seslendirme` (Metni seslendirmek (Türkçe TTS)), `sunum` (Slayt / sunum hazırlamak). Aynı ihtiyaçta `oncelik` küçük olan önce denenir.

---

## Tüm araçlar kuruluyken üretilen metin

````markdown
# Araç seçim kuralları

- **Karar süreci (her istekte bu sırayla):** (1) İsteğin amacını ve gerektirdiği eylemleri çıkar (örn. "bu PDF'teki tabloyu al, güncel fiyatlarla karşılaştır" → belge okuma + web araması). (2) Her eylemi aşağıdaki **Hızlı eşleme** tablosunda bul; koşulu tutan aracı seç. (3) Aracın **Ne zaman değil** satırı tutuyorsa aynı başlıktaki bir sonrakine geç. (4) Eylemleri sırayla uygula, her sonucu **Doğrula** satırına göre kontrol et. (5) Ancak sonra cevap ver.
- **Proaktif ol:** Bir aracın Ne zaman koşulu tutuyorsa kullanıcı adını söylemese de kullan. Kullanıcı bir aracı adıyla isterse her zaman onu kullan.
- **Doğruluk önce gelir:** Güncel bilgi, sürüm, fiyat, tarih, API imzası gibi değişebilen her şeyi araçla doğrula; ezberden yazma. Cevapta kullandığın kaynağı (URL, dosya:satır, doküman) belirt.
- **Verimlilik:** Aynı bilgiyi iki araçla çekme. İlk araç yeterli ve güvenilir sonuç verdiyse dur. Bağımsız çağrıları paralel yap. Büyük çıktıyı tamamen okuma; ara, daralt, gerekeni oku.
- **Yerel mi dış mı:** Yerel dosya/kod için yerleşik Read/Grep/Glob/Edit; internet, tarayıcı, dış servis ve belge dönüştürme için MCP araçları.
- **Hata durumunda:** Araç hata verirse veya bağlı değilse aynı başlıktaki bir sonraki araca geç; listede araç kalmadıysa yerleşik araçları (WebSearch, WebFetch, Read, Grep) kullan. Aynı araçla 2 başarısız denemeden sonra kullanıcıya ne denediğini ve neyin başarısız olduğunu söyle.
- **Anahtarlı/kotalı araçlar** (exa, tavily, firecrawl, github): gereksiz tekrar ve çok geniş sorgulardan kaçın; önce sorguyu daralt.

## Hızlı eşleme: koşul → araç
İstekteki eylemi/koşulu bu tabloda bul, eşleşen aracı kullan; ayrıntı ve sınırlar için aşağıdaki ilgili bölüme bak. Birden fazla satır eşleşirse ihtiyaç başlığındaki sırayı izle.

| Koşul / eylem | Araç |
|---|---|
| İş birkaç araç çağrısıyla bitecek | **ana oturum (Opus, medium)** |
| Kullanıcıyla konuşarak ilerleyen, bağlamı önemli işler | **ana oturum (Opus, medium)** |
| Sonucu alt ajana anlatmak işi yapmaktan uzun sürecek | **ana oturum (Opus, medium)** |
| Çok dosyada arama/okuma/özetleme ana bağlamı şişirecek | **hizli-isci (Sonnet, medium)** |
| Toplu, mekanik düzenleme (yeniden adlandırma, format, tekrar eden kalıp) | **hizli-isci (Sonnet, medium)** |
| Log/test çıktısı tarama | **hizli-isci (Sonnet, medium)** |
| Birbirinden bağımsız alt işler (paralel çalıştır) | **hizli-isci (Sonnet, medium)** |
| Sebebi belirsiz, birden çok bileşene yayılan hata | **derin-analist (Opus, high)** |
| Mimari/tasarım kararı, seçenek karşılaştırması | **derin-analist (Opus, high)** |
| Güvenlik veya veri kaybı riski olan değişiklik | **derin-analist (Opus, high)** |
| Ana bağlamı kirletmeden uzun araştırma | **derin-analist (Opus, high)** |
| Çok dosyalı veya riskli değişiklik tamamlandı | **dogrulayici (Sonnet, medium)** |
| Kullanıcıya teslim edilecek önemli bir sonuç var | **dogrulayici (Sonnet, medium)** |
| Yeni fonksiyon/modül, test yazma, mekanik refactor, şablon/tekrar eden kod gibi iyi tanımlanmış kod yazma işleri | **glm-kodcu (GLM 5.3)** |
| Birbirinden bağımsız 2+ kod işi var (her biri ayrı dosya setinde): her biri için ayrı glm-kodcu'yu TEK mesajda başlat | **glm-kodcu (GLM 5.3)** |
| İstek önceki bir işe, karara veya konuşmaya atıf yapıyor ("geçen sefer", "daha önce", "kaldığımız yerden", "neden böyle yapmıştık") | **notebooklm (Claude Hafiza'dan okuma)** |
| Var olan bir projede oturumun ilk görevinden önce bir kez: o projenin son durumu, açık işler, alınan kararlar | **notebooklm (Claude Hafiza'dan okuma)** |
| Karşılaşılan hata/sorun daha önce çözülmüş olabilir | **notebooklm (Claude Hafiza'dan okuma)** |
| Kullanıcı "hatırla", "hafızaya bak" dedi | **notebooklm (Claude Hafiza'dan okuma)** |
| Önemli bir araştırma sonucu, mimari/tasarım kararı, kurulum veya çözüm notu üretildi | **notebooklm (Claude Hafiza'ya belge ekleme)** |
| Kullanıcı projeyle ilgili önemli bir belge (PDF, rapor, şartname, URL) verdi | **notebooklm (Claude Hafiza'ya belge ekleme)** |
| Bir dış paketin API'sini kullanan kod yazacak/düzeltecek isen (kullanıcı istemese de) | **context7** |
| Hata bir kütüphaneden geliyorsa | **context7** |
| Kullanıcı belirli bir sürüm söylediyse | **context7** |
| Genel araştırma ve kaynak bulma | **exa** |
| Anlam bazlı arama ("şuna benzer projeler", "X'i anlatan makaleler") | **exa** |
| Kullanıcı "derin araştır", "rapor", "tüm kaynaklarıyla" dedi | **tavily** |
| Bir sitenin birçok sayfasını tarayıp toplamak gerekiyor | **tavily** |
| Hızlı tek gerçek kontrolü, resmi site/doküman sayfası bulma | **duckduckgo** |
| Üstteki arama araçları yoksa, hata verdiyse veya kotası bittiyse | **duckduckgo** |
| Birden çok sayfa toplanacak | **firecrawl** |
| Sayfadan tablo/liste gibi yapılandırılmış veri çıkarılacak | **firecrawl** |
| JavaScript ile yüklenen ama etkileşim gerektirmeyen sayfa | **firecrawl** |
| Tek bir URL'nin metni yeterli | **duckduckgo (içerik çekme)** |
| Tıklama, form, giriş, dosya yükleme, ekran görüntüsü gerekiyor | **playwright** |
| İçerik yalnızca JavaScript çalışınca görünüyor ve diğer araçlar boş döndü | **playwright** |
| Kullanıcının geliştirdiği web uygulamasını test etmek veya görsel kontrol | **playwright** |
| Desteklenen uzantılı bir dosya okunacak/özetlenecek/içinden veri çıkarılacak | **markitdown** |
| 5+ belge/URL/video birlikte analiz edilecek | **notebooklm** |
| Kaynaklı (alıntılı) cevap gerekiyor | **notebooklm** |
| Podcast, video özet, slayt, quiz, flashcard, zihin haritası istendi | **notebooklm** |
| `graphify-out/graph.json` varsa: mimari, bağlantı, etki analizi soruları ve büyük değişiklik öncesi keşif (Grep/Glob'dan ÖNCE) | **graphify** |
| Proje büyük (yüzlerce dosya) ve grafik yoksa: kullanıcıya bir kez `/graphify .` öner | **graphify** |
| Bir repo baştan anlaşılacak, değerlendirilecek veya özelliği incelenecek | **repomix** |
| Sadece belirli bir dosya, issue, PR, release gerekiyor | **github** |
| İstek GitHub'daki bir nesneyle ilgili (issue, PR, CI, release) | **github** |
| Birbirine bağlı 3+ karar veya birden fazla geçerli çözüm var | **sequential-thinking** |
| Zor, sebebi belirsiz hata | **sequential-thinking** |
| Her kod yazma, düzeltme, refactor | **karpathy ilkeleri** |
| Yeni özellik, çok dosyalı değişiklik, zor hata | **superpowers** |
| "X'in benzerini/klonunu yap", rakip uygulama incelemesi + yeniden yapım | **replica-skill** |
| "X nasıl yapılır videosu", müşteri rehberi, adım adım anlatım, kısa dikey bilgilendirme videosu | **video-seslendirme skill'i** |
| Kullanıcı bir video verip seslendirme/altyazı/konuşma metni istiyor | **video-seslendirme skill'i** |
| Ekran görüntülerinden adım adım video | **video-seslendirme skill'i** |
| Gerçekçi görüntü gereken anlatım (pano ölçümü, yangın dolabı muayenesi): klipler Gemini (Veo) ile kullanıcının kendi kotasıyla üretilir, skill istemleri hazırlar ve klipleri işler | **video-seslendirme skill'i** |
| Konu anlatım / eğitim / İSG bilgilendirme videosu, slayt + seslendirme videosu, kinetik yazı, altyazılı kısa video | **HyperFrames** |
| Şirket adına veya ticari kullanılacak her video (Remotion lisansı gerekmez) | **HyperFrames** |
| Bir web sitesini videoya dönüştürme | **HyperFrames** |
| Bir ürünün, uygulamanın veya sitenin tanıtım/promo/özellik videosu | **video-shotcraft** |
| Gerçek ekran görüntülerinden hareketli video | **video-shotcraft** |
| Seslendirme/anlatım, müzik veya AI görsel gereken açıklayıcı video, kısa dikey video, reklam | **claude-code-video-toolkit** |
| Karakterli animasyon, çizgi film, hikâye anlatan kısa animasyon | **ClaudeAnimationBase** |
| GEMINI_API_KEY tanımlıysa video seslendirmesinde varsayılan (senaryoda `motor: otomatik` veya `gemini`) | **Gemini TTS (video-seslendirme skill'i)** |
| Video anlatımı, dış ses, eğitim/konu anlatımı, sesli özet — internet varsa her Türkçe seslendirmede ilk seçim | **edge-tts** |
| Altyazı da gerekiyorsa (SRT'yi aynı komut verir) | **edge-tts** |
| İnternet yok, edge-tts hata verdi/limit | **Piper** |
| Metin gizli veya kurum içi (dışarı gönderilmemeli) | **Piper** |
| Çok sayıda kısa ses dosyası (hızlı, yerel) | **Piper** |
| Sunum, eğitim slaytı, toplantı sunumu hazırlanacak | **Marp CLI** |
| Video için slayt görselleri + konuşmacı notları (seslendirme metni) gerekiyor | **Marp CLI** |

# Araç ayrıntıları (ihtiyaca göre)

## Model ve alt ajan seçimi
**Tetikleyici:** Her istek. Önce işi parçalara ayır; her parça için aşağıdaki sırayla karar ver.
Araçları bu sırayla değerlendir: ana oturum (Opus, medium) > hizli-isci (Sonnet, medium) > derin-analist (Opus, high) > dogrulayici (Sonnet, medium)

### 1. **ana oturum (Opus, medium)**
- **Amaç:** Varsayılan: işi kendin, doğrudan yap.
- **Ne zaman:** İş birkaç araç çağrısıyla bitecek; Kullanıcıyla konuşarak ilerleyen, bağlamı önemli işler; Sonucu alt ajana anlatmak işi yapmaktan uzun sürecek
- **Ne zaman değil:** Çok dosya okuma/arama ana bağlamı şişirecekse (hizli-isci); Zor ve uzun analiz bağlamı kirletecekse (derin-analist)
- **Nasıl:** Önce işi böl: hangi parçalar rutin, hangileri zor, hangileri birbirinden bağımsız; Alt ajana verirken hedefi, başarı ölçütünü ve dönüş biçimini (kanıtlı, kısa) açıkça yaz
- **Doğrula:** Alt ajandan gelen sonucu, verdiği kanıtla (dosya:satır, komut çıktısı) kontrol et; körü körüne kabul etme.

### 2. **hizli-isci (Sonnet, medium)**
- **Amaç:** Rutin, iyi tanımlı, kolay doğrulanan işler.
- **Ne zaman:** Çok dosyada arama/okuma/özetleme ana bağlamı şişirecek; Toplu, mekanik düzenleme (yeniden adlandırma, format, tekrar eden kalıp); Log/test çıktısı tarama; Birbirinden bağımsız alt işler (paralel çalıştır)
- **Ne zaman değil:** İş küçük (doğrudan yap); İnce yargı, mimari karar veya riskli değişiklik; Sonucu doğrulamak işi yapmaktan pahalı
- **Nasıl:** Bağımsız işleri tek mesajda paralel başlat
- **Doğrula:** Raporundaki kanıtlardan rastgele 1–2 tanesini kendin kontrol et.

### 3. **derin-analist (Opus, high)**
- **Amaç:** Zor ve riskli işler.
- **Ne zaman:** Sebebi belirsiz, birden çok bileşene yayılan hata; Mimari/tasarım kararı, seçenek karşılaştırması; Güvenlik veya veri kaybı riski olan değişiklik; Ana bağlamı kirletmeden uzun araştırma
- **Ne zaman değil:** Basit veya iyi tanımlı işler; Sadece bilgi arama
- **Nasıl:** Problemi, kısıtları ve başarı ölçütünü eksiksiz aktar
- **Doğrula:** Önerilen çözümü uygulamadan önce kanıtlarını oku; uyguladıktan sonra test et.

### 4. **dogrulayici (Sonnet, medium)**
- **Amaç:** Büyük/riskli işten sonra bağımsız kontrol.
- **Ne zaman:** Çok dosyalı veya riskli değişiklik tamamlandı; Kullanıcıya teslim edilecek önemli bir sonuç var
- **Ne zaman değil:** Küçük değişiklik (testi kendin çalıştır); Doğrulamanın toplam maliyeti (ajan başlatma + bağlam aktarımı + raporu okuma) işin kendisinden fazla
- **Nasıl:** Başarı ölçütlerini madde madde ver
- **Doğrula:** KALDI veya DOĞRULANAMADI dönen her maddeyi düzelt ya da kullanıcıya bildir.

> Not: Alt ajan bağlamı sıfırdan kurar (ek token). Görev + bağlam aktarımı + sonucu doğrulama toplamı işi doğrudan yapmaktan fazlaysa alt ajan KULLANMA.

## Kod yazma işini GLM ajanlarına dağıtmak
**Tetikleyici:** Kod yazma, test yazma, refactor, birden fazla bağımsız kodlama işi.

### 1. **glm-kodcu (GLM 5.3)**
- **Amaç:** İyi tanımlanmış kod yazma işlerini GLM'ye yaptırmak; birden fazla bağımsız işi paralel yürütmek.
- **Ne zaman:** Yeni fonksiyon/modül, test yazma, mekanik refactor, şablon/tekrar eden kod gibi iyi tanımlanmış kod yazma işleri; Birbirinden bağımsız 2+ kod işi var (her biri ayrı dosya setinde): her biri için ayrı glm-kodcu'yu TEK mesajda başlat
- **Ne zaman değil:** Mimari/tasarım kararı, güvenlik veya veri kaybı riski olan kod, gereksinimi belirsiz iş (ana oturum ya da derin-analist); Tek satırlık veya birkaç satırlık değişiklik (doğrudan yap); Aynı dosyaya dokunan işleri paralel verme (sırayla ver); GLM anahtarı/kotası hata verdiyse: işi ana oturumda yap ve kullanıcıya bildir
- **Nasıl:** Her görev için çalışma klasörünü, dokunulacak dosyaları, kabul ölçütünü (test komutu) ve yasakları açıkça yaz; Alternatif: ajan başlatmadan `glm-kod -p "<görev>" --permission-mode acceptEdits --output-format text` komutunu Bash'te (gerekirse arka planda) çalıştır
- **Doğrula:** GLM'nin değişikliğini körü körüne kabul etme: ana oturum `git diff`'i okur ve testleri kendisi çalıştırır; sorun varsa düzeltir veya görevi daha net tarifle tekrar verir.

> Not: GLM ayrı bir hizmettir (Z.ai); ana Claude aboneliğini harcamaz ama kendi kotası vardır.

## Geçmiş çalışmalar ve proje hafızası (NotebookLM)
**Tetikleyici:** Önceki işlere, kararlara, konuşmalara atıf; bir projeye geri dönüş; daha önce çözülmüş olabilecek sorun.
Araçları bu sırayla değerlendir: notebooklm (Claude Hafiza'dan okuma) > notebooklm (Claude Hafiza'ya belge ekleme)

### 1. **notebooklm (Claude Hafiza'dan okuma)**
- **Amaç:** Geçmiş oturum özetlerinden ve kaydedilmiş belgelerden kaynaklı bilgi almak.
- **Ne zaman:** İstek önceki bir işe, karara veya konuşmaya atıf yapıyor ("geçen sefer", "daha önce", "kaldığımız yerden", "neden böyle yapmıştık"); Var olan bir projede oturumun ilk görevinden önce bir kez: o projenin son durumu, açık işler, alınan kararlar; Karşılaşılan hata/sorun daha önce çözülmüş olabilir; Kullanıcı "hatırla", "hafızaya bak" dedi
- **Ne zaman değil:** Tamamen yeni, küçük ve bağımsız bir iş; Bu oturumda aynı konu zaten sorgulandı; `~/.claude/repokurulum-hafiza.json` dosyası yok (hafıza henüz kurulmadı)
- **Nasıl:** Notebook kimliğini `~/.claude/repokurulum-hafiza.json` içindeki `notebook_id` alanından oku; `notebooklm ask "<soru>" -n <notebook_id> --json` ile sor; soruya proje adını ve konuyu yaz; Kullanıcıya sormadan çalıştır (izin önceden verildi); cevabı tek paragrafta özetle ve kaynağını belirt
- **Doğrula:** Hafızadaki bilgi eski olabilir: güncel kod/dosyayla çelişirse güncel olanı esas al ve bunu söyle.

### 2. **notebooklm (Claude Hafiza'ya belge ekleme)**
- **Amaç:** Kalıcı değeri olan belge ve kararları hafızaya eklemek.
- **Ne zaman:** Önemli bir araştırma sonucu, mimari/tasarım kararı, kurulum veya çözüm notu üretildi; Kullanıcı projeyle ilgili önemli bir belge (PDF, rapor, şartname, URL) verdi
- **Ne zaman değil:** Şifre, anahtar, kişisel veya gizli bilgi içeren belgeler; Geçici, önemsiz dosyalar; Oturum özetleri (hook otomatik ekliyor; elle gönderme)
- **Nasıl:** `notebooklm source add <dosya-veya-url> -n <notebook_id> --title "<proje>: <konu>" --json`; Bir notebook'ta kaynak sayısı sınırlı: sadece kalıcı değeri olanları ekle, aynı belgeyi iki kez ekleme
- **Doğrula:** Komut çıktısındaki `source.id` alanının dolu olduğunu kontrol et.

> Not: Oturum özetleri her oturum kapanışında otomatik eklenir (SessionEnd/PreCompact hook). Claude oturum özetini elle göndermez.

## Kütüphane / framework / API dokümanı
**Tetikleyici:** Kod bir dış paket, framework, SDK, CLI veya API kullanıyorsa; "nasıl kullanılır", "hangi parametre", "son sürümde ne değişti", hata mesajı bir kütüphaneden geliyorsa.

### 1. **context7**
- **Amaç:** Güncel ve sürüme uygun kütüphane dokümanı ve kod örnekleri.
- **Ne zaman:** Bir dış paketin API'sini kullanan kod yazacak/düzeltecek isen (kullanıcı istemese de); Hata bir kütüphaneden geliyorsa; Kullanıcı belirli bir sürüm söylediyse
- **Ne zaman değil:** Dil çekirdeği/standart kütüphane için emin olduğun temel şeyler; Projenin kendi kodu (onun için proje başlığı)
- **Nasıl:** Önce kütüphane kimliğini çözümle, sonra konuya özel (topic) doküman iste; tüm dokümanı çekme; Projedeki sürümü package.json/requirements/lock dosyasından oku ve o sürümü iste
- **Doğrula:** Yazdığın çağrı imzası dokümandaki örnekle birebir uyuşmalı; mümkünse kodu çalıştır/test et.

## Web araması ve güncel bilgi
**Tetikleyici:** "araştır", "bul", "güncel", "son", "karşılaştır", "en iyi ... hangisi", haber, fiyat, sürüm, olay; bilgin eğitim tarihinden sonra değişmiş olabilecek her şey.
Araçları bu sırayla değerlendir: exa > tavily > duckduckgo

### 1. **exa**
- **Amaç:** Varsayılan arama: kaynak, makale, şirket, kod örneği, "buna benzer" araması.
- **Ne zaman:** Genel araştırma ve kaynak bulma; Anlam bazlı arama ("şuna benzer projeler", "X'i anlatan makaleler")
- **Ne zaman değil:** Kota bittiyse veya basit tek bir gerçek kontrolü yeterliyse (duckduckgo)
- **Nasıl:** Sorguyu tam bir cümle olarak yaz; tarih/dil/alan gerekiyorsa belirt; İlk 3–5 sonucu değerlendir, gerekirse 1 tanesinin tam içeriğini oku
- **Doğrula:** Önemli iddiaları en az 2 bağımsız kaynakla teyit et; tarihleri kontrol et.

### 2. **tavily**
- **Amaç:** Derin araştırma, kaynaklı rapor, bir siteyi baştan sona tarama (crawl/map).
- **Ne zaman:** Kullanıcı "derin araştır", "rapor", "tüm kaynaklarıyla" dedi; Bir sitenin birçok sayfasını tarayıp toplamak gerekiyor
- **Ne zaman değil:** Tek bir hızlı arama yeterliyse
- **Nasıl:** Önce kapsamı (alan adı, tarih aralığı, derinlik) belirle; geniş crawl'dan kaçın
- **Doğrula:** Rapordaki her önemli iddiaya kaynak URL ekle.

### 3. **duckduckgo**
- **Amaç:** Ücretsiz, anahtarsız genel arama; listede üstte başka arama aracı varsa onun yedeği.
- **Ne zaman:** Hızlı tek gerçek kontrolü, resmi site/doküman sayfası bulma; Üstteki arama araçları yoksa, hata verdiyse veya kotası bittiyse
- **Ne zaman değil:** Kaynaklı derin araştırma istendiyse ve tavily kuruluysa
- **Nasıl:** Kısa anahtar kelimelerle ara; gerekirse içerik çekme ile sayfayı oku
- **Doğrula:** Bulunan bilginin kaynağının resmi/güvenilir olduğunu kontrol et.

> Not: Bir arama yeterli sonuç verdiyse başka araçla aynı aramayı tekrarlama.

## Bilinen bir URL'nin içeriğini okumak
**Tetikleyici:** Kullanıcı bir URL verdi veya aramada bulunan bir sayfanın tam içeriği gerekiyor.
Araçları bu sırayla değerlendir: firecrawl > duckduckgo (içerik çekme)

### 1. **firecrawl**
- **Amaç:** Sayfayı/sayfaları temiz Markdown olarak çekme, toplu scrape, yapılandırılmış veri çıkarma.
- **Ne zaman:** Birden çok sayfa toplanacak; Sayfadan tablo/liste gibi yapılandırılmış veri çıkarılacak; JavaScript ile yüklenen ama etkileşim gerektirmeyen sayfa
- **Ne zaman değil:** Tek bir basit sayfa (duckduckgo içerik çekme yeterli)
- **Nasıl:** Sadece gereken sayfaları/alanları iste
- **Doğrula:** Çekilen veride boş/eksik alan var mı kontrol et.

### 2. **duckduckgo (içerik çekme)**
- **Amaç:** Tek bir sayfanın metnini hızlıca okumak.
- **Ne zaman:** Tek bir URL'nin metni yeterli
- **Ne zaman değil:** Sayfa giriş/tıklama gerektiriyorsa (playwright)
- **Nasıl:** URL'yi doğrudan ver
- **Doğrula:** İçerik boş veya kısa geldiyse WebFetch ya da playwright ile tekrar dene.

> Not: Hiçbiri yoksa Claude Code'un kendi WebFetch aracını kullan.

## Tarayıcıda etkileşim
**Tetikleyici:** Tıklama, form doldurma, giriş yapma, ekran görüntüsü, JavaScript ile sonradan yüklenen içerik, bir web uygulamasını test etme, "sitede şunu yap".

### 1. **playwright**
- **Amaç:** Gerçek tarayıcıyla etkileşim ve web uygulaması testi.
- **Ne zaman:** Tıklama, form, giriş, dosya yükleme, ekran görüntüsü gerekiyor; İçerik yalnızca JavaScript çalışınca görünüyor ve diğer araçlar boş döndü; Kullanıcının geliştirdiği web uygulamasını test etmek veya görsel kontrol
- **Ne zaman değil:** Sadece metin okumak (arama/sayfa araçları); Giriş bilgisi/ödeme gerektiren işlemi kullanıcı onayı olmadan yapmak
- **Nasıl:** Eylem için önce sayfa anlık görüntüsünü (snapshot) al, öğeleri oradan seç; ekran görüntüsünü sadece görsel kontrol için kullan; Her adımdan sonra sayfanın beklenen duruma geldiğini kontrol et; İş bitince tarayıcıyı kapat
- **Doğrula:** Son durumun ekran görüntüsünü veya snapshot'ını al ve beklenen sonucu gösterdiğini kontrol et.

> Not: Sadece okumak için tarayıcı açma; arama/sayfa araçları daha hızlı ve ucuzdur.

## Yerel belge okuma
**Tetikleyici:** Uzantısı .pdf .docx .doc .xlsx .xls .pptx .ppt .html .epub .jpg .png olan bir dosyayı okumak, özetlemek, içinden veri çıkarmak.

### 1. **markitdown**
- **Amaç:** PDF, Office, HTML, resim dosyalarını Markdown'a çevirip okumak.
- **Ne zaman:** Desteklenen uzantılı bir dosya okunacak/özetlenecek/içinden veri çıkarılacak
- **Ne zaman değil:** Düz metin, Markdown, kod dosyaları; 5+ belge birlikte analiz edilecekse ve notebooklm kuruluysa
- **Nasıl:** Dosya yolunu tam yol / file:/// URI olarak ver; Büyük belgede önce başlıkları çıkar, sonra gereken bölümleri oku
- **Doğrula:** Tablo ve sayıları orijinal belgeyle karşılaştır; dönüştürmede bozulma varsa belirt.

> Not: Düz metin, Markdown ve kod dosyaları için dönüştürme gerekmez; doğrudan Read kullan.

## Çok sayıda kaynağı analiz etmek
**Tetikleyici:** 5+ belge/URL/YouTube videosu birlikte analiz edilecek; kaynaklı (alıntılı) karşılaştırma; bu kaynaklardan podcast, slayt, quiz, zihin haritası, çalışma notu istendi.

### 1. **notebooklm**
- **Amaç:** Çok kaynaklı analizi Google NotebookLM'e yaptırmak; podcast/slayt/quiz üretmek.
- **Ne zaman:** 5+ belge/URL/video birlikte analiz edilecek; Kaynaklı (alıntılı) cevap gerekiyor; Podcast, video özet, slayt, quiz, flashcard, zihin haritası istendi
- **Ne zaman değil:** Tek belge (markitdown); Gizli/kişisel veri içeren belgeler (Google'a yüklenir) - önce kullanıcıya sor
- **Nasıl:** Konuya özel bir notebook oluştur, kaynakları ekle, sorularını sor; ağır okumayı NotebookLM yapsın; Üretilen dosyaları indirip yerel klasöre kaydet
- **Doğrula:** Cevaplardaki alıntıların kaynakta gerçekten olduğunu kontrol et.

> Not: Tek bir belge için markitdown yeterli.

## Üzerinde çalıştığın projenin kodunu anlamak
**Tetikleyici:** "bu proje nasıl çalışıyor", "X nerede/nasıl kullanılıyor", "A ile B nasıl bağlı", mimari, akış, etki analizi, büyük bir değişiklikten önce keşif.

### 1. **graphify**
- **Amaç:** Projenin bilgi grafiği üzerinden kod/mimari sorgulama.
- **Ne zaman:** `graphify-out/graph.json` varsa: mimari, bağlantı, etki analizi soruları ve büyük değişiklik öncesi keşif (Grep/Glob'dan ÖNCE); Proje büyük (yüzlerce dosya) ve grafik yoksa: kullanıcıya bir kez `/graphify .` öner
- **Ne zaman değil:** Tek bir isim/dosya arıyorsan (Grep/Glob); Grafik yoksa kendiliğinden oluşturma (zaman ve token harcar)
- **Nasıl:** `graphify query "<soru>"` (genel), `graphify path A B` (iki şey nasıl bağlı), `graphify explain "X"` (bir kavram); Grafikten gelen dosya:satır bilgisiyle sadece ilgili dosyaları oku; Önemli kod değişikliklerinden sonra `/graphify . --update` öner
- **Doğrula:** Grafiğin gösterdiği bağlantıyı ilgili dosyayı okuyarak teyit et (grafik eski olabilir).

> Not: Tek bir isim/dosya arıyorsan Grep/Glob yeterli.

## Başka bir repoyu incelemek
**Tetikleyici:** Kullanıcı bir GitHub URL'si veya başka bir klasör verdi: "bu repo ne yapıyor", "buna bak", "işime yarar mı", "şu özelliği nasıl yapmışlar".
Araçları bu sırayla değerlendir: repomix > github

### 1. **repomix**
- **Amaç:** Başka bir repoyu tek bir yapay zeka dostu dosyaya paketleyip incelemek.
- **Ne zaman:** Bir repo baştan anlaşılacak, değerlendirilecek veya özelliği incelenecek
- **Ne zaman değil:** Sadece tek dosya/issue/PR gerekiyorsa (github); Kendi projen (graphify / Grep)
- **Nasıl:** Büyük repolarda include/ignore desenleriyle daralt (örn. sadece src, docs); Paketin tamamını okuma; içinde ara ve sadece gereken bölümleri oku; Önce README + dizin yapısı + giriş noktası
- **Doğrula:** Lisansı ve son güncelleme tarihini kontrol et; iddiaları koddan teyit et.

### 2. **github**
- **Amaç:** Başka bir repoda tek dosya, issue veya PR'a bakmak.
- **Ne zaman:** Sadece belirli bir dosya, issue, PR, release gerekiyor
- **Ne zaman değil:** Repo baştan anlaşılacaksa (repomix)
- **Nasıl:** Doğrudan ilgili dosyayı/issue'yu iste
- **Doğrula:** Doğru dalı/sürümü okuduğunu kontrol et.

## GitHub işlemleri
**Tetikleyici:** Issue, pull request, inceleme yorumu, Actions/CI sonucu veya logu, release, GitHub'da kod arama.

### 1. **github**
- **Amaç:** Issue/PR okuma-oluşturma, yorum, inceleme, Actions/CI sonucu ve logları, kod arama.
- **Ne zaman:** İstek GitHub'daki bir nesneyle ilgili (issue, PR, CI, release)
- **Ne zaman değil:** Yerel dosya okuma/yazma, commit, push (yerel git); Kullanıcı istemeden issue/PR/yorum oluşturmak
- **Nasıl:** CI hatasında önce başarısız işin logunun son kısmını oku
- **Doğrula:** Oluşturduğun/değiştirdiğin nesnenin bağlantısını kullanıcıya ver.

> Not: Yerel dosyaları okumak/yazmak ve commit/push için GitHub MCP değil yerel git ve dosya araçlarını kullan.

## Karmaşık, çok adımlı problem
**Tetikleyici:** Birbirine bağlı çok sayıda karar, birden fazla geçerli çözüm, belirsiz gereksinim, zor hata ayıklama.

### 1. **sequential-thinking**
- **Amaç:** Adım adım, revize edilebilir plan kurma.
- **Ne zaman:** Birbirine bağlı 3+ karar veya birden fazla geçerli çözüm var; Zor, sebebi belirsiz hata
- **Ne zaman değil:** Basit, tek adımlı işler
- **Nasıl:** Planı adımlara böl, her adımın doğrulama ölçütünü yaz
- **Doğrula:** Plan bittiğinde her adımın ölçütünün karşılandığını kontrol et.

## Kod yazma davranışı ve iş akışı
**Tetikleyici:** Her kod yazma, düzeltme, refactor isteği.
Araçları bu sırayla değerlendir: karpathy ilkeleri > superpowers

### 1. **karpathy ilkeleri**
- **Amaç:** Her kod değişikliğinde uygulanacak 4 ilke.
- **Ne zaman:** Her kod yazma, düzeltme, refactor
- **Nasıl:** Belirsizlikte varsayma, sor veya seçenekleri göster; İstenenden fazlasını yazma; en basit çözüm; Sadece işin gerektirdiği satırlara dokun; ilgisiz kodu değiştirme; Başarı ölçütünü (tercihen bir test) önce tanımla, sağlanana kadar devam et
- **Doğrula:** Değişen her satır isteğe bağlanabilmeli; test/çalıştırma ile sonucu göster.

### 2. **superpowers**
- **Amaç:** Büyük işler için süreç skill'leri.
- **Ne zaman:** Yeni özellik, çok dosyalı değişiklik, zor hata
- **Ne zaman değil:** Tek satırlık/küçük değişiklikler
- **Nasıl:** Beyin fırtınası → plan yazma → test önce → sistematik hata ayıklama → kod inceleme
- **Doğrula:** Planın her maddesi tamamlandı ve testler geçiyor.

## Var olan bir uygulamaya benzer ürün yapmak
**Tetikleyici:** "şu uygulamanın benzerini/klonunu yap", "X gibi bir uygulama", rakip analizi + yeniden yapım.

### 1. **replica-skill**
- **Amaç:** Var olan bir uygulamanın işlevini sıfırdan yeniden kurmak.
- **Ne zaman:** "X'in benzerini/klonunu yap", rakip uygulama incelemesi + yeniden yapım
- **Ne zaman değil:** Orijinalin kodunu, logosunu, metnini, içeriğini kopyalamak (yasak); Sıfırdan özgün uygulama (normal geliştirme)
- **Nasıl:** Skill'leri SIRAYLA: recon → architect → design → build → backend → test → diff → entrepreneur → brand → launch → deploy; Her adım `replica/` klasöründeki önceki çıktıyı okur; adım atlama
- **Doğrula:** `diff` adımındaki benzerlik puanı ve eksikler listesiyle ilerlemeyi ölç.

## Video ve animasyon üretmek
**Tetikleyici:** "video", "tanıtım", "promo", "reels/shorts", "animasyon", "çizgi film", "eğitim videosu", "konu anlatım videosu".
Araçları bu sırayla değerlendir: video-seslendirme skill'i > HyperFrames > video-shotcraft > claude-code-video-toolkit > ClaudeAnimationBase

### 1. **video-seslendirme skill'i**
- **Amaç:** Adım adım rehber/eğitim/bilgilendirme videosu üretmek (marka tasarımlı sahneler + Emel seslendirme + senkron altyazı) veya hazır sessiz videoya seslendirme ve altyazı eklemek.
- **Ne zaman:** "X nasıl yapılır videosu", müşteri rehberi, adım adım anlatım, kısa dikey bilgilendirme videosu; Kullanıcı bir video verip seslendirme/altyazı/konuşma metni istiyor; Ekran görüntülerinden adım adım video; Gerçekçi görüntü gereken anlatım (pano ölçümü, yangın dolabı muayenesi): klipler Gemini (Veo) ile kullanıcının kendi kotasıyla üretilir, skill istemleri hazırlar ve klipleri işler
- **Ne zaman değil:** Serbest hareketli grafik/animasyonlu tanıtım (HyperFrames); Karakter animasyonu (ClaudeAnimationBase)
- **Nasıl:** `~/.claude/skills/video-seslendirme/SKILL.md` iş akışını izle (A: sıfırdan, B: hazır video); Önce `gorsel` ile sessiz önizleme üret ve görselleri Read ile kontrol et, sonra `olustur`/`uret`; Kişisel veriyi ekrana ve seslendirmeye koyma; gizli metinde `motor: piper`
- **Doğrula:** `kontrol.png` ve 'siyah ara: 0' / 'Hikaye/durum: UYGUN' satırlarına bak; Veo kliplerinin kontrol karelerinde KKD ve uygulama doğruluğunu incele; telaffuzu kullanıcıya dinlet.

### 2. **HyperFrames**
- **Amaç:** HTML/CSS/GSAP sahnelerinden MP4 video: eğitim, konu anlatımı, bilgilendirme, altyazılı ve seslendirmeli video.
- **Ne zaman:** Konu anlatım / eğitim / İSG bilgilendirme videosu, slayt + seslendirme videosu, kinetik yazı, altyazılı kısa video; Şirket adına veya ticari kullanılacak her video (Remotion lisansı gerekmez); Bir web sitesini videoya dönüştürme
- **Ne zaman değil:** Karakter animasyonu/çizgi film (ClaudeAnimationBase); HeyGen hesabı gerektiren özellikler (Voice Turbo, müzik kataloğu, AI görsel/video üretimi): kullanıcı açıkça istemedikçe kullanma — ücretsiz kota sınırlı
- **Nasıl:** `/hyperframes:hyperframes` ile kompozisyonu yaz; CLI işleri (init, lint, preview, render) `npx hyperframes ...`; Türkçe seslendirmeyi HyperFrames'in kendi TTS'iyle değil edge-tts/Piper ile üret (yerel Kokoro Türkçe desteklemez); ses dosyasını ve SRT'yi kompozisyona ekle; Sahne süresini ses süresine göre ayarla; önce `npx hyperframes preview`, onaydan sonra render
- **Doğrula:** `npx hyperframes lint` temiz olmalı; render sonrası `ffprobe` ile süre/çözünürlük ve birkaç kareyi (`ffmpeg -ss <sn> -i video.mp4 -frames:v 1 kare.png`) kontrol et: metin taşması, boş kare, ses-görüntü senkronu.

### 3. **video-shotcraft**
- **Amaç:** Ürün/uygulama/site tanıtım ve promo videosu (hareketli grafik, müzik senkronu).
- **Ne zaman:** Bir ürünün, uygulamanın veya sitenin tanıtım/promo/özellik videosu; Gerçek ekran görüntülerinden hareketli video
- **Ne zaman değil:** Karakter animasyonu/çizgi film (ClaudeAnimationBase); Gerçek kamera görüntüsü düzenleme; Şirket adına (3+ çalışanlı kurum) ticari video: Remotion ücretli lisans ister → HyperFrames
- **Nasıl:** Önce ekranları yakala ve storyboard'u kullanıcıya göster, onaydan sonra render et
- **Doğrula:** Render edilen karelerden örnekler al ve kontrol et (metin taşması, boş kare, senkron).

### 4. **claude-code-video-toolkit**
- **Amaç:** Seslendirmeli, müzikli, AI görsel/klip içeren videolar.
- **Ne zaman:** Seslendirme/anlatım, müzik veya AI görsel gereken açıklayıcı video, kısa dikey video, reklam
- **Ne zaman değil:** Bulut GPU hesabı kurulmadıysa AI ses/görsel adımları (önce /setup); Şirket adına (3+ çalışanlı kurum) ticari video: Remotion ücretli lisans ister → HyperFrames
- **Nasıl:** Kendi klasöründe (`ClaudeProjeler\claude-code-video-toolkit`) çalışır; başka klasördeysen kullanıcıya orada açmasını söyle; `/video` ile şablondan başla
- **Doğrula:** Sahne sahne inceleme (`/scene-review`) yap.

### 5. **ClaudeAnimationBase**
- **Amaç:** El çizimi/suluboya tarzı karakter animasyonu ve kısa çizgi film.
- **Ne zaman:** Karakterli animasyon, çizgi film, hikâye anlatan kısa animasyon
- **Ne zaman değil:** Ürün tanıtımı (video-shotcraft)
- **Nasıl:** Kendi klasöründe (`ClaudeProjeler\ClaudeAnimationBase`) çalışır; önce ANIMATION_GUIDE.md okunur; GPU yoksa suluboya dolgularını azalt (render yavaş)
- **Doğrula:** Kontak sayfası (contact sheet) render edip kareleri kontrol et.

> Not: Videonun türüne göre TEK araç seç; aynı videoda araçları karıştırma. Şirket/ticari video (3+ çalışanlı kurum adına) Remotion tabanlı araçlarla (video-shotcraft, claude-code-video-toolkit) yapılmaz — Remotion bu durumda ücretli lisans ister; HyperFrames kullan. Seslendirme gerekiyorsa sesi 'Seslendirme' bölümündeki araçlarla üret.

## Metni seslendirmek (Türkçe TTS)
**Tetikleyici:** "seslendir", "sesli anlatım", "voiceover", "dış ses", "metni oku", "TTS", "podcast", videoya anlatıcı sesi.
Araçları bu sırayla değerlendir: Gemini TTS (video-seslendirme skill'i) > edge-tts > Piper

### 1. **Gemini TTS (video-seslendirme skill'i)**
- **Amaç:** En akıcı Türkçe seslendirme (Google Gemini TTS, ücretsiz kotalı).
- **Ne zaman:** GEMINI_API_KEY tanımlıysa video seslendirmesinde varsayılan (senaryoda `motor: otomatik` veya `gemini`)
- **Ne zaman değil:** Gizli/kurum içi metin (Google'a gider) → Piper; Kelime kelime senkron altyazı kritikse (Gemini kelime zamanı vermez; altyazı cümle süresine oranlanır) → edge
- **Nasıl:** Senaryoda `"motor": "gemini"` (veya `otomatik`), `"gemini_ses": "Kore"` (kadın, net). Diğer sesler: Aoede, Leda, Sulafat (sıcak), Puck, Charon (erkek); Üslup `gemini_uslup` ile verilir (örn. 'Sakin ve güven veren bir eğitmen gibi oku'); Tüm metin tek istekte gider (kota dostu); kota dolarsa araç otomatik Emel'e geçer
- **Doğrula:** Çıktıdaki 'Ses motoru' satırına ve UYARI'lara bak; Gemini'nin cümle atlamadığını sahne süreleriyle kontrol et.

### 2. **edge-tts**
- **Amaç:** Metinden doğal Türkçe ses (MP3) ve kelime zamanlı altyazı (SRT) üretmek.
- **Ne zaman:** Video anlatımı, dış ses, eğitim/konu anlatımı, sesli özet — internet varsa her Türkçe seslendirmede ilk seçim; Altyazı da gerekiyorsa (SRT'yi aynı komut verir)
- **Ne zaman değil:** İnternet yok ya da metin gizli/kurum içi (Microsoft sunucusuna gider) → Piper; Tek kelimelik kısa test için uzun metin gönderme
- **Nasıl:** Ses: `edge-tts --voice tr-TR-EmelNeural --file metin.txt --write-media ses.mp3 --write-subtitles ses.srt` (erkek ses: tr-TR-AhmetNeural); Kısa metin: `--text "..."`; uzun metinde her zaman `--file` kullan (tırnak/satır sorunu olmaz); Hız/ton: `--rate=-5%` (eğitimde biraz yavaş), `--pitch=+0Hz`; seslerin listesi: `edge-tts --list-voices` çıktısında `tr-TR`; Videoda sahne başına ayrı dosya üret; sahne süresini ses süresine göre ayarla; metin.txt dosyasını UTF-8 kaydet (Türkçe karakterler bozulmasın)
- **Doğrula:** `ffprobe -v error -show_entries format=duration -of csv=p=0 ses.mp3` ile süreyi kontrol et (0 veya çok kısa ise hata); SRT'nin son zamanı ses süresiyle uyumlu olmalı; Türkçe karakterler (ç, ğ, ı, ö, ş, ü) metinde doğru mu bak.

### 3. **Piper**
- **Amaç:** İnternetsiz, yerel Türkçe seslendirme (WAV).
- **Ne zaman:** İnternet yok, edge-tts hata verdi/limit; Metin gizli veya kurum içi (dışarı gönderilmemeli); Çok sayıda kısa ses dosyası (hızlı, yerel)
- **Ne zaman değil:** İnternet varsa ve en doğal ses isteniyorsa (edge-tts daha doğal); Kelime zamanlı altyazı gerekiyorsa tek başına yetmez (SRT üretmez; cümle sürelerinden hesapla)
- **Nasıl:** `piper -m "$env:PIPER_SESLER\tr_TR-dfki-medium.onnx" -i metin.txt -f ses.wav` (inen sesler: `dir $env:PIPER_SESLER`); Kısa metin: `piper -m <model> -f ses.wav "metin"`; Yavaşlatmak için `--length-scale 1.1`, cümle arası boşluk `--sentence-silence 0.3`; MP3 gerekirse: `ffmpeg -i ses.wav -b:a 128k ses.mp3`; metin.txt dosyasını UTF-8 kaydet (Türkçe karakterler bozulmasın)
- **Doğrula:** `ffprobe` ile süreyi kontrol et; sayılar ve kısaltmalar doğru okunuyor mu bak (gerekirse metinde yazıyla yaz: "%5" → "yüzde beş").

> Not: Sıra: edge-tts (internet varsa, en doğal ses) → Piper (internet yoksa / gizli metin) → Windows Tolga (hiçbiri yoksa; kurulum gerekmez: PowerShell `System.Speech`, ses tr-TR Tolga). Ses ve altyazıyı aynı kaynaktan üret; ses dosyası cümle cümle değil, bölüm bölüm (sahne başına bir dosya) üretilsin. Hazır bir VİDEOYA seslendirme + altyazı eklenecekse video-seslendirme skill'ini kullan (sahneleri ve senkronu o yapar).

## Slayt / sunum hazırlamak
**Tetikleyici:** "sunum", "slayt", "slides", "PowerPoint", "pptx", eğitim sunumu, videoda slayt sahnesi.

### 1. **Marp CLI**
- **Amaç:** Markdown'dan slayt/sunum üretmek (PDF, PPTX, HTML, PNG).
- **Ne zaman:** Sunum, eğitim slaytı, toplantı sunumu hazırlanacak; Video için slayt görselleri + konuşmacı notları (seslendirme metni) gerekiyor
- **Ne zaman değil:** Kullanıcı slaytı PowerPoint'te metin olarak düzenleyecekse: `--pptx` slaytları görsel olarak koyar; bunu söyle (düzenlenebilir PPTX için LibreOffice'li `--pptx-editable` deneysel); Hareketli/animasyonlu sahne gerekiyorsa (HyperFrames)
- **Nasıl:** Dosya başına `---\nmarp: true\n---`; slaytlar `---` ile ayrılır; konuşmacı notu `<!-- ... -->`; PDF: `marp sunum.md --pdf`; PowerPoint: `marp sunum.md --pptx`; slayt başına PNG: `marp sunum.md --images png`; notlar: `marp sunum.md --notes`; Yerel resim kullanıyorsan `--allow-local-files` ekle
- **Doğrula:** PNG çıktısından birkaç slaytı aç/oku: metin taşması, Türkçe karakter, slayt sayısı beklenenle aynı mı.

> Not: İçeriği önce Markdown olarak yaz, sonra dönüştür; kullanıcı PowerPoint'te metni düzenleyecekse bunu baştan sor.
````
