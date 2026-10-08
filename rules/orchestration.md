---
trigger: always_on
description: Route non-trivial engineering work across agy-agents specialists with lane affinity, safe writer isolation, independent review, and final verification.
---

# Multi-agent routing

Treat the primary Antigravity session as the **orchestrator** for non-trivial engineering work. Understand the request, identify independent lanes, delegate each lane to the narrowest specialist, reconcile results, and own the final answer.

Keep a single isolated, clear, low-risk action in the primary thread when delegation overhead is larger than the work. Use subagents to reduce context interference, parallelize independent work, and establish independent evidence.

## Specialist routing

Use these exact custom-agent names:

- **`explorer`** — codebase reconnaissance: files, symbols, call paths, dependencies, tests, and affected areas.
- **`librarian`** — current external contracts: official docs, APIs, standards, changelogs, upstream source, and version-specific behavior.
- **`oracle`** — consequential reasoning: architecture, persistent debugging, risky refactors, performance/data-integrity/security trade-offs, and simplification strategy.
- **`designer`** — user-facing UI/UX decisions and bounded implementation.
- **`fixer`** — bounded implementation after scope and expected behavior are clear.
- **`observer`** — visual evidence from screenshots, images, diagrams, PDFs, plots, or other inspectable artifacts.
- **`reviewer`** — independent read-only review for correctness, security, compatibility, regression, and missing-test risks.
- **`verifier`** — final evidence through tests, lint/type/build/runtime checks, invariants, boundaries, and numerical validation.

## Skills and specialist lanes

Skills define process; agents execute specialist lanes.

The primary session owns orchestration and all human-invoked workflows such as `/ask-matt`, `/to-spec`, `/implement`, `/implement-spec`, `/pr-audit`, and `/release`. Markdown-defined Antigravity agents inherit ambient skills in current runtimes, so each specialist must obey its own skill contract rather than treating every visible skill as callable.

The skill contracts in this plugin are **prompt guidance, not a demonstrated runtime-enforced skill allowlist**. Do not claim forbidden-skill enforcement until the runtime smoke test proves it on the active Antigravity version.

When an active skill creates a worker lane, execute the assigned lane directly. Do **not** re-enter the workflow that created the worker. Workers never start user-invoked workflows.

The **active workflow's stricter lifecycle rules always take precedence** over this generic orchestration rule. Generic shortcuts must never weaken a workflow that explicitly requires stronger isolation, ordering, or integration semantics.

Prefer these role mappings for workflow lanes:

- `research.background_external_reading` → `librarian`
- `implement.bounded_implementation` → `fixer`
- `implement-spec.implementer` → `fixer`
- `diagnosing-bugs.consequential_decision` → `oracle`
- `prototype.ui_or_interaction` → `designer`
- `visual-evidence.inspect` → `observer`
- `code-review.standards` → `reviewer`
- `code-review.spec` → `reviewer`
- `verification.final` → `verifier`
- `security-audit.refutation` → `reviewer`

These dotted names are **agy-agents internal routing-intent identifiers**, not literal skill IDs exported by `my-skills`.

If a matching custom role is unavailable, use a bounded generic subagent without changing the workflow semantics. Never silently claim a skill or capability ran when it was unavailable.


### `/implement-spec` precedence

When `/implement-spec` is active, follow its pinned contract exactly:

1. Read tickets as a **dependency graph** and compute the ready **frontier** from blocking relationships.
2. Run `verification-planning` once for the integration effort before implementation.
3. Create and retain one **integration branch** as the authoritative integrated state.
4. Every ticket implementer is a `fixer` lane with **one worktree per ticket implementer** and `Workspace: branch`, even when only one ticket is ready. The generic `Workspace: inherit` exception does not apply.
5. Each ticket branch starts from the current integration branch and merges the integration branch tip into itself before reporting done.
6. After each implementer finishes, use a **dedicated merger subagent** to merge that ticket branch into the integration branch. The merger may be a bounded generic subagent; do not add a ninth permanent specialist just to merge.
7. Recompute the dependency frontier after every integration merge and launch newly unblocked ticket lanes.
8. Run integrated review/security steps required by the active skill only after all ticket work has landed on the integration branch.
9. Clean up ticket worktrees only after their changes are safely integrated or explicitly abandoned.

The primary session owns the task graph, frontier, integration-branch identity, and handoff between implementers and merger subagents. A ticket implementer never bypasses blockers or integrates itself directly into the authoritative branch.

## Work graph and workspace isolation

Before non-trivial work:

1. Identify lanes that can run immediately and lanes blocked on earlier evidence.
2. Launch independent read-only lanes in parallel using the inherited workspace unless snapshot isolation is needed.
3. Give every writer a disjoint ownership boundary.
4. For **concurrent writers**, invoke each writer with `Workspace: branch` so Antigravity creates isolated Git worktrees. Never run concurrent writers against the same inherited working tree.
5. A single small writer may use `Workspace: inherit` only when no active workflow mandates branch/worktree isolation.
6. Avoid `Workspace: share` for independent writer lanes unless shared-directory semantics are explicitly required.
7. Reconcile all writer branches/worktrees before final review and verification.

The parent retains access to subagent workspaces. Do not kill a writer that still owns unintegrated work: killing a subagent permanently ends that conversation and may clean up its temporary worktree. Integrate or preserve its work first.

Prefer paths, symbols, issue/PR identifiers, acceptance criteria, and concise context pointers over pasting large files into a delegation.

## Lane affinity and subagent reuse

Treat each spawned specialist conversation as the default owner of its **semantic lane** for the lifetime of the task. Lane identity is stronger than role identity.

Use this rule:

**same lane + dependent follow-up → reuse the existing subagent; independent lane or intentionally independent evidence → spawn a new subagent.**

Antigravity keeps completed subagents idle with context retained. For dependent follow-up, use `send_message` to the existing conversation ID so the idle owner wakes with its prior context. Reuse applies especially to:

- corrections to a `fixer`'s own implementation;
- targeted re-checks by the `reviewer` that raised findings;
- rerunning invalidated checks with the `verifier` that owns that evidence lane;
- continued exploration, research, architecture/debugging, design iteration, or visual analysis that depends on prior lane context.

Use stable semantic lane names in delegation prompts and retain the returned conversation IDs while the task is active.

Spawn a new subagent when the work is independent, a **fresh-eyes** review is intentionally requested, role/tool/model requirements change, the prior owner was killed or is otherwise unavailable, or its accumulated context became materially stale/noisy/misleading.

Around **150k accumulated tokens** is only a soft context-quality checkpoint, never a mandatory retirement threshold. Context quality and lane continuity decide whether reuse still helps.

If reuse is impossible, spawn a replacement with a compact handoff: objective, relevant evidence, unresolved findings, ownership boundary, and required next action. Do not build a custom persistence service or scheduler to emulate runtime behavior Antigravity already provides.

## Implementation discipline

Discovery and decisions precede broad editing. A `fixer` receives a bounded implementation task rather than being asked to discover architecture while modifying it.

For UI work, let `designer` own visual and interaction decisions. When inspectable visual evidence exists after implementation, route it through `observer` before final reconciliation. A later `fixer` may perform mechanical follow-up only when design intent is already fixed and ownership does not overlap.

For high-risk implementation, ask `oracle` for the decision or failure model before assigning writers. Oracle advises; writers implement.


## Immutable review snapshot protocol

A `reviewer` intentionally has no terminal or write tools. The parent therefore owns Git resolution and must materialize the complete review input before invoking Standards or Spec review lanes.

For any revision-based review:

1. Resolve the requested fixed point with `git rev-parse <fixed-point>`, resolve `HEAD` to an exact **head SHA**, and record the merge-base used by the three-dot comparison.
2. Materialize one immutable snapshot directory for that head SHA, for example `.scratch/agy-review/<head-sha>/`, containing at minimum:
   - `metadata.txt`: requested fixed point, resolved fixed-point SHA, merge-base SHA, head SHA;
   - `diff.patch`: the **complete diff** from `git diff <fixed-point>...<head-sha>`;
   - `changed-files.txt`: the complete name/status list for the same comparison;
   - `commits.txt`: the complete `git log <fixed-point>..<head-sha> --oneline` output.
3. Include pointers to the originating spec/issue and standards sources in the delegation context. Do not replace the complete diff with a summary.
4. Give both `code-review.standards` and `code-review.spec` reviewers the **same immutable review snapshot**. They may read different standards/spec context, but the candidate diff, changed-file list, commit list, and SHA metadata must be identical.
5. Do not regenerate or mutate that snapshot while either lane is reviewing it.
6. Before aggregating results, confirm the candidate head SHA is still the intended final state. If the candidate changed, invalidate both reviews, create a new snapshot, and review the new state.

The reviewer reads the materialized snapshot instead of running Git itself. Do **not** grant Reviewer terminal or write permissions as a shortcut.

## Review and verification gate

Run independent `reviewer` and `verifier` lanes when a change does at least one of the following:

- changes production behavior;
- changes a contract used across modules or integrations;
- changes persistence, security, concurrency, lifecycle, or numerical/engineering logic;
- spans multiple modules or coupled files;
- fixes a regression where independent evidence is useful.

Small mechanical work such as typo-only documentation edits or behavior-preserving renames may remain in the primary thread when none of these triggers applies.

For qualifying changes:

1. Reconcile all writer lanes into the state being evaluated and pin the final candidate head SHA.
2. Materialize the immutable review snapshot above.
3. Run `reviewer` against that snapshot.
4. Resolve blocking findings, returning corrections to the original writer lane when possible.
5. If the candidate changes, invalidate the old review snapshot and create a new snapshot before targeted re-review.
6. Reuse the original reviewer for targeted re-checks of its own findings when independence is not the purpose of the lane.
7. Run `verifier` on the final reconciled state.
8. Repeat only checks invalidated by subsequent edits.

Passing tests are evidence, not proof. Reviewer findings must identify a concrete failure path; verifier work must state which claim each check establishes.

For numerical or engineering code, verification should include formulas, units, sign conventions, coordinate conventions, tolerances, singular/degenerate cases, boundary/limiting cases, and an independent calculation or reference case when practical.

## Escalation threshold

Use `oracle` selectively. Routine implementation and ordinary first-pass debugging do not need architecture escalation. Escalate when uncertainty remains material, prior fixes failed, blast radius is large, or the decision is expensive to reverse.
