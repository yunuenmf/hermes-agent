"""Deterministic Hermes Maintenance Self/Lineage status-line rendering.

This module is intentionally downstream-policy shaped: it is only auto-applied
for the Hermes Maintenance board/profile fleet.  It keeps the status vocabulary
out of model prose by computing the required two-line footer after a turn's tool
and reporting actions have already mutated Kanban state.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Iterable, Sequence

from hermes_cli import kanban_db as kb

LIVE_STATUSES = frozenset({"WORKING", "WAITING", "BLOCKED", "DORMANT"})
_WORKING_ALIASES = frozenset({"ready", "queue", "running", "in_progress", "review"})
_WAITING_ALIASES = frozenset({"todo", "scheduled", "waiting", "triage"})
_BLOCKED_ALIASES = frozenset({"blocked"})
_INACTIVE_ALIASES = frozenset({"done", "archived"})
_STATUS_LINE_RE = re.compile(r"(?im)^\s*(?:Self|Lineage) status:\s*(?:WORKING|WAITING|BLOCKED|DORMANT)\b.*$")


@dataclass(frozen=True)
class StatusLinePair:
    self_status: str
    self_detail: str
    lineage_status: str
    lineage_detail: str

    def render(self) -> str:
        return (
            f"Self status: {self.self_status} — {self.self_detail}\n"
            f"Lineage status: {self.lineage_status} — {self.lineage_detail}"
        )


def _canonical_profile(raw: str | None = None) -> str:
    value = raw if raw is not None else os.environ.get("HERMES_PROFILE", "")
    return str(value or "").strip()


def _active_tasks(tasks: Iterable[kb.Task]) -> list[kb.Task]:
    return [t for t in tasks if (t.status or "").lower() not in _INACTIVE_ALIASES]


def _aggregate_status(tasks: Sequence[kb.Task]) -> str:
    statuses = {(t.status or "").lower() for t in tasks}
    if statuses & _WORKING_ALIASES:
        return "WORKING"
    if statuses & _BLOCKED_ALIASES:
        return "BLOCKED"
    if statuses & _WAITING_ALIASES:
        return "WAITING"
    return "DORMANT"


def _sample_task(tasks: Sequence[kb.Task], status: str) -> kb.Task | None:
    aliases = {
        "WORKING": _WORKING_ALIASES,
        "WAITING": _WAITING_ALIASES,
        "BLOCKED": _BLOCKED_ALIASES,
    }.get(status, frozenset())
    for task in tasks:
        if (task.status or "").lower() in aliases:
            return task
    return tasks[0] if tasks else None


def _detail(scope: str, status: str, tasks: Sequence[kb.Task], profile: str) -> str:
    if status == "DORMANT":
        if scope == "self":
            return f"no active Hermes Maintenance duties assigned to {profile or 'this profile'} after the last action"
        return "no active downstream Hermes Maintenance duties remain after the last action"

    task = _sample_task(tasks, status)
    suffix = ""
    if task is not None:
        suffix = f" (e.g. {task.id}: {task.title})"
    if status == "WORKING":
        if scope == "self":
            return f"active assigned duty is running or immediately spawnable after the last action{suffix}"
        return f"active downstream duty is running or immediately spawnable after the last action{suffix}"
    if status == "WAITING":
        if scope == "self":
            return f"assigned duty is waiting on non-human/system conditions after the last action{suffix}"
        return f"downstream duty is waiting on non-human/system conditions after the last action{suffix}"
    # BLOCKED is human-only by policy.
    if scope == "self":
        return f"assigned duty requires concrete human action after the last action{suffix}"
    return f"downstream duty requires concrete human action after the last action{suffix}"


def _lane_terms(profile: str) -> set[str]:
    """Terms that identify structural lane ownership for responsible_* profiles."""
    if not profile.startswith("responsible_"):
        return set()
    lane = profile[len("responsible_"):].strip("_")
    if not lane:
        return set()
    terms = {lane, lane.replace("_", "-"), lane.replace("_", " ")}
    parts = [p for p in lane.split("_") if p]
    if len(parts) >= 2:
        tail = "_".join(parts[-2:])
        terms.update({tail, tail.replace("_", "-"), tail.replace("_", " ")})
    return {t.casefold() for t in terms if t}


def _task_text(task: kb.Task) -> str:
    values = [
        task.id,
        task.title,
        task.body or "",
        task.assignee or "",
        task.created_by or "",
        task.branch_name or "",
        task.idempotency_key or "",
    ]
    return "\n".join(values).casefold()


def _descendant_ids(conn, root_ids: set[str]) -> set[str]:
    if not root_ids:
        return set()
    seen = set(root_ids)
    frontier = set(root_ids)
    while frontier:
        placeholders = ",".join("?" for _ in frontier)
        rows = conn.execute(
            f"SELECT child_id FROM task_links WHERE parent_id IN ({placeholders})",
            tuple(frontier),
        ).fetchall()
        children = {str(row["child_id"]) for row in rows if str(row["child_id"]) not in seen}
        seen.update(children)
        frontier = children
    return seen - root_ids


def structural_lineage_tasks(conn, profile: str | None = None) -> list[kb.Task]:
    """Return active tasks that belong to a profile's structural lineage.

    Membership is deterministic and board-state based:
    - tasks assigned to or created by the profile;
    - descendants of those owned tasks through task_links;
    - for responsible_* lane owners, tasks whose title/body/assignee/creator/
      branch/idempotency key carries the lane token (for example
      responsible_project_autonomy owns project-autonomy downstream duties even
      when they are assigned to an implementer profile).
    """
    prof = _canonical_profile(profile)
    all_tasks = kb.list_tasks(conn, include_archived=False)
    active = _active_tasks(all_tasks)
    owned_ids = {
        t.id for t in active
        if (t.assignee or "") == prof or (t.created_by or "") == prof
    }
    descendant_ids = _descendant_ids(conn, owned_ids)
    lane_terms = _lane_terms(prof)

    selected: list[kb.Task] = []
    for task in active:
        if task.id in owned_ids or task.id in descendant_ids:
            selected.append(task)
            continue
        text = _task_text(task)
        if lane_terms and any(term in text for term in lane_terms):
            selected.append(task)
    return selected


def compute_status_line_pair(*, profile: str | None = None, board: str | None = None) -> StatusLinePair:
    prof = _canonical_profile(profile)
    conn = kb.connect(board=board)
    try:
        own_tasks = _active_tasks(kb.list_tasks(conn, assignee=prof, include_archived=False)) if prof else []
        lineage_tasks = structural_lineage_tasks(conn, prof)
    finally:
        conn.close()

    self_status = _aggregate_status(own_tasks)
    lineage_status = _aggregate_status(lineage_tasks)
    return StatusLinePair(
        self_status=self_status,
        self_detail=_detail("self", self_status, own_tasks, prof),
        lineage_status=lineage_status,
        lineage_detail=_detail("lineage", lineage_status, lineage_tasks, prof),
    )


def should_auto_append_status_lines(*, profile: str | None = None, board: str | None = None) -> bool:
    override = os.environ.get("HERMES_MAINTENANCE_STATUS_LINES", "").strip().lower()
    if override in {"0", "false", "off", "no"}:
        return False
    if override in {"1", "true", "on", "yes", "force"}:
        return True
    prof = _canonical_profile(profile)
    active_board = (board or os.environ.get("HERMES_KANBAN_BOARD", "")).strip().lower()
    if active_board != "hermes-maintenance":
        return False
    return prof.startswith(("responsible_", "coordinator_", "developer_"))


def strip_status_lines(text: str) -> str:
    stripped = _STATUS_LINE_RE.sub("", text or "")
    stripped = re.sub(r"\n{3,}", "\n\n", stripped).strip()
    return stripped


def append_status_lines(text: str, pair: StatusLinePair) -> str:
    base = strip_status_lines(text)
    footer = pair.render()
    if not base:
        return footer
    return base.rstrip() + "\n\n" + footer


def append_status_lines_if_enabled(text: str, *, profile: str | None = None, board: str | None = None) -> str:
    if not should_auto_append_status_lines(profile=profile, board=board):
        return text
    pair = compute_status_line_pair(profile=profile, board=board)
    return append_status_lines(text, pair)
