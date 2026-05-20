"""
Pixel-exact template matching for static-to-GIF element placement.
Composites transparent elements onto the background color before matching.
"""
import cv2
import numpy as np
import os
import json

STATIC = r"d:\Porcellia\AI Testing\Vsl\static-to-gif\projects\atovio-colour-picker\static.png"
ELEMENTS_DIR = r"d:\Porcellia\AI Testing\Vsl\static-to-gif\projects\atovio-colour-picker\elements"

# Background color sampled from the static (cream/beige)
BG_COLOR_BGR = np.array([232, 237, 242], dtype=np.uint8)  # #F2EDE8 in BGR

static = cv2.imread(STATIC, cv2.IMREAD_COLOR)
if static is None:
    print(f"ERROR: Cannot read static: {STATIC}")
    exit(1)

static_h, static_w = static.shape[:2]
print(f"Static: {static_w}x{static_h}")
print("=" * 80)


def composite_on_bg(elem_path, bg_color):
    """Read element with alpha, composite onto solid background color."""
    elem = cv2.imread(elem_path, cv2.IMREAD_UNCHANGED)
    if elem is None:
        return None, 0, 0
    h, w = elem.shape[:2]
    if elem.shape[2] == 4:
        alpha = elem[:, :, 3:4].astype(np.float32) / 255.0
        bgr = elem[:, :, :3].astype(np.float32)
        bg = np.full((h, w, 3), bg_color, dtype=np.float32)
        composited = (bgr * alpha + bg * (1.0 - alpha)).astype(np.uint8)
        return composited, w, h
    else:
        return elem, w, h


def find_best_match(static_img, template, scales):
    """Find best match across scales using TM_CCOEFF_NORMED."""
    best = {"confidence": -1, "x": 0, "y": 0, "w": 0, "h": 0, "scale": 1.0}

    for scale in scales:
        new_w = max(10, int(template.shape[1] * scale))
        new_h = max(10, int(template.shape[0] * scale))
        if new_w > static_img.shape[1] or new_h > static_img.shape[0]:
            continue

        if scale != 1.0:
            tmpl = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            tmpl = template

        result = cv2.matchTemplate(static_img, tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best["confidence"]:
            best = {
                "confidence": float(max_val),
                "x": int(max_loc[0]),
                "y": int(max_loc[1]),
                "w": new_w,
                "h": new_h,
                "scale": scale
            }

    return best


# Define which elements are likely at native scale vs need scaling
# Cards, headline, logo, labels = exported at 1x → match at native
# Devices = may be at higher res → need multi-scale search
DEVICE_FILES = {
    "Group 1171275467.png",   # black device
    "Group 1321314922.png",   # blue device
    "Group 2147205493.png",   # pink device
    "Group 2147205494.png",   # white device
}

results = {}

for fname in sorted(os.listdir(ELEMENTS_DIR)):
    if not fname.lower().endswith('.png'):
        continue

    fpath = os.path.join(ELEMENTS_DIR, fname)
    composited, native_w, native_h = composite_on_bg(fpath, BG_COLOR_BGR)
    if composited is None:
        print(f"SKIP: {fname}")
        continue

    if fname in DEVICE_FILES:
        # Devices: search across scales 0.3–1.2
        scales = [s / 100.0 for s in range(30, 121, 2)]
    else:
        # Non-devices: try native first, then nearby scales
        scales = [1.0, 0.95, 1.05, 0.9, 1.1, 0.85, 1.15, 0.8, 1.2]

    match = find_best_match(static, composited, scales)

    results[fname] = {
        "x": match["x"],
        "y": match["y"],
        "width": match["w"],
        "height": match["h"],
        "scale": round(match["scale"], 2),
        "confidence": round(match["confidence"], 4),
        "native_w": native_w,
        "native_h": native_h
    }

    print(f"{fname}")
    print(f"  Position: x={match['x']}, y={match['y']}")
    print(f"  Render:   {match['w']}x{match['h']} (scale={match['scale']:.2f})")
    print(f"  Native:   {native_w}x{native_h}")
    print(f"  Confidence: {match['confidence']:.4f}")
    print()

# Save
out_path = os.path.join(os.path.dirname(STATIC), "element_positions.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved: {out_path}")
