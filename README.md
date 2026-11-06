# repokurulum

Windows bilgisayarda **Claude Code + Playwright MCP + graphify** ve araştırma/belge MCP'lerini kuran **kurulum uygulaması**, betikler ve çalışma mantığının anlatımı.

## ⚡ Herhangi bir PC'de en hızlı yol (tek satır)

**PowerShell** aç (Başlat → "PowerShell"), şunu yapıştır, Enter:
```powershell
irm https://raw.githubusercontent.com/TISG-Maximon/repokurulum/HEAD/bootstrap.ps1 | iex
```
Kurulum penceresi açılır → **Seçilenleri Kur** → bitince **Claude'u Aç (giriş)** → tarayıcıda giriş. Elle yapman gereken bu kadar.

| Elle yapman gereken | Neden otomatik olamıyor |
|---|---|
| Tek satırı yapıştırmak | Bir şeyin başlatması gerekiyor |
| winget kuruluyorsa 1–2 UAC "Evet" | Node/Git/Chrome tüm kullanıcılara kurulur; Windows izin ister |
| Claude'a tarayıcıdan giriş | Hesap güvenliği; bunu sadece sen yapabilirsin |
| (Opsiyonel) API anahtarları | Tavily/Exa/Firecrawl/GitHub senin hesabına bağlı; uygulama pencerede sorar, istersen kalıcı kaydeder |

Diğer başlatma yolları:
- **`RepoKurulum.exe`**: GitHub → Actions → son "derle-ve-test" çalışması → *RepoKurulum-exe* artifact'ı (veya `v*` etiketi atılınca Releases). Tek dosya; USB'yle taşıyabilirsin. İmzasız olduğu için SmartScreen "Yine de çalıştır" der.
- **`RepoKurulum.bat`**: repo indirildiyse çift tıkla.
- **Sessiz / uzaktan** (pencere yok, varsayılanları kurar): `RepoKurulum.bat -Sessiz` veya
  ```powershell
  $env:REPOKURULUM_SESSIZ='1'; irm https://raw.githubusercontent.com/TISG-Maximon/repokurulum/HEAD/bootstrap.ps1 | iex
  ```
- **Durum listesi**: `RepoKurulum.bat -Liste`
- **Claude Code'u açmak**: `ClaudeAc.bat`'a çift tıkla (klasör ve "yeni / devam / eski konuşma" sorar) ya da bir klasörü üzerine sürükle-bırak. Masaüstüne kopyalayabilirsin.

### Uygulamanın hata azaltma özellikleri
- Her bileşen önce **kontrol edilir**; kuruluysa atlanır (tekrar çalıştırmak güvenli).
- Her bileşenin **alternatif kurulum yolu** var (örn. Claude: resmi installer → npm; uv: winget → resmi script).
- **Bağımlılıklar otomatik** seçilir ve doğru sırayla kurulur.
- npx paketleri **önceden indirilir**; MCP ilk açılışta zaman aşımına düşmez.
- MCP komutları Windows kuralına göre **otomatik** `cmd /c` ile sarılır; uv araçları **tam yol** ile kaydedilir.
- Her çalıştırma `%LOCALAPPDATA%\RepoKurulum\logs\` içine log yazar.
- GitHub Actions her push'ta uygulamayı **gerçek bir Windows makinesinde** sessiz modda kurar, ikinci çalıştırmanın her şeyi atladığını doğrular ve exe'yi derler.

Hangi araçların neden seçildiği: **[docs/MIT-REPOLAR.md](docs/MIT-REPOLAR.md)**. Claude'un hangi işte hangi aracı kullanacağı (CLAUDE.md'ye kendin yapıştırırsın): **[docs/ARAC-SECIMI.md](docs/ARAC-SECIMI.md)**. Yeni araç eklemek: `installer/bilesenler.json`.

---

```
repokurulum/
├── bootstrap.ps1            ← tek satırlık kurulumun indirdiği başlatıcı (exe'nin kaynağı)
├── RepoKurulum.bat          ← KURULUM UYGULAMASI (pencereli)
├── installer/
│   ├── RepoKurulum.ps1      ← uygulama + kurulum motoru
│   └── bilesenler.json      ← bileşen listesi (buradan genişletilir)
├── docs/MIT-REPOLAR.md      ← araştırma/düzenleme repoları özeti
├── .github/workflows/       ← Windows'ta otomatik test + exe derleme
├── kurulum.bat              ← eski/yedek betik (uygulama açılmazsa)
├── scripts/
│   ├── mcp-ekstra.bat       ← context7, sequential-thinking, GitHub MCP (opsiyonel)
│   ├── graphify-proje.bat   ← bir projede graphify hook + graphify MCP'yi açar
│   └── dogrula.bat          ← kurulumu kontrol eder (hiçbir şey değiştirmez)
├── ornek-mcp-windows.json  ← proje kapsamlı .mcp.json örneği (Windows, Playwright)
├── CLAUDE.md                ← Claude'a bu repoda nasıl davranacağını söyler
└── logs/kurulum.log         ← her çalıştırmada oluşur (git'e girmez)
```

---

## 1. Ne kuruluyor?

| Araç | Neden gerekli | Nasıl kuruluyor |
|---|---|---|
| **Git for Windows** | Repo klonlama; Claude Code Windows'ta Git Bash'i kabuk olarak kullanır | `winget install Git.Git` |
| **Node.js LTS** | `npx` → Playwright MCP ve diğer npm tabanlı MCP sunucuları | `winget install OpenJS.NodeJS.LTS` |
| **uv** (Astral) | graphify'i izole Python 3.12 ile kurar (sistem Python'una dokunmaz) | `winget install astral-sh.uv` |
| **Google Chrome** | Playwright MCP varsayılan olarak sistemdeki Chrome'u sürer | `winget install Google.Chrome` |
| **Claude Code** | Ana ajan (CLI) | resmi native installer, olmazsa `npm i -g @anthropic-ai/claude-code` |
| **Playwright MCP** (`@playwright/mcp`) | Claude'un tarayıcı açıp tıklama/doldurma/ekran görüntüsü yapması | `claude mcp add -s user playwright -- cmd /c npx -y @playwright/mcp@latest` |
| **graphify** (`graphifyy` paketi) | Kod tabanını bilgi grafiğine çevirir; `/graphify` skill'i | `uv tool install "graphifyy[mcp,pdf,office]"` + `graphify install` |

> ⚠️ graphify'in PyPI paket adı **`graphifyy`** (çift y). `graphify` adlı diğer PyPI paketleri resmi değildir. Komut adı yine `graphify`.

---

## 2. Çalışma mantığı (Skill, MCP, Hook, CLAUDE.md)

Claude Code'a yetenek eklemenin 4 yolu var; bu repo dördünü de kullanır:

### 2.1 MCP sunucusu (Model Context Protocol)
- Claude'un yanında çalışan **ayrı bir süreçtir**; Claude'a yeni **araçlar (tool)** verir.
- Örn. Playwright MCP → `browser_navigate`, `browser_click`, `browser_snapshot`, `browser_take_screenshot` …
- Claude Code her açılışta kayıtlı sunucuları başlatır (`stdio`: komut çalıştırır; `http`: uzak URL'ye bağlanır).
- **Kapsamlar (scope)** — öncelik sırası yukarıdan aşağı:

| Scope | Nerede saklanır | Kimi etkiler |
|---|---|---|
| `local` (varsayılan) | `~\.claude.json` içinde, o klasöre özel | Sadece sen, sadece o klasör |
| `project` | Repo kökünde `.mcp.json` (git'e girer) | Repoyu klonlayan herkes (ilk açılışta onay sorar) |
| `user` | `~\.claude.json` (global) | Sen, tüm projeler |

`kurulum.bat` Playwright'ı **user** kapsamında ekler → her projede çalışır. `ornek-mcp-windows.json` proje kapsamına örnektir; bir Windows projesinde kullanmak istersen adını `.mcp.json` yap.

> ⚠️ Bu repoda bilerek gerçek bir `.mcp.json` **yok**: `project` kapsamı `user` kapsamını ezer ve `cmd /c` Linux/bulut oturumlarında `ENOENT: cmd` hatası verir.

- **Windows'a özel kural:** `npx` bir `.cmd` dosyasıdır; Claude Code onu doğrudan başlatamaz. Bu yüzden komut **`cmd /c npx ...`** şeklinde verilir. (En sık yapılan hata budur: "Connection closed".)

### 2.2 Skill
- Bir klasördeki `SKILL.md` dosyası (+ yardımcı dosyalar). Claude ilgili iş geldiğinde talimatları yükler; kullanıcı `/skilladi` ile de çağırabilir.
- Konumlar: `~\.claude\skills\<ad>\SKILL.md` (global) veya `<proje>\.claude\skills\<ad>\SKILL.md` (proje).
- `graphify install` → `/graphify` skill'ini Claude Code'a kaydeder.

### 2.3 Hook
- Belirli olaylarda (ör. **PreToolUse** = bir araç çalışmadan hemen önce) otomatik çalışan komut. `settings.json` içinde tanımlanır.
- `graphify claude install` (proje içinde) bir PreToolUse hook'u ekler: Claude **Grep/Glob/Read ile dosya taramadan önce** grafiği sorgular → daha az token, daha isabetli gezinme.

### 2.4 CLAUDE.md
- Proje kökündeki kalıcı talimat dosyası; her oturumda otomatik okunur. "Bu repoda şöyle çalış" kurallarını buraya yazarsın.

### 2.5 graphify akışı
```
/graphify .            →  graphify-out/graph.json, GRAPH_REPORT.md, graph.html
graphify query "..."   →  grafikte soru sor
graphify path A B      →  iki kavram arasındaki bağlantı yolu
graphify explain "X"   →  bir kavramı açıkla
```
- Kod, yerelde **tree-sitter** ile çözümlenir (internet/anahtar gerekmez).
- PDF/doküman/görsel kavram çıkarımı Claude (veya bir LLM backend'i) üzerinden yapılır.
- Grafik oluştuktan sonra `scripts\graphify-proje.bat` grafiği bir **MCP sunucusu** olarak da bağlar (`graphify-mcp …\graph.json`).

---

## 3. Uzaktan bağlantı senaryosu (sen başka PC'de, asıl PC uzakta)

Kurulum **asıl PC'de** yapılmalı (araçlar orada çalışacak). İki yol var:

### Yol A — Uzak masaüstü ile (RDP / AnyDesk / TeamViewer) — önerilen
1. Asıl PC'ye uzak masaüstüyle bağlan, **kendi kullanıcı hesabınla** oturum aç.
2. PowerShell ya da CMD aç ve repoyu indir:
   ```bat
   cd %USERPROFILE%
   git clone https://github.com/TISG-Maximon/repokurulum.git
   ```
   Git yoksa: GitHub'da **Code → Download ZIP**, ZIP'i aç (sağ tık → Özellikler → *Engellemeyi kaldır* işaretle, yoksa SmartScreen uyarısı çıkar).
3. `kurulum.bat`'a **çift tıkla** (Yönetici olarak *çalıştırma*; winget gerekirse kendisi UAC onayı ister).
4. Bitince **yeni** bir terminal aç → `claude` yaz → tarayıcı açılır, Anthropic hesabınla giriş yap.
   - Giriş tarayıcısı uzak PC'de açılır; uzak masaüstü penceresinden tamamla.
5. `claude` içinde `/mcp` → `playwright` **connected** görünmeli.
6. `scripts\dogrula.bat` ile son kontrol.

### Yol B — Web'den asıl PC'yi sürmek
Kurulum bittikten sonra, web/telefon üzerinden asıl PC'deki Claude Code'u kullanmak için asıl PC'de Claude masaüstü uygulamasında **Settings → Claude Code → Remote Control** açılabilir veya terminalde `claude remote-control` kullanılabilir. Böylece claude.ai/code üzerinden o makinedeki klasörde çalışırsın (Playwright tarayıcısı da o PC'de açılır).

> Playwright MCP varsayılan olarak **görünür** bir Chrome penceresi açar. Uzak masaüstü oturumu kapalı/kilitliyken sorun çıkarsa `--headless` kullan:
> `claude mcp add -s user playwright -- cmd /c npx -y @playwright/mcp@latest --headless`

---

## 4. `kurulum.bat` adım adım ne yapar?

1. **Ön kontrol:** Windows sürümü, yönetici uyarısı, `winget` var mı.
2. **Temel araçlar:** git, node, uv, Chrome — her biri önce `where` ile kontrol edilir, yoksa `winget` ile sessiz kurulur.
3. **PATH yenileme:** Her kurulumdan sonra PATH registry'den okunup aynı pencereye yüklenir (yeni terminal açmadan devam edebilmek için).
4. **Git ayarları:** `core.longpaths=true` (260 karakter yol sınırı hatası), `core.autocrlf=true`.
5. **Claude Code:** yoksa resmi installer (`irm https://claude.ai/install.ps1 | iex`), başarısızsa npm; varsa `claude update`.
6. **`MCP_TIMEOUT=60000`:** İlk açılışta `npx` paket indirirken MCP'nin zaman aşımına düşmesini engeller.
7. **Playwright MCP:** paket önceden önbelleğe indirilir, eski kayıt silinip user kapsamında yeniden eklenir (tekrar çalıştırmak güvenli).
8. **graphify:** `uv tool install --python 3.12` (uv kendi Python'unu indirir → Microsoft Store "python" sahte kısayolu sorunu olmaz), `uv tool update-shell`, `graphify install`.
9. **Opsiyonel:** 15 sn içinde `E` dersen `scripts\mcp-ekstra.bat` çalışır.
10. **Özet:** hata/uyarı sayısı + `logs\kurulum.log`.

---

## 5. Elle kurulum (betik çalışmazsa)

```bat
winget install --id Git.Git -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id astral-sh.uv -e
```
Yeni terminal aç:
```bat
powershell -ExecutionPolicy Bypass -Command "irm https://claude.ai/install.ps1 | iex"
claude mcp add -s user playwright -- cmd /c npx -y @playwright/mcp@latest
uv tool install --python 3.12 "graphifyy[mcp]"
uv tool update-shell
graphify install
```
Bir projede graphify'i "her zaman açık" yapmak için (proje klasöründe):
```bat
graphify claude install
```

---

## 6. Sık hatalar ve çözümleri

| Belirti | Sebep | Çözüm |
|---|---|---|
| `'claude' is not recognized` | PATH henüz yenilenmedi | Yeni terminal aç. Hâlâ yoksa `%USERPROFILE%\.local\bin` PATH'te mi bak |
| `/mcp` → playwright **failed / Connection closed** | `cmd /c` eksik veya Node yok | `claude mcp remove playwright -s user` → betikteki komutla yeniden ekle |
| MCP **timeout** ilk açılışta | npx paketi indiriyor | `MCP_TIMEOUT=60000` (betik ayarlar), Claude'u yeniden başlat |
| Playwright: *Chromium/Chrome not found* | Chrome yok | `winget install Google.Chrome` ya da Claude'a "browser_install aracını çalıştır" de |
| `graphify` bulunamadı | uv tool dizini PATH'te değil | `uv tool update-shell` → yeni terminal |
| `python` yazınca Microsoft Store açılıyor | Store alias | Önemsiz; graphify uv'nin Python'unu kullanır. İstersen *Ayarlar → Uygulamalar → Uygulama yürütme diğer adları* → python kapat |
| Betik garip karakterler / `'...' is not recognized` satır satır | `.bat` LF satır sonuyla kaydedilmiş | `.gitattributes` CRLF'yi zorlar; ZIP yerine `git clone` kullan |
| `winget` yok | App Installer eksik | Microsoft Store → "App Installer" |
| Kurumsal ağ / proxy | npm/winget dışarı çıkamıyor | `setx HTTPS_PROXY http://proxy:port` + `npm config set proxy ...` |
| `.ps1 cannot be loaded … execution policy` | PowerShell kısıtlı | Betik zaten `-ExecutionPolicy Bypass` kullanır; elle çalıştırırken sen de ekle |
| `claude mcp add` bir şey yazıp betik kapanıyor | `.cmd` dosyası `call` olmadan çağrıldı | Kendi betiklerinde `call claude ...`, `call npx ...` kullan |

Her şey bittiğinde: `scripts\dogrula.bat`.

---

## 7. Kaynaklar
- Playwright MCP: https://github.com/microsoft/playwright-mcp
- graphify: https://github.com/safishamsi/graphify — MCP: https://graphify.com/mcp
- Claude Code MCP dokümanı: https://code.claude.com/docs/en/mcp
- Claude Code kurulum: https://code.claude.com/docs/en/setup
