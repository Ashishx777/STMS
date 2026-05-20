"""
Better device matching - try more scales, use grayscale for better contrast matching.
Also try matching against device-specific card backgrounds instead of cream.
"""
import cv2
import numpy as np
import os

STATIC = r"d:\Porcellia\AI Testing\Vsl\static-to-gif\projects\atovio-colour-picker\static.png"
ELEMENTS_DIR = r"d:\Porcellia\AI Testing\Vsl\static-to-gif\projects\atovio-colour-picker\elements"

static = cv2.imread(STATIC, cv2.IMREAD_COLOR)
static_gray = cv2.cvtColor(static, cv2.COLOR_BGR2GRAY)
h, w = static.shape[:2]

# Card backgrounds for compositing
CARD_COLORS = {
    "black": np.array([0, 0, 0], dtype=np.uint8),
    "white": np.array([255, 255, 255], dtype=np.uint8),
    "pink": np.array([196, 196, 255], dtype=np.uint8),  # BGR for pink (#FFC4C4)
    "blue": np.array([195, 221, 255], dtype=np.uint8),   # BGR for light blue
}

BG_CREAM = np.array([232, 239, 241], dtype=np.uint8)


def composite(elem_path, bg_color):
    elem = cv2.imread(elem_path, cv2.IMREAD_UNCHANGED)
    if elem is None:
        return None, 0, 0
    eh, ew = elem.shape[:2]
    if elem.shape[2] == 4:
        alpha = elem[:, :, 3:4].astype(np.float32) / 255.0
        bgr = elem[:, :, :3].astype(np.float32)
        bg = np.full((eh, ew, 3), bg_color, dtype=np.float32)
        return (bgr * alpha + bg * (1.0 - alpha)).astype(np.uint8), ew, eh
    return elem, ew, eh


def match_multiscale(search_img, template, scale_min, scale_max, scale_step):
    best = {"confidence": -1, "x": 0, "y": 0, "w": 0, "h": 0, "scale": 1.0}
    for scale in np.arange(scale_min, scale_max + scale_step, scale_step):
        nw = int(template.shape[1] * scale)
        nh = int(template.shape[0] * scale)
        if nw < 10 or nh < 10 or nw >= search_img.shape[1] or nh >= search_img.shape[0]:
            continue
        resized = cv2.resize(template, (nw, nh), interpolation=cv2.INTER_AREA)
        result = cv2.matchTemplate(search_img, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val > best["confidence"]:
            best = {"confidence": float(max_val), "x": int(max_loc[0]), "y": int(max_loc[1]),
                    "w": nw, "h": nh, "scale": float(scale)}
    return best


DEVICES = [
    {
        "file": "Group 1171275467.png",
        "name": "BLACK",
        "bg_colors": ["black", "cream"],  # sits on black card + overlaps others
        "region": (150, 200, 550, 550),
        "scales": (0.85, 1.15, 0.01),
    },
    {
        "file": "Group 1321314922.png",
        "name": "BLUE",
        "bg_colors": ["white", "cream"],  # sits on white/blue cards
        "region": (350, 150, 550, 550),
        "scales": (0.85, 1.15, 0.01),
    },
    {
        "file": "Group 2147205493.png",
        "name": "PINK",
        "bg_colors": ["pink", "cream", "black"],
        "region": (0, 400, 600, 500),
        "scales": (0.25, 0.55, 0.005),
    },
    {
        "file": "Group 2147205494.png",
        "name": "WHITE",
        "bg_colors": ["white", "blue", "cream"],
        "region": (350, 350, 550, 500),
        "scales": (0.25, 0.55, 0.005),
    },
]

for dev in DEVICES:
    fpath = os.path.join(ELEMENTS_DIR, dev["file"])
    rx, ry, rw, rh = dev["region"]
    search_area = static[ry:min(ry+rh, h), rx:min(rx+rw, w)]

    best_overall = {"confidence": -1}

    for bg_name in dev["bg_colors"]:
        bg_color = CARD_COLORS.get(bg_name, BG_CREAM)
        if bg_name == "cream":
            bg_color = BG_CREAM

        tmpl, nw, nh = composite(fpath, bg_color)
        if tmpl is None:
            continue

        # Match in color
        match = match_multiscale(search_area, tmpl,
                                 dev["scales"][0], dev["scales"][1], dev["scales"][2])
        match["bg"] = bg_name

        # Also try grayscale
        tmpl_gray = cv2.cvtColor(tmpl, cv2.COLOR_BGR2GRAY)
        search_gray = cv2.cvtColor(search_area, cv2.COLOR_BGR2GRAY)
        match_g = match_multiscale(search_gray, tmpl_gray,
                                   dev["scales"][0], dev["scales"][1], dev["scales"][2])
        match_g["bg"] = bg_name + " (gray)"

        for m in [match, match_g]:
            if m["confidence"] > best_overall.get("confidence", -1):
                best_overall = m

    # Offset back to full image coords
    best_overall["x"] += rx
    best_overall["y"] += ry

    elem = cv2.imread(fpath, cv2.IMREAD_UNCHANGED)
    native_h, native_w = elem.shape[:2]

    print(f"{dev['name']} device ({dev['file']})")
    print(f"  Position: x={best_overall['x']}, y={best_overall['y']}")
    print(f"  Render:   {best_overall['w']}x{best_overall['h']} (scale={best_overall['scale']:.3f})")
    print(f"  Native:   {native_w}x{native_h}")
    print(f"  Best bg:  {best_overall.get('bg', '?')}")
    print(f"  Confidence: {best_overall['confidence']:.4f}")
    print()
