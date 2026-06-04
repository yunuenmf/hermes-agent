from __future__ import annotations

from pathlib import Path

import yaml

from scripts import render_profile_expertise_directory as renderer


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY_PATH = ROOT / "docs" / "hermes-maintenance" / "profile-expertise-directory.yaml"


def test_profile_expertise_directory_has_required_safe_fields():
    data = yaml.safe_load(DIRECTORY_PATH.read_text())

    assert data["schema_version"] == 1
    assert data["directory_visibility"] == "internal_public_safe"
    assert data["canonical_owner"] == "responsible_project_autonomy"

    profile_ids = {profile["profile_id"] for profile in data["profiles"]}
    assert len(profile_ids) == 20
    assert "default" in profile_ids
    assert "pa_master" in profile_ids
    assert "coordinator_hermes_maintenance" in profile_ids
    assert "researcher_hermes_maintenance" in profile_ids
    assert "responsible_project_autonomy" in profile_ids

    for profile in data["profiles"]:
        assert profile["profile_id"]
        assert profile["tree_path"][0] in {"pa_yunuen", "coordinator_master"}
        assert profile["status"] in {"active", "template", "stale", "retired"}
        assert profile["privacy_level"] in {"public_safe", "internal_only", "restricted"}
        assert "secret" not in profile.get("contact", {}).get("route", "").lower()
        assert "!" not in profile.get("contact", {}).get("route", "")


def test_renderer_outputs_policy_directory_and_tree_sections():
    data = renderer.load_directory(DIRECTORY_PATH)
    rendered = renderer.render_markdown(data)

    assert "# Hermes Maintenance Profile Expertise Directory" in rendered
    assert "## Investigation and enquiry decision rule" in rendered
    assert "## Profile tree" in rendered
    assert "pa_yunuen → coordinator_hermes_maintenance → responsible_project_autonomy" in rendered
    assert "Do not expose private Matrix room IDs" in rendered
