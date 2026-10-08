# agy-agents

Native specialist-agent configuration for **Google Antigravity 2.0 and Antigravity CLI**, adapted from the operating model in `hevyfs/codex-agents`.

> **Runtime status: UNVERIFIED INITIAL CONFIGURATION.** Static validator/unit-test coverage is green, but PR #1 has not yet been executed end-to-end inside an actual Antigravity runtime. Do not describe plugin discovery, skill restrictions, idle-agent reuse, or worktree orchestration as runtime-proven until `docs/runtime-validation.md` contains recorded evidence.

The goal is not to emulate Codex internals. It preserves the useful engineering model while using Antigravity-native primitives:

- the primary session is the orchestrator;
- narrow specialists own discovery, research, architecture, design, implementation, review, and verification;
- independent lanes run concurrently;
- concurrent writers are instructed to use isolated Antigravity Git worktrees;
- same-lane dependent follow-up is instructed to return to the same idle subagent with retained context;
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

## Installing `hevyfs/my-skills`

`agy-agents` does **not** vendor `hevyfs/my-skills`. Clone the pinned fork separately and expose each individual skill folder through a path Antigravity actually discovers.

Antigravity 2.0 / IDE locations:

```text
<workspace>/.agents/skills/<skill-folder>/
~/.gemini/config/skills/<skill-folder>/
```

Antigravity CLI locations:

```text
<workspace>/.agents/skills/<skill-folder>/
~/.gemini/antigravity-cli/skills/<skill-folder>/
```

Each exposed folder must contain its original `SKILL.md` and any companion files it references. Copy or symlink the non-deprecated skill directories from `hevyfs/my-skills`, not just the Markdown body.

After skill discovery:

1. Open the target project.
2. Run `/setup-matt-pocock-skills` once for that project.
3. Run `/ask-matt` and ask which route fits a multi-ticket spec. Confirm the expected `/to-spec` → `/to-tickets` → `/implement-spec` flow.
4. Then exercise an agy-agents worker lane.

The primary session owns user-invoked workflows. Role-specific skill declarations are **prompt contracts**, not a demonstrated Antigravity runtime-enforced allowlist. Runtime refusal of recursive `/ask-matt` / `/implement-spec` invocation remains part of the smoke test.

## Compatibility manifest

`skill-routing.json` is the local machine-readable authority for workflow-lane routing and role skill contracts. The always-on rule is a human-readable projection, and CI checks that every manifest route appears there instead of maintaining a second hard-coded routing table in the validator.

This initial port is reconciled against:

- `my-skills@d5628a28514a06d0b587cf838a983321eff1557a`
- `codex-agents@0eb3b8190e19a55ac4a71620c4e212325940c429`

The dotted lane names are **agy-agents internal routing-intent identifiers**, not literal IDs exported by `my-skills`.

## Antigravity-native orchestration

The installable always-on rule lives at `rules/orchestration.md`.

### Active workflow precedence

Generic routing never weakens an active skill's stricter contract. In particular, `/implement-spec` retains one integration branch, dependency-graph/frontier scheduling, one branch/worktree per ticket implementer, a dedicated merger subagent after each completed ticket, and integrated review only after ticket work is merged.

### Immutable reviewer input

Reviewer stays read-only and has no shell. Before Standards/Spec review, the parent resolves fixed-point/merge-base/head SHAs and materializes the complete diff, changed-file list, and commit list into one immutable snapshot. Both review axes consume that exact same candidate snapshot.


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

Install the validator dependency and run:

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python scripts/validate_agents.py .
```

The validator checks:

- official plugin manifest shape;
- strict YAML parsing of agent/rule frontmatter (including rejection of invalid unquoted `: ` in values);
- all eight agent definitions and supported model/tool names;
- read-only roles do not expose mutation/terminal tools;
- high-risk roles remain on `pro`;
- verifier can execute checks but cannot directly edit source;
- `skill-routing.json` stays synchronized with the runtime rule;
- sticky-lane reuse and concurrent-writer worktree isolation remain present.

Static validation checks declarations and internal consistency; it does not prove Antigravity runtime enforcement.

GitHub Actions runs the same checks on pushes and pull requests.

For actual runtime validation, follow [`docs/smoke-test.md`](docs/smoke-test.md) and record evidence in [`docs/runtime-validation.md`](docs/runtime-validation.md).

## Source model

The role architecture is adapted from `hevyfs/codex-agents`, but Antigravity-specific behavior is implemented natively:

- plugin packaging instead of Codex TOML installation;
- Markdown/YAML custom agents instead of TOML custom agents;
- explicit Antigravity tool allowlists instead of Codex sandbox modes;
- `model: pro` for high-risk roles instead of `xhigh` reasoning effort;
- `Workspace: branch` worktrees for concurrent writer isolation;
- `send_message`/idle-agent auto-wake for sticky semantic lanes.

The suite intentionally does not add a custom scheduler, persistent worker service, or fake compatibility layer around Antigravity.
