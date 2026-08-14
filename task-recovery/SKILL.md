---
name: task-recovery
description: Recover the result of a timed-out Sonilo generation call using its task_id. Use whenever text_to_sfx, video_to_sfx, video_to_video_music, video_to_video_sfx, video_to_sound, video_to_video_sound, audio_ducking, dubbing, or video_to_music(preserve_speech=true) times out or its call was interrupted — the generation already ran (and was already charged) and its result is still retrievable.
license: MIT
compatibility: Requires Sonilo through either transport — the MCP server connected, or the `sonilo` CLI installed and signed in — plus credentials: a `sonilo login` sign-in, the hosted OAuth plugin, or SONILO_API_KEY. See the setup-api-key skill.
allowed-tools: Bash, Read, Write, mcp__sonilo__*
---

# Sonilo Task Recovery

Every Sonilo generation that runs asynchronously on the backend (SFX, ducking, video-to-video, video-to-sound, dubbing, and `video_to_music(preserve_speech=true)`) is already charged the moment it's accepted — a client-side timeout does **not** stop it or refund it. This tool checks a task's status and, once finished, downloads its result. It never itself charges anything.

> **Setup:** See the [setup-api-key](../setup-api-key) skill.

> This tool is a safety net, not something to call speculatively. Only use it when you actually have a `task_id` — from a timeout error message, or from the `[sonilo-mcp] task submitted: <id>` line a host prints to stderr the moment a task is submitted (this survives even a cancelled call).

## Transport: MCP or CLI

Pick one at the start of the session and stay on it. Do not mix the two inside
a single job, and do not announce the choice.

1. **Sonilo MCP tools visible in this session** (`get_sfx_task` and friends) — use them. This is the preferred path: it needs no shell, and it is the only one that survives a very long generation. If a call fails to authenticate — rather than failing on its inputs — this transport is not usable in this session: go to 2 instead of retrying it.
2. **No usable Sonilo MCP tools, but `sonilo account` exits 0** — use the CLI commands below. Same API, same account, same credential file. Probe with `sonilo account`, not `sonilo whoami`: whoami exits 0 even when signed out, so it cannot tell the two states apart.
3. **Neither** — stop and run the [setup-api-key](../setup-api-key) skill. Do not call `api.sonilo.com` with curl to work around it; both transports handle uploads, polling and retries that a bare request does not.

## Quick Start

### MCP tool call (recommended)

```
get_sfx_task(task_id="a1b2c3d4-...")
```

**The tool has two names.** The local `sonilo-mcp` server calls it
`get_sfx_task`; the hosted OAuth server (the `sonilo-claude-plugin` path) calls
it `get_generation_task(task_id)`. Same job, same arguments — call whichever one
the connected server actually exposes rather than assuming, since only one of
the two exists in any given session.

### Python (`pip install sonilo`)

```python
from sonilo import Sonilo

client = Sonilo()  # reads SONILO_API_KEY

status = client.tasks.get("a1b2c3d4-...")   # single check, never raises on failure
result = client.tasks.wait("a1b2c3d4-...")  # polls until terminal; raises TaskFailedError/TaskTimeoutError
result.save("recovered.wav")
```

`tasks.get`/`tasks.wait` default to parsing an SFX-shaped result. For a task from `dubbing`, `video_to_sound`/`video_to_video_sound`, or async `video_to_music`, pass the matching parser explicitly (`from sonilo.resources.tasks import parse_music_result, parse_sound_result, parse_dubbing_result`) — see [sonilo-python's README](https://github.com/sonilo-ai/sonilo-python#sound-effects-async-tasks) for the exact call shape per task type.

### JavaScript / TypeScript (`npm install sonilo`)

```ts
import { SoniloClient } from "sonilo";

const client = new SoniloClient(); // reads SONILO_API_KEY

const status = await client.tasks.get("a1b2c3d4-...");   // single check
const result = await client.tasks.wait("a1b2c3d4-...", { pollInterval: 2000, timeout: 600_000 });
```

Same caveat as Python: pass the task's actual result type as `wait<T>()`'s generic (e.g. `wait<MusicTaskResult>(...)`) for a non-SFX task — see [sonilo-js's README](https://github.com/sonilo-ai/sonilo-js/tree/main/packages/sonilo#preserve-speech-async).

### CLI (`npm install -g sonilo-cli` or `pip install sonilo-cli`)

```bash
sonilo tasks get a1b2c3d4-...

# npm's sonilo-cli: --poll-interval/--timeout are milliseconds
sonilo tasks wait a1b2c3d4-... --poll-interval 2000 --timeout 120000

# pip's sonilo-cli: the same flags are seconds
sonilo tasks wait a1b2c3d4-... --poll-interval 2 --timeout 600
```

The two `sonilo-cli` packages (npm and pip) aren't the same codebase — double-check which one is installed before assuming a flag's units.

### cURL (raw REST API, no MCP host)

```bash
curl "https://api.sonilo.com/v1/tasks/a1b2c3d4-..." \
  -H "Authorization: Bearer $SONILO_API_KEY"
```

The MCP tool does one status check and, if `status` is terminal, downloads and saves the resulting file(s) for you — it does not poll in a loop.

## Tool

| Tool | Description |
|------|-------------|
| `get_sfx_task(task_id, output_directory?)` | Check a task; if it succeeded, download and save its result file(s). |

## Behavior by Status

| Status | What happens |
|--------|--------------|
| `processing` | Returns a "still processing, try again later" message. No file saved. Call again after a short wait. |
| `succeeded` | Downloads and saves the result — audio for `text_to_sfx`/`video_to_sfx`; a single `.wav` or `.mp4` for `audio_ducking`; a single `.mp4` for `video_to_video_music`/`video_to_video_sfx`/`video_to_video_sound`; a single `.wav` for `video_to_sound`; one `.mp4` per language for `dubbing`; for a `video_to_music(preserve_speech=true)` task, the music stream(s) plus the `vocals` stem plus the `mux`. |
| `failed` | Raises an error including the backend's error code/message and whether the charge was **refunded** — check this before telling the user they've been billed for nothing. |
| task id not found (404) | The id is wrong/typo'd, or belongs to a purely streaming call (`text_to_music`, or `video_to_music` without `preserve_speech`/`ducking`/`output_format="wav"`) — those have no task at all and can't be recovered this way. Nothing to retry. |
| any other status (not `processing`/`succeeded`/`failed`) | Raised as an "unexpected task status" error naming the task id. Treat as transient — this is a backend state this tool doesn't otherwise special-case — and call `get_sfx_task(task_id)` again shortly. |

## Workflow Tips

- **Safe to call repeatedly.** If a result was already downloaded to disk, a later call reports "Already downloaded" instead of re-fetching a duplicate copy — you won't accumulate `-1`/`-2` suffixed files from checking twice.
- **Don't confuse this with `get_account_services`/`get_usage`** (the [account](../account) skill) — this tool is about recovering one specific generation's output, not account-level info.
- If a `failed` task shows `refunded: false`, point the user at `get_usage` to reconcile billing, and note the charge stands.
- `output_directory` defaults to `SONILO_MCP_BASE_PATH`, same as every generation tool — pass the same directory you'd have used for the original call if you want the recovered file alongside other output.

## Error Handling

A transient failure while checking (e.g. backend 5xx) does not mean the result is lost — re-run `get_sfx_task(task_id)` shortly after. A `401`/`402` here means the *check* failed (key rotated, account suspended) — the task itself was already charged and its result is still on the backend; resolve the auth/billing issue, then call `get_sfx_task` again.
