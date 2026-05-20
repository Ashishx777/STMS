# STMS — Static to Motion System

## OUTPUT STYLE (READ FIRST)

**Internal artifacts (code, JSON, commands, file paths):** dense and complete.

**Status updates to user:** terse. One sentence. No preambles, no recaps, no narrating commands before running — just run them. Don't echo file contents.

Examples (status):
- BAD: "I'll now check if Node.js is installed by running `node --version`..."
- GOOD: *(run it)* "Node 25.7 ✓"
- BAD: "Great! Setup is complete. All prerequisites are installed..."
- GOOD: "Setup done. /GIF to start."

**Questions to user:** USE the `AskUserQuestion` tool — it renders a popup with clickable options the user can select. Do NOT ask multi-choice questions as free-text chat prompts. Free-text chat is only for clarifications and follow-ups. List all options clearly, include relevant context, make the choice obvious. Clarity over brevity HERE.

Example (question):
- GOOD:
  > **Permission mode — pick one:**
  >
  > **1. Allow all** (recommended) — no future approval prompts during STMS runs.
  > **2. Ask each time** — Claude Code prompts before commands not pre-allowed.
  >
  > Which?
- BAD: "allow all or ask?"

---

## FIRST RUN AUTO-SETUP

**Trigger condition:** the file `static-to-gif/stms-preferences.json` is MISSING. This is the canonical signal of a fresh clone — `node_modules/` and `.hyperframes/` are gitignored and unreliable indicators.

**When the user types `/GIF` (or any STMS command) and preferences are missing → run the full setup BEFORE attempting Phase 0.** Do NOT ask "should I run setup?" — just run it. The first thing the user sees is Q0 (permission mode).

**If the user opens Claude Code without typing anything yet:** wait for them to type a command. Do NOT pre-emptively run setup just because they opened the project. Setup runs on first STMS command.

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

### Step 2: Check Prerequisites — AUTO-INSTALL EVERYTHING

The agent installs every missing tool automatically using the platform's package manager. **The user should never have to manually download installers.** A single UAC / sudo prompt may appear during install — that's the only manual interaction permitted.

Announce what's about to happen before installing:
> "Checking prerequisites. I'll auto-install anything missing (Node.js, FFmpeg, Python, OpenCV) using your system package manager. You may see one permission prompt — click yes."

Then run the auto-install for the detected platform.

---

#### Windows (winget)

`winget` ships with Windows 10 1809+ and Windows 11 by default. Use it for everything.

```powershell
# Helper: refresh PATH so newly installed binaries are findable in this session
$RefreshPath = {
  $env:PATH = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
              [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Node.js LTS (REQUIRED)
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  winget install --id OpenJS.NodeJS.LTS --silent --accept-source-agreements --accept-package-agreements
  & $RefreshPath
}

# FFmpeg (REQUIRED)
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  winget install --id Gyan.FFmpeg --silent --accept-source-agreements --accept-package-agreements
  & $RefreshPath
}

# Python 3 (OPTIONAL — for background accelerator)
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  winget install --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
  & $RefreshPath
}

# OpenCV + NumPy (OPTIONAL — for background accelerator)
if (Get-Command python -ErrorAction SilentlyContinue) {
  python -c "import cv2, numpy" 2>$null
  if ($LASTEXITCODE -ne 0) {
    python -m pip install --user opencv-python numpy
  }
}
```

**If `winget` itself is missing** (very rare on supported Windows): tell the user to install "App Installer" from the Microsoft Store (`ms-windows-store://pdp/?productid=9NBLGGH4NNS1`), then retry. This is the ONLY case where the user must do something manual on Windows.

#### Mac (brew)

```bash
# Bootstrap Homebrew if missing
if ! command -v brew &> /dev/null; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Add brew to PATH for this session
  eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"
fi

# Required + optional in one pass
command -v node     &> /dev/null || brew install node
command -v ffmpeg   &> /dev/null || brew install ffmpeg
command -v python3  &> /dev/null || brew install python

# OpenCV + NumPy (optional)
python3 -c "import cv2, numpy" 2>/dev/null || python3 -m pip install --user opencv-python numpy
```

#### Linux (apt — Debian/Ubuntu; adapt for other distros)

```bash
# Update package index once
sudo apt update -qq

command -v node    &> /dev/null || sudo apt install -y nodejs npm
command -v ffmpeg  &> /dev/null || sudo apt install -y ffmpeg
command -v python3 &> /dev/null || sudo apt install -y python3 python3-pip

# OpenCV + NumPy (optional)
python3 -c "import cv2, numpy" 2>/dev/null || pip3 install --user opencv-python numpy
```

For non-Debian distros: substitute `dnf`/`pacman`/`zypper` and tell the user which command was run.

---

#### After auto-install, verify everything

Re-run the version checks:
```bash
node --version          # required
ffmpeg -version         # required
python --version || python3 --version   # optional
python -c "import cv2, numpy"           # optional
```

**REQUIRED tools that still fail** (Node.js or FFmpeg) → STOP, show the user the exact error from the install command, and ask whether they want to retry or install manually.

**OPTIONAL tools that fail** (Python, OpenCV) → continue setup. Phase 3 falls back to pure visual overlay placement. Note in the status report that the optional background accelerator is unavailable.

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
Node.js:      [version] ✓ (required)
FFmpeg:       [version] ✓ (required)
Python:       [version] ✓ (optional — background accelerator)
OpenCV:       [version] ✓ (optional — background accelerator)
HyperFrames:  Skills installed ✓

Type /GIF to start your first project.
```

If a REQUIRED prerequisite (Node.js or FFmpeg) is missing, block setup and list it:

```
⚠ STMS Setup Incomplete
───────────────────────
❌ FFmpeg not found — install manually: https://www.gyan.dev/ffmpeg/builds/
✅ Everything else is ready

Install FFmpeg, then type /GIF to start.
```

Missing OPTIONAL tools (Python/OpenCV) do not block — just note them:

```
✅ STMS Setup Complete (with optional accelerator skipped)
Python/OpenCV not installed — Phase 3 will use pure visual overlay
placement for every element including the background. No functional loss.
```

---

## Execution Permissions — USER-CHOSEN ON FIRST RUN

**Permission mode is decided once, on the very first `/GIF` run, via Q0 of the first-run setup.** The choice is saved to `static-to-gif/stms-preferences.json` as `permission_mode` and applied to `.claude/settings.local.json`. Never re-asked.

**Two modes:**

1. **`allow_all`** (recommended, default selection) — `.claude/settings.local.json` includes broad wildcards for Bash, Read, Write, Edit, Glob, Grep, and MCP tools. The agent runs every command without prompting. Just execute. If a command fails, fix it and retry — don't ask if you're allowed to.

2. **`ask_each_time`** — narrow allow list. Claude Code prompts the user before commands not pre-allowed. The agent must NOT try to bypass these prompts. If the user denies a command, do not retry the same command — ask the user how to proceed.

**Default shipped state:** `.claude/settings.local.json` ships with the broad `allow_all` permission set so the very first `/GIF` command (which needs to read files, run platform detection, and ask Q0) does not prompt. If the user picks `ask_each_time` at Q0, the agent narrows the allow list before continuing.

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
