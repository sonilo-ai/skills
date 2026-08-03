# Sonilo video_to_sfx prompting

SFX quality comes from a time-segmented action map: what is on screen, what
it's made of, what it does, second by second. The footage is the source of
truth — if the video came with a generation prompt, use it as a hint list,
but only write segments for what is actually visible.

## Step 1 — Action map

Watch the video (or step frames: `ffmpeg -i in.mp4 -vf fps=1 f_%02d.png`;
sample faster for sub-second action). Note each beat: `0–2 tire on gravel ·
2–4 roots, chain slap · 4–6 braking · 6–8 dirt spray · 8–10 drop landing`.
Mark the 1–2 hero beats the audio must nail.

Segment boundaries belong on cut points or action beats, not even splits.

## Step 2 — Map to the API

Two fields, both matter:

- `prompt` (≤ 2000 chars, enforced — over = error): one-line scene summary —
  setting, materials, ambience. This is the bed under everything.
- `segments` (≤ 30): one entry per beat. Each segment = **one dominant sound
  bundle** — the sounds of one physical event and its immediate by-products
  (a landing: impact thud + suspension + dust). Two unrelated events in one
  window ("brakes… and then a bird") = split the segment.

Per-segment prompt formula: **source + material + action**. Concrete nouns
and material verbs (bite, slap, sizzle, clink, crunch) — never abstractions
("exciting sounds") or mix directions ("loud", "punchy" — levels are not
promptable).

Worked example — 10 s MTB clip:

```json
{
  "prompt": "Mountain bike descending a damp dirt-and-gravel forest trail, natural outdoor ambience, overcast morning",
  "segments": [
    {"start": 0, "end": 2, "prompt": "knobby tire biting packed dirt and loose gravel, small stones kicking off the tread"},
    {"start": 2, "end": 4, "prompt": "bike over roots and rock: chain slapping the frame, suspension compressing and rebounding"},
    {"start": 4, "end": 6, "prompt": "disc brake engaging, pads biting the rotor, front tire slowing on a loose surface"},
    {"start": 6, "end": 8, "prompt": "rear wheel breaking traction in a berm, a wide fan of dirt and gravel spraying across the frame"},
    {"start": 8, "end": 10, "prompt": "both wheels landing off a small drop, a compression thud into dirt, trail ambience opening up"}
  ]
}
```

Quiet footage works the same way with sparser beats — a talking-head clip
might be one ambience bed plus two segments (chair creak, papers). Don't
force 30 segments onto footage with three sound events.

## Segment rules — all backend-enforced (rejected before any charge)

- ≤ 30 segments; raw segments JSON ≤ 40,000 chars
- first `start` = 0
- contiguous: each `end` == next `start` (0.01 s tolerance)
- every `end` > `start`
- each segment prompt non-empty, ≤ 200 chars
- last `end` ≤ video duration (+0.05 s tolerance) — it does **not** have to
  reach the end; an uncovered tail simply gets no generated SFX
- sub-second floats are fine and pass through as-is (unlike music segments,
  which round to whole seconds)
- more than 30 beats? Merge adjacent minor beats into their dominant
  neighbor; keep hero beats as their own segments
- MCP: `segments` is the same array JSON-encoded as a string, same validation

## Exclusions

"No crowd noise" can go in the global prompt or a segment prompt — both are
free text passed verbatim, both best-effort, nothing enforced. Verify by
listening.

## Iterating

Hero beat doesn't land → give it its own tighter segment with more specific
material words. Wrong sound identity → the segment prompt names the wrong
source/material; fix nouns before adjectives. Two revisions haven't fixed it
→ the action map is too vague; go back to Step 1, not the thesaurus. Every
regeneration is a new charge.
