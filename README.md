# Visual Replication Skill

A multi-platform, agent-neutral skill for reproducing UIs, motion designs, animations, screenshots, Figma designs, reference videos, and visual interactions.

The implementation loop is:

1. Analyze the reference.
2. Implement.
3. Render the real application.
4. Capture actual output.
5. Compare reference and actual output.
6. Fix the highest-impact differences.
7. Re-render and re-compare.
8. Finish only after validation evidence exists.

## Supported Platforms

| Platform | Installation | Auto-trigger | Hook |
|---|---|---|---|
| **Codex** | `git clone` into `~/.codex/skills/` | Via `SKILL.md` description | `.codex/hooks.json` Stop Hook |
| **Claude Code** | Via `.claude-plugin/plugin.json` | Plugin/skill system | Manual or skill-invoked |
| **Cursor** | Copy `.cursorrules` + scripts to project | `.cursorrules` loaded per project | None |
| **Codewiz / Seal (本平台)** | `git clone` into `~/.config/codewiz/skills/` | Via `SKILL.md` description | Manual check script |

## Project-level files

For any project where you want this skill to apply, copy these files into the project root:

```text
AGENTS.md
config.json
scripts/
hooks/
.cursorrules
.codex/hooks.json
```

Then create a `references/` directory and place your reference screenshots or videos there.

## Global skill installation

### Codex

```bash
git clone https://github.com/ChenZGguo/visual-replication-skill.git ~/.codex/skills/visual-replication
```

Also run `~/.codex/skills/visual-replication/install.sh init --platform codex` in the project root, or copy `AGENTS.md`, `config.json`, `scripts/`, `hooks/`, and `.codex/hooks.json` into your project root.

### Claude Code

Install the plugin from the local directory:

```bash
/plugin install /path/to/visual-replication-skill
```

Or publish to the Claude Code plugin marketplace.

### Cursor

Cursor does not have a global skill system. Copy these into each project:

```text
.cursorrules
scripts/
hooks/
references/
subagents/
config.json
```

### Codewiz / Seal

```bash
git clone https://github.com/ChenZGguo/visual-replication-skill.git ~/.config/codewiz/skills/visual-replication
```

Also run `~/.config/codewiz/skills/visual-replication/install.sh init --platform codewiz` in the project root, or copy `AGENTS.md`, `config.json`, `scripts/`, and `hooks/` into your project root.

## Usage

### Static UI reference

Capture the implemented page:

```bash
npx tsx scripts/capture-page.ts --url http://localhost:3000 --output artifacts/actual.png --viewport 1440x900
```

Compare with the reference:

```bash
python3 scripts/compare-images.py \
  --reference references/reference.png \
  --actual artifacts/actual.png \
  --output-dir artifacts/diff \
  --report artifacts/visual-report.json
```

### Animation / video reference

Before implementation, classify the reference into one primary strategy:

| Strategy | Choose for | Typical output |
|---|---|---|
| Generative video | Photorealistic people, natural scenes, complex camera/light/materials, model-generated style | MP4, MOV, WebM, GIF, image sequence |
| Lottie / vector keyframe animation | Logos, icons, loaders, UI micro-interactions, path reveals, masks, shape morphs, short loops | Lottie JSON, dotLottie |
| Programmatic animation | Deterministic math, particles, physics, data, Canvas, SVG, WebGL, Three.js, p5.js, GSAP, shaders, interaction | Web app, Canvas, SVG, WebGL, recorded video |

For Lottie work, prefer Text-to-Lottie when available:

```bash
npx skills add diffusionstudio/lottie
```

Then ask the coding agent to generate a Lottie animation using `text-to-lottie`.

Read the reference video with the `watch` skill if available:

```bash
python3 ~/.codex/skills/watch/scripts/watch.py "<reference-video>" --out-dir artifacts/reference-frames
```

Capture your implementation as frames:

```bash
npx tsx scripts/capture-animation.ts --url http://localhost:3000 --output-dir artifacts/frames --duration-ms 3000 --fps 10
```

Compare the two videos:

```bash
python3 scripts/compare-video.py \
  --reference references/reference.mp4 \
  --actual artifacts/actual.mp4 \
  --output-dir artifacts/diff \
  --report artifacts/visual-report.json \
  --threshold 0.965 \
  --motion-threshold 0.93
```

Video comparison checks both frame similarity and frame-to-frame motion similarity, so timing, speed, easing, acceleration, deceleration, and loop seams are not judged by still frames alone.

### Finish-time check

For platforms without a native Stop Hook, run the check script manually:

```bash
python3 hooks/visual_stop_check.py
```

## Requirements

- Node.js + `npx` (for TypeScript scripts)
- Playwright and browser binaries (`npm install -D playwright` and `npx playwright install chromium`, or project-local equivalents)
- `tsx` for running TypeScript scripts (`npm install -D tsx`, or use `npx tsx`)
- Python 3
- Pillow (`python3 -m pip install pillow`)
- OpenCV + NumPy for video comparison (`python3 -m pip install opencv-python numpy`)
- `watch` skill for video reference analysis (optional but recommended)

## License

MIT
