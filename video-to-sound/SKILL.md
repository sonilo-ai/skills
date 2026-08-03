---
name: video-to-sound
description: Generate music AND sound effects for a video in a single balanced, single-charge call using Sonilo. Use instead of calling the music and sound-effects skills separately for the same video — the two layers are mixed and ducked against each other by the backend. Returns a mixed audio track, or a new video with it muxed in.
license: MIT
compatibility: Requires the Sonilo MCP server connected and a Sonilo API key (SONILO_API_KEY).
---

# Sonilo Video-to-Sound (Music + SFX Combined)

Generate a music bed and sound effects for a video in one call, balanced against each other and mixed by the backend — one charge instead of two separate generations. Use this whenever a video needs a **full soundtrack** (score + SFX), not just one or the other.

> **Setup:** See the [setup-api-key](../setup-api-key) skill.

> ⚠️ **Cost:** makes one API call that may incur charges (billed once, not twice, even though it produces both layers). Only call when explicitly requested.

## Quick Start

### MCP tool call (recommended)

```
video_to_sound(
    video_path="~/Desktop/trailer.mp4",
    music_prompt="Cinematic, building tension",
    sfx_prompt="Footsteps, wind, distant thunder"
)
```

```
video_to_video_sound(
    video_path="~/Desktop/trailer.mp4",
    music_prompt="Cinematic, building tension"
)
```

### Python (`pip install sonilo`)

```python
from sonilo import Sonilo

client = Sonilo()  # reads SONILO_API_KEY

mix = client.video_to_sound.generate(
    video="trailer.mp4",
    music_prompt="Cinematic, building tension",
    sfx_prompt="Footsteps, wind, distant thunder",
)
mix.save("soundtrack.wav")

video = client.video_to_video_sound.generate(video="trailer.mp4", music_prompt="Cinematic, building tension")
video.save("scored.mp4")
```

### JavaScript / TypeScript (`npm install sonilo`)

```ts
import { SoniloClient, download } from "sonilo";
import { writeFile } from "node:fs/promises";

const client = new SoniloClient(); // reads SONILO_API_KEY

const mix = await client.videoToSound.generate({
  video: "./trailer.mp4",
  musicPrompt: "Cinematic, building tension",
  sfxPrompt: "Footsteps, wind, distant thunder",
});
await writeFile("soundtrack.wav", await download(mix.output_url));

const video = await client.videoToVideoSound.generate({
  video: "./trailer.mp4",
  musicPrompt: "Cinematic, building tension",
});
await writeFile("scored.mp4", await download(video.output_url));
```

### CLI (`npm install -g sonilo-cli` or `pip install sonilo-cli`)

```bash
sonilo video-to-sound --video trailer.mp4 \
  --music-prompt "Cinematic, building tension" --sfx-prompt "Footsteps, wind, distant thunder" \
  --output soundtrack.wav

sonilo video-to-video-sound --video trailer.mp4 --music-prompt "Cinematic, building tension"
```

Unlike the music/sound-effects skills, **both tools here have CLI commands**. `--stem music`/`--stem sfx` (repeatable) additionally saves the individual layers next to the combined output.

### cURL (raw REST API, no MCP host)

```bash
curl -X POST "https://api.sonilo.com/v1/video-to-sound" \
  -H "Authorization: Bearer $SONILO_API_KEY" \
  -F "video=@trailer.mp4" \
  -F "music_prompt=Cinematic, building tension" \
  -F "sfx_prompt=Footsteps, wind, distant thunder"
# -> {"task_id": "..."}  poll GET /v1/tasks/{task_id}
```

Both endpoints are task-based (202 + poll), same as the sound-effects tools — the MCP tool waits for you.

## Tools

| Tool | Description |
|------|-------------|
| `video_to_sound(video_path? \| video_url?, music_prompt?, sfx_prompt?, segments?, preserve_speech?, ducking?, output_directory?)` | Generate and mix music + SFX for a video, returns a single **audio** file. |
| `video_to_video_sound(video_path? \| video_url?, music_prompt?, sfx_prompt?, segments?, preserve_speech?, ducking?, output_directory?)` | Same, but returns a **new `.mp4`** with the mixed soundtrack muxed in. |

## Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `video_path` | string | — | `.mp4/.mov/.webm/.m4v/.gif` (gif must be animated). Max **180s (3 min)**, subject to the account's upload-size cap. |
| `video_url` | string | — | HTTPS/HTTP URL. Exactly one of `video_path`/`video_url`. |
| `music_prompt` | string | — | Style hint for the music bed (max 2000 chars). Optional — omit to let Sonilo decide. |
| `sfx_prompt` | string | — | Description of the SFX layered over the music (max 2000 chars). Optional. |
| `segments` | list[dict] | — | Per-segment SFX descriptions — same schema and validation rules as in the [sound-effects](../sound-effects) skill. Max 30 segments. |
| `preserve_speech` | bool | `false` | Keep the source video's speech audible in the mix. |
| `ducking` | bool | `true` | Dips the generated music (and SFX bed) under the source speech. Defaults **on** here — pass `false` to opt out. |
| `output_directory` | string | `SONILO_MCP_BASE_PATH` | Absolute, or relative to the base path. |

## Prompting

No prompt is required — the model reads the cut. A short structured brief
adds your intent on top. Since this endpoint generates music **and** SFX in
one balanced call, both crafts apply:

- Pre-flight (inspect the video, caps, credits, verification): [references/preflight.md](../references/preflight.md)
- Music brief craft: [music/prompting.md](../music/prompting.md) · SFX action-map craft: [sound-effects/prompting.md](../sound-effects/prompting.md)

## Workflow Tips

- **Use this instead of chaining `video_to_music` + `video_to_sfx`.** The two layers are balanced against each other by the backend (so the SFX doesn't fight the score), and it's one charge, not two.
- Both `music_prompt` and `sfx_prompt` are optional — you can leave both unset and let Sonilo interpret the whole scene, or set just one to steer that layer while leaving the other automatic.
- `ducking` defaults to **on** here (unlike the standalone `audio_ducking` tool, which you'd have to call explicitly) — leave it on for any video with dialogue or narration so the soundtrack doesn't drown it out.
- Only the **combined mixed result** is saved. The individual music/SFX/processed stems exist in the task body on the backend but are deliberately not downloaded — four files per call would bury the one the user actually wants. If stems are needed, call the REST API directly and inspect the task body.
- Want the video back with the soundtrack baked in? Use `video_to_video_sound` instead of `video_to_sound`.

## Recovering a Timed-Out Call

Both tools are async; on timeout the error carries a `task_id` and the job keeps running (already charged). Call `get_sfx_task(task_id)` later — see [task-recovery](../task-recovery).

## Output Files

- `video_to_sound`: a single `.wav`, named from `music_prompt` (falling back to `sfx_prompt`, then `sound-<first 8 chars of the task id>`).
- `video_to_video_sound`: a single `.mp4` with the mix muxed in, named the same way (fallback `v2v-sound-<first 8 chars of the task id>`).

## Error Handling

Common errors: `401` invalid key, `402` insufficient balance / trial exhausted, `413` file too large, `422` invalid parameters or malformed `segments`, `429` rate limit. See the [account](../account) skill.
