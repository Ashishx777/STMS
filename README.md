# 🎬 STMS — Static to Motion System

Convert static ad designs into animated GIFs and MP4s using AI. Just type `/GIF` and the system does the rest.

---

## What This Does

You give it a **static design** (a PNG from Figma) + **exported elements** (individual layer PNGs) → it builds a pixel-perfect animated version with GSAP animations, verified overlay-by-overlay against your original design.

**No elements?** No problem. The system can AI-cutout every element from the static image itself.

**Want sound?** After animation is done, it can generate SFX (whoosh, pop, typing sounds) matched to each animation using ElevenLabs.

---

## Quick Start (2 steps)

### Step 1: Clone the repo

```bash
git clone https://github.com/Ashishx777/STMS.git
cd STMS
```

### Step 2: Open in Claude Code

```bash
claude
```

**That's it.** Claude Code reads the project, detects your platform, checks for missing tools (Node.js, FFmpeg, Python), installs what's needed, sets up HyperFrames skills, and reports when ready.

If anything is missing that can't be auto-installed (like Node.js on Windows), it tells you exactly what to download and where.

Once setup is complete, type:

```
/GIF
```

> **Don't have Claude Code?** Install it first: `npm install -g @anthropic-ai/claude-code`
>
> **Don't have Node.js?** Download from https://nodejs.org (LTS version). This is the only manual install required — everything else is handled automatically.

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

**Getting updates:** When the system is updated, just run:
```bash
cd STMS
git pull
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
