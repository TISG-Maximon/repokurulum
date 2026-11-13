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
        "motor": "edge", "ses": "tr-TR-EmelNeural", "hiz": "+4%", "piper_ses": "tr_TR-dfki-medium",
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


def uret(json_yolu):
    jy = Path(json_yolu).resolve()
    cfg = json.loads(jy.read_text(encoding="utf-8"))
    uret_cfg(cfg, jy.parent)


def uret_cfg(cfg, klasor):
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

    def sesleri_uret():
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
            fl.append(f"[{n}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
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
        fl.append("".join(ses_etiket) + f"amix=inputs={len(ses_etiket)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,apad,atrim=0:{toplam:.3f}[ses]")
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
    for k, u in bolumler:
        print(f"  Bolum {k}       : {klasor / f'{ad}-altyazili-bolum{k}.mp4'} ({u:.1f} sn)")


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
