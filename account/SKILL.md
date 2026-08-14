---
name: account
description: Check the Sonilo account's available services, rate limits, free-trial allowance, and usage/billing history. Use before calling a paid Sonilo tool to confirm it's available and whether free-trial runs remain, or when the user asks about their Sonilo usage, limits, or billing.
license: MIT
compatibility: Requires Sonilo through either transport — the MCP server connected, or the `sonilo` CLI installed and signed in — plus credentials: a `sonilo login` sign-in, the hosted OAuth plugin, or SONILO_API_KEY. See the setup-api-key skill.
allowed-tools: Bash, Read, Write, mcp__sonilo__*
---

# Sonilo Account

Two free, read-only tools for checking what a Sonilo account can do and how much it's used. Neither makes a charge.

> **Setup:** See the [setup-api-key](../setup-api-key) skill.

## Transport: MCP or CLI

Pick one at the start of the session and stay on it. Do not mix the two inside
a single job, and do not announce the choice.

1. **Sonilo MCP tools visible in this session** (`get_account_services` and friends) — use them. This is the preferred path: it needs no shell, and it is the only one that survives a very long generation. If a call fails to authenticate — rather than failing on its inputs — this transport is not usable in this session: go to 2 instead of retrying it.
2. **No usable Sonilo MCP tools, but `sonilo account` exits 0** — use the CLI commands below. Same API, same account, same credential file. Probe with `sonilo account`, not `sonilo whoami`: whoami exits 0 even when signed out, so it cannot tell the two states apart.
3. **Neither** — stop and run the [setup-api-key](../setup-api-key) skill. Do not call `api.sonilo.com` with curl to work around it; both transports handle uploads, polling and retries that a bare request does not.

## Quick Start

### MCP tool call (recommended)

```
get_account_services()
```

```
get_usage(days=7)
```

### Python (`pip install sonilo`)

```python
from sonilo import Sonilo

client = Sonilo()  # reads SONILO_API_KEY

services = client.account.services()
usage = client.account.usage(days=7)
```

### JavaScript / TypeScript (`npm install sonilo`)

```ts
import { SoniloClient } from "sonilo";

const client = new SoniloClient(); // reads SONILO_API_KEY

const services = await client.account.services();
const usage = await client.account.usage({ days: 7 });
```

### CLI (`npm install -g sonilo-cli` or `pip install sonilo-cli`)

```bash
sonilo account
sonilo usage --days 7
```

`sonilo account` prints the account JSON to stdout and, when the account has a free-trial allowance, one summary line to stderr (`Free trial: text-to-music 1/2 left, ...`) — so `sonilo account | jq .trial` still sees clean JSON.

### cURL (raw REST API, no MCP host)

```bash
curl "https://api.sonilo.com/v1/account/services" -H "Authorization: Bearer $SONILO_API_KEY"
curl "https://api.sonilo.com/v1/account/usage?days=7" -H "Authorization: Bearer $SONILO_API_KEY"
```

## Tools

| Tool | Description |
|------|-------------|
| `get_account_services()` | Available services, rate/concurrency limits, discount factor, max video upload size, and (if the account has one) free-trial allowance per service. |
| `get_usage(days=30)` | Usage summary and per-day breakdown. `days` is 1–365. |

## `get_account_services` Response Shape

```json
{
  "available_services": [...],
  "rpm_limit": 60,
  "concurrency_limit": 4,
  "discount_factor": 1.0,
  "max_upload_size_mb": 300,
  "trial": {
    "text_to_music": {"granted": 2, "used": 0, "remaining": 2},
    "video_to_music": {"granted": 1, "used": 1, "remaining": 0}
  }
}
```

- The `trial` key is **absent entirely** for accounts with no free-trial allowance — treat that as "bills normally," not as an error.
- A `trial` object that's present but has **no entry for a given service** means that service has no free-trial allowance at all and bills from the first call — this is `dubbing`'s situation on every self-serve trial account.
- When `trial[service].remaining` is `0`, calling that service fails with a `402 trial_exhausted` error that no retry fixes.

## Workflow Tips

- **Check before you generate.** Before calling any paid tool (`text_to_music`, `video_to_music`, `text_to_sfx`, `video_to_sfx`, `video_to_video_music`, `video_to_video_sfx`, `video_to_sound`, `video_to_video_sound`, `dubbing`, `audio_ducking`), call `get_account_services()` if you're unsure whether the account has free runs left. If `trial[service].remaining` is `0`, tell the user their free trial for that service is spent and that continuing needs a payment method — don't just attempt the call and surface a raw 402.
- **`dubbing` is billed from the first call, always** — even a trial account with `trial` present will show no entry (or a zero allowance) for it. See the [auto-dubbing](../auto-dubbing) skill's cost warning.
- **Usage reconciliation:** if a generation timed out or failed, use `get_usage` to confirm whether the backend actually completed (and charged) it, rather than assuming nothing happened.
- Rate-limited (`429`)? `get_account_services()` reports `rpm_limit` and `concurrency_limit` so you can tell the user what ceiling they hit.

## Error Handling

Both tools are simple authenticated GETs — expect `401` for an invalid/rotated key. `get_usage` also validates `days` client-side (1–365) before making the request.
