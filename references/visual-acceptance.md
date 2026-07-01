# Visual Acceptance Criteria

Use these criteria when judging whether a visual reproduction task can finish.

## Static UI

- Overall layout matches the reference at the requested viewport sizes.
- Major element positions are within a small visual tolerance.
- Typography, spacing, colors, radius, shadows, and borders are visually consistent.
- No unexpected scrollbars, clipping, wrapping, or overflow are introduced.
- Desktop and mobile states have both been inspected when relevant.

## Motion UI

- Initial state, key frames, and final state match the reference.
- Total duration and major event timings match the reference.
- Position, scale, rotation, opacity, and layering changes follow the same rhythm.
- Loop boundaries do not jump unless the reference also jumps.
- Side-by-side or overlay review has been inspected.

## Required Evidence

- Reference asset path.
- Actual capture path.
- Difference output path.
- JSON report path.
- Remaining known differences, if any.
