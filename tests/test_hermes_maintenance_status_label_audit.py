from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "hermes_maintenance_status_label_audit.py"
spec = importlib.util.spec_from_file_location("status_label_audit", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
status_label_audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(status_label_audit)


def test_audit_flags_legacy_role_specific_status_label(tmp_path: Path) -> None:
    policy = tmp_path / "SOUL.md"
    policy.write_text("Coordinator status: WORKING — old label\n")

    findings = status_label_audit.audit_path(policy)

    assert findings == [(1, "Coordinator status", "Coordinator status: WORKING — old label")]


def test_audit_accepts_canonical_self_and_lineage_status_labels(tmp_path: Path) -> None:
    policy = tmp_path / "SOUL.md"
    policy.write_text(
        "Self status: WORKING — current action\n"
        "Lineage status: DORMANT — no structural descendants\n"
    )

    assert status_label_audit.audit_path(policy) == []


def test_iter_audit_files_skips_runtime_history_files(tmp_path: Path) -> None:
    (tmp_path / "state.db").write_text("Coordinator status: WORKING — old history\n")
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "gateway.log").write_text("Coordinator status: WORKING — old log\n")
    policy = tmp_path / "SOUL.md"
    policy.write_text("Self status: DORMANT — template\n")

    files = list(status_label_audit.iter_audit_files([tmp_path]))

    assert policy in files
    assert tmp_path / "state.db" not in files
    assert tmp_path / "logs" / "gateway.log" not in files
