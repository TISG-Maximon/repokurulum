# Araştırma ve düzenleme için faydalı açık kaynak repolar

Lisanslar GitHub API'sinden **2026-11-05** tarihinde kontrol edildi. "Uygulamada" sütunu, `RepoKurulum` uygulamasında tek tıkla kurulup kurulamadığını gösterir.

## 1. Araştırma / web

| Repo | Lisans | Ne işe yarar | Anahtar | Uygulamada |
|---|---|---|---|---|
| [upstash/context7](https://github.com/upstash/context7) | MIT | Claude'a kütüphanelerin **güncel** dokümanını ve kod örneklerini verir. Eski ya da uydurma API kullanımını azaltır. Promptta "use context7" demen yeterli. | Yok | ✅ varsayılan |
| [nickclyde/duckduckgo-mcp-server](https://github.com/nickclyde/duckduckgo-mcp-server) | MIT | DuckDuckGo ile web araması yapar, sonuç sayfasının içeriğini temiz metin olarak çeker. | Yok | ✅ varsayılan |
| [tavily-ai/tavily-mcp](https://github.com/tavily-ai/tavily-mcp) | MIT | Yapay zeka için tasarlanmış arama: arama, sayfa çıkarma, site haritası, crawl. Kaynaklı derin araştırma için iyi. | Var (ücretsiz kota) | ✅ opsiyonel |
| [exa-labs/exa-mcp-server](https://github.com/exa-labs/exa-mcp-server) | MIT | Anlamsal (anlama dayalı) web araması; makale, şirket, kod araması. "Şuna benzeyen kaynakları bul" türü sorgularda güçlü. | Var | ✅ opsiyonel |
| [firecrawl/firecrawl-mcp-server](https://github.com/firecrawl/firecrawl-mcp-server) | MIT | Siteleri tarayıp temiz Markdown'a çevirir; toplu scrape ve yapılandırılmış veri çıkarır. | Var | ✅ opsiyonel |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | MIT | Python ile yapay zeka tarayıcı ajanı. Playwright MCP'ye alternatif; kendi betiklerinde tarayıcı otomasyonu için. | LLM anahtarı | ❌ (kütüphane) |

## 2. Belge okuma / dönüştürme / düzenleme

| Repo | Lisans | Ne işe yarar | Uygulamada |
|---|---|---|---|
| [microsoft/markitdown](https://github.com/microsoft/markitdown) | MIT | PDF, Word, Excel, PowerPoint, HTML, resim ve ses dosyalarını Markdown'a çevirir; Claude bunları okuyup özetleyebilir. `markitdown-mcp` ile MCP olarak çalışır. | ✅ varsayılan |
| [docling-project/docling](https://github.com/docling-project/docling) | MIT | Gelişmiş belge ayrıştırma: tablolar, sayfa düzeni, formüller, OCR. Taranmış veya karmaşık PDF'lerde MarkItDown'dan daha iyi sonuç verir. MCP sürümü: [docling-mcp](https://github.com/docling-project/docling-mcp) (MIT). | ❌ (ağır, elle) |
| [GongRzhe/Office-Word-MCP-Server](https://github.com/GongRzhe/Office-Word-MCP-Server) | MIT | Word (.docx) belgesi oluşturur ve **düzenler**: paragraf, tablo, biçim, yorum. | ❌ (elle) |
| [zcaceres/markdownify-mcp](https://github.com/zcaceres/markdownify-mcp) | MIT | YouTube altyazısı, PDF, web sayfası gibi kaynakları Markdown'a çevirir. | ❌ (derleme gerekir) |
| [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) | MIT | Obsidian kasası (vault), Markdown not formatları ve Obsidian CLI kullanımını öğreten skill'ler. Not ve araştırma arşivi tutanlar için. | ❌ (skill) |

## 3. Kod ve repo

| Repo | Lisans | Ne işe yarar | Uygulamada |
|---|---|---|---|
| [yamadashy/repomix](https://github.com/yamadashy/repomix) | MIT | Bir repoyu (yerel veya GitHub) tek, yapay zeka dostu bir dosyaya paketler. "Şu repoyu incele" isteklerinde Claude'a bütün resmi verir. | ✅ varsayılan |
| [github/github-mcp-server](https://github.com/github/github-mcp-server) | MIT | GitHub'ın resmi MCP sunucusu: issue, PR, kod arama, Actions. | ✅ opsiyonel (token) |
| [wonderwhy-er/DesktopCommanderMCP](https://github.com/wonderwhy-er/DesktopCommanderMCP) | MIT | Claude Desktop'a terminal, dosya arama ve diff ile düzenleme yeteneği verir. Claude Code'da bunlar zaten yerleşik, asıl faydası Desktop uygulamasında. | ❌ |
| [czlonkowski/n8n-mcp](https://github.com/czlonkowski/n8n-mcp) | MIT | n8n otomasyon iş akışlarını Claude ile kurar ve düzenler. | ❌ |

## 4. Skill ve iş akışı paketleri

| Repo | Lisans | Ne işe yarar | Uygulamada |
|---|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | MIT | En popüler skill çerçevesi: beyin fırtınası → plan yazma → TDD → sistematik hata ayıklama → kod inceleme. Claude'u daha disiplinli çalıştırır. | ✅ opsiyonel |
| [wshobson/agents](https://github.com/wshobson/agents) | MIT | Çok sayıda hazır alt ajan (subagent) ve eklentiden oluşan bir pazar yeri: güvenlik, veri, belge yazımı, mimari vb. `claude plugin marketplace add wshobson/agents` | ❌ (seçerek kur) |
| [SuperClaude-Org/SuperClaude_Framework](https://github.com/SuperClaude-Org/SuperClaude_Framework) | MIT | Claude Code'a özel komutlar, "persona"lar ve araştırma modu ekleyen yapılandırma çerçevesi. | ❌ (pip ile) |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | MIT | Bilimsel araştırma skill'leri: literatür tarama, veri analizi, biyoinformatik veri tabanları. | ❌ |
| [OthmanAdi/planning-with-files](https://github.com/OthmanAdi/planning-with-files) | MIT | Uzun görevlerde planı Markdown dosyalarında tutar; oturum kopsa da kaldığı yerden devam eder. | ❌ |


## 5. Değerlendirme: 2026-11-08 eklenenler

Lisanslar GitHub API'sinden ve repolardaki LICENSE dosyalarından kontrol edildi.

| Repo | Lisans | Ne işe yarar | Gereken | Uygulamada |
|---|---|---|---|---|
| [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) | **Belirtilmemiş** (LICENSE dosyası yok) | Claude'un kod yazma davranışı için 4 ilke: varsaymadan sor, en basit çözüm, sadece gerekene dokun, başarıyı testle tanımla. Tek bir CLAUDE.md/skill. | Hiçbir şey | ✅ varsayılan (plugin) |
| [Jakeschincariol/replica-skill](https://github.com/Jakeschincariol/replica-skill) | MIT | 11 skill: bir uygulamayı incele → mimari → tasarım → kodla → backend → test → orijinalle karşılaştır → kullanıcı şikayetlerinden iyileştir → marka → yayın. İşlevi yeniden kurar, kodu/logoyu kopyalamaz. | Python 3.8+ | ✅ opsiyonel (plugin) |
| [teng-lin/notebooklm-py](https://github.com/teng-lin/notebooklm-py) | MIT | NotebookLM'i (yeni adı Gemini Notebook) Claude'dan kullanma: kaynak yükle, kaynaklı cevap al, podcast/video/slayt/quiz/zihin haritası üret ve indir. Ağır okumayı Google'a yaptırıp token tasarrufu sağlar. | Google hesabı (`notebooklm login`). **Gayriresmi API**: Google değiştirirse bozulabilir, yoğun kullanımda kısıtlanabilir. | ✅ opsiyonel |
| [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | Apache-2.0 | Ürün/uygulama tanıtım videosu: gerçek ekranlarını yakalar, 150 hazır hareket tarifinden seçer, Remotion ile render eder, müziğe senkronlar. API anahtarı yok. | Node, ffmpeg, uv. Remotion şirketler için ücretli lisans isteyebilir. | ✅ opsiyonel |
| [digitalsamba/claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit) | MIT | Tam video stüdyosu: senaryo, AI seslendirme (Qwen3-TTS/ElevenLabs), müzik, AI görsel/klip, render, YouTube'a yükleme. Kendi klasöründe çalışır (`/setup`, `/video`). | Node 22+, uv, ffmpeg. AI modelleri için bulut GPU (Modal'ın aylık 30$ ücretsiz kotası öneriliyor); ElevenLabs opsiyonel. | ✅ opsiyonel (klasöre klonlanır) |
| [JohnHeibel/ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase) | MIT | p5.js ile el çizimi/suluboya karakter animasyonu başlangıç kiti (Clawd karakteri, 31 duygu). Claude storyboard yapar, çizer, MP4 çıkarır. | Node, Chrome, ffmpeg. GPU yoksa render yavaş. | ✅ opsiyonel (klasöre klonlanır) |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | Apache-2.0 | HTML + GSAP ile video: eğitim/konu anlatımı, altyazılı ve seslendirmeli video, siteyi videoya çevirme. Claude eklentisi olarak kurulur (`/hyperframes:hyperframes`). Remotion'a ücretsiz alternatif: **şirket kullanımında lisans ücreti yok**. | Node, ffmpeg. HeyGen girişi isteyen özellikler (Voice Turbo, müzik kataloğu, AI üretim) ücretsiz kotayla sınırlı; kurallar bunları kullandırmaz. | ✅ opsiyonel |
| [rany2/edge-tts](https://github.com/rany2/edge-tts) | LGPL-3.0 | Metni doğal Türkçe sesle MP3'e çevirir (Emel, Ahmet) ve kelime zamanlı SRT altyazı verir. API anahtarı yok. | İnternet gerekir; metin Microsoft'un sunucusuna gider (gizli metinde Piper). Resmi olmayan kullanım: Microsoft değiştirirse bozulabilir. | ✅ opsiyonel |
| [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl) | GPL-3.0 | İnternetsiz, işlemcide çalışan Türkçe seslendirme (dfki, fahrettin, fettah sesleri). | Ses edge-tts kadar doğal değil; SRT üretmez. | ✅ opsiyonel |
| [marp-team/marp-cli](https://github.com/marp-team/marp-cli) | MIT | Markdown'dan sunum: PDF, PPTX, HTML, slayt başına PNG ve konuşmacı notları (videoda slayt sahnesi için). | Sistemdeki Edge/Chrome'u kullanır. `--pptx` slaytları görsel olarak koyar (metin düzenlenemez). | ✅ opsiyonel |

### Eklenmeyenler

| Repo | Neden |
|---|---|
| "jev" repoları ([dzhng/jevgrep](https://github.com/dzhng/jevgrep), [tamaratran/fast-jev-compaction](https://github.com/tamaratran/fast-jev-compaction), [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast)) | Jev, TypeSafe'in **ücretli** bir modeli. Üçü de TypeSafe (veya Vercel/OpenRouter) API anahtarı istiyor; jevgrep anahtarı ortam değişkeninden okumuyor, `jg auth` ile elle girilmesi gerekiyor. Ayrıca kaynak kodunu üçüncü taraf bir modele gönderiyorlar. graphify + Grep zaten aynı işi ücretsiz yapıyor. Hangisini kastettiğini söylersen ayrıca bakarım. |
| [tashfeenahmed/freellmapi](https://github.com/tashfeenahmed/freellmapi) (MIT) | 34 sağlayıcının ücretsiz kotalarını tek bir API'de toplayan bir yönlendirici. Claude Code'u Claude yerine bu ücretsiz modellere bağlamak için kullanılır; Claude aboneliğinle çalışırken bir faydası yok ve README'si kişisel deneme amaçlı olduğunu, sağlayıcı kullanım şartlarının ayrıca incelenmesi gerektiğini söylüyor. Kendi uygulamanda ücretsiz LLM API'si gerekirse Windows `.exe` kurulumu var. |
| [Vincentwei1021/video-talkcraft](https://github.com/Vincentwei1021/video-talkcraft) | **PolyForm Noncommercial** lisansı (ticari kullanım yasak), dokümanı Çince ve seslendirme için Fish Audio istiyor. Aynı yazarın video-shotcraft'ı daha uygun. |

## MIT olmayan ama kullandığımız (serbest lisanslı) araçlar
- [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp): **Apache-2.0**. Ticari kullanım serbest, lisans ve NOTICE metnini korumak gerekir.
- [safishamsi/graphify](https://github.com/safishamsi/graphify): README'ye göre Apache-2.0/MIT.
- [blazickjp/arxiv-mcp-server](https://github.com/blazickjp/arxiv-mcp-server): **Apache-2.0**. arXiv makalelerini arar, indirir ve okur; akademik araştırma için iyi.
- `modelcontextprotocol/servers` (sequential-thinking, fetch, filesystem): GitHub lisansı "NOASSERTION" gösteriyor; kullanmadan önce repodaki LICENSE dosyasına bak.

## Yeni bir aracı uygulamaya eklemek
`installer/bilesenler.json` dosyasına bir nesne ekle. Örnek (npx ile çalışan bir MCP):
```json
{
  "id": "ornek-mcp", "ad": "Ornek MCP", "kategori": "2. Tarayici ve arastirma",
  "lisans": "MIT", "repo": "https://github.com/...", "aciklama": "...",
  "varsayilan": false, "gerekir": ["node", "claude"],
  "kontrol": { "mcp": "ornek" },
  "kur": [ [ { "tur": "mcp", "ad": "ornek", "komut": ["npx", "-y", "ornek-mcp"] } ] ]
}
```
Adım türleri: `winget`, `ps`, `calistir`, `uvtool`, `mcp`, `mcp-http`, `ortam`. Kontrol türleri: `komut`, `dosya`, `mcp`, `plugin`, `ortam`.
