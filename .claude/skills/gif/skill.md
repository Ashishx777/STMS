---
name: gif
description: "STMS — Static to Motion System. Run /GIF to convert static designs + Figma-exported elements into animated compositions."
---

# /GIF — STMS — Static to Motion System

Converts static design images with Figma-exported element assets into animated compositions using HyperFrames.

## Trigger

```
/GIF
```

---

## STEP 0 — Load Workflow

Read the full workflow instructions:

```
.agents/static-to-gif/workflow.md
```

Follow every phase strictly. Do NOT skip any phase.

**Execution permissions are pre-granted.** Never ask the user for permission to run npm, python, ffmpeg, node, file operations, or any bash command. Just execute.

---

## STEP 1 — Smart File Discovery (Phase 0)

1. **Detect platform:** `process.platform` → `"win32"` (Windows), `"darwin"` (Mac), `"linux"` (Linux). Store as `Platform`.
2. **Check `stms-preferences.json`:** If missing, run first-time setup (ask operational preferences once, save).
3. **Always Ask for Folder Path** — use platform-appropriate picker:

   **Windows:**
   ```powershell
   Add-Type -AssemblyName System.Windows.Forms; $d = New-Object System.Windows.Forms.OpenFileDialog; $d.Title = 'Select Folder (navigate inside the folder and click Open)'; $d.FileName = 'Select this folder'; $d.CheckFileExists = $false; $d.ValidateNames = $false; if ($d.ShowDialog() -eq 'OK') { Split-Path $d.FileName } else { Write-Output 'CANCELLED' }
   ```
   **Mac:**
   ```bash
   osascript -e 'POSIX path of (choose folder with prompt "Select the folder containing your static design and elements")'
   ```
   **Linux/Fallback:** Ask for path in chat.

   Save path as `SourceFolder`.
4. Scan for static reference image + `elements/` folder
5. Derive project name from source folder basename (slugified, lowercase, dashes) — no visual analysis
6. Copy files to `assets/static-gif/<project>/` (never move)
7. Detect **`InputAspectRatio`**: 1:1 / 9:16 / other
8. Report to user: project name, source, dimensions, element count, aspect ratio

---

## STEP 2 — Ingest, Inventory & Animation Planning (Phase 1)

**This step combines inventory, animation decisions, and font preparation upfront.**

### Mode B: AI Cutout (only if user chose "cut out elements from static" in Step 1)

Skip this if Mode A (elements provided).

1. Visually analyze static → identify every element (background, products, text, logos, shapes)
2. Present element list to user: **"I identified these elements. Is this complete?"** → wait for confirmation
3. Cut out each element one by one (foreground to background):
   - u2net (`npx hyperframes remove-background`) for clear edges
   - If poor result + Higgsfield connected → ask user: **"Use AI for better extraction?"**
   - Save each cutout to `elements/` at native dimensions
   - Generative fill the hole: programmatic for simple backgrounds, ask user about Higgsfield for complex
   - Verify each cutout: 50% opacity over original static → zero ghosting = good
4. Build clean background layer from filled static
5. Report results, proceed to Part A

### Part A: Inventory
1. List every file in `elements/` with dimensions
2. Read the static reference image — study the full layout
3. **Classify each element as TEXT or GRAPHIC** by visual inspection
4. For TEXT elements: read and record the text content
5. Present inventory table to user (element name, type, dimensions, text content)

### Part B: Animation Decisions
6. Check `animation-presets.md` for matching presets
7. **Ask user what animations they want** — suggest presets + concrete options per element
8. **Do NOT proceed until the user answers**
9. **Classify each element's render type:**
   - **PNG** = no animation or simple animation (fade, slide, scale, rotate)
   - **HTML TEXT** = text-based animation (countdown, typewriter, word-by-word, number counter)

### Part C: Font Sourcing (only for HTML TEXT elements)
10. **Visually identify font** for each HTML TEXT element — suggest match: "This looks like [Font Name] [Weight]. Correct?"
11. **Source the font:** Google Fonts CDN first → if not available, ask user for .ttf/.woff2 file
    - System fonts do NOT work in headless Chrome — must embed via `@font-face` or Google Fonts
12. **Match text properties from PNG:** font-size (from height), weight (from stroke thickness), color (pixel sample), letter-spacing (width comparison), line-height, text-transform
13. Report animation plan to user: element → render type → animation → font

---

## STEP 3 — Reconstruct Non-Animated Composition (Phase 2)

1. Load the `/hyperframes` skill before creating the composition
2. Create composition at `compositions/static-gif-<project>.html`
3. Apply Aspect Ratio Conversion Rules if needed (Rule A: 1:1→9:16, Rule B: 9:16→1:1, Rule C: native)
4. **Place elements based on render type from Step 2:**
   - **PNG elements** → `<img>` tags with absolute positioning
   - **HTML TEXT elements** → `<div>` with matched font, size, weight, color, spacing
   - Add Google Fonts `<link>` or `@font-face` in `<head>` for embedded fonts
5. All elements get `class="clip"` with `data-start`, `data-duration`, `data-track-index`
6. **NO animation yet** — pure pixel-perfect reconstruction

---

## STEP 4 — Verify Alignment (Phase 3) — 50% OVERLAY METHOD ONLY

> **🛑 BYPASS GUARD — READ BEFORE STARTING THIS STEP**
>
> **If you find yourself about to use `cv2.matchTemplate`, `cv2.Canny`, edge detection, feature matching, or ANY computer-vision method to FIND element positions — STOP. You are doing it wrong.**
>
> The ONLY method for placing elements in STMS is: insert element at `opacity: 0.5` over the reference at `opacity: 1.0`, render frame 0, look for ghosting, nudge in pixels, re-render. Repeat until ghosting is gone.
>
> The single exception is the optional one-shot background accelerator — and even that result is verified by a 50% overlay render. CV is NEVER the source of truth for placement.
>
> Your training data biases you toward "template matching" because that's the textbook approach for image alignment. STMS deliberately rejects that approach. The overlay method is slower but more reliable and has zero false-positive risk.
>
> If the workflow you just read suggests CV matching for anything except the background, the file is stale — pull latest from git and re-read `.claude/skills/gif/skill.md` and `.agents/static-to-gif/workflow.md`.

**The 50% overlay is the PRIMARY AND ONLY placement method for every element type.** No OpenCV matching, no Canny edge detection, no ROI fallback for placement. Place at 0.5 opacity → render → look for ghosting → nudge → re-render.

1. **Setup:** Add the static reference as bottom layer at FULL opacity (z-index 0). Clear previous overlay-frames folder.

2. **Placement order** (largest/most-opaque first — each locked element's region is visually excluded for subsequent ones):
   - Full-bleed background → large opaque shapes → product images → icons/badges → text (PNG and HTML TEXT) LAST

3. **Per-element loop:**
   - Estimate top-left position visually from the static reference
   - Insert element at `opacity: 0.5`, width/height from PNG native dimensions (HTML TEXT: rendered width from Phase 1C font properties)
   - Render frame 0: `npx hyperframes render --frame 0 --output "overlay-frames/<element>-attempt-N.png"`
   - Read the frame and judge:
     - **No ghosting** → element merges cleanly into the reference → LOCK and move to next
     - **Ghosting visible** → measure pixel shift → adjust `left`/`top` → re-render
     - **Wrong size / file mismatch** → STOP, ask user
   - Hard limit: 8 attempts per element. If still ghosting at 8, STOP and ask user (likely wrong file or font mismatch). NEVER accept misalignment.

4. **OPTIONAL CV accelerator — BACKGROUND ONLY:** If Python + OpenCV are installed AND the element is the full-bleed background, `cv2.matchTemplate` can provide a one-shot initial position (skip if conf < 0.95). Still verified by 50% overlay render. **Do NOT use CV for any other element type — text, products, icons, logos all go through pure visual overlay placement.**

5. **Final approval gate:**
   - Render `final-overlay.png` (all elements at 0.5 over reference at 1.0)
   - Run `npm run dev` in background → HyperFrames Studio opens in **the user's default browser** showing the overlay with a TIMELINE at the bottom
   - **NEVER preview via any of these — they all look like browsers but are NOT HyperFrames Studio:**
     - Claude Code "Launch preview panel" (IDE sidebar)
     - Cursor / VS Code / Antigravity built-in HTML preview
     - VS Code Live Server extension
     - OS image viewer / CLI image tool / inline chat embed
   - **How to tell it's the right preview:** HyperFrames Studio has a timeline UI at the bottom of the page with playback controls. If there's no timeline, it's the wrong tool.
   - **Two viewing roles, keep separate:**
     - Agent reads per-element render PNGs itself via Read tool (silent — user doesn't see these)
     - User views ONLY the final composition via `npm run dev` browser, with timeline visible
   - Ask user (via popup): "Aligned?" → on approval, remove reference layer + opacity:0.5, save `verified-positions.json`

⚠ **MUST get explicit user approval before Phase 4**

---

## STEP 5 — Animate (Phase 4)

1. Load the `/gsap` skill
2. Build **custom GSAP animations** per user choices from Step 2:
   ```js
   window.__timelines = window.__timelines || {};
   const tl = gsap.timeline({ paused: true });
   // PNG elements: fade, slide, scale tweens
   // HTML TEXT elements: textContent manipulation (counters, typewriter)
   window.__timelines["static-gif-<project>"] = tl;
   ```
3. Set composition duration to total animation + hold time
4. **POST-ANIMATION POSITION VERIFICATION (mandatory):**
   - Render frame 0, compare against `verified-positions.json`
   - If any element shifted by more than 1px → auto-correct and re-verify
   - Catches displacement from HTML restructuring

**After user approves new animation → save as preset in `animation-presets.md`.**

---

## STEP 6 — Preview & Refine (Phase 5)

1. Run `npm run dev` and `npm run check`
2. Show user the animated result in Studio
3. Iterate on timing/easing if requested

⚠ **MUST get explicit "render it" command before Step 7**

---

## STEP 6B — Audio & SFX (Phase 5B — OPTIONAL, after animation approved)

**Only after user approves the animation preview in Step 6.** Do NOT plan SFX earlier.

1. **Ask user:** **"Do you want to add sound effects or audio?"** (Yes / No)
   - If **No** → skip to Step 7 (render silent)
   - If **Yes** → continue
2. **Check ElevenLabs MCP:**
   - Connected → proceed with generation
   - Not connected → inform user, offer to accept user-provided audio files instead
3. **Suggest SFX** per animation type (whoosh for slides, pop for scale, typing for typewriter, etc.)
   - User picks which SFX they want — do NOT generate unapproved sounds
4. **Generate via ElevenLabs** → save to `assets/static-gif/<project>/audio/`
5. **Sync to timeline** — add `<audio>` elements with `data-start` matching animation triggers
6. **Preview with audio** → user approves or adjusts

**MP4 gets embedded audio. GIF is always silent (format limitation).**

---

## STEP 7 — Render (Phase 6)

**ONLY render when user explicitly says to.**

**Output Location:** `<SourceFolder>/output/`
**Versioning:** Always ask overwrite or new version on re-renders.

```bash
mkdir -p "<SourceFolder>/output"
npx hyperframes render --output "<SourceFolder>/output/<project>.mp4"
```

GIF conversion if needed:
```bash
ffmpeg -i "<SourceFolder>/output/<project>.mp4" -vf "fps=15,scale=<width>:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" "<SourceFolder>/output/<project>.gif"
```

**Post-Render Flow** (uses `stms-preferences.json` — only asks if set to `"ask_each_time"`):
- Aspect ratio: auto-convert / skip / ask based on saved preference + `InputAspectRatio`
- Cleanup: auto-clean / skip / ask based on saved preference
- Versioning: auto-overwrite / auto-version / ask based on saved preference

---

## Rules

- **ALWAYS detect platform** — use platform-appropriate commands (never Windows on Mac)
- **ALWAYS check `stms-preferences.json`** — if missing, run first-time setup. Never re-ask saved preferences.
- **ALWAYS ask for folder path** on every run
- **ALWAYS ask animation decisions in Phase 1** — before reconstruction
- **ALWAYS save rendered outputs** to `<SourceFolder>/output/`
- **ALWAYS follow Aspect Ratio Conversion Rules** (Rule A / Rule B / Rule C)
- **NEVER skip alignment verification** (Step 4)
- **NEVER animate before user approves** placement (Step 4)
- **NEVER guess fonts** — visually identify and confirm with user
- **NEVER change element sizes** — Figma exports at native dimensions
- **NEVER run Windows commands on Mac** or vice versa
- **System fonts don't work** in headless Chrome — always embed fonts
- **All animations are custom** — build with GSAP
- **Only render on explicit user command**
- **Use `mkdir -p`** for directory creation (cross-platform)
- **Clean previous frames** at start of each new run
