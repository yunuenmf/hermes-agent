# Hermes Maintenance deterministic Self/Lineage status lines

Task: t_ea3c64dc
Scope: downstream Hermes Maintenance policy and wiring.

## Semantics

Status lines are computed after the agent has finished its tool/reporting action for the turn. They are not pre-action predictions and not model-authored prose.

- `Self status` describes the current profile's own active assigned duties after the just-completed action.
- `Lineage status` describes structural downstream Hermes Maintenance responsibilities/duties after the just-completed action. It is derived from Kanban/project/profile state and owned duties, not from chat-local subagents or children in the current session.

Allowed human-facing live states are exactly:

- `WORKING`: active work is running, immediately spawnable, queued, in progress, or in review.
- `WAITING`: active work exists but is paused on non-human/system conditions such as dependencies, scheduling, CI, worker availability, or automated repair.
- `BLOCKED`: active work exists and is prevented by a concrete required human action.
- `DORMANT`: no active duties remain in that scope.

`done` and `archived` are completion/history states only and are ignored for live status aggregation.

## Structural lineage scan

The deterministic helper lives in `hermes_cli/maintenance_status_lines.py`.

For a profile, lineage membership is computed from active Kanban rows on the resolved board:

1. tasks assigned to the profile;
2. tasks created by the profile;
3. descendants of those tasks through `task_links` parent -> child edges;
4. for `responsible_*` lane owners, tasks whose title/body/assignee/creator/branch/idempotency key contains the lane token, for example `responsible_project_autonomy` matches `project_autonomy`, `project-autonomy`, and `project autonomy`.

The lane-token rule is the downstream bridge for M2 project-autonomy duties that are structurally owned by a responsible lane but assigned to implementer/developer profiles. It fixes the regression where a profile reported `Lineage status: DORMANT` merely because it had no chat-local subagents.

Aggregation precedence is:

1. any working alias -> `WORKING`;
2. otherwise any `blocked` task -> `BLOCKED`;
3. otherwise any waiting alias -> `WAITING`;
4. otherwise -> `DORMANT`.

This means a lineage with both immediately spawnable work and a blocked task reports `WORKING` because actionable downstream work still exists. A lineage with only human-blocked active duties reports `BLOCKED`.

## Auto-append wiring

`agent/conversation_loop.py` now calls `append_status_lines_if_enabled()` after `transform_llm_output` and before `post_llm_call`/session persistence. This is intentionally post-execution: Kanban tool calls that create, complete, or block duties have already mutated board state before the footer is rendered.

The appender:

- activates by default on `HERMES_KANBAN_BOARD=hermes-maintenance` for profiles whose names start with `responsible_`, `coordinator_`, or `developer_`;
- can be forced with `HERMES_MAINTENANCE_STATUS_LINES=1`;
- can be disabled with `HERMES_MAINTENANCE_STATUS_LINES=0`;
- strips any existing model-written `Self status:` / `Lineage status:` lines from the final response and appends deterministic replacements.

## Test coverage

`tests/hermes_cli/test_maintenance_status_lines.py` covers:

- active downstream duties -> `Lineage status: WORKING`;
- non-human waits only -> `Lineage status: WAITING`;
- human blockers only -> `Lineage status: BLOCKED`;
- no active downstream duties -> `Lineage status: DORMANT`;
- post-execution create/complete behavior changes the appended line;
- responsible_project_autonomy regression: existing project-autonomy duties are WORKING even without chat-local children/subagents;
- model-written stale status lines are replaced.

## Deployment note

This is code-path wiring in the agent conversation loop. Existing running Hermes Maintenance profile processes must be restarted/new sessions started before automatic append behavior is active in those processes.
