# Sonilo video_to_music prompting

The model reads the cut itself — pacing, motion, edit points — and generation
targets the video's length. What it cannot know is your intent: genre, the
moment that matters, the sounds that must not appear. The prompt supplies
intent; keep timing expectations honest (see below).

**The core principle (validated in production testing): quality tracks
consistency, not eloquence.** Output quality depends less on how well the prompt is written
than on whether the prompt and the video share the same semantics and
structure — same subject, same rhythm, same emphasized moments. A broad,
beautiful music description written from thin air loses to a plain brief
that mirrors what's actually on screen.

## The music brief

Five lines before writing the prompt:

| Field | What to write | Example (10 s MTB clip) |
|---|---|---|
| **Style & register** | Genre + what the piece is commercially (if it has a commercial register — skip for personal/editorial footage) | Kinetic action-sports score; product launch film |
| **Energy arc** | Shape over time, in relative terms | builds through the first half, peaks at the landing |
| **Hero moment** | The 1–2 on-screen beats the music must acknowledge | the drop landing at ~8s |
| **Instrumentation** | Texture and what carries it | live drums, distorted bass, no synths |
| **Exclusions** | What must NOT appear | no vocals, no EDM drop |

## AI-generated footage: reverse-derive the brief

The strongest source for a consistent brief is the prompt that generated the
video — it already encodes duration, style, beat-by-beat action, and the
moments the creator cared about. Don't discard it; re-extract from it:

| From the video-gen prompt | → brief field |
|---|---|
| Stated/actual length | Duration (verify with ffprobe — renders drift) |
| Visual style + commercial type | Style & register |
| Time-segmented action beats | Energy arc / section-shaped language |
| Emphasized shots | Hero moment |
| Mood words, materials, textures | Instrumentation & mood |
| What the creator avoided | Exclusions |

This reverse-derivation beats writing a music description from scratch — it
inherits the video's structure for free. One guardrail: the rendered pixels
still outrank the prompt. Where the render deviates from what was asked,
brief against what's on screen (see the [pre-flight](./preflight.md)).

## Writing the prompt

Spend the words on style, not timestamps:

- genre + mood + energy arc ("builds from sparse to driving")
- instrumentation and texture
- commercial register when real ("30-second product-film score", "cozy vlog bed")
- exclusions, stated plainly ("no vocals, no lo-fi crackle")

```
prompt: "Kinetic action-sports score for a 10-second product film. Gritty
live drums and distorted bass, builds tension over the first half and peaks
hard near the end. Modern, confident, cinematic. No vocals, no EDM drop,
no orchestral swell."
```

A second register, so the first example doesn't get copied everywhere —
talking-head/interview footage:

```
prompt: "Warm, unobtrusive bed for a founder interview. Soft keys and muted
guitar, slow pulse, stays out of the way of the voice. No drums entering
mid-phrase, no melody hooks, no vocals."
```

**Timing honesty.** Alignment of transitions and drops to cut points is
best-effort model behavior, not a guarantee — the backend has no alignment
logic. Use relative structural language, never promise frame-exact sync, and
don't write timestamp syntax expecting enforcement. Output length targets
the video's duration but is not contract-trimmed to it.

Worked example of section-shaped language that parses well — anchor moments
to *what happens on screen*, with rough time zones:

```
Good:  "a drop to near-silence around 12s, then the biggest beat drop of
        the track when the web line strikes the play button, triumphant
        from the landing onward"
Bad:   "drop exactly at 12.5s"
```

Where do those anchors come from? Cut timestamps fall out of scene
detection, but a hero moment *inside* a continuous shot (the strike, the
landing) has no cut to find it — step frames around the beat
(`ffmpeg -ss 10 -i in.mp4 -vf fps=10 -t 4 f_%03d.png`) and read the second
off the frames before writing "around 12s".

## Segmented music (different sections)

Two routes when the piece needs distinct sections (calm intro → driving second half):

1. **REST**: an explicit `segments` parameter exists — segment starts are
   rounded to whole seconds. Check the current API reference for the schema.
2. **MCP** (and REST without `segments`, single variant): describe the
   sections *in the prompt text*, in order, with rough spans. A backend
   prompt-analysis pass parses clearly section-shaped text into a segments
   plan; text it can't parse falls back to a whole-prompt style hint. This is
   the only segmented-music route on MCP.

## Speech and ducking

- Footage with dialogue/VO: set `preserve_speech=true` (**default is false**).
  On REST this requires `mode=async`; MCP is always async. You get a vocals
  stem plus a speech+music mux at no extra charge.
- **Ducking is ON by default in async mode**, independent of
  `preserve_speech`; disable with `ducking=false`. Best-effort — a video with
  no audio track silently gets no ducking.
- Because ducking defaults on, runs on speechless footage can still return
  ducked copies alongside the main track. When there's no speech, the ducked
  files are safe to discard — the plain music track is "the real one".
- Mix levels are computed server-side from loudness measurement; nothing in
  the prompt changes levels. Don't write "quiet" or "louder drums" —
  restate the *role* instead ("background bed", "drums carry the track").

## Exclusions are best-effort

"No vocals" has zero backend enforcement. State exclusions plainly, then
verify by listening (or stem-split as a diagnostic). If an excluded element
keeps returning, strengthen the positive description of what you want instead
of stacking more negatives.

## Variants as creative directions

`variants_num=3` is not three rerolls of one idea — treat it as three *named
creative directions* (e.g. "orchestral-cinematic", "electronic-kinetic",
"minimal-percussive"), each described in its own sentence of the prompt run.
Then review them in context, not in a file browser: mux each variant onto the
draft cut —

```
ffmpeg -i draft.mp4 -i variant1.m4a -map 0:v -map 1:a -c:v copy -shortest v1.mp4
```

— and watch all three as finished videos. Music judged against picture reads
completely differently from music judged alone.

After the pick, **lane-lock the follow-up**: "variations on that one theme,
not different genres." Otherwise the next round re-explores the whole space
and you pay for directions you already rejected. (Cost note: `variants_num`
multiplies the charge linearly — three directions = 3× one run, and still
usually cheaper than three sequential guess-and-regenerate rounds.)

## Iterating

One targeted change per regeneration, in this order: genre words wrong →
fix genre first; genre right but energy wrong → adjust arc words ("builds",
"sustained", "sparse"); style right but a section misses → move to the
segmented route. Each regeneration is a new charge — diagnose before rerolling.
