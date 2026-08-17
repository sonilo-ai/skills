---
name: video-analysis
description: Analyze a video with Sonilo and get back a creative brief for scoring it — a time-aligned section plan plus one or more ready-to-use generation prompts, derived from the footage itself. Use when the user has a video that needs sound but nobody knows yet what it should sound like, or when a first generation missed and you need a better prompt rather than another reroll. Generates no audio and no video; the output is text you feed into video-to-music, video-to-sfx, or video-to-sound.
license: MIT
compatibility: "Requires Sonilo through either transport — the MCP server connected, or the `sonilo` CLI installed and signed in — plus credentials: a `sonilo login` sign-in, the hosted OAuth plugin, or SONILO_API_KEY. See the setup-api-key skill."
allowed-tools: Bash, Read, Write, mcp__sonilo__*
---

# Sonilo Video Analysis

Hand Sonilo a video and it returns a **creative brief** for scoring it: a
time-aligned `segments` plan (what each stretch of footage wants) plus one or
more `variations`, each a single ready-to-use generation prompt.

This skill **generates nothing**. No audio, no video, no file. Its whole
output is text, and the text is the input to the next call.

> **Setup:** See the [setup-api-key](../setup-api-key) skill to connect the Sonilo MCP server and authenticate — `sonilo login` (no key) or `SONILO_API_KEY`.

> ⚠️ **Cost:** this is a paid call, even though nothing is generated. Billing has a 10-second floor and `variants_num` is billed per brief, so 3 variations cost 3×. Only call it when the user has actually asked. Check `get_account_services` (see the [account](../account) skill) if you're unsure whether free-trial runs remain.

## When to reach for this

Use it when:

- **The user doesn't know what the video should sound like.** "Make this sound good" is not a prompt. Analyze first, show them the variations, let them pick.
- **A first generation missed.** A bad result usually means a bad brief, not a bad model. Analyzing beats rerolling: a reroll is a fresh charge on the same weak prompt.
- **The video has distinct sections** and you want them scored deliberately rather than as one continuous bed. `segments` gives you the section boundaries the footage actually has.

Do **not** use it when the user already told you what they want. If they said
"tense synths, drop at the 20-second mark", go straight to
[video-to-music](../video-to-music) — analysis would just be an extra charge
between them and their track.

## Transport: MCP or CLI

Pick one at the start of the session and stay on it. Do not mix the two inside
a single job, and do not announce the choice.

1. **Sonilo MCP tools visible in this session** (`analyze_video` and friends) — use them. This is the preferred path: it needs no shell, and it is the only one that survives a very long generation. If a call fails to authenticate — rather than failing on its inputs — this transport is not usable in this session: go to 2 instead of retrying it.
2. **No usable Sonilo MCP tools, but `sonilo account` exits 0** — use the CLI commands below. Same API, same account, same credential file. Probe with `sonilo account`, not `sonilo whoami`: whoami exits 0 even when signed out, so it cannot tell the two states apart.
3. **Neither** — stop and run the [setup-api-key](../setup-api-key) skill. Do not call `api.sonilo.com` with curl to work around it; both transports handle uploads, polling and retries that a bare request does not.

### One difference between the two MCP servers

`analyze_video` takes a **local file only on the local server**. The hosted
(OAuth plugin) server is URL-only: it exposes `video_url` and nothing else. If
the user's video is a local file and you are on the hosted server, use the CLI
or an SDK instead of trying `video_path` — it is not a parameter there.

## Quick Start

### MCP tool call (recommended)

```
analyze_video(
    video_path="~/Desktop/trailer.mp4",
    prompt="focus on the chase",
    variants_num=2
)
```

Returns the brief inline as JSON. **Nothing is saved to disk** — unlike every
other Sonilo tool, there is no output path, because there is no file.

On the hosted server, pass `video_url` instead of `video_path`.

### Python (`pip install sonilo`)

```python
from sonilo import Sonilo

client = Sonilo()  # reads SONILO_API_KEY

brief = client.video_analysis.analyze(
    video="trailer.mp4",
    prompt="focus on the chase",
    variants_num=2,
)

for segment in brief.segments:
    print(f"{segment.start}-{segment.end}s [{segment.label}] {segment.prompt}")

# Feed a variation's prompt straight into a generation call.
score = client.video_to_music.generate(
    video="trailer.mp4", prompt=brief.variations[0].prompt
)
score.save("score.m4a")
```

The method is `analyze()`, not `generate()`, and the result has no `save()` —
there is nothing to download.

### JavaScript / TypeScript (`npm install sonilo`)

```ts
import { SoniloClient } from "sonilo";

const client = new SoniloClient(); // reads SONILO_API_KEY

const brief = await client.videoAnalysis.analyze({
  video: "./trailer.mp4",
  prompt: "focus on the chase",
  variantsNum: 2,
});

const score = await client.videoToMusic.generate({
  video: "./trailer.mp4",
  prompt: brief.variations![0]!.prompt,
});
```

`segments` and `variations` are both optional on the type — a `processing` or
`failed` poll carries neither — so guard with `?? []` rather than asserting.

### CLI (`npm install -g sonilo-cli` or `pip install sonilo-cli`)

```bash
sonilo video-analysis --video trailer.mp4 --prompt "focus on the chase" --variants 2
```

The brief goes to **stdout as JSON**, so it pipes:

```bash
sonilo video-analysis --video trailer.mp4 --output brief.json
sonilo video-to-music --video trailer.mp4 --prompt "$(jq -r '.variations[0].prompt' brief.json)"
```

`--output` is the only way this command writes a file, and it writes the brief,
not media.

### cURL (raw REST API, no MCP host)

```bash
curl -X POST "https://api.sonilo.com/v1/video-analysis" \
  -H "Authorization: Bearer $SONILO_API_KEY" \
  -F "video=@trailer.mp4" \
  -F "variants_num=2"
# -> 202 {"task_id": "...", "status": "processing"}

curl "https://api.sonilo.com/v1/tasks/<task_id>" -H "Authorization: Bearer $SONILO_API_KEY"
```

It is async: the POST returns a `task_id`, and the brief arrives on the task
poll. `video_url` works instead of an uploaded file — pass one or the other,
never both.

## Tools

| Tool | Description |
|------|-------------|
| `analyze_video(video_path? \| video_url?, prompt?, variants_num?)` | Analyze a video and return a creative brief for scoring it. Generates nothing and writes no file. `video_path` exists on the local server only — the hosted server is `video_url`-only. |

## Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `video_path` | string | — | Local server only. Absolute path, or relative to `SONILO_MCP_BASE_PATH`. Max **600s (10 min)**, subject to the account's upload-size cap. |
| `video_url` | string | — | HTTP(S) URL to a video file. Exactly one of `video_path`/`video_url`. The only input the hosted server accepts. |
| `prompt` | string | — | Optional guidance for the analysis, e.g. "focus on the chase". Max 2000 characters. Steers what the analysis pays attention to; it is not the generation prompt. |
| `variants_num` | int | `1` | 1–5. How many independent briefs to author for the same video — different creative directions, not rewordings of one. **Billed per brief**, so 3 variations cost 3×. Confirm the number with the user before calling. |

## What comes back

```json
{
  "task_id": "…",
  "status": "succeeded",
  "segments": [
    {"start": 0, "end": 12, "label": "intro", "prompt": "sparse piano, rising"},
    {"start": 12, "end": 30, "label": "none", "prompt": "full strings, driving"}
  ],
  "variations": [
    {"prompt": "cinematic strings, 90bpm, building to a brass hit"},
    {"prompt": "lo-fi hip hop, warm keys, steady throughout"}
  ]
}
```

- **`variations[i].prompt`** is the payload: pass it verbatim as the `prompt` of `video_to_music`, `video_to_sfx`, `video_to_sound`, or their video-to-video counterparts. It is written to be used as-is — do not paraphrase it.
- **`segments`** are whole-second bounds with a per-stretch direction. `label` is one of the music section labels, or the string `"none"`. Useful for reading the video's structure back to the user; note the **music** `segments` parameter takes `{start, prompt, label}` (no `end`) and the **SFX** one takes `{start, end, prompt}`, so a brief segment is not a drop-in for either — see the [video-to-music](../video-to-music) and [video-to-sfx](../video-to-sfx) skills for each shape.

## Workflow Tips

- **Show, then generate.** With `variants_num > 1`, print the variations and let the user pick before spending on a generation. That is the whole point of paying for the analysis.
- **The prompt parameter is not the music prompt.** `prompt` here tells the analyzer what to look at; the music prompt is what comes *back*. Passing "cinematic strings" as `prompt` narrows the analysis, it doesn't set the score.
- **Cheap relative to a wrong generation.** A 10-second billing floor plus one brief usually costs less than one rerolled video-to-video render — but say the price before calling either way.
- **Duration cap is 600s**, more generous than every generation endpoint (360s for music, 180s for SFX/sound/dubbing). A video can be analyzable but too long to score in one call.
- **Content restriction:** as everywhere in Sonilo, prompts cannot reference specific artists, bands, or copyrighted lyrics — and the returned variations will not either.

## Recovering a Timed-Out Call

`analyze_video` is async: the backend accepts and charges the task, then a
worker runs it. If the call times out, the error message includes a `task_id`
and the brief is still coming. Call `get_sfx_task(task_id)` —
`get_generation_task(task_id)` on the hosted server — to retrieve it; see the
[task-recovery](../task-recovery) skill. Because there is no file to download,
recovery hands back the brief itself, inline.

Do **not** re-run `analyze_video` after a timeout. That is a second charge for
a brief you already own.

## Error Handling

Common errors: `401` invalid key, `402` insufficient balance / trial exhausted,
`413` file too large, `422` invalid parameters (video over the 600 s cap, a
video with no video stream, `variants_num` outside 1–5), `429` rate limit. A
failed analysis carries `error.code` `ANALYSIS_FAILED` and is refunded. `503`
means video analysis is temporarily disabled server-side — it is not a key or
balance problem and no retry loop will fix it. See the [account](../account)
skill to check trial/usage before a call.
