# agy-agents

Native specialist-agent configuration for **Google Antigravity 2.0 and Antigravity CLI**, adapted from the operating model in `hevyfs/codex-agents`.

The goal is not to emulate Codex internals. It preserves the useful engineering model while using Antigravity-native primitives:

- the primary session is the orchestrator;
- narrow specialists own discovery, research, architecture, design, implementation, review, and verification;
- independent lanes run concurrently;
- concurrent writers use isolated Antigravity Git worktrees;
- same-lane dependent follow-up returns to the same idle subagent with retained context;
- the orchestrator reconciles writer lanes before independent review and final verification.

The repository is itself an Antigravity **plugin**.

## Agents

| Agent | Purpose | Effective access | Model |
| --- | --- | --- | --- |
| `explorer` | Codebase reconnaissance | read-only tool allowlist | inherit |
| `librarian` | Current external docs/contracts | local read + web read | inherit |
| `oracle` | Architecture/high-risk decisions | read-only tool allowlist | pro |
| `designer` | UI/UX + bounded user-facing implementation | writer | inherit |
| `fixer` | Bounded implementation | writer | inherit |
| `observer` | Visual evidence | read-only tool allowlist | inherit |
| `reviewer` | Independent correctness/regression/security review | read-only tool allowlist | pro |
| `verifier` | Tests/build/runtime/numerical evidence | command execution, no direct source-edit tools | pro |

Antigravity exposes model tiers (`inherit`, `flash`, `pro`) rather than Codex reasoning-effort levels. The three highest-risk roles are pinned to `pro`; routine roles inherit the parent model.

## Install

### Antigravity CLI

Clone this repository, then install it directly as a local plugin:

```bash
agy plugin install /path/to/agy-agents
agy plugin list
```

The CLI stages installed plugins under its global Antigravity configuration and discovers the bundled agents/rule automatically.

### Antigravity 2.0 / manual installation

For a global installation, place or clone this repository as:

```text
~/.gemini/config/plugins/agy-agents/
```

For one workspace only, place it under:

```text
<workspace>/.agents/plugins/agy-agents/
```

Then open the Antigravity Customizations/Agents UI (or `/agents` in CLI) and confirm the eight specialists are visible.

> The multi-subagent suite targets Antigravity 2.0 and Antigravity CLI. The legacy Antigravity IDE supports skills/rules/plugins, but custom subagent orchestration is documented for 2.0/CLI.

## Using `my-skills`

This repository does **not** vendor `hevyfs/my-skills`. Install those skills separately in an Antigravity-discovered skill location.

Current Markdown-defined Antigravity agents inherit ambient skills, rules, and subagents. That lets both layers cooperate without machine-specific skill paths:

**skills define process; agents execute specialist lanes.**

The primary session owns human-invoked workflows such as `/ask-matt`, `/to-spec`, `/implement`, and `/implement-spec`. Worker prompts restrict themselves to their allowed model-invoked disciplines and explicitly avoid recursively re-entering the workflow that spawned them.

`skill-routing.json` is the local machine-readable compatibility manifest. This initial port is reconciled against:

- `my-skills@d5628a28514a06d0b587cf838a983321eff1557a`
- `codex-agents@0eb3b8190e19a55ac4a71620c4e212325940c429`

The dotted lane names in that manifest are **agy-agents internal routing-intent identifiers**, not literal IDs exported by `my-skills`.

## Antigravity-native orchestration

The installable always-on rule lives at `rules/orchestration.md`.

### Writer isolation

Read-only lanes normally inherit the parent workspace. A single small writer may also inherit it.

When writers run concurrently, each writer must be invoked with `Workspace: branch`. Antigravity creates isolated Git worktrees, preventing concurrent writer lanes from editing the same working directory.

The parent reconciles those branches before reviewer/verifier lanes inspect the final state.

### Sticky semantic lanes

Antigravity subagents become idle after completing a task and retain their context. Sending a message to an idle subagent wakes it again.

The suite therefore uses:

> **same lane + dependent follow-up → reuse existing subagent; independent lane or intentionally independent evidence → spawn a new subagent**

Examples:

- a Fixer correction goes back to the Fixer that implemented the lane;
- a targeted re-check goes back to the Reviewer that raised the finding;
- invalidated verification goes back to the Verifier that owns the evidence;
- a deliberate fresh-eyes review gets a new Reviewer.

Do not kill a writer until its work is integrated or intentionally abandoned: a killed subagent cannot be resumed and Antigravity may clean up its temporary worktree.

## Review gate

For changes that affect production behavior, cross-module contracts, persistence, security, concurrency, lifecycle, numerical/engineering logic, or multiple coupled modules:

1. reconcile writer lanes;
2. run `reviewer`;
3. resolve blocking findings;
4. run targeted re-review as needed;
5. run `verifier` against the final reconciled state.

Small mechanical edits can remain in the primary thread when delegation costs more than execution.

## Validation

Run:

```bash
python -m unittest discover -s tests -v
python scripts/validate_agents.py .
```

The validator checks:

- official plugin manifest shape;
- all eight agent definitions and supported model/tool names;
- read-only roles do not expose mutation/terminal tools;
- high-risk roles remain on `pro`;
- verifier can execute checks but cannot directly edit source;
- `skill-routing.json` stays synchronized with the runtime rule;
- sticky-lane reuse and concurrent-writer worktree isolation remain present.

GitHub Actions runs the same checks on pushes and pull requests.

## Source model

The role architecture is adapted from `hevyfs/codex-agents`, but Antigravity-specific behavior is implemented natively:

- plugin packaging instead of Codex TOML installation;
- Markdown/YAML custom agents instead of TOML custom agents;
- explicit Antigravity tool allowlists instead of Codex sandbox modes;
- `model: pro` for high-risk roles instead of `xhigh` reasoning effort;
- `Workspace: branch` worktrees for concurrent writer isolation;
- `send_message`/idle-agent auto-wake for sticky semantic lanes.

The suite intentionally does not add a custom scheduler, persistent worker service, or fake compatibility layer around Antigravity.
