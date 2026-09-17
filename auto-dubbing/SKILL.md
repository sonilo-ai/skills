---
name: auto-dubbing
description: Dub a video into one or more other languages using Sonilo, translating and re-voicing the speech into a new video per language. Optionally supply your own target-language script per language, so the dub speaks those lines verbatim instead of the pipeline's own translation, and get a re-timed SRT back per language. Use when a user needs a video localized into another language, not just subtitled. Billed per language with zero free trial — confirm language count with the user before calling.
license: MIT
compatibility: "Requires Sonilo through either transport — the MCP server connected, or the `sonilo` CLI installed and signed in — plus credentials: a `sonilo login` sign-in, the hosted OAuth plugin, or SONILO_API_KEY. See the setup-api-key skill."
allowed-tools: Bash, Read, Write, mcp__sonilo__*
---

# Sonilo Dubbing

Dub a video into one or more other languages: the speech is translated and re-voiced, producing a new `.mp4` per target language (not just an audio track or subtitles). If the user already has approved translations, pass them as `subtitles` and the dub speaks those lines instead of translating the source itself.

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

With the user's own scripts, and a re-timed `.srt` back per language:

```
dubbing(
    video_path="~/Desktop/product-demo.mp4",
    languages=["es", "fr"],
    subtitles={"es": "~/Desktop/demo.es.srt", "fr": "~/Desktop/demo.fr.srt"},
    export_srt=True
)
```

> On the **hosted** server every subtitle value must be an `https://` URL — that server has no filesystem to read a path from, and `video_url` is likewise its only source. The **local** `sonilo-mcp` server takes either a local `.srt`/`.vtt` path or an https URL.

### Python (`pip install sonilo`)

```python
from sonilo import Sonilo

with Sonilo() as client:  # reads SONILO_API_KEY
    result = client.dubbing.generate(
        video="product-demo.mp4",
        languages=["es", "fr"],
        # Optional: the lines to speak in each target language. A value is
        # either a local .srt/.vtt path or an https URL.
        subtitles={"es": "demo.es.srt", "fr": "demo.fr.srt"},
        export_srt=True,
        timeout=7200,  # seconds — matches the backend's own ~2h ceiling
    )
    for language, path in result.save_all("./dubbed").items():
        print(language, path)
    # Only present with export_srt. Iterate this map, not the videos: a
    # language whose export was blocked still has its .mp4.
    for language, path in result.save_all_subtitles("./dubbed").items():
        print(language, path)
```

### JavaScript / TypeScript (`npm install sonilo`)

```ts
import { SoniloClient } from "sonilo";
import type { DubbingResult } from "sonilo";

const client = new SoniloClient(); // reads SONILO_API_KEY

const result = await client.dubbing.generate(
  {
    video: "./product-demo.mp4",
    languages: ["es", "fr"],
    // Optional: a local .srt/.vtt path, an https URL, or a File in a browser.
    subtitles: { es: "./demo.es.srt", fr: "https://example.com/demo.fr.vtt" },
    exportSrt: true,
  },
  { timeout: 7_200_000 }, // milliseconds — matches the backend's own ~2h ceiling
);
for (const [language, url] of Object.entries((result as DubbingResult).outputs ?? {})) {
  console.log(language, url);
}
// Only present with exportSrt, and a language whose export was blocked is absent.
for (const [language, url] of Object.entries((result as DubbingResult).subtitles ?? {})) {
  console.log(language, url);
}
```

### CLI (`npm install -g sonilo-cli` or `pip install sonilo-cli`)

```bash
sonilo dubbing --video-url https://example.com/product-demo.mp4 --languages es,fr --output dubbed.mp4
# writes dubbed.es.mp4 and dubbed.fr.mp4

# With the user's own scripts. --subtitle is repeatable, once per language, and
# its value is a local .srt/.vtt path or an https URL.
sonilo dubbing --video-url https://example.com/product-demo.mp4 --languages es,fr --subtitle es=demo.es.srt --subtitle fr=demo.fr.srt --export-srt --output dubbed.mp4
# also writes dubbed.es.srt and dubbed.fr.srt beside the videos, so --output may not end in .srt
```

`--timeout` defaults to 7200 seconds already, matching the backend's ceiling. That is fine in a normal terminal; inside an agent host shell, use the shorter submit-and-poll pattern above so the shell tool does not kill the foreground command.

### cURL (raw REST API, no MCP host)

```bash
curl -X POST "https://api.sonilo.com/v1/dubbing" \
  -H "Authorization: Bearer $SONILO_API_KEY" \
  -F "video=@product-demo.mp4" \
  -F 'languages=["es","fr"]' \
  -F "subtitles[es]=@demo.es.srt" \
  -F "subtitles[fr]=https://example.com/demo.fr.vtt" \
  -F "export_srt=true"
# -> {"task_id": "...", "subtitle_preflight": {...}}
#    poll GET /v1/tasks/{task_id} — can take up to ~2 hours
```

`video_url` is also accepted instead of an uploaded file, but **must be https** — the dubbing pipeline fetches the source itself and rejects plain http.

One `subtitles[<language>]` field per language, each either an uploaded `.srt`/`.vtt` part or an https URL string. The bracket key is required: a bare `subtitles`, a repeated key, or a near-miss code (`subtitles[zh-CN]` — the codes use underscores, `zh_cn`) is rejected, never silently ignored.

## Tool

| Tool | Description |
|------|-------------|
| `dubbing(video_path? \| video_url?, languages?, ducking?, lipsync?, subtitles?, export_srt?, output_directory?)` | Dub a video into each requested language; one `.mp4` saved per language, plus one `.srt` per language with `export_srt`. |

## Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `video_path` | string | — | `.mp4/.mov/.webm/.m4v/.gif` (gif must be animated). Max **300s (5 min)**, subject to the account's upload-size cap. |
| `video_url` | string | — | **Must be https** (not just http). Exactly one of `video_path`/`video_url`. |
| `languages` | list[str] | `["zh_cn", "es", "fr"]` | Target language codes. Supported: `en`, `zh_cn`, `ja`, `ko`, `pt`, `pt_br`, `es`, `es_419`, `de`, `fr`, `it`, `ru`, `th`, `ar`, `tr`, `vi`, `id`, `ta`, `ml`, `kn`, `gu`, `pa_in`, `sd_in`. `pt_br` is Brazilian Portuguese and `es_419` Latin American Spanish; plain `pt`/`es` are unqualified, so ask which the user wants when it matters. `ar` is unqualified Arabic rather than a country dialect, so there is nothing to ask there. `pa_in` and `sd_in` are Punjabi and Sindhi as spoken in India — the only variants available, so say so if the user's audience is in Pakistan, where both are written in another script. **Omitting this still dubs into 3 languages and bills for 3** — pass an explicit single-element list if the user only wants one. |
| `ducking` | bool | off | Duck the background music/effects bed under the dubbed voice while it speaks. Off by default: the bed is always kept, at a constant level. Free either way. |
| `lipsync` | bool | `true` | Whether the speaker's mouth is re-rendered to match the dubbed speech. Set `false` to leave the picture completely untouched instead — the video comes back at its original resolution and frame rate rather than re-rendered, and only the audio is replaced, so the mouths keep moving to the original language. Reach for it when the footage has no on-camera speaker (screen recordings, b-roll, voice-over), or when preserving the exact original picture matters more than matching lip movement. Same price either way. |
| `subtitles` | dict[str, str] | — | One script per target language, e.g. `{"es": "demo.es.srt"}`. Each value is a local `.srt`/`.vtt` path or an https URL (the hosted MCP server takes URLs only). These are **target-language** scripts carrying the lines to speak, not source transcripts — the dub says them verbatim instead of translating. The key set must equal `languages` exactly. See the rules below; every one of them is a `422` before any charge. |
| `export_srt` | bool | `false` | Also return each language's lines re-timed against its delivered audio, by forced alignment, keeping the wording verbatim. **Requires `subtitles`** — sending it alone is a `422`. |
| `output_directory` | string | `SONILO_MCP_BASE_PATH` | Absolute, or relative to the base path. |

## Bringing Your Own Scripts

Use `subtitles` when the user already has approved translations and wants them
spoken word for word. Every rule below is checked before anything is charged, so
breaking one costs a `422` and not money — but it also costs the user a round
trip, and the first two are easy to get wrong:

- **Cover every language, and only those languages.** The key set must equal
  `languages` exactly; a missing or extra code is refused and the error names it.
  If the user gives you a script for two of three languages, ask for the third
  rather than dropping it — and remember that omitting `languages` altogether
  still means three (`zh_cn`, `es`, `fr`), so all three need a script.
- **Target-language scripts, not source transcripts.** A file of the original
  English lines submitted under `"es"` is a valid-looking script that produces a
  Spanish dub speaking English. The check reads the text and rejects a script
  whose language is not the one it was submitted under, but read what the user
  handed you before sending it.
- **`.srt` or `.vtt` only**, lower-cased extension, up to 1 MiB each. Anything
  else is refused.
- **`export_srt` needs `subtitles`.** There is nothing to align the audio
  against without a script, so on its own it is a `422`.
- **A blocked export does not fail the job.** The dubbed videos are still
  delivered and charged; that language simply has no `.srt`. Report it as a
  missing extra, never as a failed dub, and do not re-run the job for it.
- The `202` carries `subtitle_preflight` — what the check made of each script —
  and the finished task repeats it alongside `subtitle_export` (per-language
  `status`, `alignment_loss`, `issues`). The pipeline stores those numbers as
  JSON of whatever type it recorded, so a count or a loss may arrive as a string
  rather than a number; do not assume one when you surface them.

## Workflow Tips

- **Always ask which language(s)** if the user hasn't said, rather than relying on the `["zh_cn", "es", "fr"]` default — that default silently bills for three languages.
- **Consider `lipsync=false` when nobody is speaking on camera.** Screen recordings, b-roll and voice-over have no mouth to match, and lip-syncing them re-renders the picture for no benefit — the original frames are returned untouched instead, at their own resolution and frame rate. Do not turn it off on a talking-head video unless the user asks: the mouths will visibly keep speaking the original language.
- **Ask for scripts when the user has them.** If they mention approved copy, an existing localization, or a translation they want said exactly, that is `subtitles` — the pipeline's own translation would overwrite it. Do not invent one: a script you wrote yourself is a translation the user never approved, spoken in their video.
- **This is not the music or SFX skills** ([text-to-music](../text-to-music), [video-to-music](../video-to-music), [text-to-sfx](../text-to-sfx), [video-to-sfx](../video-to-sfx)). It doesn't touch music/SFX at all — it translates and re-voices existing speech.
- **Set expectations on time.** Tell the user up front this can take up to ~2 hours and that walking away is fine — the result is recoverable afterward.
- Because there is no free trial here at all, if the account is self-serve and hasn't added a payment method, warn the user before calling rather than letting it fail with `trial_exhausted` (which doesn't even apply — dubbing bills immediately regardless of trial status). Check `get_account_services` (see [account](../account)) if unsure about billing status.

## Recovering a Timed-Out Call

If the call's own long poll is interrupted (e.g. the host itself times out or the session is closed), the error message — or the task id printed to stderr at submission time — gives you a `task_id`. Call `get_sfx_task(task_id)` — `get_generation_task(task_id)` on the hosted server — to check status and download finished files once ready; see [task-recovery](../task-recovery).

## Output Files

One `.mp4` per requested language, named `dubbing-<first 8 chars of the task id>.<language>.mp4` — there's no prompt to name files after, so all dubbing output shares the task-id-based name.

With `export_srt`, one `.srt` lands beside each video under the same stem —
`dubbing-<first 8 chars of the task id>.<language>.srt` — carrying that
language's own lines re-timed against its delivered audio. A language whose
export was blocked has its video and no `.srt`; that is reported as a note, not
an error. On the CLI the SRTs follow `--output` the same way the videos do
(`--output dubbed.mp4` writes `dubbed.es.mp4` and `dubbed.es.srt`), which is why
`--output` may not itself end in `.srt`.

## Error Handling

Common errors: `401` invalid key, `402` insufficient balance (dubbing has no trial to exhaust — it bills immediately), `413` file too large, `422` invalid parameters or unsupported language code (rejected before any charge), `429` rate limit. See the [account](../account) skill.

A `422` with `code: SUBTITLE_PREFLIGHT_BLOCKED` means a submitted script itself
did not pass the check. The message names the blocked languages and their issue
codes, and `details` carries the per-language report. Nothing was charged — fix
or replace that script and resubmit; do not strip `subtitles` and run the job
anyway, which would silently deliver the pipeline's own translation instead of
the user's approved lines.
