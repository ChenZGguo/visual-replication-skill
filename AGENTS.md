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
- Element appearance and disappearance timing
- Translation, scale, rotation, and opacity changes
- Easing curves and motion rhythm
- Layering and occlusion
- Natural loop transitions

Do not judge completion only by reading code. Always inspect the rendered result.

## Shared Agent Resources

Use the visual replication resources in this project when available:

- Skill contract: `SKILL.md`
- Config: `config.json`
- Scripts: `scripts/`
- Stop-check adapter: `hooks/visual_stop_check.py`
- Independent reviewer prompt: `subagents/visual-reviewer.md`

These resources are intentionally agent-neutral. They are not tied to one specific product or runtime.
