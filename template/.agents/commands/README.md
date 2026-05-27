# Slash commands

Cross-tool slash command definitions live here. Each command is a single
Markdown file with YAML frontmatter:

- `description` — surfaced in the slash-command picker. Required.
- `argument-hint` — placeholder shown after the command name. Optional.
- `allowed-tools` — Claude Code permission allowlist for the command,
  comma-separated. Optional; least-privilege wins. OpenCode ignores
  unknown keys, so the single file is dual-harness safe.
- `model` — pin the command to a specific model. Optional; same
  dual-harness tolerance.

The same files are read by Claude Code (symlinked at `.claude/commands/`) and
OpenCode (symlinked at `.opencode/commands/`). The symlinks are created by the
post-generation hook; if you copy this layout manually, recreate them with:

```sh
ln -s ../.agents/commands .claude/commands
ln -s ../.agents/commands .opencode/commands
```

Authoring tips: keep each command short and imperative — the description is
what surfaces in the slash-command picker, and the body is the prompt the
agent will follow. Reference `cmd('verify')` and the other shared macros via
`{% from '_macros.jinja' import cmd with context %}` so the wording tracks
the chosen `task_runner`.
