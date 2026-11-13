# /// script
# requires-python = ">=3.10"
# dependencies = ["edge-tts>=7"]
# ///
# repokurulum: video-seslendirme skill'inin araci.
#
# Hazir (sessiz) bir videoya Turkce seslendirme ve konusmaya senkron, sabit konumlu altyazi ekler.
# Sahneler arasindaki siyaha kararan gecisleri cikarir, sahneleri yumusak gecisle birlestirir ve
# her sahneyi kendi anlatimi kadar uzatir/kisaltir.
#
#   uv run --script seslendir.py analiz  <video> [--klasor K]   -> sahneler.json taslagi + sahne gorselleri
#   uv run --script seslendir.py uret    <K/sahneler.json>      -> <ad>.mp4, <ad>-altyazili.mp4, <ad>.srt, kontrol.png
#   uv run --script seslendir.py gorsel  <K/senaryo.json>       -> sahne gorselleri (sifirdan video icin, sessiz onizleme)
#   uv run --script seslendir.py olustur <K/senaryo.json>       -> gorseller + seslendirme + altyazi ile video
#   uv run --script seslendir.py istemler <K/senaryo.json>      -> veo-istemleri.md (Gemini/Veo ile gercekci klip uretmek icin)
#   uv run --script seslendir.py klipler <K/senaryo.json>       -> indirilen kliplerin kontrol kareleri
#   uv run --script seslendir.py dene    "metin" [--ses ...]    -> deneme.mp3 (telaffuz denemesi)
#
# Gerekenler: ffmpeg + ffprobe (PATH'te). Ses: edge-tts (internet), yoksa Piper (PIPER_SESLER).
import argparse, asyncio, json, os, re, shutil, statistics, subprocess, sys
from pathlib import Path

VARSAYILAN_TELAFFUZ = {"İSG": "İ Se Ge", "ISG": "İ Se Ge", "KATİP": "Katip", "T.C.": "Te Ce", "SGK": "Se Ge Ka",
                       "e-Devlet": "e-Devlet", "OSGB": "O Se Ge Be", "İSGB": "İ Se Ge Be"}


def calistir(args, **kw):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if r.returncode != 0:
        sys.exit("HATA: " + " ".join(map(str, args[:6])) + " ...\n" + r.stderr[-3000:])
    return r


def sure(dosya):
    return float(calistir(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(dosya)]).stdout.strip())


def filtre_secenegi(betik):
    """FFmpeg 7.1+ '-/filter_complex dosya' ister (8.x eski -filter_complex_script'i kaldirdi); eskiler eski yazimi."""
    cikti = calistir(["ffmpeg", "-version"]).stdout
    m = re.search(r"version\s+n?(\d+)\.(\d+)", cikti)
    yeni = (int(m.group(1)), int(m.group(2))) >= (7, 1) if m else ("version N-" in cikti or "git-" in cikti)   # N-/git = guncel derleme
    return ["-/filter_complex", str(betik)] if yeni else ["-filter_complex_script", str(betik)]


def klip_bilgi(k):
    o = json.loads(calistir(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
                             "-of", "json", str(k)]).stdout)
    v = next(x for x in o["streams"] if x["codec_type"] == "video")
    return float(o["format"]["duration"]), int(v["width"]), int(v["height"]), any(x["codec_type"] == "audio" for x in o["streams"])


def video_bilgi(v):
    o = json.loads(calistir(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                             "stream=width,height,r_frame_rate", "-of", "json", str(v)]).stdout)["streams"][0]
    a, b = o["r_frame_rate"].split("/")
    return int(o["width"]), int(o["height"]), round(float(a) / float(b), 3)


# ---------------------------------------------------------------- analiz
def analiz(video, klasor):
    video = Path(video).resolve()
    klasor = Path(klasor) if klasor else video.parent / (video.stem + "-seslendirme")
    klasor.mkdir(parents=True, exist_ok=True)
    w, h, fps = video_bilgi(video)
    toplam = sure(video)
    # Kare basina parlaklik (siyaha kararan gecisleri bulmak icin)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-an", "-vf",
                        "scale=96:-2,signalstats,metadata=print:key=lavfi.signalstats.YAVG", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    zaman, parlak, t = [], [], None
    for satir in r.stderr.splitlines():
        m = re.search(r"pts_time:([\d.]+)", satir)
        if m:
            t = float(m.group(1))
        m = re.search(r"YAVG=([\d.]+)", satir)
        if m and t is not None:
            zaman.append(t); parlak.append(float(m.group(1)))
    # Ani sahne degisimleri (kararmadan gecis)
    r2 = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-an", "-vf",
                         "select='gt(scene,0.15)',showinfo", "-f", "null", "-"],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    kesmeler = [float(x) for x in re.findall(r"pts_time:([\d.]+)", r2.stderr)]
    if not parlak:
        sys.exit("HATA: video karelerinin parlakligi okunamadi")
    medyan = statistics.median(parlak)
    karanlik = [p < medyan * 0.55 for p in parlak]
    # Karanlik olmayan araliklar = aday sahneler
    araliklar, bas = [], None
    for i, k in enumerate(karanlik):
        if not k and bas is None:
            bas = i
        if (k or i == len(karanlik) - 1) and bas is not None:
            son = i if not k else i - 1
            araliklar.append((bas, son)); bas = None
    sahneler = []
    for (i0, i1) in araliklar:
        # Gecis (kararma/acilma) karelerini at: aralik medyaninin %95'ine ulasan ilk/son kare
        ic = parlak[i0:i1 + 1]
        m = statistics.median(ic)
        j0 = next((j for j in range(i0, i1 + 1) if abs(parlak[j] - m) <= max(2.0, m * 0.05)), i0)
        j1 = next((j for j in range(i1, i0 - 1, -1) if abs(parlak[j] - m) <= max(2.0, m * 0.05)), i1)
        a, b = zaman[j0], min(zaman[j1] + 1.0 / fps, toplam)
        # Aradaki ani kesmelerde bol
        noktalar = [a] + [k for k in kesmeler if a + 0.4 < k < b - 0.4] + [b]
        for x, y in zip(noktalar, noktalar[1:]):
            if y - x >= 0.5:
                sahneler.append([round(x + (0.03 if x != a else 0), 2), round(y - (0.03 if y != b else 0), 2)])
    gorsel = klasor / "sahneler"
    gorsel.mkdir(exist_ok=True)
    for f in gorsel.glob("sahne_*.png"):
        f.unlink()
    kayit = []
    for n, (a, b) in enumerate(sahneler, 1):
        ad = f"sahne_{n:02d}.png"
        orta = a + (b - a) * 0.6
        calistir(["ffmpeg", "-v", "error", "-y", "-ss", f"{orta:.2f}", "-i", str(video), "-frames:v", "1",
                  "-vf", "scale=540:-2", str(gorsel / ad)])
        kayit.append({"no": n, "bas": a, "son": b, "gorsel_sure": round(b - a, 2), "gorsel": "sahneler/" + ad, "metin": ""})
    calistir(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf",
              f"fps={min(2, 60 / max(toplam, 1)):.4f},scale=160:-2,tile=10x6", "-frames:v", "1", str(klasor / "genel.png")])
    js = {
        "_aciklama": "Her sahneye 'metin' yaz (ekranda altyazi olarak da gorunur). Bos metinli sahne sessiz ve kendi suresinde kalir. "
                     "'atla': true sahneyi cikarir. bas/son: sahnenin kararma/gecis icermeyen temiz araligi (saniye). "
                     "'telaffuz': ses motoruna giden metinde yapilacak degisiklikler (kisaltmalar).",
        "video": str(video), "cikti_adi": video.stem + "-seslendirmeli",
        "motor": "otomatik", "gemini_ses": "Kore", "ses": "tr-TR-EmelNeural", "hiz": "+4%", "piper_ses": "tr_TR-dfki-medium",
        "gecis_sn": 0.3, "on_bosluk_sn": 0.35, "son_bosluk_sn": 0.45,
        "altyazi": {"yazi_tipi": "Arial", "boyut_orani": 0.026, "y_orani": 0.80, "max_karakter": 40},
        "telaffuz": VARSAYILAN_TELAFFUZ,
        "video_bilgi": {"genislik": w, "yukseklik": h, "fps": fps, "sure": round(toplam, 2),
                        "karanlik_gecis_sayisi": max(0, len(araliklar) - 1)},
        "sahneler": kayit,
    }
    hedef = klasor / "sahneler.json"
    if hedef.exists():
        hedef.rename(klasor / "sahneler.onceki.json")
    hedef.write_text(json.dumps(js, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Video: {w}x{h}, {fps} fps, {toplam:.1f} sn; {len(kayit)} sahne, {max(0, len(araliklar) - 1)} siyah gecis")
    for s in kayit:
        print(f"  sahne {s['no']:2d}: {s['bas']:6.2f} - {s['son']:6.2f}  ({s['gorsel_sure']:.1f} sn)  {s['gorsel']}")
    print(f"Taslak: {hedef}\nGenel bakis: {klasor / 'genel.png'}")


# ---------------------------------------------------------------- metin
def parcala(metin, azami):
    """Altyaziyi ekrana sigan, anlam butunlugu olan parcalara bol."""
    metin = re.sub(r"\s+", " ", metin).strip()
    if not metin:
        return []
    # Kisaltma ve sayilardaki noktayi koru (T.C., 1.5, www.site.com): sadece ardindan bosluk gelen isarette bol
    ham = [p.strip() for p in re.split(r"(?<=[.,:;!?])(?<!\b[A-ZÇĞİÖŞÜ]\.)\s+", metin) if p.strip()]
    parcalar = []
    for p in ham:
        kisa = parcalar and len(parcalar[-1]) < 14 and len(parcalar[-1]) + 1 + len(p) <= azami * 1.4
        if parcalar and (kisa or (len(parcalar[-1]) + 1 + len(p) <= azami and not re.search(r"[.!?]$", parcalar[-1]))):
            parcalar[-1] += " " + p
        else:
            parcalar.append(p)
    sonuc = []
    for p in parcalar:
        while len(p) > azami * 1.6:
            k = p.split(" ")
            yarim, toplam_k = len(p) / 2, 0
            for i, kel in enumerate(k):
                toplam_k += len(kel) + 1
                if toplam_k >= yarim:
                    break
            sonuc.append(" ".join(k[:i + 1])); p = " ".join(k[i + 1:])
        if p:
            sonuc.append(p)
    return sonuc


def seslendirilecek(metin, telaffuz):
    s = metin.replace('"', "").replace("“", "").replace("”", "")
    for k in sorted(telaffuz, key=len, reverse=True):
        s = re.sub(r"(?<![\wİıĞğÜüŞşÖöÇç])" + re.escape(k) + r"(?![\wİıĞğÜüŞşÖöÇç])", telaffuz[k], s)
    s = re.sub(r"(\w)-(?=[A-ZÇĞİÖŞÜ][a-zçğıöşü])", r"\1 ", s)   # "İ Se Ge-Katip" -> "İ Se Ge Katip"
    return s


def yumusat(wav):
    """Ses parcasinin basina/sonuna cok kisa gecis ekler (kesim noktasindaki 'pat/tik' sesini onler) ve tepe seviyeyi sinirlar."""
    gecici = Path(str(wav) + ".y.wav")
    calistir(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-af",
              "highpass=f=60,volume=-2dB,afade=t=in:st=0:d=0.025,areverse,afade=t=in:st=0:d=0.04,areverse,alimiter=limit=0.89:attack=1:release=50",
              "-ar", "44100", "-ac", "1", str(gecici)])
    os.replace(gecici, wav)


def kelime_say(s):
    return len([t for t in s.split() if re.search(r"\w", t)])


# ---------------------------------------------------------------- ses
async def edge_ses(metin, ses, hiz, dosya):
    import edge_tts
    kw = {"boundary": "WordBoundary"}
    vekil = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if vekil:
        kw["proxy"] = vekil
    c = edge_tts.Communicate(metin, ses, rate=hiz, **kw)
    kelimeler = []
    with open(dosya, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                kelimeler.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]))
    return kelimeler


def piper_model(ad):
    """Istenen Piper sesi; yoksa klasordeki herhangi bir Turkce ses."""
    for d in [os.environ.get("PIPER_SESLER"), os.path.join(os.environ.get("LOCALAPPDATA", ""), "piper-sesler")]:
        if d and Path(d).is_dir():
            if Path(d, ad + ".onnx").exists():
                return str(Path(d, ad + ".onnx"))
            diger = sorted(Path(d).glob("tr_TR-*.onnx"))
            if diger:
                return str(diger[0])
    return None


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/"


def gemini_anahtar():
    k = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not k and os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as a:
                k = winreg.QueryValueEx(a, "GEMINI_API_KEY")[0]
        except Exception:
            k = None
    return k


def gemini_istek(yol, govde=None):
    import urllib.request, urllib.error
    bas = {"Content-Type": "application/json"}
    k = gemini_anahtar()
    if k:
        bas["x-goog-api-key"] = k
    istek = urllib.request.Request(GEMINI_URL + yol, data=json.dumps(govde).encode() if govde is not None else None, headers=bas)
    for deneme in range(4):
        try:
            with urllib.request.urlopen(istek, timeout=300) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            ayrinti = e.read().decode("utf-8", "replace")[:600]
            if e.code == 429 and deneme < 3:
                print(f"Gemini kota/hiz siniri (429), {20 * (deneme + 1)} sn bekleniyor..."); import time; time.sleep(20 * (deneme + 1)); continue
            if e.code in (401, 403):
                sys.exit("HATA: Gemini API anahtari yok ya da gecersiz. Repo Kurulum'da 'Gemini seslendirme' anahtarini gir "
                         "(aistudio.google.com/apikey, ucretsiz) ya da GEMINI_API_KEY ortam degiskenini ayarla.\n" + ayrinti)
            if e.code == 429:
                sys.exit("HATA: Gemini ucretsiz kotasi doldu (gunluk/dakikalik). Daha sonra tekrar dene ya da 'motor': 'edge' kullan.\n" + ayrinti)
            sys.exit(f"HATA: Gemini API {e.code}: {ayrinti}")
        except urllib.error.URLError as e:
            if deneme == 3:
                sys.exit(f"HATA: Gemini API'ye ulasilamadi: {e}")


def gemini_model(cfg):
    if cfg.get("gemini_model"):
        return cfg["gemini_model"]
    try:
        modeller = [m["name"].split("/")[-1] for m in gemini_istek("models?pageSize=200").get("models", []) if "tts" in m["name"]]
    except SystemExit:
        raise
    except Exception:
        modeller = []
    for tercih in ("flash", "pro", ""):
        aday = sorted([m for m in modeller if tercih in m], reverse=True)
        if aday:
            return aday[0]
    return "gemini-2.5-flash-preview-tts"


def gemini_fazla_okuma(wav, metin, is_d):
    """Uretilen sesi Gemini ile yaziya doker; metne gore fazladan okunan kelime oranini dondurur (kontrol yapilamazsa None)."""
    import base64
    try:
        modeller = [m["name"].split("/")[-1] for m in gemini_istek("models?pageSize=200").get("models", [])]
        yazici = sorted([m for m in modeller if "transcribe" in m], reverse=True) or sorted([m for m in modeller if "flash" in m and "-tts" not in m and "lite" not in m and "image" not in m], reverse=True)
        if not yazici:
            return None
        mp3 = is_d / "denetim.mp3"
        calistir(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-ar", "16000", "-ac", "1", "-b:a", "48k", str(mp3)])
        govde = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/mp3", "data": base64.b64encode(mp3.read_bytes()).decode()}},
                                         {"text": "Bu Türkçe ses kaydını kelimesi kelimesine yazıya dök, başka bir şey yazma."}]}]}
        y = gemini_istek(f"models/{yazici[0]}:generateContent", govde)
        parca = y["candidates"][0]["content"]["parts"][0]
        yazi = parca.get("text") or parca.get("audioTranscription", {}).get("text", "")
        say = lambda t: len(re.findall(r"\w+", t))
        return max(0.0, (say(yazi) - say(metin)) / max(1, say(metin)))
    except (SystemExit, Exception):
        return None


def gemini_toplu(metinler, cfg, is_d):
    """Tum sahne metinlerini TEK istekte seslendirir (kota dostu), sesi sahne aralarindaki duraklamalardan boler.
    Donus: [(wav, sure), ...] metinler sirasiyla."""
    import base64, hashlib
    ses = cfg.get("gemini_ses", "Kore")
    uslup = cfg.get("gemini_uslup", "")   # bos: modelin dogal okuyusu (talimat metne karisip okunabiliyor)
    metin = "\n\n".join(metinler)
    anahtar = hashlib.sha1(f"{ses}|{uslup}|{metin}|{cfg.get('gemini_model', '')}".encode()).hexdigest()[:16]
    ham = is_d / f"gemini_{anahtar}.wav"
    if not ham.exists():
        model = gemini_model(cfg)
        for deneme, us in enumerate([uslup, ""] if uslup else [""]):
            istem = f"{us.rstrip(':')}:\n{metin}" if us else metin
            print(f"Gemini TTS: model {model}, ses {ses}{' (uslup: ' + us + ')' if us else ''}")
            govde = {"contents": [{"parts": [{"text": istem}]}],
                     "generationConfig": {"responseModalities": ["AUDIO"],
                                          "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": ses}}}}}
            y = gemini_istek(f"models/{model}:generateContent", govde)
            try:
                veri = next(p["inlineData"] for p in y["candidates"][0]["content"]["parts"] if "inlineData" in p)
            except Exception:
                sys.exit("HATA: Gemini ses dondurmedi: " + json.dumps(y)[:500])
            pcm = is_d / f"gemini_{anahtar}.pcm"
            pcm.write_bytes(base64.b64decode(veri["data"]))
            oran = re.search(r"rate=(\d+)", veri.get("mimeType", "")); oran = oran.group(1) if oran else "24000"
            calistir(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", oran, "-ac", "1", "-i", str(pcm), "-ar", "44100", str(ham)])
            fazla = gemini_fazla_okuma(ham, metin, is_d)
            if fazla is None or fazla < 0.15 or deneme == 1 or not us:
                if fazla is not None and fazla >= 0.15:
                    print(f"UYARI: Gemini metinde olmayan kelimeler okumus olabilir (%{fazla * 100:.0f} fazla). Sesi dinleyerek kontrol et.")
                break
            print("UYARI: Gemini uslup talimatini da okumus; talimatsiz yeniden uretiliyor.")
            ham.unlink()
    toplam = sure(ham)
    n = len(metinler)
    # Sessizlikleri bul; en uzun n-1 tanesinden bol (paragraf aralari)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(ham), "-af", "silencedetect=n=-38dB:d=0.18", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    bas_l = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    son_l = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    araliklar = [(a, b) for a, b in zip(bas_l, son_l) if a > 0.05 and b < toplam - 0.05]
    if len(araliklar) < n - 1:
        sys.exit(f"HATA: Gemini sesi {n} sahneye bolunemedi ({len(araliklar)} duraklama bulundu). Tekrar dene ya da metinleri sadelestir.")
    # Her sinir icin metin uzunlugundan beklenen zamani hesapla; ona en yakin (ve yeterince uzun) duraklamayi sec.
    # Paragraf aralari genelde cumle ici duraklamalardan uzundur: uzunluga hafif agirlik ver.
    uz = [max(1, len(m)) for m in metinler]
    konusma = toplam - sum(b - a for a, b in araliklar) * 0.5
    secilen, onceki = [], 0.0
    for k in range(1, n):
        hedef = toplam * sum(uz[:k]) / sum(uz)
        kalan = n - 1 - k   # sonra secilecek sinir sayisi kadar aralik birak
        adaylar = [ab for ab in araliklar if (ab[0] + ab[1]) / 2 > onceki + 0.3]
        adaylar = adaylar[:len(adaylar) - kalan] if kalan else adaylar
        if not adaylar:
            sys.exit("HATA: Gemini sesi sahnelere bolunemedi.")
        en = min(adaylar, key=lambda ab: abs((ab[0] + ab[1]) / 2 - hedef) - 1.5 * (ab[1] - ab[0]))
        secilen.append(en); onceki = (en[0] + en[1]) / 2
    kes = [0.0] + [(a + b) / 2 for a, b in secilen] + [toplam]
    cikti = []
    for i in range(n):
        wav = is_d / f"g{i:02d}.wav"
        calistir(["ffmpeg", "-v", "error", "-y", "-ss", f"{kes[i]:.3f}", "-to", f"{kes[i + 1]:.3f}", "-i", str(ham), "-af",
                  "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                  "-ar", "44100", "-ac", "1", str(wav)])
        yumusat(wav)
        cikti.append((wav, sure(wav)))
    return cikti


def ses_uret(metin, cfg, hedef_wav, gecici):
    """Sesi uretir, bas/son sessizligi kirpar. Donus: (sure, [(bas, son, kelime)...] kirpilmis zamana gore veya None)."""
    motor = cfg.get("motor", "edge")
    if motor == "edge":
        try:
            ham = gecici.with_suffix(".mp3")
            k = asyncio.run(edge_ses(metin, cfg["ses"], cfg.get("hiz", "+0%"), ham))
            if not k or ham.stat().st_size < 1000:
                raise RuntimeError("bos ses")
            a = max(0.0, k[0][0] - 0.02); b = k[-1][1] + 0.15
            calistir(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(ham),
                      "-ar", "44100", "-ac", "1", str(hedef_wav)])
            yumusat(hedef_wav)
            return sure(hedef_wav), [(x - a, y - a, t) for x, y, t in k]
        except Exception as e:
            if not piper_model(cfg.get("piper_ses", "tr_TR-dfki-medium")):
                sys.exit(f"HATA: edge-tts calismadi ({e}) ve Piper sesi bulunamadi. Internet baglantisini kontrol et.")
            print(f"UYARI: edge-tts calismadi ({e}); Piper ile devam ediliyor.")
            cfg["motor"] = "piper"
    model = piper_model(cfg.get("piper_ses", "tr_TR-dfki-medium"))
    if not model or not shutil.which("piper"):
        sys.exit("HATA: Piper veya Turkce ses modeli yok (Repo Kurulum'da 'Piper' bilesenini kur).")
    txt = gecici.with_suffix(".txt"); txt.write_text(metin, encoding="utf-8")
    ham = gecici.with_suffix(".piper.wav")
    calistir(["piper", "-m", model, "-i", str(txt), "-f", str(ham)])
    calistir(["ffmpeg", "-v", "error", "-y", "-i", str(ham), "-af",
              "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
              "-ar", "44100", "-ac", "1", str(hedef_wav)])
    yumusat(hedef_wav)
    return sure(hedef_wav), None


def deneme(metin, ses, hiz, telaffuz_dosya):
    tel = dict(VARSAYILAN_TELAFFUZ)
    if telaffuz_dosya:
        tel.update(json.loads(Path(telaffuz_dosya).read_text(encoding="utf-8")).get("telaffuz", {}))
    s = seslendirilecek(metin, tel)
    asyncio.run(edge_ses(s, ses, hiz, "deneme.mp3"))
    print(f"Seslendirilen metin: {s}\nDosya: {Path('deneme.mp3').resolve()}")


# ---------------------------------------------------------------- uret
def zaman_ass(x):
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02}:{x % 60:05.2f}"


def zaman_srt(x):
    ms = int(round(x * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


# ---------------------------------------------------------------- ortak ayarlar (her videonun temeli)
VARSAYILAN_AYAR = {
    "platform": "hikaye", "hedef_sure_sn": 58, "boyut": [1080, 1920], "fps": 30,
    "motor": "otomatik", "gemini_ses": "Kore", "gemini_uslup": "", "ses": "tr-TR-EmelNeural", "hiz": "+4%",
    "piper_ses": "tr_TR-dfki-medium", "gecis_sn": 0.3, "on_bosluk_sn": 0.3, "son_bosluk_sn": 0.4, "hareket": "yakinlas",
    "altyazi": {"yazi_tipi": "Arial", "boyut_orani": 0.026, "max_karakter": 40},
    "telaffuz": {"İSG": "İ Se Ge", "KATİP": "Katip", "T.C.": "Te Ce", "SGK": "Se Ge Ka", "KKD": "Ka Ka De", "OSGB": "O Se Ge Be"},
    "marka": {},
}


def kullanici_ayar_yolu():
    return Path.home() / "ClaudeProjeler" / "videolar" / "ayarlar.json"


def _birlestir(a, b):
    c = dict(a)
    for k, v in (b or {}).items():
        c[k] = _birlestir(c[k], v) if isinstance(v, dict) and isinstance(c.get(k), dict) else v
    return c


def ayar_birlestir(cfg):
    """Sira: arac varsayilanlari < kullanicinin ortak ayarlari (ClaudeProjeler/videolar/ayarlar.json) < senaryo."""
    temel = VARSAYILAN_AYAR
    ka = kullanici_ayar_yolu()
    if ka.exists():
        try:
            temel = _birlestir(temel, {k: v for k, v in json.loads(ka.read_text(encoding="utf-8")).items() if not k.startswith("_")})
        except Exception as e:
            print(f"UYARI: {ka} okunamadi ({e}); varsayilanlar kullaniliyor")
    return _birlestir(temel, cfg)


def yeni_proje(ad, tur):
    """Video turune gore hazir proje klasoru acar; ortak ayarlar dosyasi yoksa olusturur."""
    burasi = Path(__file__).resolve().parent
    kaynak = {"tanitim": "ornekler/tanitim-yangin-tesisati.json", "rehber": "ornek-senaryo.json", "gercekci": "ornek-gercekci.json"}.get(tur)
    if not kaynak:
        sys.exit("HATA: tur tanitim, rehber ya da gercekci olmali")
    kok = kullanici_ayar_yolu().parent
    duz = ad.translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")).lower()
    klasor = kok / re.sub(r"[^a-z0-9]+", "-", duz).strip("-")
    if (klasor / "senaryo.json").exists():
        sys.exit(f"HATA: {klasor} zaten var")
    (klasor / "klipler").mkdir(parents=True, exist_ok=True)
    ornek = json.loads((burasi / kaynak).read_text(encoding="utf-8"))
    senaryo = {"_aciklama": f"repokurulum {tur} videosu. Ortak ayarlar (marka, ses, format) {kullanici_ayar_yolu()} dosyasindan gelir; burada sadece farkli olanlari yaz.",
               "cikti_adi": klasor.name, "sahneler": ornek["sahneler"]}
    for k in ("marka",):
        if ornek.get(k, {}).get("renk_vurgu"):
            senaryo["marka"] = {"renk_vurgu": ornek[k]["renk_vurgu"]}
    (klasor / "senaryo.json").write_text(json.dumps(senaryo, ensure_ascii=False, indent=1), encoding="utf-8")
    ka = kullanici_ayar_yolu()
    if not ka.exists():
        sys.path.insert(0, str(burasi)); sys.dont_write_bytecode = True
        import gorsel
        ortak = {"_aciklama": "Tum videolarin ortak ayarlari. Burayi degistirince sonraki her video buna gore uretilir.",
                 "marka": {k: v for k, v in gorsel.VARSAYILAN_MARKA.items() if k not in ("yazi_tipi", "logo")},
                 "motor": VARSAYILAN_AYAR["motor"], "gemini_ses": VARSAYILAN_AYAR["gemini_ses"], "ses": VARSAYILAN_AYAR["ses"],
                 "platform": "hikaye", "telaffuz": VARSAYILAN_AYAR["telaffuz"]}
        ka.write_text(json.dumps(ortak, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Ortak ayarlar olusturuldu: {ka}")
    print(f"Yeni proje: {klasor}\n  Senaryo: {klasor / 'senaryo.json'} (ornek sahneler; konuya gore degistir)")


# ---------------------------------------------------------------- kalite kontrolu
def kalite(video, hikaye=True):
    """Uretilen videoyu olcer: ses patlamasi, tavana vurma, ses seviyesi, sure, cozunurluk, siyah kare. GECTI/KALDI raporu."""
    import wave, struct
    video = Path(video)
    sonuc = []
    w, h, fps = video_bilgi(video)
    toplam = sure(video)
    sonuc.append(("Cozunurluk", f"{w}x{h}", (w, h) == (1080, 1920) or not hikaye))
    sonuc.append(("Sure", f"{toplam:.1f} sn", toplam <= 60 or not hikaye))
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-vf", "blackdetect=d=0.1:pic_th=0.90:pix_th=0.12", "-an", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    sonuc.append(("Siyah ara", str(len(re.findall("black_start", r.stderr))), "black_start" not in r.stderr))
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    ozet = r.stderr[r.stderr.rfind("Summary:"):]
    lufs = re.search(r"I:\s+(-?[\d.]+) LUFS", ozet); tp = re.search(r"Peak:\s+(-?[\d.]+) dBFS", ozet)
    if lufs:
        sonuc.append(("Ses seviyesi", f"{float(lufs.group(1)):.1f} LUFS (hedef -16)", -19 <= float(lufs.group(1)) <= -13))
    if tp:
        sonuc.append(("Tepe seviye", f"{float(tp.group(1)):.1f} dBTP", float(tp.group(1)) <= -0.5))
    gecici = video.with_suffix(".kalite.wav")
    calistir(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "44100", str(gecici)])
    with wave.open(str(gecici)) as f:
        n = f.getnframes(); ornek = struct.unpack("<%dh" % n, f.readframes(n))
    gecici.unlink()
    bas, son = max(map(abs, ornek[:441])) if n else 0, max(map(abs, ornek[-441:])) if n else 0
    sonuc.append(("Baslangic/bitis patlamasi", f"ilk/son 10 ms tepe {bas}/{son}", bas < 1500 and son < 1500))
    tavan = sum(1 for x in ornek if abs(x) >= 32700)
    sonuc.append(("Tavana vurma (clipping)", f"{tavan} ornek", tavan == 0))
    gecti = all(ok for _, _, ok in sonuc)
    rapor = [f"KALITE: {'GECTI' if gecti else 'KALDI'}  ({video.name})"] + [f"  [{'OK ' if ok else 'XX '}] {ad}: {deger}" for ad, deger, ok in sonuc]
    (video.parent / "kalite.txt").write_text("\n".join(rapor) + "\n", encoding="utf-8")
    print("\n".join(rapor))
    return gecti


def uret(json_yolu):
    jy = Path(json_yolu).resolve()
    cfg = json.loads(jy.read_text(encoding="utf-8"))
    uret_cfg(cfg, jy.parent)


def uret_cfg(cfg, klasor):
    cfg.update(ayar_birlestir(cfg))
    klasor = Path(klasor)
    video = None
    if cfg.get("video"):
        video = Path(cfg["video"])
        if not video.is_absolute():
            video = (klasor / video).resolve()
        w, h, fps = video_bilgi(video)
    else:
        w, h = cfg.get("boyut", [1080, 1920]); fps = cfg.get("fps", 30)
    tel = cfg.get("telaffuz", VARSAYILAN_TELAFFUZ)
    alt = cfg.get("altyazi", {})
    azami = int(alt.get("max_karakter", 40))
    X, ON, SON = float(cfg.get("gecis_sn", 0.3)), float(cfg.get("on_bosluk_sn", 0.35)), float(cfg.get("son_bosluk_sn", 0.45))
    sahneler = [s for s in cfg["sahneler"] if not s.get("atla")]
    if not sahneler:
        sys.exit("HATA: sahne yok")
    is_d = klasor / "_is"; is_d.mkdir(exist_ok=True)

    # 1) Ses ve kelime zamanlari
    hikaye = cfg.get("platform", "hikaye") == "hikaye"
    hedef_sn = float(cfg.get("hedef_sure_sn", 58 if hikaye else 0))   # WhatsApp durum / Instagram hikaye: en fazla 60 sn

    if cfg.get("motor", "otomatik") == "otomatik":
        cfg["motor"] = "gemini" if gemini_anahtar() else "edge"
        print(f"Ses motoru: {cfg['motor']}")

    def gemini_sesleri():
        for s in sahneler:
            s["_parcalar"] = parcala(s.get("metin", ""), azami); s["_ses"] = None
        konusanlar = [s for s in sahneler if s["_parcalar"]]
        sesler = gemini_toplu([" ".join(seslendirilecek(p, tel) for p in s["_parcalar"]) for s in konusanlar], cfg, is_d)
        for s, (wav, sr) in zip(konusanlar, sesler):
            s["_ses"], s["_sure"], s["_kelimeler"] = wav, sr, None
            print(f"sahne: ses {sr:.2f} sn  | {s.get('metin', '')}")

    def sesleri_uret():
        if cfg.get("motor") == "gemini":
            try:
                return gemini_sesleri()
            except SystemExit as e:
                print(f"UYARI: Gemini seslendirme olmadi, Microsoft Emel ile devam ediliyor.\n  {e}")
                cfg["motor"] = "edge"; cfg["ses"] = cfg.get("yedek_ses", "tr-TR-EmelNeural")
        for i, s in enumerate(sahneler):
            s["_parcalar"] = parcala(s.get("metin", ""), azami)
            s["_ses"] = None
            if s["_parcalar"]:
                konusma = " ".join(seslendirilecek(p, tel) for p in s["_parcalar"])
                wav = is_d / f"s{i:02d}.wav"
                s["_sure"], s["_kelimeler"] = ses_uret(konusma, cfg, wav, is_d / f"s{i:02d}")
                s["_ses"] = wav
                print(f"sahne {s.get('no', i + 1):>2}: ses {s['_sure']:.2f} sn  | {konusma}")

    def uzunluklar():
        for s in sahneler:
            if s["_ses"]:
                s["_uzunluk"] = ON + s["_sure"] + SON
            elif s.get("_klip"):
                s["_uzunluk"] = float(s.get("sure", min(6.0, klip_bilgi(s["_klip"])[0])))
            elif s.get("goruntu"):
                s["_uzunluk"] = float(s.get("sure", 2.5))
            else:
                s["_uzunluk"] = float(s["son"]) - float(s["bas"])
        sahneler[-1]["_uzunluk"] += 0.6
        return sum(s["_uzunluk"] for s in sahneler) - X * (len(sahneler) - 1)

    sesleri_uret()
    tahmin = uzunluklar()
    if hedef_sn and tahmin > hedef_sn:
        ON, SON = min(ON, 0.2), min(SON, 0.3)
        tahmin = uzunluklar()
        print(f"Sure {hedef_sn:.0f} sn hedefini asiyor; bosluklar kisaltildi -> {tahmin:.1f} sn")
    if hedef_sn and tahmin > hedef_sn and cfg.get("motor", "edge") == "edge":
        konusma_top = sum(s["_sure"] for s in sahneler if s["_ses"])
        gerek = konusma_top / max(1.0, konusma_top - (tahmin - hedef_sn))   # gereken hizlanma orani
        mevcut = int(re.sub(r"[^\d-]", "", str(cfg.get("hiz", "+0%"))) or 0)
        yeni = min(10, int((1 + mevcut / 100) * gerek * 100 - 100 + 0.999))
        if yeni > mevcut:
            cfg["hiz"] = f"+{yeni}%"
            print(f"Konusma hizi {mevcut:+d}% -> {yeni:+d}% (en fazla +10%) ile yeniden uretiliyor")
            sesleri_uret()
            tahmin = uzunluklar()
    if hedef_sn and tahmin > hedef_sn:
        print(f"UYARI: video {tahmin:.1f} sn, {hedef_sn:.0f} sn hedefini asiyor. Metinleri kisaltmak en iyisi; "
              f"simdilik video sahne sinirindan parcalara bolunecek.")

    # 2) Goruntu: temiz araliklar + kendi anlatimi kadar sure + yumusak gecis (siyah yok)
    fl, ofset = [], [0.0]
    girdiler = ["-i", str(video)] if video else []
    n = 1 if video else 0
    for i, s in enumerate(sahneler):
        L = s["_uzunluk"]
        if s.get("_klip"):
            ksure, kw, kh, kses = klip_bilgi(s["_klip"])
            a = float(s.get("klip_bas", 0)); b = min(float(s.get("klip_son", ksure)), ksure)
            parca = max(0.5, b - a)
            yavas = min(L / parca, 1.35) if L > parca else 1.0     # klip kisaysa en fazla %35 yavaslat, kalani son kare
            doldur = s.get("doldur", "otomatik")
            if doldur == "otomatik":
                doldur = "kirp" if abs(kw / kh - w / h) < 0.2 else "bulanik"
            girdiler += ["-i", s["_klip"]]
            temel = f"[{n}:v]trim={a:.3f}:{b:.3f},setpts=(PTS-STARTPTS)*{yavas:.4f},fps={fps}"
            if doldur == "kirp":
                fl.append(f"{temel},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1[kb{i}]")
            else:   # yatay klip: arkada bulanik buyutulmus kopya, onde tam klip
                fl.append(f"{temel},split[ka{i}][kc{i}];[ka{i}]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=25:4[kd{i}];"
                          f"[kc{i}]scale={w}:{h}:force_original_aspect_ratio=decrease[ke{i}];[kd{i}][ke{i}]overlay=(W-w)/2:(H-h)/2,setsar=1[kb{i}]")
            if kses and float(s.get("klip_ses", 0)) > 0:
                s["_klip_ses"] = (n, a, b, yavas)
            n += 1
            son_etiket = f"kb{i}"
            if s.get("_serit"):
                girdiler += ["-loop", "1", "-framerate", str(fps), "-t", f"{L + 0.5:.3f}", "-i", str(Path(klasor, s["_serit"]))]
                fl.append(f"[{n}:v]format=rgba[ks{i}];[kb{i}][ks{i}]overlay=0:0:shortest=0[kf{i}]")
                son_etiket = f"kf{i}"; n += 1
            fl.append(f"[{son_etiket}]tpad=stop_mode=clone:stop_duration={L + 0.5:.3f},trim=0:{L:.3f},setpts=PTS-STARTPTS,format=yuv420p,settb=AVTB[v{i}]")
        elif s.get("goruntu"):
            girdiler += ["-loop", "1", "-framerate", str(fps), "-t", f"{L + 0.5:.3f}", "-i", str(Path(klasor, s["goruntu"]))]
            hareket = s.get("hareket", cfg.get("hareket", "yakinlas"))
            zoom = ""
            if hareket == "yakinlas":   # hafif ve puruzsuz yakinlasma (2x olcekte hesaplanir, titremez)
                kare = int(round((L + 0.5) * fps))
                zoom = (f",scale={2 * w}:{2 * h},zoompan=z='1+0.045*on/{kare}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                        f":d=1:s={w}x{h}:fps={fps}")
            fl.append(f"[{n}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1{zoom},"
                      f"trim=0:{L:.3f},setpts=PTS-STARTPTS,fps={fps},format=yuv420p,settb=AVTB[v{i}]")
            n += 1
        else:
            if not video:
                sys.exit(f"HATA: sahne {s.get('no', i + 1)} icin ne 'goruntu' ne de 'video' var")
            a, b = float(s["bas"]), float(s["son"])
            fl.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={max(0.0, L - (b - a)) + 0.2:.3f},"
                      f"trim=0:{L:.3f},setpts=PTS-STARTPTS,fps={fps},format=yuv420p,settb=AVTB[v{i}]")
    onceki, toplam = "v0", sahneler[0]["_uzunluk"]
    for i in range(1, len(sahneler)):
        o = toplam - X
        ofset.append(o)
        fl.append(f"[{onceki}][v{i}]xfade=transition=fade:duration={X}:offset={o:.3f}[x{i}]")
        onceki, toplam = f"x{i}", o + sahneler[i]["_uzunluk"]
    ses_etiket = []
    for i, s in enumerate(sahneler):
        s["_bas"] = ofset[i] + ON
        if s["_ses"]:
            girdiler += ["-i", str(s["_ses"])]
            fl.append(f"[{n}:a]adelay={int(s['_bas'] * 1000)}:all=1[a{i}]"); ses_etiket.append(f"[a{i}]"); n += 1
    for i, s in enumerate(sahneler):
        if s.get("_klip_ses"):
            kn, a, b, yavas = s["_klip_ses"]
            fl.append(f"[{kn}:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,atempo={1 / yavas:.4f},volume={float(s['klip_ses']):.2f},"
                      f"apad,atrim=0:{s['_uzunluk']:.3f},adelay={int(ofset[i] * 1000)}:all=1[ka{i}x]")
            ses_etiket.append(f"[ka{i}x]")
    if ses_etiket:
        fl.append("".join(ses_etiket) + f"amix=inputs={len(ses_etiket)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,apad,atrim=0:{toplam:.3f},afade=t=in:st=0:d=0.05,afade=t=out:st={max(0, toplam - 0.4):.3f}:d=0.4[ses]")
    else:
        fl.append(f"anullsrc=r=44100:cl=mono,atrim=0:{toplam:.3f}[ses]")
    betik = is_d / "filtre.txt"; betik.write_text(";\n".join(fl), encoding="utf-8")
    ad = cfg.get("cikti_adi") or ((video.stem + "-seslendirmeli") if video else "video")
    sesli = klasor / f"{ad}.mp4"
    calistir(["ffmpeg", "-v", "error", "-y"] + girdiler + [*filtre_secenegi(betik), "-map", f"[{onceki}]", "-map", "[ses]",
              "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
              "-movflags", "+faststart", str(sesli)])

    # 3) Altyazi: kelime zamanina senkron, parca parca, ust uste binmez, ekranda surekli ve sabit yerde
    ipuclari = []
    for s in sahneler:
        if not s["_ses"]:
            continue
        parcalar, k = s["_parcalar"], s["_kelimeler"]
        sayilar = [kelime_say(seslendirilecek(p, tel)) for p in parcalar]
        if k and sum(sayilar) == len(k):
            i = 0
            for p, c in zip(parcalar, sayilar):
                ipuclari.append([s["_bas"] + k[i][0], p.rstrip(",;")]); i += c
        else:   # kelime zamani yok/uyusmuyor: karakter oranina gore
            uz = sum(len(p) for p in parcalar); acc = 0
            for p in parcalar:
                ipuclari.append([s["_bas"] + s["_sure"] * acc / uz, p.rstrip(",;")]); acc += len(p)
    if ipuclari:
        ipuclari[0][0] = 0.0
    boyut = int(round(h * float(alt.get("boyut_orani", 0.026))))
    y_vars = (0.765 if not video else 0.78) if hikaye and h > w else 0.80
    y = int(round(h * float(alt.get("y_orani", y_vars))))
    font = alt.get("yazi_tipi", "Arial")
    ass = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {w}", f"PlayResY: {h}", "WrapStyle: 0", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: A,{font},{boyut},&H00FFFFFF,&H00FFFFFF,&H90000000,&H00000000,1,0,0,0,100,100,0,0,3,{max(6, boyut // 4)},0,5,{w // 12},{w // 12},0,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    srt = []
    for j, (b0, metin) in enumerate(ipuclari):
        b1 = (ipuclari[j + 1][0] if j + 1 < len(ipuclari) else toplam) - 0.01
        ass.append(f"Dialogue: 0,{zaman_ass(b0)},{zaman_ass(b1)},A,,0,0,0,,{{\\an5\\pos({w // 2},{y})}}{metin}")
        srt.append(f"{j + 1}\n{zaman_srt(b0)} --> {zaman_srt(b1)}\n{metin}\n")
    (klasor / "altyazi.ass").write_text("\n".join(ass) + "\n", encoding="utf-8")
    (klasor / f"{ad}.srt").write_text("\n".join(srt), encoding="utf-8")
    altyazili = klasor / f"{ad}-altyazili.mp4"
    calistir(["ffmpeg", "-v", "error", "-y", "-i", sesli.name, "-vf", "ass=altyazi.ass", "-c:v", "libx264", "-crf", "19",
              "-preset", "medium", "-c:a", "copy", "-movflags", "+faststart", altyazili.name], cwd=str(klasor))

    # 4) Hikaye siniri asildiysa sahne sinirlarindan bol
    bolumler = []
    if hedef_sn and toplam > hedef_sn + 1.5:
        kesimler, bas = [], 0.0
        sinirlar = [ofset[i] + X / 2 for i in range(1, len(sahneler))] + [toplam]
        onceki_sinir = 0.0
        for sn in sinirlar:
            if sn - bas > hedef_sn and onceki_sinir > bas:
                kesimler.append((bas, onceki_sinir)); bas = onceki_sinir
            onceki_sinir = sn
        kesimler.append((bas, toplam))
        for k, (a, b) in enumerate(kesimler, 1):
            for kaynak, ek in ((altyazili, "-altyazili"), (sesli, "")):
                hedef_d = klasor / f"{ad}{ek}-bolum{k}.mp4"
                calistir(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(kaynak),
                          "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-c:a", "aac", "-b:a", "160k",
                          "-movflags", "+faststart", str(hedef_d)])
            bolumler.append((k, b - a))

    # 5) Kontrol
    kare = max(0.5, toplam / 30)
    calistir(["ffmpeg", "-v", "error", "-y", "-i", str(altyazili), "-vf", f"fps=1/{kare:.3f},scale=200:-2,tile=6x5",
              "-frames:v", "1", str(klasor / "kontrol.png")])
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(sesli), "-vf", "blackdetect=d=0.1:pic_th=0.90:pix_th=0.12",
                        "-an", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    siyah = len(re.findall(r"black_start", r.stderr))
    print(f"\nTAMAM. Sure {toplam:.1f} sn, {len(ipuclari)} altyazi parcasi, siyah ara: {siyah}")
    print(f"  Seslendirmeli : {sesli}\n  Altyazili     : {altyazili}\n  Altyazi (SRT) : {klasor / (ad + '.srt')}\n  Kontrol karesi: {klasor / 'kontrol.png'}")
    if hedef_sn:
        print(f"  Hikaye/durum  : {'UYGUN' if toplam <= 60 else 'UZUN'} ({toplam:.1f} sn; WhatsApp durum ve Instagram hikaye en fazla 60 sn)")
    kalite(altyazili, hedef_sn > 0)
    for k, u in bolumler:
        print(f"  Bolum {k}       : {klasor / f'{ad}-altyazili-bolum{k}.mp4'} ({u:.1f} sn)")


def ikon_ara(kelime):
    d = json.loads((Path(__file__).resolve().parent / "ikon-dizin.json").read_text(encoding="utf-8"))
    bul = [k for k in d if all(p in k for p in kelime.lower().split())]
    print(f"{len(bul)} ikon ({kelime}):\n" + ", ".join(bul[:200]))
    sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.dont_write_bytecode = True
    import parcalar
    print("Teknik parcalar (\"parca\"): " + ", ".join(parcalar.PARCALAR))


def istemler(json_yolu):
    """Gemini (Veo) icin istem listesi: kullanici Gemini uygulamasinda uretir, klipler/ klasorune verilen adla kaydeder."""
    jy = Path(json_yolu).resolve()
    cfg = json.loads(jy.read_text(encoding="utf-8"))
    (jy.parent / "klipler").mkdir(exist_ok=True)
    satir = ["# Gemini (Veo) video istemleri", "",
             "1. gemini.google.com > araçlar > **Video** (Veo) seç.",
             "2. Her istemi ayrı ayrı yapıştır, üretilen videoyu indir.",
             f"3. İndirdiğin dosyayı `{(jy.parent / 'klipler').as_posix()}` klasörüne **her istemin altındaki adla** kaydet.",
             "4. Beğenmediğin klibi (yanlış KKD, bozuk el/alet, yazı) yeniden üret. Hepsi hazır olunca Claude'a \"klipler hazır\" de.",
             "", "Not: Klip yatay (16:9) gelirse sistem dikeye otomatik uyarlar. Klibin sesi varsayılan olarak kullanılmaz.", ""]
    adet = 0
    for n, sh in enumerate(cfg["sahneler"], 1):
        if sh.get("tur") != "klip" or sh.get("atla"):
            continue
        adet += 1
        ad = sh.get("klip") or f"klipler/sahne_{n:02d}.mp4"
        var = (jy.parent / ad).exists()
        satir += [f"## Sahne {n}: {sh.get('baslik', '')}  {'(HAZIR)' if var else ''}", "",
                  f"**Kaydedilecek ad:** `{Path(ad).name}`", "", "```", sh.get("veo_istemi", "(istem yazilmamis)"), "```", ""]
    hedef = jy.parent / "veo-istemleri.md"
    hedef.write_text("\n".join(satir), encoding="utf-8")
    print(f"{adet} klip istemi: {hedef}")


def klip_kontrol(json_yolu):
    """Indirilen klipleri listeler ve her biri icin 6 karelik kontrol gorseli uretir (Claude Read ile inceler)."""
    jy = Path(json_yolu).resolve()
    cfg = json.loads(jy.read_text(encoding="utf-8"))
    eksik = []
    for n, sh in enumerate(cfg["sahneler"], 1):
        if sh.get("tur") != "klip" or sh.get("atla"):
            continue
        k = jy.parent / (sh.get("klip") or f"klipler/sahne_{n:02d}.mp4")
        if not k.exists():
            eksik.append(f"sahne {n}: {k.name}"); continue
        sure_k, kw, kh, kses = klip_bilgi(k)
        kare = jy.parent / "klipler" / f"kontrol_{n:02d}.png"
        calistir(["ffmpeg", "-v", "error", "-y", "-i", str(k), "-vf", f"fps={6 / max(sure_k, 1):.4f},scale=320:-2,tile=6x1:padding=4",
                  "-frames:v", "1", str(kare)])
        print(f"sahne {n:2d}: {k.name}  {sure_k:.1f} sn  {kw}x{kh}  {'sesli' if kses else 'sessiz'}  -> {kare}")
    for e in eksik:
        print("EKSIK  " + e)
    print("Kareleri incele: dogru KKD (baret, gozluk, eldiven), aletin dogru kullanimi, bozuk el/yuz/yazi, logo. Sorunlu klibi yeniden urettir.")


def olustur(json_yolu, sadece_gorsel=False):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import gorsel
    jy = Path(json_yolu).resolve()
    cfg = json.loads(jy.read_text(encoding="utf-8"))
    cfg.pop("video", None)
    cfg.update(ayar_birlestir(cfg))
    gorsel.gorselleri_uret(cfg, jy.parent)
    liste = jy.parent / "_is" / "gorseller.txt"; liste.parent.mkdir(exist_ok=True)
    liste.write_text("".join(f"file '{(jy.parent / x['goruntu']).as_posix()}'\n" for x in cfg["sahneler"] if x.get("goruntu")), encoding="utf-8")
    calistir(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(liste), "-vf", "scale=216:-2,tile=8x3:padding=6",
              "-frames:v", "1", str(jy.parent / "gorseller.png")])
    print(f"Gorsellerin toplu gorunumu: {jy.parent / 'gorseller.png'}")
    if not sadece_gorsel:
        uret_cfg(cfg, jy.parent)


def main():
    # Windows konsolu/yonlendirme cp1252 olabilir: Turkce karakterde cokmesin
    for akis in (sys.stdout, sys.stderr):
        try:
            akis.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Videoya Turkce seslendirme + senkron altyazi (repokurulum)")
    alt = ap.add_subparsers(dest="komut", required=True)
    a = alt.add_parser("analiz"); a.add_argument("video"); a.add_argument("--klasor")
    u = alt.add_parser("uret"); u.add_argument("sahneler_json")
    o = alt.add_parser("olustur"); o.add_argument("senaryo_json")
    g = alt.add_parser("gorsel"); g.add_argument("senaryo_json")
    yp = alt.add_parser("yeni"); yp.add_argument("ad"); yp.add_argument("--tur", default="tanitim", choices=["tanitim", "rehber", "gercekci"])
    kp = alt.add_parser("kalite"); kp.add_argument("video")
    ia = alt.add_parser("ikonlar"); ia.add_argument("kelime", nargs="?", default="")
    i_ = alt.add_parser("istemler"); i_.add_argument("senaryo_json")
    kk = alt.add_parser("klipler"); kk.add_argument("senaryo_json")
    d = alt.add_parser("dene"); d.add_argument("metin"); d.add_argument("--ses", default="tr-TR-EmelNeural")
    d.add_argument("--hiz", default="+4%"); d.add_argument("--json")
    x = ap.parse_args()
    for arac in ("ffmpeg", "ffprobe"):
        if not shutil.which(arac):
            sys.exit(f"HATA: {arac} bulunamadi (Repo Kurulum'da FFmpeg bilesenini kur).")
    if x.komut == "analiz":
        analiz(x.video, x.klasor)
    elif x.komut == "uret":
        uret(x.sahneler_json)
    elif x.komut == "olustur":
        olustur(x.senaryo_json)
    elif x.komut == "yeni":
        yeni_proje(x.ad, x.tur)
    elif x.komut == "kalite":
        sys.exit(0 if kalite(x.video) else 1)
    elif x.komut == "ikonlar":
        ikon_ara(x.kelime)
    elif x.komut == "istemler":
        istemler(x.senaryo_json)
    elif x.komut == "klipler":
        klip_kontrol(x.senaryo_json)
    elif x.komut == "gorsel":
        olustur(x.senaryo_json, sadece_gorsel=True)
    else:
        deneme(x.metin, x.ses, x.hiz, x.json)


if __name__ == "__main__":
    main()
