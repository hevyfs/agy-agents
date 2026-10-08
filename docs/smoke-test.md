# Antigravity runtime smoke test

Run this after installing or updating `agy-agents`. Static CI validates the repository contract; this checklist validates Antigravity discovery and runtime behavior.

## Preconditions

- Current Antigravity 2.0 or Antigravity CLI.
- A disposable Git repository with at least one commit.
- `agy-agents` installed as a plugin.
- Optional: `hevyfs/my-skills` installed in an Antigravity-discovered skill location for the skill-inheritance checks.

## 1. Plugin and agent discovery

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

## 2. Read-only boundary

Ask the parent:

> Use explorer to map this repository without changing anything.

Expected:

- Explorer uses read/search tools only.
- No terminal command or source edit is attempted.
- The result contains paths/symbols/evidence.

Repeat with Reviewer on an existing diff. Expected: review only, no edits.

## 3. Writer lane

Ask:

> Delegate a small bounded documentation edit to fixer. Keep architecture and research with the parent.

Expected:

- Fixer can read, edit, and run bounded validation.
- It stays inside the assigned ownership.
- It reports changed files and validation.

Discard the disposable edit afterward if desired.

## 4. Concurrent writer isolation

Create two independent edits in different files and ask the parent to run them concurrently through two Fixer lanes.

Expected:

- both invocations use `Workspace: branch`;
- each worker receives its own Git worktree/branch;
- no two writers edit the same inherited working directory;
- the parent can inspect both workspaces and reconcile the results.

Do not kill either worker until its work is integrated or intentionally abandoned.

## 5. Sticky semantic lane

Have one Fixer perform an implementation. After it becomes idle, send a dependent correction to the **same lane**.

Expected:

- the parent uses `send_message` to the existing Fixer conversation ID;
- the idle Fixer wakes with prior context retained;
- a replacement Fixer is not spawned merely because this is a second round.

Perform the same pattern for a Reviewer re-checking its own findings.

## 6. Fresh-eyes exception

After a targeted Reviewer re-check, explicitly request:

> Run an independent fresh-eyes review of the final change.

Expected: a **new** Reviewer conversation is spawned. Fresh-eyes independence must not reuse the previous reviewer thread.

## 7. Review and verifier gate

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

## 8. Ambient `my-skills` inheritance

When `my-skills` is installed, open the skills panel or invoke `/ask-matt` from the primary session.

Then assign a lane whose specialist has a narrow model-invoked skill contract (for example, a research lane to Librarian).

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
- ambient `my-skills` remain usable without being vendored into this plugin.
