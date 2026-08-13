---
name: audio-ducking
description: Duck a music bed under a voice track using Sonilo — automatically lowers the music wherever the voice speaks and lifts it back in the gaps. Use when mixing a separately-generated or existing music track under narration, dialogue, or a video's own voice track, without manual volume automation.
license: MIT
compatibility: Requires the Sonilo MCP server connected and Sonilo credentials — either a `sonilo login` sign-in, the hosted OAuth plugin, or SONILO_API_KEY. See the setup-api-key skill.
---

# Sonilo Audio Ducking

Automatically duck a music bed under a voice track: Sonilo lowers the music wherever the voice is speaking and lifts it back in the gaps, then returns the mixed result. The voice input may be a video — its audio track is used as the voice, and the ducked mix is muxed back into a new video.

> **Setup:** See the [setup-api-key](../setup-api-key) skill.

> ⚠️ **Cost:** makes an API call that may incur charges. Only call when explicitly requested.

## Quick Start

### MCP tool call (recommended)

```
audio_ducking(
    voice_path="~/Desktop/interview.mp4",
    music_path="~/Desktop/background-track.wav"
)
```

### Python / JavaScript — no dedicated SDK method

Unlike every other tool in this repo, `audio_ducking` has **no dedicated resource** in either official SDK (no `client.audio_ducking` in Python, no `client.audioDucking` in JS) and **no CLI command**. Reach for one of these instead:

- **`sonilo-video-kit`'s `duck_music_under_speech()` / `duckMusicUnderSpeech()`** — the closest equivalent, but a different shape: it takes a video plus already-generated audio *bytes* (not two file paths/URLs) and calls this same ducking API internally, then re-muxes the result into a new video. See [sonilo-video-kit (Python)](https://github.com/sonilo-ai/sonilo-python/tree/main/sonilo-video-kit) / [sonilo-video-kit (JS)](https://github.com/sonilo-ai/sonilo-js/tree/main/packages/sonilo-video-kit).
- **The JS SDK's generic `client.request()` escape hatch** — calls the raw endpoint directly with the same params as the MCP tool:

  ```ts
  import { SoniloClient } from "sonilo";

  const client = new SoniloClient(); // reads SONILO_API_KEY
  const res = await client.request("/v1/audio-ducking", {
    method: "POST",
    body: (() => {
      const form = new FormData();
      form.set("voice_url", "https://example.com/interview.mp4");
      form.set("music_url", "https://example.com/background-track.wav");
      return form;
    })(),
  });
  const { task_id } = await res.json();
  ```

  The Python SDK has no public equivalent of `client.request()` — call the REST endpoint directly with `httpx`/`requests` instead (see cURL below for the exact form fields).

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
