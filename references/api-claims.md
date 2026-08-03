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

## Billing / general

- [x] Charged up front at submission; **failed generations auto-refunded**. Caller retries = new charge. **No preview/low-cost mode.** Music + SFX = separate task types, separate per-second rates, separate prepay minute pools. `variants_num` scales v2m cost linearly; N>1 never covered by free trial.
- [x] MCP vs REST — field names + numeric limits match. Three structural differences (⚠️ document, don't claim identity):
  1. MCP input = **`video_url` only**, no file upload
  2. MCP **always async** — no `mode` param; returns `task_id`, results via `get_generation_task`
  3. MCP `video_to_music` has **no `segments` param** — segmented music via MCP only through section-shaped prompt text (prompt-analysis path)
- [x] Output = **audio files only** (not stems-in-DAW-sense, not video). v2m: m4a default, `output_format=wav` optional (async-only on REST; always on MCP); preserve_speech adds vocals track + mux; ducking adds ducked music URLs. v2sfx: single file, aac default, wav/mp3/flac optional. Video out = separate `/v1/video-to-video-*` endpoints + corresponding MCP tools.
- [x] Multi-track input — default ffmpeg stream selection (typically first audio track) for ducking/speech. Wording: "for multi-track videos, the default audio track is used."

## Empirical test (2026-07-29)

- 240 s synthetic video → `POST https://api.sonilo.com/v1/video-to-sfx` → **422** `{"code":"unprocessable_entity","message":"Video duration 240.0s exceeds the 180s video-to-sfx maximum"}`. Instant, no task created, no charge. Confirms the API **rejects** (does not truncate) over-cap SFX input. Consumer-app behavior for over-cap uploads remains unverified.

## Live spec observations (sonilo.com/openapi.json, 2026-07-29)

- Public endpoints: `/v1/text-to-music` · `/v1/video-to-music` · `/v1/audio-ducking` · `/v1/text-to-sfx` · `/v1/video-to-sfx` · `/v1/tasks/{task_id}` — **no combined music+SFX endpoint, no video-out endpoints in the public spec**. One-call "music + SFX, one finished track" is a product-app feature, not a public API call; on the API you run v2m and v2sfx separately and mix (`/v1/audio-ducking` helps).
- `VideoToMusicRequest` confirms REST `segments` param exists; also has `isolate_vocals` — **behavior unverified, not yet covered by the skills**.
