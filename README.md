![Sonilo](https://sonilo.com/homepage/logos/logo_white.png)

# Sonilo Skills

Agent skills for [Sonilo](https://sonilo.com/?utm_source=github&utm_medium=oss&utm_campaign=skills-repo)'s licensed music, sound-effects, dubbing, and audio-ducking API. These skills follow the [Agent Skills specification](https://agentskills.io/specification) and can be used with any compatible AI coding assistant.

Sonilo's flagship capability is **video-to-music**: hand it a finished video and it composes an original soundtrack matched to the cut — the music follows the pacing, motion, and emotion because the model saw them. Every track is licensed and safe for commercial use.

## Installation

These skills follow the community [Agent Skills specification](https://agentskills.io/specification), so any compatible tool can install them via `npx skills add`. This repo is also set up as a **Claude Code plugin marketplace**, so Claude Code users can install the same skills with `/plugin` instead — pick whichever fits your workflow.

### Option 1: `npx skills` (any compatible assistant)

```bash
npx skills add sonilo-ai/skills
```

Or install a single skill:

```bash
npx skills add sonilo-ai/skills/video-to-music
```

### Option 2: Claude Code plugin

```
/plugin marketplace add sonilo-ai/skills
/plugin install skills@sonilo-skills
```

This installs the same eleven skills (`video-to-music`, `text-to-music`, `video-to-sfx`, `text-to-sfx`, `video-to-sound`, `audio-ducking`, `auto-dubbing`, `task-recovery`, `account`, `audio-playback`, `setup-api-key`) as a single Claude Code plugin, discovered directly from their existing top-level directories — no separate copy to keep in sync. It's a skills-only plugin (no MCP server, no bundled tools); see [Configuration](#configuration) below for how to connect the Sonilo MCP server itself.

## Available Skills

| Skill | Description |
|-------|-------------|
| [video-to-music](./video-to-music) | Score a video with original music matched to its pacing and emotion (`video_to_music`, `video_to_video_music`) |
| [text-to-music](./text-to-music) | Generate music from a text prompt alone, no video (`text_to_music`) |
| [video-to-sfx](./video-to-sfx) | Generate sound effects matched to a video, with optional timed segments (`video_to_sfx`, `video_to_video_sfx`) |
| [text-to-sfx](./text-to-sfx) | Generate one sound effect from a text description alone (`text_to_sfx`) |
| [video-to-sound](./video-to-sound) | Generate music **and** SFX for a video in one balanced, single-charge call (`video_to_sound`, `video_to_video_sound`) |
| [audio-ducking](./audio-ducking) | Duck a music bed under a voice track (or a video's voice track) automatically (`audio_ducking`) |
| [auto-dubbing](./auto-dubbing) | Dub a video into other languages with re-voiced speech (`dubbing`) |
| [task-recovery](./task-recovery) | Recover the result of a timed-out generation using its task id (`get_sfx_task`, or `get_generation_task` on the hosted server) |
| [account](./account) | Check available services, limits, free-trial allowance, and usage history (`get_account_services`, `get_usage`) |
| [audio-playback](./audio-playback) | Play a local audio file through the system's speakers (`play_audio`) |
| [setup-api-key](./setup-api-key) | Guide through obtaining a Sonilo API key and connecting the Sonilo MCP server |

### Renamed in v2

Each skill is now named for the tool it documents. If you installed an earlier
version, reinstall under the new name — the old ones no longer exist:

| Was | Now |
|---|---|
| `music` | `text-to-music` (text prompt only) and `video-to-music` (scoring a video) |
| `sound-effects` | `text-to-sfx` (text prompt only) and `video-to-sfx` (matched to a video) |
| `dubbing` | `auto-dubbing` |

### Prompting guidance

Sonilo needs no prompt — the video is the context. When you want control, a
structured audio brief adds your intent (genre, the moment that must hit,
the sounds that must not appear) on top of what the model reads from the
cut. That guidance is folded into the skills themselves (ported from
[sonilo-prompt-assist](https://github.com/sonilo-ai/sonilo-prompt-assist),
now deprecated in favor of this repo):

- [references/preflight.md](./references/preflight.md) — pre-flight before any paid call: inspect the video, duration caps, credits, verification
- [references/music-prompting.md](./references/music-prompting.md) — style-prompt craft for `video_to_music`
- [references/sfx-prompting.md](./references/sfx-prompting.md) — action map → segments craft for `video_to_sfx`
- [references/api-claims.md](./references/api-claims.md) — verified API behavior the guidance relies on

## Configuration

Each skill's Quick Start shows every way to call that capability — pick whichever fits how you're working:

- **MCP, local, signed in** — sign in once with either CLI and the [sonilo-mcp](https://github.com/sonilo-ai/sonilo-mcp) server (0.16.0+) reads the same credential, so the host config holds no secret:

  ```bash
  npm install -g sonilo-cli && sonilo login   # or: pip install sonilo-cli
  claude mcp add sonilo -- uvx sonilo-mcp     # Claude Code
  codex mcp add sonilo -- uvx sonilo-mcp      # Codex
  ```

  Approving in the browser mints a 90-day key named `cli: <hostname>` in `~/.config/sonilo/credentials.json`; `sonilo whoami` shows what is active and `sonilo logout` revokes it.

- **MCP, local, with a key** — for CI, containers, or if you prefer holding one:

  ```bash
  claude mcp add sonilo --env SONILO_API_KEY=sk-... -- uvx sonilo-mcp
  ```

  `SONILO_API_KEY` takes precedence over a sign-in wherever both exist. Get a key from the [Sonilo dashboard](https://platform.sonilo.com/dashboard/api-keys), or use the `setup-api-key` skill for guided setup. See the [sonilo-mcp README](https://github.com/sonilo-ai/sonilo-mcp) for Claude Desktop / Codex setup and the full environment variable reference (`SONILO_API_URL`, `SONILO_MCP_BASE_PATH`, `SONILO_MCP_ALLOW_ANY_PATH`, `TIME_OUT_SECONDS`).

- **MCP, remote (Claude Code only, no API key)** — the [sonilo-claude-plugin](https://github.com/sonilo-ai/sonilo-claude-plugin) connects to a hosted, OAuth-authenticated MCP server (`https://api.sonilo.com/mcp`) instead of running anything locally:

  ```
  /plugin marketplace add sonilo-ai/sonilo-claude-plugin
  /plugin install sonilo@sonilo
  ```

  You sign in with your Sonilo Platform account on first use — no key to copy or configure. It carries the same tool set as the local server — every tool these skills document (music and SFX from text/video, video-to-video, video-to-sound, dubbing, ducking, account/usage).

- **Python / JavaScript SDK, or the `sonilo` CLI** — see [Client Libraries](#client-libraries) below if you're integrating outside an MCP host entirely.

## Client Libraries

Sonilo also ships official client libraries, independent of MCP:

| Library | Install | Repo |
|---|---|---|
| Python SDK | `pip install sonilo` | [sonilo-ai/sonilo-python](https://github.com/sonilo-ai/sonilo-python) |
| JS/TS SDK | `npm install sonilo` | [sonilo-ai/sonilo-js](https://github.com/sonilo-ai/sonilo-js) |
| CLI | `pip install sonilo-cli` or `npm install -g sonilo-cli` | same repos, `sonilo-cli` package |
| Video helpers (local ffmpeg mixing) | `pip install sonilo-video-kit` or `npm install sonilo-video-kit` | same repos, `sonilo-video-kit` package |

Both SDKs read `SONILO_API_KEY` from the environment by default; both CLIs additionally fall back to a `sonilo login` credential when it is not set. Each skill's Quick Start includes Python, JavaScript, and (where a command exists) CLI examples alongside the MCP tool call and raw cURL — use whichever matches your integration; they all hit the same underlying API.

Every generation tool has a 1:1 SDK resource and CLI command (`audio_ducking`, the last holdout, gained both in Python SDK 0.13 / JS SDK 0.14, with the CLI command in PyPI `sonilo-cli` 0.12 / npm `sonilo-cli` 0.13). The one deliberate exception is `play_audio`, which just plays a local file — MCP-only by nature. Where a skill's SDK/CLI coverage differs from its MCP tool in any other way, the skill says so explicitly rather than implying full parity.

## Billing

Tools marked with a cost warning make an API call that may incur charges. Self-serve accounts start with a few free runs per service (no card required) — call `get_account_services` to check `trial[service].remaining` before a paid call. `dubbing` has **zero** free runs and bills per language from the first call. See the [account](./account) skill.

## Evaluations

[`evals/`](./evals) holds five trigger evals — does the right skill fire for the
right query — covering the routing decisions the v2 split put at risk, including
the combined music+SFX request that must reach `video-to-sound` rather than
billing twice for the two separate skills.

```bash
claude plugin eval skills@sonilo-skills
```

`claude plugin eval` is in early access and does not run yet; the cases are
schema-valid and their assumptions verified headlessly. See
[evals/README.md](./evals/README.md) for what was checked and how. Functional
evals — does the call produce correct audio — are still open; contributions
welcome.

## License

MIT
