---
name: setup-api-key
description: Guides users through connecting to Sonilo — signing in with `sonilo login` (OAuth, no key), the remote OAuth Claude Code plugin, or an API key for CI and headless use. Use when the user needs to configure Sonilo, wants to sign in or connect their Sonilo account, when Sonilo tools are missing, or when a call fails because no key or credential is available. First checks what already works, and only runs full setup when needed.
license: MIT
compatibility: Requires internet access to platform.sonilo.com and api.sonilo.com. Exact requirement depends on the chosen path — a CLI install plus a browser for `sonilo login`, `claude mcp add`/`/plugin install` for MCP, or just `pip`/`npm` for the SDKs.
---

# Sonilo Setup

Guide the user through connecting to Sonilo. There are several ways in — pick based on what the user is actually doing, not just whichever is listed first:

| Path | Needs an API key? | Best for |
|---|---|---|
| **A. `sonilo login`** (CLI sign-in, credential shared with the local MCP server) | No — OAuth in the browser | Anyone on a machine with a browser. One sign-in covers the CLI *and* `uvx sonilo-mcp`, so the MCP config carries no secret. |
| **B. Remote OAuth MCP plugin** (`sonilo-claude-plugin`) | No — OAuth sign-in | Claude Code users who want nothing running locally. Full tool coverage. |
| **C. API key** (`SONILO_API_KEY`) | Yes | CI, containers, headless boxes, and anyone who prefers holding a key. Works with every client. |

Choosing:

- On a machine with a browser and any MCP host → **Path A**. It is the shortest path and leaves no secret in a config file.
- Claude Code specifically, and nothing local wanted → **Path B**.
- No browser (CI, a container, a remote box), or the user says they already have a key → **Path C**.
- Not working through an agent at all (writing code, scripting a shell) → **Path D** at the end; the MCP configuration in A–C does not apply.

## Step 0: Check what already works (all paths)

Do this before changing anything — the answer is often "nothing to do".

There are two transports, and either one is enough. Probe both before
concluding that nothing is set up.

1. **MCP:** is a `sonilo` MCP server connected (any Sonilo tool, e.g. `text_to_music` or `get_account_services`, available to call)? If so, call the free, read-only `get_account_services()`.
2. **CLI:** if there are no Sonilo tools, run `sonilo account` — the same free, read-only call as above. Exit code 0 means the CLI is installed, signed in, and reaching the API, and the skills can drive it directly. **Do not probe with `sonilo whoami`:** it exits 0 even when signed out, so it cannot separate the two states, and on an account with no display name it prints an empty `account:` line that reads like a broken credential. It is worth running only to *show* which account is active, never to decide.
3. **Either one succeeds:** Sonilo is configured and working. Say so and stop. Ask only whether they want to rotate credentials.
4. **Fails with 401:** authentication is stale, not missing. If they signed in with `sonilo login`, the key may have expired (90 days) or been revoked — `sonilo login` again fixes it. Otherwise the key is wrong: continue at Path C.
5. **Neither responds:** nothing is connected — pick a path below and run it. MCP is the better default (it needs no shell, and it is the only transport that survives a dubbing job's two-hour poll), but a CLI that is installed and signed in is a complete setup on its own; do not make someone configure MCP they will not use.

Never print, quote, or echo a key or the contents of the credential file. If you must refer to one, redact it.

## Path A: `sonilo login` (no API key, any MCP host)

One sign-in, then both the CLI and the local MCP server are authenticated — the
CLI writes a credential to `~/.config/sonilo/credentials.json` and
`sonilo-mcp` (0.16.0 and later) reads it.

```bash
npm install -g sonilo-cli     # or: pip install sonilo-cli
sonilo login
```

The CLI prints a one-time code and opens the browser to
platform.sonilo.com. The user signs in to their **Sonilo Platform** account
(separate from a consumer sonilo.com account), confirms the code matches what
the terminal printed, and approves. On a machine without a browser, add
`--no-browser` and have them approve the printed URL from another device.

Then add the MCP server with **no secret in the config**:

```bash
claude mcp add sonilo -- uvx sonilo-mcp     # Claude Code
codex mcp add sonilo -- uvx sonilo-mcp      # Codex
```

For Claude Desktop, the whole config is:

```json
{
  "mcpServers": {
    "sonilo": { "command": "uvx", "args": ["sonilo-mcp"], "env": {} }
  }
}
```

Both need the `uv` package manager (provides `uvx`): install it with
`brew install uv` (macOS), `pipx install uv` / `pip install uv`, or
`winget install --id=astral-sh.uv` (Windows) — other methods at
https://docs.astral.sh/uv/getting-started/installation/.

Worth telling the user up front:

- Approving mints an ordinary API key on their account, named `cli: <hostname>`, that **expires after 90 days** and is visible and revocable at https://platform.sonilo.com/dashboard/api-keys.
- `sonilo whoami` shows which account and source is active; `sonilo logout` revokes the key server-side and then forgets it locally.
- **An exported `SONILO_API_KEY` takes precedence over the sign-in.** If tools authenticate as an unexpected account, check for that variable first — `sonilo whoami` says so explicitly when it is set.
- Sign-in is for humans. Provisioned/POC accounts are issued a key by Sonilo and cannot use `sonilo login`; those users belong on Path C.

Validate with `get_account_services()`, exactly as in Step 0.

## Path B: Remote OAuth plugin (Claude Code only, no API key)

```
claude
/plugin marketplace add sonilo-ai/sonilo-claude-plugin
/plugin install sonilo@sonilo
```

The first Sonilo tool call opens the browser to sign in to a **Sonilo Platform** account (platform.sonilo.com — separate from a consumer sonilo.com account) and approve access. Claude Code stores the resulting token per-user in the OS keychain; nothing to copy, paste, or configure. Review or disconnect anytime from `/mcp`.

This connects to a single hosted endpoint (`https://api.sonilo.com/mcp`, OAuth 2.1 + PKCE) that carries the same tool set as the local server (Paths A and C): music/SFX from text or video, video-to-video music/SFX, video-to-sound, video-to-video-sound, dubbing, audio ducking, and account/usage. Paths A and C are still the better fit for MCP hosts other than Claude Code, or for users who prefer holding and managing their own key.

## Path C: API key (CI, containers, or by preference)

### Step 1: Get an API key

Only take this path when Path A does not fit — no browser, a provisioned
account, CI, or an explicit preference for holding a key. Tell the user:

> Get your Sonilo API key from the dashboard: https://platform.sonilo.com/dashboard/api-keys
>
> (Need an account? Sign up there first — self-serve accounts start with a few free generation runs on most endpoints, no card required.)
>
> Once you have a key (it looks like `sk-...`), tell me and I'll connect it — don't paste it directly into this chat if you can avoid it; I'll wire it into the MCP server config instead.

### Step 2: Connect the MCP server

Once the user has a key, connect the `sonilo` MCP server with it. Prefer the CLI form when the host supports it:

```bash
claude mcp add sonilo --env SONILO_API_KEY=sk-... -- uvx sonilo-mcp
```

For hosts without that CLI (Claude Desktop, Codex), edit the MCP config directly:

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "sonilo": {
      "command": "uvx",
      "args": ["sonilo-mcp"],
      "env": { "SONILO_API_KEY": "sk-..." }
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
SONILO_API_KEY = "sk-..."
```

Both require the `uv` package manager (provides `uvx`) — if not already installed, use `brew install uv`, `pipx install uv` / `pip install uv`, or `winget install --id=astral-sh.uv` (see https://docs.astral.sh/uv/getting-started/installation/ for other methods). After editing a config file directly, tell the user to restart the host app (Claude Desktop/Codex) — a `claude mcp add` in Claude Code takes effect on the next session without a restart.

### Step 3: Validate

After connecting, call `get_account_services()`:

- **Succeeds:** confirm Sonilo is configured and working. Mention `get_account_services()` also shows what free-trial runs remain per service.
- **Fails (401):** the credential is wrong. On this path that means a bad key — point back to the dashboard link in Step 1 and ask for a corrected one. If the user signed in with `sonilo login` instead, the key behind that sign-in has expired or been revoked: `sonilo login` again.
- **No Sonilo tools appear at all:** the MCP server itself isn't connected — re-check Step 2's config location and confirm the host was restarted/reloaded.

## Path D: Python/JS SDK or CLI (no MCP)

Not every integration goes through an MCP host. If the user is writing code or scripting from a shell:

```bash
pip install sonilo          # Python SDK
npm install sonilo          # JS/TS SDK
pip install sonilo-cli      # Python-distributed CLI
npm install -g sonilo-cli   # npm-distributed CLI
```

Same API key as Path C — get one from https://platform.sonilo.com/dashboard/api-keys and set it as `SONILO_API_KEY` in the environment (both SDKs and both CLIs read it automatically; no MCP config, `claude mcp add`, or plugin install involved). Validate with the SDK's own account call (`client.account.services()` / `sonilo.account.services()`) or `sonilo account` on the CLI.

## Optional Configuration (local MCP server)

Mention these only if relevant to what the user is trying to do — they all have sane defaults:

| Variable | Default | When to mention it |
|---|---|---|
| `SONILO_API_URL` | `https://api.sonilo.com` | Only for a non-default deployment. |
| `SONILO_MCP_BASE_PATH` | `~/Desktop` | Where generated files are saved by default, and the base for relative input paths. Suggest changing it if the user wants output elsewhere. |
| `SONILO_MCP_ALLOW_ANY_PATH` | `false` | Set `true` only if the user needs to read/write files outside `SONILO_MCP_BASE_PATH` — explain this widens the tool's file-system access before suggesting it. |
| `TIME_OUT_SECONDS` | `600` | Raise this if the user hits generation timeouts on long videos — note that `get_sfx_task` / `get_generation_task` (see [task-recovery](../task-recovery)) can always recover a timed-out result regardless of this setting. |

## Safety Rules

- Never ask the user to paste an API key, token, or secret directly into chat if a config-file or `claude mcp add` path is available.
- Never print or echo the key's value once configured.
- Point users at the dashboard (https://platform.sonilo.com/dashboard/api-keys) to create or rotate keys, and at https://platform.sonilo.com/dashboard/billing for billing/top-up — never fabricate either URL's content.
