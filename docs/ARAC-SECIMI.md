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
"kurallar": [ { "ihtiyac": "arama", "oncelik": 2, "metin": "**ornek**: Ne zaman kullanılacağı..." } ]
```
`ihtiyac` değerleri: `dokuman` (Kütüphane / framework / API dokümanı), `arama` (Web araması ve güncel bilgi), `sayfa` (Bilinen bir URL'nin içeriğini okumak), `tarayici` (Tarayıcıda etkileşim (tıklama, form, giriş, ekran görüntüsü)), `belge` (Yerel belge okuma (PDF, Word, Excel, PowerPoint, resim)), `proje` (Üzerinde çalıştığın projenin kodunu anlamak), `dis-repo` (Başka bir repoyu incelemek), `github` (GitHub işlemleri (issue, PR, inceleme, Actions)), `dusunme` (Karmaşık, çok adımlı problem), `is-akisi` (Geliştirme iş akışı). Aynı ihtiyaçta `oncelik` küçük olan önce denenir.

---

## Tüm araçlar kuruluyken üretilen metin

````markdown
# Araç seçim kuralları

- Kullanıcı bir aracı adıyla isterse her zaman onu kullan; aşağıdaki sıra sadece varsayılandır.
- Her ihtiyaç için araçları listedeki SIRAYLA düşün; ilk araç yeterli sonuç verdiyse dur, aynı işi başka araçla tekrarlama.
- Bir araç hata verirse, kota dolduysa veya bağlı değilse listedeki bir sonrakine geç; hiçbiri yoksa Claude Code'un kendi araçlarını (WebSearch, WebFetch, Read, Grep, Glob) kullan.
- Yerel dosyalar için Read/Grep/Glob/Edit; internet, tarayıcı ve dış servisler için MCP araçları.
- Anahtarlı araçlar (exa, tavily, firecrawl, github) kota tüketir: gereksiz tekrar ve çok geniş sorgulardan kaçın.
- Hangi aracı neden seçtiğini uzun uzun anlatma; işi yap, kullandığın kaynağı belirt.

## Kütüphane / framework / API dokümanı
1. **context7**: Bir kütüphane, framework, SDK veya API kullanırken ÖNCE context7 ile güncel dokümanı ve örnekleri al. Sürüm belirtilmişse o sürümün dokümanını iste.
- Kod yazarken bir paketin nasıl kullanıldığından emin değilsen ezberden yazma.

## Web araması ve güncel bilgi
1. **exa**: Varsayılan arama aracı. Kaynak, makale, şirket, kod örneği bulma ve "buna benzer" aramalar.
2. **tavily**: Kaynak gösterilmesi gereken DERİN araştırmada veya bir siteyi baştan sona taramak (crawl/map) gerektiğinde.
3. **duckduckgo**: Ücretsiz ve anahtarsız genel arama. Bu başlıkta üstünde başka bir arama aracı varsa onun yedeğidir (kota bittiğinde, hata verdiğinde veya basit/hızlı bir arama yeterliyse).
- Bir arama yeterli sonuç verdiyse başka araçla aynı aramayı tekrarlama.

## Bilinen bir URL'nin içeriğini okumak
1. **firecrawl**: Bir veya birden çok sayfayı temiz Markdown olarak çekmek, toplu scrape, sayfadan yapılandırılmış veri çıkarmak.
2. **duckduckgo** (içerik çekme): Tek bir sayfanın metnini hızlıca okumak için.
- Hiçbiri yoksa Claude Code'un kendi WebFetch aracını kullan.

## Tarayıcıda etkileşim (tıklama, form, giriş, ekran görüntüsü)
1. **playwright**: SADECE sayfayla etkileşim gerektiğinde: tıklama, form doldurma, giriş yapma, ekran görüntüsü, JavaScript ile sonradan yüklenen içerik, bir web uygulamasını test etmek. İş bitince tarayıcıyı kapat.
- Sadece okumak için tarayıcı açma; yukarıdaki arama/sayfa araçları daha hızlı ve ucuzdur.

## Yerel belge okuma (PDF, Word, Excel, PowerPoint, resim)
1. **markitdown**: PDF, Word, Excel, PowerPoint, HTML ve resim dosyalarını önce Markdown'a çevir, sonra oku. Büyük belgede önce içindekiler/başlıkları çıkar, gerekeni oku.
- Düz metin, Markdown ve kod dosyaları için dönüştürme gerekmez; doğrudan Read kullan.

## Üzerinde çalıştığın projenin kodunu anlamak
1. **graphify**: Projede `graphify-out/graph.json` varsa geniş Grep/Glob aramalarından ÖNCE `graphify query "<soru>"`, `graphify path A B` veya `graphify explain "X"` kullan. Grafik yoksa ve proje büyükse kullanıcıya `/graphify .` öner; kendiliğinden çalıştırma (zaman ve token harcar).
- Tek bir isim/dosya arıyorsan Grep/Glob yeterli.

## Başka bir repoyu incelemek
1. **repomix**: Başka bir repoyu (GitHub URL veya yerel klasör) baştan anlamak için paketle. Büyük repolarda include/ignore desenleriyle daralt; çıktının tamamını okumaya çalışma, önce yapıyı ve ana dosyaları incele.
2. **github**: Başka bir repoda yalnızca tek bir dosyaya, issue'ya veya PR'a bakmak yeterliyse (tüm repoyu paketlemeye gerek yoksa).

## GitHub işlemleri (issue, PR, inceleme, Actions)
1. **github**: Issue/PR okuma-oluşturma, yorum, kod inceleme, Actions/CI sonuçları ve logları, GitHub'da kod arama.
- Yerel dosyaları okumak/yazmak ve commit için GitHub MCP değil yerel git ve dosya araçlarını kullan.

## Karmaşık, çok adımlı problem
1. **sequential-thinking**: Yalnızca çok adımlı ve belirsiz problemlerde (mimari karar, zor hata ayıklama, birbirine bağlı çok değişiklik) adım adım plan kurmak için. Basit işlerde kullanma.

## Geliştirme iş akışı
1. **superpowers** skill'leri: Yeni özellik veya hata düzeltme işlerinde ilgili skill'i izle (beyin fırtınası → plan yazma → test önce → sistematik hata ayıklama → kod inceleme). Tek satırlık küçük değişikliklerde süreci uzatma.
````
