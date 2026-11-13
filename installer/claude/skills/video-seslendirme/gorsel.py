# repokurulum: video-seslendirme - sahne gorsellerini marka sablonuyla uretir (HTML -> PNG, sistem tarayicisi ile).
import base64, html, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

BURASI = Path(__file__).resolve().parent

VARSAYILAN_MARKA = {
    "ad": "Teknik İSG",
    "logo": str(BURASI / "marka" / "logo.png"),
    "site": "teknikisg.com.tr",
    "eposta": "teknik@teknikisg.com.tr",
    "telefon": "0537 918 48 21",
    "renk_arka1": "#0b2340",
    "renk_arka2": "#164a7c",
    "renk_vurgu": "#f6b420",
    "renk_kirmizi": "#e1251b",
    "yazi_tipi": "'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif",
}


def tarayici_bul():
    aday = [os.environ.get("TARAYICI", "")]
    for kok in [os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), os.environ.get("LOCALAPPDATA")]:
        if kok:
            aday += [os.path.join(kok, "Microsoft", "Edge", "Application", "msedge.exe"),
                     os.path.join(kok, "Google", "Chrome", "Application", "chrome.exe")]
    for ad in ["msedge", "google-chrome", "chromium", "chromium-browser", "chrome"]:
        aday.append(shutil.which(ad) or "")
    for a in aday:
        if a and os.path.exists(a):
            return a
    sys.exit("HATA: Edge veya Chrome bulunamadi (gorsel uretmek icin gerekli). TARAYICI ortam degiskeniyle yol verebilirsin.")


def vurgula(metin):
    """**kalin vurgu** -> marka vurgu rengi; satir sonu -> <br>."""
    t = html.escape(metin or "")
    t = re.sub(r"\*\*(.+?)\*\*", r'<span class="v">\1</span>', t)
    return t.replace("\n", "<br>")


def resim_veri(yol):
    p = Path(yol)
    if not p.exists():
        sys.exit(f"HATA: gorsel bulunamadi: {p}")
    tur = {"png": "png", "jpg": "jpeg", "jpeg": "jpeg", "webp": "webp", "svg": "svg+xml"}.get(p.suffix.lower().lstrip("."), "png")
    return f"data:image/{tur};base64," + base64.b64encode(p.read_bytes()).decode()


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{--v:%(vurgu)s;--k:%(kirmizi)s;--a1:%(a1)s;--a2:%(a2)s}
html,body{width:%(W)dpx;height:%(H)dpx;overflow:hidden}
body{font-family:%(font)s;color:#fff;background:radial-gradient(120%% 80%% at 70%% 30%%,%(a2)s 0%%,%(a1)s 70%%);position:relative}
.logo{position:absolute;top:%(u)dpx;left:50%%;transform:translateX(-50%%);background:#fff;border-radius:22px;padding:22px 36px;box-shadow:0 10px 30px rgba(0,0,0,.35)}
.logo img{height:%(lh)dpx;display:block}
.logo .yazi{font-weight:900;font-size:%(lh)dpx;color:#111;letter-spacing:2px}
.icerik{position:absolute;left:%(k)dpx;right:%(k)dpx;top:%(it)dpx;bottom:%(ib)dpx;display:flex;flex-direction:column}
.orta{justify-content:center;align-items:center;text-align:center}
.etiket{display:inline-block;background:%(vurgu)s;color:#1b1b1b;font-weight:800;border-radius:999px;padding:8px 26px;font-size:%(s3)dpx;letter-spacing:1px}
.etiket.kirmizi{background:%(kirmizi)s;color:#fff}
h1{font-size:%(s1)dpx;line-height:1.15;font-weight:800;margin-top:22px}
.acik{font-size:%(s2)dpx;line-height:1.35;color:#d8e2f0;margin-top:16px}
.v{color:%(vurgu)s;font-weight:800}
.ekran{margin-top:36px;flex:1;min-height:0;display:flex;align-items:flex-start;justify-content:center}
.ekran img{max-width:100%%;max-height:100%%;border-radius:18px;box-shadow:0 18px 40px rgba(0,0,0,.45);background:#fff}
.ekran .kart{width:100%%;max-height:100%%;overflow:hidden;background:#fff;color:#1d2733;border-radius:18px;box-shadow:0 18px 40px rgba(0,0,0,.45);font-size:%(sk)dpx}
.bant{display:inline-block;margin-top:34px;background:%(kirmizi)s;color:#fff;font-weight:700;border-radius:10px;padding:12px 26px;font-size:%(s3)dpx}
.liste{width:100%%;margin-top:40px;display:flex;flex-direction:column;align-items:center}
.liste .m{width:100%%;background:#fff;color:#1d2733;border-radius:14px;padding:22px;font-weight:700;font-size:%(s2)dpx;text-align:center}
.liste .m.son{background:%(vurgu)s;color:#1b1b1b}
.liste .ok{color:%(vurgu)s;font-size:%(s2)dpx;line-height:1.6}
.kutu{margin-top:40px;width:100%%;border:2px solid %(kirmizi)s;background:rgba(80,20,40,.35);border-radius:16px;padding:30px;font-size:%(s2)dpx;color:#e8edf5}
.ilerleme{position:absolute;left:50%%;transform:translateX(-50%%);bottom:%(pb)dpx;display:flex;gap:14px}
.ilerleme i{display:block;width:%(pw)dpx;height:8px;border-radius:4px;background:rgba(255,255,255,.25)}
.ilerleme i.d{background:%(vurgu)s}
.alt{position:absolute;bottom:%(fb)dpx;width:100%%;text-align:center;color:#9fb3cc;font-size:%(s4)dpx}
.sahne3d{position:relative;width:100%%;aspect-ratio:600/520;container-type:inline-size}
.sahne3d .k{position:absolute}
.sahne3d .k img,.sahne3d .k svg{width:100%%;height:auto;display:block}
.sahne3d .golgeli{filter:drop-shadow(0 22px 22px rgba(0,0,0,.5))}
.sahne3d .zemin{position:absolute;transform:translate(-50%%,-50%%);border-radius:50%%;background:radial-gradient(closest-side,rgba(0,0,0,.55),rgba(0,0,0,0));}
.sahne3d .zemin::after{content:"";position:absolute;inset:-35%% -10%%;border-radius:50%%;background:radial-gradient(closest-side,color-mix(in srgb,var(--v) 35%%,transparent),transparent)}
.sahne3d .oklar{position:absolute;inset:0;width:100%%;height:100%%;overflow:visible}
.sahne3d .cip{position:absolute;white-space:nowrap;font-weight:800;font-size:4.6cqw;padding:.35em .8em;border-radius:.6em;box-shadow:0 8px 18px rgba(0,0,0,.4)}
.sahne3d .yazi3d{position:absolute;white-space:nowrap;font-weight:900;text-shadow:0 6px 14px rgba(0,0,0,.5)}
.cizim{margin-top:%(cm)dpx;width:84%%;display:flex;justify-content:center}
.cizim svg{width:100%%;height:auto;display:block;overflow:visible}
.baslik-buyuk{font-size:%(sb)dpx;line-height:1.15;font-weight:900}
.buyuk{font-size:%(s0)dpx;font-weight:800;color:%(vurgu)s;line-height:1.2}
.iletisim{margin-top:40px;font-size:%(s2)dpx;line-height:1.6}
/* Temsili ekran parcalari (ekran_html icinde kullanilir) */
.pencere{background:#fff;color:#1d2733;border-radius:14px;overflow:hidden;width:100%%}
.pbas{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;border-bottom:2px solid #e3e8ef;font-weight:800}
.pbas .marka{color:%(kirmizi)s}
.pgovde{display:flex;min-height:200px}
.yan{background:#2f3b4a;color:#dfe6ee;width:30%%;padding:12px 0;font-size:.9em}
.yan div{padding:8px 16px}
.yan .sec{background:%(vurgu)s;color:#1b1b1b;font-weight:700}
.sag{flex:1;padding:16px 18px}
.alan{border:1px solid #cdd5df;border-radius:8px;padding:10px 12px;margin:8px 0;color:#7a8696}
.dugme{display:inline-block;border-radius:8px;padding:10px 18px;font-weight:700;margin:6px 6px 0 0;background:#e3e8ef;color:#1d2733}
.dugme.mavi{background:#1f5fbf;color:#fff}.dugme.kirmizi{background:%(kirmizi)s;color:#fff}.dugme.sari{background:%(vurgu)s;color:#1b1b1b}
.hedef{outline:5px solid %(vurgu)s;outline-offset:3px;border-radius:8px;box-shadow:0 0 0 12px rgba(246,180,32,.25)}
table.t{width:100%%;border-collapse:collapse;font-size:.9em}
table.t td,table.t th{padding:8px 10px;border-bottom:1px solid #e3e8ef;text-align:left}
table.t tr.yesil td{background:#cfeec6}table.t tr.kirmizi td{background:#f6c9cc}table.t tr.mavi td{background:#d6e6fb}
.not{font-size:.8em;color:#8a96a6;text-align:right;padding:6px 12px}
"""


IKON_KAYNAK = "https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/"   # Fluent Emoji 3D (MIT)
_ikon_dizin = None


def ikon_veri(ad):
    """Fluent Emoji 3D ikonunu (ilk kullanimda indirip ikonlar/ altinda saklar) data URI olarak dondurur."""
    global _ikon_dizin
    import json, urllib.parse, urllib.request
    if _ikon_dizin is None:
        _ikon_dizin = json.loads((BURASI / "ikon-dizin.json").read_text(encoding="utf-8"))
    yol = _ikon_dizin.get(ad)
    if not yol:
        benzer = [k for k in _ikon_dizin if ad.split("_")[0] in k][:12]
        sys.exit(f"HATA: '{ad}' adinda 3B ikon yok. Benzerleri: {', '.join(benzer)} (liste: seslendir.py ikonlar <kelime>)")
    yerel = BURASI / "ikonlar" / (ad + ".png")
    if not yerel.exists():
        yerel.parent.mkdir(exist_ok=True)
        url = IKON_KAYNAK + urllib.parse.quote(yol)
        for i in range(3):
            try:
                with urllib.request.urlopen(url, timeout=60) as r:
                    yerel.write_bytes(r.read())
                break
            except Exception as e:
                if i == 2:
                    sys.exit(f"HATA: ikon indirilemedi ({ad}): {e}")
    return resim_veri(yerel)


def sahne3d_html(katmanlar):
    """600x520 sahne: 3B ikonlar, teknik parcalar, zemin golgesi, oklu etiketler, yazilar."""
    sys.path.insert(0, str(BURASI))
    import parcalar
    yuzde = lambda v, t: f"{v / t * 100:.2f}%"
    ogeler, oklar = [], []
    renkler = {"k": "var(--k)", "v": "var(--v)", "beyaz": "#ffffff", "yesil": "#18a34a", "koyu": "#1d3048"}
    for k in katmanlar:
        x, y = float(k.get("x", 300)), float(k.get("y", 260))
        konum = f"left:{yuzde(x, 600)};top:{yuzde(y, 520)};"
        don = f" rotate({float(k.get('don', 0))}deg)" if k.get("don") else ""
        if k.get("zemin"):
            g = float(k.get("g", 420))
            ogeler.append(f'<div class="zemin" style="{konum}width:{yuzde(g, 600)};height:{yuzde(g * 0.16, 520)}"></div>')
            continue
        if k.get("etiket"):
            renk = renkler.get(k.get("renk", "k"), k.get("renk"))
            yazi_renk = "#1b1b1b" if k.get("renk") in ("v", "beyaz") else "#fff"
            if k.get("ok"):
                tx, ty = k["ok"]
                oklar.append(f'<line x1="{x}" y1="{y}" x2="{tx}" y2="{ty}" stroke="{renk}" stroke-width="5" stroke-linecap="round"/>'
                             f'<circle cx="{tx}" cy="{ty}" r="10" fill="{renk}" stroke="#fff" stroke-width="4"/>')
            ogeler.append(f'<div class="cip" style="{konum}background:{renk};color:{yazi_renk};transform:translate(-50%,-50%){don}">{vurgula(k["etiket"])}</div>')
            continue
        if k.get("yazi"):
            renk = renkler.get(k.get("renk", "v"), k.get("renk"))
            ogeler.append(f'<div class="yazi3d" style="{konum}color:{renk};font-size:{float(k.get("boyut", 44)) / 600 * 100:.2f}cqw;transform:translate(-50%,-50%){don}">{vurgula(k["yazi"])}</div>')
            continue
        genislik = f"width:{yuzde(float(k.get('boyut', 220)), 600)};"
        golge = "" if k.get("golge") is False else " golgeli"
        saydam = f"opacity:{k['saydam']};" if "saydam" in k else ""
        if k.get("ikon"):
            icerik = f'<img src="{ikon_veri(k["ikon"])}">'
        elif k.get("parca"):
            f = parcalar.PARCALAR.get(k["parca"])
            if not f:
                sys.exit(f"HATA: parca yok: {k['parca']} (var olanlar: {', '.join(parcalar.PARCALAR)})")
            icerik = f(**k.get("secenek", {}))
        elif k.get("svg"):
            icerik = k["svg"]
        else:
            continue
        ogeler.append(f'<div class="k{golge}" style="{konum}{genislik}{saydam}transform:translate(-50%,-50%){don}">{icerik}</div>')
    ok_svg = f'<svg class="oklar" viewBox="0 0 600 520">{"".join(oklar)}</svg>' if oklar else ""
    # sira: zemin/ikonlar, sonra oklar, sonra etiket/yazi (ogeler listesinde etiketler zaten sonra eklenmisse ustte kalir)
    alt = [o for o in ogeler if 'class="cip"' not in o and 'class="yazi3d"' not in o]
    ust = [o for o in ogeler if o not in alt]
    return f'<div class="sahne3d">{"".join(alt)}{ok_svg}{"".join(ust)}</div>'


def sahne_html(s, marka, w, h, adim_no, adim_top, hikaye=True):
    o = w / 1080.0
    if hikaye and h > w:
        # WhatsApp durum / Instagram hikaye guvenli alani: ustte ~250 px (profil, ilerleme), altta ~340 px (yanit kutusu) bos
        yer = dict(u=int(h * 0.136), it=int(h * 0.229), ib=int(h * 0.302), pb=int(h * 0.284), fb=int(h * 0.18))
    else:
        yer = dict(u=int(70 * o), it=int(300 * o), ib=int(h * 0.255), pb=int(h * 0.115), fb=int(h * 0.05))
    deg = dict(W=w, H=h, font=marka["yazi_tipi"], a1=marka["renk_arka1"], a2=marka["renk_arka2"], vurgu=marka["renk_vurgu"],
               kirmizi=marka["renk_kirmizi"], lh=int(78 * o), k=int(60 * o),
               s0=int(84 * o), s1=int(62 * o), sb=int(76 * o), cm=int(60 * o), s2=int(38 * o), s3=int(30 * o), s4=int(28 * o), sk=int(34 * o), pw=int(70 * o), **yer)
    logo = marka.get("logo")
    logo_html = f'<img src="{resim_veri(logo)}">' if logo and Path(logo).exists() else f'<span class="yazi">{html.escape(marka["ad"])}</span>'
    tur = s.get("tur", "adim")
    g = []
    if tur == "kapak":
        g.append('<div class="icerik orta">')
        if s.get("etiket"): g.append(f'<span class="etiket">{vurgula(s["etiket"])}</span>')
        g.append(f'<h1 style="font-size:{int(80 * o)}px">{vurgula(s.get("baslik", ""))}</h1>')
        if s.get("aciklama"): g.append(f'<div class="acik">{vurgula(s["aciklama"])}</div>')
        if s.get("bant"): g.append(f'<span class="bant">{vurgula(s["bant"])}</span>')
        g.append('</div>')
    elif tur == "liste":
        g.append('<div class="icerik orta">')
        g.append(f'<h1>{vurgula(s.get("baslik", ""))}</h1><div class="liste">')
        mad = s.get("maddeler", [])
        for i, m in enumerate(mad):
            if i: g.append('<div class="ok">↓</div>')
            g.append(f'<div class="m{" son" if i == len(mad) - 1 and s.get("son_vurgulu", True) else ""}">{vurgula(m)}</div>')
        g.append('</div>')
        if s.get("aciklama"): g.append(f'<div class="acik">{vurgula(s["aciklama"])}</div>')
        g.append('</div>')
    elif tur == "uyari":
        g.append('<div class="icerik orta">')
        if s.get("etiket"): g.append(f'<span class="etiket kirmizi">{vurgula(s["etiket"])}</span>')
        g.append(f'<h1>{vurgula(s.get("baslik", ""))}</h1>')
        if s.get("kutu"): g.append(f'<div class="kutu">{vurgula(s["kutu"])}</div>')
        if s.get("ekran_html"): g.append(f'<div class="ekran" style="flex:0;margin-top:40px;width:100%">{s["ekran_html"]}</div>')
        if s.get("aciklama"): g.append(f'<div class="acik">{vurgula(s["aciklama"])}</div>')
        g.append('</div>')
    elif tur == "cizim":
        # Anlati/tanitim sahnesi: buyuk baslik + ortada SVG cizim (renkler: var(--v) vurgu, var(--k) kirmizi)
        g.append('<div class="icerik orta">')
        if s.get("etiket"): g.append(f'<span class="etiket">{vurgula(s["etiket"])}</span>')
        g.append(f'<h1 class="baslik-buyuk">{vurgula(s.get("baslik", ""))}</h1>')
        if s.get("aciklama"): g.append(f'<div class="acik">{vurgula(s["aciklama"])}</div>')
        if s.get("katmanlar"): g.append(f'<div class="cizim">{sahne3d_html(s["katmanlar"])}</div>')
        elif s.get("cizim"): g.append(f'<div class="cizim">{s["cizim"]}</div>')
        g.append('</div>')
    elif tur == "kapanis":
        g.append('<div class="icerik orta">')
        g.append(f'<div class="buyuk">{vurgula(s.get("baslik", "Takılırsanız bizi arayın."))}</div>')
        satirlar = s.get("satirlar") or [marka.get("site", ""), ("☎ " + marka["telefon"]) if marka.get("telefon") else marka.get("eposta", "")]
        g.append('<div class="iletisim">' + "<br>".join(f"<b>{vurgula(x)}</b>" if i == 0 else vurgula(x) for i, x in enumerate(satirlar) if x) + '</div>')
        g.append('</div>')
    else:   # adim
        g.append('<div class="icerik">')
        if s.get("adim") or adim_no:
            g.append(f'<div><span class="etiket">{vurgula(s.get("adim") or f"ADIM {adim_no}")}</span></div>')
        g.append(f'<h1>{vurgula(s.get("baslik", ""))}</h1>')
        if s.get("aciklama"): g.append(f'<div class="acik">{vurgula(s["aciklama"])}</div>')
        if s.get("ekran_gorsel"):
            g.append(f'<div class="ekran"><img src="{resim_veri(s["ekran_gorsel"])}"></div>')
        elif s.get("ekran_html"):
            g.append(f'<div class="ekran"><div class="kart">{s["ekran_html"]}</div></div>')
        g.append('</div>')
    ilerleme = ""
    if tur == "adim" and adim_top > 1 and s.get("ilerleme", True):
        ilerleme = '<div class="ilerleme">' + "".join(f'<i class="{"d" if i < adim_no else ""}"></i>' for i in range(adim_top)) + '</div>'
    site = marka.get("site", "")
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS % deg}</style></head><body>'
            f'<div class="logo">{logo_html}</div>{"".join(g)}{ilerleme}<div class="alt">{html.escape(site)}</div></body></html>')


def serit_html(s, marka, w, h, adim_no, adim_top, hikaye=True):
    """Gercek/AI klibin ustune binen seffaf katman: ustte logo + adim + baslik, altta altyazi icin koyulasan zemin."""
    sayfa = sahne_html(dict(s, tur="adim", ekran_html=None, ekran_gorsel=None), marka, w, h, adim_no, adim_top, hikaye)
    ust = int(h * (0.42 if hikaye and h > w else 0.30))
    ek = ("<style>body{background:transparent!important}"
          f".golge-ust{{position:absolute;left:0;right:0;top:0;height:{ust}px;background:linear-gradient(rgba(5,15,30,.82),rgba(5,15,30,.55) 60%,rgba(5,15,30,0))}}"
          f".golge-alt{{position:absolute;left:0;right:0;bottom:0;height:{int(h * 0.36)}px;background:linear-gradient(rgba(5,15,30,0),rgba(5,15,30,.7) 45%,rgba(5,15,30,.85))}}"
          "h1,.acik{text-shadow:0 2px 8px rgba(0,0,0,.6)}</style>")
    sayfa = sayfa.replace("</head><body>", ek + '</head><body><div class="golge-ust"></div><div class="golge-alt"></div>', 1)
    return sayfa


def ekran_goruntusu(tarayici, sayfa, png, w, h, profil, seffaf=False):
    if png.exists():
        png.unlink()
    temel = [tarayici, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
             "--no-default-browser-check", "--force-device-scale-factor=1", f"--window-size={w},{h}", f"--screenshot={png}"]
    if seffaf:
        temel.append("--default-background-color=00000000")
    if os.name != "nt" and hasattr(os, "geteuid") and os.geteuid() == 0:
        temel.append("--no-sandbox")
    # Windows'ta acik Edge/Chrome penceresine baglanmasin diye ayri gecici profil
    denemeler = ([temel + [f"--user-data-dir={profil}"]] if os.name == "nt" else []) + [temel]
    r = None
    for arg in denemeler:
        try:
            r = subprocess.run(arg + [sayfa.resolve().as_uri()], capture_output=True, text=True, timeout=90)
            if png.exists():
                return
        except subprocess.TimeoutExpired:
            print("UYARI: tarayici zaman asimi, farkli ayarla yeniden deneniyor")
    sys.exit(f"HATA: gorsel uretilemedi ({png.name}):\n{(r.stderr if r else '')[-1500:]}")


def gorselleri_uret(cfg, klasor):
    """cfg['sahneler'] icindeki her sahne icin gorseller/sahne_XX.png uretir ve s['goruntu']'ya yazar."""
    klasor = Path(klasor)
    w, h = cfg.get("boyut", [1080, 1920])
    marka = dict(VARSAYILAN_MARKA); marka.update(cfg.get("marka", {}))
    if marka.get("logo") and not Path(marka["logo"]).is_absolute():
        marka["logo"] = str((klasor / marka["logo"]).resolve())
    for s in cfg["sahneler"]:
        for anahtar in ("ekran_gorsel",):
            if s.get(anahtar) and not Path(s[anahtar]).is_absolute():
                s[anahtar] = str((klasor / s[anahtar]).resolve())
    hedef = klasor / "gorseller"; hedef.mkdir(exist_ok=True)
    tarayici = tarayici_bul()
    etiketler = []
    for s in cfg["sahneler"]:
        if s.get("tur", "adim") in ("adim", "klip") and not s.get("atla") and (s.get("tur", "adim") == "adim" or s.get("adim")):
            e = s.get("adim") or f"ADIM {len(etiketler) + 1}"
            s["_adim_etiket"] = e
            if e not in etiketler:
                etiketler.append(e)
    profil = tempfile.mkdtemp(prefix="vs-tarayici-")
    try:
        for n, s in enumerate(cfg["sahneler"], 1):
            if s.get("atla") or s.get("goruntu_hazir"):
                continue
            sira = (etiketler.index(s["_adim_etiket"]) + 1) if s.get("_adim_etiket") else 0
            hik = cfg.get("platform", "hikaye") == "hikaye"
            if s.get("tur") == "klip":
                klip = Path(s.get("klip", ""))
                if s.get("klip") and not klip.is_absolute():
                    klip = (klasor / klip).resolve()
                if s.get("klip") and klip.exists():
                    s["_klip"] = str(klip)
                    sayfa = hedef / f"serit_{n:02d}.html"
                    sayfa.write_text(serit_html(s, marka, w, h, sira, len(etiketler), hik), encoding="utf-8")
                    png = hedef / f"serit_{n:02d}.png"
                    ekran_goruntusu(tarayici, sayfa, png, w, h, profil, seffaf=True)
                    s["_serit"] = f"gorseller/serit_{n:02d}.png"
                    s.pop("goruntu", None)
                    print(f"klip: {klip.name} + serit {png.name}")
                    continue
                print(f"UYARI: sahne {n} klibi yok ({s.get('klip')}); yerine tasarim gorseli kullaniliyor. Klibi Gemini'de uretip bu ada kaydet.")
            sayfa = hedef / f"sahne_{n:02d}.html"
            sayfa.write_text(sahne_html(dict(s, tur="adim") if s.get("tur") == "klip" else s, marka, w, h, sira, len(etiketler), hik), encoding="utf-8")
            png = hedef / f"sahne_{n:02d}.png"
            ekran_goruntusu(tarayici, sayfa, png, w, h, profil)
            s["goruntu"] = f"gorseller/sahne_{n:02d}.png"
            print(f"gorsel: {png}")
    finally:
        shutil.rmtree(profil, ignore_errors=True)
