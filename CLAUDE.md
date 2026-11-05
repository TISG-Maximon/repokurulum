# CLAUDE.md

Bu repo, Windows'ta Claude Code + Playwright MCP + graphify ortamını kuran betikleri içerir.

## Kurallar
- Kullanıcıyla Türkçe konuş.
- `.bat` dosyalarında: ASCII karakter kullan (Türkçe karakter yok), `.cmd` olan araçları (`claude`, `npm`, `npx`) her zaman `call` ile çağır, satır sonları CRLF olmalı (`.gitattributes` zorlar).
- Betikler idempotent olmalı: tekrar çalıştırıldığında kurulu olanı atlamalı, MCP kayıtlarını önce `claude mcp remove` ile silip sonra eklemeli.
- Windows'ta stdio MCP sunucuları `cmd /c npx ...` ile eklenir.
- graphify'in PyPI adı `graphifyy`'dir; `uv tool install --python 3.12` ile kur.

## Araçlar
- Tarayıcı işleri için Playwright MCP araçlarını (`browser_*`) kullan.
- `graphify-out/graph.json` varsa, geniş Grep/Glob aramasından önce `graphify query "<soru>"` ile grafiği sorgula.
