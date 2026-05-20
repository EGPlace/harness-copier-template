# Changelog

All notable changes to this Copier template are recorded here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
for the questions and generated layout (a breaking change to a question
name, default, or output path bumps the major version).

## [0.2.0] – 2026-05-20

### Added

- New question **`task_runner`** (`make` | `just` | `none`, default
  `make`) that selects the task-runner file the template generates.
  See [ADR 0001](docs/decisions/0001-decouple-task-runner-and-scripts.md)
  for the rationale.
- New question **`verify_command`** (default `./scripts/verify.sh`).
  Drives the Claude Code `Stop` hook and the `/verify` slash command;
  for `task_runner=none` it is the actual verify entry point.
- New question **`generate_scripts`** (boolean, default `true`).
  Controls whether the `scripts/` folder is populated with placeholders
  for the harness's shell-entry-point slots. Initial placeholder set:
  `scripts/verify.sh` (canonical lint+test gate) and
  `scripts/fmt-file.sh` (per-file formatter slot the Claude Code
  `PostToolUse` hook already discovers via `test -x`).
- Shared `_macros.jinja` partial at the repo root exposing
  `cmd(target)`, `has_cmd(target)`, and `runner_file_name()` so every
  agent-facing surface renders the same command form for the chosen
  runner.
- ADR 0001 documenting the rationale for decoupling the task runner
  and the `scripts/` folder from agent-facing wording.

### Changed

- The Claude Code `Stop` hook now invokes the `task_runner`-aware
  `cmd('verify')` (e.g. `make verify` / `just verify` / the raw
  `verify_command`) instead of bypassing the runner with a fixed
  `./scripts/verify.sh`. The hook's `INPUT` payload is now piped to
  `jq` via `printf '%s' "$INPUT"` rather than unquoted `echo $INPUT`,
  so payloads containing whitespace, globs, or shell metacharacters
  are passed through literally.
- The OpenCode and Claude Code permission allowlists are now
  conditional on `task_runner` (`Bash(make:*)` / `Bash(just:*)` /
  omitted) instead of always listing `make`.
- Agent-facing surfaces (AGENTS.md, CLAUDE.md, README, the verify
  skill, the `/verify` slash command, `docs/testing.md`, the example
  spec's `tasks.md`) now render their command examples from the shared
  macro instead of hard-coded `make <target>` strings.
- The post-copy "Next steps" message now prints the user-facing
  invocation (`make verify` / `just verify` / the raw `verify_command`
  for `task_runner=none`) so the runner wiring is exercised during the
  smoke test rather than being bypassed.
- `hooks/post_gen.py` now parses `.copier-answers.yml` with PyYAML
  (already a Copier dependency), catches `yaml.YAMLError`, validates
  that the root is a `dict` and that values are simple scalars, and
  collapses whitespace before rendering the answer in the printed
  next-step line.
- Renamed `docs/harness-engineering-report.md` →
  `docs/harness-engineering-2026-05.md` to make the dated provenance
  explicit and leave room for follow-up reports.

### Removed

- The old `generate_verify_script` question is replaced by the broader
  `generate_scripts` (default unchanged at `true`). Existing projects
  running `copier update` will be prompted for the new key once; the
  generated behaviour is identical when the new key is `true`.

## [0.1.0] – 2026-05-19

### Added

- Initial release of the template. Implements Proposal A from
  [`docs/harness-engineering-2026-05.md`](docs/harness-engineering-2026-05.md):
  a short root `AGENTS.md`, a `CLAUDE.md` import overlay, a
  `docs/` hierarchy (`architecture.md`, `style.md`, `testing.md`,
  `adr/`), an optional `specs/<date>-<slug>/` convention, a
  `Makefile` with `test` / `lint` / `fmt` / `verify` targets, an
  optional `scripts/verify.sh` entry point, and thin tool-specific
  overlays for Claude Code (`.claude/`), OpenCode (`.opencode/`),
  Cursor (`.cursor/`), and GitHub Copilot (`.github/`).
- Brownfield-safe defaults: `README.md`, `Makefile`, `.gitignore`,
  `.mcp.json`, and the populated `docs/` files are protected by
  `_skip_if_exists`.
- Post-generation hook (`hooks/post_gen.py`) that idempotently
  merges a managed block of agent-related entries into an existing
  `.gitignore` and symlinks shared agent assets (`skills/`,
  `subagents/`) into `.claude/` and `.opencode/`.

[0.2.0]: https://github.com/grAItools/harness-copier-template/releases/tag/v0.2.0
[0.1.0]: https://github.com/grAItools/harness-copier-template/releases/tag/v0.1.0
