"""
Crop devices to their opaque bounding box (remove transparent padding),
then template match the cropped version against the static.
This gives better results because the transparent edges don't confuse matching.
"""
import cv2
import numpy as np
import os

STATIC = r"d:\Porcellia\AI Testing\Vsl\static-to-gif\projects\atovio-colour-picker\static.png"
ELEMENTS_DIR = r"d:\Porcellia\AI Testing\Vsl\static-to-gif\projects\atovio-colour-picker\elements"

static = cv2.imread(STATIC, cv2.IMREAD_COLOR)
h, w = static.shape[:2]

DEVICES = [
    ("Group 1171275467.png", "BLACK", (0.90, 1.15, 0.01)),
    ("Group 1321314922.png", "BLUE", (0.90, 1.15, 0.01)),
    ("Group 2147205493.png", "PINK", (0.30, 0.65, 0.005)),
    ("Group 2147205494.png", "WHITE", (0.30, 0.65, 0.005)),
]


def get_opaque_bbox(img_path):
    """Get the bounding box of opaque pixels in an RGBA image."""
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
    if img is None or img.shape[2] < 4:
        return None, None, None
    alpha = img[:, :, 3]
    # Threshold at 50 to ignore very faint pixels
    mask = alpha > 50
    coords = np.argwhere(mask)
    if len(coords) == 0:
        return None, None, None
    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0)
    return img, (x0, y0, x1 - x0 + 1, y1 - y0 + 1), (x0, y0)


for fname, name, (s_min, s_max, s_step) in DEVICES:
    fpath = os.path.join(ELEMENTS_DIR, fname)

    img, bbox, offset = get_opaque_bbox(fpath)
    if img is None:
        print(f"SKIP: {fname}")
        continue

    bx, by, bw, bh = bbox
    native_h, native_w = img.shape[:2]

    # Crop to opaque bbox
    cropped = img[by:by+bh, bx:bx+bw]

    # Composite cropped onto multiple backgrounds and match
    best = {"confidence": -1}

    bg_colors = [
        np.array([0, 0, 0]),       # black card
        np.array([255, 255, 255]), # white card
        np.array([196, 196, 255]),  # pink card
        np.array([195, 221, 255]),  # blue card
        np.array([232, 239, 241]),  # cream background
    ]

    for bg_color in bg_colors:
        alpha = cropped[:, :, 3:4].astype(np.float32) / 255.0
        bgr = cropped[:, :, :3].astype(np.float32)
        bg = np.full((bh, bw, 3), bg_color, dtype=np.float32)
        composited = (bgr * alpha + bg * (1.0 - alpha)).astype(np.uint8)

        for scale in np.arange(s_min, s_max + s_step, s_step):
            nw = int(bw * scale)
            nh = int(bh * scale)
            if nw < 10 or nh < 10 or nw >= w or nh >= h:
                continue

            resized = cv2.resize(composited, (nw, nh), interpolation=cv2.INTER_AREA)

            # Match in grayscale (more robust)
            tmpl_gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            static_gray = cv2.cvtColor(static, cv2.COLOR_BGR2GRAY)
            result = cv2.matchTemplate(static_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val > best["confidence"]:
                best = {
                    "confidence": float(max_val),
                    "crop_x": int(max_loc[0]),
                    "crop_y": int(max_loc[1]),
                    "crop_w": nw,
                    "crop_h": nh,
                    "scale": float(scale),
                }

    # Convert crop coords back to full-image coords
    # The crop offset within the native image is (bx, by)
    # At the matched scale, the offset is (bx*scale, by*scale)
    # The full image position = crop_position - offset*scale
    full_x = best["crop_x"] - int(bx * best["scale"])
    full_y = best["crop_y"] - int(by * best["scale"])
    full_w = int(native_w * best["scale"])
    full_h = int(native_h * best["scale"])

    print(f"{name} device ({fname})")
    print(f"  Opaque bbox: x={bx}, y={by}, {bw}x{bh} (within {native_w}x{native_h})")
    print(f"  Matched crop at: x={best['crop_x']}, y={best['crop_y']}, {best['crop_w']}x{best['crop_h']}")
    print(f"  Full image pos:  x={full_x}, y={full_y}, {full_w}x{full_h} (scale={best['scale']:.3f})")
    print(f"  Confidence: {best['confidence']:.4f}")
    print()
