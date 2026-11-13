# repokurulum: video-seslendirme - 3B gorunumlu teknik parca cizimleri (SVG). Her fonksiyon tam bir <svg> dondurur.
# Kullanim (senaryo): {"parca": "vana", "x": 300, "y": 260, "boyut": 260, "secenek": {...}}
import math

_id = [0]


def _yeni(on):
    _id[0] += 1
    return f"{on}{_id[0]}"


def _silindir_yatay(gid, a="#c9d3de", b="#6f7d8c"):
    return (f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{b}"/>'
            f'<stop offset=".35" stop-color="{a}"/><stop offset=".55" stop-color="#eef3f8"/><stop offset="1" stop-color="{b}"/></linearGradient>')


def _silindir_dikey(gid, a="#c9d3de", b="#6f7d8c"):
    return (f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{b}"/>'
            f'<stop offset=".4" stop-color="{a}"/><stop offset=".6" stop-color="#eef3f8"/><stop offset="1" stop-color="{b}"/></linearGradient>')


def vana(renk="#e1251b", govde=True, **_):
    g1, g2, g3 = _yeni("v"), _yeni("v"), _yeni("v")
    kol = ""
    for i in range(6):
        a = math.radians(i * 60 + 15)
        kol += f'<line x1="200" y1="150" x2="{200 + 112 * math.cos(a):.1f}" y2="{150 + 112 * math.sin(a) * 0.55:.1f}" stroke="url(#{g2})" stroke-width="16" stroke-linecap="round"/>'
    gv = (f'<rect x="185" y="160" width="30" height="120" fill="url(#{g3})"/>'
          f'<path d="M110 280 h180 a30 30 0 0 1 30 30 v40 a30 30 0 0 1 -30 30 h-180 a30 30 0 0 1 -30 -30 v-40 a30 30 0 0 1 30 -30z" fill="url(#{g3})"/>'
          f'<rect x="0" y="300" width="80" height="60" fill="url(#{g1})"/><rect x="320" y="300" width="80" height="60" fill="url(#{g1})"/>') if govde else ""
    return (f'<svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg"><defs>{_silindir_yatay(g1)}'
            f'<linearGradient id="{g2}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff6b5e"/><stop offset=".5" stop-color="{renk}"/><stop offset="1" stop-color="#7a120c"/></linearGradient>'
            f'{_silindir_dikey(g3, "#b8c2cd", "#4f5b68")}</defs>{gv}'
            f'<ellipse cx="200" cy="158" rx="120" ry="68" fill="#5a0d08" opacity=".5"/>'
            f'<ellipse cx="200" cy="150" rx="118" ry="65" fill="none" stroke="url(#{g2})" stroke-width="22"/>{kol}'
            f'<ellipse cx="200" cy="150" rx="26" ry="16" fill="#3b4652"/><ellipse cx="196" cy="146" rx="10" ry="5" fill="#9aa6b2"/></svg>')


def boru(bant=False, sizinti=False, uzunluk=600, **_):
    g1, g2 = _yeni("b"), _yeni("b")
    t = (f'<svg viewBox="0 0 {uzunluk} 300" xmlns="http://www.w3.org/2000/svg"><defs>{_silindir_yatay(g1)}'
         f'<linearGradient id="{g2}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9da5ad"/><stop offset=".4" stop-color="#e9ecef"/><stop offset="1" stop-color="#8d959d"/></linearGradient></defs>'
         f'<ellipse cx="{uzunluk / 2}" cy="200" rx="{uzunluk * 0.45}" ry="14" fill="#000" opacity=".25"/>'
         f'<rect x="0" y="70" width="{uzunluk}" height="100" fill="url(#{g1})"/>'
         f'<ellipse cx="{uzunluk - 2}" cy="120" rx="16" ry="50" fill="#5b6876"/><ellipse cx="{uzunluk - 2}" cy="120" rx="9" ry="34" fill="#2b333c"/>')
    if bant:
        m = uzunluk / 2
        t += (f'<path d="M{m - 75} 58 L{m + 70} 64 L{m + 78} 178 L{m - 70} 184 Z" fill="url(#{g2})" stroke="#7d858d" stroke-width="3"/>'
              + "".join(f'<path d="M{m - 60 + i * 30} 62 l6 118" stroke="#b3b9bf" stroke-width="3"/>' for i in range(5))
              + f'<path d="M{m + 70} 150 l45 18 l-40 4 z" fill="#c9ced3"/>')
    if sizinti:
        m = uzunluk / 2
        t += "".join(f'<path d="M{m} {y} c-10 14 -10 22 0 26 c10 -4 10 -12 0 -26z" fill="#4aa3ff"/>' for y in (195, 228, 262))
    return t + "</svg>"


def manometre(deger=0.15, carpi=False, **_):
    g1, g2 = _yeni("m"), _yeni("m")
    t = (f'<svg viewBox="0 0 400 420" xmlns="http://www.w3.org/2000/svg"><defs>'
         f'<radialGradient id="{g1}" cx=".4" cy=".35" r=".8"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#d6dde5"/></radialGradient>'
         f'<linearGradient id="{g2}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e5ebf1"/><stop offset=".5" stop-color="#7d8a98"/><stop offset="1" stop-color="#3f4a56"/></linearGradient></defs>'
         f'<rect x="178" y="330" width="44" height="80" fill="url(#{g2})"/>'
         f'<circle cx="200" cy="190" r="170" fill="url(#{g2})"/><circle cx="200" cy="190" r="146" fill="url(#{g1})"/>'
         f'<path d="M95 270 A130 130 0 0 1 120 100" stroke="#e1251b" stroke-width="16" fill="none" opacity=".85"/>'
         f'<path d="M280 100 A130 130 0 0 1 305 270" stroke="#22a55a" stroke-width="16" fill="none" opacity=".85"/>')
    for i in range(11):
        a = math.radians(135 + i * 27)
        t += f'<line x1="{200 + 128 * math.cos(a):.1f}" y1="{190 + 128 * math.sin(a):.1f}" x2="{200 + 108 * math.cos(a):.1f}" y2="{190 + 108 * math.sin(a):.1f}" stroke="#2b333c" stroke-width="6"/>'
    a = math.radians(135 + deger * 270)
    t += (f'<line x1="200" y1="190" x2="{200 + 110 * math.cos(a):.1f}" y2="{190 + 110 * math.sin(a):.1f}" stroke="#e1251b" stroke-width="10" stroke-linecap="round"/>'
          f'<circle cx="200" cy="190" r="18" fill="#2b333c"/><text x="200" y="262" font-size="30" font-weight="800" text-anchor="middle" fill="#2b333c" font-family="Arial">bar</text>'
          f'<ellipse cx="160" cy="120" rx="70" ry="30" fill="#fff" opacity=".45" transform="rotate(-25 160 120)"/>')
    return t + "</svg>"


def tarak(kirik=None, **_):
    g1, g2, g3 = _yeni("t"), _yeni("t"), _yeni("t")
    t = (f'<svg viewBox="0 0 600 360" xmlns="http://www.w3.org/2000/svg"><defs>'
         f'<linearGradient id="{g1}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9e2cf"/><stop offset="1" stop-color="#a99a78"/></linearGradient>'
         f'<linearGradient id="{g2}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d7cbb0"/><stop offset="1" stop-color="#6e6450"/></linearGradient>'
         f'<linearGradient id="{g3}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a4654"/><stop offset="1" stop-color="#151b22"/></linearGradient></defs>'
         f'<path d="M20 60 L580 60 L560 130 L40 130 Z" fill="url(#{g1})"/><path d="M40 130 L560 130 L560 150 L40 150 Z" fill="#7c705a"/>'
         f'<path d="M0 230 L600 230 L600 360 L0 360 Z" fill="url(#{g3})"/>'
         + "".join(f'<rect x="{6 + i * 24}" y="236" width="14" height="124" fill="#2a343f"/><rect x="{6 + i * 24}" y="236" width="4" height="124" fill="#4a5867"/>' for i in range(25)))
    for i in range(22):
        x = 48 + i * 23
        h = 85 if i != kirik else 30
        t += f'<path d="M{x} 150 l14 0 l-3 {h} l-8 0 z" fill="url(#{g2})"/>'
        if i == kirik:
            t += f'<path d="M{x} {150 + h} l4 -6 l3 5 l4 -7 l3 8" stroke="#3b3326" stroke-width="2" fill="none"/>'
    return t + "</svg>"


def yuruyen_merdiven(**_):
    g1, g2 = _yeni("y"), _yeni("y")
    adim = "".join(f'<path d="M{150 + i * 34} {392 - i * 30} l34 0 l0 -30 l-34 0 z" fill="#5d6c7c"/><path d="M{150 + i * 34} {392 - i * 30} l34 0 l6 5 l-34 0 z" fill="#c3ccd6"/>' for i in range(9))
    return (f'<svg viewBox="0 0 600 480" xmlns="http://www.w3.org/2000/svg"><defs>'
            f'<linearGradient id="{g1}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a7b4c2"/><stop offset="1" stop-color="#46525f"/></linearGradient>'
            f'<linearGradient id="{g2}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#f6b420"/><stop offset="1" stop-color="#c58a06"/></linearGradient></defs>'
            f'<ellipse cx="300" cy="455" rx="260" ry="18" fill="#000" opacity=".3"/>'
            f'<path d="M30 400 L150 400 L460 130 L580 130 L580 175 L470 175 L160 445 L30 445 Z" fill="url(#{g1})"/>{adim}'
            f'<path d="M30 330 L150 330 L460 60 L580 60" stroke="#1c232b" stroke-width="22" fill="none" stroke-linecap="round"/>'
            f'<path d="M30 330 L150 330 L460 60 L580 60" stroke="url(#{g2})" stroke-width="10" fill="none" stroke-linecap="round"/></svg>')


def sensor(isik="#18c25a", **_):
    g1, g2 = _yeni("s"), _yeni("s")
    return (f'<svg viewBox="0 0 400 420" xmlns="http://www.w3.org/2000/svg"><defs>'
            f'<linearGradient id="{g1}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5b6b7c"/><stop offset="1" stop-color="#1e262f"/></linearGradient>'
            f'<radialGradient id="{g2}" cx=".4" cy=".35" r=".7"><stop offset="0" stop-color="#eafff1"/><stop offset=".35" stop-color="{isik}"/><stop offset="1" stop-color="#0a5a2a"/></radialGradient></defs>'
            f'<ellipse cx="200" cy="395" rx="120" ry="16" fill="#000" opacity=".3"/><rect x="175" y="250" width="50" height="140" fill="url(#{g1})"/>'
            f'<rect x="70" y="60" width="260" height="210" rx="34" fill="url(#{g1})"/><rect x="82" y="70" width="236" height="20" rx="10" fill="#fff" opacity=".12"/>'
            f'<circle cx="200" cy="165" r="80" fill="{isik}" opacity=".25"/><circle cx="200" cy="165" r="52" fill="url(#{g2})"/></svg>')


def yangin_dolabi(acik=True, **_):
    g1, g2 = _yeni("d"), _yeni("d")
    hortum = "".join(f'<circle cx="200" cy="215" r="{r}" fill="none" stroke="#e8e2d0" stroke-width="15"/><circle cx="200" cy="215" r="{r}" fill="none" stroke="#b9b09a" stroke-width="3"/>' for r in (110, 88, 66))
    kapak = f'<path d="M330 40 L395 70 L395 410 L330 440 Z" fill="url(#{g1})" opacity=".95"/>' if acik else ""
    return (f'<svg viewBox="0 0 420 470" xmlns="http://www.w3.org/2000/svg"><defs>'
            f'<linearGradient id="{g1}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff5a4f"/><stop offset="1" stop-color="#8f140e"/></linearGradient>'
            f'<radialGradient id="{g2}" cx=".5" cy=".5" r=".6"><stop offset="0" stop-color="#5a1612"/><stop offset="1" stop-color="#2b0907"/></radialGradient></defs>'
            f'<ellipse cx="200" cy="455" rx="190" ry="14" fill="#000" opacity=".3"/>'
            f'<rect x="40" y="30" width="300" height="420" rx="14" fill="url(#{g1})"/><rect x="62" y="52" width="256" height="376" rx="8" fill="url(#{g2})"/>'
            f'{hortum}<circle cx="200" cy="215" r="34" fill="#c7cdd3"/><circle cx="200" cy="215" r="12" fill="#5b6876"/>'
            f'<path d="M200 330 v50 q0 20 30 20 h40" fill="none" stroke="#e8e2d0" stroke-width="15" stroke-linecap="round"/>'
            f'<rect x="268" y="388" width="44" height="22" rx="6" fill="#2b333c"/>{kapak}</svg>')


def boru_kesiti(kirec=0.6, **_):
    g1 = _yeni("k")
    tas = ""
    for i in range(16):
        a = i * 2 * math.pi / 16
        r = 118 - kirec * 10
        tas += f'<circle cx="{200 + r * math.cos(a):.1f}" cy="{200 + r * math.sin(a):.1f}" r="{18 + kirec * 26 + (i % 3) * 6:.1f}" fill="#e6d7ae" stroke="#c4b182" stroke-width="3"/>'
    ic = max(30, 120 - kirec * 110)
    return (f'<svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg"><defs>'
            f'<radialGradient id="{g1}" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#e3e9ef"/><stop offset="1" stop-color="#5c6977"/></radialGradient></defs>'
            f'<circle cx="200" cy="200" r="190" fill="url(#{g1})"/><circle cx="200" cy="200" r="160" fill="#efe3c3"/>{tas}'
            f'<circle cx="200" cy="200" r="{ic:.0f}" fill="#0b1e33"/><circle cx="200" cy="200" r="{ic:.0f}" fill="#4aa3ff" opacity=".25"/></svg>')


def acil_stop(**_):
    g1, g2 = _yeni("a"), _yeni("a")
    return (f'<svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg"><defs>'
            f'<radialGradient id="{g1}" cx=".38" cy=".3" r=".75"><stop offset="0" stop-color="#ff8a80"/><stop offset=".45" stop-color="#e1251b"/><stop offset="1" stop-color="#6d0f0a"/></radialGradient>'
            f'<linearGradient id="{g2}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd54a"/><stop offset="1" stop-color="#c79400"/></linearGradient></defs>'
            f'<ellipse cx="200" cy="330" rx="170" ry="40" fill="#000" opacity=".3"/><rect x="40" y="200" width="320" height="120" rx="24" fill="url(#{g2})"/>'
            f'<ellipse cx="200" cy="215" rx="110" ry="40" fill="#5b0c08"/><path d="M95 200 a105 90 0 0 1 210 0 v15 a105 40 0 0 1 -210 0 z" fill="url(#{g1})"/>'
            f'<ellipse cx="165" cy="150" rx="40" ry="18" fill="#fff" opacity=".4"/></svg>')


def pano(acik=True, **_):
    g1, g2 = _yeni("p"), _yeni("p")
    sigortalar = "".join(f'<rect x="{90 + i * 38}" y="{y}" width="28" height="64" rx="4" fill="#f4f6f8"/><rect x="{97 + i * 38}" y="{y + 22}" width="14" height="20" fill="#{c}"/>' for y, c in ((120, "2b333c"), (230, "e1251b")) for i in range(6))
    return (f'<svg viewBox="0 0 420 470" xmlns="http://www.w3.org/2000/svg"><defs>'
            f'<linearGradient id="{g1}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d9dfe5"/><stop offset="1" stop-color="#7c8794"/></linearGradient>'
            f'<linearGradient id="{g2}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2f3944"/><stop offset="1" stop-color="#1a2028"/></linearGradient></defs>'
            f'<ellipse cx="210" cy="455" rx="190" ry="14" fill="#000" opacity=".3"/><rect x="50" y="30" width="320" height="420" rx="12" fill="url(#{g1})"/>'
            f'<rect x="70" y="52" width="280" height="376" rx="6" fill="url(#{g2})"/><rect x="80" y="108" width="260" height="10" fill="#9aa6b2"/><rect x="80" y="218" width="260" height="10" fill="#9aa6b2"/>'
            f'{sigortalar}<path d="M90 330 h240 M90 360 h240 M90 390 h240" stroke="#f6b420" stroke-width="6"/>'
            f'<path d="M190 70 l-18 34 h16 l-10 26 l28 -38 h-16 l12 -22z" fill="#f6b420"/></svg>')


PARCALAR = {"vana": vana, "boru": boru, "manometre": manometre, "tarak": tarak, "yuruyen_merdiven": yuruyen_merdiven,
            "sensor": sensor, "yangin_dolabi": yangin_dolabi, "boru_kesiti": boru_kesiti, "acil_stop": acil_stop, "pano": pano}
