# API facts — verified with Sonilo engineering 2026-07-28

Every numeric limit and behavior claim used by the skills in this repo, verified against the backend on 2026-07-28. Re-verify before major releases; trust the live API reference over this file if they disagree. ⚠️ marks corrections relative to earlier draft wording.

## video_to_music

- [x] **Cap 360 s — the only cap.** ⚠️ 600 s figure doesn't exist in code (internal note was stale). All video endpoints share ffprobe-based 360 s, incl. muxed `/v1/video-to-video-music`. Over-cap = **422 reject**, never truncated.
- [x] Cut-point alignment = **heuristic / best-effort**, NOT a guarantee. ⚠️ Skill draft overclaims — soften wording. Music segment starts round to **whole seconds** upstream.
- [x] Output length: targets video duration, **no trim/pad contract**. ⚠️ Say "matches the video length", drop "exactly". With preserve_speech, mux takes the shorter track.
- [x] Timestamps in prompt: **partially honored**. ⚠️ Big draft correction — with no `segments` and `variants_num=1`, a prompt-analysis service parses section-shaped prompt text into a segments plan; unparseable → whole prompt = style hint. Same on REST + MCP. So structured sections in the prompt CAN steer segmented music (and on MCP it's the ONLY path — see below).
- [x] `preserve_speech` — exact name, **default false**. REST requires `mode=async` (400 in stream); MCP always async. Adds vocals stem + mux at no extra charge.
- [x] Ducking **default ON in async mode**, independent of preserve_speech. `ducking=false` to disable. Best-effort (no-audio source silently degrades). REST stream mode: no ducking (`ducking=true` = 400).
- [x] Mix levels not promptable — confirmed. Server-side LUFS-based gain, prompt never consulted.
- [x] Negative prompts ("no vocals") — **best-effort**, zero backend enforcement.

## video_to_sfx

- [x] **Cap 180 s** both surfaces; over-cap = 422 reject. (Internal 360 s probe backstop exists; publicly say 180 s.)
- [x] `prompt` ≤ 2000 chars — enforced, **error** not truncate.
- [x] Segment rules — **ALL backend-enforced**, rejected before any charge: ≤30 entries · first start = 0 (±1e-3) · contiguous end == next start (±0.01 s) · end > start · segment prompt non-empty ≤200 chars. Plus undocumented **40,000-char raw-JSON cap**. Identical on MCP (segments = JSON-encoded array string, same validation).
- [x] Last `end` need NOT equal duration — only `≤ duration + 0.05 s` enforced. Uncovered tail = **no generated SFX** (upstream behavior, don't promise more).
- [x] Exclusions — global prompt or segment prompts, both verbatim free text, **best-effort**.
- [x] Timestamps — sub-second floats passed upstream **as-is, no rounding** (⚠️ unlike music segments which round to whole seconds — don't conflate).

## video_analysis

Added 2026-08-16 with the endpoint itself; verified against the shipped backend and the live
`platform.sonilo.com/openapi.json`, not against an engineering conversation.

- [x] **Cap 480 s** (raised from 360 s on 2026-09-18) — matching the SFX/sound endpoints; music is 360 s and dubbing 300 s. A video can still be analyzable and too long to score with music in one call. Over-cap = **422 reject**.
- [x] **Generates nothing.** No audio, no video, no artifact. The result carries `mode` (an echo of the request) and, by default (`both`), a music-direction brief — `segments` (whole-second `start`/`end`, a `label`, and a per-stretch `prompt`) plus `variations` (one generation `prompt` each) — **and** a sound-design brief — `sfx_segments` (shot-sized `start`/`end`/`label`/`prompt`, `label` always `"none"`) plus `sfx_prompt` (one whole-clip sound-design prompt, authored once regardless of `variants_num`). This is the only Sonilo task type with no media in its envelope, which is why every client surfaces it as text rather than a saved file.
- [x] `mode` accepts `both` / `music` / `sfx`, default `both`, same price for all three. `music` returns only `segments` + `variations` (the pre-`mode` shape); `sfx` returns only the sound-design brief, in `segments` + `variations` (labels `"none"`); neither carries the `sfx_*` keys. An invalid `mode` = **422 reject**.
- [x] `variants_num` **1-5**, billed per brief — narrower than the music endpoints' 1-10. `prompt` ≤ 2000 chars, and it steers the **analysis**, not the score.
- [x] **10-second billing floor**: a fixed per-request output cost regardless of clip length, so a 3-second clip costs the same as a 10-second one.
- [x] Free trial: 2 calls, self-serve accounts only (the platform default allowance).
- [x] Async, worker-executed: `202` + `task_id`, result on `GET /v1/tasks/{id}`. Failure carries `error.code` `ANALYSIS_FAILED` and is refunded; `TRANSFER_FAILED`, `INVALID_PAYLOAD` and `GENERATION_FAILED` are also possible depending on where it broke.
- [x] `503 "Video analysis is temporarily unavailable"` is a server-side kill switch (`PROMPT_SERVICE_ENABLED`), not an auth or balance problem. No retry loop fixes it.
- [x] The variation prompts are **narrower than what the upstream produces** by product decision: `negative_prompt`, `thinking`, `structure_source` and the variation title/summary/tags are stripped before the envelope is built and are not recoverable from the task.
- [x] ⚠️ **Input differs by MCP server**: the hosted server exposes `video_url` only; local `sonilo-mcp` (0.17.0+) also takes `video_path`. Both SDKs and both CLIs accept a local file or a URL.

## stems (text_to_music + video_to_music)

Added 2026-08-17, verified against the shipped backend (live on REST `/v1/text-to-music` + `/v1/video-to-music` and on the hosted MCP server's `text_to_music` + `video_to_music`).

- [x] **Free of charge.** Splits each generated track into four separated instrument tracks — `drums`, `bass`, `vocals`, `other` — delivered as a `stems` array alongside the clean `audio` in the task result.
- [x] REST requires `mode=async` (`stems=true` in stream mode = **400**); MCP is always async, so the param just works there.
- [x] Result entry shape: `{ stream_index, drums, bass, vocals, other }`, each stem `{ url, content_type, file_size }`. **Look entries up by `stream_index`, never by position** — a stream whose separation failed is absent, so `stems` can be shorter than `audio`.
- [x] `stems_error` (string) appears when separation failed wholly/partly or was skipped, and **can appear alongside a partial `stems`**. The generation itself succeeded and the audio URLs are valid — a missing extra, never a failed generation.
- [x] Separation runs after generation: typically **+2–6 min**, gives up after **30 min**. Stems normally follow `output_format`; each stem's `content_type` reports what was delivered.
- [x] On `video_to_music` it splits the **generated** music, never the video's own audio (source speech = `preserve_speech`, unrelated).
- [x] The four stem names are fixed (htdemucs): melodic instruments land in `other`; on instrumental tracks `vocals` is near-silent — correct behavior, not a bug.
- [x] **Surface gap closed 2026-08-17** (same day): sonilo-mcp 0.18.0, npm sonilo 0.16.0 / sonilo-cli 0.15.0, and PyPI sonilo 0.15.0 / sonilo-cli 0.14.0 all ship `stems`; `tests/tool_surface.json` refreshed against the published 0.18.0. Every surface now accepts it.

## dubbing subtitle scripts (`subtitles` + `export_srt`)

Added 2026-09-13, verified against the shipped backend and a paid production run, not against an engineering conversation.

- [x] `subtitles` is **one script per target language**, wired as Stripe-style bracket keys on the multipart body (`subtitles[<language>]`). Each value is an uploaded `.srt`/`.vtt` part **or** an https URL string. A bare `subtitles` key, a repeated key, or a near-miss code (`subtitles[zh-CN]`; the codes use underscores) is **refused, never silently ignored**.
- [x] **Full coverage enforced**: the key set must equal `languages` exactly, and the `422` names the missing or extra code. This bites the caller who omits `languages` — the server default is still `["zh_cn", "es", "fr"]`, so all three need a script. The clients deliberately do **not** duplicate this check, precisely so that default keeps working.
- [x] **Target-language scripts**, carrying the lines to be spoken — not source transcripts. The preflight reads the text and rejects a script whose language is not the one it was submitted under.
- [x] Per-file limits: extension `.srt`/`.vtt`, lower-cased, **at most 1 MiB**. The size cap is server-owned; clients do not copy it.
- [x] `export_srt` (bool, **default false**) **requires `subtitles`** — alone it is a `422`. It force-aligns each language's delivered audio against that language's script and returns the lines re-timed, **verbatim**.
- [x] Every rule above is checked **before anything is charged**. A blocked preflight is `422` `code: SUBTITLE_PREFLIGHT_BLOCKED`, naming the blocked languages and their issue codes, with `details: {<language>: <report>}`.
- [x] ⚠️ **A blocked export does NOT fail the task.** The dubbed videos are still delivered and charged; `subtitles` simply lacks that language. `subtitle_export[lang].status` is `exported`, `exported_review_required` or `blocked`.
- [x] Result envelope: `outputs` (unchanged) plus `subtitles: {<language>: <srt url>}` (only with `export_srt`), `subtitle_preflight` and `subtitle_export`. The `202` also carries `subtitle_preflight`.
- [x] ⚠️ **Report numbers can arrive as strings.** They are stored as DynamoDB numbers, so on a finished task `cue_count` may be `"5"` and `alignment_loss` `"0.6305176995017312"`. Anything surfacing them must tolerate both a string and a number.
- [x] ⚠️ **Input differs by MCP server**, the same split as `video_path`: the hosted server takes https URLs only (it has no filesystem to read a path from); local `sonilo-mcp` and both SDKs and CLIs take a local `.srt`/`.vtt` path or an https URL. In JS a `File` is also accepted; blobs, byte arrays and streams are not, because the server needs a filename to check the extension.
- [x] **Published everywhere as of 2026-09-14**: REST, the hosted MCP server, sonilo-mcp 0.23.0, PyPI `sonilo` 0.17.0 / `sonilo-cli` 0.16.0, npm `sonilo` 0.18.0 / `sonilo-cli` 0.17.0. Both CLIs take `--subtitle <lang>=<path-or-url>` (repeatable) and `--export-srt`. The two MCP servers differ in what a subtitle value may be: the hosted one has no filesystem and takes https URLs only, the local one also takes a `.srt`/`.vtt` path.
- [x] `lipsync` (bool, **default true**) shipped just ahead of this, in sonilo-mcp 0.22.0 and on the hosted server. `false` skips the mouth re-render: the deliverable keeps the source's own frames, resolution and frame rate, and only the audio is replaced. Absent must mean true — that is what every dubbing task did before the parameter existed.

## proofread

Added 2026-09-18 with `POST /v1/proofread`. Verified against the live API and one paid
multi-language run on 2026-09-16; the request/response contract, the error-code list and the
billing numbers are from the shipped docs contract extracted 2026-09-18, and the per-surface
differences from the client sources. Not from an engineering conversation.

- [x] **Cap 300 s and 300 MB**, the same as dubbing. A video over either limit is rejected rather
  than transcribed; the contract states the limits, not the status code they come back as.
- [x] **The video must have an audio track.** There is nothing to transcribe without one, so such a
  video is rejected rather than run — again, the contract states the requirement and not a code,
  and the hosted MCP server checks it client-side before any request is made (the local server
  does not probe for audio and leaves it to the API). A video *with*
  audio but *without speech* is different: that task is accepted, charged, then comes back `failed`
  with `TRANSCRIPTION_EMPTY` and is refunded.
- [x] `video_url` **must be https** — the backend fetches the source itself and rejects plain http,
  the same rule as dubbing. Exactly one of `video` / `video_url`.
- [x] `languages` is **optional**, a JSON-array **string** form field (the same wire shape as
  dubbing's), e.g. `["ja","zh_cn"]`. Omit it or send `[]` for the source-language transcript alone.
  It takes **the same codes as dubbing**, which is the point — a proofread script goes straight
  into a dub. An unsupported code is a `422` naming it, and it is **not** validated client-side:
  the server owns the list, so a code added later works without a client upgrade.
- [x] `source_language` is an **optional hint** for transcription (one of the same codes), useful
  on short, noisy or mixed-language audio. It does not add a language and does not change the
  price. Omitted = detected. Either way the finished task reports the language the transcript is
  actually in.
- [x] **Billing: video seconds × max(1, number of target languages) at $0.001/sec, 10-second
  floor**, account discount applies. A transcript-only request (no `languages`) counts as **one**.
  Charged up front at submission; failed tasks are refunded.
- [x] **Free trial: 2 calls**, self-serve accounts only — `dubbing`'s is 1, as a 15-second preview.
- [x] Async: `202` `{"task_id", "status": "processing"}`, result on `GET /v1/tasks/{task_id}`.
  Typical wall time 20–45 s for a 3.4-minute clip with 2–6 languages, so the clients keep their
  ordinary wait default rather than dubbing's two-hour floor.
- [x] Result envelope: `source_language`, `subtitles`, `cue_count`, `warnings`, `duration_seconds`.
- [x] ⚠️ **`subtitles` ALWAYS includes the detected source language**, under its detected code, on
  top of one entry per requested target. A request with no `languages` still returns one file, and
  a one-language request returns two. Values are **presigned `.srt` URLs that expire** — the same
  map shape as dubbing's `outputs`, which is why every client models it as a map rather than a list.
- [x] `cue_count` is the cues in the **source** script; every language has the same count, since
  translation is cue by cue.
- [x] ⚠️ **`warnings` is non-blocking.** It maps a language to a list of preflight issues
  `{"cue": <1-based>, "code": "high_text_speed", "severity": "warning", <measurement>}`, and is
  `{}` when there are none. Nothing in it fails the task or withholds a file — surface it as a note.
- [x] Failure carries `error.code` one of `SOURCE_DOWNLOAD_FAILED`, `SOURCE_PROCESSING_FAILED`,
  `TRANSCRIPTION_EMPTY`, `TRANSCRIPTION_FAILED`, `TRANSLATION_FAILED`, `PREFLIGHT_BLOCKED`,
  `PREFLIGHT_UNAVAILABLE`, `TRANSFER_FAILED`. A `503` is the server-side kill switch, not an auth
  or balance problem.
- [x] **The handoff is the contract**: the returned `.srt` files, once corrected, go to
  `POST /v1/dubbing` as `subtitles[<language>]` with `languages` matching. Dubbing's key set must
  equal `languages` **exactly**, so the source-language file proofread always returns has to be
  dropped before the dub.
- [x] ⚠️ **Input differs by MCP server**, the same split as `video_path` elsewhere: the hosted
  server exposes `video_url`, `languages` and `source_language` only; local `sonilo-mcp` also takes
  `video_path` and `output_directory` and saves one `.srt` per language as
  `proofread-<first 8 chars of the task id>.<language>.srt`. `get_generation_task` (hosted) /
  `get_sfx_task` (local) recover a timed-out call.
- [x] ⚠️ **Not published yet as of 2026-09-18.** The REST endpoint and the hosted MCP tool are
  live; sonilo-mcp 0.26.0, PyPI `sonilo-cli` 0.19.0 and their npm twins are merged but unreleased,
  so `tests/tool_surface.json`'s `proofread` entries were recorded by hand from those sources and
  `python tests/validate.py --refresh` cannot confirm them until the packages land.

## Billing / general

- [x] Charged up front at submission; **failed generations auto-refunded**. Caller retries = new charge. **No preview/low-cost mode.** Music + SFX = separate task types, separate per-second rates, separate prepay minute pools. `variants_num` scales v2m cost linearly; N>1 never covered by free trial.
- [x] MCP vs REST — field names + numeric limits match. Three structural differences (⚠️ document, don't claim identity):
  1. MCP input = **`video_url` only**, no file upload
  2. MCP **always async** — no `mode` param; returns `task_id`, results via `get_generation_task` (named `get_sfx_task` on the local server)
  3. MCP `video_to_music` has **no `segments` param** — segmented music via MCP only through section-shaped prompt text (prompt-analysis path)
- [x] Output = **audio files only** (not video). v2m: m4a default, `output_format=wav` optional (async-only on REST; always on MCP); preserve_speech adds vocals track + mux; ducking adds ducked music URLs. v2sfx: single file, aac default, wav/mp3/flac optional. Video out = separate `/v1/video-to-video-*` endpoints + corresponding MCP tools. ⚠️ An earlier pass said "not stems-in-DAW-sense" — no longer true: `stems=true` on t2m/v2m (added 2026-08-17, see the stems section below) returns exactly that.
- [x] Multi-track input — default ffmpeg stream selection (typically first audio track) for ducking/speech. Wording: "for multi-track videos, the default audio track is used."

## Empirical test (2026-07-29)

- 240 s synthetic video → `POST https://api.sonilo.com/v1/video-to-sfx` → **422** `{"code":"unprocessable_entity","message":"Video duration 240.0s exceeds the 180s video-to-sfx maximum"}`. Instant, no task created, no charge. Confirms the API **rejects** (does not truncate) over-cap SFX input. Consumer-app behavior for over-cap uploads remains unverified.

## Live spec observations (sonilo.com/openapi.json, 2026-07-29)

- Public endpoints (re-verified 2026-08-12 against `platform.sonilo.com/openapi.json`): `/v1/account/services` · `/v1/account/usage` · `/v1/text-to-music` · `/v1/text-to-sfx` · `/v1/video-to-music` · `/v1/video-to-sfx` · `/v1/video-to-video-music` · `/v1/video-to-video-sfx` · `/v1/video-to-sound` · `/v1/video-to-video-sound` · `/v1/audio-ducking` · `/v1/dubbing` · `/v1/video-analysis` (added 2026-08-16) · `/v1/tasks/{task_id}`. ⚠️ Corrects the 2026-07-29 observation this replaces: a combined music+SFX endpoint now exists (`/v1/video-to-sound` for audio-only output, `/v1/video-to-video-sound` for video output), and video-out endpoints are in the public spec (`/v1/video-to-video-music`, `/v1/video-to-video-sfx`, `/v1/video-to-video-sound`) — consistent with line 32's MCP claim above. Dubbing (`/v1/dubbing`) also shipped since the earlier pass.
- `VideoToMusicRequest` confirms REST `segments` param exists; also has `isolate_vocals` — **behavior unverified, not yet covered by the skills**.
