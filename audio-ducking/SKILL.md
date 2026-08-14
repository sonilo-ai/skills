---
name: audio-ducking
description: Duck a music bed under a voice track using Sonilo — automatically lowers the music wherever the voice speaks and lifts it back in the gaps. Use when mixing a separately-generated or existing music track under narration, dialogue, or a video's own voice track, without manual volume automation.
license: MIT
compatibility: Requires Sonilo through either transport — the MCP server connected, or the `sonilo` CLI installed and signed in — plus credentials: a `sonilo login` sign-in, the hosted OAuth plugin, or SONILO_API_KEY. See the setup-api-key skill.
allowed-tools: Bash, Read, Write, mcp__sonilo__*
---

# Sonilo Audio Ducking

Automatically duck a music bed under a voice track: Sonilo lowers the music wherever the voice is speaking and lifts it back in the gaps, then returns the mixed result. The voice input may be a video — its audio track is used as the voice, and the ducked mix is muxed back into a new video.

> **Setup:** See the [setup-api-key](../setup-api-key) skill.

> ⚠️ **Cost:** makes an API call that may incur charges. Only call when explicitly requested.

## Transport: MCP or CLI

Pick one at the start of the session and stay on it. Do not mix the two inside
a single job, and do not announce the choice.

1. **Sonilo MCP tools visible in this session** (`audio_ducking` and friends) — use them. This is the preferred path: it needs no shell, and it is the only one that survives a very long generation. If a call fails to authenticate — rather than failing on its inputs — this transport is not usable in this session: go to 2 instead of retrying it.
2. **No usable Sonilo MCP tools, but `sonilo account` exits 0** — use the CLI commands below. Same API, same account, same credential file. Probe with `sonilo account`, not `sonilo whoami`: whoami exits 0 even when signed out, so it cannot tell the two states apart.
3. **Neither** — stop and run the [setup-api-key](../setup-api-key) skill. Do not call `api.sonilo.com` with curl to work around it; both transports handle uploads, polling and retries that a bare request does not.

## Quick Start

### MCP tool call (recommended)

```
audio_ducking(
    voice_path="~/Desktop/interview.mp4",
    music_path="~/Desktop/background-track.wav"
)
```

### Python (`pip install "sonilo>=0.13"`)

```python
from sonilo import Sonilo

client = Sonilo()  # reads SONILO_API_KEY

result = client.audio_ducking.generate(
    voice="interview.mp4",  # audio or video; also voice_url=
    music="background-track.wav",  # audio only; also music_url=
)
result.save("ducked.mp4" if result.output_type == "video" else "ducked.wav")
```

### JavaScript / TypeScript (`npm install sonilo@>=0.14`)

```ts
import { SoniloClient, download } from "sonilo";
import { writeFile } from "node:fs/promises";

const client = new SoniloClient(); // reads SONILO_API_KEY

const result = await client.audioDucking.generate({
  voice: "./interview.mp4", // audio or video; also voiceUrl
  musicUrl: "https://example.com/background-track.wav", // audio only; also music
});
await writeFile(
  result.output_type === "video" ? "ducked.mp4" : "ducked.wav",
  await download(result.output_url!),
);
```

### CLI (`npm install -g sonilo-cli` or `pip install sonilo-cli`)

```bash
sonilo audio-ducking --voice interview.mp4 --music-url https://example.com/background-track.wav
```

Always async under the hood — the CLI submits and polls for you. Exactly one of `--voice`/`--voice-url` and one of `--music`/`--music-url`. The default output name follows what comes back (`output.wav`, or `output.mp4` when the voice input was a video); `--output` overrides it. A local `--music` file must have an audio extension — the CLI rejects a video there up front, for the same reason the MCP tool does.

### cURL (raw REST API, no MCP host)

```bash
curl -X POST "https://api.sonilo.com/v1/audio-ducking" \
  -H "Authorization: Bearer $SONILO_API_KEY" \
  -F "voice_file=@interview.mp4" \
  -F "music_file=@background-track.wav"
# -> {"task_id": "..."}  poll GET /v1/tasks/{task_id}
```

A local file uses the `voice_file`/`music_file` multipart fields; a remote source uses `voice_url`/`music_url` form fields instead (mix and match freely between the two inputs).

## Tool

| Tool | Description |
|------|-------------|
| `audio_ducking(voice_path? \| voice_url?, music_path? \| music_url?, output_directory?)` | Mix `music` under `voice`, ducking automatically wherever the voice speaks. |

## Parameters

| Parameter | Type | Notes |
|-----------|------|-------|
| `voice_path` | string | Absolute path, or relative to `SONILO_MCP_BASE_PATH`. **Audio or video**: `.wav/.mp3/.m4a/.aac/.ogg/.flac` or `.mp4/.mov/.avi/.wmv/.webm/.mkv`. |
| `voice_url` | string | HTTPS URL to the voice audio/video. Exactly one of `voice_path`/`voice_url`. |
| `music_path` | string | Absolute path, or relative to the base path. **Audio only** — a video here is not treated specially and will be mishandled. |
| `music_url` | string | HTTPS URL to the music audio. Exactly one of `music_path`/`music_url`. |
| `output_directory` | string | Defaults to `SONILO_MCP_BASE_PATH`. |

Each input is capped at **360 seconds (6 minutes)** and by the account's upload-size limit (typically 300 MB).

## Workflow Tips

- **This tool takes two already-existing tracks** — it does not generate music or SFX itself. If you need to generate the music bed first, use the [text-to-music](../text-to-music) or [video-to-music](../video-to-music) skill (`text_to_music`/`video_to_music`), then feed the result in here as `music_path`.
- **The voice input can be a video.** If the user hands you a talking-head clip or an interview and a separate music file, pass the video straight through as `voice_path` — Sonilo extracts its audio track, ducks the music under it, and re-muxes the ducked mix back into a new video automatically.
- **Prefer [video-to-sound](../video-to-sound) or `video_to_music(ducking=true)`** when the music itself is also being *generated* for that same video — those tools duck internally as part of generation, so you don't need a separate ducking call. Reach for `audio_ducking` specifically when the music track is fixed/external and you just need the mix.

## Recovering a Timed-Out Call

This tool submits an async task on the backend. If the call times out, the error carries a `task_id` — the job keeps running (already charged). Call `get_sfx_task(task_id)` later (`get_generation_task(task_id)` on the hosted server); see [task-recovery](../task-recovery).

## Output Files

A single file: a `.wav` if the voice input was audio, or a `.mp4` (ducked mix re-muxed in) if the voice input was a video. Named after the voice input (e.g. `interview.mp4` → `interview-ducked.mp4`), falling back to `ducked-<first 8 chars of the task id>`.

## Error Handling

Common errors: `401` invalid key, `402` insufficient balance / trial exhausted, `413` file too large, `422` invalid parameters, `429` rate limit. See the [account](../account) skill.
