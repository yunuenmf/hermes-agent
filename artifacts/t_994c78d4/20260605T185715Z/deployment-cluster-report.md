# Runtime deployment cluster report — t_994c78d4

Timestamp UTC: 20260605T185715Z
Runtime checkout: /home/engs2272/.hermes/hermes-agent
Runtime branch: deployment/approved-downstream-main-20260605T184745Z
Runtime HEAD: 08b886c2020b5de21e88b403c82d2110bc71d212
Upstream: yunuenmf/main, ahead/behind: 0/0
Workspace: /home/engs2272/.worktrees/t_994c78d4

## Cluster selected
First safe runtime deployment cluster from the drift audit: runtime dirty-state preservation plus live activation proof for the already switched clean deployment branch, stopping before service restarts.

## Dirty-state backup
- Branch/head snapshot: /home/engs2272/.worktrees/t_994c78d4/artifacts/t_994c78d4/20260605T185715Z/runtime-head.txt
- Status snapshot: /home/engs2272/.worktrees/t_994c78d4/artifacts/t_994c78d4/20260605T185715Z/runtime-status.txt
- Unstaged patch: /home/engs2272/.worktrees/t_994c78d4/artifacts/t_994c78d4/20260605T185715Z/runtime-unstaged.patch
- Staged patch: /home/engs2272/.worktrees/t_994c78d4/artifacts/t_994c78d4/20260605T185715Z/runtime-staged.patch
- Untracked manifest: /home/engs2272/.worktrees/t_994c78d4/artifacts/t_994c78d4/20260605T185715Z/runtime-untracked.txt
- Untracked tar placeholder/copy: /home/engs2272/.worktrees/t_994c78d4/artifacts/t_994c78d4/20260605T185715Z/runtime-untracked.tgz.empty or runtime-untracked.tgz

Observed dirty status: clean except the branch header (`## deployment/approved-downstream-main-20260605T184745Z...yunuenmf/main`). Observed untracked manifest: empty. No blanket pull/reset/rebase was performed by this task.

## Runtime tests
Command:

    source venv/bin/activate && pytest -q tests/hermes_cli/test_maintenance_status_lines.py tests/hermes_cli/test_kanban_status_lines.py tests/tools/test_kanban_tools.py tests/hermes_cli/test_kanban_db.py tests/hermes_cli/test_kanban_cli.py tests/plugins/test_kanban_dashboard_plugin.py tests/hermes_cli/test_kanban_boards.py tests/gateway/test_kanban_dispatcher_ownership.py tests/agent/test_memory_capacity_fact_store_fallback.py

Result: 552 passed in 108.50s (0:01:48)
Full output: /home/engs2272/.worktrees/t_994c78d4/artifacts/t_994c78d4/20260605T185715Z/runtime-tests.txt

## Live activation probes before restart
- Import/status-renderer probe: /home/engs2272/.worktrees/t_994c78d4/artifacts/t_994c78d4/20260605T185715Z/import-probes.json
- Import probes passed for hermes_cli.kanban_status_lines, hermes_cli.maintenance_status_lines, tools.kanban_tools, plugins.kanban.dashboard.plugin_api, gateway.run, hermes_cli.main.
- Status renderer probe returned: `Self status: DORMANT — no active task` and `Lineage status: WORKING — working: 2; waiting: 0; blocked: 0; dormant: 0`.
- Non-mutating service status snapshot: /home/engs2272/.worktrees/t_994c78d4/artifacts/t_994c78d4/20260605T185715Z/systemctl-status-before-restart.txt
- Process snapshot: /home/engs2272/.worktrees/t_994c78d4/artifacts/t_994c78d4/20260605T185715Z/processes-before-restart.txt

## Restart impact
The source checkout is at the approved deployment commit, but the long-running gateway/dashboard processes shown in the service/process snapshots were started before this task. Activating in-memory runtime code requires a user-level service restart of:

- hermes-gateway.service
- hermes-gateway-coordinator_hermes_maintenance.service
- hermes-dashboard.service

Impact: interrupts the default gateway, coordinator maintenance gateway, and dashboard web UI; active Kanban-dispatched child processes may be terminated/requeued by service shutdown.

## Rollback handle
Primary rollback is the runtime backup branch created by t_8d44d790:

    backup/runtime-overlay-20260605T184745Z @ f53bfd76b6994e4fbcac948fd3f3dd1f5a37294f

Rollback plan if a restart/deployment fails:

1. cd /home/engs2272/.hermes/hermes-agent
2. git switch backup/runtime-overlay-20260605T184745Z
3. restart the same three user services listed above
4. verify imports/processes; if necessary, use the saved staged/unstaged patches and untracked manifest artifacts from this task and t_8d44d790.

Additional preservation artifacts for this task are under /home/engs2272/.worktrees/t_994c78d4/artifacts/t_994c78d4/20260605T185715Z.

## Deployment gate
Restart/deployment was not executed by this task because it requires explicit service-restart approval and may terminate this worker's parent gateway/session. Safe preparation/probes are complete.
