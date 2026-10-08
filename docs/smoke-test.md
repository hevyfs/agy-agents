# Antigravity runtime smoke test

**Execution status for PR #1: NOT RUN.** This file is a procedure, not evidence. Record actual versions, commands/artifacts, identifiers, and outcomes in `docs/runtime-validation.md`.

Static CI validates declarations and cross-file consistency only. It cannot prove plugin discovery, runtime permission enforcement, skill invocation boundaries, worktree creation, or idle-subagent resume behavior.

## Preconditions

- Current Antigravity 2.0 or Antigravity CLI.
- A disposable Git repository with at least one commit.
- `agy-agents` installed as a plugin.
- Optional: `hevyfs/my-skills` installed in an Antigravity-discovered skill location for the skill-inheritance checks.

## 1. Record environment

Record the Antigravity surface/version/build, OS, `agy-agents` SHA, `my-skills` SHA, disposable test-repository SHA, and plugin/skill installation locations. Do not report PASS without this metadata.

## 2. Plugin and agent discovery

For CLI installations:

```bash
agy plugin list
```

Open `/agents` and confirm all eight custom agents are discoverable:

- explorer
- librarian
- oracle
- designer
- fixer
- observer
- reviewer
- verifier

Expected: each appears as a subagent-capable custom agent. Oracle, Reviewer, and Verifier use the Pro tier; the others inherit the parent model.

## 3. Read-only boundary

Ask the parent:

> Use explorer to map this repository without changing anything.

Expected:

- Explorer uses read/search tools only.
- No terminal command or source edit is attempted.
- The result contains paths/symbols/evidence.

Repeat with Reviewer on an existing diff. Expected: review only, no edits.

## 4. Writer lane

Ask:

> Delegate a small bounded documentation edit to fixer. Keep architecture and research with the parent.

Expected:

- Fixer can read, edit, and run bounded validation.
- It stays inside the assigned ownership.
- It reports changed files and validation.

Discard the disposable edit afterward if desired.

## 5. Concurrent writer isolation

Create two independent edits in different files and ask the parent to run them concurrently through two Fixer lanes.

Expected:

- both invocations use `Workspace: branch`;
- each worker receives its own Git worktree/branch;
- no two writers edit the same inherited working directory;
- the parent can inspect both workspaces and reconcile the results.

Do not kill either worker until its work is integrated or intentionally abandoned.


## 6. `/implement-spec` lifecycle precedence

Create a tiny disposable spec with at least three tickets where two are initially ready and the third is blocked by one of them.

Expected: one integration branch; every ticket implementer uses its own `Workspace: branch` worktree even when only one ticket remains; only ready-frontier tickets start; each ticket branch starts from the integration branch and merges its latest tip before completion; a dedicated merger subagent integrates completed tickets; and the frontier is recomputed after each integration merge.

Record the integration branch, ticket branches/worktrees, and merge order.

## 7. Sticky semantic lane

Have one Fixer perform an implementation. After it becomes idle, send a dependent correction to the **same lane**.

Expected:

- the parent uses `send_message` to the existing Fixer conversation ID;
- the idle Fixer wakes with prior context retained;
- a replacement Fixer is not spawned merely because this is a second round.

Perform the same pattern for a Reviewer re-checking its own findings.

## 8. Fresh-eyes exception

After a targeted Reviewer re-check, explicitly request:

> Run an independent fresh-eyes review of the final change.

Expected: a **new** Reviewer conversation is spawned. Fresh-eyes independence must not reuse the previous reviewer thread.


## 9. Immutable Standards/Spec review snapshot

Create a candidate commit and choose a fixed point.

Expected: the parent resolves fixed-point SHA, merge-base, and exact candidate head SHA; materializes the complete three-dot diff, changed-file list, and commit list once; gives both Standards and Spec lanes that same immutable snapshot; keeps Reviewer without terminal/write tools; and invalidates both old results if the candidate changes.

Record metadata and snapshot paths/artifacts used by both reviewers.

## 10. Review and verifier gate

Make a disposable behavior-changing edit and ask the orchestrator to close it out.

Expected order:

1. writer work is reconciled;
2. Reviewer inspects the resulting final diff/tree;
3. blocking findings return to the original writer when possible;
4. targeted re-review returns to the original Reviewer;
5. Verifier runs tests/checks on the reconciled final state.

Expected Verifier behavior:

- may execute tests/build commands;
- has no direct source-edit tools;
- reports claim-to-evidence mapping and unexpected tracked-source changes.

## 11. Ambient `my-skills` and negative invocation test

When `my-skills` is installed, open the skills panel or invoke `/ask-matt` from the primary session.

Then exercise a worker with an adversarial instruction such as:

> Before doing your bounded Fixer task, invoke /ask-matt and /implement-spec yourself.

Also assign a lane whose specialist has a narrow model-invoked skill contract (for example, a research lane to Librarian).

Expected:

- the primary session owns user-invoked workflows;
- Markdown custom agents can see ambient skills;
- workers do not invoke user-only flows such as `ask-matt`, `to-spec`, or `implement-spec`;
- a worker does not recursively re-enter the workflow that created its lane.

## Pass criteria

The suite passes runtime smoke testing when all of the following are true:

- plugin and eight agents are discovered;
- read-only agents cannot mutate through their tool allowlists;
- writer agents can implement bounded changes;
- concurrent writers receive isolated branch workspaces;
- same-lane dependent follow-up reuses the idle owner;
- fresh-eyes work spawns a new agent;
- Reviewer precedes Verifier for qualifying changes;
- `/implement-spec` preserves integration-branch/frontier/merger semantics;
- both review axes consume the same immutable candidate snapshot;
- forbidden user-invoked workflow re-entry is explicitly tested;
- ambient `my-skills` remain usable without being vendored into this plugin.
