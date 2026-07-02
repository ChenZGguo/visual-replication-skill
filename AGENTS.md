# Visual reproduction requirements

When a task involves reproducing an interface from a screenshot, design file, Figma, animation, or video:

1. Do not finish immediately after the first implementation pass.
2. Run the project and inspect the actual rendered result.
3. Compare the actual result with the reference asset visually.
4. Make at least one targeted improvement based on the differences.
5. Render and compare again after changes.
6. Finish only after the acceptance criteria are satisfied.

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
