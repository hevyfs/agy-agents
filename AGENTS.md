# agy-agents repository instructions

This repository is itself an Antigravity plugin. Keep the installable orchestration contract in one place and include it here so development sessions exercise the same rules that users install.

@[agy-agents orchestration](rules/orchestration.md)

When changing agents, routing, or skill compatibility, update `skill-routing.json`, the affected agent definitions, documentation, validator tests, and the orchestration projection together.
