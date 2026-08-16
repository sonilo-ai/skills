---
name: video-to-sfx
description: Generate sound effects matched to a video using Sonilo — footsteps, impacts, ambience, foley — optionally scripted to specific timed segments, returning either the audio or a new video with the SFX muxed in. Use when the user has footage that needs sound design. For SFX from a text description alone, use the text-to-sfx skill; for music, use video-to-music.
license: MIT
compatibility: "Requires Sonilo through either transport — the MCP server connected, or the `sonilo` CLI installed and signed in — plus credentials: a `sonilo login` sign-in, the hosted OAuth plugin, or SONILO_API_KEY. See the setup-api-key skill."
allowed-tools: Bash, Read, Write, mcp__sonilo__*
---

# Sonilo Video-to-SFX

Hand Sonilo a video and it generates sound effects matching what it sees —
footsteps, impacts, ambience, UI sounds, whatever the scene calls for — or pin
specific sounds to specific moments with `segments`. Generation runs as an async
task on the backend; the tools poll internally and hand back the saved file.

> **Setup:** See the [setup-api-key](../setup-api-key) skill.

> ⚠️ **Cost:** every tool below makes an API call that may incur charges. Only call it when explicitly requested.

## Transport: MCP or CLI

Pick one at the start of the session and stay on it. Do not mix the two inside
a single job, and do not announce the choice.

1. **Sonilo MCP tools visible in this session** (`video_to_sfx` and friends) — use them. This is the preferred path: it needs no shell, and it is the only one that survives a very long generation. If a call fails to authenticate — rather than failing on its inputs — this transport is not usable in this session: go to 2 instead of retrying it.
2. **No usable Sonilo MCP tools, but `sonilo account` exits 0** — use the CLI commands below. Same API, same account, same credential file. Probe with `sonilo account`, not `sonilo whoami`: whoami exits 0 even when signed out, so it cannot tell the two states apart.
3. **Neither** — stop and run the [setup-api-key](../setup-api-key) skill. Do not call `api.sonilo.com` with curl to work around it; both transports handle uploads, polling and retries that a bare request does not.

## Quick Start

### MCP tool call (recommended)

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

foley = client.video_to_sfx.generate(video="action-scene.mp4", prompt="Footsteps on gravel, distant traffic, a door slam")
foley.save("foley.wav")

# video_to_video_sfx: get the video back with the effects muxed in
video = client.video_to_video_sfx.generate(video="action-scene.mp4", segments=[{"start": 0, "end": 2, "prompt": "footsteps on gravel"}])
video.save("with_sfx.mp4")
```

### JavaScript / TypeScript (`npm install sonilo`)

```ts
import { SoniloClient } from "sonilo";

const client = new SoniloClient(); // reads SONILO_API_KEY

const foley = await client.videoToSfx.generate({
  video: "./action-scene.mp4",
  prompt: "Footsteps on gravel, distant traffic, a door slam",
});

// video_to_video_sfx: get the video back with the effects muxed in
const video = await client.videoToVideoSfx.generate({
  video: "./action-scene.mp4",
  segments: [{ start: 0, end: 2, prompt: "footsteps on gravel" }],
});
```

### CLI (`npm install -g sonilo-cli` or `pip install sonilo-cli`)

```bash
sonilo video-to-sfx --video action-scene.mp4 --output foley.wav
```

Always async under the hood — the CLI submits and polls for you. `--format` accepts `wav|mp3|aac|flac`.

```bash
# the muxed video, from the CLI
sonilo video-to-video-sfx --video clip.mp4 --prompt "footsteps, distant thunder" --output foley.mp4
```

### cURL (raw REST API, no MCP host)

```bash
curl -X POST "https://api.sonilo.com/v1/video-to-sfx" \
  -H "Authorization: Bearer $SONILO_API_KEY" \
  -F "video=@action-scene.mp4" \
  -F "prompt=Footsteps on gravel, distant traffic, a door slam"
# -> {"task_id": "..."}  poll GET /v1/tasks/{task_id} until status is succeeded/failed
```

Every call is task-based: the endpoint returns `{"task_id": ...}` (HTTP 202), and the result is fetched from `GET /v1/tasks/{task_id}` once `status` is terminal. The MCP tools do this polling for you and return the saved path directly — you only see the `task_id` if the call times out (see [task-recovery](../task-recovery)).

## Tools

| Tool | Description |
|------|-------------|
| `video_to_sfx(video_path? \| video_url?, prompt?, segments?, audio_format?, output_directory?)` | Generate SFX matched to a video. Returns **audio only** (not the source video). |
| `video_to_video_sfx(video_path? \| video_url?, prompt?, segments?, output_directory?)` | Same, but returns a **new `.mp4`** with the SFX muxed in. |

## Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `prompt` | string | — | Optional overall description (max 2000 chars) — omit it to let Sonilo interpret the video on its own. |
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

## Prompting

No prompt is required — the model reads the cut. Quality comes from a
time-segmented action map: what is on screen, what it's made of, what it does,
second by second. The footage is the source of truth.

Before a paid call: probe the exact duration and existing audio, respect the
**180 s** cap (over = 422 reject, never truncated), and get sign-off — failed
runs auto-refund, but your own retry is a new charge.

- Full pre-flight (inspect the video, caps, credits, verification): [references/preflight.md](../references/preflight.md)
- Action-map craft (scene bed, sound bundles, materials vocabulary, segment rules): [references/sfx-prompting.md](../references/sfx-prompting.md)

## Workflow Tips

- **Leave `prompt`/`segments` unset** to let Sonilo read the whole video and decide; use `segments` when you need specific sounds pinned to specific moments (e.g. a punch landing at 2.3s, a door slam at 5.0s).
- **Want the video back with SFX baked in?** Use `video_to_video_sfx` instead of `video_to_sfx`.
- **Prompting:** be specific and combine elements — "Heavy rain on a tin roof" beats "Rain".
- **Don't confuse this with music.** For a background score or soundtrack, use [video-to-music](../video-to-music) instead. To generate both music and SFX together in one balanced, single-charge call, use [video-to-sound](../video-to-sound).
- **No footage?** [text-to-sfx](../text-to-sfx) generates a single clip from a description alone.

## Recovering a Timed-Out Call

Every tool here is async on the backend already; a long generation can still exceed `TIME_OUT_SECONDS`. If it does, the error carries a `task_id` — the job keeps running (and is already charged). Call `get_sfx_task(task_id)` — `get_generation_task(task_id)` on the hosted server — later to retrieve the result; see [task-recovery](../task-recovery).

## Output Files

- `video_to_sfx`: saved in the requested `audio_format` (`.wav`/`.mp3`/`.flac`, or `.m4a` for the `aac` default), named from the prompt (slugified) or `sfx-<first 8 chars of the task id>`.
- `video_to_video_sfx`: a single `.mp4` with the SFX muxed in.

## Error Handling

Common errors: `401` invalid key, `402` insufficient balance / trial exhausted, `413` file too large, `422` invalid parameters or malformed `segments`, `429` rate limit. See the [account](../account) skill.
