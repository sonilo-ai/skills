---
name: text-to-music
description: Generate music from a text prompt using Sonilo — instrumental tracks, background beds, jingles, loops — when there is no video to score. Use when the user describes the music they want in words and gives a duration. Every track is licensed and cleared for commercial use. For scoring an existing video, use the video-to-music skill instead.
license: MIT
compatibility: "Requires Sonilo through either transport — the MCP server connected, or the `sonilo` CLI installed and signed in — plus credentials: a `sonilo login` sign-in, the hosted OAuth plugin, or SONILO_API_KEY. See the setup-api-key skill."
allowed-tools: Bash, Read, Write, mcp__sonilo__*
---

# Sonilo Text-to-Music

Generate music from a text description alone — no video involved. The prompt IS
the input, so the brief carries everything: genre, mood, energy arc,
instrumentation, and what must not appear. Every track is licensed (music
licensed via Shutterstock) and cleared for commercial use on social, brand
content, and advertising.

> **Setup:** See the [setup-api-key](../setup-api-key) skill to connect the Sonilo MCP server and authenticate — `sonilo login` (no key) or `SONILO_API_KEY`.

> ⚠️ **Cost:** this tool makes an API call that may incur charges. Only call it when the user has actually asked for a generation. Check `get_account_services` (see the [account](../account) skill) if you're unsure whether free-trial runs remain.

> **Scoring a video instead?** Use [video-to-music](../video-to-music) — it matches pacing, motion, and emotion to the actual cut, which a text prompt cannot do.

## Transport: MCP or CLI

Pick one at the start of the session and stay on it. Do not mix the two inside
a single job, and do not announce the choice.

1. **Sonilo MCP tools visible in this session** (`text_to_music` and friends) — use them. This is the preferred path: it needs no shell, and it is the only one that survives a very long generation. If a call fails to authenticate — rather than failing on its inputs — this transport is not usable in this session: go to 2 instead of retrying it.
2. **No usable Sonilo MCP tools, but `sonilo account` exits 0** — use the CLI commands below. Same API, same account, same credential file. Probe with `sonilo account`, not `sonilo whoami`: whoami exits 0 even when signed out, so it cannot tell the two states apart.
3. **Neither** — stop and run the [setup-api-key](../setup-api-key) skill. Do not call `api.sonilo.com` with curl to work around it; both transports handle uploads, polling and retries that a bare request does not.

## Quick Start

### MCP tool call (recommended)

```
text_to_music(
    prompt="A chill lo-fi hip hop beat with jazzy piano chords",
    duration=30
)
```

Saves the generated file(s) to `SONILO_MCP_BASE_PATH` (`~/Desktop` by default) and returns the saved path(s) as text.

### Python (`pip install sonilo`)

```python
from sonilo import Sonilo

client = Sonilo()  # reads SONILO_API_KEY

track = client.text_to_music.generate(prompt="A chill lo-fi hip hop beat with jazzy piano chords", duration=30)
track.save("output.mp3")
```

### JavaScript / TypeScript (`npm install sonilo`)

```ts
import { SoniloClient } from "sonilo";

const client = new SoniloClient(); // reads SONILO_API_KEY

const track = await client.textToMusic.generate({
  prompt: "A chill lo-fi hip hop beat with jazzy piano chords",
  duration: 30,
});
```

### CLI (`npm install -g sonilo-cli` or `pip install sonilo-cli`)

```bash
sonilo text-to-music --prompt "A chill lo-fi hip hop beat with jazzy piano chords" --duration 30
```

### cURL (raw REST API, no MCP host)

```bash
curl -X POST "https://api.sonilo.com/v1/text-to-music" \
  -H "Authorization: Bearer $SONILO_API_KEY" \
  --data-urlencode "prompt=A chill lo-fi hip hop beat with jazzy piano chords" \
  --data-urlencode "duration=30" \
  --output output.m4a
```

## Tool

| Tool | Description |
|------|-------------|
| `text_to_music(prompt, duration, output_format?, variants_num?, stems?, output_directory?)` | Generate music from a text description only — no video. |

## Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `prompt` | string | — | Required. 1–1000 chars. |
| `duration` | int | — | Required. 1–360 seconds. Unlike the video tools, there is no source to take the length from, so you must set it. |
| `variants_num` | int | `1` | 1–10. Generates that many distinct creative directions in one request — different takes, not re-renders of one. **Cost scales linearly with the count, and any value above 1 is never covered by the free trial**, so confirm the number with the user first. Above 1 writes one file per variant and forces the backend's async mode. |
| `output_format` | string | `m4a` | `m4a` or `wav`. `wav` triggers the backend's async mode internally — no user-facing "mode" param needed. |
| `stems` | bool | `false` | **Free.** Additionally splits each generated track into four separated instrument tracks — `drums`, `bass`, `vocals`, `other` — returned alongside the untouched full mix. Async-only on REST (`stems=true` without `mode=async` is a `400`). Live on REST and the **hosted** MCP server today; the local `sonilo-mcp` package does not accept it yet. See [Stems](#stems). |
| `output_directory` | string | `SONILO_MCP_BASE_PATH` | Absolute, or relative to the base path. |

## Stems

`stems=true` additionally returns each generated track split into four
separated instrument tracks — `drums`, `bass`, `vocals`, `other` — **free of
charge**. The full mix is untouched; the stems arrive alongside it in the task
result as a `stems` array next to `audio`:

```json
"stems": [
  {
    "stream_index": 0,
    "drums":  { "url": "…", "content_type": "audio/mp4", "file_size": 2913044 },
    "bass":   { "url": "…", "content_type": "audio/mp4", "file_size": 2870211 },
    "vocals": { "url": "…", "content_type": "audio/mp4", "file_size": 2794560 },
    "other":  { "url": "…", "content_type": "audio/mp4", "file_size": 3011830 }
  }
]
```

What matters when you use it:

- **Async only on REST.** `stems=true` requires `mode=async` (a `400` otherwise): you get a `202` + `task_id` and poll `/v1/tasks/{task_id}`. The MCP tools are always async, so on the hosted server the param just works.
- **Surfaces today: REST and the hosted MCP server.** The local `sonilo-mcp` package does not accept `stems` yet (its next release adds it), and the SDKs and CLIs don't expose it yet either — use the REST call or the hosted tool until they do.
- **Match stems to tracks by `stream_index`, never by array position.** A stream whose separation failed is simply absent, so `stems` can be shorter than `audio`.
- **`stems_error` is not a failed generation.** When separation failed wholly or partly, or was skipped, the task carries a `stems_error` string — possibly *alongside* a partial `stems` array. The generation itself succeeded and every `audio` URL is valid: treat missing stems as a missing extra, never as a reason to retry or refund.
- **Timing:** separation runs after generation finishes — typically another 2–6 min, giving up after 30 min (then `stems_error`).
- **The four stem names are fixed** (htdemucs separation): melodic instruments — piano, synths, guitar, strings — land in `other`, and on instrumental tracks `vocals` is near-silent. That is correct behavior, not a bug.
- **Formats:** stems normally follow `output_format`; trust each stem's `content_type` for what was actually delivered.

```bash
# REST: submit with stems, then poll the task
curl -X POST "https://api.sonilo.com/v1/text-to-music" \
  -H "Authorization: Bearer $SONILO_API_KEY" \
  --data-urlencode "prompt=A chill lo-fi hip hop beat with jazzy piano chords" \
  --data-urlencode "duration=30" \
  --data-urlencode "mode=async" \
  --data-urlencode "stems=true"
# → {"task_id": "…"} — poll GET /v1/tasks/{task_id} for audio + stems
```

## Prompting

The prompt is the only input — there is no footage to lean on. Describe genre,
mood, tempo, instrumentation, and the energy arc; "A driving synthwave track
with arpeggiated leads" beats "electronic music." Describe structure in words
too ("builds for 10 s, drops, outro"), since there is no cut to infer it from.
Name exclusions explicitly — the sounds that must not appear.

The same craft vocabulary applies as for video scoring, minus the video
pre-flight: [references/music-prompting.md](../references/music-prompting.md).

Generate once and iterate on the prompt, not on rerolls — failed runs
auto-refund, but your own retry is a new charge.

## Workflow Tips

- **If the user has a finished video, you are in the wrong skill.** [video-to-music](../video-to-music) syncs to the actual cut instead of producing a generic track of matching length.
- **Duration is required here.** Don't guess it — ask if the user hasn't said.
- **Several takes in one go:** `variants_num=3` returns three distinct directions for one request instead of three re-rolls. It costs 3×, and it is never free-trial covered — say the price before calling.
- **User wants the track's instruments as separate files** (to remix, re-balance, or drop one)? `stems=true` — it's free, but async-only and not on every surface yet; see [Stems](#stems).
- **Content restriction:** prompts cannot reference specific artists, bands, or copyrighted lyrics.

## Recovering a Timed-Out Call

`text_to_music` streams its result in one call unless `output_format="wav"`,
`variants_num` above 1, or `stems=true` triggers the backend's async mode. If an async variant
times out, the error message includes a `task_id`; the generation keeps running
(and is already charged) on the backend. Call `get_sfx_task(task_id)` —
`get_generation_task(task_id)` on the hosted server — to retrieve the result;
see the [task-recovery](../task-recovery) skill.

## Output Files

`.m4a` by default (`.wav` if requested), named from the prompt (slugified) or `sonilo-<timestamp>.m4a`. Multiple parallel streams get a `-<index>` suffix.

## Error Handling

Common errors: `401` invalid key, `402` insufficient balance / trial exhausted, `422` invalid parameters (e.g. duration out of range), `429` rate limit. See the [account](../account) skill to check trial/usage before a call.
