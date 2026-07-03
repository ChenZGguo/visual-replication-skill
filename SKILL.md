---
name: visual-replication
description: Use when reproducing a UI, motion design, animation, screenshot, Figma design, reference video, or visual interaction. Automatically render, compare, diagnose differences, revise, and repeat.
---

# Visual Replication Loop

Use this workflow when reproducing a UI, motion design, animation, screenshot, Figma design, reference video, or visual interaction.

## Required Workflow

1. Analyze the reference asset.
2. If the reference includes motion, extract every frame of the reference at its native frame rate before analyzing the animation. Do not rely only on sampled frames, sparse screenshots, or key frames for the initial motion analysis.
3. If the reference includes motion, describe the understood animation to the user before implementation: visual states, key objects, timeline, motion rhythm, shape/form transitions, and why those transitions matter.
4. For motion references, wait for explicit user approval of that interpretation before starting code replication.
5. Extract measurable visual requirements.
6. Implement the first version.
7. Launch the actual application.
8. Capture the implementation using the same viewport, resolution, and timeline as the reference.
9. Run the visual comparison scripts.
10. Read the generated report and diff images.
11. Identify the three highest-impact discrepancies.
12. Modify the implementation.
13. Capture and compare again.

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

For animation or video references, the first analysis pass must extract all frames at the source/native frame rate. Full-frame extraction is required before semantic analysis, phase mapping, strategy choice, or implementation planning.

Use `ffmpeg` directly when full-frame extraction is needed:

```bash
ffmpeg -i "<reference-video>" -vsync 0 artifacts/reference-frames/frame_%06d.png
```

After full-frame extraction, use the `watch` skill (`~/.codex/skills/watch`) for complementary timeline reading, transcript extraction, and auto-scaled overview frames:

```bash
python3 ~/.codex/skills/watch/scripts/watch.py "<reference-video-url-or-path>" --out-dir artifacts/reference-frames
```

This downloads the video, extracts auto-scaled frames with timestamps, and pulls a transcript (captions or Whisper fallback). Treat those frames as an overview only when the source is motion; the authoritative motion analysis must use the all-frame extraction. Read the full frame sequence plus transcript to understand:

- Total duration and timeline structure
- Key frames, all transition frames, and major visual states
- Element appearance/disappearance timing
- Motion rhythm and easing
- Spoken content or on-screen text

Use `--start` / `--end` only for additional focused analysis after the full-frame pass, not as a substitute for initial all-frame extraction.

### Motion decomposition and approval

Before writing animation code, present the agent's interpretation of the motion and wait for user approval. Do not begin code replication until the user confirms the interpretation.

The interpretation must cover:

- Overall story of the motion in plain language
- Semantic replay: identify which element moves or transforms, the action order, and the visual cause-effect relationship between states
- Major visual states and how each state transforms into the next
- Timeline phases, approximate durations, and ordering
- Key object shape/form changes, including morphing, stretching, folding, masking, clipping, or layout reflow
- Transition continuity between phases, especially whether the form change feels natural rather than abrupt
- Motion rhythm, easing, pauses, acceleration, and deceleration
- Layering, occlusion, entrances, exits, and loop seam if present

For complex animations, split the reproduction into stages:

- First map the whole animation into distinct phases.
- Create a reference phase map with phase names, start/end times, visible elements, active transformations, and handoff points.
- Reproduce and validate each phase independently.
- Integrate phases only after each phase matches its target behavior.
- Tune boundaries between phases so timing, shape continuity, velocity, opacity, layering, and easing connect naturally.
- Treat natural shape-to-shape transition quality as a primary acceptance criterion, not a secondary polish task.
- If a transition feels stiff, jumpy, or disconnected, revise the transition before optimizing less important visual details.

### Lottie and vector motion quality gates

For Lottie, SVG, or vector keyframe animation, validate motion semantics before visual polish:

- Confirm the animation meaning is correct before tuning pixels: element identity, movement direction, transformation order, and cause-effect relationship must match the reference.
- Prefer deliberate vector shapes, masks, and path/keyframe logic over image-like hacks when reproducing typography, icons, or morphing objects.
- Define a font/rendering strategy early: exact font when available, otherwise vectorized outlines or an intentional fallback. Check weight, edge quality, spacing, and anti-aliasing.
- Avoid fixing still frames by adding duplicated or redundant keyframes that can create stutter, snapping, or disconnected motion.
- After every fix, run a regression pass for previously observed artifacts instead of validating only the newly changed segment.

Handoff invariant for any A -> B transform:

- Compare the last frame of state A and the first frame of state B.
- Check center position, bounding box, scale, rotation, opacity, and visible contour continuity.
- If the element is meant to be continuous, the handoff should not teleport, jump layers, change identity, or reset velocity.
- If the handoff is intentionally discontinuous, the reference must show a cut, occlusion, flash, or other visual reason for the discontinuity.

Stutter check:

- Inspect consecutive keyframes around each transition.
- Flag repeated or near-repeated positions without corresponding scale, opacity, rotation, mask, or path change.
- Flag tiny unintended pauses, backtracks, duplicate holds, or keyframe clusters that create a visible hiccup.
- Validate frame-to-frame deltas, not only whether individual keyframes look similar to the reference.

Motion delta report:

- For each phase, summarize displacement, velocity changes, acceleration/deceleration, pause duration, scale/opacity changes, and handoff continuity.
- Pay special attention to transition segments, because they often determine whether the whole animation feels natural.

User critique taxonomy:

- Classify feedback before fixing: trajectory error, morph/shape error, rhythm/timing error, typography/edge rendering error, layering/occlusion error, or handoff/continuity error.
- Choose validation based on the category. Do not use still-image comparison alone for trajectory, rhythm, or handoff complaints.

Regression checklist before completion:

- Previously fixed discontinuities have not returned.
- No new stutter, snapping, or teleporting appears near edited keyframes.
- No new visual artifacts appear in shape edges, masks, typography, or layer order.
- Font/rendering strategy still matches the reference.
- Fixes use motion logic, not frame-patching that only hides one sampled mismatch.

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
- Per-phase displacement and velocity changes
- Opacity, scale, and rotation
- Animation start and end times
- Easing and motion rhythm
- Loop seam continuity when the reference is looping
- Timing drift for entrances, exits, pauses, accelerations, and decelerations
- Natural continuity of shape/form transitions between major visual states and phases
- Handoff continuity between states: center, contour, velocity, opacity, scale, rotation, and layer identity
- Stutter risk around transition keyframes: repeated positions, duplicate holds, keyframe clusters, or unexpected pauses

Motion validation must inspect both absolute frames and temporal changes. A visually similar still frame sequence can still fail if the speed, easing, acceleration, or previous-to-next-frame deltas do not match the reference.
For most animations, the most important quality check is whether transitions between forms and phases feel natural, continuous, and intentional.

Generate:

- Side-by-side video when possible
- Difference video or difference frames
- Contact sheet when possible
- Machine-readable JSON report

## Commands

### Reading a reference video (preferred for video/animation references)

Extract every source frame first:

```bash
ffmpeg -i "<reference-video>" -vsync 0 artifacts/reference-frames/frame_%06d.png
```

Then run the overview/transcript helper:

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
