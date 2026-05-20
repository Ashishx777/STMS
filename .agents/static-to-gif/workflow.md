# STMS — Static to Motion System Workflow

## Overview

Converts static design images (with Figma-exported element assets) into animated compositions (GIF or MP4) using HyperFrames.

---

## Command Syntax

```
/GIF                              → Agent asks where the files are
/GIF <path>                       → Agent reads directly from that path
/GIF --project <existing-name>    → Resume an existing project
```

---

## Folder Structure

```
assets/
  static-gif/
    <project-name>/             # Assets for this project (copied from source)
      static.png                # The full static reference image
      elements/                 # Figma export or AI cutout — individual layers
      fonts/                    # Font files for text animation (if needed)
      audio/                    # SFX and music files (if Phase 5B used)
      generated/                # AI-generated assets (Higgsfield outputs)

static-to-gif/
  stms-preferences.json         # One-time user preferences (created on first run)
  imports/                      # Legacy drop folder (still supported)
  projects/                     # Project metadata & overlay debug frames
    <project-name>/
      overlay-frames/           # Overlay verification renders (temp)
      verified-positions.json   # Element positions confirmed in Phase 3
  output/                       # Final GIFs/MP4s land here

compositions/
  static-gif-<project>.html     # HyperFrames composition files
```

---

## Step-by-Step Workflow

### FIRST RUN SETUP: One-Time Permissions

**On the very first `/GIF` run in a project, check for `static-to-gif/stms-preferences.json`.** If it doesn't exist, ask the user these operational questions ONCE, save their answers, and never ask again:

```
"Before we start, I need to set up your preferences (one time only):"

1. After rendering, do you want me to automatically generate the alternate aspect ratio version?
   → Always yes / Always no / Ask each time

2. After rendering, do you want me to automatically clean up temporary debug files?
   → Always yes / Always no / Ask each time

3. When re-rendering, should I overwrite the previous file or create a new version?
   → Always overwrite / Always new version / Ask each time
```

Save to `static-to-gif/stms-preferences.json`:
```json
{
  "created": "2026-05-20",
  "platform": "windows",
  "aspect_ratio_conversion": "always_yes",
  "cleanup_after_render": "always_yes",
  "overwrite_behavior": "always_ask"
}
```

**On subsequent runs:** Read `stms-preferences.json` and apply saved preferences silently. Never re-ask operational questions unless the user explicitly says to change preferences.

**To change preferences later:** User can say "update my STMS preferences" or "change cleanup setting" at any time.

**Questions that are ALWAYS asked** (creative/quality decisions that change per project):
- Animation choices (Phase 1 Part B) — different per design
- Font confirmation (Phase 1 Part C) — different per design  
- Overlay placement approval (Phase 3) — quality gate, non-negotiable
- "Render it" command (Phase 5→Phase 6) — explicit trigger

---

### PLATFORM DETECTION

**Auto-detect the platform at the start of every run** and store as `Platform` variable:

```bash
# Auto-detect
if [[ "$OSTYPE" == "darwin"* ]]; then
  Platform="mac"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
  Platform="windows"
else
  Platform="linux"
fi
```

Or via Node.js: `process.platform` returns `"win32"`, `"darwin"`, or `"linux"`.

All platform-specific commands in this workflow use the `Platform` variable to select the correct variant. The agent must NEVER run a Windows command on Mac or vice versa.

---

### EXECUTION PERMISSIONS — PRE-GRANTED

**All code execution permissions are pre-granted in `.claude/settings.local.json`.** The agent must NEVER ask the user for permission to run any command — just execute.

Pre-approved commands (execute without asking):
- `npm run dev` / `npm run check` / `npm run render`
- `npx hyperframes render` / `npx hyperframes lint` / `npx hyperframes inspect`
- `python` / `python3` (OpenCV, PIL, composite checks, any helper scripts)
- `ffmpeg` (MP4→GIF conversion, palette optimization)
- `mkdir -p` / `cp` / `rm` (file operations)
- Platform folder pickers (PowerShell on Windows, osascript on Mac)
- `node` / `npx` (any Node.js execution)
- File read/write operations anywhere in the project

**The user has granted blanket permission once. Do NOT re-ask. Do NOT confirm before running. Just run the command.**

If a command fails, report the error and fix it — don't ask if you're allowed to retry.

#### Platform-Specific Security Setup (one-time, handled on first run)

The agent must detect the platform and ensure the required OS-level permissions are in place. If any are missing, guide the user through granting them ONCE — then never mention it again.

**Windows:**
- No special OS permissions needed. PowerShell and Node.js run without restrictions by default.
- If Windows Defender blocks a script → tell user to allow it in Windows Security settings.

**Mac (macOS has stricter security — handle with care):**
- **Terminal / Antigravity needs "Files and Folders" access** — macOS will prompt the user the first time the agent tries to read/write outside the project directory. The user clicks "Allow" once and it persists.
- **`osascript` (folder picker) may trigger a one-time security prompt** — "[App] wants to control Finder." The user clicks "OK" once.
- **Homebrew tools (python3, ffmpeg)** must be installed via `brew install python ffmpeg` and available in PATH. If not found, guide the user:
  ```bash
  # Check if Homebrew is installed
  which brew || echo "Install Homebrew first: https://brew.sh"
  # Install required tools
  brew install python ffmpeg
  ```
- **Gatekeeper / SIP** — the STMS system does NOT require disabling Gatekeeper or SIP. All tools run within normal macOS security boundaries.
- **No admin password is ever needed** during normal STMS operation. If a command asks for `sudo`, something is wrong — do NOT run it. Report the issue instead.

**Linux:**
- No special permissions needed. Ensure `python3`, `ffmpeg`, and `node` are installed:
  ```bash
  # Debian/Ubuntu
  sudo apt install python3 python3-pip ffmpeg nodejs npm
  # Arch
  sudo pacman -S python ffmpeg nodejs npm
  ```
- After initial install, no `sudo` is needed for STMS operations.

**Trust principle:** The STMS system never requires elevated privileges (admin/root/sudo) for normal operation. It only reads/writes within the project directory and the user-selected source folder. If any command requests elevated access, it is a bug — report it, don't grant it.

---

### PHASE 0: Smart File Discovery

1. **Resolve the source folder (Always Ask):**
   - Every single time `/GIF` is run, the Agent **must** ask the user for the folder path.
   - Even if `/GIF <path>` is used, the Agent **must** confirm this path with the user.
   - **Use the platform-appropriate folder picker:**

     **Windows:**
     ```powershell
     Add-Type -AssemblyName System.Windows.Forms; $d = New-Object System.Windows.Forms.OpenFileDialog; $d.Title = 'Select Folder (navigate inside the folder and click Open)'; $d.FileName = 'Select this folder'; $d.CheckFileExists = $false; $d.ValidateNames = $false; if ($d.ShowDialog() -eq 'OK') { Split-Path $d.FileName } else { Write-Output 'CANCELLED' }
     ```

     **Mac:**
     ```bash
     osascript -e 'POSIX path of (choose folder with prompt "Select the folder containing your static design and elements")'
     ```

     **Linux / Fallback:**
     Ask the user for the path in chat: **"Please paste the full path to the folder containing your static design and elements."**

   - If the dialog returns `CANCELLED` or the user does not provide a path, stop and tell the user that a folder selection is required.
   - Save the selected folder path as the **`SourceFolder`** variable.

2. **Scan the source location** — find:
   - A **static reference image** (the largest `.png`, `.jpg`, or `.webp` file)
   - An **`elements/` subfolder** with individual layer PNGs

3. **If no `elements/` folder found — ASK the user:**
   > **"I found a static image but no elements folder. How do you want to proceed?"**
   > 1. **"I have elements in a different folder"** → ask for the path, use those
   > 2. **"Cut out the elements from the static using AI"** → enter **Mode B** (AI-assisted cutout — see Phase 1 Mode B)
   > 3. **"I’ll export them from Figma and come back"** → stop, wait for user
   
   Store the user's choice as `ElementMode`: `"exported"` (Mode A) or `"ai_cutout"` (Mode B).
   
   **Do NOT assume Mode B automatically.** Only enter AI cutout mode when the user explicitly chooses option 2.

4. **Auto-name the project** — read the static image visually, derive a descriptive name (e.g., `atovio-colour-picker`, `summer-sale-banner`, `product-launch-hero`)

5. **Set up project structure:**
   - **Copy** (NOT move) the static image → `assets/static-gif/<project-name>/static.png`
   - **If Mode A:** Copy the elements folder → `assets/static-gif/<project-name>/elements/`
   - **If Mode B:** Create empty `assets/static-gif/<project-name>/elements/` (will be populated in Phase 1)
   - Create project folder → `static-to-gif/projects/<project-name>/`
   - Source files remain untouched at their original location

6. **Detect and store the input aspect ratio** as the **`InputAspectRatio`** variable:
   - Width = Height → `1:1`
   - Width × 1.77 ≈ Height (within 5%) → `9:16`
   - Anything else → `other` (store actual W×H)

7. **Report to user:**
   > Project: `<project-name>`
   > Source: `<path>`
   > Static: `<filename>` (WxH)
   > Elements: X files found / Mode B (AI cutout pending)
   > Aspect Ratio: `<detected ratio>`
   
   Proceed immediately to Phase 1 — do NOT block waiting for name confirmation.

### PHASE 1: Ingest, Inventory & Animation Planning

This phase combines element inventory, animation decisions, and font preparation into a single upfront planning step. By deciding animations before reconstruction, the system knows which elements need HTML text (for text-based animation) versus PNG (for simple animation) — eliminating double work.

#### Mode B: AI-Assisted Element Cutout (only if `ElementMode` is `"ai_cutout"`)

**Skip this section entirely if Mode A (user provided elements).** This section runs ONLY when the user explicitly chose AI cutout in Phase 0.

1. **Visually analyze the static reference** — identify every distinct visual element:
   - Background layer (solid, gradient, pattern, or photographic)
   - Product images / photos
   - Text elements (headlines, labels, prices, CTAs)
   - Logos / icons / badges
   - Decorative shapes (circles, lines, gradients)
   - Any other distinct visual component

2. **Present the element map to user for confirmation:**
   > **"I identified these elements in the static:"**
   > 1. Background — gradient with grid pattern
   > 2. Product image (purifier, center) — ~380×450px
   > 3. Headline text — "LOWEST PRICE EVER"
   > 4. Price badge — "₹4,999" bottom-right
   > 5. Logo — top-left corner
   > ...
   > **"Is this complete? Any elements I missed or should split differently?"**
   
   **Do NOT proceed until user confirms the element list.**

3. **Cut out each element one by one:**
   - Work from **foreground to background** (top layers first)
   - For each element:
     a. **Identify the element boundary** in the static (bounding box)
     b. **Use AI segmentation to isolate it:**
        - `npx hyperframes remove-background` (u2net) for objects with clear edges
        - If u2net produces poor results (complex edges, hair, transparency) AND Higgsfield MCP is connected → ask user: **"The cutout for [element] isn’t clean enough. Want me to use AI (Higgsfield) for a better extraction?"**
        - If Higgsfield not connected or user declines → use OpenCV contour detection + manual refinement
     c. **Save the cutout** as `assets/static-gif/<project>/elements/<element-name>.png` at native dimensions
     d. **Generative fill the hole** left in the working background:
        - If background is solid/gradient/pattern → programmatic fill (PIL/numpy) — no AI needed
        - If background is photographic/complex AND Higgsfield MCP is connected → ask user: **"The background behind [element] needs AI fill. Use Higgsfield to generate it?"**
        - If user declines or no Higgsfield → use OpenCV `inpaint` as fallback
     e. **Verify the cutout** — place cutout at 50% opacity over original static at the same position. If it merges cleanly with zero ghosting → cutout is good. If ghosting visible → refine edges and retry.

4. **Build the clean background layer:**
   - After all foreground elements are cut out and holes are filled, the remaining image is the clean background
   - Save as `assets/static-gif/<project>/elements/background.png`

5. **Report cutout results:**
   > **"AI cutout complete:"**
   > - X elements extracted and saved to elements/
   > - Background cleaned and saved
   > - All cutouts verified against static reference
   >
   > Proceeding to inventory.

**After Mode B completes, the elements folder is populated and the rest of Phase 1 proceeds identically to Mode A.**

---

#### Part A: Inventory

1. **Scan the project assets** — list all files in `assets/static-gif/<project>/`
2. **Identify the static reference** — the full-frame design image
3. **Read the static reference image** — visually inspect to understand the full layout
4. **Inventory elements** — for each file in `elements/`:
   - File name, dimensions (W×H), file size
   - **Classify as TEXT or GRAPHIC** by visual inspection:
     - TEXT = element contains readable text (headlines, labels, prices, stats, CTAs)
     - GRAPHIC = element is an image, shape, background, product photo, logo mark, icon
   - For TEXT elements: read and record the text content (what does it say?)

5. **Present inventory to user:**
   > | # | Element | Type | Dimensions | Content |
   > |---|---------|------|------------|---------|
   > | 1 | background.png | GRAPHIC | 1080×1080 | — |
   > | 2 | headline.png | TEXT | 420×60 | "LOWEST PRICE EVER" |
   > | 3 | product-purifier.png | GRAPHIC | 380×450 | — |
   > | 4 | price-tag.png | TEXT | 200×45 | "₹4,999" |
   > | ... | | | | |

#### Part B: Animation Decisions

6. **Check `.agents/static-to-gif/animation-presets.md` for matching presets.** If a preset fits the current layout, suggest it by name.

7. **Ask the user what animations they want.** Present concrete suggestions:

   > **Matching preset found: "[Preset Name]"** (used in [project])
   > - [Brief description]
   >
   > **Suggested animations for your design:**
   > 1. **[Element/group]**: [animation type] — e.g. "Products: Slide in from left/right with fade + blur"
   > 2. **[Element/group]**: [animation type] — e.g. "Price: Count-up from 0 to ₹4,999"
   > 3. **[Element/group]**: [animation type] — e.g. "Headline: Typewriter reveal"
   > 4. **[Element/group]**: [animation type] — e.g. "Logo: Subtle fade in"
   >
   > **Options:**
   > - Speed: Fast (0.5s) / Medium (0.8s) / Slow (1.2s)?
   > - Stagger: Tight (0.1s gaps) / Relaxed (0.3s gaps)?
   > - Easing: Smooth (power2.out) / Snappy (back.out) / Bouncy (elastic)?
   > - Loop: Infinite / Once / Play + reverse?
   > - Total duration: 3s / 5s / 8s?

   **Do NOT proceed until the user answers.**

8. **Classify each element's render type** based on the user's animation choices:
   - **PNG** = element gets no animation, or simple animation only (fade, slide, scale, rotate). The Figma PNG is used as-is.
   - **HTML TEXT** = element gets text-based animation (countdown, count-up, typewriter, word-by-word, number counter, or any animation that manipulates text content). The PNG must be replaced with HTML text.

#### Part C: Font Identification & Sourcing (only for HTML TEXT elements)

**Skip this section entirely if no elements are classified as HTML TEXT.**

9. **For each HTML TEXT element, identify the font:**
   - Visually inspect the text element against common font characteristics:
     - Serif vs sans-serif vs display/decorative
     - Geometric vs humanist vs grotesque (for sans-serif)
     - Weight (thin/light/regular/medium/bold/black) — compare stroke thickness
     - Style (normal/italic/condensed/extended)
   - **Suggest a match to the user**: **"[element-name] looks like [Font Name] [Weight]. Is that correct?"**
     - If user confirms → proceed
     - If user says different font → use what they say
     - If user doesn't know → suggest 2-3 closest matches, let user pick

10. **Source each confirmed font:**
    - **Check Google Fonts CDN first** → if found, note the `<link>` URL for later
    - **If NOT on Google Fonts** → ask user: **"[Font Name] isn't on Google Fonts. Can you provide the .ttf or .woff2 file?"**
    - Copy any user-provided font files into `assets/static-gif/<project>/fonts/`
    - **System fonts do NOT work in headless Chrome** — the font MUST be embedded via `@font-face` or Google Fonts CDN
    - If user needs to find font files on their system:
      - **Windows:** `C:\Windows\Fonts\`
      - **Mac:** `/Library/Fonts/` or `~/Library/Fonts/`
      - **Linux:** `/usr/share/fonts/` or `~/.local/share/fonts/`

11. **Match text properties from each PNG** (these measurements will be used in Phase 2):
    - **Font size**: derive from PNG height (`font-size ≈ PNG_height / 1.2`)
    - **Font weight**: compare stroke thickness (300–900)
    - **Color**: sample pixel hex directly from PNG
    - **Letter spacing**: render text at derived size with `letter-spacing: 0`, compare width to PNG width, calculate: `letter-spacing = (PNG_width - rendered_width) / (character_count - 1)`
    - **Line height** (multi-line): measure baseline distance between lines
    - **Text transform**: uppercase / lowercase / none
    - **Additional**: text-shadow, stroke/outline, background highlight

12. **Report animation plan to user:**
    > **Animation Plan:**
    > | Element | Render Type | Animation | Font |
    > |---------|------------|-----------|------|
    > | background.png | PNG | None (static) | — |
    > | headline.png | HTML TEXT | Typewriter reveal | Bebas Neue Bold |
    > | product-purifier.png | PNG | Slide in from left | — |
    > | price-tag.png | HTML TEXT | Count-up 0→₹4,999 | Bebas Neue Bold |
    >
    > **Fonts sourced:** Bebas Neue Bold via Google Fonts ✓
    >
    > Proceeding to reconstruction.

### PHASE 2: Reconstruct — Non-Animated Composition

1. **Create a new HyperFrames composition** at `compositions/static-gif-<project>.html`

2. **Match the static dimensions** — read the static image to determine width × height.

3. **Aspect Ratio Conversion Rules**:

   **A. 1:1 → 9:16 Expansion** (when `InputAspectRatio` is `1:1` and output needs 9:16):
   - The output composition width and height **must** be set to 1080x1920.
   - **Keep original element sizes and positions**: Center the 1080x1080 design block vertically inside the 1080x1920 frame. Shift the vertical coordinate (`top`) of all original elements down by exactly `420px` (i.e. `top_new = top_original + 420px`). Do NOT scale, resize, or reposition them relative to each other.
   - **Expand the Background — ask user which method:**
     > **"How should I extend the background for 9:16?"**
     > 1. **Programmatic** (free, local) — tile/mirror/repeat for patterns, extend gradient for gradients, solid fill for solid colors
     > 2. **AI-generated** (Higgsfield) — generative outpainting for photographic/complex backgrounds
     
     - If user picks **Programmatic** or Higgsfield is not connected:
       - *Pattern/Generic background*: Repeat, duplicate, or tile the pattern vertically.
       - *Gradient*: Extend the gradient mathematically.
       - *Solid color*: Fill with the sampled color.
     - If user picks **AI-generated** AND Higgsfield MCP is connected:
       - Send the original background + a prompt describing the scene to Higgsfield
       - Request a 1080x1920 output that seamlessly extends the original
       - Verify the generated background visually with the user before proceeding

   **B. 9:16 → 1:1 Crop** (when `InputAspectRatio` is `9:16` and output needs 1:1):
   - The output composition width and height **must** be set to 1080x1080.
   - **Extract the center 1080x1080 region** (y=420 to y=1500).
   - **Shift all element positions UP by 420px**. Do NOT scale or resize.
   - **Check for clipped elements**: elements fully outside the crop zone → ask user to remove or reposition. Partially clipped → inform user and ask.
   - **Crop the background** to the center 1080x1080 region.

   **C. Native format** (no conversion needed):
   - Use static dimensions directly.

4. **NEVER change element sizes** — Figma exports are at NATIVE size. Width and height come directly from the PNG file dimensions.

5. **Place elements based on their render type from Phase 1:**

   **For PNG elements** (graphic elements + text with simple animation):
   - Use `<img>` tags pointing to `../assets/static-gif/<project>/elements/<filename>`
   - `position: absolute; left: Xpx; top: Ypx; width: Wpx; height: Hpx;`

   **For HTML TEXT elements** (text with text-based animation):
   - Use `<div>` elements with the font and properties matched in Phase 1:
     ```html
     <div id="element-name" class="clip"
          data-start="0" data-duration="5" data-track-index="N"
          style="position: absolute; left: Xpx; top: Ypx; width: Wpx;
                 font-family: 'FontName', sans-serif; font-size: XXpx;
                 font-weight: 700; color: #XXXXXX;
                 letter-spacing: X.XXem; line-height: X.X;
                 text-transform: uppercase;">
       TEXT CONTENT HERE
     </div>
     ```
   - Add Google Fonts `<link>` or `@font-face` in the `<head>`

   **Layer order** (z-index) must match the static — background at bottom, foreground on top.

6. **Set all elements as clips** with `class="clip"` and timing attributes:
   - `data-start="0"` `data-duration="<total-gif-duration>"` `data-track-index="<layer>"`

7. **DO NOT animate anything yet** — this phase is purely about pixel-perfect reconstruction.

### PHASE 3: Position & Verify — OVERLAY METHOD (PRIMARY TECHNIQUE)

**The overlay method IS the positioning technique. It is not a separate verification step — it is HOW you place elements. Non-negotiable.**

This phase verifies ALL elements — both PNG images and HTML text — against the static reference in a single pass. Because animation decisions and font sourcing happened in Phase 1, the composition already contains the correct element types. No conversion or replacement will happen after this point.

#### How it works:

1. **Set up the composition with reference as base:**
   - Add the reference static image as the BOTTOM layer at **FULL opacity** (z-index 0)
   - Source: `../assets/static-gif/<project>/static.png`
   - This stays in the composition throughout the entire placement process

2. **Add elements using SMART MATCHING ORDER (largest/most-opaque first):**
   - **Matching order is critical for speed.** Process elements in this exact sequence:
     1. **Full-bleed backgrounds** — largest area, highest confidence match. Locks immediately.
     2. **Large opaque shapes** — colored rectangles, panels, gradient blocks.
     3. **Product images / photos** — distinct pixel patterns, reliable template matching.
     4. **Icons, badges, logos** — smaller but still opaque. Search only REMAINING unmatched regions.
     5. **Text elements (PNG and HTML)** — match LAST, using edge-based matching.
   - Each confirmed element's bounding box is **excluded from the search region** for all subsequent elements.
   - Each element gets `opacity: 0.5`

3. **Use the right matching technique per element type:**
   - **Opaque PNG elements (backgrounds, products, shapes):** Standard OpenCV template matching (`cv2.matchTemplate` with `TM_CCOEFF_NORMED`).
   - **PNG text / transparent elements:** Edge-based matching — apply Canny edge detection to both element and reference region, match edge maps.
   - **HTML text elements:** Render the HTML text at current position, compare against the corresponding region in the static reference:
     - The HTML text must match the original text PNG in the static within 2px for width/height and 1px for position
     - If mismatched → adjust font-size, letter-spacing, line-height, or position and re-verify
     - **Do NOT proceed until HTML text is visually indistinguishable from the text in the static reference**
   - **Fallback:** If both standard and edge-based matching return low confidence (< 0.6), fall back to restricted-ROI pixel-difference search within remaining unmatched region only.
   - The overlay render is always the **final visual judge**.

4. **Render ONE frame after each element:**
   - Perfect alignment = element merges seamlessly with reference (no ghosting)
   - Misalignment = visible doubling/ghosting → adjust and re-render
   - Save overlay frames to `static-to-gif/projects/<project>/overlay-frames/`

5. **Once ALL elements are placed and verified:**
   - Show the full overlay to the user for approval
   - User may request fine adjustments — apply them
   - Once approved → remove reference layer, remove all `opacity: 0.5`, write clean composition
   - **Save verified positions** to `static-to-gif/projects/<project>/verified-positions.json` (element ID → {left, top, width, height, render_type: "png"|"html_text"})

**The overlay IS the process. Do not place elements without it. Do not verify without it. NEVER proceed to Phase 4 until the user explicitly approves.**

### PHASE 4: Animate

1. **Load the GSAP skill** for timeline-based animation
2. **Create animations** per user's choices from Phase 1 — every animation is custom-built using GSAP tweens:
   ```js
   window.__timelines = window.__timelines || {};
   const tl = gsap.timeline({ paused: true });
   
   // Example: fade-in + slide-up for a PNG element
   tl.fromTo("#product-image", 
     { opacity: 0, y: 30 }, 
     { opacity: 1, y: 0, duration: 0.6, ease: "power2.out" },
     0.2
   );
   
   // Example: count-up for an HTML TEXT element
   const counter = { val: 0 };
   tl.to(counter, {
     val: 4999,
     duration: 1.5,
     ease: "power1.out",
     onUpdate: () => {
       document.querySelector('#price-tag').textContent = '₹' + Math.round(counter.val).toLocaleString();
     }
   }, 0.4);
   
   window.__timelines["static-gif-<project>"] = tl;
   ```
3. **Register the timeline** on `window.__timelines`
4. **Set composition duration** to match the total animation length + hold time
5. **POST-ANIMATION POSITION VERIFICATION (mandatory):**
   - After all animation code is written but BEFORE opening Studio for preview:
   - Render frame 0 of the animated composition (the resting state before any animation plays)
   - Load `static-to-gif/projects/<project>/verified-positions.json` (saved in Phase 3)
   - Compare each element's current position at frame 0 against its verified position
   - **If any element has shifted by more than 1px** from its Phase 3 approved position:
     - Log which elements shifted and by how much
     - Auto-correct the displacement (adjust CSS left/top to compensate)
     - Re-render frame 0 and verify the fix
   - This catches accidental displacement caused by HTML restructuring (wrapping elements in animation containers, re-nesting for z-index layering, CSS inheritance changes, margin collapse, or transform origin offsets)
   - This check runs once, takes under a second, and ensures animation never displaces verified element positions

**After user approves ANY new animation → save it as a new preset in `animation-presets.md`.**

### PHASE 5: Preview & Refine

1. Run `npm run dev` to preview in browser
2. Run `npm run check` to lint the composition — fix any errors
3. Show the user the animated result in HyperFrames Studio
4. Iterate on timing/easing/speed if the user wants changes

⚠ **MUST get explicit "render it" command before Phase 6**

### PHASE 5B: Audio & SFX (OPTIONAL — only after animation is approved)

**This phase runs ONLY after the user has previewed and approved the animation in Phase 5.** The animation must be finalized before adding sound.

1. **Ask the user:**
   > **"The animation looks good. Do you want to add sound effects or audio?"**
   > - **Yes** → proceed with audio planning
   > - **No** → skip to Phase 6 (render silent)

   **Do NOT suggest or plan SFX earlier in the pipeline.** Audio comes after visual is locked.

2. **If yes — check for ElevenLabs MCP:**
   - If ElevenLabs MCP is connected → proceed with SFX generation
   - If ElevenLabs is NOT connected → inform user: **"ElevenLabs MCP is not connected. You can connect it in your Claude Code settings to generate SFX, or provide your own audio files."**
   - If user provides their own audio files → copy to `assets/static-gif/<project>/audio/` and skip to step 5

3. **Suggest SFX per animation type:**
   > **"Based on your animations, here are suggested sound effects:"**
   > | Element | Animation | Suggested SFX |
   > |---------|-----------|---------------|
   > | Products | Slide in from left | Soft whoosh/swoosh |
   > | Price | Count-up 0→₹4,999 | Tick/beep on each digit |
   > | Headline | Typewriter reveal | Keyboard typing sounds |
   > | Badge | Scale pop-in | Pop/click |
   > | Logo | Fade in | Subtle ambient rise |
   >
   > **"Want all of these, some, or different sounds? You can also add background music."**
   
   **User picks which SFX they want.** Do NOT generate anything the user didn’t approve.

4. **Generate approved SFX via ElevenLabs:**
   - For each approved SFX:
     ```
     ElevenLabs Sound Generation API:
     POST /v1/sound-generation
     {"text": "short soft whoosh sound effect for slide animation"}
     → saves to assets/static-gif/<project>/audio/<element>-sfx.mp3
     ```
   - For background music (if requested):
     ```
     ElevenLabs Music Generation API:
     {"text": "upbeat minimal electronic loop 5 seconds for product ad"}
     → saves to assets/static-gif/<project>/audio/bg-music.mp3
     ```
   - **Preview each generated sound with the user** — regenerate if not right

5. **Sync audio to the composition timeline:**
   - Add `<audio>` elements to the composition with `data-start` matching animation triggers:
     ```html
     <audio src="../assets/static-gif/<project>/audio/product-sfx.mp3"
            data-start="0.2" data-duration="1" data-track-index="100"></audio>
     <audio src="../assets/static-gif/<project>/audio/bg-music.mp3"
            data-start="0" data-duration="5" data-track-index="101" loop></audio>
     ```
   - Each SFX `data-start` must align with its animation’s start time from the GSAP timeline

6. **Preview with audio** — open Studio, play with sound. User approves or adjusts.

⚠ **After Phase 5B, the composition has both visual animation and audio. Phase 6 renders MP4 with embedded audio. GIF output is always silent (GIF format has no audio support).**

### PHASE 6: Render

1. **Only render when user explicitly says to** (no auto-render).
2. **Output Location Rule**: Create an `output/` subfolder inside the selected source folder (`<SourceFolder>/output/`) and render/save the final MP4/GIF deliverables **only** there.
3. **Overwriting vs. Versioning Rule**: If the user requests changes to an existing animation and tells you to re-render, **always ask the user** whether they want to **overwrite** the existing render or **create a new version** of it (e.g. `<project>-v2.gif`, `<project>-v3.gif`). Save the output file according to their choice.
4. Render command:
   ```bash
   mkdir -p "<SourceFolder>/output"
   npx hyperframes render --format gif --output "<SourceFolder>/output/<project>.gif"
   ```
5. If GIF format isn't directly supported, render to MP4 first then convert:
   ```bash
   npx hyperframes render --output "<SourceFolder>/output/<project>.mp4"
   ffmpeg -i "<SourceFolder>/output/<project>.mp4" -vf "fps=15,scale=<width>:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" "<SourceFolder>/output/<project>.gif"
   ```
6. **Post-Render Flow (uses saved preferences from `stms-preferences.json`):**

   **Read `stms-preferences.json`** and apply saved choices. Only ask questions for settings set to `"ask_each_time"`.

   **Step A — Aspect Ratio Conversion:**
   - If preference `aspect_ratio_conversion` is `"always_yes"` → auto-proceed with conversion (no question)
   - If preference is `"always_no"` → skip conversion (no question)
   - If preference is `"ask_each_time"` → ask in chat:
     - `InputAspectRatio` is `1:1` → **"Generate a 9:16 version?"** (Yes / No)
     - `InputAspectRatio` is `9:16` → **"Generate a 1:1 version?"** (Yes / No)
     - `InputAspectRatio` is `other` → skip
   - If converting: proceed to Phase 2 using the correct Aspect Ratio Conversion Rule, verify layout, render alternate version

   **Step B — Cleanup:**
   - If preference `cleanup_after_render` is `"always_yes"` → auto-cleanup (no question)
   - If preference is `"always_no"` → skip cleanup (no question)
   - If preference is `"ask_each_time"` → ask in chat: **"Clean up temporary debug files?"** (Yes / No)
   - If cleaning: delete temp overlay PNGs + debug images; keep helper scripts + positions.json + final outputs

   **Step C — Re-render versioning** (only on re-renders, not first render):
   - If preference `overwrite_behavior` is `"always_overwrite"` → overwrite silently
   - If preference is `"always_version"` → auto-create `<project>-v2.gif` etc.
   - If preference is `"ask_each_time"` → ask: **"Overwrite existing render or save as new version?"**

---

## Key Rules

- **ALWAYS detect platform** (Windows/Mac/Linux) at the start of every run — use platform-appropriate commands
- **ALWAYS check `stms-preferences.json`** on every run — if missing, run first-time setup. Never re-ask operational questions that have saved preferences.
- **ALWAYS ask for the folder path** — every single time `/GIF` is run
- **ALWAYS render to `<SourceFolder>/output/`** — final deliverables only
- **ALWAYS ask animation decisions in Phase 1** — before reconstruction
- **ALWAYS follow the Aspect Ratio Conversion Rules** — Rule A or Rule B. Never scale elements.
- **ALWAYS suggest animations with options** — presets first, then custom
- **NEVER change element sizes** — Figma exports at native dimensions. No scaling ever.
- **NEVER skip overlay verification** — Phase 3 is MANDATORY
- **NEVER guess positions** — overlay method only
- **NEVER animate before user approves** placement in Phase 3
- **NEVER guess fonts** — visually identify and confirm with user in Phase 1
- **NEVER run Windows commands on Mac** or vice versa — always use `Platform` variable
- **Source files are NEVER moved or deleted** — only copied
- **System fonts do NOT work** in headless Chrome — always embed fonts
- **All animations are custom** — build from scratch with GSAP
- **Clean previous overlay frames** at the start of each new run
- **Only render on explicit user command**
- **Use `mkdir -p`** for directory creation (cross-platform safe)

## Font Handling

**Fonts are identified and sourced in Phase 1** (Part C) during animation planning. This ensures fonts are ready before reconstruction begins in Phase 2.

**For HTML TEXT elements** (countdown, typewriter, word-by-word): Font is visually identified → confirmed with user → sourced from Google Fonts or user-provided file → properties matched from PNG measurements → used directly in Phase 2 reconstruction.

**For PNG elements** (text stays as image): No font handling needed. The Figma PNG is used as-is.

**General font sourcing** (when fonts are needed):
1. Check Google Fonts CDN first → use `<link>` tag
2. If not on Google Fonts → ask user for `.ttf`/`.woff2` file
3. Copy font file into `assets/static-gif/<project>/fonts/`
4. Embed via `@font-face` in the composition
5. System fonts are NOT available in headless Chrome — fonts must always be embedded

---

## Optional MCP Connectors

The core pipeline (Phases 0→1→2→3→4→5→6) works without any MCP connectors. These are optional enhancements that unlock AI-powered features when connected.

| Connector | What it enables | Where it’s used | Required? |
|---|---|---|---|
| **Higgsfield** | AI image generation, background outpainting, element extraction for complex cases | Phase 1 Mode B (cutout), Phase 2 (9:16 outpainting) | No — falls back to u2net + OpenCV + programmatic fill |
| **ElevenLabs** | SFX generation, background music, voiceover | Phase 5B (audio) | No — system renders silent GIF/MP4 without it, or user provides own audio |

**The system always asks before using any AI connector.** It checks if the connector is available, and if so, offers it as an option. If the user declines or the connector isn’t connected, the system uses local/programmatic alternatives.

**To connect in Claude Code:**
- Settings → MCP Servers → Add Higgsfield (`https://mcp.higgsfield.ai/mcp`)
- Settings → MCP Servers → Add ElevenLabs (install via `npx skills add elevenlabs`)

**To connect in other MCP-compatible clients:**
- Add the MCP server URLs to your client’s configuration
- Authenticate with your Higgsfield/ElevenLabs account
