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
