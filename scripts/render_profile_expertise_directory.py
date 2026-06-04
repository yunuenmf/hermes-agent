#!/usr/bin/env python3
"""Render the Hermes Maintenance profile expertise directory.

The source YAML is intentionally public-safe: it names profiles, expertise,
ownership, and abstract contact routes, but it must not contain private Matrix
room IDs, tokens, invite links, or credentials.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

DEFAULT_SOURCE = Path("docs/hermes-maintenance/profile-expertise-directory.yaml")


def load_directory(path: Path) -> dict[str, Any]:
    """Load and lightly validate a profile expertise directory YAML file."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a YAML mapping")
    profiles = data.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ValueError("directory must contain a non-empty profiles list")
    return data


def _join(values: list[Any]) -> str:
    return ", ".join(str(v) for v in values) if values else "—"


def _tree_path(profile: dict[str, Any]) -> str:
    return " → ".join(str(part) for part in profile.get("tree_path", []))


def render_markdown(data: dict[str, Any]) -> str:
    """Render a Markdown directory from the machine-readable YAML."""
    lines: list[str] = []
    lines.append("# Hermes Maintenance Profile Expertise Directory")
    lines.append("")
    lines.append("> Generated from `docs/hermes-maintenance/profile-expertise-directory.yaml`. Keep the YAML canonical and regenerate this view after edits.")
    lines.append("")
    lines.append(f"- Schema version: {data.get('schema_version')}")
    lines.append(f"- Visibility: {data.get('directory_visibility')}")
    lines.append(f"- Canonical owner: {data.get('canonical_owner')}")
    lines.append(f"- Update cadence: {data.get('update_cadence')}")
    lines.append("")
    lines.append("## Investigation and enquiry decision rule")
    lines.append("")
    decision_rule = data.get("decision_rule", {})
    labels = {
        "proceed_locally": "Proceed locally when",
        "research_prior_art": "Research internet/prior art when",
        "consult_profile": "Consult another profile when",
        "ask_yunuen": "Ask Yunuen when",
    }
    for key, heading in labels.items():
        lines.append(f"### {heading}")
        for item in decision_rule.get(key, []):
            lines.append(f"- {item}")
        lines.append("")
    lines.append("## Privacy rules")
    lines.append("")
    for item in data.get("privacy_rules", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Profile tree")
    lines.append("")
    for profile in data["profiles"]:
        lines.append(f"- {_tree_path(profile)}")
    lines.append("")
    lines.append("## Directory")
    lines.append("")
    lines.append("| Profile | Type | Project | Status | Expertise | Consult on | Contact |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for profile in data["profiles"]:
        contact = profile.get("contact", {})
        lines.append(
            "| {profile_id} | {profile_type} | {project} | {status} | {expertise} | {consult_on} | {contact} |".format(
                profile_id=profile.get("profile_id", ""),
                profile_type=profile.get("profile_type", ""),
                project=profile.get("project", ""),
                status=profile.get("status", ""),
                expertise=_join(profile.get("expertise_tags", [])),
                consult_on=_join(profile.get("consult_on", [])),
                contact=contact.get("route", ""),
            )
        )
    lines.append("")
    lines.append("## Maintenance workflow")
    lines.append("")
    lines.append("1. On profile creation, `hermes profile create --description` or `hermes profile describe` seeds `profile.yaml`; the owning coordinator/responsible adds a public-safe directory entry before assigning durable work.")
    lines.append("2. On profile rename, project move, or retirement, update the YAML in the same PR/commit as the operational change.")
    lines.append("3. During monthly Hermes Maintenance review, the canonical owner checks `hermes profile list`, refreshes `last_verified`, and marks missing or inactive profiles as `stale` or `retired` rather than deleting history.")
    lines.append("4. Profiles discover expertise by reading this rendered doc, loading the YAML, or asking the coordinator for the best-fit owner. Consultation uses direct profile commands or validated internal rooms; Kanban remains for durable work, not chat.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=Path("docs/hermes-maintenance/profile-expertise-directory.md"))
    args = parser.parse_args()

    data = load_directory(args.source)
    rendered = render_markdown(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(f"rendered {args.output} from {args.source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
