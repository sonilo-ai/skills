---
name: music
description: Generate music using Sonilo. Use when creating instrumental tracks, background music, jingles, or a soundtrack scored to a video's pacing, motion, and emotion. Supports text-to-music, video-to-music, and video-to-video (muxed) output. Every track is licensed and cleared for commercial use.
license: MIT
compatibility: Requires the Sonilo MCP server connected and Sonilo credentials — either a `sonilo login` sign-in, the hosted OAuth plugin, or SONILO_API_KEY. See the setup-api-key skill.
---

# Sonilo Music Generation

Generate music from a text prompt, or score it directly to a video — Sonilo watches the cut and matches pacing, motion, and emotion, with transitions and beat drops aligned to the edit. Every track is licensed (music licensed via Shutterstock) and cleared for commercial use on social, brand content, and advertising.

> **Setup:** See the [setup-api-key](../setup-api-key) skill to connect the Sonilo MCP server and authenticate — `sonilo login` (no key) or `SONILO_API_KEY`.

> ⚠️ **Cost:** every tool below makes an API call that may incur charges. Only call it when the user has actually asked for a generation. Check `get_account_services` (see the [account](../account) skill) if you're unsure whether free-trial runs remain.

## Quick Start

### MCP tool call (recommended)

Once the `sonilo` MCP server is connected, call the tool directly — no SDK needed:

```
text_to_music(
    prompt="A chill lo-fi hip hop beat with jazzy piano chords",
    duration=30
)
```

```
video_to_music(
    video_path="~/Desktop/trailer.mp4",
    prompt="Build suspense, then resolve with a warm cinematic finish"
)
```

Both save the generated file(s) to `SONILO_MCP_BASE_PATH` (`~/Desktop` by default) and return the saved path(s) as text.

### Python (`pip install sonilo`)

```python
from sonilo import Sonilo

client = Sonilo()  # reads SONILO_API_KEY

track = client.text_to_music.generate(prompt="A chill lo-fi hip hop beat with jazzy piano chords", duration=30)
track.save("output.mp3")

score = client.video_to_music.generate(video="trailer.mp4", prompt="Build suspense, then resolve with a warm cinematic finish")
score.save("score.m4a")

# video_to_video_music has no CLI command — this is the only non-MCP way to get the muxed video back
video = client.video_to_video_music.generate(video="trailer.mp4", prompt="cinematic, uplifting")
video.save("scored.mp4")
```

`preserve_speech=True` on `video_to_music` requires the async path — use `generate_async()` instead of `generate()` to get the extra `vocals`/`mux`/`ducked` outputs; see [sonilo-python's README](https://github.com/sonilo-ai/sonilo-python#preserve-speech-async) for the full pattern.

### JavaScript / TypeScript (`npm install sonilo`)

```ts
import { SoniloClient } from "sonilo";

const client = new SoniloClient(); // reads SONILO_API_KEY

const track = await client.textToMusic.generate({
  prompt: "A chill lo-fi hip hop beat with jazzy piano chords",
  duration: 30,
});

const score = await client.videoToMusic.generate({
  video: "./trailer.mp4",
  prompt: "Build suspense, then resolve with a warm cinematic finish",
});

// video_to_video_music has no CLI command — this is the only non-MCP way to get the muxed video back
const video = await client.videoToVideoMusic.generate({
  video: "./trailer.mp4",
  prompt: "cinematic, uplifting",
});
```

`preserveSpeech: true` on `videoToMusic` requires the async path — use `.submit()` + `client.tasks.wait()` instead of `.generate()`; see [sonilo-js's README](https://github.com/sonilo-ai/sonilo-js/tree/main/packages/sonilo#preserve-speech-async) for the full pattern.

### CLI (`npm install -g sonilo-cli` or `pip install sonilo-cli`)

```bash
sonilo text-to-music --prompt "A chill lo-fi hip hop beat with jazzy piano chords" --duration 30
sonilo video-to-music --video trailer.mp4 --prompt "Build suspense, then resolve with a warm cinematic finish" --output score.m4a
```

`--format wav`, `--preserve-speech`, and `--isolate-vocals` each switch `video-to-music` to the async submit-and-poll path. **There is no CLI command for `video_to_video_music`** (the video-to-video variants aren't exposed by either CLI) — use the Python/JS SDK or the MCP tool for that.

### cURL (raw REST API, no MCP host)

```bash
curl -X POST "https://api.sonilo.com/v1/text-to-music" \
  -H "Authorization: Bearer $SONILO_API_KEY" \
  --data-urlencode "prompt=A chill lo-fi hip hop beat with jazzy piano chords" \
  --data-urlencode "duration=30" \
  --output output.m4a
```

```bash
curl -X POST "https://api.sonilo.com/v1/video-to-music" \
  -H "Authorization: Bearer $SONILO_API_KEY" \
  -F "video=@trailer.mp4" \
  -F "prompt=Build suspense, then resolve with a warm cinematic finish" \
  --output score.m4a
```

`video_to_music` also accepts a `video_url` form field instead of an uploaded file — pass one or the other, never both.

## Tools

| Tool | Description |
|------|-------------|
| `text_to_music(prompt, duration, output_format?, variants_num?, output_directory?)` | Generate music from a text description only — no video. |
| `video_to_music(video_path? \| video_url?, prompt?, preserve_speech?, output_format?, ducking?, variants_num?, prompt_influence?, output_directory?)` | Score a video: matches pacing/motion/emotion, matches the video's duration exactly. Returns audio only (the video itself is not muxed). |
| `video_to_video_music(video_path? \| video_url?, prompt?, segments?, keep_original_sound?, ducking?, preserve_speech?, variants_num?, prompt_influence?, output_directory?)` | Same scoring as `video_to_music`, but returns a **new `.mp4`** with the music already muxed in. **By default the source's own audio is dropped** — see `keep_original_sound`. |

## Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `prompt` | string | — | Required for `text_to_music` (1–1000 chars). Optional style hint for the video tools. |
| `duration` | int | — | `text_to_music` only. 1–360 seconds. |
| `video_path` | string | — | Absolute path, or relative to `SONILO_MCP_BASE_PATH`. `.mp4/.mov/.avi/.wmv/.webm/.mkv`. Max **360s (6 min)**, subject to the account's upload-size cap (typically 300 MB). |
| `video_url` | string | — | HTTPS URL to a video file. Exactly one of `video_path`/`video_url`. |
| `preserve_speech` | bool | `false` | `video_to_music`/`video_to_video_music` only. Keeps the source speech audible. On `video_to_music`, also returns a `vocals` speech stem and a ready-to-use `mux` (speech+music mixed) — this makes the call run asynchronously (submit + poll) instead of streaming, so it takes a bit longer but the tool still waits for completion. |
| `ducking` | bool \| null | server default ON for `video_to_music`, `false` for `video_to_video_music` | Dips the generated music under the source voice. Free, best-effort. On `video_to_video_music` it only does anything alongside `keep_original_sound` or `preserve_speech` — with neither, there is no source voice left in the output to duck under. |
| `keep_original_sound` | bool | `false` | `video_to_video_music` only. **This is the parameter to reach for when the result sounds wrong.** By default the returned `.mp4` carries the generated music *alone* — the source's dialogue, room tone, and effects are gone. Set `true` to keep the whole source track with the music mixed under it, and add `ducking=true` to dip the music under the voice rather than mixing it flat. `keep_original_sound` supersedes `preserve_speech`. |
| `variants_num` | int | `1` | 1–10. Generates that many distinct creative directions in one request — different takes, not re-renders of one. Available on `text_to_music`, `video_to_music` and `video_to_video_music`. **Cost scales linearly with the count, and any value above 1 is never covered by the free trial**, so confirm the number with the user first. Above 1 writes one file per variant and forces the backend's async mode. |
| `prompt_influence` | float \| null | API default `0.5` | `video_to_music`/`video_to_video_music` only. 0–1: how strictly the music follows your prompt versus what the video itself suggests. Lower lets the footage lead, higher enforces the brief. **Free**, and it does not change the mode or the number of files — omit it unless the user asks for stricter or looser adherence. |
| `output_format` | string | `m4a` | `text_to_music`/`video_to_music` only — `video_to_video_music` has no such param and always outputs a muxed `.mp4`. `m4a` or `wav`. `wav` (and, on `video_to_music`, `preserve_speech`/`ducking`) triggers the backend's async mode internally — no user-facing "mode" param needed. |
| `output_directory` | string | `SONILO_MCP_BASE_PATH` | Absolute, or relative to the base path. |

## Prompting

Two different situations:

- **`video_to_music`** — no prompt required; the model reads the cut. A short
  structured brief adds what the video can't carry: your intent — genre, the
  moment that must hit, the sounds that must not appear.
- **`text_to_music`** — the prompt IS the input; there is no video to lean on.
  The same craft vocabulary applies (genre, mood, energy arc, instrumentation,
  exclusions — see [prompting.md](./prompting.md)); skip the video pre-flight
  and describe structure in the prompt ("builds for 10 s, drops, outro").

Before a paid call: probe the exact duration and existing audio, respect the
**360 s** `video_to_music` cap (over = 422 reject, never truncated), and get
sign-off — failed runs auto-refund, but your own retry is a new charge.
Write the brief first, generate once, iterate on the prompt, not on rerolls.

- Full pre-flight (inspect the video, caps, credits, verification): [references/preflight.md](../references/preflight.md)
- Style-prompt craft (audio brief, genre/energy wording, `preserve_speech`, segmented music): [prompting.md](./prompting.md)

## Workflow Tips

- **Video-to-music is the flagship use case.** If the user has a finished video and wants a soundtrack, prefer `video_to_music` over `text_to_music` — the result is synced to the actual cut, not just a generic track of matching length.
- **Prompting:** describe genre, mood, tempo, and instrumentation. "A driving synthwave track with arpeggiated leads" beats "electronic music." For video scoring, prompt is optional — Sonilo already reads the footage — but a style hint (e.g. "cinematic, uplifting") steers the result.
- **`preserve_speech` for talking-head or narrated video:** if the source video has dialogue/voiceover the user wants kept, set `preserve_speech=true`. Behavior differs by tool: on `video_to_music` you get the music, the isolated speech stem, *and* a ready-mixed combined file (the mux) — use the mux directly rather than re-mixing yourself. On `video_to_video_music` there's no separate stem or mux file; `preserve_speech` just keeps the source speech audible in the single muxed output video.
- **Want the video back with the score baked in?** Use `video_to_video_music` instead of `video_to_music` — same inputs, but the output is a new `.mp4`, not just audio. **Warn the user that the source audio is dropped by default**: if their video has dialogue, narration, or effects they expect to hear, pass `keep_original_sound=true` (add `ducking=true` to keep the voice on top), or `preserve_speech=true` for the isolated speech only. A "the music is there but my voiceover vanished" report is always this.
- **Several takes in one go:** `variants_num=3` returns three distinct directions for one request instead of three re-rolls. It costs 3×, and it is never free-trial covered — say the price before calling.
- **Duration:** `text_to_music` needs an explicit `duration`; the video tools always match the source video's length automatically — don't ask for it.
- **Content restriction:** prompts cannot reference specific artists, bands, or copyrighted lyrics.

## Recovering a Timed-Out Call

`text_to_music` and `video_to_music` (without any of `preserve_speech`/`ducking`/`output_format="wav"`) stream their result in one call. Any variant that triggers the backend's async mode — and `video_to_video_music`, which is always async — can time out on a very long `TIME_OUT_SECONDS`. If it does, the error message includes a `task_id`; the generation keeps running (and is already charged) on the backend. Call `get_sfx_task(task_id)` — `get_generation_task(task_id)` on the hosted server — to retrieve the result once ready — see the [task-recovery](../task-recovery) skill.

## Output Files

- `text_to_music` / `video_to_music`: `.m4a` by default (`.wav` if requested), named from the prompt (slugified) or `sonilo-<timestamp>.m4a`. Multiple parallel streams get a `-<index>` suffix.
- `video_to_music(preserve_speech=true)`: also saves `<base>-vocals.<ext>` (isolated speech) and `<base>-mux.<ext>` (speech+music combined — the one to actually use).
- `video_to_video_music`: a single `.mp4` with the score muxed in.

## Error Handling

Common errors: `401` invalid key, `402` insufficient balance / trial exhausted, `413` file too large, `422` invalid parameters (e.g. duration out of range), `429` rate limit. See the [account](../account) skill to check trial/usage before a call, and the sonilo-mcp README's error table for exact recovery steps.
