# AGENTS.md

Notes for coding agents working in this repo, and for agents that use these
skills to call Sonilo.

## What this repo is

Agent Skills (per the [Agent Skills spec](https://agentskills.io/specification))
for Sonilo's music, sound effects, dubbing and audio ducking API. There is no
build and no runtime code: every skill is a `SKILL.md` describing tools that
live in other repos (the local `sonilo-mcp` server, the hosted MCP server at
`https://api.sonilo.com/mcp`, the `sonilo` CLI and the SDKs). The same
directory is also a Claude Code plugin marketplace (`.claude-plugin/`), a
Muse Code plugin (`.muse-plugin/`) and a Cursor plugin (`.cursor-plugin/`).

## Layout

```
<skill>/SKILL.md          one directory per skill; directory name == frontmatter `name`
references/               shared guidance the skills link to
  api_reference.md        one-page REST reference (base URL, every endpoint, errors)
  api-claims.md           API behaviour verified against the backend
  preflight.md            checks to run before any paid call
  music-prompting.md, sfx-prompting.md
tests/validate.py         the whole test suite
tests/tool_surface.json   recorded tool names, parameters, defaults, CLI flags, banned tokens
evals/routing/            trigger evals: does the right skill load for a query
.claude-plugin/           plugin.json (skill list, version) + marketplace.json
.muse-plugin/plugin.json  same skills and version, plus the hosted MCP server
.cursor-plugin/plugin.json  same skills and version, plus the hosted MCP server (OAuth); logo in assets/
```

## Commands

```bash
python -m pip install PyYAML
python tests/validate.py             # offline; CI runs this on every push and PR
pip install sonilo-mcp
python tests/validate.py --refresh   # re-read the local tool surface from the installed package
```

CI (`.github/workflows/validate.yml`) runs both, and fails if `--refresh`
changes `tests/tool_surface.json`. It also runs weekly, because the tools these
skills describe change in other repos.

## Making changes

- A skill's `name` must equal its directory name; the description must stay
  under 1024 characters and mention Sonilo, or it never routes.
- Any tool, parameter, default or `sonilo <subcommand> --flag` you write in a
  `SKILL.md`, `README.md` or `references/*.md` is checked against
  `tests/tool_surface.json`. If the upstream tool changed, update the surface
  first, then the prose.
- The two MCP servers name the task recovery tool differently: `get_sfx_task`
  on the local server, `get_generation_task` on the hosted one. Never mention
  one without the other.
- `banned_tokens` in `tool_surface.json` lists statements that used to be true.
  Do not reintroduce them.
- Adding or renaming a skill: update `.claude-plugin/plugin.json`,
  `.muse-plugin/plugin.json`, `.cursor-plugin/plugin.json` and the table in
  `README.md`. All three manifests carry the same version; bump it in all of
  them (commit titles end with the version, e.g. `(2.5.1)`).
- When a check misses a bug you fixed by hand, add the case to `validate.py`.

## Using Sonilo from a skill

### Credentials

Any one of these works:

- `sonilo login` (from `npm install -g sonilo-cli` or `pip install sonilo-cli`)
  writes a 90-day key to `~/.config/sonilo/credentials.json`. The CLI and
  `sonilo-mcp` 0.16.0+ read it.
- `SONILO_API_KEY`, an `sk-` key from
  https://platform.sonilo.com/dashboard/api-keys. It takes precedence over a
  sign-in.
- The hosted MCP server (`https://api.sonilo.com/mcp`) signs in with OAuth on
  first use; no key.

The `setup-api-key` skill walks a user through this.

### API basics

| | |
|---|---|
| Base URL | `https://api.sonilo.com` |
| Auth | `Authorization: Bearer $SONILO_API_KEY` |
| OpenAPI | `https://platform.sonilo.com/openapi.json` |
| Async results | `POST` returns `202 {"task_id": ...}`; poll `GET /v1/tasks/{task_id}` until `succeeded` or `failed` |
| Account | `GET /v1/account/services` (limits, free trial left), `GET /v1/account/usage` |

`text-to-music` and `video-to-music` return the audio directly unless
`mode=async`; everything else is a task. Full parameter tables are in
`references/api_reference.md`.

### Video length caps (rejected with 422 before any charge)

| Endpoint | Max |
|---|---|
| video-to-music, video-to-video-music | 360 s |
| video-to-sfx, video-to-video-sfx, video-to-sound, video-to-video-sound, video-analysis | 480 s |
| audio-ducking | 360 s per input |
| dubbing, proofread | 300 s |

### Billing rules a skill must respect

- Charged when the task is accepted. A client timeout does not cancel or
  refund it: recover the result with the task id instead of submitting again.
- Failed generations are refunded automatically.
- `variants_num` multiplies the cost and is never covered by the free trial.
- Music plus SFX for one video is `video_to_sound` (one charge), not
  `video_to_music` + `video_to_sfx` (two).
- Only call a paid tool when the user asked for it; check
  `get_account_services` for `trial[service].remaining` first.

### Common errors

| Status / code | Meaning | What to do |
|---|---|---|
| 401 `unauthorized` | Key invalid, revoked, or a 90-day CLI key expired | Run `sonilo login` again or replace `SONILO_API_KEY` |
| 402 `trial_exhausted` | Free trial for that service is spent | Add a payment method at https://platform.sonilo.com/dashboard/billing; retrying cannot help |
| 402 `insufficient_balance` | Funded balance ran out | Top up, then retry |
| 400 | An async-only option (`stems`, `preserve_speech`, `ducking`, `output_format=wav`) sent without `mode=async` | Add `mode=async` |
| 413 | File over the upload limit (`max_upload_size_mb`, typically 300) | Compress or trim |
| 422 | Over a length cap, bad `segments`, unsupported language | Fix the input; nothing was charged |
| 429 `rate_limit_exceeded` | Requests per minute or concurrent generations | RPM: wait a full minute. Concurrency: wait for a running task to finish |
| 503 | Video analysis or proofread temporarily disabled | Try later |
| 404 on `/v1/tasks/{id}` | Wrong id, or the call returned audio directly and has no task | Check the id |
