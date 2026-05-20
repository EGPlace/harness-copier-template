# Harness Engineering for AI Coding Agents in 2025–2026

## TL;DR

- **The center of gravity has converged on AGENTS.md** — an OpenAI-led, now Linux-Foundation-stewarded Markdown convention launched **August 2025** and adopted by 60,000+ repos and most major agent CLIs (Codex, Cursor, Amp, Factory, Gemini CLI, Jules, GitHub Copilot, VS Code, OpenCode). Anthropic's Claude Code still reads CLAUDE.md natively but can be made AGENTS.md-aware via a one-line `@AGENTS.md` import; OpenCode reads AGENTS.md natively and falls back to CLAUDE.md.
- **The repo-side "harness" is now a small, well-defined kit**: a short root AGENTS.md (≤200 lines, written against the ~150–200-instruction budget Kyle Mistele of HumanLayer documented in his 25 Nov 2025 post *Writing a good CLAUDE.md*), a `docs/` hierarchy of progressively-disclosed reference material, optional ADRs, an explicit per-feature plan/spec/tasks/scratchpad layout, agent-readable shell snippets (a `Makefile` / `scripts/`), and a thin tool-specific overlay (`.claude/`, `.opencode/`, `.cursor/rules/`, `.github/`) that the AGENTS.md core delegates to. Hooks, Skills, MCP servers, and subagents are *additive* — opt in only when the cost is justified.
- **My recommendation**: adopt **Proposal A** below — an agent-agnostic AGENTS.md-rooted layout with a thin Claude Code + OpenCode overlay — in any repo touched by more than one agent or engineer. Use **Proposal B**'s "minimum viable harness" (three files) for personal/throwaway projects and grow it modularly as concrete pains appear.

---

## 1. Background and Terminology

### 1.1 What "harness engineering" means in 2026

The agent CLI — Claude Code, Codex CLI, OpenCode, Cursor's agent mode, Aider, Gemini CLI, Windsurf, Continue, Cline, Roo Code, Kilo Code, Amp, Factory — is the **harness**. The repository-side files, folders, hooks, and MCP servers that shape what that harness sees and is allowed to do are what practitioners now call **harness engineering**, **agent scaffolding**, or (Karpathy / Breunig / Horthy) **context engineering**. Kyle Mistele of HumanLayer puts it tersely: *"Harness engineering is the art and science of leveraging your coding agent's configuration points to improve output quality"* (HumanLayer blog, 12 Mar 2026).

The shift from "prompt engineering" to "context engineering" was crystallized by Andrej Karpathy in mid-2025 ("the delicate art and science of filling the context window with just the right information for the next step") and elaborated by Drew Breunig's *How Long Contexts Fail* / *How to Fix Your Context* (June 2025), giving the field its canonical failure-mode taxonomy: **context poisoning, context distraction, context confusion, context clash** ("context rot"). The repo-side discipline that emerged from those ideas is what this report is about.

### 1.2 The 2026 landscape of agent CLIs

| Tool | Maker | Reads AGENTS.md natively? | Native instruction file | Notes |
|---|---|---|---|---|
| Claude Code | Anthropic | No (CLAUDE.md). Can `@AGENTS.md`-import. | `CLAUDE.md` + `.claude/` | Skills, hooks, subagents, MCP |
| Codex CLI | OpenAI | Yes (canonical) | `AGENTS.md` (+ `AGENTS.override.md`) | Hierarchical, `CODEX_HOME=.codex` |
| OpenCode | sst (anomalyco) | Yes (primary) | `AGENTS.md` (+ falls back to `CLAUDE.md`) | `.opencode/`, primary/subagent split |
| Cursor | Cursor | Yes (with Project Rules) | `.cursor/rules/*.mdc` (+ AGENTS.md) | MDC frontmatter |
| Windsurf | Codeium | Yes | `.windsurfrules` + AGENTS.md | |
| Aider | Paul Gauthier | Reads `CONVENTIONS.md` / AGENTS.md via config | `.aider.conf.yml` | |
| Gemini CLI | Google | Yes | `GEMINI.md` + AGENTS.md | |
| GitHub Copilot | GitHub | Yes (custom agents) | `.github/copilot-instructions.md` + `.github/agents/*.md` | |
| Amp | Sourcegraph | Yes | AGENTS.md | "Oracle" subagent design |
| Factory | Factory.ai | Yes (signatory) | AGENTS.md | |
| Continue, Cline, Roo, Kilo | various | Yes | AGENTS.md | Kilo deprecated its "memory bank" in favor of AGENTS.md |
| Zed (ACP) | Zed Industries | Via the agent it runs | n/a | Hosts other agents over Agent Client Protocol |

### 1.3 AGENTS.md — provenance, governance, scope

- **Origin**: OpenAI Codex internal convention, released publicly **August 2025** as an open spec at `agents.md`. Working group co-founded with **Google, Sourcegraph (Amp), Factory, and Cursor**; Factory's blog post (Aug 19, 2025) names that group.
- **Spec essentials** (`agents.md`): "a simple, open format for guiding coding agents… a README for agents." Plain Markdown, no required schema. *"The closest AGENTS.md to the edited file wins; explicit user chat prompts override everything."* Monorepos place AGENTS.md in subdirectories; "at time of writing the main OpenAI repo has 88 AGENTS.md files."
- **Governance (Dec 9, 2025)**: AGENTS.md was donated, along with **Anthropic's MCP** and **Block's goose**, to the new **Linux Foundation Agentic AI Foundation (AAIF)**. Platinum members: AWS, Anthropic, Block, Bloomberg, Cloudflare, Google, Microsoft, OpenAI. OpenAI's own post claims **60,000+ projects** using AGENTS.md by year-end 2025.
- **Codex behavior**: documented precedence is `AGENTS.override.md → AGENTS.md → TEAM_GUIDE.md → .agents.md` per directory, walking from global (`$CODEX_HOME` default `~/.codex`) down through the project tree to the working directory; more-specific files override.

### 1.4 CLAUDE.md — Anthropic's parallel convention

Anthropic publishes a documented memory hierarchy (`code.claude.com/docs/en/memory`):

1. **Enterprise/managed policy** (`/Library/Application Support/ClaudeCode/CLAUDE.md` on macOS; `/etc/claude-code/CLAUDE.md` on Linux)
2. **User memory** `~/.claude/CLAUDE.md`
3. **Project memory** `./CLAUDE.md` *or* `./.claude/CLAUDE.md`
4. **Path-scoped project rules** `./.claude/rules/*.md` (with optional `paths:` frontmatter)
5. **Local override** `./CLAUDE.local.md` (gitignored)
6. **Auto memory** (Claude Code v2.1.59+ writes to `~/.claude/projects/<hash>/memory/` automatically)

Imports use `@path/to/file.md`, resolved recursively up to 5 levels. The cleanest cross-tool bridge is therefore a one-line CLAUDE.md that says `@AGENTS.md`. OpenCode's docs explicitly support the inverse: AGENTS.md is canonical and `~/.claude/CLAUDE.md` is read as a fallback.

### 1.5 llms.txt vs AGENTS.md — distinct purposes

`/llms.txt` was proposed by **Jeremy Howard (Answer.AI), 3 Sep 2024**, for **public-facing websites** to advertise LLM-friendly Markdown navigation: an H1 project name, a blockquote summary, then H2 link sections. A companion `/llms-full.txt` contains the whole documentation flattened. Adoption is real on docs sites (Cursor, Anthropic, Vercel, Mintlify, Bolt.new, Instructor) but Google's John Mueller has publicly noted no major LLM provider's crawler is known to fetch the file. **llms.txt is for outside-in (web); AGENTS.md is for inside-out (repo).** A library that ships both is doing the right thing — `llms.txt` on the docs domain, `AGENTS.md` in the repo root.

---

## 2. Survey of Practices

### 2.1 Instruction file conventions

**Consensus rules from Anthropic, OpenAI, Augment Code, HumanLayer, Simon Willison, Armin Ronacher, GitHub:**

- **Keep it short.** Kyle Mistele (HumanLayer, *Writing a good CLAUDE.md*, 25 Nov 2025): frontier thinking LLMs reliably follow ~150–200 instructions; Claude Code's own system prompt already consumes ~50 of those slots, so a bloated CLAUDE.md actively degrades following of *all* instructions, not just the late ones. Augment Code's *"A good AGENTS.md is a model upgrade. A bad one is worse than no docs at all"* (Slava Zhenylenko, Augment Code blog, 22 Apr 2026) documents the phenomenon empirically.
- **Six sections cover most of the value** (GitHub's analysis of 2,500+ agents.md files, *"How to write a great agents.md"*, github.blog, 2026): **commands** (put `npm test`, `pnpm build`, `pytest -v` early with flags), **testing**, **project structure**, **code style** (show one example, don't describe in paragraphs), **git workflow**, and **boundaries (what NOT to do)**. Pair every "don't" with a "do" — Zhenylenko reports verbatim: *"The agent checked each warning for relevance and explored code it didn't need to touch. The PR took twice as long and was 20% less complete on average."*
- **Describe capabilities, not file paths** (Mistele). File paths rot; capabilities don't.
- **Never auto-generate it.** Both Anthropic's `/init` and OpenCode's `/init` produce a starting point that should be hand-pruned. Auto-generated files "prioritize comprehensiveness over restraint" (HumanLayer).
- **Use progressive disclosure.** Reference deeper docs (`See @docs/testing.md`) rather than inlining them. Both AGENTS.md (`@path` import) and CLAUDE.md (`@path/to/file.md`, 5-level recursion) support this.
- **Use nested AGENTS.md / CLAUDE.md in monorepos.** The closest file to the edited file wins.

### 2.2 Folder layout

The 2026 pattern is **a small public root and a thin tool-specific overlay**:

```
repo/
├─ README.md                  # humans
├─ AGENTS.md                  # agents (root, canonical)
├─ CLAUDE.md                  # one line: @AGENTS.md (+ optional CC-only stanzas)
├─ CLAUDE.local.md            # gitignored personal overrides
├─ docs/
│  ├─ architecture.md
│  ├─ style.md
│  ├─ testing.md
│  ├─ adr/                    # Michael Nygard format
│  │  └─ 0001-record-architecture-decisions.md
│  └─ runbooks/
├─ specs/                     # per-feature, see Spec Kit / Sean Grove
│  └─ 2026-05-billing/
│     ├─ spec.md
│     ├─ plan.md
│     ├─ tasks.md
│     └─ scratch.md
├─ scripts/                   # small shell helpers the agent uses
├─ .agents/                   # cross-tool shared agent assets
│  ├─ skills/                 # SKILL.md format, also usable by Claude Code
│  └─ subagents/              # markdown agent definitions
├─ .claude/                   # Claude-Code-specific
│  ├─ settings.json           # hooks, permissions
│  ├─ commands/               # slash commands
│  ├─ agents/                 # subagents (or symlink to ../.agents/subagents)
│  ├─ skills/                 # symlink to ../.agents/skills
│  └─ rules/                  # path-scoped CLAUDE.md fragments
├─ .opencode/                 # OpenCode-specific
│  ├─ opencode.jsonc
│  ├─ agents/
│  └─ commands/
├─ .cursor/                   # Cursor-specific
│  └─ rules/
│     └─ *.mdc
└─ .github/
   ├─ copilot-instructions.md # one line: see ../AGENTS.md
   └─ agents/                 # Copilot custom agents (optional)
```

`.agents/` is an emerging vendor-neutral parking spot for skills and subagent definitions that you symlink into tool-specific folders.

### 2.3 Skills, commands, subagents — when to use which

Anthropic's *Equipping agents for the real world with Agent Skills* (anthropic.com/engineering, **16 Oct 2025**) frames skills as **progressive-disclosure folders, not files**:

```
skill-name/
├─ SKILL.md             # required; YAML frontmatter (name, description) + body
├─ scripts/             # optional executable code (deterministic tasks)
├─ references/          # optional docs loaded on demand
└─ assets/              # optional templates, fonts, icons
```

The Anthropic engineer guide *"Skills for Claude Code"* (Tort Mario, April 2026, Medium) emphasizes: (a) skills are **folders not files**, (b) frontmatter `description` should be slightly **"pushy"** because Claude *under*-triggers skills, (c) the most valuable section is **Gotchas**, and (d) you can put a script in `scripts/` and let Claude run it deterministically instead of generating tokens. The same SKILL.md format works in Claude Code, OpenCode, and other agents — Anthropic shipped it as an open standard alongside the `anthropics/skills` repo (the official `frontend-design` skill has 277,000+ installs as of March 2026).

**Decision rule** (cross-tool synthesis):

| Use… | When… | Storage |
|---|---|---|
| **Root AGENTS.md** | Every-task information (stack, commands, layout, hard "don'ts") | `/AGENTS.md` |
| **Nested AGENTS.md** | Per-package conventions in a monorepo | `packages/x/AGENTS.md` |
| **Skill (SKILL.md)** | Reusable expertise, loaded on demand by description match | `.agents/skills/<name>/SKILL.md` |
| **Slash command** | A user-triggered repeatable workflow (e.g. `/release`, `/triage`) | `.claude/commands/<name>.md` |
| **Subagent** | Read-heavy or context-isolating task — runs in its own context window | `.claude/agents/<name>.md`, `.opencode/agents/<name>.md` |
| **Hook** | A *deterministic* enforcement gate (auto-format, block `rm -rf`) | `.claude/settings.json` |
| **MCP server** | When the alternative would be a brittle CLI scrape (Playwright is canonical) | `.mcp.json` |

### 2.4 Claude Code subagents — exact format

Subagents launched in Claude Code around **24–25 July 2025**. They live in `.claude/agents/*.md` (project) or `~/.claude/agents/*.md` (user). Precedence (highest first): managed settings → `--agents` CLI flag → `.claude/agents/` → `~/.claude/agents/` → plugin agents. Subagents are scanned recursively; identity comes from the `name` frontmatter field, not the filename. Subagents **cannot spawn other subagents**.

Verbatim official-docs example:

```yaml
---
name: code-reviewer
description: Expert code review specialist. Proactively reviews code for quality,
  security, and maintainability. Use immediately after writing or modifying code.
tools: Read, Grep, Glob, Bash
model: inherit
---

You are a code reviewer. When invoked, analyze the code and provide
specific, actionable feedback on quality, security, and best practices.
```

Optional frontmatter: `disallowedTools`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation: worktree`, `color`, `initialPrompt`.

OpenCode's `.opencode/agents/<name>.md` equivalent (opencode.ai/docs/agents):

```yaml
---
description: Reviews code for correctness and style
mode: subagent              # primary | subagent | all (default: all)
model: anthropic/claude-opus-4-6
temperature: 0.1
permission:
  read: allow
  write: allow
  edit: allow
  bash:
    "npm install *": ask
---

You are a code reviewer. Your job is to...
```

`permission:` replaces the deprecated `tools:` field. `hidden: true` removes the agent from `@`-mention autocomplete. OpenCode ships built-in `build` (full-access primary), `plan` (read-only primary that denies edits except inside `.opencode/plans/*.md`), and `general` (subagent for searches).

### 2.5 Hooks and automation

Hooks turn advisory CLAUDE.md instructions into deterministic gates. The Dotzlaw team's *"Claude Code Hooks: The Deterministic Control Layer for AI Agents"* (dotzlaw.com, 2026) quantifies this: *"Prompt-based instructions achieve 70–90% compliance. The agent usually follows them but can skip under context pressure, long sessions, or competing priorities. Hooks achieve 100% compliance. They execute at the system level, outside the LLM's reasoning chain."* Configured in `.claude/settings.json` (committed) or `.claude/settings.local.json` (gitignored) or `~/.claude/settings.json` (user).

High-leverage events: **`SessionStart`** (inject branch/dirty-state context), **`UserPromptSubmit`**, **`PreToolUse`** (the only event that can *block* — exit code 2 or JSON `permissionDecision: "deny"`), **`PostToolUse`** (auto-format, lint, log), **`Stop`** (force tests to pass), and **`SubagentStop`**. Hooks can be `command`, `prompt` (Haiku decides yes/no), `agent`, or `http` types.

Canonical examples (paste into `.claude/settings.json`):

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [{ "type": "command",
        "command": "ruff format \"$CLAUDE_TOOL_INPUT_FILE_PATH\" && ruff check --fix \"$CLAUDE_TOOL_INPUT_FILE_PATH\"" }]
    }],
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{ "type": "command",
        "command": "echo \"$CLAUDE_TOOL_INPUT\" | grep -qE 'rm -rf|DROP TABLE|git push.*--force' && exit 2 || exit 0" }]
    }],
    "Stop": [{
      "hooks": [{ "type": "command",
        "command": "INPUT=$(cat); [ \"$(echo $INPUT | jq -r '.stop_hook_active')\" = 'true' ] && exit 0; make test || exit 2" }]
    }]
  }
}
```

A `PreToolUse` hook returning `permissionDecision: "deny"` blocks even in `--dangerously-skip-permissions` mode. Always guard `Stop` hooks with `stop_hook_active` to avoid infinite loops. Eric Ma's *Safe ways to let your coding agent work autonomously* (8 Nov 2025) is the canonical recipe — auto-approve read-only commands, require approval for state-changing ones.

### 2.6 MCP server configuration

Practitioner consensus (Ronacher, Willison, HumanLayer, Mario Zechner's *"pi" coding agent* post, 30 Nov 2025) is **prefer a Makefile target or a CLI to an MCP server**. Ronacher: *"MCP for me is really only needed if I need to give Claude access to something that it finds too hard to use otherwise. A good example is playwright-mcp."* Willison's *Designing agentic loops* (30 Sep 2025) makes the same argument and demonstrates a custom AGENTS.md screenshot-recipe using `shot-scraper`. Zechner: *"many MCP servers are overengineered and include large toolsets that consume lots of context."* When you do need MCP, configure servers in `.mcp.json` at the repo root (Claude Code, Codex, OpenCode all read this) and scope tightly.

### 2.7 Plan / spec / scratchpad files

The dominant pattern (Harper Reed, *My LLM codegen workflow*, 16 Feb 2025; Anthropic best practices; GitHub Spec Kit; HumanLayer 12-Factor Agents; Geoffrey Huntley's `/specs` and `/stdlib`) is:

1. **Brainstorm / interview** → `spec.md` (Anthropic recommends: *"Start with a minimal prompt and ask Claude to interview you using the AskUserQuestion tool"*).
2. **Plan** (often a separate session, reasoning model) → `plan.md` with numbered, testable steps.
3. **Tasks** → `tasks.md` checklist.
4. **Implement** → `scratch.md` working memory the agent writes to.

GitHub **Spec Kit** (announced **2 Sep 2025**; **101k stars as of 17 May 2026** per the github/spec-kit Issues page; supports 30+ agents) formalizes this as `/speckit.constitution → /speckit.specify → /speckit.clarify → /speckit.plan → /speckit.tasks → /speckit.implement`, with artifacts under `.specify/` (constitution, scripts, templates). **BMAD-METHOD** and AWS's **Kiro** IDE implement variants of the same loop. Sean Grove's *"The New Code"* talk at AI Engineer World's Fair (2025) is the position piece: specs, not code, are the durable artifact; that is also the thesis of Spec Kit lead Manfred Riem (*"specifications don't serve code — code serves specifications"*).

A pragmatic, lighter-weight version that works without Spec Kit (recommended for most teams):

```
specs/
└─ 2026-05-billing-rework/
   ├─ spec.md      # WHAT and WHY; no implementation detail
   ├─ plan.md      # numbered phased plan; each phase has tests
   ├─ tasks.md     # checkbox list the agent ticks off
   └─ scratch.md   # agent's working notes; cleared on completion
```

Commit all four. The branch dies; the spec lives.

### 2.8 ADRs (Architecture Decision Records)

Michael Nygard's 2011 ADR format has had a quiet renaissance because *one short markdown file per decision* is exactly the shape an agent reads well. The convention is `docs/adr/NNNN-kebab-title.md` with sections **Context / Decision / Status / Consequences**. The widely-used `adr-tools` (Nat Pryce) is a single shell-script binary that scaffolds them. ADRs are *append-only* — supersession is recorded by a new ADR that references the old one, not by editing history. For agents this is gold: the historical record is searchable in plain text and the *current* state can be derived deterministically.

### 2.9 Per-user vs per-repo vs per-machine layering

| Layer | Claude Code | OpenCode | Codex | Cursor |
|---|---|---|---|---|
| Org policy (immutable) | `/Library/Application Support/ClaudeCode/CLAUDE.md` (mac) | Managed `opencode.json` via MDM | `$CODEX_HOME/AGENTS.override.md` | Team Rules (enforced) |
| User defaults | `~/.claude/CLAUDE.md`, `~/.claude/settings.json` | `~/.config/opencode/AGENTS.md` | `~/.codex/AGENTS.md` | User Rules |
| Project (committed) | `./CLAUDE.md`, `./.claude/settings.json` | `./AGENTS.md`, `./.opencode/opencode.json` | `./AGENTS.md` | `.cursor/rules/*.mdc` |
| Project local (gitignored) | `./CLAUDE.local.md`, `.claude/settings.local.json` | `.opencode/local/` (convention) | `./.codex/` | local settings |
| Session | `--agents`, `--add-dir` | CLI flags | `--cd`, `CODEX_HOME` | n/a |

**Rule**: more-specific wins on conflict in every tool, but rules **merge** rather than replace. Personal preferences (color, editor, "use TypeScript over JS") belong in user memory; project standards belong in project memory; secrets and per-developer paths belong in the gitignored local layer.

### 2.10 .gitignore patterns

Standard 2026 set:

```
# Agent local overrides
CLAUDE.local.md
.claude/settings.local.json
.claude/.last_*
.claude/checkpoints/
.claude/shell-snapshots/
.opencode/local/
.codex/auth.json
.cursor/settings.local.json

# Agent scratch (team decision)
specs/*/scratch.md
.agents/.cache/
```

Commit: `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`, `.claude/commands/`, `.claude/agents/`, `.claude/skills/`, `.claude/rules/`, `.opencode/opencode.json`, `.opencode/agents/`, `.opencode/commands/`, `.cursor/rules/*.mdc`, `.mcp.json`. Do NOT commit auto-generated session transcripts.

### 2.11 Brown-field adoption strategy

Synthesized from Augment Code, Anthropic, Huntley's `/stdlib`, and Harper Reed:

1. **Day 1 — Have the agent generate AGENTS.md from the repo, then *aggressively delete*.** Target ≤200 lines. Strip everything "useful for most scenarios" but not for the next task. Auto-generated files always over-include.
2. **Day 1 — Wire a one-line `CLAUDE.md` (`@AGENTS.md`) and a Cursor `project-context.mdc` (`alwaysApply: true`) that points to AGENTS.md.** Pick the canonical agent and stop fighting.
3. **Week 1 — Add 3 hooks**: auto-format on edit, block destructive bash, run tests on stop.
4. **Week 1 — Add ADRs retroactively for the 5–10 biggest past decisions** (database, framework, auth model, deployment, language version policy).
5. **Week 2 — Per-package nested AGENTS.md** where conventions actually differ from root.
6. **Week 2 — Two skills**: one shape-of-output, one deterministic verification.
7. **Month 2 — Spec-driven flow** (`specs/<date>-<topic>/`) for net-new features.

Huntley's `/stdlib` (Feb 2025) and Andre Ratzenberger's `cursor-rules` repo show the extreme: a personal stdlib of hundreds of composable rules. For a team I recommend the opposite — fewer, better, owned and pruned.

### 2.12 Parallel agents

Simon Willison's *Embracing the parallel coding agent lifestyle* (5 Oct 2025) and Geoffrey Huntley's "Ralph Wiggum" technique (popularized late 2025) document the now-common `git worktree`-per-agent pattern. Cursor's mid-2026 internal experiment ran "hundreds of agents collaborating to build a browser from scratch" (~1M LOC in a week). The relevant repo-side practice: each worktree gets its own `specs/<task>/` and `scratch.md`; the `.agents/`/`.claude/` config is shared via the main repo. Tooling like `agrimsingh/ralph-wiggum-cursor` and HumanLayer's CodeLayer formalize this.

---

## 3. Direct quotes and key sources (provenance)

| Source | Date | Where | What it gives us |
|---|---|---|---|
| **agents.md** spec | Aug 2025 | agents.md | Canonical spec; nested precedence; "README for agents" |
| **OpenAI**, *AGENTS.md* announcement | 19 Aug 2025 | factory.ai/news/agents-md; openai.com/index/agentic-ai-foundation | Working group (OpenAI, Google, Sourcegraph/Amp, Factory, Cursor); 60K+ adoption claim |
| **Linux Foundation**, AAIF launch | 9 Dec 2025 | linuxfoundation.org press release | AGENTS.md + MCP + goose donated |
| **Anthropic**, *Best practices for Claude Code* | 2025–26 | anthropic.com/engineering/claude-code-best-practices | Interview-driven specs; Writer/Reviewer; parallel `claude -p` |
| **Anthropic**, *Equipping agents for the real world with Agent Skills* | 16 Oct 2025 | anthropic.com/engineering | Skills as folders, progressive disclosure, SKILL.md format |
| **Anthropic** Claude Code docs | live | code.claude.com/docs | Memory hierarchy; hooks lifecycle; subagent format |
| **Codex** docs, *Custom instructions with AGENTS.md* | live | developers.openai.com/codex/guides/agents-md | Codex precedence chain incl. AGENTS.override.md / TEAM_GUIDE.md fallback |
| **OpenCode** docs | live | opencode.ai/docs | AGENTS.md primacy; CLAUDE.md fallback; agent modes |
| **Cursor** docs, *Rules* | live | cursor.com/docs/context/rules | `.cursor/rules/*.mdc`, MDC frontmatter, Team/Project/User rule layering |
| **Kilo Code** docs | live | kilo.ai/docs/customize/agents-md | Deprecation of "memory bank" in favor of AGENTS.md |
| **Jeremy Howard / Answer.AI**, llms.txt | 3 Sep 2024 | llmstxt.org; answer.ai/posts/2024-09-03-llmstxt.html | The proposal itself; llms-full.txt addendum |
| **Simon Willison**, *Designing agentic loops* | 30 Sep 2025 | simonwillison.net/2025/Sep/30/ | "Prefer AGENTS.md and a CLI to MCP" |
| **Simon Willison**, *Embracing the parallel coding agent lifestyle* | 5 Oct 2025 | simonwillison.net | Multi-worktree workflow |
| **Simon Willison**, *Vibe engineering* | 7 Oct 2025 | simonwillison.net | Naming for the discipline |
| **Armin Ronacher**, *Agentic Coding Recommendations* | 12 Jun 2025 | lucumr.pocoo.org/2025/6/12/agentic-coding | "Logging is super important"; "dumbest possible thing that will work"; Go > Python for agentic loops |
| **Armin Ronacher**, *Agent Design Is Still Hard* | 21 Nov 2025 | lucumr.pocoo.org/2025/11/21/agents-are-hard | Self-reinforcement (todo write tool as echo); shared FS for subagents |
| **Geoffrey Huntley**, */stdlib* | 8 Feb 2025 | ghuntley.com/stdlib | Build a stdlib of composable rules instead of one-off prompts |
| **Geoffrey Huntley**, */specs* | 3 Mar 2025 | ghuntley.com/specs | Spec+stdlib combo |
| **Thorsten Ball**, *How to Build an Agent* | 15 Apr 2025 | ampcode.com/how-to-build-an-agent | ~300 lines of Go = a working coding agent |
| **Dexter "Dex" Horthy / HumanLayer**, *12-Factor Agents* | Apr 2025 | github.com/humanlayer/12-factor-agents (**19.8k stars / 1.5k forks** as of mid-May 2026) | The 12 factors; coined "context engineering" |
| **Kyle Mistele (HumanLayer)**, *Writing a good CLAUDE.md* | 25 Nov 2025 | humanlayer.dev/blog | "Instruction budget" ~150–200; CC system prompt ~50 of those |
| **Kyle Mistele (HumanLayer)**, *Harness engineering* | 12 Mar 2026 | humanlayer.dev/blog | The definition used in this report |
| **Drew Breunig**, *How Long Contexts Fail* / *How to Fix Your Context* | 22 / 26 Jun 2025 | dbreunig.com | Context-rot taxonomy; loadout, quarantine, pruning, summarization, offloading |
| **Andrej Karpathy** | mid-2025 | tweets | "Context engineering" framing |
| **Harper Reed**, *My LLM codegen workflow atm* | 16 Feb 2025 | harper.blog | spec.md → prompt_plan.md → todo.md → iterate |
| **Slava Zhenylenko (Augment Code)**, *A good AGENTS.md is a model upgrade. A bad one is worse than no docs at all.* | 22 Apr 2026 | augmentcode.com/blog | Empirical effects; too-much-architecture-overview hurts |
| **GitHub Engineering**, *How to write a great agents.md* | 2026 | github.blog | Analysis of 2,500+ files; six-section pattern |
| **GitHub Spec Kit** | 2 Sep 2025; ongoing | github.com/github/spec-kit (**101k stars on 17 May 2026**) | constitution/specify/plan/tasks/implement workflow |
| **Sean Grove**, *The New Code* | 2025 | AI Engineer World's Fair | "Specifications, not code, are the durable artifact" |
| **Mario Zechner**, *What I learned building an opinionated and minimal coding agent (pi)* | 30 Nov 2025 | mariozechner.at | AGENTS.md hierarchically loaded; "What if you don't need MCP at all?" |
| **Eric Ma**, *Safe ways to let your coding agent work autonomously* | 8 Nov 2025 | ericmjl.github.io | Auto-approve read-only; require approval for state-changing |
| **Dotzlaw team**, *Claude Code Hooks: The Deterministic Control Layer for AI Agents* | 2026 | dotzlaw.com | The 70–90% vs 100% compliance datapoint |
| **Anthropic**, *How Anthropic teams use Claude Code* | 2025 | anthropic.com (PDF) | "More time we invest in CLAUDE.md, the better Claude performs"; MCP-over-CLI for sensitive data |
| **Mitchell Hashimoto**, talks/posts on Claude Code in Ghostty | 2025–26 | hachyderm.io/@mitchellh, X | Practical CC integration; concerns about CC auto-editing terminal configs |

The HumanLayer 12 factors, verbatim from the README:

> 1. Natural Language to Tool Calls
> 2. Own your prompts
> 3. Own your context window
> 4. Tools are just structured outputs
> 5. Unify execution state and business state
> 6. Launch/Pause/Resume with simple APIs
> 7. Contact humans with tool calls
> 8. Own your control flow
> 9. Compact Errors into Context Window
> 10. Small, Focused Agents
> 11. Trigger from anywhere, meet users where they are
> 12. Make your agent a stateless reducer

(Bonus Factor 13: *"Pre-fetch all the context you might need."*)

---

## 4. Anti-patterns

- **The 1000-line CLAUDE.md / AGENTS.md.** Burns instruction budget on every turn and uniformly degrades adherence to *all* rules, not just late ones (Mistele). Anthropic ships an explicit "ignore these bad instructions" mitigation in its system prompt — a signal that this is the dominant failure mode in the wild.
- **Auto-generating the root instruction file and committing it unedited.** Universally regretted; auto-generators prioritize comprehensiveness over restraint.
- **Documenting file paths instead of capabilities.** Paths rot; capabilities don't.
- **A wall of "don't"s with no matching "do"s.** Zhenylenko (Augment Code, 22 Apr 2026): *"The PR took twice as long and was 20% less complete on average."*
- **Per-developer hot-fix instructions appended to project CLAUDE.md.** These belong in `~/.claude/CLAUDE.md` (user) or `CLAUDE.local.md` (gitignored).
- **Stuffing every conceivable command into the root file.** Use a Makefile or `scripts/` and reference one or two examples.
- **Adding MCP servers reflexively.** Zechner: most MCP servers are overengineered and dilute context.
- **Context-stuffing huge architecture overviews.** Augment Code's empirical finding: agents read 12+ doc files for a two-line config change and produce worse output than with no docs.
- **Skill descriptions that don't trigger.** Anthropic's own engineers note Claude *under-triggers* skills; descriptions should be slightly "pushy" and list synonyms.
- **Stop-hooks that exit 2 without `stop_hook_active` guards.** Infinite-loop your agent.
- **Documenting REST + polling patterns for a feature that requires WebSockets.** Augment Code's example: agent followed the docs and shipped technically functional but architecturally wrong code. The fix is spec-driven development for net-new architecture, not better AGENTS.md.
- **Trusting agent verification without independent checks.** Always provide tests/screenshots/logs.
- **Letting `/clear` and `/compact` decisions be implicit.** Anthropic: `/clear` between tasks, `/compact <instructions>` to focus what is preserved.
- **Mixing project and user concerns in the same file.** Once you do, you can no longer commit it safely.
- **Editing CLAUDE.md from inside an agent session and assuming it reloads.** Use `@CLAUDE.md` in a prompt to trigger a re-read mid-session.

---

## 5. Proposal A — Concrete reference layout (recommended)

**Design goals**: AGENTS.md-rooted, agent-agnostic, lightweight (markdown + folders), brown-field-friendly, with a *thin* Claude Code and OpenCode overlay. Single-binary tools only. Works without any external service.

### 5.1 Filesystem

```
repo/
├─ README.md
├─ AGENTS.md                         # canonical, ≤200 lines
├─ CLAUDE.md                         # one line: @AGENTS.md (+ CC-only extras)
├─ CLAUDE.local.md                   # gitignored
├─ .mcp.json                         # only if MCP is actually used
├─ Makefile                          # canonical commands
├─ docs/
│  ├─ architecture.md
│  ├─ style.md
│  ├─ testing.md
│  └─ adr/
│     ├─ 0001-record-architecture-decisions.md
│     └─ 0002-...
├─ specs/
│  └─ <YYYY-MM>-<slug>/
│     ├─ spec.md
│     ├─ plan.md
│     ├─ tasks.md
│     └─ scratch.md
├─ scripts/
│  ├─ verify.sh                      # invoked by Stop hook + by humans
│  └─ codegen.sh
├─ .agents/                          # vendor-neutral shared assets
│  ├─ skills/
│  │  └─ <skill-name>/SKILL.md
│  └─ subagents/
│     └─ <agent-name>.md
├─ .claude/
│  ├─ settings.json                  # committed
│  ├─ settings.local.json            # gitignored
│  ├─ commands/
│  │  ├─ spec.md                     # /spec
│  │  ├─ plan.md                     # /plan
│  │  └─ verify.md                   # /verify
│  ├─ agents/                        # symlink: -> ../.agents/subagents
│  ├─ skills/                        # symlink: -> ../.agents/skills
│  └─ rules/
├─ .opencode/
│  ├─ opencode.jsonc
│  ├─ agents/                        # symlink: -> ../.agents/subagents
│  ├─ commands/
│  └─ skills/                        # symlink: -> ../.agents/skills
├─ .cursor/
│  └─ rules/
│     └─ project-context.mdc         # alwaysApply: true; points to AGENTS.md
└─ .github/
   ├─ copilot-instructions.md        # one line: "See ../AGENTS.md"
   └─ agents/
```

### 5.2 Root AGENTS.md (template, ≤200 lines)

```markdown
# <Project> — Agent Instructions

> README for agents. Read by Codex, OpenCode, Cursor, Amp, Factory, Gemini CLI,
> Copilot, and (via `@AGENTS.md`) Claude Code.

## Stack
- <language + version>
- <framework>, <database>, <test runner>
- Single source of truth for tool versions: `.tool-versions` / `mise.toml`

## Commands (prefer these over guessing)
- `make test`     — fast unit tests; <30s
- `make test-all` — full suite including integration
- `make lint`     — static checks; runs `make fmt` first
- `make verify`   — calls `scripts/verify.sh`; what the Stop hook runs
- `make dev`      — local dev server; emails/webhooks log to stdout

## Where things live (capabilities, not paths)
- HTTP boundary: see @docs/architecture.md
- Persistence: <orm/library>; never call it from the HTTP layer
- Generated code: anything under `*/generated/` — regenerated by `make codegen`

## Conventions
- Style guide: @docs/style.md
- Testing strategy: @docs/testing.md
- ADRs (decisions of record): @docs/adr/

## Do
- Run `make verify` before claiming done.
- For new features, create `specs/<YYYY-MM>-<slug>/` and put the spec there
  before writing code (see @.claude/commands/spec.md).
- For new architectural choices, add an ADR in `docs/adr/`.

## Don't
- Don't add dependencies without an ADR.
- Don't edit `*/generated/`.
- Don't run destructive Git operations (`push --force`, `reset --hard origin`).
- Don't put secrets, hostnames, or per-developer paths in this file —
  put them in `CLAUDE.local.md` (gitignored).
```

### 5.3 CLAUDE.md (thin overlay)

```markdown
@AGENTS.md

# Claude Code specifics
- Default to plan mode (`shift-tab` to enter).
- Use TodoWrite aggressively; the harness echo helps stay on track.
- Skills available under `.claude/skills/` — invoke by name.
- Subagents under `.claude/agents/` — say "use the explorer subagent" explicitly.
- Slash commands under `.claude/commands/`: `/spec`, `/plan`, `/verify`.
```

### 5.4 .claude/settings.json (the three hooks worth having)

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [{ "type": "command",
        "command": "test -x scripts/fmt-file.sh && scripts/fmt-file.sh \"$CLAUDE_TOOL_INPUT_FILE_PATH\" || true" }]
    }],
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{ "type": "command",
        "command": "echo \"$CLAUDE_TOOL_INPUT\" | grep -qE 'rm -rf|push --force|reset --hard|DROP TABLE' && exit 2 || exit 0" }]
    }],
    "Stop": [{
      "hooks": [{ "type": "command",
        "command": "INPUT=$(cat); [ \"$(echo $INPUT | jq -r '.stop_hook_active')\" = 'true' ] && exit 0; make verify || exit 2" }]
    }]
  },
  "permissions": {
    "allow": ["Bash(make:*)", "Bash(git status)", "Bash(git diff:*)", "Bash(rg:*)"],
    "deny":  ["Bash(git push --force:*)", "Bash(git reset --hard origin:*)"]
  }
}
```

### 5.5 .opencode/opencode.jsonc

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "default_agent": "build",
  "instructions": ["AGENTS.md", "docs/architecture.md", "docs/style.md"],
  "model": "anthropic/claude-sonnet-4-6",
  "small_model": "anthropic/claude-haiku-4",
  "permission": {
    "bash": {
      "make *": "allow",
      "git push --force*": "deny",
      "rm -rf*": "deny"
    }
  }
}
```

### 5.6 .cursor/rules/project-context.mdc

```mdc
---
description: ""
alwaysApply: true
globs:
---
# Project Context
This project follows the conventions in AGENTS.md at the repository root.
Read AGENTS.md before any task. See @AGENTS.md.
```

### 5.7 Cross-tool subagent (`.agents/subagents/explorer.md`)

Claude Code form (`.claude/agents/explorer.md`):

```yaml
---
name: explorer
description: Read-only codebase explorer. Use proactively for "find where X
  is implemented", "how does Y work", "what calls Z". Returns a focused summary,
  never edits files.
tools: Read, Grep, Glob, Bash
model: inherit
---

You are a read-only codebase explorer. Your job is to investigate the
repository and return a focused, citation-rich answer — file paths with
line numbers, never code dumps. Constraints:
- Never edit files. Never run state-changing commands.
- Limit your scope; if the question is broad, ask one clarifying question.
- Output: 1) Answer (2–6 sentences). 2) Evidence (bulleted file:line refs).
```

OpenCode form (`.opencode/agents/explorer.md`):

```yaml
---
description: Read-only codebase explorer (mirrors .agents/subagents/explorer.md)
mode: subagent
permission:
  read: allow
  write: deny
  edit: deny
  bash:
    "rg *": allow
    "ls *": allow
    "*": deny
---
You are a read-only codebase explorer. ...
```

### 5.8 .agents/skills/verify/SKILL.md

```yaml
---
name: verify
description: Run the project's verification gate. Use whenever the user
  says "verify", "is this ready", "check before commit", or after any non-trivial
  edit. Runs `make verify`, summarizes failures with file:line evidence,
  and proposes fixes.
---

1. Run `make verify`.
2. If it passes, summarize what changed and stop.
3. If it fails, parse the output, group errors by file, and propose the
   smallest fix that would make the next run pass.
4. Never silently disable a failing test. If a test must be skipped, write
   an ADR draft and ask the user to confirm.
```

### 5.9 docs/adr/0001-record-architecture-decisions.md (Nygard)

```markdown
# 1. Record architecture decisions
## Status
Accepted
## Context
We need a durable record of architecturally significant decisions that
agents and humans can both read.
## Decision
Use Michael Nygard's ADR format, one file per decision in `docs/adr/`,
named `NNNN-kebab-title.md`, append-only. Supersession is recorded by
a new ADR referencing the old one.
## Consequences
- Easy to read by agents (small markdown files).
- History is searchable in plain text.
- Cost: another file to write per decision.
```

---

## 6. Proposal B — Modular minimum + options

### 6.1 Minimum viable harness (three files)

For personal repos, throwaway projects, and the first day of brown-field adoption:

```
repo/
├─ AGENTS.md          # 30–80 lines: stack, commands, where things live, 3 don'ts
├─ CLAUDE.md          # one line: @AGENTS.md
└─ Makefile           # at minimum: test, lint, fmt, verify
```

Every AGENTS.md-aware agent works; Claude Code works via the import; Cursor's AGENTS.md support handles Cursor. No `.claude/`, no `.opencode/`, no `.cursor/rules/`. Add `.gitignore` entries for `CLAUDE.local.md` and `.claude/settings.local.json` defensively.

### 6.2 Optional modules, ordered by typical ROI

Add when the listed pain shows up; not before.

| # | Module | Add when… | Cost | Files |
|---|---|---|---|---|
| 1 | **ADRs** | "Why did we choose Postgres again?" comes up; agent re-suggests previously rejected options | 30 min to seed 5–10 ADRs | `docs/adr/*` |
| 2 | **docs/ progressive disclosure** | AGENTS.md is creeping past 200 lines | Reorg; no new tools | `docs/architecture.md`, `docs/style.md`, `docs/testing.md`; reference from AGENTS.md with `@` |
| 3 | **Three hooks** | Agent keeps writing unformatted code, or runs a dangerous command | 15 min; one JSON file | `.claude/settings.json` |
| 4 | **Skills** | Re-prompting the same workflow >2×/day, or agent keeps mis-using a library | One folder per skill | `.agents/skills/<name>/SKILL.md` |
| 5 | **Subagents** | Want read-only exploration without polluting main context | One MD per agent | `.agents/subagents/<name>.md`, symlinked into `.claude/agents/`, `.opencode/agents/` |
| 6 | **MCP server** | A specific external system is genuinely too painful via CLI | One JSON entry + one binary | `.mcp.json` |
| 7 | **Spec-driven workflow** | Net-new architecture (not just feature work in known territory) | One folder per feature; or install Spec Kit | `specs/<YYYY-MM>-<slug>/{spec,plan,tasks,scratch}.md` |
| 8 | **Eval/verification harness** | Need to claim "the agent improves over time" with data | `scripts/eval/` folder; small Python harness | out of scope here |
| 9 | **Cursor `.cursor/rules`** | 2+ Cursor users | One `.mdc` per rule | `.cursor/rules/*.mdc` with `alwaysApply: true` for the core one |
| 10 | **Cross-tool symlinks** (`.agents/`) | Maintaining the same agents in two places | 5 min once | `.agents/{skills,subagents}/`, symlinks |

The ordering matters. ADRs first because they're cheap and durable. Hooks early because they're deterministic. Skills/subagents only after you've felt the re-prompting tax. MCP last because it has the worst cost-to-value ratio.

### 6.3 What this is *not* (deliberately out of scope)

- **Heavy orchestration frameworks** (BMAD, full Spec Kit, LangGraph-as-a-product). Adopt only when the lighter version is being skipped by the team.
- **Vector DBs / RAG over your own repo.** Modern agents grep and read files faster than they retrieve from a vector store, and the indexing pipeline is its own maintenance burden. (Anthropic, Ronacher, Willison all converge here.)
- **Auto-memory persistence across sessions in the committed repo.** Claude Code's auto-memory writes to `~/.claude/projects/<hash>/memory/` — leave it there; don't commit it.

---

## 7. Recommendations

### Stage 1 (today, 1 hour)
1. Hand-write `AGENTS.md` at the root, ≤80 lines (use §5.2 template). Don't auto-generate.
2. Add `CLAUDE.md` with one line: `@AGENTS.md`.
3. Add a `Makefile` with `test`, `lint`, `fmt`, `verify` targets.
4. Add `.gitignore` lines for `CLAUDE.local.md` and `.claude/settings.local.json`.

**Threshold to move on**: the agent stops asking how to run tests.

### Stage 2 (week 1, 2 hours)
5. Add 5–10 ADRs covering load-bearing past decisions; commit `docs/adr/0001-record-architecture-decisions.md` first.
6. Split AGENTS.md into AGENTS.md + `docs/architecture.md` + `docs/style.md`; reference with `@`.
7. Add the three hooks from §5.4 to `.claude/settings.json`.

**Threshold to move on**: the agent's PRs match house style without intervention.

### Stage 3 (week 2, half a day)
8. Add `.agents/skills/verify/SKILL.md`; symlink into `.claude/skills/` and `.opencode/skills/`.
9. Add an `explorer` subagent under `.agents/subagents/`; symlink into both tool folders.
10. Adopt the `specs/<date>-<slug>/` convention for the next feature. Write `spec.md` and `plan.md` *before* a single line of code.

**Threshold to move on**: net-new features routinely begin with a spec, not a prompt.

### Stage 4 (month 2, opt-in)
11. Decide on Spec Kit vs. lightweight `specs/` based on whether your team is actually skipping spec-first. Spec Kit gives you a CLI and 30+ agent integrations; the lightweight version is one folder.
12. Add MCP only if you have a *specific* automation (Playwright, a sensitive DB) that is unambiguously worse via CLI.
13. If you run >1 agent in parallel, adopt `git worktree`-per-task with shared `.agents/` and per-task `specs/`.

### When to *remove* something
- An AGENTS.md section is "remove it if Claude is already doing the right thing without it" (Anthropic).
- A skill that has never auto-triggered in 30 days — delete it or rewrite the `description:` to be more pushy.
- A hook that has never blocked or fired — delete it; hooks tax every turn.
- A superseded ADR — keep it (append-only is the value); add a new ADR that says so.

---

## 8. Caveats

- **The field is moving fast.** Anthropic shipped Skills (Oct 2025); AGENTS.md was donated to the Linux Foundation (9 Dec 2025); Anthropic split subscription billing on 15 Jun 2026 (Agent SDK credits separated from interactive Claude Code); "Dreaming"/outcomes/multi-agent orchestration shipped May 2026. Treat any single tool's UI as ephemeral; treat the markdown files in your repo as durable.
- **Tool-specific claims age fastest.** The exact frontmatter fields for Claude Code subagents and OpenCode agents are pinned to the docs as of mid-2026; check the linked official pages before relying on `disable-model-invocation`, `mode: all` defaults, etc.
- **"Instruction budget" numbers are estimates.** Kyle Mistele's ~150–200 figure (HumanLayer, 25 Nov 2025) is community analysis, not Anthropic-published data. The shape of the claim — that adding more rules degrades adherence to *all* rules — is consistent with Anthropic's own behavior (their system prompt explicitly tells Claude to ignore bad CLAUDE.md instructions).
- **Hook compliance numbers come from a non-Anthropic source.** The Dotzlaw write-up (dotzlaw.com, 2026) frames prompts as 70–90% compliance and hooks as 100% compliance. The qualitative claim is uncontroversial; the precise percentages should be read as that team's measurement, not industry-wide truth.
- **Context-rot numbers from Chroma have a vendor lens.** Chroma sells a vector DB and benefits from "long contexts fail"; Databricks Mosaic partially replicated the result. The qualitative claim (accuracy degrades non-uniformly well before the advertised limit) is solid; specific percentages should be read carefully.
- **llms.txt adoption is real on docs sites but no LLM provider's crawler is known to fetch it** (John Mueller, cited in Search Engine Land and Mintlify's posts). Adopt it as a hedge, not as a sole strategy.
- **Spec Kit's "code serves specifications" framing is aspirational.** GitHub's own Manfred Riem cautions that AI agents are "very capable interns" — spec-driven workflows constrain the intern but don't replace review.
- **Auto-memory is opt-in and version-gated.** Claude Code v2.1.59+ writes to `~/.claude/projects/<hash>/memory/`; behavior, location, and toggles have changed across point releases. Don't build automation against it without pinning a version.
- **Tool precedence rules differ subtly.** Cursor: Team → Project → User Rules, "earlier sources take precedence when guidance conflicts." Claude Code: more-specific wins, files merge. Codex: `AGENTS.override.md > AGENTS.md > TEAM_GUIDE.md > .agents.md` per directory. If you mix tools, validate with a small "what rules are active?" probe before trusting a layered setup.
- **MCP cost-benefit is changing.** Anthropic's 15 Jun 2026 billing split makes third-party MCP usage explicitly metered, strengthening the case for plain-CLI tools whenever feasible.
- **Don't underestimate Augment Code's data.** Slava Zhenylenko, *A good AGENTS.md is a model upgrade. A bad one is worse than no docs at all.* (Augment Code blog, 22 Apr 2026): *"The same file boosted best_practices by 25% on a routine bug fix and dropped completeness by 30% on a complex feature task in the same module."* Same AGENTS.md, opposite effects on different tasks. Plan to maintain it.

## Addendum: task-runner flexibility

The original report (§5, §6, §7) treats the `Makefile` as the canonical
command interface for agents. That recommendation still stands as the
default: `make` is universally installed, target syntax is stable across
decades, and every agent CLI surveyed allow-lists `make *` without
friction.

This template now exposes a `task_runner` choice so that recommendation
can be matched to the surrounding toolchain instead of forced onto it:

- **`make`** (recommended default for projects without a native task
  manager) — generates a `Makefile`. Matches the report's original
  prescription verbatim.
- **`just`** — generates a `justfile` (https://just.systems/). Same
  ergonomics for agents (recipe targets, doc-comments via `just --list`),
  cleaner authoring (no tab-sensitivity, comment syntax, variables).
  Appropriate where contributors already have `just` on PATH.
- **`none`** — generates neither. For projects whose package/project
  manager already provides task management — **pixi** (`pixi run <task>`,
  defined in `pixi.toml`), **hatch** (`hatch run <env:task>` from
  `pyproject.toml`), pnpm scripts, cargo aliases, etc. The harness then
  surfaces the raw `test_command` / `lint_command` / `fmt_command` /
  `verify_command` answers to agents directly, and the Claude Code Stop
  hook and `/verify` slash command invoke whatever `verify_command` was
  set to (commonly `pixi run verify` or `hatch run verify`).

The agent-facing wording in AGENTS.md, CLAUDE.md, README.md, the
`/verify` slash command, the `verify` skill, and the OpenCode permission
list is rendered from a single shared Jinja macro
(`template/_macros.jinja`) so that all surfaces stay consistent with the
chosen runner.