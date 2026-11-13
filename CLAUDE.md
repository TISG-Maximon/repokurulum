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

## Yeni bileşen ekleme kuralı (kullanıcı kararı)
- Sadece **ücretsiz** araçlar eklenir. Ücret, abonelik veya ücretli API anahtarı isteyen (ücretsiz kotası olsa bile) eklenmez.
- `installer/bilesenler.json`'da aynı işi yapan bir bileşen zaten varsa yenisi eklenmez.
- Mevcut bileşenler silinmez; bu kural yalnızca bundan sonra eklenecekler için geçerlidir.
- İstisna: `glm-ajanlar` (GLM 5.3 kod ajanları) kullanıcının açık isteğiyle, kendi ücretsiz Z.ai API anahtarıyla kullanılmak üzere eklendi.
- İstisna: gerçekçi video klipleri kullanıcının kendi Gemini (Google AI Pro, Veo) kotasıyla, elle üretilir (kullanıcı kararı: "ücretsiz veya kotalı"). Kuruluma bileşen olarak eklenmez; `video-seslendirme` skill'i istem listesini hazırlar ve klipleri işler.
- Her yeni bileşene `kurallar` alanında ne işe yaradığı ve hangi ihtiyaçta kaçıncı sırada kullanılacağı yazılır.
