"""
Optimize device positions using differential evolution.
Minimizes pixel difference between reconstruction and static reference.
"""
import cv2
import numpy as np
import os
import sys
from scipy.optimize import differential_evolution

sys.stdout.reconfigure(encoding='utf-8')

STATIC = r"d:\Porcellia\AI Testing\Vsl\static-to-gif\projects\atovio-personality-types\static.png"
E = r"d:\Porcellia\AI Testing\Vsl\static-to-gif\projects\atovio-personality-types\elements"

static = cv2.imread(STATIC, cv2.IMREAD_COLOR)
sh, sw = static.shape[:2]

# Pre-load elements
def load(name):
    path = os.path.join(E, name)
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"WARNING: Cannot load {path}")
    return img

dev_pink = load('Group 2147205493.png')
dev_white = load('Group 2147205494.png')
dev_blue = load('Group 1321314922.png')
dev_black = load('Group 1171275467.png')

card_black = load('Rectangle 3214923.png')
card_white = load('Rectangle 3214924.png')
card_pink = load('Rectangle 3214925.png')
card_blue = load('Rectangle 3214926.png')

# Find label files
label1 = label2 = label3 = label4 = None
for f in os.listdir(E):
    if f.startswith('1.') and f.endswith('.png'): label1 = load(f)
    elif f.startswith('2.') and f.endswith('.png'): label2 = load(f)
    elif f.startswith('3.') and f.endswith('.png'): label3 = load(f)
    elif f.startswith('4.') and f.endswith('.png'): label4 = load(f)

headline = load('Which colour shall I wear today_.png')
logo = load('Layer 4.png')


def place(canvas, img, x, y, w=None, h=None):
    if img is None:
        return
    ih, iw = img.shape[:2]
    if w is None: w = iw
    if h is None: h = ih
    w, h, x, y = int(w), int(h), int(x), int(y)
    if w < 1 or h < 1:
        return
    if w != iw or h != ih:
        img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
    if img.shape[2] == 4:
        alpha = img[:, :, 3:4].astype(np.float32) / 255.0
        bgr = img[:, :, :3].astype(np.float32)
    else:
        alpha = np.ones((h, w, 1), dtype=np.float32)
        bgr = img.astype(np.float32)
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(sw, x + w), min(sh, y + h)
    if x2 <= x1 or y2 <= y1:
        return
    sx, sy = x1 - x, y1 - y
    roi = canvas[y1:y2, x1:x2].astype(np.float32)
    a = alpha[sy:sy + (y2 - y1), sx:sx + (x2 - x1)]
    b = bgr[sy:sy + (y2 - y1), sx:sx + (x2 - x1)]
    canvas[y1:y2, x1:x2] = (b * a + roi * (1.0 - a)).astype(np.uint8)


# Pre-build base canvas (bg + cards)
base_canvas = np.full((sh, sw, 3), [241, 239, 232], dtype=np.uint8)
place(base_canvas, card_black, 0, 321)
place(base_canvas, card_white, 556, 321)
place(base_canvas, card_pink, 0, 699)
place(base_canvas, card_blue, 556, 699)

# Device native sizes
NATIVE = {
    'pink': (759, 639),
    'white': (699, 707),
    'blue': (298, 386),
    'black': (326, 420),
}

# Focus scoring on device area
DY1, DY2 = 220, 780
DX1, DX2 = 80, 980
static_roi = static[DY1:DY2, DX1:DX2].astype(np.float32)

call_count = 0


def objective(params):
    global call_count
    call_count += 1

    px, py, ps, wx, wy, ws, bx, by, bs, kx, ky, ks = params

    c = base_canvas.copy()

    # Devices back to front
    place(c, dev_pink, px, py, int(NATIVE['pink'][0] * ps), int(NATIVE['pink'][1] * ps))
    place(c, dev_white, wx, wy, int(NATIVE['white'][0] * ws), int(NATIVE['white'][1] * ws))
    place(c, dev_blue, bx, by, int(NATIVE['blue'][0] * bs), int(NATIVE['blue'][1] * bs))
    place(c, dev_black, kx, ky, int(NATIVE['black'][0] * ks), int(NATIVE['black'][1] * ks))

    # Labels on top
    place(c, label1, 55, 365, 186, 196)
    place(c, label2, 852, 365, 177, 196)
    place(c, label3, 54, 763, 139, 156)
    place(c, label4, 907, 763, 122, 196)
    place(c, headline, 81, 154)
    place(c, logo, 477, 52)

    roi = c[DY1:DY2, DX1:DX2].astype(np.float32)
    diff = np.abs(static_roi - roi)
    return np.mean(diff)


# Bounds: [pink_x, pink_y, pink_scale, white_x, white_y, white_scale,
#          blue_x, blue_y, blue_scale, black_x, black_y, black_scale]
bounds = [
    (80, 250),    # pink_x
    (380, 560),   # pink_y
    (0.40, 0.70), # pink_scale
    (420, 620),   # white_x
    (300, 500),   # white_y
    (0.40, 0.65), # white_scale
    (460, 620),   # blue_x
    (200, 330),   # blue_y
    (0.90, 1.15), # blue_scale
    (200, 320),   # black_x
    (220, 320),   # black_y
    (0.90, 1.15), # black_scale
]

print("Running differential evolution optimization...")
print("12 parameters: x, y, scale for each of 4 devices")
print(f"Population: 25, Max iterations: 100")

result = differential_evolution(
    objective, bounds,
    maxiter=100, popsize=25, tol=0.0005,
    seed=42, workers=1,
    disp=True
)

px, py, ps, wx, wy, ws, bx, by, bs, kx, ky, ks = result.x

print(f"\nOptimization complete: {call_count} evaluations, score={result.fun:.3f}")
print(f"\nFINAL DEVICE POSITIONS:")
print(f"  PINK:  left={int(px)}; top={int(py)}; width={int(NATIVE['pink'][0]*ps)}; height={int(NATIVE['pink'][1]*ps)}; scale={ps:.3f}")
print(f"  WHITE: left={int(wx)}; top={int(wy)}; width={int(NATIVE['white'][0]*ws)}; height={int(NATIVE['white'][1]*ws)}; scale={ws:.3f}")
print(f"  BLUE:  left={int(bx)}; top={int(by)}; width={int(NATIVE['blue'][0]*bs)}; height={int(NATIVE['blue'][1]*bs)}; scale={bs:.3f}")
print(f"  BLACK: left={int(kx)}; top={int(ky)}; width={int(NATIVE['black'][0]*ks)}; height={int(NATIVE['black'][1]*ks)}; scale={ks:.3f}")

# Build final image
c = base_canvas.copy()
place(c, dev_pink, int(px), int(py), int(NATIVE['pink'][0]*ps), int(NATIVE['pink'][1]*ps))
place(c, dev_white, int(wx), int(wy), int(NATIVE['white'][0]*ws), int(NATIVE['white'][1]*ws))
place(c, dev_blue, int(bx), int(by), int(NATIVE['blue'][0]*bs), int(NATIVE['blue'][1]*bs))
place(c, dev_black, int(kx), int(ky), int(NATIVE['black'][0]*ks), int(NATIVE['black'][1]*ks))
place(c, label1, 55, 365, 186, 196)
place(c, label2, 852, 365, 177, 196)
place(c, label3, 54, 763, 139, 156)
place(c, label4, 907, 763, 122, 196)
place(c, headline, 81, 154)
place(c, logo, 477, 52)

cv2.imwrite(r'd:\Porcellia\AI Testing\Vsl\temp_verify\recon_de.png', c)

# Stats
diff = cv2.absdiff(static, c)
dg = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
total = dg.size
print(f"\nFull image stats:")
print(f"  Mean error: {np.mean(dg):.2f}/255")
print(f"  Perfect: {100*np.sum(dg==0)/total:.1f}%")
print(f"  Near-perfect (<=3): {100*np.sum(dg<=3)/total:.1f}%")
print(f"  Significant (>20): {100*np.sum(dg>20)/total:.1f}%")

dg_roi = dg[DY1:DY2, DX1:DX2]
roi_total = dg_roi.size
print(f"\nDevice region stats:")
print(f"  Mean error: {np.mean(dg_roi):.2f}/255")
print(f"  Perfect: {100*np.sum(dg_roi==0)/roi_total:.1f}%")
print(f"  Significant (>20): {100*np.sum(dg_roi>20)/roi_total:.1f}%")
