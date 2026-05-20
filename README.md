# 🎬 STMS — Static to Motion System

Convert static ad designs into animated GIFs and MP4s using AI. Just type `/GIF` and the system does the rest.

---

## What This Does

You give it a **static design** (a PNG from Figma) + **exported elements** (individual layer PNGs) → it builds a pixel-perfect animated version with GSAP animations, verified overlay-by-overlay against your original design.

**No elements?** No problem. The system can AI-cutout every element from the static image itself.

**Want sound?** After animation is done, it can generate SFX (whoosh, pop, typing sounds) matched to each animation using ElevenLabs.

---

## Quick Start (1 command)

Copy-paste the line for your OS. It clones the repo, enters the folder, and launches Claude Code — all in one go.

**macOS / Linux:**
```bash
git clone https://github.com/Ashishx777/STMS.git && cd STMS && claude
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/Ashishx777/STMS.git; cd STMS; claude
```

**Windows (cmd.exe):**
```cmd
git clone https://github.com/Ashishx777/STMS.git && cd STMS && claude
```

⚠ **You MUST be inside the `STMS` folder when Claude Code launches.** If you run `claude` from the parent folder, the `/GIF` command, auto-setup, and permissions won't load. The chained command above handles this automatically.

**What happens next:** Claude Code reads the project, auto-installs missing tools via your system's package manager (winget on Windows, brew on Mac, apt on Linux), asks you 4 one-time setup questions, and reports when ready.

Once setup is complete, type:

```
/GIF
```

> **Don't have Claude Code?** Install it first: `npm install -g @anthropic-ai/claude-code`
>
> **Don't have Node.js?** Download from https://nodejs.org (LTS version). This is the ONE manual install required (Claude Code itself needs Node). Everything else — FFmpeg, Python, OpenCV — is auto-installed by the agent on first run.

---

## What You Need Per Project

**Option A — Static + Elements (recommended):**
```
your-design-folder/
  static.png        ← the full flat design (1080×1080 or 1080×1920)
  elements/          ← individual layers exported from Figma
    background.png
    product.png
    headline.png
    logo.png
    ...
```

**Option B — Static Only (AI cutout):**
```
your-design-folder/
  static.png        ← just the full design, no elements needed
```
The system will ask if you want it to AI-extract every element from the static.

---

## Commands

| Type this | What happens |
|-----------|-------------|
| `/GIF` | Start a new project — the main command |
| `/GIF <path>` | Start with a specific folder path |
| `/GIF --project <name>` | Resume an existing project |
| `preview the composition` | Opens browser preview |
| `render the video` | Creates MP4/GIF output |
| `check for errors` | Runs lint + validation |

---

## Optional: AI Enhancements

These are **not required** — the core system works without them. But they unlock extra features.

### Higgsfield (AI image generation)
- **What it adds:** Better element cutout from static, AI background extension for 9:16
- **Setup:** In Claude Code → Settings → Connectors → Add → Higgsfield → `https://mcp.higgsfield.ai/mcp`

### ElevenLabs (AI sound effects)
- **What it adds:** Whoosh, pop, typing sounds matched to your animations
- **Setup:** `npx skills add elevenlabs` or connect via MCP settings

---

## How It Works (The Pipeline)

```
/GIF
 ↓
Phase 0 — Select your design folder
 ↓
Phase 1 — Inventory elements + decide animations + source fonts
           (AI cutout here if no elements provided)
 ↓
Phase 2 — Build the HTML composition (pixel-perfect, no animation yet)
 ↓
Phase 3 — Overlay verify every element against your original design
           (THE core technique — nothing moves until this is perfect)
 ↓
Phase 4 — Animate with GSAP (custom per your choices)
 ↓
Phase 5 — Preview in browser, refine timing
 ↓
Phase 5B — Add sound effects (optional, only if you want)
 ↓
Phase 6 — Render to MP4 + GIF
```

---

## For Your Team

**Getting updates:** When the system is updated, pull the latest from inside the STMS folder:
```bash
# macOS / Linux / Windows cmd
cd STMS && git pull

# Windows PowerShell
cd STMS; git pull
```

**First-time setup asks you 3 questions** (preferences for cleanup, aspect ratio conversion, versioning). After that, it never asks again — just runs.

**All code execution permissions are pre-granted.** The system will never ask "Can I run this command?" — it just executes.

---

## Folder Structure

```
STMS/
├── CLAUDE.md              ← AI reads this automatically
├── AGENTS.md              ← Same (for Antigravity)
├── README.md              ← You're reading this
├── index.html             ← Main composition template
├── .claude/skills/gif/    ← /GIF skill definition
├── .agents/static-to-gif/ ← Workflow rules + animation presets
├── compositions/          ← Generated compositions (per project)
├── assets/static-gif/     ← Project assets (per project)
├── static-to-gif/output/  ← Final GIF/MP4 renders
└── renders/               ← Rendered outputs
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "node is not recognized" | Reinstall Node.js, check "Add to PATH" |
| "ffmpeg is not recognized" | Install FFmpeg and add to PATH |
| Skills not found | Type: `install hyperframes skills` |
| Folder picker doesn't open | Use `/GIF <path>` with the full path instead |
| Video won't render | Type: `run doctor` — the AI will diagnose |

---

## Platform Support

Works on **Windows**, **Mac**, and **Linux**. The system auto-detects your platform and uses the correct commands. No configuration needed.

---

Built on [HyperFrames](https://hyperframes.heygen.com) by HeyGen.
