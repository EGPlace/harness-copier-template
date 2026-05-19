# AI agent harness — Copier template

A [Copier](https://copier.readthedocs.io/) template that scaffolds the
**agent-agnostic harness** described in Proposal A: an `AGENTS.md`-rooted
repository layout with a thin Claude Code + OpenCode overlay enabled by
default, and everything else (Cursor, GitHub Copilot, MCP, example
ADR/skill/subagent, Claude hooks) opt-in.

## What it generates

```
your-repo/
├─ AGENTS.md                         # canonical, ≤200 lines target
├─ CLAUDE.md                         # @AGENTS.md + Claude-Code-only stanzas
├─ README.md                         # greenfield only
├─ Makefile                          # test / lint / fmt / verify
├─ .gitignore                        # greenfield: full; brownfield: merged
├─ docs/
│  ├─ architecture.md
│  ├─ style.md
│  ├─ testing.md
│  └─ adr/0001-record-architecture-decisions.md   # if include_example_adr
├─ specs/                            # per-feature; YYYY-MM-example/ if opted in
├─ scripts/verify.sh                 # what Stop hook runs
├─ .agents/                          # vendor-neutral shared assets
│  ├─ skills/verify/SKILL.md         # if include_example_skill
│  └─ subagents/explorer.md          # if include_example_subagent
├─ .claude/                          # Claude Code (always)
│  ├─ settings.json                  # permissions (+ hooks if opted in)
│  ├─ commands/{spec,plan,verify}.md
│  ├─ skills/    -> ../.agents/skills        (symlink, post-gen)
│  ├─ agents/    -> ../.agents/subagents     (symlink, post-gen)
│  └─ rules/
├─ .opencode/                        # OpenCode (always)
│  ├─ opencode.jsonc
│  ├─ commands/
│  ├─ skills/    -> ../.agents/skills        (symlink, post-gen)
│  └─ agents/    -> ../.agents/subagents     (symlink, post-gen)
├─ .cursor/rules/project-context.mdc # if cursor
├─ .github/copilot-instructions.md   # if copilot
└─ .mcp.json + .mcp.example.jsonc    # if mcp
```

## Usage

### Greenfield (new repo)

```sh
copier copy gh:your-org/harness-copier-template ./my-new-repo
cd my-new-repo
git init && git add -A && git commit -m "Initial harness from copier template"
```

The template asks you:

| Question                  | Notes                                                    |
| ------------------------- | -------------------------------------------------------- |
| `mode`                    | `greenfield` here                                        |
| `project_name`            | Human-readable name                                      |
| `project_slug`            | Lowercase-dashed slug                                    |
| `project_description`     | One sentence                                             |
| `primary_language`        | Drives sensible defaults for commands                    |
| `package_manager`         | Restricted to your language's options                    |
| `test_command`            | Wired into `make test`                                   |
| `lint_command`            | Wired into `make lint`                                   |
| `fmt_command`             | Wired into `make fmt`                                    |
| `license`                 | SPDX id                                                  |
| `cursor`                  | Off by default                                           |
| `copilot`                 | Off by default                                           |
| `mcp`                     | Off by default                                           |
| `include_example_adr`     | On                                                       |
| `include_example_skill`   | On                                                       |
| `include_example_subagent`| On                                                       |
| `include_claude_hooks`    | On                                                       |
| `include_example_spec`    | Off by default                                           |

### Brown-field (existing repo)

```sh
cd existing-repo
copier copy gh:your-org/harness-copier-template .
```

Choose `mode: brownfield`. The template:

- **Never silently overwrites** `README.md`, `Makefile`, `.gitignore`,
  `.mcp.json`, or anything under `docs/`. They're listed in
  `_skip_if_exists` — copier leaves the existing file in place.
- **Appends** the harness's gitignore entries inside a fenced
  `# >>> ai-agent-harness >>>` … `# <<< ai-agent-harness <<<` block via the
  post-generation hook, so the operation is idempotent across re-runs.
- **Symlinks** `.claude/{skills,agents}` and `.opencode/{skills,agents}` to
  `.agents/{skills,subagents}` after generation.

For files that aren't on the skip list (`AGENTS.md`, `CLAUDE.md`, the slash
commands, the Claude/OpenCode configs), Copier prompts before overwriting,
showing a diff. Pick `s` (skip), `o` (overwrite), or `u` (merge with your
editor) per-file.

### Updates

```sh
cd your-repo
copier update
```

Copier replays the answers from `.copier-answers.yml` and prompts for any
new questions added since you generated. The same `_skip_if_exists` rules
apply, and the post-gen hook re-runs idempotently.

## Repository layout

```
harness-copier-template/
├─ copier.yml         # Questions + engine config
├─ hooks/
│  └─ post_gen.py     # Idempotent .gitignore merge + symlink creation
├─ template/          # _subdirectory = "template"; everything below is rendered
│  ├─ AGENTS.md.jinja
│  ├─ CLAUDE.md.jinja
│  ├─ README.md.jinja
│  ├─ Makefile.jinja
│  ├─ .gitignore.jinja
│  ├─ docs/
│  ├─ specs/
│  ├─ scripts/
│  ├─ .agents/
│  ├─ .claude/
│  ├─ .opencode/
│  ├─ {% if cursor %}.cursor{% endif %}/
│  ├─ {% if copilot %}.github{% endif %}/
│  └─ {% if mcp %}.mcp.json{% endif %}.jinja
└─ README.md          # this file
```

Conditional dirs and files use Copier's standard Jinja-in-path technique:
the path segment renders to an empty string when the gate is false, and
Copier drops the file/dir.

## Provenance

This template implements **Proposal A** from the *Harness Engineering for AI
Coding Agents in 2025–2026* report ([`docs/harness-engineering-report.md`](docs/harness-engineering-report.md)),
which synthesises practice as of mid-2026 from:

- Anthropic Claude Code docs and engineering blog
- OpenAI Codex `AGENTS.md` spec (agents.md, donated to the Linux Foundation
  Agentic AI Foundation on 9 Dec 2025)
- OpenCode docs (sst/opencode)
- HumanLayer (Kyle Mistele, *Writing a good CLAUDE.md*; *12-Factor Agents*)
- Augment Code (*A good AGENTS.md is a model upgrade*)
- Simon Willison, Armin Ronacher, Geoffrey Huntley, Harper Reed, Eric Ma
- GitHub Engineering (analysis of 2,500+ AGENTS.md files)

## License

Apache-2.0.
