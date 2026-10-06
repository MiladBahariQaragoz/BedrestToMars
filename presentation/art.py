# Space-themed assets for the deck: title background, opaque planet dots, gradient stripe.
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter
earth_src, mars_src = sys.argv[1], sys.argv[2]

def globe(src, size, lon0, lat0=0.0, glow=None):
    tex = np.asarray(Image.open(src).convert('RGB')).astype(float)
    H, W, _ = tex.shape
    y, x = np.mgrid[-1:1:size*1j, -1:1:size*1j]
    r2 = x**2 + y**2; inside = r2 <= 1
    z = np.sqrt(np.clip(1 - r2, 0, 1)); la0 = np.radians(lat0)
    yy = -y*np.cos(la0) + z*np.sin(la0); zz = y*np.sin(la0) + z*np.cos(la0)
    lat = np.arcsin(np.clip(yy, -1, 1)); lon = np.arctan2(x, zz) + np.radians(lon0)
    u = ((lon/(2*np.pi) + 0.5) % 1) * (W-1); v = (0.5 - lat/np.pi) * (H-1)
    img = tex[v.astype(int), u.astype(int)]
    # light from the upper left, dark limb at the lower right
    light = np.clip(z*0.75 + (-x*0.45) + (-y*0.3) + 0.05, 0, 1)
    img = np.clip(img*(0.18 + 0.95*light)[..., None], 0, 255)
    edge = np.clip((1 - np.sqrt(r2)) * size / 2, 0, 1)
    return Image.fromarray(np.dstack([img, inside*edge*255]).astype(np.uint8), 'RGBA')

# opaque dots for the progress tracker and agenda
globe(earth_src, 200, 10, 20).save('dot-earth.png')
globe(mars_src, 200, -60, 10).save('dot-mars.png')

# title background, 1920 x 1080 (13.33 x 7.5 in at 144 px/in)
W, H, PX = 1920, 1080, 144
yy, xx = np.mgrid[0:H, 0:W]
d = np.sqrt(((xx - 0.35*W)/W)**2 + ((yy - 0.45*H)/H)**2)
c0, c1 = np.array([22, 44, 78]), np.array([4, 9, 20])
t = np.clip(d/0.9, 0, 1)[..., None]
bg = (c0*(1-t) + c1*t)
rng = np.random.default_rng(7)
img = Image.fromarray(bg.astype(np.uint8), 'RGB').convert('RGBA')
dr = ImageDraw.Draw(img)
for _ in range(900):
    x, y = rng.uniform(0, W), rng.uniform(0, H)
    r = rng.choice([0.6, 0.9, 1.3, 1.8], p=[0.55, 0.3, 0.12, 0.03]); a = int(rng.uniform(70, 230))
    if x < 9.3*PX and 1.0*PX < y < 6.6*PX:  # behind the text block: fewer, fainter stars
        if rng.uniform() < 0.6: continue
        r, a = min(r, 0.9), a // 3
    dr.ellipse([x-r, y-r, x+r, y+r], fill=(255, 255, 255, a))
# Mars: large, at the right edge, with a thin warm glow
mR = int(2.7*PX); mcx, mcy = int(12.35*PX), int(3.0*PX)
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
gd.ellipse([mcx-mR-14, mcy-mR-14, mcx+mR+14, mcy+mR+14], fill=(214, 96, 46, 120))
glow = glow.filter(ImageFilter.GaussianBlur(22)); img = Image.alpha_composite(img, glow)
mars = globe(mars_src, 2*mR, -60, 10); img.alpha_composite(mars, (mcx-mR, mcy-mR))
# Earth: small, lower right of the text block
eR = int(0.36*PX); ecx, ecy = int(8.95*PX), int(6.55*PX)
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
gd.ellipse([ecx-eR-8, ecy-eR-8, ecx+eR+8, ecy+eR+8], fill=(90, 150, 230, 110))
glow = glow.filter(ImageFilter.GaussianBlur(10)); img = Image.alpha_composite(img, glow)
img.alpha_composite(globe(earth_src, 2*eR, 10, 20), (ecx-eR, ecy-eR))
# transfer trajectory: dashed arc from Earth to Mars
dr = ImageDraw.Draw(img)
p0, p2 = np.array([ecx+eR+10, ecy-14]), np.array([mcx-mR*0.72, mcy+mR*0.72])
p1 = np.array([p0[0]+0.75*(p2[0]-p0[0]), p0[1]+10])
ts = np.linspace(0, 1, 160)
pts = [(1-t)**2*p0 + 2*(1-t)*t*p1 + t**2*p2 for t in ts]
for i in range(0, len(pts)-1, 2):
    dr.line([tuple(pts[i]), tuple(pts[i+1])], fill=(242, 208, 169, 200), width=3)
img.convert('RGB').save('title-bg.png', optimize=True)

# gradient stripe: Earth blue -> space navy -> Mars rust
w = 2000; g = np.zeros((16, w, 3))
stops = [(0, (47, 102, 144)), (0.5, (11, 37, 69)), (1, (193, 68, 14))]
for i in range(w):
    f = i/(w-1)
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= f <= b:
            k = (f-a)/(b-a); g[:, i] = np.array(ca)*(1-k) + np.array(cb)*k
Image.fromarray(g.astype(np.uint8)).save('stripe.png')
print('ok')
