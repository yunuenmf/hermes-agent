from hermes_cli import kanban_db as kb
from hermes_cli.maintenance_status_lines import (
    StatusLinePair,
    append_status_lines,
    append_status_lines_if_enabled,
    compute_status_line_pair,
)


def _init_board(tmp_path, monkeypatch):
    db_path = tmp_path / "kanban.db"
    monkeypatch.setenv("HERMES_KANBAN_DB", str(db_path))
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "hermes-maintenance")
    kb.init_db()
    return kb.connect()


def _task(conn, *, title="duty", assignee="developer", status="ready", body=None, created_by=None, parents=()):
    tid = kb.create_task(
        conn,
        title=title,
        body=body,
        assignee=assignee,
        created_by=created_by,
        parents=parents,
        initial_status="running",
    )
    conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, tid))
    conn.commit()
    return tid


def test_lineage_status_working_for_active_downstream_duties(tmp_path, monkeypatch):
    conn = _init_board(tmp_path, monkeypatch)
    try:
        tid = _task(
            conn,
            title="implement project-autonomy duty model",
            assignee="developer_hermes_maintenance",
            status="ready",
        )
    finally:
        conn.close()

    pair = compute_status_line_pair(profile="responsible_project_autonomy")

    assert pair.lineage_status == "WORKING"
    assert tid in pair.lineage_detail


def test_lineage_status_waiting_for_non_human_waits_only(tmp_path, monkeypatch):
    conn = _init_board(tmp_path, monkeypatch)
    try:
        _task(
            conn,
            title="project-autonomy dependency wait",
            assignee="developer_hermes_maintenance",
            status="scheduled",
        )
    finally:
        conn.close()

    pair = compute_status_line_pair(profile="responsible_project_autonomy")

    assert pair.lineage_status == "WAITING"
    assert "non-human/system" in pair.lineage_detail


def test_lineage_status_blocked_for_human_blockers_only(tmp_path, monkeypatch):
    conn = _init_board(tmp_path, monkeypatch)
    try:
        _task(
            conn,
            title="project-autonomy review choice needed",
            assignee="developer_hermes_maintenance",
            status="blocked",
        )
    finally:
        conn.close()

    pair = compute_status_line_pair(profile="responsible_project_autonomy")

    assert pair.lineage_status == "BLOCKED"
    assert "human action" in pair.lineage_detail


def test_lineage_status_dormant_when_no_active_downstream_duties(tmp_path, monkeypatch):
    conn = _init_board(tmp_path, monkeypatch)
    try:
        _task(
            conn,
            title="project-autonomy finished duty",
            assignee="developer_hermes_maintenance",
            status="done",
        )
    finally:
        conn.close()

    pair = compute_status_line_pair(profile="responsible_project_autonomy")

    assert pair.lineage_status == "DORMANT"


def test_post_execution_create_and_complete_change_appended_line(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_PROFILE", "responsible_project_autonomy")
    conn = _init_board(tmp_path, monkeypatch)
    try:
        before = append_status_lines_if_enabled("report complete")
        tid = _task(
            conn,
            title="project-autonomy downstream implementation",
            assignee="developer_hermes_maintenance",
            status="ready",
        )
        after_create = append_status_lines_if_enabled("created downstream duty")
        conn.execute("UPDATE tasks SET status = 'done' WHERE id = ?", (tid,))
        conn.commit()
        after_done = append_status_lines_if_enabled("completed downstream duty")
    finally:
        conn.close()

    assert "Lineage status: DORMANT" in before
    assert "Lineage status: WORKING" in after_create
    assert "Lineage status: DORMANT" in after_done


def test_regression_lineage_not_chat_local_descendants(tmp_path, monkeypatch):
    """Existing project-autonomy duties make lineage WORKING without subagents/children."""
    conn = _init_board(tmp_path, monkeypatch)
    try:
        _task(
            conn,
            title="project-autonomy dashboard rollout",
            body="Owned by the project-autonomy lane; no chat-local child exists.",
            assignee="developer_hermes_maintenance",
            status="running",
        )
    finally:
        conn.close()

    pair = compute_status_line_pair(profile="responsible_project_autonomy")

    assert pair.lineage_status == "WORKING"


def test_append_replaces_model_written_status_lines():
    original = (
        "Work is queued.\n\n"
        "Self status: WAITING — stale handwritten line\n"
        "Lineage status: DORMANT — no structural descendants currently active in this session"
    )
    rendered = append_status_lines(
        original,
        pair=StatusLinePair(
            self_status="WORKING",
            self_detail="deterministic",
            lineage_status="WORKING",
            lineage_detail="deterministic",
        ),
    )

    assert "stale handwritten" not in rendered
    assert "chat-local" not in rendered
    assert rendered.endswith("Lineage status: WORKING — deterministic")
