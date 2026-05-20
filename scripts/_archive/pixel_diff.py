"""
Pixel-diff comparison: render vs static reference.
Outputs a diff heatmap and per-region error statistics.
"""
import cv2
import numpy as np

STATIC = r"d:\Porcellia\AI Testing\Vsl\static-to-gif\projects\atovio-colour-picker\static.png"
RENDER = r"d:\Porcellia\AI Testing\Vsl\temp_verify\atovio-frames\frame_000060.png"
OUTPUT = r"d:\Porcellia\AI Testing\Vsl\temp_verify\pixel_diff.png"

static = cv2.imread(STATIC, cv2.IMREAD_COLOR)
render = cv2.imread(RENDER, cv2.IMREAD_COLOR)

if static.shape != render.shape:
    print(f"Size mismatch: static={static.shape}, render={render.shape}")
    render = cv2.resize(render, (static.shape[1], static.shape[0]))

# Compute absolute difference
diff = cv2.absdiff(static, render)
diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

# Overall stats
total_pixels = diff_gray.size
mean_err = np.mean(diff_gray)
max_err = np.max(diff_gray)
perfect = np.sum(diff_gray == 0)
near_perfect = np.sum(diff_gray <= 3)
significant = np.sum(diff_gray > 20)

print(f"Overall pixel diff stats:")
print(f"  Mean error:     {mean_err:.2f} / 255")
print(f"  Max error:      {max_err}")
print(f"  Perfect pixels: {perfect}/{total_pixels} ({100*perfect/total_pixels:.1f}%)")
print(f"  Near-perfect:   {near_perfect}/{total_pixels} ({100*near_perfect/total_pixels:.1f}%)")
print(f"  Significant:    {significant}/{total_pixels} ({100*significant/total_pixels:.1f}%)")
print()

# Per-region analysis
REGIONS = {
    "Logo":       (477, 52, 127, 38),
    "Headline":   (81, 154, 919, 65),
    "Card-Black": (0, 321, 524, 283),
    "Card-White": (556, 321, 524, 283),
    "Card-Pink":  (0, 699, 524, 283),
    "Card-Blue":  (556, 699, 524, 283),
    "Label-1":    (55, 365, 186, 196),
    "Label-2":    (852, 365, 177, 196),
    "Label-3":    (54, 763, 139, 156),
    "Label-4":    (907, 763, 122, 196),
    "Device-Black": (269, 263, 329, 424),
    "Device-Blue":  (552, 254, 312, 405),
    "Device-Pink":  (269, 626, 189, 159),
    "Device-White": (575, 626, 174, 176),
}

print("Per-region analysis:")
print(f"{'Region':<15} {'Mean Err':>10} {'Max Err':>10} {'Perfect%':>10} {'Sig>20%':>10}")
print("-" * 60)
for name, (rx, ry, rw, rh) in REGIONS.items():
    region_diff = diff_gray[ry:ry+rh, rx:rx+rw]
    r_mean = np.mean(region_diff)
    r_max = np.max(region_diff)
    r_perfect = 100 * np.sum(region_diff == 0) / region_diff.size
    r_sig = 100 * np.sum(region_diff > 20) / region_diff.size
    print(f"{name:<15} {r_mean:>10.2f} {r_max:>10} {r_perfect:>9.1f}% {r_sig:>9.1f}%")

# Generate diff heatmap
diff_amplified = cv2.normalize(diff_gray, None, 0, 255, cv2.NORM_MINMAX)
heatmap = cv2.applyColorMap(diff_amplified, cv2.COLORMAP_JET)

# Side by side: static | render | diff
combined = np.hstack([static, render, heatmap])
cv2.imwrite(OUTPUT, combined)
print(f"\nDiff heatmap saved: {OUTPUT}")

# Also save just the diff heatmap at full size
cv2.imwrite(r"d:\Porcellia\AI Testing\Vsl\temp_verify\diff_heatmap.png", heatmap)
