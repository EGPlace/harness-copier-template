# `/babysit-copilot-review` — operator guide

## What this is

A user-triggered slash command that drives a GitHub Copilot code-review
loop on a single pull request. The agent requests a Copilot review,
waits for it to arrive, triages each new inline comment (fix /
dismiss-and-resolve / escalate), runs the project's verify gate, pushes
the fix, and re-triggers Copilot for another pass — stopping on a
clean review, an escalation, or an iteration cap. **The loop never
merges.** The command body the agent follows lives in this template
under `template/.agents/commands/` (gated on the `copilot_review_loop`
flag in the path) and renders to `.agents/commands/babysit-copilot-review.md`
in generated projects.

## Prerequisites

- **`gh` CLI ≥ 2.88.0** on PATH and authenticated (`gh auth status`).
- **Copilot Code Review enabled** on the repository (Settings → Code &
  automation → Code review → enable for this repository).
- **Recommended:** generate `.github/copilot-instructions.md` by setting
  the `copilot` Copier flag to `true`. Copilot Code Review reads the
  first 4,000 characters of that file from the base branch and uses
  them to steer review focus.
- **Recommended:** add a default-branch ruleset:
  Settings → Rules → New ruleset → enable
  **"Automatically request Copilot code review"** with
  **"Review new pushes"**. This is the cleanest re-trigger mechanism;
  the bundled GraphQL `requestReviews(botIds:)` workaround in
  `scripts/gh_rerequest_copilot.sh` is only a fallback for when the
  ruleset is not configured.

## Auth & permissions

The loop performs read+write operations against the PR. Pick the
tightest token your environment allows:

**Fine-grained personal access token** (local developer use):

| Scope          | Permission   | Why                                            |
| -------------- | ------------ | ---------------------------------------------- |
| Pull requests  | Read & write | Request reviews, dismiss, comment, push fixes. |
| Contents       | Read & write | Required by `resolveReviewThread` (see below). |
| Metadata       | Read         | Default. Discover the repo/PR.                 |

The Contents:write requirement on `resolveReviewThread` is non-obvious
— it is documented in GitHub Community Discussion #44650; a token with
only Pull requests:write gets a permissions error from the mutation.

**GitHub App** (org-scale deployments): grant the same permissions
under the equivalent App scope names (`pull_requests:write`,
`contents:write`, `metadata:read`) and install on the target repo.

## Cost & rate-limit awareness

- Each Copilot review consumes **1 premium request** from the seat
  owner. As of June 1 2026, Copilot moved to usage-based billing via
  AI Credits; an unchecked loop can run up the bill quickly.
- The `--max-iterations 5` default in `babysit_copilot_review.py`
  exists for exactly this reason. Lower it for cost-sensitive repos;
  raise it only if you've measured the cost.
- Each iteration also runs the project's verify gate at least once
  locally (CI cost is the project's own to budget).

## Local dev vs CI

The driver script is harness-agnostic — it talks to `gh` and your
local checkout, so it runs identically from a developer machine and
from a CI runner.

For an automated CI variant, use
[`anthropics/claude-code-action@v1`](https://github.com/anthropics/claude-code-action)
on the `pull_request` and `pull_request_review` events, filtering on
`sender.login == 'copilot-pull-request-reviewer[bot]'`. **Do not use
the `pull_request_target` event** for this — it runs with the base
repo's secrets in the context of fork PRs, which is a known
exfiltration vector. The bundled command refuses fork PRs for the
same reason; if you need fork support in CI, gate the workflow on a
maintainer-applied label and review the secrets blast-radius first.

## Known gaps

- **`github/github-mcp-server` does not yet ship a
  `resolve_review_thread` tool** (tracking issue #1768). Until it
  lands, the loop uses `scripts/gh_resolve_thread.sh`, which calls
  `gh api graphql` directly.
- **REST review re-requests are no-ops post-submission.** Once
  Copilot has reviewed a PR, `POST /pulls/{n}/requested_reviewers`
  and `gh pr edit --add-reviewer @copilot` silently do nothing. We
  work around it with the GraphQL `requestReviews(botIds:)` mutation
  in `scripts/gh_rerequest_copilot.sh` (also called from the Python
  driver under `--next-iteration`).
- **`authorAssociation` is not a Copilot signal.** The upstream
  Codex CLI `babysit-pr` watcher (openai/codex#19148) filters reviews
  by `authorAssociation == "BOT"` and ends up dropping every Copilot
  review (Copilot reviews come back as `"NONE"`). Our driver matches
  on `user.login` prefix `copilot-pull-request-reviewer` instead, so
  it does not have this bug — but if you fork it, keep the same
  filter.

## Troubleshooting

The Python driver uses distinct exit codes the slash command consumes:

| Exit | Meaning                                                            |
| ---- | ------------------------------------------------------------------ |
| 0    | Success; a fresh Copilot review for the current HEAD has arrived.  |
| 2    | Prerequisite failure (`gh` missing, not authenticated, bad args).  |
| 3    | `--pr auto` could not find an open PR for the current branch.      |
| 4    | No Copilot review within the `--max-wait-s` cap (default 20 min).  |
| 5    | Infinite-loop guard: same comment body seen on two SHAs.           |

Common situations and where to look:

- **No review ever arrives (exit 4).** Check `gh pr checks` — if CI is
  red, Copilot may be waiting. Open `gh pr view --web` and confirm
  Copilot is a requested reviewer; if not, the bot may have been
  removed from the requested-reviewers list and the GraphQL re-trigger
  workaround didn't take. Try `scripts/gh_rerequest_copilot.sh
  <owner> <repo> <pr>` manually.
- **Exit 2 from `gh auth status`.** Run `gh auth login` (or `gh auth
  refresh -s repo,read:org` if your existing token is missing scopes).
- **Exit 3 from `--pr auto`.** The current branch has no open PR. Open
  one first with `gh pr create`, or pass `--pr <number>` explicitly.
- **Exit 5 (infinite-loop guard).** Either Copilot is fixated on a
  single comment the loop cannot satisfy, or your fix is being undone
  by formatter/linter passes between iterations. Inspect the
  comment under `~/.cache/babysit-copilot-review/seen-comments-<pr>.json`
  and decide manually.
- **Stale cached bot id.** Delete
  `~/.cache/babysit-copilot-review/bot-ids.json` and let the driver
  rediscover.
