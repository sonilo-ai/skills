# Routing evals

Five trigger evals: does the right skill fire for the right query? They exist
because the v2 rename split two skills into four, and a split only pays for
itself if each half still wins the queries it should. A skill that never loads
is worse than one that is merely imperfect, and nothing else in this repo can
catch that — `tests/validate.py` checks what the prose *claims*, not what an
agent *does* with it.

| Case | Prompt is about | Must load | Must not load |
|---|---|---|---|
| `routing/video-scoring` | a finished video needing a soundtrack | `video-to-music` | `text-to-music` |
| `routing/text-only-music` | a beat for an audio-only podcast | `text-to-music` | `video-to-music` |
| `routing/video-sfx` | foley matched to a fight scene | `video-to-sfx` | `text-to-sfx` |
| `routing/dubbing` | localizing a demo into two languages | `auto-dubbing` | — |
| `routing/music-and-sfx` | one video needing music **and** SFX | `video-to-sound` | `video-to-music`, `video-to-sfx` |

The last one is the case worth having. Splitting `sound-effects` and `music`
created two plausible-but-wrong answers for a combined request, and taking them
separately bills the user twice for what `video_to_sound` does in one charge.

## Running them

```bash
claude plugin eval skills@sonilo-skills          # or a path, or plugin@marketplace
claude plugin eval . --case 'routing-*' --runs 3
```

**`claude plugin eval` is in early access and refuses to run as of CLI 2.1.231**,
so these cases are schema-valid but have not been executed by the harness. What
*has* been verified is every assumption they rest on:

- The schema itself is transcribed from the CLI's own validator in 2.1.231
  (`schema_version` 1.1; grader types `regex`, `tool_order`, `tool_used`,
  `file_exists`, `llm`, `baseline`), because the format is not yet documented
  publicly. Re-check it when the feature ships.
- `tool_used` compares the tool name exactly and tests `input_match` as a JS
  RegExp against the serialized tool input.
- A skill invocation records as tool `Skill` with input
  `{"skill": "skills:<name>"}` — confirmed by running the video-scoring prompt
  headlessly and reading the tool call off the stream:

  ```bash
  claude -p '<prompt>' --output-format stream-json --verbose
  ```

  All five prompts were checked this way against the plugin installed from a
  local marketplace, and each loaded its intended skill.

## These cases cannot spend money

Sonilo's generation tools are `mcp__*`, which the runner gates behind an
explicit `--allow-tools` grant, and each case additionally sets
`allowed_tools: ["Skill"]`. An agent under these cases can load a skill and talk
about it; it cannot call a paid endpoint. Keep it that way — a routing eval that
bills per run will not get run.

`arm: with-only` on every grader is deliberate. The ablation's baseline arm has
no Sonilo skills installed, so "did it load `video-to-music`" is a guaranteed
fail there that measures nothing.

## Adding a case

One directory per case under `evals/`, each holding a `case.yaml`. Write the
prompt the way a user would actually say it — no skill names, no "which skill
would you pick", since naming the choice is the thing being measured. Pair every
`loads-X` grader with an `avoids-Y` grader for whichever wrong skill is most
tempting; a case that only asserts the positive passes even when the agent loads
three skills to get there.
