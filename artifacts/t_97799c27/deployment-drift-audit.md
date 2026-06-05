# Deployment drift audit for approved downstream merges

Task: t_97799c27
Runtime checkout: `/home/engs2272/.hermes/hermes-agent`
Runtime branch/HEAD: `feature/gateway-fragmentation-finalize-reset` @ `22df1f29585156b2ef09549969afd0b7bf490bc1`
Downstream main: `yunuenmf/main` @ `08b886c2020b5de21e88b403c82d2110bc71d212`
Runtime divergence: `6` commits runtime-only, `1250` commits on downstream main not in runtime.
Runtime dirty preservation artifacts were written before any mutation:

- `artifacts/t_97799c27/runtime-status.txt`
- `artifacts/t_97799c27/runtime-unstaged.patch`
- `artifacts/t_97799c27/runtime-staged.patch`
- `artifacts/t_97799c27/runtime-untracked.txt`

No runtime checkout mutation, service restart, or deployment was performed.

## Compact activation matrix

Definitions:
- `Merged`: PR is merged into `yunuenmf/main`.
- `Runtime commit`: merge commit is an ancestor of runtime `HEAD`.
- `Runtime worktree`: files touched by the PR equal current `yunuenmf/main` content in the dirty runtime working tree.
- `Installed import path`: the `hermes` console script imports Python modules from `/home/engs2272/.hermes/hermes-agent` when launched outside a repo; therefore runtime worktree presence is what new CLI/worker processes see.
- `Active gateway/dashboard`: running processes started from the runtime checkout, but already-imported Python modules and built dashboard assets require process restart/relaunch to pick up changed source/assets.

| PR | Addition | Merged | Runtime commit | Runtime worktree vs main | Installed import path | Active gateway/dashboard | Requires restart/deploy | Shadowed by dirty patch |
|---:|---|---|---|---|---|---|---|---|
| #14 | downstream canonical status projection | yes | no | partial: 1/5 touched files equal | partial only | not final; `kanban_db.py`/dashboard API differ from main | yes for final main behavior | yes: `hermes_cli/kanban_db.py`, `plugins/kanban/dashboard/plugin_api.py` |
| #15 | canonical migration safety gate | yes | no | partial: 1/5 equal | partial only | not final | yes | yes: `hermes_cli/kanban_db.py` |
| #17 | auto-append maintenance status lines | yes | no | partial: 3/4 equal | mostly present for new CLI/workers, but `agent/conversation_loop.py` differs | gateway process was started from runtime after local file mtimes, but it is not the merged final source | yes for final main behavior | yes: all 4 touched files are local dirty/untracked overlay |
| #18 | three-layer functionality tracking guard | yes | no | partial: 3/8 equal | partial; `tools/kanban_tools.py` contains three-layer guard markers, but not final main tree | worker processes import dirty runtime overlay, not merged final source | yes for final main behavior | yes: all 8 touched files overlap dirty/staged overlay |
| #19 | compact Kanban agent show output | yes | no | absent by equality: 0/12 equal | not deployed as merged | not active final behavior | yes | yes: multiple dirty overlaps, but none equal final main |
| #21 | project autonomy levels | yes | no | absent by equality: 0/7 equal | not deployed as merged | dashboard/API final behavior not active | yes | yes: `kanban_db.py`, dashboard dist/API dirty overlaps |
| #22 | Task 2 memory recall / dispatcher ownership coverage | yes | no | partial: 2/12 equal | partial; `agent.memory_write_bridge` import exists, but final main source not deployed | `gateway/run.py` differs from main; running gateway is not final merged behavior | yes | yes: many core touched files overlap dirty overlay |
| #24 | clean generic Self/Lineage status downstream | yes | no | absent by equality: 0/6 equal | not deployed: `hermes_cli.kanban_status_lines` import is absent; docs/script absent | not active | yes | partial skill-file dirty overlap only |

Bottom line: none of PRs #14, #15, #17, #18, #19, #21, #22, or #24 are deployed as merge commits in runtime `HEAD`. Several older/local dirty overlays partially implement earlier variants, but only #17/#18/#22 have notable source fragments visible to newly launched CLI/worker imports. PRs #19, #21, and #24 are not active as merged additions; #24's import module is absent from runtime.

## Runtime/import/process evidence

- `command -v hermes` -> `/home/engs2272/.hermes/hermes-agent/venv/bin/hermes`.
- From `/tmp`, the venv imports `run_agent`, `cli`, `gateway.run`, `hermes_cli.kanban_db`, and `tools.kanban_tools` from `/home/engs2272/.hermes/hermes-agent`.
- `hermes --version` reports project `/home/engs2272/.hermes/hermes-agent` and says it is `1675 commits behind`.
- Active user service: `hermes-gateway.service`, running since `Fri 2026-06-05 10:54:21 BST`, command `/home/engs2272/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main gateway run --replace`.
- Dashboard process: `/home/engs2272/.hermes/hermes-agent/venv/bin/hermes dashboard --host 100.114.47.12 --port 9119 --no-open --skip-build --insecure`, running since `Fri 2026-06-05 09:11:24 BST`.
- Runtime imports checked from `/tmp`: `hermes_cli.maintenance_status_lines` exists; `hermes_cli.kanban_status_lines` does not; `agent.memory_write_bridge` exists.

## Verification run

On clean audit worktree at `yunuenmf/main`:

```
source /home/engs2272/.hermes/hermes-agent/venv/bin/activate && pytest -q tests/hermes_cli/test_maintenance_status_lines.py tests/hermes_cli/test_kanban_status_lines.py tests/tools/test_kanban_tools.py tests/hermes_cli/test_kanban_db.py tests/hermes_cli/test_kanban_cli.py tests/plugins/test_kanban_dashboard_plugin.py tests/hermes_cli/test_kanban_boards.py tests/gateway/test_kanban_dispatcher_ownership.py tests/agent/test_memory_capacity_fact_store_fallback.py
```

Result: `552 passed in 109.77s`.

## Safe reconciliation path

The safe path is controlled deployment from `yunuenmf/main`, not cherry-picking. Reasons:

1. Runtime is 1250 commits behind downstream main with 6 runtime-only commits.
2. Runtime checkout is dirty with staged, unstaged, and untracked overlays across core agent, gateway, Kanban DB/API, dashboard dist, skills, package locks, and tests.
3. The approved PRs overlap the dirty runtime overlay heavily, so cherry-picking/rebasing directly onto the dirty checkout risks silently preserving stale local patches over merged main.
4. The installed console script imports from the runtime checkout; changing that checkout is production/runtime deployment and requires restart/relaunch to activate cleanly.

Recommended gated command set, after explicit deployment approval:

```
set -euo pipefail
stamp=$(date +%Y%m%d-%H%M%S)
runtime=/home/engs2272/.hermes/hermes-agent
backup=/home/engs2272/.worktrees/t_97799c27/artifacts/t_97799c27/deploy-backup-$stamp
mkdir -p "$backup"
cd "$runtime"

git status --short --branch | tee "$backup/status.txt"
git rev-parse HEAD | tee "$backup/runtime-head.txt"
git branch --show-current | tee "$backup/runtime-branch.txt"
git diff --binary > "$backup/unstaged.patch"
git diff --cached --binary > "$backup/staged.patch"
git ls-files --others --exclude-standard > "$backup/untracked.txt"
tar -czf "$backup/untracked-files.tgz" -T "$backup/untracked.txt" || true

git switch -c backup/runtime-overlay-$stamp
git add -A
git commit -m "chore: preserve runtime dirty overlay before downstream main deployment"

git fetch yunuenmf --prune
git switch -c deploy/yunuenmf-main-$stamp yunuenmf/main
source "$runtime/venv/bin/activate"
pytest -q tests/hermes_cli/test_maintenance_status_lines.py tests/hermes_cli/test_kanban_status_lines.py tests/tools/test_kanban_tools.py tests/hermes_cli/test_kanban_db.py tests/hermes_cli/test_kanban_cli.py tests/plugins/test_kanban_dashboard_plugin.py tests/hermes_cli/test_kanban_boards.py tests/gateway/test_kanban_dispatcher_ownership.py tests/agent/test_memory_capacity_fact_store_fallback.py
systemctl --user restart hermes-gateway
systemctl --user --no-pager --full status hermes-gateway
hermes --version
cd /tmp && "$runtime/venv/bin/python" - <<'PY'
import importlib.util
for mod in ['hermes_cli.kanban_status_lines','hermes_cli.maintenance_status_lines','agent.memory_write_bridge','gateway.run']:
    spec = importlib.util.find_spec(mod)
    print(mod, spec.origin if spec else None)
PY
```

Dashboard relaunch is also needed for PR #21 dashboard dist/API activation. The currently observed command was:

```
/home/engs2272/.hermes/hermes-agent/venv/bin/hermes dashboard --host 100.114.47.12 --port 9119 --no-open --skip-build --insecure
```

Do not kill/relaunch it without approval because it is a live runtime process.

Rollback plan if deployment fails:

```
set -euo pipefail
runtime=/home/engs2272/.hermes/hermes-agent
cd "$runtime"
systemctl --user stop hermes-gateway
git switch backup/runtime-overlay-<stamp>
systemctl --user start hermes-gateway
systemctl --user --no-pager --full status hermes-gateway
```

If the backup commit was not created, use the saved patches in `deploy-backup-<stamp>` with `git apply --index staged.patch` and `git apply unstaged.patch`, then restore untracked files from `untracked-files.tgz`.

## Three-layer evidence

- Matrix: deployment approval is required before changing runtime source or restarting live gateway/dashboard; no Matrix deployment message was sent by this worker.
- Kanban: this report and the block handoff on task `t_97799c27` record the activation matrix, tests, gated commands, and rollback plan.
- GitHub: issue https://github.com/yunuenmf/hermes-maintenance/issues/37 and merged downstream PRs https://github.com/yunuenmf/hermes-agent/pull/14, /15, /17, /18, /19, /21, /22, /24.
