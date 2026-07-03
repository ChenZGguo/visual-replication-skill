# Visual reproduction requirements

When a task involves reproducing an interface from a screenshot, design file, Figma, animation, or video:

1. Do not finish immediately after the first implementation pass.
2. Run the project and inspect the actual rendered result.
3. Compare the actual result with the reference asset visually.
4. Make at least one targeted improvement based on the differences.
5. Render and compare again after changes.
6. Finish only after the acceptance criteria are satisfied.

When a task involves reproducing motion or animation:

1. Extract every frame of the reference at its native frame rate before analyzing the animation.
2. Analyze the full frame sequence first and describe the understood animation to the user before implementation.
3. Do not rely only on sampled frames, sparse screenshots, or key frames for initial motion analysis.
4. Include semantic replay, visual states, key objects, timeline, motion rhythm, shape/form transitions, and transition continuity in that description.
5. Wait for explicit user approval before starting code replication.
6. For complex animations, split the whole motion into distinct phases before implementation.
7. Create a reference phase map with phase times, visible elements, active transformations, and handoff points.
8. Reproduce phases one by one, then integrate them.
9. Tune phase boundaries so timing, velocity, shape continuity, opacity, layering, and easing connect naturally.
10. Treat natural shape-to-shape and phase-to-phase transitions as a primary acceptance criterion.

For Lottie, SVG, or vector keyframe animation:

- Validate motion semantics before visual polish: element identity, action order, movement direction, and visual cause-effect must match the reference.
- Establish a font/rendering strategy early. Check font weight, spacing, edge quality, outlines, and anti-aliasing.
- Prefer vector paths, masks, and keyframe logic over frame-patching or duplicated keyframes.
- Enforce handoff invariants for each A -> B transform: center, bounding box, scale, rotation, opacity, contour, layer identity, and velocity should continue unless the reference shows an intentional cut or occlusion.
- Run a stutter check around transition keyframes: repeated positions, duplicate holds, keyframe clusters, tiny pauses, or backtracks are risks.
- Classify user feedback before fixing: trajectory, morph/shape, rhythm/timing, typography/edge rendering, layering/occlusion, or handoff/continuity.
- After each fix, run a regression checklist for earlier issues, new stutter, snapping, teleporting, artifacts, font/rendering drift, and frame-patching shortcuts.

Static interfaces must be checked for:

- Layout, size, spacing, and alignment
- Font family, font size, font weight, and line height
- Color, border radius, shadow, and blur
- Desktop and mobile responsive behavior

Animations must be checked for:

- Total duration
- Selected strategy: generative video, Lottie/vector keyframe animation, or programmatic animation
- Element appearance and disappearance timing
- Translation, scale, rotation, and opacity changes
- Easing curves and motion rhythm
- Frame-to-frame motion deltas, acceleration, and deceleration
- Layering and occlusion
- Natural loop transitions
- Natural shape/form transitions between major visual states and phases
- Handoff continuity between states: center, contour, velocity, opacity, scale, rotation, and layer identity
- Stutter risk around transition keyframes

Before implementing an animation, classify the reference:

- Generative video: photorealistic people, natural scenes, complex lighting/materials, camera realism, or model-generated style. Prefer video/image-sequence generation outputs.
- Lottie/vector keyframe animation: logo, icon, loader, UI micro-interaction, short loop, SVG path reveal, shape morph, masks, opacity/position/scale/rotation keyframes. Prefer Lottie JSON or dotLottie, and use the Text-to-Lottie skill (`npx skills add diffusionstudio/lottie`) when available.
- Programmatic animation: deterministic math, particles, physics, data, Canvas, SVG, WebGL, Three.js, p5.js, GSAP, shaders, or real-time user input. Prefer code-based implementation.

State the selected strategy and evidence before implementation. If multiple strategies fit, prefer the one with higher determinism, editability, and smaller output for the required use case.

Do not judge completion only by reading code. Always inspect the rendered result.

## Shared Agent Resources

Use the visual replication resources in this project when available:

- Skill contract: `SKILL.md`
- Config: `config.json`
- Scripts: `scripts/`
- Stop-check adapter: `hooks/visual_stop_check.py`
- Independent reviewer prompt: `subagents/visual-reviewer.md`

These resources are intentionally agent-neutral. They are not tied to one specific product or runtime.
