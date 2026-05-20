# STMS — Static to Motion System

## FIRST RUN AUTO-SETUP

**If this is a fresh clone (no `node_modules/`, no `.hyperframes/`, no `stms-preferences.json`), run the full setup automatically. Do NOT ask — just do it.**

### Auto-Setup Sequence:

```
Step 1: Detect platform
Step 2: Check prerequisites → install what's missing
Step 3: Install HyperFrames skills
Step 4: Report status → ready
```

### Step 1: Detect Platform

```bash
# Node.js method (works everywhere)
node -e "console.log(process.platform)"
# Returns: "win32" (Windows), "darwin" (Mac), "linux" (Linux)
```

Store as `Platform` variable for all subsequent commands.

### Step 2: Check Prerequisites

Check each tool. If missing, install it automatically (Mac/Linux) or tell the user exactly what to do (Windows).

**Node.js:**
```bash
node --version
```
- If found → continue
- If missing → STOP. Tell user: "Node.js is required. Download from https://nodejs.org (LTS version). Install it, then run me again."
- Node.js cannot be auto-installed — it requires a system installer.

**FFmpeg:**
```bash
ffmpeg -version
```
- If found → continue
- If missing on **Mac**: `brew install ffmpeg` (auto-install)
- If missing on **Linux**: `sudo apt install ffmpeg -y` (auto-install, this is the one exception for sudo)
- If missing on **Windows**: Tell user: "FFmpeg is required for GIF conversion. Download from https://www.gyan.dev/ffmpeg/builds/ → extract to C:\ffmpeg → add C:\ffmpeg\bin to your system PATH. Then run me again."

**Python 3 (needed for OpenCV overlay verification):**
```bash
python3 --version || python --version
```
- If found → continue
- If missing on **Mac**: `brew install python`
- If missing on **Linux**: `sudo apt install python3 python3-pip -y`
- If missing on **Windows**: Tell user: "Python 3 is required. Download from https://python.org → install with 'Add to PATH' checked."

**OpenCV + NumPy (Python packages for Phase 3 matching):**
```bash
python3 -c "import cv2; import numpy; print('OK')" || python -c "import cv2; import numpy; print('OK')"
```
- If found → continue
- If missing: `pip3 install opencv-python numpy --break-system-packages` (or `pip install` on Windows)

### Step 3: Install HyperFrames Skills

```bash
npx --yes skills add heygen-com/hyperframes
```

This installs all HyperFrames skills (gsap, hyperframes, hyperframes-cli, hyperframes-media, etc.) into `.agents/skills/`.

If skills are already installed (`.agents/skills/hyperframes/SKILL.md` exists), skip this step.

### Step 4: Report Status

After setup completes, report:

```
✅ STMS Setup Complete
─────────────────────
Platform:     [Windows/Mac/Linux]
Node.js:      [version] ✓
FFmpeg:       [version] ✓
Python:       [version] ✓
OpenCV:       [version] ✓
HyperFrames:  Skills installed ✓

Type /GIF to start your first project.
```

If any prerequisite failed and couldn't be auto-installed, list it clearly:

```
⚠ STMS Setup Incomplete
───────────────────────
❌ FFmpeg not found — install manually: https://www.gyan.dev/ffmpeg/builds/
✅ Everything else is ready

Install FFmpeg, then type /GIF to start.
```

---

## Execution Permissions — PRE-GRANTED (DO NOT ASK)

**All code execution permissions are pre-granted via `.claude/settings.local.json`.** This is a blanket one-time grant. The agent must NEVER ask the user for permission to run bash commands, npm scripts, python, ffmpeg, node, file operations, or any other system command. Just execute. If a command fails, fix it and retry — don't ask if you're allowed to.

**Security:** The system auto-detects the platform (Windows/Mac/Linux) and uses the correct commands. On Mac, the first run may trigger one-time OS security prompts (folder access, osascript) — the user grants once and it persists. The system NEVER requires admin/root/sudo for normal operation (except the one-time FFmpeg/Python install on Linux). If a command asks for elevated access outside of initial setup, it is a bug — report it, don't grant it.

---

## Skills — AUTO-LOAD BEFORE ANY COMPOSITION WORK

**Always invoke the relevant skill before writing or modifying compositions.** Skills encode framework-specific patterns (e.g., `window.__timelines` registration, `data-*` attribute semantics, shader-compatible CSS rules) that are NOT in generic web docs. Skipping them produces broken compositions.

If skills are not installed, run: `npx skills add heygen-com/hyperframes`

| Skill | When to use |
| --- | --- |
| **hyperframes** | Creating or editing HTML compositions, captions, TTS, audio-reactive animation, marker highlights |
| **hyperframes-cli** | Dev-loop CLI: init, lint, inspect, preview, render, doctor |
| **hyperframes-media** | Asset preprocessing: tts (Kokoro), transcribe (Whisper), remove-background (u2net) |
| **hyperframes-registry** | Installing blocks and components via `hyperframes add` |
| **website-to-hyperframes** | Capturing a URL and turning it into a video — full website-to-video pipeline |
| **tailwind** | Tailwind v4 browser-runtime styles for projects created with `hyperframes init --tailwind` |
| **gsap** | GSAP animations for HyperFrames — tweens, timelines, easing, performance |
| **animejs** | Anime.js animations registered on `window.__hfAnime` |
| **css-animations** | CSS keyframes that HyperFrames can pause and seek |
| **lottie** | `lottie-web` and dotLottie players registered on `window.__hfLottie` |
| **three** | Three.js scenes rendered from HyperFrames `hf-seek` events |
| **waapi** | Web Animations API motion driven through `document.getAnimations()` |

---

## Slash Commands — EXECUTE IMMEDIATELY ON USE

When a user types any of these commands, **do NOT ask what they mean or explain how they work**. Load the referenced workflow file and start executing immediately.

### `/GIF`

**STMS (Static to Motion System).** Converts static designs + Figma-exported elements into animated motion (GIF/MP4).

**Syntax:**
```
/GIF                              → Opens a folder picker dialog to select the folder for static and element files
/GIF <path>                       → Opens a confirmation prompt for the specified path
```

**Key Execution Rules:**
- **Always Ask for Folder Path**: The Agent must prompt the user or open the folder browser dialog on every run to select or confirm the source folder path.
- **Save Output Locally**: The final rendered MP4 or GIF must be written inside an `output/` subfolder directly within the user's selected source folder (i.e. `<SourceFolder>/output/`).

**On trigger:**
1. Read `.agents/static-to-gif/workflow.md` — follow it phase by phase
2. Read `.agents/static-to-gif/SYSTEM.md` — understand the system constraints
3. Read `.agents/static-to-gif/animation-presets.md` — check for reusable presets
4. Start at **Phase 0** (Smart File Discovery) and work through to completion

---

## Standard Commands

```bash
npm run dev          # preview in browser (studio editor)
npm run check        # lint + validate + inspect
npm run render       # render to MP4
npm run publish      # publish and get a shareable link
npx hyperframes docs <topic>  # reference docs in terminal
```

---

## Project Structure

- `index.html` — main composition (root timeline)
- `compositions/` — sub-compositions referenced via `data-composition-src`
- `assets/` — media files (video, audio, images, fonts, SFX)
- `.agents/` — workflow definitions, skills, STMS pipeline
- `.claude/` — skill definitions, permissions
- `static-to-gif/` — imports, projects, and output for the /GIF pipeline
- `renders/` — rendered MP4 output files

## Key Rules

1. Every timed element needs `data-start`, `data-duration`, and `data-track-index`
2. Visible timed elements **must** have `class="clip"`
3. GSAP timelines must be paused and registered on `window.__timelines`
4. Only deterministic logic — no `Date.now()`, no `Math.random()`, no network fetches
5. After creating or editing any composition, **always** run `npm run check`

## Documentation

Full docs: https://hyperframes.heygen.com/introduction
