#!/usr/bin/env python3
"""
Post-generation copier task.

Runs in the *destination* directory after all template files are rendered.

Responsibilities
----------------
1. Idempotently append agent-harness entries to an existing .gitignore that
   _skip_if_exists preserved. We never duplicate lines; we append only what's
   missing, between fenced markers, so a subsequent `copier update` keeps the
   block tidy.
2. Create the .agents/{skills,subagents} -> .claude/{skills,agents} and
   .opencode/{skills,agents} symlinks. We create them as relative symlinks
   when the platform supports them, and emit a small note otherwise (Windows
   without developer mode). Symlinks make a single source of truth for
   cross-tool agent assets.

This script is deliberately stdlib-only and side-effect-light: it does
nothing destructive, prints a short summary, and exits 0 on success.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable

CWD = Path.cwd()


def _read_answer(key: str, default: str) -> str:
    """Read a single scalar value from .copier-answers.yml.

    Uses PyYAML (already a Copier dependency, so always available when this
    script is invoked by the Copier engine) so quoted strings, inline
    comments, and block scalars all parse correctly. Falls back to ``default``
    if the file is missing, the key is absent, or the value is empty.
    """
    answers = CWD / ".copier-answers.yml"
    if not answers.exists():
        return default
    try:
        import yaml
    except ImportError:
        return default
    data = yaml.safe_load(answers.read_text(encoding="utf-8")) or {}
    value = data.get(key)
    if value is None:
        return default
    return str(value) or default


GITIGNORE_BEGIN = "# >>> ai-agent-harness (managed by copier) >>>"
GITIGNORE_END = "# <<< ai-agent-harness (managed by copier) <<<"

GITIGNORE_BLOCK = [
    "# Personal overrides — never commit",
    "CLAUDE.local.md",
    ".claude/settings.local.json",
    ".claude/.last_*",
    ".claude/checkpoints/",
    ".claude/shell-snapshots/",
    ".opencode/local/",
    ".codex/auth.json",
    ".cursor/settings.local.json",
    "",
    "# Agent scratch space (team decision; comment out to commit)",
    "specs/*/scratch.md",
    ".agents/.cache/",
]


def merge_gitignore(path: Path) -> str:
    """
    Return a message describing what we did to .gitignore.

    - If the file is missing, we do nothing (the template renderer will have
      written one in greenfield mode; in brownfield mode the user likely
      doesn't have one and we don't want to surprise them).
    - If the file is present and already contains our fenced block, we leave
      it alone.
    - Otherwise, append a fresh fenced block at the end of the file.
    """
    if not path.exists():
        return "skip: .gitignore not present"

    content = path.read_text(encoding="utf-8")
    if GITIGNORE_BEGIN in content:
        return "skip: .gitignore already has managed block"

    suffix = "" if content.endswith("\n") else "\n"
    block = "\n".join([GITIGNORE_BEGIN, *GITIGNORE_BLOCK, GITIGNORE_END]) + "\n"
    path.write_text(content + suffix + "\n" + block, encoding="utf-8")
    return "appended managed block to .gitignore"


def _make_relative_symlink(link: Path, target_relative: str) -> str:
    """Create `link` -> `target_relative` if the target exists and the link is missing."""
    if link.exists() or link.is_symlink():
        return f"skip: {link} already exists"
    target_abs = (link.parent / target_relative).resolve()
    if not target_abs.exists():
        return f"skip: target {target_abs} missing"
    try:
        os.symlink(target_relative, link, target_is_directory=True)
    except OSError as e:
        return f"warn: could not symlink {link} -> {target_relative}: {e}"
    return f"linked: {link} -> {target_relative}"


def link_agent_assets() -> Iterable[str]:
    """
    Symlink shared agent assets into tool-specific folders.

    Layout (after this runs):
        .agents/skills/       <- source of truth
        .agents/subagents/    <- source of truth
        .claude/skills        -> ../.agents/skills
        .claude/agents        -> ../.agents/subagents
        .opencode/skills      -> ../.agents/skills
        .opencode/agents      -> ../.agents/subagents
    """
    pairs = [
        (Path(".claude/skills"), "../.agents/skills"),
        (Path(".claude/agents"), "../.agents/subagents"),
        (Path(".opencode/skills"), "../.agents/skills"),
        (Path(".opencode/agents"), "../.agents/subagents"),
    ]
    for link, rel in pairs:
        link.parent.mkdir(parents=True, exist_ok=True)
        yield _make_relative_symlink(link, rel)


def main() -> int:
    messages = []
    messages.append(merge_gitignore(CWD / ".gitignore"))
    messages.extend(link_agent_assets())

    print()
    print("AI agent harness — post-generation summary")
    print("-" * 44)
    for m in messages:
        print(f"  - {m}")
    print()
    verify_cmd = _read_answer("verify_command", "./scripts/verify.sh")
    print("Next steps:")
    print("  1. Open AGENTS.md and tighten it for your project (target ≤200 lines).")
    print(f"  2. Run `{verify_cmd}` to confirm the toolchain wiring.")
    print("  3. Commit and push; subsequent runs use `copier update`.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
