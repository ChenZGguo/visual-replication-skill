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
- Element positions over time
- Opacity, scale, and rotation
- Animation start and end times
- Easing and motion rhythm

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
