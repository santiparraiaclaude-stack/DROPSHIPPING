import sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
IMG, OUT = sys.argv[1], sys.argv[2]
W,H,FPS = 1080,1920,30
B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def F(s): return ImageFont.truetype(B,s)
def load(p, crop=None):
    im=Image.open(p).convert("RGB")
    if crop: im=im.crop(crop)
    return im
leg = load(f"{IMG}/2.webp", (0,0,700,690))   # quitar margen blanco
box = load(f"{IMG}/3.webp")
def canvas(im, z, fx=0.5, fy=0.5):
    # fondo desenfocado + imagen centrada con zoom z
    bg = im.resize((W, int(im.height*W/im.width)) if im.width/im.height<W/H else (int(im.width*H/im.height),H))
    bg = bg.resize((max(W,bg.width),max(H,bg.height)))
    bg = bg.crop(((bg.width-W)//2,(bg.height-H)//2,(bg.width-W)//2+W,(bg.height-H)//2+H)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB",(W,H),(20,20,25)), 0.35)
    s = W*1.0/im.width*z
    fg = im.resize((int(im.width*s), int(im.height*s)), Image.LANCZOS)
    x = int((W-fg.width)*fx); y=int((H-fg.height)*fy)
    bg.paste(fg,(x,y)); return bg
def ease(t): t=max(0,min(1,t)); return 1-(1-t)**3
def label(d, text, y, size, fg=(255,255,255), bg=(0,0,0,170), t=1.0, pad=28):
    if t<=0: return
    f=F(size); lines=text.split("\n")
    sc=0.6+0.4*ease(t); 
    for i,l in enumerate(lines):
        f2=F(int(size*sc)); bb=d.textbbox((0,0),l,font=f2); w=bb[2]-bb[0]; h=bb[3]-bb[1]
        yy=y+i*int(size*1.35); x=(W-w)//2
        d.rounded_rectangle((x-pad,yy-pad//2,x+w+pad,yy+h+pad), radius=24, fill=bg)
        d.text((x-bb[0],yy-bb[1]+pad//4),l,font=f2,fill=fg)
YEL=(255,214,0,240); RED=(229,57,53,235); GRN=(37,211,102,240)
scenes=[ # (dur, fn)
 (3.0,"hook"),(4.0,"benef"),(4.0,"box"),(4.0,"cta")]
n=0
for dur,name in scenes:
    N=int(dur*FPS)
    for i in range(N):
        t=i/N; ts=i/FPS
        if name=="hook": im=canvas(leg,1.0+0.25*t,0.5,0.42)
        elif name=="benef": im=canvas(leg,1.25-0.15*t,0.3+0.2*t,0.45)
        elif name=="box": im=canvas(box,1.0+0.15*t,0.5,0.5)
        else: im=canvas(box,1.15,0.5,0.5); im=Image.blend(im,Image.new("RGB",(W,H),(10,10,14)),0.45)
        ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
        if name=="hook":
            label(d,"¿PIERNAS CANSADAS\nDESPUÉS DEL TRABAJO?",230,64,(0,0,0),YEL,ts/0.35)
            label(d,"Mira esto...",1650,56,t=(ts-1.4)/0.3)
        elif name=="benef":
            label(d,"MASAJE RELAJANTE",200,70,(0,0,0),YEL,ts/0.3)
            label(d,"✓ Úsalo sentado, en casa\n   o en la oficina",1450,50,t=(ts-0.6)/0.3)
            label(d,"✓ Se ajusta a la pantorrilla",1700,50,t=(ts-1.6)/0.3)
        elif name=="box":
            label(d,"PORTÁTIL Y FÁCIL DE USAR",200,62,(0,0,0),YEL,ts/0.3)
            label(d,"🎁 EL REGALO PERFECTO\nPARA MAMÁ, PAPÁ O LOS ABUELOS".replace("🎁 ",""),1520,50,t=(ts-0.8)/0.3)
        else:
            label(d,"PRECIO ESPECIAL",330,60,t=ts/0.3)
            label(d,"$129.900",460,130,(255,255,255),RED,(ts-0.3)/0.3,pad=36)
            label(d,"PAGO CONTRA ENTREGA\nEN TODA COLOMBIA",780,62,(0,0,0),YEL,(ts-0.9)/0.3)
            label(d,"ESCRÍBENOS POR WHATSAPP",1150,58,(255,255,255),GRN,(ts-1.6)/0.3)
            if ts>2.2 and int(ts*3)%2==0: label(d,"👇 PIDE EL TUYO HOY".replace("👇 ",""),1330,52,t=1)
        d2=ImageDraw.Draw(ov); f=F(26)
        d2.text((W-40,H-50),"Imagen de referencia del producto",font=f,fill=(255,255,255,170),anchor="rs")
        # flash de transición
        if i<5 and n>0: ov=Image.alpha_composite(ov,Image.new("RGBA",(W,H),(255,255,255,int(160*(1-i/5)))))
        im=Image.alpha_composite(im.convert("RGBA"),ov).convert("RGB")
        im.save(f"{OUT}/f{n:04d}.jpg",quality=90); n+=1
print(n)
