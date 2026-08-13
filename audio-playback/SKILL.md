---
name: audio-playback
description: Play a local audio file through the system's default speakers using Sonilo's MCP server. Use after generating a track with Sonilo (or for any local WAV/MP3/M4A/AAC/OGG/FLAC file) when the user wants to hear it immediately instead of just getting the saved path.
license: MIT
compatibility: Requires the Sonilo MCP server connected — this is the one skill with no CLI equivalent, since `play_audio` exists only as an MCP tool. Does not require SONILO_API_KEY or network access — playback is entirely local. macOS and Linux use a native system player (afplay / mpg123 or aplay) when available; on Windows, and on Linux without a native player, this falls back to the sounddevice and soundfile Python packages plus PortAudio (brew install portaudio on macOS / apt-get install libportaudio2 on Debian-Ubuntu).
allowed-tools: Bash, Read, mcp__sonilo__*
---

# Sonilo Audio Playback

Play a local audio file out loud through the system's default output device. This is the one Sonilo tool that makes **no network call** — it's pure local playback, useful right after a generation so the user can hear the result without leaving the conversation.

> **Setup:** just needs the Sonilo MCP server connected — no API key required (see [setup-api-key](../setup-api-key) if the server itself isn't connected yet).

## Quick Start

### MCP tool call

```
play_audio(input_file_path="~/Desktop/thunder.m4a")
```

There is no REST, Python/JS SDK, or CLI equivalent — this is local-only playback specific to the MCP server, not a Sonilo API call at all. If you're integrating via the SDK or CLI instead of MCP, just play the saved file with whatever your own language/platform normally uses for local audio playback.

## Tool

| Tool | Description |
|------|-------------|
| `play_audio(input_file_path)` | Play a local audio file through the system's default speakers. |

## Parameters

| Parameter | Type | Notes |
|-----------|------|-------|
| `input_file_path` | string | Absolute path, or relative to `SONILO_MCP_BASE_PATH`. Supports `.wav/.mp3/.m4a/.aac/.ogg/.flac`. |

## Workflow Tips

- **Natural follow-up after any generation tool.** Once `text_to_music`, `text_to_sfx`, `video_to_music`, etc. return a saved path, offer (or default, if the user's phrasing implies it — e.g. "play what you just made") to call `play_audio` on that same path.
- **Platform playback path:** macOS uses `afplay`; Linux prefers `mpg123` for `.mp3` or `aplay` otherwise. **Windows has no native-player branch at all** and always falls back to the `sounddevice`/`soundfile` Python packages, same as Linux when neither `mpg123` nor `aplay` is installed — that fallback needs the system `PortAudio` library installed separately (`brew install portaudio` on macOS, `sudo apt-get install libportaudio2` on Debian/Ubuntu). Everything else in this repo works without PortAudio.
- Respects the same file-access confinement as every other tool: a path outside `SONILO_MCP_BASE_PATH` is rejected unless `SONILO_MCP_ALLOW_ANY_PATH=true` is set.

## Error Handling

Raises if the file doesn't exist, isn't a recognized audio format, is outside the confined base path, or if no player is available on the platform (with a message naming what's missing).
