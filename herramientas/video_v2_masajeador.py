"""Video anuncio v2 · masajeador de pantorrilla · 9:16
Uso: python3 video_v2_masajeador.py <foto_pierna> <foto_caja> <vo.mp3> <vo.mp3.json> <carpeta_salida>
Genera frames + música + SFX y los une con ffmpeg (ver bloque final).
"""
import sys, json, math, random, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

LEG, BOX, VO, VOJ, OUT = sys.argv[1:6]
os.makedirs(f"{OUT}/frames", exist_ok=True)
W, H, FPS = 1080, 1920, 30
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_fc = {}
def F(s):
    s = max(8, int(s))
    if s not in _fc: _fc[s] = ImageFont.truetype(FB, s)
    return _fc[s]
def ease(t): t = max(0., min(1., t)); return 1 - (1 - t) ** 3
def back(t):  # ease-out-back (rebote)
    t = max(0., min(1., t)); c = 1.7
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2

YEL = (255, 214, 0); RED = (229, 57, 53); GRN = (37, 211, 102); WHT = (255, 255, 255); BLK = (0, 0, 0)

# ---------- imágenes base ----------
leg = Image.open(LEG).convert("RGB").crop((0, 0, 680, 680))
box = Image.open(BOX).convert("RGB")
# polígono de la funda (coords en la foto de la pierna)
SLEEVE = [(440, 118), (566, 150), (472, 487), (338, 466)]
SCREEN = (455, 242, 529, 284)       # pantalla negra del control
CTRL = (423, 232, 532, 390)

def sleeve_mask(size, dil=0, blur=6):
    m = Image.new("L", size, 0); ImageDraw.Draw(m).polygon(SLEEVE, fill=255)
    if dil: m = m.filter(ImageFilter.MaxFilter(dil * 2 + 1))
    return m.filter(ImageFilter.GaussianBlur(blur))
MASK = sleeve_mask(leg.size, dil=3)
MASK_IN = sleeve_mask(leg.size, dil=0, blur=3)
cx = sum(p[0] for p in SLEEVE) / 4; cy = sum(p[1] for p in SLEEVE) / 4

def leg_frame(t_abs, inflate=0.0, wave=None, screen_mode=None, heat=0.0):
    """Devuelve la foto de la pierna con efectos de funcionamiento."""
    im = leg.copy()
    if inflate > 0:
        s = 1 + 0.055 * inflate
        big = leg.resize((int(680 * s), int(680 * s)), Image.LANCZOS)
        ox, oy = int(cx * s - cx), int(cy * s - cy)
        big = big.crop((ox, oy, ox + 680, oy + 680))
        bm = sleeve_mask(leg.size, dil=int(3 + 18 * inflate), blur=10)
        im = Image.composite(big, im, bm)
        # sombra/luz sutil de "aire"
        light = Image.new("RGB", leg.size, (255, 255, 255))
        im = Image.composite(Image.blend(im, light, 0.06 * inflate), im, bm)
    if heat > 0:
        warm = Image.new("RGB", leg.size, (255, 120, 40))
        a = MASK_IN.point(lambda v: int(v * 0.28 * heat))
        im = Image.composite(warm, im, a)
    if wave is not None:  # banda de compresión que sube (0..1 de abajo a arriba)
        band = Image.new("L", leg.size, 0); d = ImageDraw.Draw(band)
        yb = 487 - wave * 380
        d.rectangle((300, yb - 22, 600, yb + 22), fill=150)
        band = band.filter(ImageFilter.GaussianBlur(14))
        band = ImageChops.multiply(band, MASK_IN)
        im = Image.composite(Image.new("RGB", leg.size, (120, 220, 255)), im, band)
    if screen_mode is not None:
        d = ImageDraw.Draw(im)
        x0, y0, x1, y1 = SCREEN
        d.rectangle((x0, y0, x1, y1), fill=(5, 10, 20))
        glow = (60, 220, 255)
        d.text(((x0 + x1) // 2, (y0 + y1) // 2), f"M{screen_mode}", font=F(28), fill=glow, anchor="mm")
        for i in range(3):
            c = glow if i < screen_mode else (40, 60, 80)
            d.rectangle((x0 + 8 + i * 12, y1 - 9, x0 + 16 + i * 12, y1 - 4), fill=c)
    return im

# ---------- composición en 9:16 ----------
_bgc = {}
def blurred_bg(src, key):
    if key not in _bgc:
        r = max(W / src.width, H / src.height)
        b = src.resize((int(src.width * r) + 2, int(src.height * r) + 2))
        b = b.crop(((b.width - W) // 2, (b.height - H) // 2, (b.width - W) // 2 + W, (b.height - H) // 2 + H))
        b = b.filter(ImageFilter.GaussianBlur(45))
        _bgc[key] = Image.blend(b, Image.new("RGB", (W, H), (15, 15, 20)), 0.4)
    return _bgc[key].copy()

def place(src, key, zoom, focus, shake=0.0, t=0.0, fill=False):
    """zoom=1 -> la foto ocupa el ancho; focus=(fx,fy) punto de la foto (0..1) que va al centro."""
    bg = blurred_bg(src, key)
    base = W / src.width * zoom
    if fill: base = max(W / src.width, H / src.height) * zoom
    fw, fh = int(src.width * base), int(src.height * base)
    fg = src.resize((fw, fh), Image.BILINEAR)
    x = int(W / 2 - focus[0] * fw); y = int(H / 2 - focus[1] * fh)
    if shake:
        x += int(math.sin(t * 61) * 14 * shake); y += int(math.cos(t * 47) * 14 * shake)
    bg.paste(fg, (x, y)); return bg

# ---------- textos ----------
def chip(d, text, cxp, y, size, fg=BLK, bg=YEL, p=1.0, pad=26, radius=22, alpha=245):
    if p <= 0: return
    sc = back(p); f = F(size * sc)
    lines = text.split("\n"); lh = int(size * sc * 1.25)
    for i, l in enumerate(lines):
        bb = d.textbbox((0, 0), l, font=f); w = bb[2] - bb[0]; h = bb[3] - bb[1]
        yy = y + i * (lh + 10); x = cxp - w // 2
        d.rounded_rectangle((x - pad, yy - pad // 2, x + w + pad, yy + h + pad), radius=radius, fill=bg + (int(alpha * min(1, p * 2)),))
        d.text((x - bb[0], yy - bb[1] + pad // 4), l, font=f, fill=fg)

def stroke_text(d, xy, text, size, fill=WHT, sw=7, anchor="la"):
    d.text(xy, text, font=F(size), fill=fill, stroke_width=sw, stroke_fill=BLK, anchor=anchor)

def captions(d, sent, t):
    """Subtítulos estilo viral: 3-4 palabras visibles, palabra actual en amarillo."""
    for typ, st, du, txt in sent:
        if st <= t < st + du + 0.05:
            words = txt.split()
            wts = [len(w) + 2 for w in words]; tot = sum(wts)
            acc = st; times = []
            for w_ in wts: times.append(acc); acc += du * w_ / tot
            idx = max(i for i, tt in enumerate(times) if tt <= t) if t >= times[0] else 0
            g0 = (idx // 4) * 4; group = words[g0:g0 + 4]
            size = 64
            parts = [(w, i + g0 == idx) for i, w in enumerate(group)]
            sp = d.textlength(" ", font=F(size)) + 6
            widths = [d.textlength(w, font=F(size * (1.12 if cur else 1))) + sp for w, cur in parts]
            x = (W - sum(widths)) // 2; y = 1480
            for (w, cur), wd in zip(parts, widths):
                s = size * (1.12 if cur else 1)
                stroke_text(d, (x, y - (6 if cur else 0)), w, s, YEL if cur else WHT)
                x += wd
            return

# ---------- partículas ----------
random.seed(4)
SNOW = [(random.random() * W, random.random() * H, random.uniform(3, 9), random.uniform(60, 160)) for _ in range(90)]
def snow(d, t):
    for x, y, r, v in SNOW:
        yy = (y + v * t) % H; xx = x + math.sin(t * 1.5 + y) * 20
        d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=(255, 255, 255, 200))

def arrows(d, t, cxp, cyp, spread, p):
    """Flechas de presión que entran hacia la pantorrilla."""
    if p <= 0: return
    k = (math.sin(t * 2 * math.pi * 0.9) + 1) / 2
    for side in (-1, 1):
        for j in range(3):
            x = cxp + side * (spread + 70 - 40 * k); y = cyp - 220 + j * 220
            pts = [(x, y), (x + side * 70, y - 38), (x + side * 70, y + 38)]
            d.polygon(pts, fill=(60, 220, 255, int(230 * p)))
            d.rectangle((min(x + side * 70, x + side * 140), y - 12, max(x + side * 70, x + side * 140), y + 12), fill=(60, 220, 255, int(230 * p)))

# ---------- guion (se sincroniza con la voz) ----------
sent = json.load(open(VOJ))
T = [s[1] for s in sent]
DUR = sent[-1][1] + sent[-1][2] + 0.8
scene_starts = [0.0, T[1], T[2], T[3], T[4], T[5], T[6]]
def scene_of(t):
    k = 0
    for i, s in enumerate(scene_starts):
        if t >= s: k = i
    return k

N = int(DUR * FPS)
cuts = []
for n in range(N):
    t = n / FPS; k = scene_of(t); ts = t - scene_starts[k]
    nxt = scene_starts[k + 1] if k + 1 < len(scene_starts) else DUR; sd = nxt - scene_starts[k]; u = ts / sd
    if n > 0 and scene_of((n - 1) / FPS) != k: cuts.append(t)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)

    if k == 0:   # gancho: zoom con golpe + vibración
        z = 1.35 + 0.25 * ease(u) - 0.12 * max(0, 1 - ts / 0.25)
        im = place(leg_frame(t), "leg", z, (0.6, 0.5), shake=max(0, 1 - ts / 0.6), t=t)
        chip(d, "¿PIERNAS CANSADAS?", W // 2, 260, 82, p=ts / 0.3)
        chip(d, "después de 8 horas de trabajo", W // 2, 420, 46, WHT, RED, p=(ts - 0.6) / 0.3)
    elif k == 1:  # "mira esto": zoom rápido a la funda
        z = 1.6 + 1.2 * ease(u)
        im = place(leg_frame(t, inflate=0.3 * ease(u)), "leg", z, (0.66, 0.45))
        stroke_text(d, (W // 2, 330), "MIRA ESTO 👀".replace(" 👀", ""), 96 * back(ts / 0.3), YEL, 9, "mm")
    elif k == 2:  # cómo funciona: se infla, ondas, flechas, calor
        cyc = (ts * 0.9) % 1
        infl = math.sin(cyc * math.pi) ** 2
        wave = (ts * 0.75) % 1
        im = place(leg_frame(t, inflate=infl, wave=wave, heat=0.0), "leg", 2.55, (0.68, 0.45))
        arrows(d, ts, W // 2 + 30, H // 2, 300, ease(ts / 0.4))
        chip(d, "MASAJE DE PRESIÓN\nDE AIRE", W // 2, 210, 70, p=ts / 0.3)
        chip(d, "se infla y relaja tu pantorrilla", W // 2, 1290, 44, WHT, (20, 20, 25), p=(ts - 1.2) / 0.3, alpha=200)
    elif k == 3:  # un botón: zoom al control, cambia de modo
        mode = 1 + min(2, int(ts / (sd / 3)))
        z = 3.1 + 0.3 * ease(u)
        heat_on = ease((ts - sd * 0.55) / 0.4)  # el control real tiene botón de calor
        im = place(leg_frame(t, inflate=0.2, screen_mode=mode, heat=heat_on), "leg", z, (0.705, 0.46))
        chip(d, "+ FUNCIÓN CALOR", W // 2, 1100, 56, WHT, (230, 110, 20), p=(ts - sd * 0.55) / 0.3)
        chip(d, "1 SOLO BOTÓN", W // 2, 230, 84, p=ts / 0.3)
        # pulsación del dedo (círculo)
        k2 = (ts % (sd / 3)) / (sd / 3)
        r = 40 + 80 * k2
        d.ellipse((W // 2 - r, H // 2 + 240 - r, W // 2 + r, H // 2 + 240 + r), outline=(255, 255, 255, int(255 * (1 - k2))), width=8)
        chip(d, f"MODO {mode}", W // 2, 1290, 60, WHT, (20, 120, 200), p=1)
    elif k == 4:  # dónde usarlo
        z = 1.25 - 0.1 * ease(u)
        im = place(leg_frame(t, inflate=(math.sin(ts * 3) + 1) / 4), "leg", z, (0.55, 0.5))
        for i, lab in enumerate(["EN EL SOFÁ", "EN LA OFICINA", "VIENDO TU SERIE"]):
            chip(d, "✓ " + lab, W // 2, 230 + i * 140, 60, BLK, YEL, p=(ts - i * 0.9) / 0.3)
    elif k == 5:  # regalo navidad
        z = 1.05 + 0.12 * ease(u)
        im = place(box, "box", z, (0.5, 0.52))
        snow(d, t)
        chip(d, "EL REGALO PERFECTO", W // 2, 210, 74, WHT, RED, p=ts / 0.3)
        chip(d, "para mamá, papá\no los abuelos", W // 2, 360, 54, BLK, YEL, p=(ts - 0.8) / 0.3)
    else:  # CTA
        im = place(box, "box", 1.2, (0.5, 0.55))
        im = Image.blend(im, Image.new("RGB", (W, H), (8, 8, 12)), 0.55)
        snow(d, t)
        chip(d, "PRECIO ESPECIAL", W // 2, 250, 58, WHT, (30, 30, 35), p=ts / 0.3)
        chip(d, "$129.900", W // 2, 370, 140, WHT, RED, p=(ts - 0.2) / 0.35, pad=40)
        chip(d, "PAGAS AL RECIBIR\nEN TODA COLOMBIA", W // 2, 680, 64, BLK, YEL, p=(ts - 0.8) / 0.3)
        pul = 1 + 0.06 * math.sin(ts * 9) if ts > 2.3 else 1
        chip(d, "ESCRÍBENOS POR WHATSAPP", W // 2, 1000, int(60 * pul), WHT, GRN, p=(ts - 2.2) / 0.3)

    captions(d, sent, t)
    # barra de progreso + aviso
    d.rectangle((0, 0, int(W * t / DUR), 12), fill=YEL + (255,))
    d.text((W - 30, H - 40), "Imagen ilustrativa", font=F(24), fill=(255, 255, 255, 150), anchor="rs")
    # flash corto en cada corte
    if cuts and 0 <= t - cuts[-1] < 0.12:
        ov = Image.alpha_composite(ov, Image.new("RGBA", (W, H), (255, 255, 255, int(170 * (1 - (t - cuts[-1]) / 0.12)))))
    frame = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    frame.save(f"{OUT}/frames/f{n:05d}.jpg", quality=88)

# ---------- audio: música + efectos ----------
SR = 44100; L = int(DUR * SR); tt = np.arange(L) / SR
mus = np.zeros(L)
bpm = 104; beat = 60 / bpm
def env(n, a=0.005, r=0.2):
    x = np.arange(n) / SR; return np.minimum(1, x / a) * np.exp(-x / r)
chords = [[220.0, 261.6, 329.6], [174.6, 220.0, 261.6], [261.6, 329.6, 392.0], [196.0, 246.9, 293.7]]  # Am F C G
nb = int(DUR / beat) + 1
for b in range(nb):
    s = int(b * beat * SR)
    if s >= L: break
    n = min(L - s, int(0.5 * SR)); x = np.arange(n) / SR
    if b % 2 == 0:  # bombo
        kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-x * 30)) * x) * env(n, 0.001, 0.12)
        mus[s:s + n] += 0.9 * kick
    else:  # palmas
        clap = np.random.randn(n) * env(n, 0.001, 0.06)
        mus[s:s + n] += 0.35 * clap
    for h in (0, 0.5):  # hi-hat
        hs = int((b + h) * beat * SR)
        if hs < L:
            hn = min(L - hs, int(0.05 * SR)); hh = np.random.randn(hn); hh = np.diff(hh, prepend=0)
            mus[hs:hs + hn] += 0.12 * hh * env(hn, 0.001, 0.015)
    if b % 4 == 0:  # acorde + bajo cada compás
        ch = chords[(b // 4) % 4]; n = min(L - s, int(4 * beat * SR)); x = np.arange(n) / SR
        pad = sum(np.sin(2 * np.pi * f * x) + 0.3 * np.sin(4 * np.pi * f * x) for f in ch) / 3
        mus[s:s + n] += 0.18 * pad * np.minimum(1, x / 0.05) * np.exp(-x / 2.5)
        bass = np.sin(2 * np.pi * ch[0] / 2 * x)
        mus[s:s + n] += 0.35 * bass * np.exp(-x / 0.9)
mus /= np.max(np.abs(mus)) + 1e-9
sfx = np.zeros(L)
for c in [0.0] + cuts:  # whoosh en cada corte
    s = max(0, int((c - 0.15) * SR)); n = min(L - s, int(0.4 * SR)); x = np.arange(n) / SR
    w = np.random.randn(n); w = np.convolve(w, np.ones(12) / 12, "same")
    sfx[s:s + n] += 0.5 * w * np.sin(np.pi * x / x[-1]) ** 2
s2 = int(scene_starts[2] * SR); e2 = int(scene_starts[3] * SR)  # "pssh" de aire en la escena de compresión
x = np.arange(e2 - s2) / SR
air = np.convolve(np.random.randn(e2 - s2), np.ones(40) / 40, "same") * (np.sin(np.pi * ((x * 0.9) % 1)) ** 2)
sfx[s2:e2] += 0.6 * air
import wave as wv
def wav(path, sig):
    sig = np.clip(sig, -1, 1); d16 = (sig * 32767).astype(np.int16)
    with wv.open(path, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes(d16.tobytes())
wav(f"{OUT}/music.wav", mus * 0.9); wav(f"{OUT}/sfx.wav", sfx / (np.max(np.abs(sfx)) + 1e-9))
print("frames", N, "dur", DUR)

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{OUT}/frames/f%05d.jpg",
    "-i", VO, "-i", f"{OUT}/music.wav", "-i", f"{OUT}/sfx.wav",
    "-filter_complex",
    "[1:a]volume=1.6,aresample=44100,aformat=channel_layouts=mono,asplit[vo1][vo2];[2:a]volume=0.16[mu];[3:a]volume=0.22[fx];"
    "[mu][vo1]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300[md];"
    "[vo2][md][fx]amix=inputs=3:normalize=0,alimiter=limit=0.95[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium",
    "-c:a", "aac", "-b:a", "192k", "-t", str(DUR), "-movflags", "+faststart", f"{OUT}/masajeador_v2.mp4"], check=True)
