---
name: setup-api-key
description: Guides users through connecting to Sonilo — either the local MCP server with an API key, the remote OAuth Claude Code plugin with no key at all, or a Python/JS SDK or CLI install. Use when the user needs to configure Sonilo, when Sonilo tools are missing or fail due to a missing/invalid API key, or when the user mentions wanting to use Sonilo for the first time. First checks what's already connected and working, and only runs full setup when needed.
license: MIT
compatibility: Requires internet access to platform.sonilo.com and api.sonilo.com. Exact requirement depends on the chosen path — `claude mcp add`/`/plugin install` for MCP, or just `pip`/`npm` for the SDK and CLI.
---

# Sonilo Setup

Guide the user through connecting to Sonilo. There are several ways in — pick based on what the user is actually doing, not just whichever is listed first:

| Path | Needs an API key? | Best for |
|---|---|---|
| **A. Remote OAuth MCP plugin** (`sonilo-claude-plugin`) | No — OAuth sign-in | Claude Code users who just want to try it fast. Narrower tool coverage (music/SFX from text or video, ducking, account/usage) — no video-to-video, video-to-sound, or dubbing. |
| **B. Local MCP server** (`sonilo-mcp`, this repo's skills) | Yes | Any MCP host (Claude Code, Claude Desktop, Codex). Full tool coverage — every skill in this repo. |
| **C. Python/JS SDK or CLI, no MCP** | Yes | Building an app or script directly against the API, or scripting from a shell — not using an MCP-capable agent at all. |

If the user is in Claude Code and just wants to test Sonilo with the least friction, lead with **Path A**. If they need the full tool set, or aren't on Claude Code, use **Path B**. If they're not working through an agent at all, point them at **Path C** and stop — the rest of this skill (API key, MCP config) doesn't apply.

## Path A: Remote OAuth plugin (Claude Code only, no API key)

```
claude
/plugin marketplace add sonilo-ai/sonilo-claude-plugin
/plugin install sonilo@sonilo
```

The first Sonilo tool call opens the browser to sign in to a **Sonilo Platform** account (platform.sonilo.com — separate from a consumer sonilo.com account) and approve access. Claude Code stores the resulting token per-user in the OS keychain; nothing to copy, paste, or configure. Review or disconnect anytime from `/mcp`.

This connects to a single hosted endpoint (`https://api.sonilo.com/mcp`, OAuth 2.1 + PKCE) with a smaller capability set than the local server — don't promise the user tools this path doesn't have (video-to-video music/SFX, video-to-sound, dubbing). If they need those, switch to Path B.

## Path B: Local MCP server with an API key

### Step 0: Check what's already set up

1. Check whether a `sonilo` MCP server is already connected (e.g. `text_to_music`, `get_account_services`, or any other Sonilo tool is available to call).
2. If tools are available, check whether `SONILO_API_KEY` is already valid by calling the free, read-only `get_account_services()` tool.
3. Do not print, quote, or repeat the key. If you mention it, redact it.
4. **If the call succeeds:** tell the user Sonilo is already configured and working. Skip the rest of this workflow. Ask whether they want to rotate the key; if not, stop.
5. **If tools exist but the call fails (401):** the key is invalid/expired — continue to Step 2 (key only, MCP server is already connected).
6. **If no Sonilo tools exist at all:** continue to Step 1 (full setup).

### Step 1: Get an API key

Tell the user:

> Get your Sonilo API key from the dashboard: https://platform.sonilo.com/dashboard/api-keys
>
> (Need an account? Sign up there first — self-serve accounts start with a few free generation runs on most endpoints, no card required.)
>
> Once you have a key (it looks like `sks_...`), tell me and I'll connect it — don't paste it directly into this chat if you can avoid it; I'll wire it into the MCP server config instead.

### Step 2: Connect the MCP server

Once the user has a key, connect the `sonilo` MCP server with it. Prefer the CLI form when the host supports it:

```bash
claude mcp add sonilo --env SONILO_API_KEY=sks_... -- uvx sonilo-mcp
```

For hosts without that CLI (Claude Desktop, Codex), edit the MCP config directly:

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "sonilo": {
      "command": "uvx",
      "args": ["sonilo-mcp"],
      "env": { "SONILO_API_KEY": "sks_..." }
    }
  }
}
```

**Codex** (`~/.codex/config.toml`):

```toml
[mcp_servers.sonilo]
command = "uvx"
args = ["sonilo-mcp"]

[mcp_servers.sonilo.env]
SONILO_API_KEY = "sks_..."
```

Both require the `uv` package manager (provides `uvx`): `curl -LsSf https://astral.sh/uv/install.sh | sh` if not already installed. After editing a config file directly, tell the user to restart the host app (Claude Desktop/Codex) — a `claude mcp add` in Claude Code takes effect on the next session without a restart.

### Step 3: Validate

After connecting, call `get_account_services()`:

- **Succeeds:** confirm Sonilo is configured and working. Mention `get_account_services()` also shows what free-trial runs remain per service.
- **Fails (401):** the key is wrong — point back to the dashboard link in Step 1 and ask for a corrected key, then retry this step.
- **No Sonilo tools appear at all:** the MCP server itself isn't connected — re-check Step 2's config location and confirm the host was restarted/reloaded.

## Path C: Python/JS SDK or CLI (no MCP)

Not every integration goes through an MCP host. If the user is writing code or scripting from a shell:

```bash
pip install sonilo          # Python SDK
npm install sonilo          # JS/TS SDK
pip install sonilo-cli      # Python-distributed CLI
npm install -g sonilo-cli   # npm-distributed CLI
```

Same API key as Path B — get one from https://platform.sonilo.com/dashboard/api-keys and set it as `SONILO_API_KEY` in the environment (both SDKs and both CLIs read it automatically; no MCP config, `claude mcp add`, or plugin install involved). Validate with the SDK's own account call (`client.account.services()` / `sonilo.account.services()`) or `sonilo account` on the CLI.

## Optional Configuration (Path B: local MCP server)

Mention these only if relevant to what the user is trying to do — they all have sane defaults:

| Variable | Default | When to mention it |
|---|---|---|
| `SONILO_API_URL` | `https://api.sonilo.com` | Only for a non-default deployment. |
| `SONILO_MCP_BASE_PATH` | `~/Desktop` | Where generated files are saved by default, and the base for relative input paths. Suggest changing it if the user wants output elsewhere. |
| `SONILO_MCP_ALLOW_ANY_PATH` | `false` | Set `true` only if the user needs to read/write files outside `SONILO_MCP_BASE_PATH` — explain this widens the tool's file-system access before suggesting it. |
| `TIME_OUT_SECONDS` | `600` | Raise this if the user hits generation timeouts on long videos — note that `get_sfx_task` (see [task-recovery](../task-recovery)) can always recover a timed-out result regardless of this setting. |

## Safety Rules

- Never ask the user to paste an API key, token, or secret directly into chat if a config-file or `claude mcp add` path is available.
- Never print or echo the key's value once configured.
- Point users at the dashboard (https://platform.sonilo.com/dashboard/api-keys) to create or rotate keys, and at https://platform.sonilo.com/dashboard/billing for billing/top-up — never fabricate either URL's content.
