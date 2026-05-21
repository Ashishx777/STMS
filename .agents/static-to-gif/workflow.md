# STMS — Static to Motion System Workflow

## OUTPUT STYLE (READ FIRST — affects every turn)

**Internal artifacts (code, JSON, commands, file paths):** keep dense and complete. The agent reads these.

**Status updates to user:** terse. One sentence. No preambles, no recaps, no "here's what I'm doing", no summaries of completed tool calls. Don't echo file contents. Don't narrate a command before running — just run it.

Examples (status):
- BAD: "I'll now read the static reference image and analyze its dimensions..."
- GOOD: *(run it)* "1:1, 1080×1080."
- BAD: "Great! I've successfully placed the background. The overlay shows perfect alignment..."
- GOOD: "Background locked. Next: headline."

**Questions to user:** USE THE STRUCTURED-QUESTION POPUP UI of your CLI:
- **Claude Code:** call the `AskUserQuestion` tool — it renders a popup with clickable options
- **Antigravity / Cursor / others:** use their equivalent interactive selection UI if available
- **No structured UI available:** fall back to numbered chat questions (last resort only)

Structured popups apply to: Q0 (permission mode), Q1–Q3 (first-run preferences), Phase 1B (animation choices B1–B5 + timing), Phase 1C (font picker), Phase 2 (1:1→9:16 expansion mode), Phase 3 (final overlay approval), Phase 5B (audio yes/no + SFX picker), Phase 6 (re-render versioning).

Even with structured UI, list ALL options clearly with relevant context. Make the choice obvious. Clarity over brevity HERE — the user needs to make a good decision.

Example (question):
- GOOD:
  > **Animation choice — pick one:**
  >
  > **Option A — Preset:** "Slide-In Fade Blur" (used in atovio-colour-picker). Products slide in from sides with fade + blur.
  > **Option B — Custom:** per-element control over speed, easing, stagger, loop, duration.
  >
  > Which?
- BAD: "preset or custom?"

---

## Overview

Static design + element PNGs → animated GIF/MP4 via HyperFrames.

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

### MANDATORY GATE — Run BEFORE any phase

**On every `/GIF` invocation, before doing ANYTHING ELSE, run this check sequence. No exceptions. Do not skip even if the user provided a path argument.**

```
1. Does `static-to-gif/stms-preferences.json` exist?
   NO  → run FIRST RUN SETUP (below) — ask Q0–Q3, save preferences, install missing prereqs
   YES → load preferences and proceed

2. Are required binaries (node, ffmpeg) on PATH?
   NO  → run the auto-install for the detected platform from CLAUDE.md / AGENTS.md Step 2
   YES → proceed

3. Are HyperFrames skills installed (`.agents/skills/hyperframes/SKILL.md` exists)?
   NO  → run `npx --yes skills add heygen-com/hyperframes`
   YES → proceed
```

**This gate is non-negotiable.** A new user typing `/GIF` for the first time MUST be walked through setup before Phase 0. Do NOT attempt the folder picker or any other Phase 0 work if preferences are missing — the user hasn't agreed to permission mode yet.

If the gate fails (e.g., user cancels Q0, prereq install fails), STOP and report the blocker. Do not silently fall back to Phase 0.

---

### FIRST RUN SETUP: One-Time Preferences

**On the very first `/GIF` run in a project, check for `static-to-gif/stms-preferences.json`.** If it doesn't exist, ask the user these questions ONCE, save their answers, and never ask again:

**Q0 — Permission mode (asked FIRST, before anything else) — ASK VIA STRUCTURED POPUP:**

*Header:* `Permission mode`
*Question:* `Allow all commands automatically, or ask before each one?`
*Multi-select:* `false`
*Options:*
- `Allow all (Recommended)` — *description: Broad permissions written to .claude/settings.local.json. No approval prompts during STMS runs.*
- `Ask each time` — *description: Your CLI will prompt before running any command not already in your global allow list.*

Based on the answer:
- If **"Allow all"** → write/merge into `.claude/settings.local.json`:
  ```json
  {
    "permissions": {
      "allow": [
        "Bash(*)",
        "Read(*)",
        "Write(*)",
        "Edit(*)",
        "Glob(*)",
        "Grep(*)",
        "mcp__*"
      ]
    }
  }
  ```
  Preserve any existing entries (merge, don't overwrite). Save `permission_mode: "allow_all"` to preferences.
- If **"Ask each time"** → leave `.claude/settings.local.json` untouched. Save `permission_mode: "ask_each_time"` to preferences. The user accepts that Claude Code will prompt per command.

**Q1–Q3 — Operational preferences (asked after Q0) — ASK VIA STRUCTURED POPUP, ONE QUESTION AT A TIME:**

**Q1 — Aspect ratio conversion:**
*Header:* `Alt aspect ratio`
*Question:* `After rendering, automatically generate the alternate aspect ratio (1:1 ↔ 9:16)?`
*Multi-select:* `false`
*Options:*
- `Always yes` — *description: Auto-generate the alternate version every time.*
- `Always no` — *description: Only render the input aspect ratio.*
- `Ask each time` — *description: Prompt me at the end of each run.*

**Q2 — Cleanup:**
*Header:* `Cleanup`
*Question:* `After rendering, automatically clean up temporary debug files (overlay frames, etc.)?`
*Multi-select:* `false`
*Options:*
- `Always yes` — *description: Auto-delete overlay-frames/, extracted/, helper PNGs. Keep verified-positions.json + final outputs.*
- `Always no` — *description: Keep all temp files for inspection.*
- `Ask each time` — *description: Prompt me at the end of each run.*

**Q3 — Re-render versioning:**
*Header:* `Re-render`
*Question:* `When you ask me to re-render an existing project, overwrite the previous file or save as a new version?`
*Multi-select:* `false`
*Options:*
- `Always overwrite` — *description: Replace the existing file in place.*
- `Always new version` — *description: Save as project-v2.gif, project-v3.gif, etc.*
- `Ask each time` — *description: Prompt me each re-render.*

Save to `static-to-gif/stms-preferences.json`:
```json
{
  "created": "2026-05-20",
  "platform": "windows",
  "permission_mode": "allow_all",
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

### EXECUTION PERMISSIONS — USER-CHOSEN AT Q0

**Permission behavior is decided by the user at Q0 of FIRST RUN SETUP.** The choice is stored in `static-to-gif/stms-preferences.json` as `permission_mode`.

**Mode `"allow_all"`** (recommended, default selection at Q0):
`.claude/settings.local.json` contains broad wildcards. The agent runs every command without prompting. NEVER re-ask, NEVER confirm before running — just execute. If a command fails, report the error and fix it.

Pre-approved command families under `allow_all`:
- `npm run dev` / `npm run check` / `npm run render`
- `npx hyperframes render` / `npx hyperframes lint` / `npx hyperframes inspect`
- `python` / `python3` (OpenCV background accelerator, PIL, any helper scripts)
- `ffmpeg` (MP4→GIF conversion, palette optimization)
- `mkdir -p` / `cp` / `rm` (file operations)
- Platform folder pickers (PowerShell on Windows, osascript on Mac)
- `node` / `npx` (any Node.js execution)
- File read/write/edit operations anywhere in the project
- Glob / Grep searches
- MCP tools (Higgsfield, ElevenLabs, etc.)

**Mode `"ask_each_time"`**:
The agent runs commands knowing Claude Code may prompt the user. The agent must NOT try to bypass prompts. If the user denies a command, do NOT retry it — ask the user how to proceed (different command, skip step, change preference).

**To change permission mode later:** user says "switch STMS to allow all" or "switch STMS to ask each time". Update `permission_mode` in `stms-preferences.json` AND adjust `.claude/settings.local.json` accordingly.

#### Platform-Specific Security Setup (one-time, handled on first run)

The agent must detect the platform and ensure the required OS-level permissions are in place. If any are missing, guide the user through granting them ONCE — then never mention it again.

**Windows:**
- **PowerShell Execution Policy:** new user accounts default to `Restricted` which blocks scripts. The agent must invoke PowerShell with `-ExecutionPolicy Bypass` for every PowerShell command (folder picker, install scripts, etc.) — see Phase 0 picker code. Do NOT permanently change the user's policy with `Set-ExecutionPolicy`.
- **PATH after winget install:** newly installed binaries are added to the system PATH registry, but the current shell session (and child Bash tool processes) may not see them until restart. After installing Node/FFmpeg/Python via winget:
  1. The setup script refreshes `$env:PATH` from the registry — works for PowerShell commands in the same session
  2. For agent Bash tool calls that still can't find the binary → tell user: **"Tools installed but not visible in this session. Restart Claude Code (or your CLI) and run `/GIF` again."**
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

     **Windows** (invoke via `powershell.exe -ExecutionPolicy Bypass -Command "..."` to bypass Restricted policy on fresh user accounts):
     ```powershell
     powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $d = New-Object System.Windows.Forms.OpenFileDialog; $d.Title = 'Select Folder (navigate inside the folder and click Open)'; $d.FileName = 'Select this folder'; $d.CheckFileExists = $false; $d.ValidateNames = $false; if ($d.ShowDialog() -eq 'OK') { Split-Path $d.FileName } else { Write-Output 'CANCELLED' }"
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

3. **If no `elements/` folder found — ASK VIA STRUCTURED POPUP:**

   *Header:* `Missing elements`
   *Question:* `I found a static image but no elements folder. How do you want to proceed?`
   *Multi-select:* `false`
   *Options:*
   - `I have elements in a different folder` — *description: Provide a different path; I'll use those PNGs.*
   - `Cut out elements from the static using AI` — *description: Enter Mode B — AI-assisted cutout from the static image.*
   - `I'll export from Figma and come back` — *description: Stop here. Re-run /GIF after you've added the elements folder.*

   Store the user's choice as `ElementMode`: `"exported"` (Mode A) or `"ai_cutout"` (Mode B).

   **Do NOT assume Mode B automatically.** Only enter AI cutout mode when the user explicitly chooses that option.

4. **Derive the project name from the source folder name** — no visual analysis, no brand detection. Just slugify the source folder's basename (lowercase, replace non-alphanumeric with dashes, collapse repeats, trim edges).

   **Windows (PowerShell):**
   ```powershell
   $ProjectName = (Split-Path -Leaf $SourceFolder).ToLower() -replace '[^a-z0-9]+','-' -replace '^-|-$',''
   ```

   **Mac/Linux (bash):**
   ```bash
   ProjectName=$(basename "$SourceFolder" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
   ```

   Examples:
   - `C:\Users\me\Desktop\Atovio Colour Picker\` → `atovio-colour-picker`
   - `~/projects/summer_sale/` → `summer-sale`
   - `D:\work\AdCampaign2026\` → `adcampaign2026`

   **Why:** the source folder name is already descriptive (the user named it for a reason), and there's no benefit to scanning the static for a "brand." Re-running on the same source folder reuses the same `assets/static-gif/<name>/` and `static-to-gif/projects/<name>/` working folders — supports iteration without duplicate folders piling up.

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

2. **Present the element map to user — STRUCTURED POPUP:**

   First, show the identified element list in chat (it can be long):
   > **"I identified these elements in the static:**
   > 1. Background — gradient with grid pattern
   > 2. Product image (purifier, center) — ~380×450px
   > 3. Headline text — "LOWEST PRICE EVER"
   > 4. Price badge — "₹4,999" bottom-right
   > 5. Logo — top-left corner
   > ..."

   Then ask via popup:

   *Header:* `Element list`
   *Question:* `Is this element list complete and correctly split?`
   *Multi-select:* `false`
   *Options:*
   - `Looks correct — proceed with cutout` — *description: All elements identified. Start AI cutout from foreground to background.*
   - `Missing elements (describe in chat)` — *description: I missed something. You'll tell me what to add.*
   - `Splits wrong (describe in chat)` — *description: Some elements should be merged or split differently. You'll tell me how.*

   **Do NOT proceed with cutout until the user picks "Looks correct".**

3. **Cut out each element one by one:**
   - Work from **foreground to background** (top layers first)
   - For each element:
     a. **Identify the element boundary** in the static (bounding box)
     b. **Use AI segmentation to isolate it:**
        - `npx hyperframes remove-background` (u2net) for objects with clear edges
        - If u2net produces poor results (complex edges, hair, transparency) AND Higgsfield MCP is connected → **ASK VIA STRUCTURED POPUP:**
          *Header:* `Cutout quality`
          *Question:* `The u2net cutout for "[element]" has rough edges. Use Higgsfield (AI) for a cleaner extraction?`
          *Multi-select:* `false`
          *Options:*
          - `Yes — use Higgsfield` — *description: AI-powered extraction. Better for hair, complex edges, semi-transparency.*
          - `No — refine with OpenCV` — *description: Keep u2net result, refine with contour detection.*
          - `Skip this element` — *description: Don't include this element. You'll add it manually later.*
        - If Higgsfield not connected or user declines → use OpenCV contour detection + manual refinement
     c. **Save the cutout** as `assets/static-gif/<project>/elements/<element-name>.png` at native dimensions
     d. **Generative fill the hole** left in the working background:
        - If background is solid/gradient/pattern → programmatic fill (PIL/numpy) — no AI needed
        - If background is photographic/complex AND Higgsfield MCP is connected → **ASK VIA STRUCTURED POPUP:**
          *Header:* `Background fill`
          *Question:* `The background behind "[element]" needs to be reconstructed. How should I fill the hole?`
          *Multi-select:* `false`
          *Options:*
          - `Use Higgsfield (AI generative fill)` — *description: AI generates a seamless fill. Best for photographic / complex backgrounds.*
          - `Use OpenCV inpaint (local)` — *description: Local algorithmic inpainting. Faster, works for simple backgrounds.*
          - `Leave the hole (I'll fix manually)` — *description: Save the cutout but skip the fill step.*
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

#### Part B: Animation Decisions — USE STRUCTURED POPUP QUESTIONS

**IMPORTANT — UI mechanism:** Use the agent's structured-question UI (Claude Code: `AskUserQuestion` tool; Antigravity / Cursor: their equivalent interactive question UI). Do NOT ask these as free-text chat prompts. The user clicks options, not types responses. This applies to questions B1–B5 below.

If your CLI has no structured-question UI, fall back to numbered chat questions — but only as a last resort. Structured UI is the default.

---

6. **Check `.agents/static-to-gif/animation-presets.md`** — find any presets that could fit this layout. Note them but do not auto-apply.

7. **Ask the structured-question sequence (5 questions, one popup each).** Wait for the answer before showing the next question.

   ---

   **Question B1 — Which elements to animate?**

   *Header:* `Animate which`
   *Question:* `Which elements should be animated?`
   *Multi-select:* `true`
   *Options:* the elements from the Phase 1 Part A inventory table, each listed individually. Plus:
   - `All elements` (selects everything in one click)
   - `Other (describe in chat)` — for when the user wants a group like "all text" or "just products"

   Example options (built from inventory):
   - All elements
   - background.png
   - headline.png
   - product-purifier.png
   - price-tag.png
   - logo.png
   - Other (describe in chat)

   ---

   **Question B2 — Animation type: preset or custom?**

   *Header:* `Animation type`
   *Question:* `How do you want to animate the selected elements?`
   *Multi-select:* `false`
   *Options:*
   - `Use a matching preset` — *description: Apply one of the saved presets from past projects (faster, proven).*
   - `Custom — describe what you want` — *description: Specify per-element animation in your own words (e.g., "word by word", "blur in one by one").*

   If there are NO matching presets in `animation-presets.md`, skip B2 and go directly to custom (B3 skipped, B4 asks the description).

   ---

   **Question B3 — Pick the preset** (only if B2 = `Use a matching preset`)

   *Header:* `Pick preset`
   *Question:* `Which preset?`
   *Multi-select:* `false`
   *Options:* every preset from `animation-presets.md` that could fit this layout, listed individually with one-line descriptions:
   - `Slide-In Fade Blur (Left/Right)` — *description: Products slide from sides with fade + blur. Used in atovio-colour-picker.*
   - `Counter Count-Up` — *description: Numbers animate from 0 to target. Used in atovio-wearable-purifier.*
   - `Delayed Highlight Pop` — *description: Static scene with delayed accent pops on key elements.*
   - (etc., from animation-presets.md)
   - `None of these fit — describe custom` — *description: Switch to custom description.*

   ---

   **Question B4 — Animation style picker** (only if B2 = `Custom — describe what you want`)

   *Header:* `Animation style`
   *Question:* `Pick the style for the selected elements (or describe in chat for "Other"):`
   *Multi-select:* `false`
   *Options:* concrete animation styles, each with a one-line description:
   - `Fade in — one by one` — *description: Each element fades in sequentially with stagger.*
   - `Blur in — one by one` — *description: Each element starts blurred and sharpens, sequentially.*
   - `Slide in from sides` — *description: Elements slide in from left/right based on position.*
   - `Slide in from bottom` — *description: Elements rise into place from below.*
   - `Scale pop (overshoot)` — *description: Elements pop in with back-ease overshoot.*
   - `Word by word` — *description: Text reveals word by word (HTML TEXT only).*
   - `Typewriter` — *description: Text appears character by character.*
   - `Count-up` — *description: Numeric text counts from 0 to target value.*
   - `Other (describe in chat)` — *description: Type a description of what you want.*

   ---

   **Question B5 — Leave non-selected elements static?**

   *Header:* `Non-animated`
   *Question:* `For elements you did NOT select to animate in B1 — what should they do?`
   *Multi-select:* `false`
   *Options:*
   - `Leave them fully static` — *description: They appear from frame 0 and never move. (Recommended)*
   - `Fade them in at start` — *description: Subtle fade-in (0.3s) at t=0 so they don't pop in jarringly.*
   - `Hide them entirely` — *description: Remove them from the composition.*

   ---

8. **Ask timing follow-ups (one popup):**

   *Header:* `Timing`
   *Question:* `Animation timing settings:`
   *Multi-select:* `true` — user picks one option per row
   *Options:* present as four grouped sub-options. If your structured UI doesn't support sub-grouping, ask four separate popups in sequence (Speed → Stagger → Easing → Duration):
   - **Speed:** Fast (0.5s) / Medium (0.8s) / Slow (1.2s)
   - **Stagger:** Tight (0.1s gaps) / Relaxed (0.3s gaps) / None (all at once)
   - **Easing:** Smooth (power2.out) / Snappy (back.out) / Bouncy (elastic)
   - **Total duration:** 3s / 5s / 8s
   - **Loop:** Infinite / Once / Play + reverse

9. **Classify each element's render type** based on the user's choices:
   - **PNG** = element gets no animation, or simple animation only (fade, slide, scale, rotate). The Figma PNG is used as-is.
   - **HTML TEXT** = element gets text-based animation (word-by-word, typewriter, count-up, or any animation that manipulates text content). The PNG must be replaced with HTML text — Part C font sourcing applies.

**Agent has NO preference between preset and custom.** Never recommend one over the other unless the user asks. Both paths produce identical-quality output.

#### Part C: Font Identification & Sourcing (only for HTML TEXT elements)

**Skip this section entirely if no elements are classified as HTML TEXT.**

10. **For each HTML TEXT element, identify the font — ASK VIA STRUCTURED POPUP:**

    First, visually inspect the text against common font characteristics (serif vs sans-serif, weight, style, geometric vs humanist) and form a top guess plus 2 alternates.

    Then ask via popup (one per HTML TEXT element):

    *Header:* `Font for [element]`
    *Question:* `Which font is "[element-name]" using?` (show the text content in the question, e.g., `Which font is the headline "LOWEST PRICE EVER" using?`)
    *Multi-select:* `false`
    *Options:* the top guess + 2 closest alternates + free-text fallback:
    - `[Top guess font + weight]` — *description: e.g., "Bebas Neue Bold. Used in past projects."*
    - `[Alt 1]` — *description: e.g., "Anton Regular. Similar geometric grotesque."*
    - `[Alt 2]` — *description: e.g., "Oswald Bold. Similar condensed sans-serif."*
    - `I don't know — pick the closest visually` — *description: Agent picks top guess, you can correct after preview.*
    - `Other (type in chat)` — *description: Specify font name in chat.*

11. **Source each confirmed font:**
    - **Check Google Fonts CDN first** → if found, note the `<link>` URL for later
    - **If NOT on Google Fonts** → ask user: **"[Font Name] isn't on Google Fonts. Can you provide the .ttf or .woff2 file?"**
    - Copy any user-provided font files into `assets/static-gif/<project>/fonts/`
    - **System fonts do NOT work in headless Chrome** — the font MUST be embedded via `@font-face` or Google Fonts CDN
    - If user needs to find font files on their system:
      - **Windows:** `C:\Windows\Fonts\`
      - **Mac:** `/Library/Fonts/` or `~/Library/Fonts/`
      - **Linux:** `/usr/share/fonts/` or `~/.local/share/fonts/`

12. **Match text properties from each PNG** (these measurements will be used in Phase 2):
    - **Font size**: derive from PNG height (`font-size ≈ PNG_height / 1.2`)
    - **Font weight**: compare stroke thickness (300–900)
    - **Color**: sample pixel hex directly from PNG
    - **Letter spacing**: render text at derived size with `letter-spacing: 0`, compare width to PNG width, calculate: `letter-spacing = (PNG_width - rendered_width) / (character_count - 1)`
    - **Line height** (multi-line): measure baseline distance between lines
    - **Text transform**: uppercase / lowercase / none
    - **Additional**: text-shadow, stroke/outline, background highlight

13. **Report animation plan to user:**
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
   - **Ask the user how the 9:16 should look — STRUCTURED POPUP** — the original 1:1 block sits centered (Y: 420–1500), leaving a 420px top region (Y: 0–420) and 420px bottom region (Y: 1500–1920) to fill:

     *Header:* `9:16 layout`
     *Question:* `Expanding your 1:1 design to 9:16 (1080×1920). Original design stays centered. How should I fill the top 420px and bottom 420px regions?`
     *Multi-select:* `false`
     *Options:*
     - `Extend the background only` — *description: Pattern repeats, gradient extends, or solid fill. Original design stays as the visual centerpiece with a clean frame.*
     - `Move existing elements into the new regions` — *description: e.g., logo moves up to top, CTA moves down to bottom. You tell me which elements go where in a follow-up.*
     - `Describe a layout for the new regions` — *description: Type a description in chat (e.g., "logo + brand name at top, disclaimer at bottom"). I'll build it.*
     - `AI-generate an extended background (Higgsfield)` — *description: Generative outpainting for complex/photographic backgrounds. Original elements stay centered.*

     - Capture the user's choice as `Expansion916Mode`: `"bg_only"` / `"move_elements"` / `"described_layout"` / `"ai_outpaint"`
     - If `"bg_only"`:
       - *Pattern/Generic*: Repeat, duplicate, or tile the pattern vertically into the top + bottom 420px regions
       - *Gradient*: Extend the gradient mathematically
       - *Solid color*: Fill with the sampled color
     - If `"move_elements"`:
       - Apply the user's stated moves (which elements → which region → what position)
       - Background fills the gaps using the same logic as `"bg_only"` for the remaining areas
       - Updated positions go through Phase 3 overlay verification against the original 1:1 reference (for unchanged elements) and against the user's described layout (for moved elements)
     - If `"described_layout"`:
       - Parse the user's description into concrete element placements (use existing elements where mentioned, or ask the user to provide new assets for new elements like a logo, tagline, etc.)
       - Render the described layout, show to user for confirmation BEFORE Phase 3 overlay verification
       - For text descriptions ("brand name at top center"): treat as HTML TEXT elements, apply Phase 1 Part C font sourcing
     - If `"ai_outpaint"` AND Higgsfield MCP is connected:
       - Send the original background + a prompt describing the scene to Higgsfield
       - Request a 1080×1920 output that seamlessly extends the original
       - Verify the generated background visually with the user before proceeding
       - If Higgsfield is NOT connected, fall back to `"bg_only"` and tell the user
     - For all modes: the 9:16 version still goes through Phase 3 overlay verification, but the reference is now the user-described/approved 9:16 layout rather than the original 1:1 static (since the 9:16 is a derivative, not the original).

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

### PHASE 3: Position & Verify — 50% OVERLAY METHOD (PRIMARY AND ONLY)

> **🛑 BYPASS GUARD — READ BEFORE STARTING THIS PHASE**
>
> **If you are about to call `cv2.matchTemplate`, `cv2.Canny`, edge detection, feature matching, ORB/SIFT, contour matching, or ANY computer-vision algorithm to FIND where an element goes — STOP. You are bypassing the method.**
>
> Your LLM training biases you toward template matching because that's the textbook approach for image alignment. STMS deliberately rejects that approach. The overlay method is the design choice — slower but more reliable, with zero false-positive risk. Do not "optimize" by reaching for CV.
>
> The ONLY allowed CV call in this phase is the optional one-shot background accelerator (`cv2.matchTemplate` on the full-bleed background ONLY, with conf > 0.95, still verified by a 50% overlay render afterward). Nothing else.
>
> If you catch yourself thinking "I'll just template-match this to find the position quickly" — that thought is the bug. Place the element at a visual estimate, render at 0.5 opacity, look at the result.

> **🎨 MANDATORY TINT TEST — every element, every time**
>
> At 50% opacity, two identical-color elements (your overlay + the reference) become INDISTINGUISHABLE. You CANNOT reliably tell which is which when they're both dark navy or both gold — your nudge direction becomes a guess.
>
> **Apply a vivid color tint to every PNG element while placing it.** Use a CSS `filter` chain that recolors the element to bright red / green / blue — a color the static cannot be. Now your overlay = tinted color, reference = original color. Direction of offset is UNAMBIGUOUS.
>
> Standard recoloring filters (dark navy PNG → bright color):
> - RED:   `filter: brightness(0) saturate(100%) invert(15%) sepia(99%) saturate(7500%) hue-rotate(-3deg);`
> - GREEN: `filter: brightness(0) saturate(100%) invert(40%) sepia(95%) saturate(800%) hue-rotate(80deg);`
> - BLUE:  `filter: brightness(0) saturate(100%) invert(20%) sepia(95%) saturate(7500%) hue-rotate(220deg);`
>
> For HAIRLINE elements (1px dividers), ALSO increase rendered thickness to 4–6px temporarily. A 1px static line peeks out from above or below your thick tint if misaligned.
>
> **For pixel-perfect verification, ALSO use `mix-blend-mode: difference`** on the overlay at full opacity (no filter): matching pixels become BLACK, any 1-px offset shows a visible colored ghost. Run this BEFORE locking.
>
> **Revert the filter / thickness / blend-mode to original** before declaring the element locked. The tint is a verification aid only, never the final render.

> **🚦 LOCKING PROTOCOL — never silently lock**
>
> "Locked" means the USER agreed the position is correct. Until the user says so, the element is still in flight even if YOU think it looks aligned.
>
> The agent's internal "this looks fine to me" judgment is the LEAST reliable signal in this loop, because:
> - Image renders shown back to the agent are downscaled and lose 1–3px precision.
> - Identical-color overlays at 50% disguise small offsets entirely.
> - The agent has no spatial intuition for whether a position "feels right" — only the user does.
>
> So the order is: visual estimate → render → tint test → difference test → present to user in Studio → **user approves explicitly** → locked. Skip any step and you are guessing.

**The overlay method IS the positioning technique. Place each element at 50% opacity over the full-opacity reference, render one frame, look for ghosting, adjust pixel positions, re-render. Repeat until ghosting is gone. No CV matching for placement. No edge detection. No template matching as a search method. Just place → render → look → adjust.**

#### Why overlay-only:

- Every miss is obviously a miss — no silent CV false positives that lie with high confidence
- Works identically for every element type: opaque PNGs, transparent PNGs, text PNGs, HTML text, logos, gradients, anything
- The LLM reads the rendered overlay frame and judges visually — exactly what a human designer would do
- No Python/OpenCV dependency for placement (kept optional as a one-shot accelerator for the background only)

#### Setup (once per project):

1. **Clear previous overlay frames:**
   - Delete contents of `static-to-gif/projects/<project>/overlay-frames/` if it exists
   - Recreate the folder fresh

2. **Add the reference static as the base layer:**
   - BOTTOM layer, z-index 0, **FULL opacity** (1.0)
   - Source: `../assets/static-gif/<project>/static.png`
   - `position: absolute; left: 0; top: 0; width: <composition-width>px; height: <composition-height>px;`
   - Stays in the composition for the entire phase, removed only on final user approval

#### Placement order (largest/most-opaque first):

Process elements in this exact sequence — each locked element's region is visually excluded when judging subsequent elements:

1. **Full-bleed background** — covers the whole frame, locks first
2. **Large opaque shapes** — colored panels, gradient blocks, decorative rectangles
3. **Product images / photos**
4. **Icons, badges, logos**
5. **Text elements (PNG and HTML)** — LAST

#### Per-element loop:

**Two distinct viewing roles in this loop — keep them separate:**

- **Agent inspects rendered PNG** (each `npx hyperframes render --frame 0` output) by READING the file with Read tool to judge ghosting itself. The user does NOT see these intermediate renders. The agent is the judge. Per-element iteration is silent on the user side — they only see terse status updates like "Element 3 ghosting, nudging -8px Y."
- **User views composition** at the FINAL APPROVAL GATE (step 7 below) via `npm run dev` opening HyperFrames Studio in their browser. NEVER show per-element renders to the user. NEVER use the IDE preview panel for this.

If the user can see the composition in a sidebar/panel inside the IDE (Claude Code Launch panel, Cursor preview, VS Code Live Server, etc.), the agent is doing it wrong — that preview lacks the HyperFrames Studio timeline.

For each element in the order above:

1. **Estimate the initial position visually** from the static reference:
   - Identify where the element sits in the static (read the image)
   - Estimate the top-left corner in pixels
   - Width and height come from the PNG file dimensions (never resize)
   - For HTML TEXT: width = rendered width at the font properties matched in Phase 1

2. **Insert the element** into the composition at the estimated position with `opacity: 0.5`:
   ```html
   <!-- PNG element -->
   <img src="../assets/static-gif/<project>/elements/<file>.png"
        style="position: absolute; left: <X>px; top: <Y>px;
               width: <W>px; height: <H>px;
               opacity: 0.5; z-index: <N>;">

   <!-- HTML TEXT element -->
   <div style="position: absolute; left: <X>px; top: <Y>px;
               width: <W>px; opacity: 0.5; z-index: <N>;
               font-family: '<Font>'; font-size: <S>px; font-weight: <W>;
               color: #<HEX>; letter-spacing: <LS>em;">
     <TEXT CONTENT>
   </div>
   ```

3. **Render a single frame** at frame 0:
   ```bash
   npx hyperframes render --frame 0 --output "static-to-gif/projects/<project>/overlay-frames/<element>-attempt-<N>.png"
   ```

4. **Read the rendered frame and judge:**
   - **Locked:** Element merges into the reference cleanly. The reference's version of that element is no longer visible separately — there is no doubling, no halo, no shifted edges. → record final position, move to next element.
   - **Ghosting visible:** Two copies of the element are visible — the full-opacity reference version AND the 50%-opacity overlay version, shifted by some amount.
     - Measure the shift: which way is the overlay off, and by how many pixels? (compare a known edge — top of headline, left of product, etc.)
     - Adjust `left` and/or `top` by that exact pixel delta
     - Re-render as `<element>-attempt-<N+1>.png`
   - **Wrong size or wrong file:** Do NOT resize the element. Figma exports are at native dimensions. If size visibly disagrees with the static, the element file or the wrong file was picked — stop and ask the user.
   - **Element doesn't appear in the static:** Stop and ask user — element may be unused or in the wrong folder.

5. **Iterate until ghosting is gone — perfection is mandatory, not optional.** The 8-attempt limit is a sanity check, NOT a quality cap. If ghosting persists after 8 attempts, that's a signal of a deeper issue (wrong element file, font mismatch on HTML text, transparent edge that needs special handling) — STOP and ask the user. Do NOT "accept" misalignment and move on. There is no "close enough" mode in STMS.

6. **Lock the element.** Record its final `{left, top, width, height, render_type}` and move to the next element.

#### Optional CV accelerator (background ONLY):

The full-bleed background is the one case where OpenCV template matching is reliable enough to skip visual estimation. If Python + OpenCV are installed AND the element being placed is the background:

```python
import cv2
ref = cv2.imread("static.png")
elem = cv2.imread("elements/background.png")
res = cv2.matchTemplate(ref, elem, cv2.TM_CCOEFF_NORMED)
_, conf, _, loc = cv2.minMaxLoc(res)
if conf > 0.95:
    left, top = loc  # use as initial position, then still verify with 50% overlay render
```

Then proceed to step 2 of the per-element loop above (insert at `opacity: 0.5`, render, judge). If ghosting appears, discard the CV result and switch to visual nudging.

**Do NOT use CV for any other element type.** Text, products, logos, icons, shapes — all go through pure visual overlay placement. The CV accelerator exists solely to skip a few iterations on the background.

#### Final approval gate:

7. **Once ALL elements are placed and locked:**
   - Render a final composite overlay frame with every element still at `opacity: 0.5` over the full-opacity reference
   - Save as `static-to-gif/projects/<project>/overlay-frames/final-overlay.png`
   - **Start HyperFrames Studio for the user.** Run `npm run dev` as a background process — this serves the composition (reference at full opacity + all elements at 0.5) on a local URL and opens it in the user's default browser. Studio hot-reloads, so any subsequent adjustments appear instantly without restart.
   - **NEVER preview the overlay in any other way.** Specifically:
     - Do NOT open the PNG with an OS image viewer (`start`, `open`, `xdg-open`, Preview.app, Photos, etc.)
     - Do NOT embed or attempt to display the image inline in the Claude chat
     - Do NOT use any CLI image viewer (`viu`, `chafa`, `kitty +kitten icat`, terminal-image, etc.)
     - Do NOT describe the image to the user in lieu of showing it
     - **Do NOT use Claude Code's built-in "Launch preview panel" or any IDE-embedded HTML preview** — these render the HTML statically without HyperFrames Studio's timeline, scrubber, or animation playback. They are NOT acceptable previews for STMS work even though they look superficially similar to a browser tab.
     - Do NOT use VS Code Live Server, Cursor's preview, Antigravity's preview panel, or any similar built-in HTML preview tool.
     - The ONLY user-facing preview mechanism in STMS is `npm run dev` (HyperFrames Studio in the user's default browser — recognizable by its timeline UI at the bottom of the page). If you see the composition without a timeline, you're previewing it wrong.
   - Once the dev server is up, tell the user: **"HyperFrames Studio is open in your browser showing the overlay — reference at full opacity, every element at 50%. Does everything look aligned?"**
   - If `npm run dev` printed a URL but the browser didn't auto-open, include the URL in the message so the user can click it.
   - User may request fine adjustments → apply, save → Studio hot-reloads → re-confirm in the same browser session

8. **On explicit user approval:**
   - Remove the reference layer from the composition
   - Remove `opacity: 0.5` from all elements (set to 1.0 or remove the property)
   - Write the clean composition file
   - Save verified positions to `static-to-gif/projects/<project>/verified-positions.json`:
     ```json
     {
       "elements": [
         {"id": "background", "left": 0, "top": 0, "width": 1080, "height": 1080, "render_type": "png"},
         {"id": "headline", "left": 84, "top": 120, "width": 420, "height": 60, "render_type": "html_text"}
       ]
     }
     ```

**The 50% overlay IS the process. No CV matching for placement (except optional background accelerator). No proceeding to Phase 4 until the user explicitly approves the final overlay.**

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
5. **🚨 GSAP TIMELINE DURATION GOTCHA — MANDATORY EXTENSION TO MATCH `data-duration`:**

   When the renderer captures frames past the GSAP timeline's natural end, sub-composition clips can drop out and produce **blank/white frames** even though every clip has `data-duration` set to the full composition length. This happens because the sub-composition root inherits the GSAP timeline's `totalDuration()` as its effective lifetime when no explicit duration is on the inner `<div data-composition-id="...">` root.

   **Symptom:** The MP4 renders correctly for the first ~1–2 seconds (during the animation), then the screen goes pure white for the remaining hold period.

   **Cause:** A GSAP timeline with tweens that all end by t=1.0s reports `tl.totalDuration() === 1.0`. The renderer seeks past 1.0s, GSAP clamps, the sub-composition clip is treated as ended, and the rendered frame is empty (composition background color, typically white).

   **Fix:** Extend the GSAP timeline to the full composition duration with a no-op `tl.set()` at the end. This anchors `tl.totalDuration()` to the composition length without animating anything:

   ```js
   const tl = gsap.timeline({ paused: true });
   // ... all your real tweens ...
   tl.fromTo('#last-element', { opacity: 0 }, { opacity: 1, duration: 0.5 }, 1.5);

   // MANDATORY: anchor timeline to composition duration so final hold renders
   tl.set('#last-element', { opacity: 1 }, COMPOSITION_DURATION_SECONDS);

   window.__timelines["<composition-id>"] = tl;
   ```

   The `tl.set()` at position `COMPOSITION_DURATION_SECONDS` (e.g. `5` for a 5-second composition) is a zero-duration action that extends `tl.totalDuration()` to that value. Pick any real element selector — the operation is a no-op (setting opacity:1 on something already at opacity:1).

   **Verify the fix:** After rendering, extract a frame at t = `COMPOSITION_DURATION - 0.5s` using `ffmpeg -ss <t> -vframes 1 ...`. A blank ~6 KB output means the gotcha is still active; a full-image >100 KB output means the timeline is correctly extended.

   This is a NON-NEGOTIABLE final step on every animated composition. Do NOT skip it just because the lint passes — `npm run check` does not catch this; only an actual MP4 render reveals it.

6. **POST-ANIMATION POSITION VERIFICATION (mandatory):**
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

1. **Ask the user — STRUCTURED POPUP:**

   *Header:* `Sound?`
   *Question:* `The animation looks good. Add sound effects or audio?`
   *Multi-select:* `false`
   *Options:*
   - `Yes — add SFX` — *description: I'll suggest SFX matched to each animation (whoosh, pop, typing). Requires ElevenLabs MCP or your own audio files.*
   - `No — render silent` — *description: Skip to Phase 6, no audio.*

   **Do NOT suggest or plan SFX earlier in the pipeline.** Audio comes after visual is locked.

2. **If yes — check for ElevenLabs MCP:**
   - If ElevenLabs MCP is connected → proceed with SFX generation
   - If ElevenLabs is NOT connected → inform user: **"ElevenLabs MCP is not connected. You can connect it in your Claude Code settings to generate SFX, or provide your own audio files."**
   - If user provides their own audio files → copy to `assets/static-gif/<project>/audio/` and skip to step 5

3. **Suggest SFX per animation type — STRUCTURED POPUP:**

   First, show the suggestion table in chat:
   > **"Based on your animations, here are suggested sound effects:**
   > | Element | Animation | Suggested SFX |
   > |---------|-----------|---------------|
   > | Products | Slide in from left | Soft whoosh/swoosh |
   > | Price | Count-up 0→₹4,999 | Tick/beep on each digit |
   > | Headline | Typewriter reveal | Keyboard typing sounds |
   > | Badge | Scale pop-in | Pop/click |
   > | Logo | Fade in | Subtle ambient rise |"

   Then ask via popup (multi-select so user can pick any combination):

   *Header:* `Pick SFX`
   *Question:* `Which sounds do you want? Pick any combination.`
   *Multi-select:* `true`
   *Options:* one row per suggested SFX, plus background music + none:
   - `Products: whoosh on slide` — *description: Soft whoosh synced to each slide-in.*
   - `Price: tick on count-up` — *description: Tick/beep on each digit change.*
   - `Headline: typewriter` — *description: Keyboard typing sound during reveal.*
   - `Badge: pop` — *description: Pop/click on scale-in.*
   - `Logo: ambient rise` — *description: Subtle ambient sweep on fade-in.*
   - `Background music` — *description: Looping music bed under the SFX.*
   - `None of these — describe in chat` — *description: Type your own SFX descriptions.*

   **Do NOT generate anything the user didn't pick.**

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
- **NEVER trade quality for speed.** Perfect pixel placement, perfect font matching, perfect render. The user explicitly accepts longer runtimes for perfection. If a step would compromise quality (skip iterations, accept "close enough" alignment, substitute a font that's "good enough"), STOP and ask the user — never silently downgrade.
- **NEVER recommend preset over custom (or vice versa)** in Phase 1B unless the user asks for a recommendation. Present both options neutrally and let the user choose.
- **NEVER preview to the user via Claude, CLI tools, or OS image viewers** — the only user-facing preview mechanism is `npm run dev` (HyperFrames Studio in the browser). This applies to every phase, but is most critical at the Phase 3 alignment-approval gate: start the dev server BEFORE asking "does everything look aligned?"
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
