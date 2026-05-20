"""
Find exact card and element positions by pixel sampling and edge detection.
"""
import cv2
import numpy as np
import json

STATIC = r"d:\Porcellia\AI Testing\Vsl\static-to-gif\projects\atovio-colour-picker\static.png"

static = cv2.imread(STATIC, cv2.IMREAD_COLOR)
h, w = static.shape[:2]
print(f"Static: {w}x{h}")

# Background color (average of corners)
bg = np.mean([static[5, 5], static[5, w-5], static[h-5, 5], static[h-5, w-5]], axis=0)
print(f"Background: BGR={bg.astype(int)}")


def is_bg(pixel, threshold=25):
    """Check if a pixel is background color."""
    return np.sqrt(np.sum((pixel.astype(float) - bg) ** 2)) < threshold


def find_vertical_edges(col_x, start_y=0, end_y=None):
    """Scan a column to find where non-background regions start/end."""
    if end_y is None:
        end_y = h
    edges = []
    in_region = False
    region_start = 0
    for y in range(start_y, end_y):
        px = static[y, col_x]
        bg_match = is_bg(px)
        if not bg_match and not in_region:
            in_region = True
            region_start = y
        elif bg_match and in_region:
            in_region = False
            edges.append((region_start, y - 1))
    if in_region:
        edges.append((region_start, end_y - 1))
    return edges


def find_horizontal_edges(row_y, start_x=0, end_x=None):
    """Scan a row to find where non-background regions start/end."""
    if end_x is None:
        end_x = w
    edges = []
    in_region = False
    region_start = 0
    for x in range(start_x, end_x):
        px = static[row_y, x]
        bg_match = is_bg(px)
        if not bg_match and not in_region:
            in_region = True
            region_start = x
        elif bg_match and in_region:
            in_region = False
            edges.append((region_start, x - 1))
    if in_region:
        edges.append((region_start, end_x - 1))
    return edges


print("\n=== VERTICAL SCAN at x=5 (left edge, inside left cards) ===")
left_edges = find_vertical_edges(5)
for start, end in left_edges:
    color = static[start + 5, 5]
    print(f"  y={start} to y={end} (height={end - start + 1}) color=BGR{color.tolist()}")

print("\n=== VERTICAL SCAN at x=1075 (right edge, inside right cards) ===")
right_edges = find_vertical_edges(1075)
for start, end in right_edges:
    color = static[start + 5, 1075]
    print(f"  y={start} to y={end} (height={end - start + 1}) color=BGR{color.tolist()}")

print("\n=== HORIZONTAL SCAN at y=5 (top edge) ===")
top_edges = find_horizontal_edges(5)
for start, end in top_edges:
    print(f"  x={start} to x={end} (width={end - start + 1})")

# Scan at various y positions to find card boundaries
print("\n=== HORIZONTAL SCANS at card regions ===")
for test_y in [250, 300, 320, 325, 330, 340, 350, 400, 500, 600, 650, 660, 670, 680, 700, 800, 900, 950, 960]:
    hedges = find_horizontal_edges(test_y)
    if hedges:
        regions = []
        for start, end in hedges:
            color = static[test_y, (start + end) // 2]
            regions.append(f"x={start}-{end}(w={end-start+1}) BGR{color.tolist()}")
        print(f"  y={test_y}: {'; '.join(regions)}")

# Find the exact boundaries of the card grid
print("\n=== FINDING CARD GRID BOUNDARIES ===")
# Scan the leftmost 3 pixels of each row to find where left cards start/end
print("Scanning x=2 column for left-card top/bottom edges:")
left_col = find_vertical_edges(2, start_y=200, end_y=1000)
for start, end in left_col:
    color = static[(start + end) // 2, 2]
    print(f"  y={start} to y={end} (height={end-start+1}) mid-color=BGR{color.tolist()}")

print("\nScanning x=1078 column for right-card top/bottom edges:")
right_col = find_vertical_edges(1078, start_y=200, end_y=1000)
for start, end in right_col:
    color = static[(start + end) // 2, 1078]
    print(f"  y={start} to y={end} (height={end-start+1}) mid-color=BGR{color.tolist()}")

# Find horizontal extent of cards at reliable y positions
print("\n=== CARD LEFT/RIGHT EDGES ===")
# For top cards - scan at y where we expect to be inside the card but outside devices
# The devices overlap in the center, so scan at the extreme left/right of the cards
print("Top cards row - scanning y=330:")
print(f"  Regions: {find_horizontal_edges(330)}")
print("Top cards row - scanning y=600:")
print(f"  Regions: {find_horizontal_edges(600)}")
print("Bottom cards row - scanning y=680:")
print(f"  Regions: {find_horizontal_edges(680)}")
print("Bottom cards row - scanning y=950:")
print(f"  Regions: {find_horizontal_edges(950)}")
