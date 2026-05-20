# 1. Decouple the task runner and the `scripts/` folder from agent-facing wording

## Status

Accepted (2026-05-20).

## Context

The source report this template implements
([`docs/harness-engineering-2026-05.md`](../harness-engineering-2026-05.md))
treats the `Makefile` as the canonical command interface for both
humans and AI coding agents. The original template encoded that
recommendation literally — it always generated a `Makefile`, and every
agent-facing surface (AGENTS.md, CLAUDE.md, README, the Claude Code
`Stop` hook, the OpenCode permission allowlist, the `/verify` slash
command, the example skill, the example spec) hard-coded
`make <target>` strings.

That worked, but forced an awkward shape on three common situations:

1. **Teams that have standardised on `just`** (https://just.systems/)
   for its cleaner syntax and lack of tab-sensitivity. Wrapping
   everything in `make` recipes that delegate to a separate runner
   doubles the indirection.
2. **Projects whose package/project manager already provides a task
   runner** — pixi (`pixi run <task>` from `pixi.toml`), hatch
   (`hatch run <env:task>`), `pnpm` scripts, `cargo` aliases. For these
   projects a generated `Makefile` is a second runner layered on top of
   one they already maintain.
3. **Future shell-entry-point slots beyond `verify.sh`.** The
   `PostToolUse` hook in `.claude/settings.json` already references
   `scripts/fmt-file.sh` (guarded by `test -x`, so it gracefully
   no-ops when absent). Other slots (`codegen.sh`, etc.) will follow.
   Gating *only* `verify.sh` behind a boolean (`generate_verify_script`)
   doesn't scale once the script folder holds multiple placeholders.

There is also a structural problem: the agent-facing wording was
duplicated across nine files. Any change to the canonical command form
(`make X` → `just X`, or omitted entirely) required nine coordinated
edits, and a missed file silently misled the agent.

## Decision

Recast the harness around two orthogonal axes — *what runs the
commands* and *what the commands are implemented in* — and let users
pick each independently. Render all agent-facing wording from a single
shared Jinja partial so the surfaces can never disagree.

**`task_runner` answer** (`make` | `just` | `none`, default `make`):
- `make`  → generate `Makefile` with `test` / `lint` / `fmt` / `verify`
  / `dev` / `clean` recipes. The report's original recommendation
  verbatim; `make` is universally installed and every surveyed agent
  CLI allow-lists `make *` without friction.
- `just`  → generate `justfile` with the same recipes in `just`
  syntax. Same ergonomics for agents, cleaner authoring for humans.
- `none`  → generate neither. The harness surfaces the raw
  `test_command` / `lint_command` / `fmt_command` / `verify_command`
  answers to agents. Use this when the project already has a native
  task runner (pixi, hatch, pnpm, cargo, …).

**`verify_command` answer** (default `./scripts/verify.sh`):
What the Claude Code `Stop` hook and the `/verify` slash command
invoke. For `task_runner=none`, this is the actual entry point.

**`generate_scripts` answer** (boolean, default `true`):
Whether to populate `scripts/` with placeholders for the harness's
shell-entry-point slots. Initial set: `scripts/verify.sh` (canonical
lint+test gate) and `scripts/fmt-file.sh` (the per-file formatter
slot the `PostToolUse` hook already discovers). Independent of
`task_runner` — a project can pick `task_runner=none` and still keep
the scripts, or pick `task_runner=make` and skip them if
`verify_command` points at a project-native pipeline.

**Shared `_macros.jinja`** at the repo root (outside the `_subdirectory`
so templates can import it as `{% from '_macros.jinja' import … %}`
without a `template/` prefix). Exposes `cmd(target)` returning
`make <t>` / `just <t>` / the raw underlying command depending on
`task_runner`, plus `has_cmd(target)` for guarding prose that
references task-runner-only targets like `test-all`. Imported by
every doc that used to reference `make` directly.

## Consequences

**Positive.**

- Agent-facing wording stays consistent across nine surfaces by
  construction. Adding a tenth surface only requires importing the
  macro.
- pixi/hatch/cargo-shaped projects don't get a second task runner
  imposed on them. They set `task_runner=none` and point
  `verify_command` at their own gate (e.g. `pixi run verify`).
- The `scripts/` toggle scales as more harness slots appear. Adding a
  `codegen.sh` placeholder is now a one-line change to one path token;
  there is no second binary question to add.
- The Claude Code `Stop` hook and `/verify` slash command remain
  pointed at the *user-facing* invocation
  (`make verify` / `just verify` / `pixi run verify`) rather than
  bypassing the runner layer, so verifying that the runner wiring
  works is part of the loop.

**Negative.**

- One new mandatory question (`task_runner`) for users to answer. We
  default it to `make` so existing prose and intuition still apply;
  users who want `just` or `none` opt in.
- Brownfield switches between runners do not delete the previously
  generated file. `_skip_if_exists` protects both `Makefile` and
  `justfile`, so switching from `make` to `just` leaves the old
  `Makefile` in place — the user must delete it manually if desired.
  Documented in `README.md`.
- The OpenCode and Claude Code permission allowlists no longer
  auto-allow the project's task manager when `task_runner=none`. The
  post-copy message advises adding e.g. `pixi *` manually; we don't
  try to auto-detect the project manager from `package_manager`.
- The shared macro adds one more file to keep correct (with `has_cmd`
  target sets that must stay in sync with the generated runner files).
  We mitigate this with a Jinja import path that is identical across
  every consumer and a comment in `_macros.jinja` flagging the
  invariant.

## Alternatives considered

- **Keep `make` as the only option, document `just`/pixi adoption as
  manual post-edit.** Rejected: too easy for the nine duplicated
  `make <target>` strings to drift from the reality of the generated
  repo, which is exactly the failure mode the harness is supposed to
  prevent.
- **Auto-detect the task runner from `package_manager`.** Rejected:
  the relationship is not 1-to-1 (a `uv`-managed project might still
  prefer `make` or `just`), and an auto-decision is harder to override
  than an explicit one.
- **Add a separate `test_all_command` answer for `task_runner=none`.**
  Rejected as premature: no concrete need has surfaced yet. The
  current `has_cmd('test-all')` guard simply omits the slow-suite
  guidance for `task_runner=none`, which is a clear cue rather than a
  misleading one.

## References

- [`docs/harness-engineering-2026-05.md`](../harness-engineering-2026-05.md)
  — the source report; §5/§6/§7 set the original `Makefile`-centric
  reference layout.
- `copier.yml` — `task_runner`, `verify_command`, `generate_scripts`
  question definitions and the post-copy warnings.
- `_macros.jinja` — `cmd()` / `has_cmd()` / `runner_file_name()`
  implementations.
