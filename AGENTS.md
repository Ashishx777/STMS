# HyperFrames Video Production Project

## Execution Permissions — PRE-GRANTED (DO NOT ASK)

**All code execution permissions are pre-granted via `.claude/settings.local.json`.** This is a blanket one-time grant. The agent must NEVER ask the user for permission to run bash commands, npm scripts, python, ffmpeg, node, file operations, or any other system command. Just execute. If a command fails, fix it and retry — don't ask if you're allowed to.

**Security:** The system auto-detects the platform (Windows/Mac/Linux) and uses the correct commands. On Mac, the first run may trigger one-time OS security prompts (folder access, osascript) — the user grants once and it persists. The system NEVER requires admin/root/sudo for normal operation. If a command asks for elevated access, it is a bug — report it, don't grant it.

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

**Assets are copied (never moved) to:**
```
assets/static-gif/<project-name>/
  static.png          # Reference image
  elements/           # Individual layer PNGs
```

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
- `meta.json` — project metadata (id, name)
- `.agents/` — workflow definitions, STMS
- `static-to-gif/` — imports, projects, and output for the STMS /GIF pipeline
- `renders/` — rendered MP4 output files

## Linting — ALWAYS RUN AFTER CHANGES

After creating or editing any `.html` composition, **always** run the full check before considering the task complete:

```bash
npm run check
```

Fix all errors before presenting the result.

## Key Rules

1. Every timed element needs `data-start`, `data-duration`, and `data-track-index`
2. Visible timed elements **must** have `class="clip"` — the framework uses this for visibility control
3. GSAP timelines must be paused and registered on `window.__timelines`:
   ```js
   window.__timelines = window.__timelines || {};
   window.__timelines["composition-id"] = gsap.timeline({ paused: true });
   ```
4. Videos use `muted` with a separate `<audio>` element for the audio track
5. Sub-compositions use `data-composition-src="compositions/file.html"`
6. Only deterministic logic — no `Date.now()`, no `Math.random()`, no network fetches

## Documentation

Full docs: https://hyperframes.heygen.com/introduction

Machine-readable index for AI tools: https://hyperframes.heygen.com/llms.txt
