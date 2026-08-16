---
name: auto-dubbing
description: Dub a video into one or more other languages using Sonilo, translating and re-voicing the speech into a new video per language. Use when a user needs a video localized into another language, not just subtitled. Billed per language with zero free trial — confirm language count with the user before calling.
license: MIT
compatibility: "Requires Sonilo through either transport — the MCP server connected, or the `sonilo` CLI installed and signed in — plus credentials: a `sonilo login` sign-in, the hosted OAuth plugin, or SONILO_API_KEY. See the setup-api-key skill."
allowed-tools: Bash, Read, Write, mcp__sonilo__*
---

# Sonilo Dubbing

Dub a video into one or more other languages: the speech is translated and re-voiced, producing a new `.mp4` per target language (not just an audio track or subtitles).

> **Setup:** See the [setup-api-key](../setup-api-key) skill.

> ⚠️ **Cost — read before calling:** this is billed **per language**, with **zero free-trial runs** — even a trial account is charged from the very first call, unlike every other Sonilo tool. Requesting four languages costs four times as much as one. Confirm the exact language list with the user before calling; do not guess a long list "to be helpful."

> ⏱ **This call is slow.** It polls for **at least two hours** internally regardless of any shorter `TIME_OUT_SECONDS` — that's the backend's own ceiling for the dubbing pipeline. A call that sits for an hour or more is normal, not a hang. Do not cancel it: the job keeps running and charging either way, and cancelling just loses the easy path to the result (use `get_sfx_task`, or `get_generation_task` on the hosted server, to recover it instead).

## Transport: MCP or CLI

Pick one at the start of the session and stay on it. Do not mix the two inside
a single job, and do not announce the choice.

1. **Sonilo MCP tools visible in this session** (`dubbing` and friends) — use them. This is the preferred path: it needs no shell, and it is the only one that survives a very long generation. If a call fails to authenticate — rather than failing on its inputs — this transport is not usable in this session: go to 2 instead of retrying it.
2. **No usable Sonilo MCP tools, but `sonilo account` exits 0** — use the CLI commands below. Same API, same account, same credential file. Probe with `sonilo account`, not `sonilo whoami`: whoami exits 0 even when signed out, so it cannot tell the two states apart.
3. **Neither** — stop and run the [setup-api-key](../setup-api-key) skill. Do not call `api.sonilo.com` with curl to work around it; both transports handle uploads, polling and retries that a bare request does not.

> ⏱ **On the CLI path this call cannot be one command.** The backend polls for
> up to two hours, while a host's shell tool is capped far below that (ten
> minutes in Claude Code), so `sonilo dubbing` run in the foreground will be
> killed with the job still running and already charged. Submit it and poll
> separately instead:
>
> ```bash
> # --timeout is the CLI's own wait, not the job's: this returns before a host
> # shell can kill the process. The id comes from the "Submitted task ..." line.
> sonilo dubbing --video-url https://example.com/clip.mp4 --languages es,fr --timeout 300
> sonilo tasks wait <task-id>   # repeat until it finishes
> ```
>
> The MCP path has no such limit and is the better transport for dubbing.

## Quick Start

### MCP tool call (recommended)

```
dubbing(
    video_path="~/Desktop/product-demo.mp4",
    languages=["es", "fr"]
)
```

### Python (`pip install sonilo`)

```python
from sonilo import Sonilo

with Sonilo() as client:  # reads SONILO_API_KEY
    result = client.dubbing.generate(
        video="product-demo.mp4",
        languages=["es", "fr"],
        timeout=7200,  # seconds — matches the backend's own ~2h ceiling
    )
    for language, path in result.save_all("./dubbed").items():
        print(language, path)
```

### JavaScript / TypeScript (`npm install sonilo`)

```ts
import { SoniloClient } from "sonilo";
import type { DubbingResult } from "sonilo";

const client = new SoniloClient(); // reads SONILO_API_KEY

const result = await client.dubbing.generate(
  { video: "./product-demo.mp4", languages: ["es", "fr"] },
  { timeout: 7_200_000 }, // milliseconds — matches the backend's own ~2h ceiling
);
for (const [language, url] of Object.entries((result as DubbingResult).outputs ?? {})) {
  console.log(language, url);
}
```

### CLI (`npm install -g sonilo-cli` or `pip install sonilo-cli`)

```bash
sonilo dubbing --video-url https://example.com/product-demo.mp4 --languages es,fr --output dubbed.mp4
# writes dubbed.es.mp4 and dubbed.fr.mp4
```

`--timeout` defaults to 7200 seconds already, matching the backend's ceiling. That is fine in a normal terminal; inside an agent host shell, use the shorter submit-and-poll pattern above so the shell tool does not kill the foreground command.

### cURL (raw REST API, no MCP host)

```bash
curl -X POST "https://api.sonilo.com/v1/dubbing" \
  -H "Authorization: Bearer $SONILO_API_KEY" \
  -F "video=@product-demo.mp4" \
  -F 'languages=["es","fr"]'
# -> {"task_id": "..."}  poll GET /v1/tasks/{task_id} — can take up to ~2 hours
```

`video_url` is also accepted instead of an uploaded file, but **must be https** — the dubbing pipeline fetches the source itself and rejects plain http.

## Tool

| Tool | Description |
|------|-------------|
| `dubbing(video_path? \| video_url?, languages?, output_directory?)` | Dub a video into each requested language; one `.mp4` saved per language. |

## Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `video_path` | string | — | `.mp4/.mov/.webm/.m4v/.gif` (gif must be animated). Max **180s (3 min)**, subject to the account's upload-size cap. |
| `video_url` | string | — | **Must be https** (not just http). Exactly one of `video_path`/`video_url`. |
| `languages` | list[str] | `["zh_cn", "es", "fr"]` | Target language codes. Supported: `en`, `zh_cn`, `ja`, `ko`, `pt`, `es`, `de`, `fr`, `it`, `ru`. **Omitting this still dubs into 3 languages and bills for 3** — pass an explicit single-element list if the user only wants one. |
| `output_directory` | string | `SONILO_MCP_BASE_PATH` | Absolute, or relative to the base path. |

## Workflow Tips

- **Always ask which language(s)** if the user hasn't said, rather than relying on the `["zh_cn", "es", "fr"]` default — that default silently bills for three languages.
- **This is not the music or SFX skills** ([text-to-music](../text-to-music), [video-to-music](../video-to-music), [text-to-sfx](../text-to-sfx), [video-to-sfx](../video-to-sfx)). It doesn't touch music/SFX at all — it translates and re-voices existing speech.
- **Set expectations on time.** Tell the user up front this can take up to ~2 hours and that walking away is fine — the result is recoverable afterward.
- Because there is no free trial here at all, if the account is self-serve and hasn't added a payment method, warn the user before calling rather than letting it fail with `trial_exhausted` (which doesn't even apply — dubbing bills immediately regardless of trial status). Check `get_account_services` (see [account](../account)) if unsure about billing status.

## Recovering a Timed-Out Call

If the call's own long poll is interrupted (e.g. the host itself times out or the session is closed), the error message — or the task id printed to stderr at submission time — gives you a `task_id`. Call `get_sfx_task(task_id)` — `get_generation_task(task_id)` on the hosted server — to check status and download finished files once ready; see [task-recovery](../task-recovery).

## Output Files

One `.mp4` per requested language, named `dubbing-<first 8 chars of the task id>.<language>.mp4` — there's no prompt to name files after, so all dubbing output shares the task-id-based name.

## Error Handling

Common errors: `401` invalid key, `402` insufficient balance (dubbing has no trial to exhaust — it bills immediately), `413` file too large, `422` invalid parameters or unsupported language code (rejected before any charge), `429` rate limit. See the [account](../account) skill.
