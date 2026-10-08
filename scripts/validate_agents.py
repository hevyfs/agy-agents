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
EXECUTING_ROLES = {"designer", "fixer", "verifier"}
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


def declared_role_skills(body: str) -> set[str] | None:
    match = re.search(
        r"\\*\\*Skill contract:\\*\\* allowed model-invoked skills = ([^\\n]+)",
        body,
    )
    if not match:
        return None
    declaration = match.group(1)
    if declaration.startswith("none"):
        return set()
    return set(re.findall(r"`([a-z0-9-]+)`", declaration))


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

    routes: dict[str, str] = {}
    role_skills: dict[str, list[str]] = {}
    if manifest:
        if manifest.get("platform") != "google-antigravity":
            errors.append("skill-routing.json: platform must be google-antigravity")
        if manifest.get("skill_contract_enforcement") != "prompt-guidance-only-until-runtime-verified":
            errors.append("skill-routing.json: skill contracts must remain prompt guidance until runtime verification exists")
        if manifest.get("runtime_validation_status") != "unverified-in-antigravity-runtime":
            errors.append("skill-routing.json: runtime status must remain unverified until evidence is recorded")

        raw_routes = manifest.get("workflow_lane_agents")
        if not isinstance(raw_routes, dict) or not raw_routes:
            errors.append("skill-routing.json: workflow_lane_agents must be a non-empty object")
        else:
            routes = raw_routes
            unknown_roles = set(routes.values()) - REQUIRED_AGENTS
            if unknown_roles:
                errors.append(f"skill-routing.json: routes target unknown roles: {sorted(unknown_roles)}")

        raw_role_skills = manifest.get("role_model_invoked_skills")
        if not isinstance(raw_role_skills, dict):
            errors.append("skill-routing.json: role_model_invoked_skills must be an object")
        else:
            role_skills = raw_role_skills
            if set(role_skills) != REQUIRED_AGENTS:
                errors.append("skill-routing.json: role skill contracts must cover exactly the eight agents")
            for role, skills in role_skills.items():
                if not isinstance(skills, list) or not all(isinstance(skill, str) for skill in skills):
                    errors.append(f"skill-routing.json: invalid skill list for role {role}")

        user_skills = set(manifest.get("user_invoked_skills", []))
        missing = REQUIRED_USER_SKILLS - user_skills
        if missing:
            errors.append(f"skill-routing.json: missing user-invoked skills: {sorted(missing)}")

        allowed_model_skills = {
            skill for skills in role_skills.values() if isinstance(skills, list) for skill in skills
        }
        overlap = allowed_model_skills & user_skills
        if overlap:
            errors.append(f"skill-routing.json: user-invoked skills cannot be worker-allowed: {sorted(overlap)}")

        requirements = manifest.get("lane_requirements", {})
        if requirements.get("security-audit.refutation", {}).get("access") != "read-only":
            errors.append("skill-routing.json: security-audit.refutation must remain read-only")

        implement_spec = requirements.get("implement-spec.implementer", {})
        expected_implement_spec = {
            "workspace": "branch-always",
            "base": "integration-branch",
            "scheduling": "dependency-frontier",
            "integration": "dedicated-merger-subagent",
        }
        for key, value in expected_implement_spec.items():
            if implement_spec.get(key) != value:
                errors.append(f"skill-routing.json: implement-spec.implementer {key} must be {value}")

        for lane in ("code-review.standards", "code-review.spec"):
            if requirements.get(lane, {}).get("review_input") != "immutable-parent-materialized-snapshot":
                errors.append(f"skill-routing.json: {lane} must consume an immutable parent snapshot")

    agents_dir = root / "agents"
    found = {p.stem for p in agents_dir.glob("*.md")} if agents_dir.exists() else set()
    if found != REQUIRED_AGENTS:
        errors.append(
            f"agents/: expected {sorted(REQUIRED_AGENTS)}, found {sorted(found)}"
        )

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

        if role in EXECUTING_ROLES and fm.get("commandExecutionPolicy") != "sandbox":
            errors.append(f"{path}: executing role must set commandExecutionPolicy: sandbox")

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

        declared = declared_role_skills(body)
        if declared is None:
            errors.append(f"{path}: missing explicit model-invoked skill contract")
        else:
            expected = set(role_skills.get(role, []))
            if declared != expected:
                errors.append(
                    f"{path}: declared model-invoked skills {sorted(declared)} do not match manifest {sorted(expected)}"
                )

        if role == "reviewer":
            for phrase in ["immutable review snapshot", "complete diff", "exact candidate head SHA", "Do not run Git yourself"]:
                if phrase not in body:
                    errors.append(f"{path}: missing immutable-review requirement: {phrase}")

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
            "active workflow's stricter lifecycle rules always take precedence",
            "one worktree per ticket implementer",
            "integration branch",
            "dedicated merger subagent",
            "dependency graph",
            "ready **frontier**",
            "immutable review snapshot",
            "git diff <fixed-point>...<head-sha>",
            "same immutable review snapshot",
            "prompt guidance, not a demonstrated runtime-enforced skill allowlist",
            "agy-agents internal routing-intent identifiers",
        ]
        for phrase in required_phrases:
            if phrase not in rule_body:
                errors.append(f"rules/orchestration.md: missing invariant: {phrase}")

        for lane, role in routes.items():
            if f"`{lane}` → `{role}`" not in rule_body:
                errors.append(f"rules/orchestration.md: missing manifest route {lane} -> {role}")

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
            "UNVERIFIED INITIAL CONFIGURATION",
            "/setup-matt-pocock-skills",
            "/ask-matt",
            "<workspace>/.agents/skills/",
            "~/.gemini/config/skills/",
            "~/.gemini/antigravity-cli/skills/",
            "Static validation checks declarations and internal consistency",
        ]:
            if token not in text:
                errors.append(f"README.md: missing required compatibility/install text: {token}")

    runtime_status = root / "docs" / "runtime-validation.md"
    if not runtime_status.exists():
        errors.append("docs/runtime-validation.md: missing")
    else:
        text = runtime_status.read_text(encoding="utf-8")
        if "Status: NOT RUN" not in text:
            errors.append("docs/runtime-validation.md: must remain NOT RUN until runtime evidence is recorded")

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
