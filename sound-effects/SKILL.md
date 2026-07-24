---
name: sound-effects
description: Generate sound effects using Sonilo. Use when creating SFX from a text description, generating SFX matched to what happens in a video (optionally scripted to specific timed segments), or muxing SFX into a video. Not for music — see the music skill.
license: MIT
compatibility: Requires the Sonilo MCP server connected and a Sonilo API key (SONILO_API_KEY).
---

# Sonilo Sound Effects

Generate sound effects from a text description, or hand Sonilo a video and it generates SFX matching what it sees — footsteps, impacts, ambience, UI sounds, whatever the scene calls for. All generation runs as an async task on the backend; the tools poll internally and hand back the saved file.

> **Setup:** See the [setup-api-key](../setup-api-key) skill.

> ⚠️ **Cost:** every tool below makes an API call that may incur charges. Only call it when explicitly requested.

## Quick Start

### MCP tool call (recommended)

```
text_to_sfx(
    prompt="Thunder rumbling in the distance with light rain",
    duration=6
)
```

```
video_to_sfx(
    video_path="~/Desktop/action-scene.mp4",
    prompt="Footsteps on gravel, distant traffic, a door slam"
)
```

### Python (`pip install sonilo`)

```python
from sonilo import Sonilo

client = Sonilo()  # reads SONILO_API_KEY

sfx = client.text_to_sfx.generate(prompt="Thunder rumbling in the distance with light rain", duration=6)
sfx.save("thunder.m4a")

foley = client.video_to_sfx.generate(video="action-scene.mp4", prompt="Footsteps on gravel, distant traffic, a door slam")
foley.save("foley.wav")

# video_to_video_sfx has no CLI command — this is the only non-MCP way to get the muxed video back
video = client.video_to_video_sfx.generate(video="action-scene.mp4", segments=[{"start": 0, "end": 2, "prompt": "footsteps on gravel"}])
video.save("with_sfx.mp4")
```

### JavaScript / TypeScript (`npm install sonilo`)

```ts
import { SoniloClient } from "sonilo";

const client = new SoniloClient(); // reads SONILO_API_KEY

const sfx = await client.textToSfx.generate({
  prompt: "Thunder rumbling in the distance with light rain",
  duration: 6,
});

const foley = await client.videoToSfx.generate({
  video: "./action-scene.mp4",
  prompt: "Footsteps on gravel, distant traffic, a door slam",
});

// video_to_video_sfx has no CLI command — this is the only non-MCP way to get the muxed video back
const video = await client.videoToVideoSfx.generate({
  video: "./action-scene.mp4",
  segments: [{ start: 0, end: 2, prompt: "footsteps on gravel" }],
});
```

### CLI (`npm install -g sonilo-cli` or `pip install sonilo-cli`)

```bash
sonilo text-to-sfx --prompt "Thunder rumbling in the distance with light rain" --duration 6
sonilo video-to-sfx --video action-scene.mp4 --output foley.wav
```

Both are always async under the hood — the CLI submits and polls for you. `--format` accepts `wav|mp3|aac|flac`. **There is no CLI command for `video_to_video_sfx`** (the video-to-video variants aren't exposed by either CLI) — use the Python/JS SDK or the MCP tool for that.

### cURL (raw REST API, no MCP host)

```bash
curl -X POST "https://api.sonilo.com/v1/text-to-sfx" \
  -H "Authorization: Bearer $SONILO_API_KEY" \
  --data-urlencode "prompt=Thunder rumbling in the distance with light rain" \
  --data-urlencode "duration=6"
# -> {"task_id": "..."}  poll GET /v1/tasks/{task_id} until status is succeeded/failed
```

```bash
curl -X POST "https://api.sonilo.com/v1/video-to-sfx" \
  -H "Authorization: Bearer $SONILO_API_KEY" \
  -F "video=@action-scene.mp4" \
  -F "prompt=Footsteps on gravel, distant traffic, a door slam"
```

Every SFX call is task-based: the endpoint returns `{"task_id": ...}` (HTTP 202), and the result is fetched from `GET /v1/tasks/{task_id}` once `status` is terminal. The MCP tools do this polling for you and return the saved path directly — you only see the `task_id` if the call times out (see [task-recovery](../task-recovery)).

## Tools

| Tool | Description |
|------|-------------|
| `text_to_sfx(prompt, duration, audio_format?, output_directory?)` | Generate one SFX clip from a text description only. |
| `video_to_sfx(video_path? \| video_url?, prompt?, segments?, audio_format?, output_directory?)` | Generate SFX matched to a video. Returns **audio only** (not the source video). |
| `video_to_video_sfx(video_path? \| video_url?, prompt?, segments?, output_directory?)` | Same as `video_to_sfx`, but returns a **new `.mp4`** with the SFX muxed in. |

## Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `prompt` | string | — | Required for `text_to_sfx` (1–2000 chars). Overall description for the video tools (optional, max 2000 chars) — omit it to let Sonilo interpret the video on its own. |
| `duration` | int | — | `text_to_sfx` only. 1–180 seconds. |
| `video_path` | string | — | `.mp4/.mov/.webm/.m4v/.gif` (gif must be animated) — a narrower set than the music tools. Max **180s (3 min)**, subject to the account's upload-size cap. |
| `video_url` | string | — | HTTPS/HTTP URL to a video. Exactly one of `video_path`/`video_url`. |
| `segments` | list[dict] | — | Script SFX to specific time ranges: `[{"start": float, "end": float, "prompt": str}, ...]`. See rules below. Max 30 segments. |
| `audio_format` | string | `aac` (`.m4a`) | `wav`, `mp3`, `aac`, or `flac`. `video_to_sfx` only (video-to-video always outputs `.mp4`). |
| `output_directory` | string | `SONILO_MCP_BASE_PATH` | Absolute, or relative to the base path. |

### `segments` rules

Validated by the backend before any charge — an invalid list is rejected with a 422/400 and nothing is billed:

- First segment's `start` must be `0`.
- Segments must be contiguous: each `end` must equal the next segment's `start`.
- Every `end` must be greater than its `start`.
- Every `prompt` must be non-empty, max 200 chars.
- The last `end` must not exceed the video's actual duration.
- Max 30 segments total.

## Workflow Tips

- **Text-only SFX** (`text_to_sfx`) is for a single clip with no video context — a UI chime, a whoosh, a foley element you'll layer yourself.
- **Video-driven SFX** (`video_to_sfx` / `video_to_video_sfx`) is for matching sound design to an actual scene. Leave `prompt`/`segments` unset to let Sonilo read the whole video and decide; use `segments` when you need specific sounds pinned to specific moments (e.g. a punch landing at 2.3s, a door slam at 5.0s).
- **Want the video back with SFX baked in?** Use `video_to_video_sfx` instead of `video_to_sfx`.
- **Prompting:** be specific and combine elements — "Heavy rain on a tin roof" beats "Rain"; "Cinematic braam, horror" or "8-bit retro jump sound" for stylized cues.
- **Don't confuse this with music.** For a background score or soundtrack, use the [music](../music) skill instead. To generate both music and SFX together in one balanced, single-charge call, use [video-to-sound](../video-to-sound).

## Recovering a Timed-Out Call

Every tool here is async on the backend already; a long generation can still exceed `TIME_OUT_SECONDS`. If it does, the error carries a `task_id` — the job keeps running (and is already charged). Call `get_sfx_task(task_id)` later to retrieve the result; see [task-recovery](../task-recovery).

## Output Files

- `text_to_sfx` / `video_to_sfx`: saved in the requested `audio_format` (`.wav`/`.mp3`/`.flac`, or `.m4a` for the `aac` default), named from the prompt (slugified) or `sfx-<first 8 chars of the task id>`.
- `video_to_video_sfx`: a single `.mp4` with the SFX muxed in.

## Error Handling

Common errors: `401` invalid key, `402` insufficient balance / trial exhausted, `413` file too large, `422` invalid parameters or malformed `segments`, `429` rate limit. See the [account](../account) skill.
