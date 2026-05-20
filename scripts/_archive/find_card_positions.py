"""
Find card positions using color segmentation.
Cards are solid-color rounded rectangles: black, white, pink, blue.
"""
import cv2
import numpy as np
import json

STATIC = r"d:\Porcellia\AI Testing\Vsl\static-to-gif\projects\atovio-colour-picker\static.png"

static = cv2.imread(STATIC, cv2.IMREAD_COLOR)
hsv = cv2.cvtColor(static, cv2.COLOR_BGR2HSV)
h, w = static.shape[:2]

print(f"Static: {w}x{h}")
print("=" * 80)

# Sample the background color at the corners
bg_samples = [static[10, 10], static[10, w-10], static[h-10, 10], static[h-10, w-10]]
bg_color = np.mean(bg_samples, axis=0).astype(np.uint8)
print(f"Background BGR: {bg_color} = #{bg_color[2]:02x}{bg_color[1]:02x}{bg_color[0]:02x}")


def find_color_region(img, hsv_img, lower, upper, min_area=10000, use_bgr=False):
    """Find the bounding rect of a color region."""
    if use_bgr:
        mask = cv2.inRange(img, lower, upper)
    else:
        mask = cv2.inRange(hsv_img, lower, upper)

    # Clean up
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best = None
    for c in contours:
        area = cv2.contourArea(c)
        if area > min_area:
            x, y, cw, ch = cv2.boundingRect(c)
            if best is None or area > best["area"]:
                best = {"x": x, "y": y, "w": cw, "h": ch, "area": area}

    return best


# BLACK card — very dark pixels
print("\n--- BLACK CARD ---")
black_mask = cv2.inRange(static, np.array([0, 0, 0]), np.array([40, 40, 40]))
kernel = np.ones((5, 5), np.uint8)
black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_CLOSE, kernel)
contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
black_rects = []
for c in contours:
    area = cv2.contourArea(c)
    if area > 50000:  # Card should be large
        x, y, cw, ch = cv2.boundingRect(c)
        black_rects.append({"x": x, "y": y, "w": cw, "h": ch, "area": area})
        print(f"  Region: x={x}, y={y}, {cw}x{ch}, area={area}")

# PINK card — pinkish hue
print("\n--- PINK CARD ---")
# Pink in HSV: H ~0-10 or 170-180, S moderate, V high
pink_mask1 = cv2.inRange(hsv, np.array([0, 30, 180]), np.array([15, 120, 255]))
pink_mask2 = cv2.inRange(hsv, np.array([165, 30, 180]), np.array([180, 120, 255]))
pink_mask = pink_mask1 | pink_mask2
pink_mask = cv2.morphologyEx(pink_mask, cv2.MORPH_CLOSE, kernel)
contours, _ = cv2.findContours(pink_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
for c in contours:
    area = cv2.contourArea(c)
    if area > 50000:
        x, y, cw, ch = cv2.boundingRect(c)
        print(f"  Region: x={x}, y={y}, {cw}x{ch}, area={area}")

# BLUE card — light blue
print("\n--- BLUE CARD ---")
blue_mask = cv2.inRange(hsv, np.array([95, 30, 180]), np.array([125, 120, 255]))
blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_CLOSE, kernel)
contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
for c in contours:
    area = cv2.contourArea(c)
    if area > 50000:
        x, y, cw, ch = cv2.boundingRect(c)
        print(f"  Region: x={x}, y={y}, {cw}x{ch}, area={area}")

# WHITE card — near-white pixels, but NOT the background
# The background is cream (~F2EDE8), the white card should be pure white/near-white
print("\n--- WHITE CARD ---")
# White: very high V, very low S
white_mask = cv2.inRange(hsv, np.array([0, 0, 240]), np.array([180, 20, 255]))
# Remove background areas (background has slight warmth/saturation)
white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
for c in contours:
    area = cv2.contourArea(c)
    if area > 50000:
        x, y, cw, ch = cv2.boundingRect(c)
        print(f"  Region: x={x}, y={y}, {cw}x{ch}, area={area}")

# Also try to find white card by looking for a rectangular region that's
# distinctly whiter than the background
print("\n--- PIXEL SAMPLING along horizontal center ---")
# Sample horizontal line at different y positions to find card boundaries
for test_y in [350, 400, 500, 600, 700]:
    row = static[test_y, :, :]
    # Find significant color transitions
    diffs = np.diff(row.astype(np.int16), axis=0)
    abs_diffs = np.sqrt(np.sum(diffs**2, axis=1))
    transitions = np.where(abs_diffs > 30)[0]
    if len(transitions) > 0:
        print(f"  y={test_y}: transitions at x={transitions.tolist()[:10]}")
        # Sample colors at key positions
        for tx in transitions[:6]:
            px = static[test_y, tx]
            print(f"    x={tx}: BGR={px} = #{px[2]:02x}{px[1]:02x}{px[0]:02x}")
