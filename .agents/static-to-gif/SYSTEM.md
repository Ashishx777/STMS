# STMS — Static to Motion System

## What It Is

An AI-powered pipeline (STMS) that converts static design images (Figma exports) into animated GIF/MP4 compositions. Point it at a folder with a static reference + exported element layers → get a pixel-perfect animated version out.

Built on [HyperFrames](https://hyperframes.heygen.com) with GSAP animations, rendered via headless Chrome.

---

## How It Works

### Input
- A **static reference image** (the final design as a flat PNG/JPG)
- An **elements folder** (individual layers exported from Figma — products, text labels, backgrounds, logos, etc.)
- Files can live **anywhere** — Desktop, Downloads, a shared drive, wherever

### Output
- Animated **MP4** and/or **GIF** with the same visual as the static, but with motion

### The Pipeline

```
/GIF <path>           (or just /GIF — agent asks for path)
  │
  ├── Phase 0: Smart File Discovery
  │   Accept path arg or ask → scan source → auto-name project
  │   Detect input aspect ratio (1:1 / 9:16 / other)
  │   COPY files to assets/static-gif/<name>/ (source untouched)
  │
  ├── Phase 1: Ingest, Inventory & Animation Planning
  │   Mode B (if no elements): AI cutout from static → user confirms element list
  │   → segment each element → generative fill holes → verify cutouts
  │   Inventory all elements, classify as TEXT or GRAPHIC
  │   Ask user: what animations do you want? (presets + suggestions)
  │   Classify elements as PNG or HTML TEXT based on animation type
  │   For HTML TEXT: identify font → confirm → source → match properties from PNG
  │
  ├── Phase 2: Reconstruct
  │   Build HTML composition with correct element types:
  │   PNG <img> for graphic/simple-animation elements
  │   HTML <div> with matched font for text-animation elements
  │   9:16 expansion: user chooses programmatic or AI (Higgsfield) fill
  │   NO resizing — only positioning (left, top)
  │
  ├── Phase 3: Overlay Positioning (THE core technique)
  │   Reference image at full opacity as base layer
  │   Elements matched in SMART ORDER (largest/opaque first)
  │   Opaque elements: standard template matching
  │   Transparent elements: edge-based matching (Canny)
  │   HTML text verified directly against reference — no double work
  │   User approves final placement
  │   Verified positions saved to JSON
  │
  ├── Phase 4: Animate
  │   Custom GSAP timeline animations
  │   Post-animation position check against Phase 3 verified positions
  │   Auto-corrects any displacement from HTML restructuring
  │   Approved animations saved as reusable presets
  │
  ├── Phase 5: Preview & Refine
  │   Preview in Studio, user adjusts timing/easing
  │
  ├── Phase 5B: Audio & SFX (optional, after animation approved)
  │   Ask user: "Want to add sound effects?"
  │   If yes + ElevenLabs connected: suggest SFX per animation → generate → sync
  │   If no: render silent
  │
  └── Phase 6: Render
      MP4 with audio (if SFX added) / GIF always silent
      Smart aspect ratio conversion (1:1↔9:16 or 9:16↔1:1)
      Ask user to clean up temporary files
```

---

## Key Innovation: The Overlay Method

The system's core positioning technique. Instead of guessing coordinates or relying solely on template matching:

1. The **reference image** sits at the bottom at **full opacity**
2. Each **element** is placed on top at **50% opacity**
3. After each element, a **single frame is rendered**
4. **Perfect alignment** = element blends seamlessly into the reference (no ghosting)
5. **Misalignment** = visible doubling → adjust and re-render

This eliminates guesswork entirely. Every element is verified visually against the original design before moving on.

### Smart Matching Order

Elements are matched in order of size and opacity (largest/most-opaque first). Each confirmed element's bounding box is excluded from the search region for subsequent elements, progressively shrinking the search space. By the time small text elements are reached, the system is searching a fraction of the original canvas.

Order: full-bleed backgrounds → large opaque shapes → product images → icons/badges/logos → text/transparent overlays.

### Edge-Based Matching for Transparent Elements

Standard OpenCV template matching fails on transparent and semi-transparent elements (text overlays, badges with alpha, curved text). Instead of falling back to slow ROI pixel-difference search, the system uses Canny edge detection on both the element and the reference region. Edges are binary and unaffected by transparency — this makes matching fast and accurate for exactly the elements that cause standard matching to fail.

### Post-Animation Position Verification

After Phase 5 adds GSAP animations (which may restructure HTML by wrapping elements in containers), the system renders frame 0 and compares every element's position against the verified positions saved in Phase 3. If any element has shifted by more than 1px, it auto-corrects before the user ever sees the preview. This ensures animation never displaces verified element positions.

---

## Adaptive Learning

The system improves with every project:

### What It Remembers
- **Process rules** — overlay method, no size changes, single-frame static checks, font handling
- **User preferences** — efficiency expectations, minimal questions, suggest don't ask
- **Past mistakes** — never repeated (stored in memory + workflow)

### Animation Presets
Approved animations are saved in `animation-presets.md` and suggested for matching layouts in future projects:

| Preset | Layout Type | Best For |
|--------|------------|----------|
| Slide-In Fade Blur (Left/Right) | 2x2 grid, multi-item | Product showcases, comparisons |
| Counter Animation (Count-Up) | Stats/numbers | Feature highlights, specs |

The preset library grows with each completed project.

---

## Rules (Non-Negotiable)

- **ALWAYS ask for the folder path** — every single time `/GIF` is run
- **ALWAYS ask animation decisions in Phase 1** — before reconstruction, so the system knows which elements need HTML text vs PNG
- **ALWAYS render to the selected folder's `output/` subfolder**
- **ALWAYS give the option to overwrite or create a version** — on re-renders
- **ALWAYS follow the Aspect Ratio Conversion Rules** — Rule A (1:1→9:16) or Rule B (9:16→1:1). Never scale elements.
- **ALWAYS suggest animations with options** — presets first, then custom
- **ALWAYS ask aspect ratio and cleanup questions in chat** — adapts based on `InputAspectRatio`
- **NEVER change element sizes** — Figma exports are at native pixel dimensions
- **NEVER skip overlay verification** — Phase 3 is MANDATORY
- **NEVER guess positions** — overlay method for positioning
- **NEVER animate before user approves** static placement in Phase 3
- **NEVER guess fonts** — visually identify and confirm with user in Phase 1
- **Source files are NEVER moved or deleted** — only copied
- **System fonts do NOT work** in headless Chrome — always embed via Google Fonts or @font-face
- **All animations are custom** — build from scratch with GSAP
- **Only render on explicit user command**

---

## File Structure

```
.agents/static-to-gif/
  workflow.md              # Full phase-by-phase process
  animation-presets.md     # Approved animation library (grows over time)
  SYSTEM.md                # This file — system description

assets/
  static-gif/
    <project-name>/        # Project assets (copied from source, never moved)
      static.png
      elements/

static-to-gif/
  imports/                 # Legacy drop folder (still supported)
  projects/                # Project metadata & overlay debug frames
  output/                  # Legacy/default deliverables folder (active output is placed in <SourceFolder>/output/)

compositions/
  static-gif-<project>.html   # HyperFrames composition files

scripts/
  _archive/                # Legacy Python helper scripts
```

---

## Tech Stack

- **HyperFrames** — HTML-based video composition framework
- **GSAP** — Animation engine (timelines, tweens, easing)
- **Headless Chrome** — Frame capture and rendering
- **FFmpeg** — MP4 → GIF conversion with palette optimization
- **OpenCV + NumPy** — Template matching helpers (supplementary, in `scripts/_archive/`)
- **Python PIL** — Pixel analysis for edge cases (low-contrast text)
