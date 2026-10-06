# Prompt Composer production plan

Experimental instruction composition, not a generated image or video.

## Concise prompt

Create a controlled video of a satin-metal hero product. keep a satin reflection broad and restrained while preserving the base color and fine surface texture. a narrow highlight sweeps across the surface in the requested direction, revealing detail without moving the object. the primary change approaches its target, applies only the explicitly requested overshoot and reduced rebound, and settles. use one broad controlled light source to define a readable highlight width and a coherent soft shadow.

## Detailed prompt

Create a model-neutral video of a satin-metal hero product. keep a satin reflection broad and restrained while preserving the base color and fine surface texture. a narrow highlight sweeps across the surface in the requested direction, revealing detail without moving the object. the primary change approaches its target, applies only the explicitly requested overshoot and reduced rebound, and settles. use one broad controlled light source to define a readable highlight width and a coherent soft shadow. reveal a thin clear top reflection layer separately from the underlying satin-metal reflection. Preserve identity, geometry, logo, composition, background. Requested delivery: duration in seconds: 5; fps: 24; aspect ratio: 16:9; resolution: 1920x1080. Required: thin transparent coat; left-to-right highlight sweep; single subtle overshoot. Hold the described initial state. Begin the requested primary change continuously. Make that change readable; preserve the stated subject constraints. Approach the target; apply only explicitly requested secondary motion. Hold the final state for review.

## Selection rationale

Scores are heuristic selection scores, not model success rates.

- MM-007 — directional sweep front (52); primary_motion
- MM-024 — spline ease and overshoot (51); supporting_motion_or_timing
- RS-VM-011 — roughness to highlight width and sharpness (60); material
- RS-VM-014 — coat independent top reflection layer (35); material
- RS-VM-001 — area light size and shape to highlight and shadow (38); lighting

## Temporal plan

Ranges are editorial suggestions, not observed frame timing.

- 0-15%: Hold the described initial state.
- 15-40%: Begin the requested primary change continuously.
- 40-65%: Make that change readable; preserve the stated subject constraints.
- 65-85%: Approach the target; apply only explicitly requested secondary motion.
- 85-100%: Hold the final state for review.

## Required and excluded conditions (original input)

```json
{
  "must_include": [
    "thin transparent coat",
    "left-to-right highlight sweep",
    "single subtle overshoot"
  ],
  "must_avoid": [
    "melt",
    "texture morph",
    "global brightness pumping"
  ]
}
```

## Sources

- [Redshift Standard Material](https://help.maxon.net/c4d/en-us/Content/_REDSHIFT_/html/Standard_Material.html)
- [Cinema 4D Linear Field](https://help.maxon.net/c4d/2026/en-us/Content/html/FLINEAR.html)
- [Cinema 4D Keys and Interpolation](https://help.maxon.net/c4d/2025/en-us/Content/html/10616.html)
- [Redshift Physical Light](https://help.maxon.net/c4d/2025/en-us/Subsystems/Default/Content/html/Physical%2BLight.html)
- [Common Redshift Light Parameters](https://help.maxon.net/c4d/2026/en-us/Content/_REDSHIFT_/html/Common%2BRedshift%2BLight%2BParameters.html)

## Unverified behavior

- Model quality, exact timing, and reference adherence require real generation comparisons.
- This is not a general translator. Unmapped Korean subjects use a neutral English placeholder.
