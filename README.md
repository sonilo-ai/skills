![Sonilo](https://sonilo.com/homepage/logos/logo_white.png)

# Sonilo Skills

Agent skills for [Sonilo](https://sonilo.com)'s licensed music, sound-effects, dubbing, and audio-ducking API. These skills follow the [Agent Skills specification](https://agentskills.io/specification) and can be used with any compatible AI coding assistant.

Sonilo's flagship capability is **video-to-music**: hand it a finished video and it composes an original soundtrack matched to the cut — the music follows the pacing, motion, and emotion because the model saw them. Every track is licensed and safe for commercial use.

## Installation

These skills follow the community [Agent Skills specification](https://agentskills.io/specification), so any compatible tool can install them via `npx skills add`. This repo is also set up as a **Claude Code plugin marketplace**, so Claude Code users can install the same skills with `/plugin` instead — pick whichever fits your workflow.

### Option 1: `npx skills` (any compatible assistant)

```bash
npx skills add sonilo-ai/skills
```

Or install a single skill:

```bash
npx skills add sonilo-ai/skills/music
```

### Option 2: Claude Code plugin

```
/plugin marketplace add sonilo-ai/skills
/plugin install skills@sonilo-skills
```

This installs the same nine skills (`music`, `sound-effects`, `video-to-sound`, `audio-ducking`, `dubbing`, `task-recovery`, `account`, `audio-playback`, `setup-api-key`) as a single Claude Code plugin, discovered directly from their existing top-level directories — no separate copy to keep in sync. It's a skills-only plugin (no MCP server, no bundled tools); see [Configuration](#configuration) below for how to connect the Sonilo MCP server itself.

## Available Skills

| Skill | Description |
|-------|-------------|
| [music](./music) | Generate music from text or score it to a video's pacing and emotion (`text_to_music`, `video_to_music`, `video_to_video_music`) |
| [sound-effects](./sound-effects) | Generate sound effects from text or match them to a video, with optional timed segments (`text_to_sfx`, `video_to_sfx`, `video_to_video_sfx`) |
| [video-to-sound](./video-to-sound) | Generate music **and** SFX for a video in one balanced, single-charge call (`video_to_sound`, `video_to_video_sound`) |
| [audio-ducking](./audio-ducking) | Duck a music bed under a voice track (or a video's voice track) automatically (`audio_ducking`) |
| [dubbing](./dubbing) | Dub a video into other languages with re-voiced speech (`dubbing`) |
| [task-recovery](./task-recovery) | Recover the result of a timed-out generation using its task id (`get_sfx_task`) |
| [account](./account) | Check available services, limits, free-trial allowance, and usage history (`get_account_services`, `get_usage`) |
| [audio-playback](./audio-playback) | Play a local audio file through the system's speakers (`play_audio`) |
| [setup-api-key](./setup-api-key) | Guide through obtaining a Sonilo API key and connecting the Sonilo MCP server |

### Prompting guidance

Sonilo needs no prompt — the video is the context. When you want control, a
structured audio brief adds your intent (genre, the moment that must hit,
the sounds that must not appear) on top of what the model reads from the
cut. That guidance is folded into the skills themselves (ported from
[sonilo-prompt-assist](https://github.com/sonilo-ai/sonilo-prompt-assist),
now deprecated in favor of this repo):

- [references/preflight.md](./references/preflight.md) — pre-flight before any paid call: inspect the video, duration caps, credits, verification
- [music/prompting.md](./music/prompting.md) — style-prompt craft for `video_to_music`
- [sound-effects/prompting.md](./sound-effects/prompting.md) — action map → segments craft for `video_to_sfx`
- [references/api-claims.md](./references/api-claims.md) — verified API behavior the guidance relies on

## Configuration

Each skill's Quick Start shows every way to call that capability — pick whichever fits how you're working:

- **MCP, local** — the [sonilo-mcp](https://github.com/sonilo-ai/sonilo-mcp) server, connected with an API key:

  ```bash
  claude mcp add sonilo --env SONILO_API_KEY=sks_... -- uvx sonilo-mcp
  ```

  Get your API key from the [Sonilo dashboard](https://platform.sonilo.com/dashboard/api-keys), or use the `setup-api-key` skill for guided setup. See the [sonilo-mcp README](https://github.com/sonilo-ai/sonilo-mcp) for Claude Desktop / Codex setup and the full environment variable reference (`SONILO_API_URL`, `SONILO_MCP_BASE_PATH`, `SONILO_MCP_ALLOW_ANY_PATH`, `TIME_OUT_SECONDS`).

- **MCP, remote (Claude Code only, no API key)** — the [sonilo-claude-plugin](https://github.com/sonilo-ai/sonilo-claude-plugin) connects to a hosted, OAuth-authenticated MCP server (`https://api.sonilo.com/mcp`) instead of running anything locally:

  ```
  /plugin marketplace add sonilo-ai/sonilo-claude-plugin
  /plugin install sonilo@sonilo
  ```

  You sign in with your Sonilo Platform account on first use — no key to copy or configure. Its tool surface is narrower than the local server's (music and SFX from text/video, ducking, account/usage) — it does not cover every tool these skills document (e.g. video-to-video, video-to-sound, dubbing).

- **Python / JavaScript SDK, or the `sonilo` CLI** — see [Client Libraries](#client-libraries) below if you're integrating outside an MCP host entirely.

## Client Libraries

Sonilo also ships official client libraries, independent of MCP:

| Library | Install | Repo |
|---|---|---|
| Python SDK | `pip install sonilo` | [sonilo-ai/sonilo-python](https://github.com/sonilo-ai/sonilo-python) |
| JS/TS SDK | `npm install sonilo` | [sonilo-ai/sonilo-js](https://github.com/sonilo-ai/sonilo-js) |
| CLI | `pip install sonilo-cli` or `npm install -g sonilo-cli` | same repos, `sonilo-cli` package |
| Video helpers (local ffmpeg mixing) | `pip install sonilo-video-kit` or `npm install sonilo-video-kit` | same repos, `sonilo-video-kit` package |

Both SDKs read `SONILO_API_KEY` from the environment by default. Each skill's Quick Start includes Python, JavaScript, and (where a command exists) CLI examples alongside the MCP tool call and raw cURL — use whichever matches your integration; they all hit the same underlying API.

Not every MCP tool has a 1:1 SDK/CLI equivalent — most notably `audio_ducking` has no dedicated SDK resource or CLI command (see the [audio-ducking](./audio-ducking) skill for the closest equivalents). Where a skill's SDK/CLI coverage differs from its MCP tool, the skill says so explicitly rather than implying full parity.

## Billing

Tools marked with a cost warning make an API call that may incur charges. Self-serve accounts start with a few free runs per service (no card required) — call `get_account_services` to check `trial[service].remaining` before a paid call. `dubbing` has **zero** free runs and bills per language from the first call. See the [account](./account) skill.

## Evaluations

Not yet included in this repo. Contributions welcome — the intent is trigger evals (does the right skill fire for the right query) and functional evals (does the tool call produce correct output) per skill.

## License

MIT
