# 2. Canonicalize slash commands under `.agents/commands/`

## Status

Accepted (2026-05-21).

## Context

The harness keeps shared agent assets under a single vendor-neutral
directory (`.agents/`) and surfaces them to each tool via post-generation
symlinks. Two of the three shared-asset kinds already follow this rule
(see `hooks/post_gen.py:link_agent_assets`):

```
.agents/skills/       <- source of truth
.agents/subagents/    <- source of truth
.claude/skills        -> ../.agents/skills
.claude/agents        -> ../.agents/subagents
.opencode/skills      -> ../.agents/skills
.opencode/agents      -> ../.agents/subagents
```

Slash commands, however, were the odd one out. The source of truth was
`.claude/commands/{spec,plan,verify}.md.jinja`, and `.opencode/commands/`
held only a README explaining that, "if you use OpenCode primarily, move
them here and reference them from `.claude/commands/` via symlinks
instead." That asymmetry was already leaking into user-facing prose:

- `AGENTS.md` listed slash commands as a Claude-only surface ("Slash
  commands: `.claude/commands/` — `/spec`, `/plan`, `/verify`"), even
  though OpenCode also reads `.opencode/commands/`.
- The OpenCode README invited each team to invert the symlink direction
  by hand — a manual step the harness explicitly tries to avoid for
  skills and subagents.
- Any new shared command had to be authored at the Claude path while
  OpenCode users got the file only by setting up their own symlink.

There is no good reason for slash commands to differ from skills or
subagents: both Claude Code and OpenCode read the same Markdown-with-
YAML-frontmatter format, and both look for files at
`<tool-dir>/commands/`. The asymmetry was an accident of how the
template grew, not a design choice.

## Decision

Promote `.agents/commands/` to the canonical location for slash command
definitions, and create the corresponding `.claude/commands/` and
`.opencode/commands/` symlinks from the post-generation hook in the same
pass that creates the skills and subagents symlinks.

Concretely:

- The three example slash commands (`spec`, `plan`, `verify`) move from
  `template/.claude/commands/` to `template/.agents/commands/`.
- `template/.agents/commands/README.md` is added, mirroring the
  authoring guidance in `template/.agents/{skills,subagents}/README.md`.
- `hooks/post_gen.py:link_agent_assets()` gains two new entries:
  `.claude/commands -> ../.agents/commands` and
  `.opencode/commands -> ../.agents/commands`.
- `template/.opencode/commands/README.md` is removed; its content
  ("commands are maintained under `.claude/commands/`, flip the symlink
  yourself if you prefer OpenCode") is no longer true.
- `AGENTS.md.jinja`, `CLAUDE.md.jinja`, and the project README are
  updated to describe slash commands the same way they already describe
  skills and subagents ("symlinked from `.agents/commands/`").

## Consequences

**Positive.**

- One place to author shared commands. OpenCode and Claude Code see
  identical files automatically, with no manual symlink step.
- Symmetry across all three shared-asset kinds (skills, subagents,
  commands). The shape of `.agents/` is now learnable from one example:
  *put it under `.agents/<kind>/`; the tool dirs see it via symlink.*
- The user-facing prose collapses: AGENTS.md, CLAUDE.md, and the
  project README all describe the three shared-asset kinds with the
  same sentence template.
- Adding a fourth shared-asset kind in the future (rules?, snippets?)
  is now a clear, one-paragraph change in `hooks/post_gen.py` plus a
  README under `.agents/`.

**Negative.**

- Brownfield repos that already contain a real `.claude/commands/`
  directory will hit the existing `skip: already exists` branch of
  `_make_relative_symlink` (`hooks/post_gen.py`). Users must
  manually move their existing command files into `.agents/commands/`
  and delete the old directory to opt in to the shared layout. This is
  documented in this ADR and surfaced in the post-copy message.
- `copier update` on previously-generated repos will not retroactively
  create the new symlinks (because the old directories already exist).
  The same manual migration step is required.

## Alternatives considered

- **Keep the status quo and just delete `template/.opencode/commands/README.md`.**
  Rejected: leaves the asymmetry in place. OpenCode users still need
  to set up symlinks themselves, and the AGENTS.md slash-commands line
  remains Claude-centric.
- **Introduce a `commands_source` answer (`claude | opencode | shared`).**
  Rejected: per [ADR 0001](0001-decouple-task-runner-and-scripts.md),
  the harness should not duplicate agent-facing wording across tools.
  The only sensible default is "shared", which is what this change
  bakes in without an extra question.
- **Author commands under `.claude/commands/` and add a single
  `.opencode/commands -> ../.claude/commands` symlink.** Rejected:
  this works mechanically but encodes a Claude-Code bias into the
  vendor-neutral layout. Skills and subagents already live under
  `.agents/`; commands should follow the same shape rather than
  inventing a third pattern.

## References

- [`hooks/post_gen.py`](../../hooks/post_gen.py) — `link_agent_assets()`
  is where the new symlinks are wired up.
- [`ADR 0001`](0001-decouple-task-runner-and-scripts.md) — the prior
  decision to render all agent-facing wording from a single shared
  source so the tool surfaces can never disagree.
- `template/.agents/commands/README.md` — authoring guidance for the
  new canonical location.
