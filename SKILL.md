---
name: visual-replication
description: Use when reproducing a UI, motion design, animation, screenshot, Figma design, reference video, or visual interaction. Automatically render, compare, diagnose differences, revise, and repeat.
---

# Visual Replication Loop

Use this workflow when reproducing a UI, motion design, animation, screenshot, Figma design, reference video, or visual interaction.

## Required Workflow

1. Analyze the reference asset.
2. Extract measurable visual requirements.
3. Implement the first version.
4. Launch the actual application.
5. Capture the implementation using the same viewport, resolution, and timeline as the reference.
6. Run the visual comparison scripts.
7. Read the generated report and diff images.
8. Identify the three highest-impact discrepancies.
9. Modify the implementation.
10. Capture and compare again.

Do not declare completion after only one implementation pass.

## Static Reference Validation

Use Playwright or the browser tools available to the agent to:

- Open the target route
- Set the required viewport
- Wait for fonts and images
- Disable irrelevant dynamic content
- Capture screenshots
- Compare reference and actual results

## Animation / Video Reference Validation

### Animation strategy selection

Before implementing any animation, GIF, motion graphic, or reference video, classify the reference into exactly one primary strategy. State the selected strategy and the reason before implementation.

| Strategy | Use when | Preferred output | Avoid when |
|---|---|---|---|
| Generative video | The reference is photorealistic, includes people, natural scenes, complex lighting/materials, camera realism, or details that cannot be decomposed into stable layers. | MP4, MOV, WebM, GIF, image sequence | Precise UI timing, editable vector assets, transparent backgrounds, deterministic interaction, text/UI consistency |
| Lottie / vector keyframe animation | The reference is a logo, icon, loading animation, UI micro-interaction, short loop, path reveal, shape morph, opacity/position/scale/rotation keyframes, masks, or layered vector motion. | Lottie JSON, dotLottie, vector assets | Photorealistic scenes, fluids, particles, large real-time simulations, long narrative videos |
| Programmatic animation | The motion is best described by code, math, physics, particles, data, Canvas, SVG, WebGL, Three.js, p5.js, GSAP, shaders, or real-time user input. | Web app, Canvas, SVG, WebGL, shader, recorded video | Photorealistic footage or animation that depends on generative model style rather than deterministic rules |

Decision rules:

- Choose generative video for realistic people, natural environments, complex camera shots, or model-generated visual style.
- Choose Lottie when the animation can be decomposed into vector layers, paths, masks, keyframes, and easing curves.
- Choose programmatic animation when deterministic control, interactivity, parameters, data, particles, geometry, or real-time rendering are central.
- If both Lottie and programmatic animation are viable, prefer the smaller and more maintainable output. Use Lottie for asset-like UI motion and programmatic animation for interaction or simulation.
- If the selected strategy is Lottie, prefer the Text-to-Lottie skill from `diffusionstudio/lottie` when available. Install with `npx skills add diffusionstudio/lottie`, then ask the agent to generate a Lottie animation using `text-to-lottie`.
- If classification is uncertain, inspect extracted frames first, list the top two candidate strategies, then choose the one with higher determinism and editability.

The implementation plan must include:

- Selected strategy: `generative-video`, `lottie`, or `programmatic-animation`
- Evidence from the reference that supports the choice
- Expected output format
- Validation method and thresholds

### Reading the reference video

Prefer the `watch` skill (`~/.codex/skills/watch`) to analyze the reference video first:

```bash
python3 ~/.codex/skills/watch/scripts/watch.py "<reference-video-url-or-path>" --out-dir artifacts/reference-frames
```

This downloads the video, extracts auto-scaled frames with timestamps, and pulls a transcript (captions or Whisper fallback). Read the output frames and transcript to understand:

- Total duration and timeline structure
- Key frames and major visual states
- Element appearance/disappearance timing
- Motion rhythm and easing
- Spoken content or on-screen text

Use `--start` / `--end` to focus on a specific section for denser frame coverage when needed.

### Quantitative comparison

After implementing, normalize the reference and implementation to:

- Identical resolution
- Identical frame rate
- Identical start time
- Identical duration when possible

Compare:

- Key frames
- Frame-to-frame motion deltas, not only individual frame pixels
- Element positions over time
- Opacity, scale, and rotation
- Animation start and end times
- Easing and motion rhythm
- Loop seam continuity when the reference is looping
- Timing drift for entrances, exits, pauses, accelerations, and decelerations

Motion validation must inspect both absolute frames and temporal changes. A visually similar still frame sequence can still fail if the speed, easing, acceleration, or previous-to-next-frame deltas do not match the reference.

Generate:

- Side-by-side video when possible
- Difference video or difference frames
- Contact sheet when possible
- Machine-readable JSON report

## Commands

### Reading a reference video (preferred for video/animation references)

```bash
python3 ~/.codex/skills/watch/scripts/watch.py "<reference-video>" --out-dir artifacts/reference-frames
```

Optional: `--start 0:05 --end 0:15` for focused sections, `--resolution 1024` for reading on-screen text.

### Capturing the implementation

Capture a static page:

```bash
npx tsx scripts/capture-page.ts --url http://localhost:3000 --output artifacts/actual.png --viewport 1440x900
```

Capture an animation as frames:

```bash
npx tsx scripts/capture-animation.ts --url http://localhost:3000 --output-dir artifacts/frames --duration-ms 3000 --fps 10
```

### Comparing

Compare static images:

```bash
python3 scripts/compare-images.py --reference references/reference.png --actual artifacts/actual.png --output-dir artifacts/diff --report artifacts/visual-report.json
```

Compare two videos:

```bash
python3 scripts/compare-video.py --reference references/reference.mp4 --actual artifacts/actual.mp4 --output-dir artifacts/diff --report artifacts/visual-report.json
```

### Summarize and finish-check

Summarize validation:

```bash
python3 scripts/generate-report.py --project-root "$PWD" --report artifacts/visual-report.json
```

Run the finish-time check manually:

```bash
python3 hooks/visual_stop_check.py
```

## Completion Requirements

The final response must contain:

- Validation command executed
- Number of iterations
- Remaining known differences
- Locations of comparison outputs

Do not claim visual parity without running validation.
