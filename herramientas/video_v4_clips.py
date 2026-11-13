"""Anuncio final v4 · clips con movimiento (Kling/Higgsfield) + voz + subtítulos + CTA · 9:16
Uso: python3 video_v4_clips.py <carpeta_clips> <carpeta_imagenes> <vo.mp3> <vo.mp3.json> <salida>
Clips: clip1_llega.mp4, clip2_boton.mp4, clip3_sofa.mp4, clip4_abuelo.mp4 · Imagen 7.webp = collage de usos.
"""
import sys, os, json, math, random, subprocess, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CL, IMG, VO, VOJ, OUT = sys.argv[1:6]
W, H, FPS = 1080, 1920, 30
os.makedirs(f"{OUT}/frames", exist_ok=True)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_fc = {}
def F(s):
    s = max(8, int(s))
    if s not in _fc: _fc[s] = ImageFont.truetype(FB, s)
    return _fc[s]
def ease(t): t = max(0., min(1., t)); return 1 - (1 - t) ** 3
def back(t):
    t = max(0., min(1., t)); c = 1.7
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
YEL = (255, 214, 0); RED = (229, 57, 53); GRN = (37, 211, 102); WHT = (255, 255, 255); BLK = (0, 0, 0)

# --- extraer frames de cada clip a 1080x1920 ---
clips = {}
for name in ["clip1_llega", "clip2_boton", "clip3_sofa", "clip4_abuelo"]:
    d = f"{OUT}/src_{name}"; os.makedirs(d, exist_ok=True)
    if not glob.glob(f"{d}/*.jpg"):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{CL}/{name}.mp4", "-vf",
                        f"fps={FPS},scale={W}:{H}:flags=lanczos", "-q:v", "2", f"{d}/%04d.jpg"], check=True)
    clips[name] = sorted(glob.glob(f"{d}/*.jpg"))
def clip_frame(name, t, speed=1.0):
    fr = clips[name]; i = min(len(fr) - 1, int(t * speed * FPS)); return Image.open(fr[i]).convert("RGB")

COL = Image.open(f"{IMG}/7.webp").convert("RGB")
PANELS = [(COL.crop((0, 0, 944, 570)), "✓ EN CASA"), (COL.crop((0, 1120, 460, 1680)), "✓ EN LA OFICINA"),
          (COL.crop((465, 1120, 944, 1680)), "✓ DONDE QUIERAS")]
def still(src, z):
    r = max(W / src.width, H / src.height) * z
    im = src.resize((int(src.width * r), int(src.height * r)), Image.LANCZOS)
    x = (im.width - W) // 2; y = (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))

def chip(d, text, cx, y, size, fg=BLK, bg=YEL, p=1.0, pad=26, alpha=245):
    if p <= 0: return
    sc = back(p); f = F(size * sc); lh = int(size * sc * 1.25)
    for i, l in enumerate(text.split("\n")):
        bb = d.textbbox((0, 0), l, font=f); w = bb[2] - bb[0]; h = bb[3] - bb[1]
        yy = y + i * (lh + 10); x = cx - w // 2
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
            size = 68; sp = d.textlength(" ", font=F(size)) + 6
            widths = [d.textlength(w, font=F(size * (1.12 if c else 1))) + sp for w, c in parts]
            x = (W - sum(widths)) // 2; y = 1480
            for (w, c), wd in zip(parts, widths):
                d.text((x, y - (6 if c else 0)), w, font=F(size * (1.12 if c else 1)), fill=YEL if c else WHT, stroke_width=8, stroke_fill=BLK)
                x += wd
            return

random.seed(4)
SNOW = [(random.random() * W, random.random() * H, random.uniform(3, 8), random.uniform(60, 150)) for _ in range(70)]
def snow(d, t):
    for x, y, r, v in SNOW:
        yy = (y + v * t) % H; xx = x + math.sin(t * 1.5 + y) * 20
        d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=(255, 255, 255, 170))

sent = json.load(open(VOJ)); T = [s[1] for s in sent]
DUR = sent[-1][1] + sent[-1][2] + 0.9
starts = [0.0, T[1], T[2], T[3], T[4], T[5]]
def scene_of(t): return max(i for i, s in enumerate(starts) if t >= s)

N = int(DUR * FPS); cuts = []; last = None
for n in range(N):
    t = n / FPS; k = scene_of(t); ts = t - starts[k]
    sd = (starts[k + 1] if k + 1 < len(starts) else DUR) - starts[k]
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov); sub = k
    if k == 0:
        im = clip_frame("clip1_llega", ts + 0.4)
        chip(d, "¿PIERNAS CANSADAS?", W // 2, 230, 84, p=ts / 0.3)
        chip(d, "después de un día largo", W // 2, 385, 46, WHT, RED, p=(ts - 0.7) / 0.3)
    elif k == 1:
        im = clip_frame("clip2_boton", ts, speed=5.0 / max(sd, 3.5))
        chip(d, "UN SOLO BOTÓN", W // 2, 230, 84, p=ts / 0.3)
    elif k == 2:
        im = clip_frame("clip3_sofa", ts, speed=0.9)
        chip(d, "PRESIÓN DE AIRE + CALOR", W // 2, 230, 66, p=ts / 0.3)
        chip(d, "se infla y relaja tu pantorrilla", W // 2, 380, 44, WHT, (20, 20, 25), p=(ts - 0.8) / 0.3, alpha=210)
    elif k == 3:
        j = min(2, int(ts / (sd / 3))); tj = ts - j * sd / 3; sub = (3, j)
        src, lab = PANELS[j]
        im = still(src, 1.0 + 0.1 * tj / (sd / 3))
        chip(d, lab, W // 2, 260, 74, p=tj / 0.25)
    elif k == 4:
        im = clip_frame("clip4_abuelo", ts, speed=5.0 / max(sd, 5.0))
        snow(d, t)
        chip(d, "EL REGALO PERFECTO", W // 2, 210, 74, WHT, RED, p=ts / 0.3)
        chip(d, "para mamá, papá o los abuelos", W // 2, 360, 48, BLK, YEL, p=(ts - 0.8) / 0.3)
    else:
        im = clip_frame("clip3_sofa", 1.0 + ts * 0.6)
        im = Image.blend(im.filter(ImageFilter.GaussianBlur(3)), Image.new("RGB", (W, H), (8, 8, 12)), 0.5)
        snow(d, t)
        chip(d, "PRECIO ESPECIAL", W // 2, 260, 58, WHT, (30, 30, 35), p=ts / 0.3)
        chip(d, "$129.900", W // 2, 380, 140, WHT, RED, p=(ts - 0.2) / 0.35, pad=40)
        chip(d, "PAGAS AL RECIBIR\nEN TODA COLOMBIA", W // 2, 690, 64, BLK, YEL, p=(ts - 0.8) / 0.3)
        pul = 1 + 0.06 * math.sin(ts * 9) if ts > 2.3 else 1
        chip(d, "ESCRÍBENOS POR WHATSAPP", W // 2, 1010, int(60 * pul), WHT, GRN, p=(ts - 2.2) / 0.3)
    if last is not None and sub != last: cuts.append(t)
    last = sub
    captions(d, sent, t)
    d.rectangle((0, 0, int(W * t / DUR), 12), fill=YEL + (255,))
    d.text((W - 30, H - 40), "Video ilustrativo creado con IA", font=F(24), fill=(255, 255, 255, 160), anchor="rs")
    if cuts and 0 <= t - cuts[-1] < 0.08:
        ov = Image.alpha_composite(ov, Image.new("RGBA", (W, H), (255, 255, 255, int(120 * (1 - (t - cuts[-1]) / 0.08)))))
    Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB").save(f"{OUT}/frames/f{n:05d}.jpg", quality=90)

# --- audio: música + whoosh ---
SR = 44100; Ls = int(DUR * SR); mus = np.zeros(Ls); beat = 60 / 100
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
            hn = min(Ls - hs, int(0.05 * SR)); mus[hs:hs + hn] += 0.1 * np.diff(np.random.randn(hn), prepend=0) * env(hn, 0.001, 0.015)
    if b % 4 == 0:
        ch = chords[(b // 4) % 4]; n = min(Ls - s, int(4 * beat * SR)); x = np.arange(n) / SR
        mus[s:s + n] += 0.2 * sum(np.sin(2 * np.pi * f * x) + 0.3 * np.sin(4 * np.pi * f * x) for f in ch) / 3 * np.minimum(1, x / 0.05) * np.exp(-x / 2.5)
        mus[s:s + n] += 0.3 * np.sin(np.pi * ch[0] * x) * np.exp(-x / 0.9)
mus /= np.max(np.abs(mus)) + 1e-9
sfx = np.zeros(Ls)
for c in [0.0] + cuts:
    s = max(0, int((c - 0.15) * SR)); n = min(Ls - s, int(0.35 * SR)); x = np.arange(n) / SR
    sfx[s:s + n] += 0.5 * np.convolve(np.random.randn(n), np.ones(12) / 12, "same") * np.sin(np.pi * x / x[-1]) ** 2
import wave as wv
def wav(p, sig):
    with wv.open(p, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((np.clip(sig, -1, 1) * 32767).astype(np.int16).tobytes())
wav(f"{OUT}/music.wav", mus * 0.9); wav(f"{OUT}/sfx.wav", sfx / (np.max(np.abs(sfx)) + 1e-9))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{OUT}/frames/f%05d.jpg",
    "-i", VO, "-i", f"{OUT}/music.wav", "-i", f"{OUT}/sfx.wav", "-filter_complex",
    "[1:a]volume=1.6,aresample=44100,aformat=channel_layouts=mono,asplit[vo1][vo2];[2:a]volume=0.15[mu];[3:a]volume=0.18[fx];"
    "[mu][vo1]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300[md];"
    "[vo2][md][fx]amix=inputs=3:normalize=0,alimiter=limit=0.95[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
    "-c:a", "aac", "-b:a", "192k", "-t", f"{DUR:.2f}", "-movflags", "+faststart", f"{OUT}/anuncio_masajeador_final.mp4"], check=True)
print("ok", N, DUR)
