"""Video anuncio v3 · escenas generadas con IA + voz + subtítulos + música · 9:16
Uso: python3 video_v3_escenas.py <carpeta_imagenes> <vo.mp3> <vo.mp3.json> <carpeta_salida>
Imágenes esperadas (944x1680): 4=sofá relajada, 5=llega cansada (tacones), 6=dedo en botón,
7=collage de usos, 8=abuelo en mecedora, 3=caja del producto.
"""
import sys, json, math, random, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

IMG, VO, VOJ, OUT = sys.argv[1:5]
os.makedirs(f"{OUT}/frames", exist_ok=True)
W, H, FPS = 1080, 1920, 30
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_fc = {}
def F(s):
    s = max(8, int(s))
    if s not in _fc: _fc[s] = ImageFont.truetype(FB, s)
    return _fc[s]
def ease(t): t = max(0., min(1., t)); return 1 - (1 - t) ** 3
def inout(t): t = max(0., min(1., t)); return t * t * (3 - 2 * t)
def back(t):
    t = max(0., min(1., t)); c = 1.7
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
YEL = (255, 214, 0); RED = (229, 57, 53); GRN = (37, 211, 102); WHT = (255, 255, 255); BLK = (0, 0, 0)

def L(n): return Image.open(f"{IMG}/{n}.webp").convert("RGB")
A, B, C, COL, D, BOX = L(5), L(4), L(6), L(7), L(8), L(3)
# paneles del collage (x0,y0,x1,y1)
P_TOP, P_OFI, P_BED = COL.crop((0, 0, 944, 570)), COL.crop((0, 1120, 460, 1680)), COL.crop((465, 1120, 944, 1680))

_bg = {}
def fit(src, key, zoom=1.0, focus=(0.5, 0.5), shake=0.0, t=0.0):
    """Llena 9:16 (cover) con zoom y punto de enfoque; fondo desenfocado si la imagen no cubre."""
    base = max(W / src.width, H / src.height) * zoom
    fw, fh = int(src.width * base), int(src.height * base)
    x = int(W / 2 - focus[0] * fw); y = int(H / 2 - focus[1] * fh)
    x = min(0, max(W - fw, x)) if fw >= W else (W - fw) // 2
    y = min(0, max(H - fh, y)) if fh >= H else (H - fh) // 2
    if shake: x += int(math.sin(t * 57) * 10 * shake); y += int(math.cos(t * 43) * 10 * shake)
    if key not in _bg:
        r = max(W / src.width, H / src.height) * 1.1
        b = src.resize((int(src.width * r), int(src.height * r))).crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(40))
        _bg[key] = Image.blend(b, Image.new("RGB", (W, H), (12, 12, 16)), 0.35)
    can = _bg[key].copy()
    can.paste(src.resize((fw, fh), Image.BILINEAR), (x, y)); return can

def chip(d, text, cxp, y, size, fg=BLK, bg=YEL, p=1.0, pad=26, alpha=245):
    if p <= 0: return
    sc = back(p); f = F(size * sc); lh = int(size * sc * 1.25)
    for i, l in enumerate(text.split("\n")):
        bb = d.textbbox((0, 0), l, font=f); w = bb[2] - bb[0]; h = bb[3] - bb[1]
        yy = y + i * (lh + 10); x = cxp - w // 2
        d.rounded_rectangle((x - pad, yy - pad // 2, x + w + pad, yy + h + pad), radius=22, fill=bg + (int(alpha * min(1, p * 2)),))
        d.text((x - bb[0], yy - bb[1] + pad // 4), l, font=f, fill=fg)

def captions(d, sent, t):
    for typ, st, du, txt in sent:
        if st <= t < st + du + 0.05:
            words = txt.split(); wts = [len(w) + 2 for w in words]; tot = sum(wts)
            acc = st; times = []
            for w_ in wts: times.append(acc); acc += du * w_ / tot
            idx = max([i for i, tt in enumerate(times) if tt <= t] or [0])
            g0 = (idx // 4) * 4; parts = [(w, i + g0 == idx) for i, w in enumerate(words[g0:g0 + 4])]
            size = 66; sp = d.textlength(" ", font=F(size)) + 6
            widths = [d.textlength(w, font=F(size * (1.12 if c else 1))) + sp for w, c in parts]
            x = (W - sum(widths)) // 2; y = 1500
            for (w, c), wd in zip(parts, widths):
                d.text((x, y - (6 if c else 0)), w, font=F(size * (1.12 if c else 1)), fill=YEL if c else WHT, stroke_width=7, stroke_fill=BLK)
                x += wd
            return

random.seed(4)
SNOW = [(random.random() * W, random.random() * H, random.uniform(3, 9), random.uniform(60, 160)) for _ in range(90)]
def snow(d, t):
    for x, y, r, v in SNOW:
        yy = (y + v * t) % H; xx = x + math.sin(t * 1.5 + y) * 20
        d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=(255, 255, 255, 190))

def press_ring(d, x, y, k):
    r = 30 + 90 * k
    d.ellipse((x - r, y - r, x + r, y + r), outline=(255, 255, 255, int(255 * (1 - k))), width=8)

def pressure(d, ts, cx, cy, h, spread, p):
    """Flechas de presión de aire hacia la funda + ondas."""
    if p <= 0: return
    k = (math.sin(ts * 2 * math.pi * 0.9) + 1) / 2
    for side in (-1, 1):
        for j in range(3):
            x = cx + side * (spread + 60 - 35 * k); y = cy - h / 2 + j * h / 2
            d.polygon([(x, y), (x + side * 60, y - 32), (x + side * 60, y + 32)], fill=(60, 220, 255, int(230 * p)))
            d.rectangle((min(x + side * 60, x + side * 120), y - 10, max(x + side * 60, x + side * 120), y + 10), fill=(60, 220, 255, int(230 * p)))

sent = json.load(open(VOJ)); T = [s[1] for s in sent]
DUR = sent[-1][1] + sent[-1][2] + 0.8
starts = [0.0, T[1], T[2], T[3], T[4], T[5]]
def scene_of(t): return max(i for i, s in enumerate(starts) if t >= s)

N = int(DUR * FPS); cuts = []; last_sub = None
for n in range(N):
    t = n / FPS; k = scene_of(t); ts = t - starts[k]
    sd = (starts[k + 1] if k + 1 < len(starts) else DUR) - starts[k]; u = ts / sd
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov); sub = k

    if k == 0:   # llega cansada: acercamiento lento a ella quitándose el tacón
        im = fit(A, "A", 1.05 + 0.18 * inout(u), (0.32, 0.55 + 0.1 * u), shake=max(0, 1 - ts / 0.5), t=t)
        chip(d, "¿PIERNAS CANSADAS?", W // 2, 230, 82, p=ts / 0.3)
        chip(d, "después de un día largo", W // 2, 380, 46, WHT, RED, p=(ts - 0.7) / 0.3)
    elif k == 1:  # dedo en el botón: zoom al control + pulsación
        im = fit(C, "C", 1.0 + 0.35 * inout(u), (0.55, 0.45))
        z = 1.0 + 0.35 * inout(u); base = max(W / C.width, H / C.height) * z
        bx = W / 2 + (0.585 - 0.55) * C.width * base; by = H / 2 + (0.465 - 0.45) * C.height * base
        press_ring(d, bx, by, (ts % 0.9) / 0.9)
        chip(d, "UN SOLO BOTÓN", W // 2, 230, 84, p=ts / 0.3)
    elif k == 2:  # sofá: presión de aire + calor
        z = 1.0 + 0.55 * inout(min(1, u * 1.4))
        im = fit(B, "B", z, (0.45, 0.5 + 0.15 * inout(u)))
        base = max(W / B.width, H / B.height) * z
        sx = W / 2 + (0.40 - 0.45) * B.width * base
        sy = H / 2 + (0.67 - (0.5 + 0.15 * inout(u))) * B.height * base
        pressure(d, ts, sx, sy, 300 * base / 1.3, 120 * base / 1.3, ease((ts - 0.6) / 0.4))
        chip(d, "PRESIÓN DE AIRE + CALOR", W // 2, 230, 66, p=ts / 0.3)
    elif k == 3:  # usos: 3 cortes rápidos del collage
        third = sd / 3; j = min(2, int(ts / third)); tj = ts - j * third; sub = (3, j)
        src, key, lab = [(P_TOP, "p1", "EN CASA"), (P_OFI, "p2", "EN LA OFICINA"), (P_BED, "p3", "DONDE QUIERAS")][j]
        im = fit(src, key, 1.0 + 0.12 * (tj / third), (0.5, 0.5))
        chip(d, "✓ " + lab, W // 2, 260, 74, p=tj / 0.25)
    elif k == 4:  # abuelo: regalo navidad
        im = fit(D, "D", 1.15 - 0.12 * inout(u), (0.55, 0.45))
        snow(d, t)
        chip(d, "EL REGALO PERFECTO", W // 2, 210, 74, WHT, RED, p=ts / 0.3)
        chip(d, "para mamá, papá o los abuelos", W // 2, 360, 48, BLK, YEL, p=(ts - 0.8) / 0.3)
    else:  # CTA sobre la escena del sofá oscurecida
        im = fit(B, "B", 1.1 + 0.05 * u, (0.5, 0.5))
        im = Image.blend(im, Image.new("RGB", (W, H), (8, 8, 12)), 0.55)
        snow(d, t)
        chip(d, "PRECIO ESPECIAL", W // 2, 260, 58, WHT, (30, 30, 35), p=ts / 0.3)
        chip(d, "$129.900", W // 2, 380, 140, WHT, RED, p=(ts - 0.2) / 0.35, pad=40)
        chip(d, "PAGAS AL RECIBIR\nEN TODA COLOMBIA", W // 2, 690, 64, BLK, YEL, p=(ts - 0.8) / 0.3)
        pul = 1 + 0.06 * math.sin(ts * 9) if ts > 2.3 else 1
        chip(d, "ESCRÍBENOS POR WHATSAPP", W // 2, 1010, int(60 * pul), WHT, GRN, p=(ts - 2.2) / 0.3)

    if last_sub is not None and sub != last_sub: cuts.append(t)
    last_sub = sub
    captions(d, sent, t)
    d.rectangle((0, 0, int(W * t / DUR), 12), fill=YEL + (255,))
    d.text((W - 30, H - 40), "Imágenes ilustrativas creadas con IA", font=F(24), fill=(255, 255, 255, 160), anchor="rs")
    if cuts and 0 <= t - cuts[-1] < 0.1:
        ov = Image.alpha_composite(ov, Image.new("RGBA", (W, H), (255, 255, 255, int(150 * (1 - (t - cuts[-1]) / 0.1)))))
    Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB").save(f"{OUT}/frames/f{n:05d}.jpg", quality=90)

# ---------- audio ----------
SR = 44100; Ls = int(DUR * SR); mus = np.zeros(Ls); bpm = 100; beat = 60 / bpm
def env(n, a=0.005, r=0.2): x = np.arange(n) / SR; return np.minimum(1, x / a) * np.exp(-x / r)
chords = [[220.0, 261.6, 329.6], [174.6, 220.0, 261.6], [261.6, 329.6, 392.0], [196.0, 246.9, 293.7]]
for b in range(int(DUR / beat) + 1):
    s = int(b * beat * SR)
    if s >= Ls: break
    n = min(Ls - s, int(0.5 * SR)); x = np.arange(n) / SR
    if b % 2 == 0: mus[s:s + n] += 0.8 * np.sin(2 * np.pi * (50 + 90 * np.exp(-x * 30)) * x) * env(n, 0.001, 0.12)
    else: mus[s:s + n] += 0.3 * np.random.randn(n) * env(n, 0.001, 0.05)
    for h in (0, 0.5):
        hs = int((b + h) * beat * SR)
        if hs < Ls:
            hn = min(Ls - hs, int(0.05 * SR)); hh = np.diff(np.random.randn(hn), prepend=0)
            mus[hs:hs + hn] += 0.1 * hh * env(hn, 0.001, 0.015)
    if b % 4 == 0:
        ch = chords[(b // 4) % 4]; n = min(Ls - s, int(4 * beat * SR)); x = np.arange(n) / SR
        pad = sum(np.sin(2 * np.pi * f * x) + 0.3 * np.sin(4 * np.pi * f * x) for f in ch) / 3
        mus[s:s + n] += 0.2 * pad * np.minimum(1, x / 0.05) * np.exp(-x / 2.5)
        mus[s:s + n] += 0.3 * np.sin(np.pi * ch[0] * x) * np.exp(-x / 0.9)
mus /= np.max(np.abs(mus)) + 1e-9
sfx = np.zeros(Ls)
for c in [0.0] + cuts:
    s = max(0, int((c - 0.15) * SR)); n = min(Ls - s, int(0.35 * SR)); x = np.arange(n) / SR
    sfx[s:s + n] += 0.5 * np.convolve(np.random.randn(n), np.ones(12) / 12, "same") * np.sin(np.pi * x / x[-1]) ** 2
s2, e2 = int(starts[2] * SR), int(starts[3] * SR); x = np.arange(e2 - s2) / SR
sfx[s2:e2] += 0.5 * np.convolve(np.random.randn(e2 - s2), np.ones(40) / 40, "same") * np.sin(np.pi * ((x * 0.9) % 1)) ** 2
import wave as wv
def wav(p, sig):
    with wv.open(p, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((np.clip(sig, -1, 1) * 32767).astype(np.int16).tobytes())
wav(f"{OUT}/music.wav", mus * 0.9); wav(f"{OUT}/sfx.wav", sfx / (np.max(np.abs(sfx)) + 1e-9))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{OUT}/frames/f%05d.jpg",
    "-i", VO, "-i", f"{OUT}/music.wav", "-i", f"{OUT}/sfx.wav", "-filter_complex",
    "[1:a]volume=1.6,aresample=44100,aformat=channel_layouts=mono,asplit[vo1][vo2];[2:a]volume=0.16[mu];[3:a]volume=0.2[fx];"
    "[mu][vo1]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300[md];"
    "[vo2][md][fx]amix=inputs=3:normalize=0,alimiter=limit=0.95[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium",
    "-c:a", "aac", "-b:a", "192k", "-t", f"{DUR:.2f}", "-movflags", "+faststart", f"{OUT}/masajeador_v3.mp4"], check=True)
print("ok", N, DUR)
