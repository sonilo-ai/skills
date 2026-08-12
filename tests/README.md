# Validating the skills

`python tests/validate.py` is the whole test suite. It exists because a skills
repo has no build to break: every claim in here is prose, and prose about
another repo's API goes stale silently. It has already caught, on its first
run, a recovery tool named for only one of the two servers, three
behaviour-changing parameters documented nowhere, a `ducking` default that had
been flipped upstream a release earlier, and a key prefix that was never right.

```bash
python tests/validate.py             # offline; what CI runs on every push
python tests/validate.py --refresh   # needs `pip install sonilo-mcp`; re-reads
                                     # the local tool surface from the package
```

## What it checks

| Check | Catches |
|---|---|
| Frontmatter | `name` not matching the directory (installed copies resolve by name), missing fields, a description over the spec's 1024 chars or one that never says "Sonilo" and so never routes |
| Tool names | A tool that exists on neither server; naming `get_sfx_task` without `get_generation_task` (or the reverse) — the two servers use different names for the same tool, so a doc that knows only one breaks for half the users |
| Parameters | A parameter passed in an example that the tool does not have; a behaviour- or cost-changing parameter missing from the skill that covers it (`must_document`) |
| Defaults | A documented default that contradicts the server's schema |
| Banned tokens | Strings that were true once — see `banned_tokens` in `tool_surface.json` |

## Keeping it honest

`tool_surface.json` is the recorded ground truth: the `local` block comes from
introspecting an installed `sonilo-mcp` (`mcp.list_tools()`), the `hosted`
block from `backend/app/mcp_server.py` in the dashboard repo. CI re-installs
the published server weekly and fails if the recorded surface has drifted, so
an upstream rename surfaces here as a red build rather than as a user finding
out the hard way.

When a check needs to change, change the check — and add the case that would
have caught the bug you just fixed by hand.
