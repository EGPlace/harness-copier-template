# AI agent harness — Copier template

A [Copier](https://copier.readthedocs.io/) template that scaffolds an
**agent-agnostic harness** based on standard practices from multiple
respected sources as of mid-2026. The harness is an `AGENTS.md`-rooted
repository layout with a thin Claude Code + OpenCode overlay enabled by
default, and everything else (Cursor, GitHub Copilot, MCP, example
ADR/skill/subagent, Claude hooks) opt-in.

## What it generates

```
your-repo/
├─ AGENTS.md                         # canonical, ≤200 lines target
├─ CLAUDE.md                         # @AGENTS.md + Claude-Code-only stanzas
├─ README.md                         # greenfield only
├─ Makefile  OR  justfile  (or neither)  # task_runner: make | just | none
├─ .gitignore                        # greenfield: full; brownfield: merged
├─ docs/
│  ├─ architecture.md
│  ├─ style.md
│  ├─ testing.md
│  └─ adr/0001-record-architecture-decisions.md   # if include_example_adr
├─ specs/                            # per-feature; YYYY-MM-example/ if opted in
├─ scripts/verify.sh                 # what Stop hook runs (if generate_verify_script)
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
| `test_command`            | Wired into the task runner's `test` target               |
| `lint_command`            | Wired into the task runner's `lint` target               |
| `fmt_command`             | Wired into the task runner's `fmt` target                |
| `task_runner`             | `make` \| `just` \| `none` — no default, pick explicitly |
| `verify_command`          | What hooks and `/verify` run; default `./scripts/verify.sh` |
| `generate_verify_script`  | Generate `scripts/verify.sh`; default `true`             |
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

- **Never silently overwrites** `README.md`, `Makefile`, `justfile`,
  `.gitignore`, `.mcp.json`, or anything under `docs/`. They're listed in
  `_skip_if_exists` — copier leaves the existing file in place. (This also
  means switching `task_runner` later does not delete the previous file;
  remove it manually if you no longer want it.)
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
├─ docs/
│  └─ harness-engineering-report.md  # Source report this template implements
├─ hooks/
│  └─ post_gen.py     # Idempotent .gitignore merge + symlink creation
├─ template/          # _subdirectory = "template"; everything below is rendered
│  ├─ AGENTS.md.jinja
│  ├─ CLAUDE.md.jinja
│  ├─ README.md.jinja
│  ├─ _macros.jinja                                   # shared Jinja macros (excluded from output)
│  ├─ {% if task_runner == 'make' %}Makefile{% endif %}.jinja
│  ├─ {% if task_runner == 'just' %}justfile{% endif %}.jinja
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

## Choosing a task runner

`task_runner` is asked with no default — pick the one that matches how your
team already runs tasks:

- **`make`** — generate a `Makefile`. Universal toolchain, no extra install.
  Recommended when the project doesn't already have its own task runner.
- **`just`** — generate a `justfile` ([just.systems](https://just.systems/)).
  Cleaner syntax, no tab-sensitivity. Requires `just` on PATH.
- **`none`** — generate neither. Use this for projects whose package /
  project manager already provides task management (e.g. **pixi** tasks
  defined in `pixi.toml`, **hatch** scripts in `pyproject.toml`, `pnpm`
  scripts, `cargo` aliases). The harness will then surface the raw
  `test_command` / `lint_command` / `fmt_command` / `verify_command` to
  agents directly. Consider setting `verify_command` to e.g.
  `pixi run verify` to keep the Stop hook and `/verify` slash command
  pointed at your existing pipeline.

The `verify_command` answer (default `./scripts/verify.sh`) is what the
Claude Code Stop hook and the `/verify` slash command invoke; `scripts/verify.sh`
itself is generated only when `generate_verify_script=true`.

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

[MIT](LICENSE).

Note: this license covers the template repository itself. The `license`
question in `copier.yml` (default `Apache-2.0`) only sets an SPDX
identifier inside the rendered docs — it does **not** generate a LICENSE
file in downstream repos. Projects scaffolded from this template should
add their own LICENSE file separately.
