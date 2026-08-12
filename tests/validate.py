#!/usr/bin/env python3
"""Validate this repo's skills against the tool surfaces they claim to describe.

A skills repo has no build to break, so nothing here has ever failed loudly when
a claim went stale — and claims did go stale: a tool renamed on one server, a
parameter that changes what the default output *contains* shipping undocumented,
a key prefix that was never right. This script is the missing failure.

What it checks:

  1. Frontmatter — `name` matches the directory, required fields present, the
     description within the Agent Skills spec's 1024-char limit.
  2. Tool names — every `tool_name(` mentioned in prose exists on at least one
     server, and anything that exists on only one is labelled as such. This is
     the check that catches `get_sfx_task` being told to hosted-plugin users, who
     have `get_generation_task` instead.
  3. Parameters — every parameter a skill passes exists on that tool, and every
     parameter in `must_document` appears somewhere in the repo. The first
     direction catches invention; the second catches silence about a flag that
     changes cost or output.
  4. Banned tokens — strings that were true once (see tool_surface.json).

Run: python tests/validate.py            # offline, this is what CI runs
     python tests/validate.py --refresh  # regenerate the local surface from an
                                         # installed sonilo-mcp, then check
Stdlib only, on purpose: CI needs no install step to run the offline checks.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SURFACE = Path(__file__).resolve().parent / "tool_surface.json"
DESCRIPTION_LIMIT = 1024  # Agent Skills spec

failures: list[str] = []
notes: list[str] = []


def fail(where: str, message: str) -> None:
    failures.append(f"{where}: {message}")


def note(message: str) -> None:
    notes.append(message)


def parse_frontmatter(text: str, where: str) -> dict:
    """Read the leading `---` block. Deliberately not a YAML parser: these files
    are flat `key: value` pairs and a dependency-free CI is worth more than
    supporting nesting nobody uses."""
    if not text.startswith("---\n"):
        fail(where, "no frontmatter block")
        return {}
    end = text.find("\n---\n", 3)
    if end == -1:
        fail(where, "frontmatter block is never closed")
        return {}
    out: dict[str, str] = {}
    key = None
    for line in text[4:end].splitlines():
        m = re.match(r"^([a-zA-Z_-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            out[key] = m.group(2).strip()
        elif key and line.startswith((" ", "\t")):
            out[key] += " " + line.strip()  # folded continuation
    return out


def check_frontmatter(skill_dir: Path, text: str) -> None:
    where = f"{skill_dir.name}/SKILL.md"
    fm = parse_frontmatter(text, where)
    if not fm:
        return
    if fm.get("name") != skill_dir.name:
        fail(where, f"name is {fm.get('name')!r} but the directory is {skill_dir.name!r} — "
                    "the spec ties them together and installed copies resolve by name")
    for field in ("description", "license"):
        if not fm.get(field):
            fail(where, f"missing `{field}`")
    desc = fm.get("description", "")
    if len(desc) > DESCRIPTION_LIMIT:
        fail(where, f"description is {len(desc)} chars, over the spec's {DESCRIPTION_LIMIT}")
    # The description is what routes an agent to the skill. One that never names
    # the product will not be selected when the user says "Sonilo".
    if "sonilo" not in desc.lower():
        fail(where, "description never mentions Sonilo, so it cannot route on the product name")


def markdown_files() -> list[Path]:
    files = sorted(ROOT.glob("*/SKILL.md")) + [ROOT / "README.md"]
    files += sorted((ROOT / "references").glob("*.md"))
    return [f for f in files if f.exists()]


def check_tool_names(surface: dict, docs: dict[Path, str]) -> None:
    hosted, local = surface["hosted"], surface["local"]
    known = set(hosted) | set(local)
    hosted_only = set(hosted) - set(local)
    local_only = set(local) - set(hosted)

    for path, text in docs.items():
        rel = path.relative_to(ROOT)
        # A call site looks like `tool_name(` — enough to distinguish a real
        # mention from prose using the same words.
        for name in sorted(set(re.findall(r"\b([a-z][a-z0-9_]{3,})\(", text))):
            if name in known or "_" not in name:
                continue
            # Only flag things shaped like our tools, not arbitrary code.
            if re.match(r"^(text|video|audio|get|play|dubbing)_", name):
                fail(str(rel), f"mentions `{name}(` which exists on neither server")

    # The divergent-name trap: naming one server's tool without the other's.
    for path, text in docs.items():
        rel = path.relative_to(ROOT)
        for name in sorted(local_only | hosted_only):
            if not re.search(rf"\b{name}\b", text):
                continue
            counterpart = {"get_sfx_task": "get_generation_task",
                           "get_generation_task": "get_sfx_task"}.get(name)
            if counterpart and not re.search(rf"\b{counterpart}\b", text):
                which = "local" if name in local_only else "hosted"
                fail(str(rel), f"names `{name}` (the {which} server's name) without "
                               f"`{counterpart}` — the other half of the users have that one")


def check_parameters(surface: dict, docs: dict[Path, str]) -> None:
    hosted, local = surface["hosted"], surface["local"]
    all_text = "\n".join(docs.values())

    # Direction 1: a parameter shown being passed must exist on that tool.
    for path, text in docs.items():
        rel = path.relative_to(ROOT)
        for call in re.finditer(r"\b([a-z][a-z0-9_]{3,})\(([^)]{0,400})\)", text):
            tool, args = call.group(1), call.group(2)
            valid = set(hosted.get(tool, [])) | set(local.get(tool, []))
            if not valid and tool not in hosted and tool not in local:
                continue
            for param in re.findall(r"\b([a-z][a-z0-9_]*)\s*=", args):
                if param not in valid:
                    fail(str(rel), f"`{tool}({param}=…)` — {tool} has no `{param}` parameter")

    # Direction 2: the behaviour-changing parameters must be documented in a
    # SKILL.md that covers the tool — not merely somewhere in the repo. An agent
    # loads the skill it was routed to; a note buried in references/ that it
    # never opens does not inform the call it is about to make.
    skills = {p: t for p, t in docs.items() if p.name == "SKILL.md"}
    for tool, params in surface["must_document"].items():
        if tool.startswith("_"):
            continue
        covering = [p for p, t in skills.items() if re.search(rf"\b{tool}\b", t)]
        if not covering:
            fail("coverage", f"no skill mentions `{tool}` at all")
            continue
        for param in params:
            if any(re.search(rf"\b{param}\b", skills[p]) for p in covering):
                continue
            where = ", ".join(sorted(p.parent.name for p in covering))
            elsewhere = " (mentioned only outside the skills)" if re.search(
                rf"\b{param}\b", all_text) else ""
            fail("coverage", f"`{param}` (on {tool}) is missing from the skill(s) that "
                             f"cover it — {where}{elsewhere}; it changes cost or what "
                             "the output contains")


def check_documented_defaults(surface: dict, docs: dict[Path, str]) -> None:
    """A default the docs state must match the schema.

    This is its own check because a wrong default is invisible to every other
    one: the parameter exists, it is documented, the prose reads fine — and the
    agent still calls the tool expecting the opposite behaviour. `ducking` was
    documented as defaulting on for a release after the API flipped it off.

    Only parameter tables are inspected: a row shaped
    `| \\`name\\` | type | default | notes |`.
    """
    defaults: dict[str, str] = surface.get("defaults", {})
    if not defaults:
        return
    for path, text in docs.items():
        if path.name != "SKILL.md":
            continue
        rel = path.relative_to(ROOT)
        for row in re.finditer(r"^\|\s*`([a-z_]+)`\s*\|([^|]*)\|([^|]*)\|", text, re.M):
            param, stated = row.group(1), row.group(3).strip()
            want = defaults.get(param)
            if want is None:
                continue
            # The stated cell may carry qualifiers ("`false` for x, ON for y").
            # Only a cell that names the opposite boolean and never the right
            # one is wrong; anything ambiguous is left to a human.
            opposite = {"false": "true", "true": "false"}.get(want)
            if not opposite:
                continue
            has_right = re.search(rf"\b{want}\b", stated, re.I)
            has_wrong = re.search(rf"\b{opposite}\b|\bON\b", stated) if want == "false" \
                else re.search(rf"\b{opposite}\b|\boff\b", stated, re.I)
            if has_wrong and not has_right:
                fail(str(rel), f"documents `{param}` as defaulting to {stated!r}, but the "
                               f"tool schema says {want!r}")


def check_banned_tokens(surface: dict, docs: dict[Path, str]) -> None:
    for path, text in docs.items():
        rel = path.relative_to(ROOT)
        for token, instead in surface["banned_tokens"].items():
            if token.startswith("_"):
                continue
            if token in text:
                fail(str(rel), f"contains {token!r} — {instead}")


def check_key_prefix(docs: dict[Path, str]) -> None:
    """Keys are `sk-` + hex. `sk_...` reads as correct and is not."""
    for path, text in docs.items():
        rel = path.relative_to(ROOT)
        for m in re.finditer(r"\bsk[_s]+[a-z0-9]*\.{0,3}", text):
            if not m.group(0).startswith("sk-"):
                fail(str(rel), f"shows {m.group(0)!r}; minted keys look like `sk-…`")


def refresh_local_surface(surface: dict) -> None:
    """Regenerate the `local` block by introspecting an installed sonilo-mcp."""
    import asyncio
    import logging

    logging.disable(logging.WARNING)
    try:
        from sonilo_mcp.api import mcp  # type: ignore
    except ImportError:
        print("--refresh needs sonilo-mcp installed: pip install sonilo-mcp", file=sys.stderr)
        raise SystemExit(2)
    tools = asyncio.run(mcp.list_tools())
    fresh = {t.name: list((t.inputSchema or {}).get("properties", {}).keys()) for t in tools}
    if fresh != surface["local"]:
        added = set(fresh) - set(surface["local"])
        removed = set(surface["local"]) - set(fresh)
        note(f"local surface refreshed: +{sorted(added) or '[]'} -{sorted(removed) or '[]'}")
        surface["local"] = fresh
        SURFACE.write_text(json.dumps(surface, indent=2) + "\n")
    else:
        note("local surface already matches the installed sonilo-mcp")


def main() -> int:
    surface = json.loads(SURFACE.read_text())
    if "--refresh" in sys.argv:
        refresh_local_surface(surface)

    docs = {p: p.read_text() for p in markdown_files()}
    for skill in sorted(ROOT.glob("*/SKILL.md")):
        check_frontmatter(skill.parent, docs[skill])
    check_tool_names(surface, docs)
    check_parameters(surface, docs)
    check_documented_defaults(surface, docs)
    check_banned_tokens(surface, docs)
    check_key_prefix(docs)

    for line in notes:
        print(f"note: {line}")
    print(f"checked {len(docs)} files, {len(list(ROOT.glob('*/SKILL.md')))} skills, "
          f"{len(surface['hosted'])} hosted tools, {len(surface['local'])} local tools")
    if failures:
        print(f"\n{len(failures)} problem(s):\n", file=sys.stderr)
        for line in failures:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
