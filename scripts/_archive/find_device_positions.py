"""
Find device positions using restricted-region template matching.
Devices overlap, so we search within expected regions only.
"""
import cv2
import numpy as np
import json

STATIC = r"d:\Porcellia\AI Testing\Vsl\static-to-gif\projects\atovio-colour-picker\static.png"
ELEMENTS_DIR = r"d:\Porcellia\AI Testing\Vsl\static-to-gif\projects\atovio-colour-picker\elements"

BG_COLOR_BGR = np.array([232, 239, 241], dtype=np.uint8)

static = cv2.imread(STATIC, cv2.IMREAD_COLOR)
h, w = static.shape[:2]

def composite_on_bg(elem_path, bg_color):
    elem = cv2.imread(elem_path, cv2.IMREAD_UNCHANGED)
    if elem is None:
        return None
    eh, ew = elem.shape[:2]
    if elem.shape[2] == 4:
        alpha = elem[:, :, 3:4].astype(np.float32) / 255.0
        bgr = elem[:, :, :3].astype(np.float32)
        bg = np.full((eh, ew, 3), bg_color, dtype=np.float32)
        return (bgr * alpha + bg * (1.0 - alpha)).astype(np.uint8)
    return elem


# Known card positions from edge detection:
# Black: x=0, y=321  |  White: x=556, y=321
# Pink:  x=0, y=699  |  Blue:  x=556, y=699
# Each card: 524x283

# Device search regions (x, y, w, h) - where to look in the static
# Based on the static layout, devices cluster in the center
DEVICES = {
    "Group 1171275467.png": {  # BLACK device - foreground center
        "name": "black",
        "search_region": (200, 250, 500, 500),  # center area
        "scale_range": (0.70, 1.10, 0.02),
    },
    "Group 1321314922.png": {  # BLUE device - right side
        "name": "blue",
        "search_region": (400, 200, 500, 500),  # right-center
        "scale_range": (0.70, 1.10, 0.02),
    },
    "Group 2147205493.png": {  # PINK device - bottom left
        "name": "pink",
        "search_region": (100, 400, 500, 500),  # bottom-left area
        "scale_range": (0.25, 0.65, 0.01),  # needs heavy downscaling (759px native)
    },
    "Group 2147205494.png": {  # WHITE device - bottom right
        "name": "white",
        "search_region": (400, 350, 500, 500),  # bottom-right area
        "scale_range": (0.25, 0.65, 0.01),  # needs heavy downscaling (699px native)
    },
}

import os

results = {}

for fname, config in DEVICES.items():
    fpath = os.path.join(ELEMENTS_DIR, fname)
    template = composite_on_bg(fpath, BG_COLOR_BGR)
    if template is None:
        print(f"SKIP: {fname}")
        continue

    rx, ry, rw, rh = config["search_region"]
    # Clamp search region
    rx2 = min(rx + rw, w)
    ry2 = min(ry + rh, h)
    search_area = static[ry:ry2, rx:rx2]

    scale_min, scale_max, scale_step = config["scale_range"]
    scales = np.arange(scale_min, scale_max + scale_step, scale_step)

    best = {"confidence": -1, "x": 0, "y": 0, "w": 0, "h": 0, "scale": 1.0}

    for scale in scales:
        new_w = int(template.shape[1] * scale)
        new_h = int(template.shape[0] * scale)
        if new_w < 10 or new_h < 10:
            continue
        if new_w >= search_area.shape[1] or new_h >= search_area.shape[0]:
            continue

        resized = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA)
        result = cv2.matchTemplate(search_area, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best["confidence"]:
            best = {
                "confidence": float(max_val),
                "x": int(max_loc[0]) + rx,  # offset back to full image coords
                "y": int(max_loc[1]) + ry,
                "w": new_w,
                "h": new_h,
                "scale": float(scale)
            }

    native_h, native_w = template.shape[:2]
    results[fname] = best
    results[fname]["native_w"] = native_w
    results[fname]["native_h"] = native_h

    print(f"{config['name'].upper()} device ({fname})")
    print(f"  Position: x={best['x']}, y={best['y']}")
    print(f"  Render:   {best['w']}x{best['h']} (scale={best['scale']:.2f})")
    print(f"  Native:   {native_w}x{native_h}")
    print(f"  Confidence: {best['confidence']:.4f}")
    print()

# Save
out_path = os.path.join(os.path.dirname(STATIC), "device_positions.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"Saved: {out_path}")
