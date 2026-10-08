#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED_AGENTS = {
    "explorer",
    "librarian",
    "oracle",
    "designer",
    "fixer",
    "observer",
    "reviewer",
    "verifier",
}

READ_ONLY_ROLES = {"explorer", "librarian", "oracle", "observer", "reviewer"}
WRITE_ROLES = {"designer", "fixer"}
PRO_ROLES = {"oracle", "reviewer", "verifier"}

KNOWN_TOOLS = {
    "view_file",
    "write_to_file",
    "replace_file_content",
    "multi_replace_file_content",
    "list_dir",
    "find_by_name",
    "grep_search",
    "search_web",
    "read_url_content",
    "run_command",
    "manage_task",
    "ask_question",
    "generate_image",
    "invoke_subagent",
    "define_subagent",
    "send_message",
    "manage_subagents",
}

MUTATING_TOOLS = {
    "write_to_file",
    "replace_file_content",
    "multi_replace_file_content",
    "run_command",
}

EXPECTED_LANES = {
    "research.background_external_reading": "librarian",
    "implement.bounded_implementation": "fixer",
    "implement-spec.implementer": "fixer",
    "diagnosing-bugs.consequential_decision": "oracle",
    "prototype.ui_or_interaction": "designer",
    "visual-evidence.inspect": "observer",
    "code-review.standards": "reviewer",
    "code-review.spec": "reviewer",
    "verification.final": "verifier",
    "security-audit.refutation": "reviewer",
}

EXPECTED_ROLE_SKILLS = {
    "explorer": [],
    "librarian": ["research"],
    "oracle": [
        "diagnosing-bugs",
        "codebase-design",
        "domain-modeling",
        "performance-optimization",
        "deprecation-and-migration",
    ],
    "designer": ["prototype"],
    "fixer": ["verification-planning", "tdd"],
    "observer": [],
    "reviewer": [],
    "verifier": [],
}

REQUIRED_USER_SKILLS = {
    "ask-matt",
    "to-spec",
    "to-tickets",
    "implement",
    "implement-spec",
    "pr-audit",
    "github-resolution",
    "release",
}

def parse_scalar(value: str):
    value = value.strip()
    if value in {"true", "false"}:
        return value == "true"
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value

def parse_frontmatter(text: str, path: Path) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError(f"{path}: unterminated YAML frontmatter")
    raw = text[4:end]
    body = text[end + 5 :]
    data: dict[str, object] = {}
    current_list: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if current_list is None:
                raise ValueError(f"{path}: list item without key")
            cast = data[current_list]
            assert isinstance(cast, list)
            cast.append(parse_scalar(line[4:]))
            continue
        if ":" not in line:
            raise ValueError(f"{path}: invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            data[key] = []
            current_list = key
        else:
            data[key] = parse_scalar(value)
            current_list = None
    return data, body

def load_manifest(root: Path) -> dict:
    return json.loads((root / "skill-routing.json").read_text(encoding="utf-8"))

def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []

    plugin_path = root / "plugin.json"
    if not plugin_path.exists():
        errors.append("plugin.json: missing")
    else:
        try:
            plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
            if plugin.get("name") != "agy-agents":
                errors.append("plugin.json: name must be agy-agents")
            if plugin.get("$schema") != "https://antigravity.google/schemas/v1/plugin.json":
                errors.append("plugin.json: missing official schema URL")
            extra = set(plugin) - {"$schema", "name", "description"}
            if extra:
                errors.append(f"plugin.json: unsupported keys: {sorted(extra)}")
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"plugin.json: invalid JSON: {exc}")

    manifest_path = root / "skill-routing.json"
    if not manifest_path.exists():
        errors.append("skill-routing.json: missing")
        manifest = {}
    else:
        try:
            manifest = load_manifest(root)
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"skill-routing.json: invalid JSON: {exc}")
            manifest = {}

    if manifest:
        if manifest.get("platform") != "google-antigravity":
            errors.append("skill-routing.json: platform must be google-antigravity")
        if manifest.get("workflow_lane_agents") != EXPECTED_LANES:
            errors.append("skill-routing.json: workflow lane routing drifted")
        if manifest.get("role_model_invoked_skills") != EXPECTED_ROLE_SKILLS:
            errors.append("skill-routing.json: role skill contracts drifted")
        user_skills = set(manifest.get("user_invoked_skills", []))
        missing = REQUIRED_USER_SKILLS - user_skills
        if missing:
            errors.append(f"skill-routing.json: missing user-invoked skills: {sorted(missing)}")
        if manifest.get("lane_requirements", {}).get(
            "security-audit.refutation", {}
        ).get("access") != "read-only":
            errors.append("skill-routing.json: security-audit.refutation must remain read-only")

    agents_dir = root / "agents"
    found = {p.stem for p in agents_dir.glob("*.md")} if agents_dir.exists() else set()
    if found != REQUIRED_AGENTS:
        errors.append(
            f"agents/: expected {sorted(REQUIRED_AGENTS)}, found {sorted(found)}"
        )

    role_skills = manifest.get("role_model_invoked_skills", {}) if manifest else {}
    for role in sorted(REQUIRED_AGENTS & found):
        path = agents_dir / f"{role}.md"
        text = path.read_text(encoding="utf-8")
        try:
            fm, body = parse_frontmatter(text, path)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        if fm.get("name") != role:
            errors.append(f"{path}: frontmatter name must be {role}")
        if fm.get("subagent") is not True:
            errors.append(f"{path}: subagent must be true")
        if fm.get("mainAgent") is not False:
            errors.append(f"{path}: mainAgent must be false")
        if fm.get("model") not in {"inherit", "flash", "pro"}:
            errors.append(f"{path}: model must be inherit, flash, or pro")
        if role in PRO_ROLES and fm.get("model") != "pro":
            errors.append(f"{path}: high-risk role must use model: pro")

        tools = fm.get("tools")
        if not isinstance(tools, list) or not tools:
            errors.append(f"{path}: tools must be a non-empty explicit allowlist")
            tools = []
        unknown = set(tools) - KNOWN_TOOLS
        if unknown:
            errors.append(f"{path}: unknown tools: {sorted(unknown)}")

        if role in READ_ONLY_ROLES:
            bad = set(tools) & MUTATING_TOOLS
            if bad:
                errors.append(f"{path}: read-only role exposes mutating tools: {sorted(bad)}")
            if fm.get("commandExecutionPolicy") != "off":
                errors.append(f"{path}: read-only role must set commandExecutionPolicy: off")

        if role in WRITE_ROLES:
            required = {
                "write_to_file",
                "replace_file_content",
                "multi_replace_file_content",
                "run_command",
            }
            missing_tools = required - set(tools)
            if missing_tools:
                errors.append(f"{path}: writer missing tools: {sorted(missing_tools)}")

        if role == "verifier":
            if "run_command" not in tools:
                errors.append(f"{path}: verifier requires run_command")
            direct_edits = {
                "write_to_file",
                "replace_file_content",
                "multi_replace_file_content",
            } & set(tools)
            if direct_edits:
                errors.append(f"{path}: verifier must not expose direct edit tools")

        if "Never start a user-invoked workflow" not in body:
            errors.append(f"{path}: missing user-invoked workflow boundary")
        allowed = role_skills.get(role, [])
        if allowed:
            for skill in allowed:
                if f"`{skill}`" not in body:
                    errors.append(f"{path}: missing allowed skill contract for {skill}")
        elif "allowed model-invoked skills = none" not in body:
            errors.append(f"{path}: must declare no model-invoked skills")

    rule_path = root / "rules" / "orchestration.md"
    if not rule_path.exists():
        errors.append("rules/orchestration.md: missing")
    else:
        rule_text = rule_path.read_text(encoding="utf-8")
        try:
            rule_fm, rule_body = parse_frontmatter(rule_text, rule_path)
            if rule_fm.get("trigger") != "always_on":
                errors.append("rules/orchestration.md: trigger must be always_on")
        except ValueError as exc:
            errors.append(str(exc))
            rule_body = ""

        required_phrases = [
            "same lane + dependent follow-up",
            "reuse the existing subagent",
            "fresh-eyes",
            "send_message",
            "Workspace: branch",
            "Never run concurrent writers against the same inherited working tree",
            "reviewer",
            "verifier",
            "agy-agents internal routing-intent identifiers",
        ]
        for phrase in required_phrases:
            if phrase not in rule_body:
                errors.append(f"rules/orchestration.md: missing invariant: {phrase}")

        for lane, role in EXPECTED_LANES.items():
            if f"`{lane}` → `{role}`" not in rule_body:
                errors.append(f"rules/orchestration.md: missing route {lane} -> {role}")

    agents_md = root / "AGENTS.md"
    if not agents_md.exists():
        errors.append("AGENTS.md: missing")
    else:
        text = agents_md.read_text(encoding="utf-8")
        if "@[agy-agents orchestration](rules/orchestration.md)" not in text:
            errors.append("AGENTS.md: must include installable orchestration rule")

    readme = root / "README.md"
    if not readme.exists():
        errors.append("README.md: missing")
    else:
        text = readme.read_text(encoding="utf-8")
        for token in [
            "agy plugin install",
            "Antigravity 2.0",
            "skill-routing.json",
            "my-skills@d5628a28514a06d0b587cf838a983321eff1557a",
            "codex-agents@0eb3b8190e19a55ac4a71620c4e212325940c429",
        ]:
            if token not in text:
                errors.append(f"README.md: missing required compatibility/install text: {token}")

    return errors

def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    errors = validate_repository(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("agy-agents validation passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
