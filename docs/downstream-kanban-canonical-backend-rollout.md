# Downstream-only Kanban canonical backend rollout

Scope: Yunuen explicitly chose a downstream-only/local redesign for the Hermes Maintenance runtime. Do not open or route an upstream PR for this backend redesign without a new explicit review.

## Canonical backend target

Persist and expose canonical live/user statuses as first-class semantics:

- `working` — active work is underway or immediately spawnable.
- `waiting` — an active task/dependency waits on non-human/system action, including unfinished parents and schedules.
- `blocked` — human action is required; `blocked` is human-only.
- `dormant` — no active actionable assignment exists, such as unspecced triage with no active specifier.
- `done` — completion history, not profile availability.

Legacy values (`todo`, `ready`, `running`, `review`, `triage`, `scheduled`) are compatibility/storage aliases during rollout only. They must not be treated as canonical user-facing truth.

## Implementation sequence

1. Schema/runtime representation
   - Add a schema-versioned canonical task status field or new task state table for `working|waiting|blocked|dormant|done`.
   - Add a runtime/dispatch representation for spawnability, claim state, schedules, review-pending, and triage-needed.
   - Preserve `done` as terminal history; do not use it as a live availability state.

2. Compatibility adapter
   - Keep legacy dispatcher/storage aliases behind an explicit adapter boundary only.
   - Map old dispatcher reads from canonical state + runtime state, for example `working+spawnable -> ready`, `working+running -> running`, `waiting+parents_unfinished -> todo`, `waiting+scheduled -> scheduled`, `dormant+triage_needed -> triage`.
   - Reject new user/API writes of legacy aliases once dry-run backfill proves safe.

3. CLI/API/dashboard user-facing rendering
   - Render `Self status:` and `Lineage status:` with canonical vocabulary where profile status is reported.
   - Show canonical task status first in CLI/API/dashboard. If legacy storage is still present during migration, surface it only as explicit compatibility metadata.
   - Make list filters/counts/columns canonical, with legacy filters accepted only under a clearly named compatibility flag or endpoint.

4. Migration/backfill dry-run and rollback artifact
   - Before mutating any live Kanban DB, produce a deterministic backup path, a dry-run report of each row's old status, proposed canonical status, proposed runtime state, reason, and blocker-human audit outcome.
   - Produce rollback/export tooling that can materialize legacy statuses from canonical + runtime state for old runtimes.
   - Do not run old and new dispatchers against the same live DB concurrently.

5. Acceptance fixtures
   - Parent-gated child with unfinished or blocked parent reports canonical backend/user status `waiting`, not `todo`.
   - Completing/archiving all parents promotes a spawnable child to canonical `working`.
   - A blocked parent does not make descendants `blocked`; descendants remain `waiting` unless they themselves need human action.
   - Non-human blocker migration becomes `waiting`; human blockers remain `blocked`.

## First safe implementation slice in this branch

This branch implements only a non-invasive compatibility/projection slice:

- `hermes_cli.kanban_db.canonical_live_status()` maps legacy storage statuses to canonical downstream live statuses.
- `hermes_cli.kanban_db.canonical_live_status_for_task()` additionally treats any child with unfinished parents as canonical `waiting`, even if a legacy/racy row says `ready`.
- CLI JSON task payloads include `canonical_status`, and plain `kanban show` prints canonical status first with legacy storage status marked as compatibility metadata.
- Dashboard task dictionaries include `canonical_status` for frontend migration.
- Tests cover the observed parent-gated child regression without mutating live DB schema or live board data.

This is intentionally not the full backend redesign. It creates the adapter seam and acceptance fixture needed before the backup/dry-run/backfill slice.


## Backup / dry-run / rollback gate slice

Before any live Kanban DB mutation for canonical status backfill, run the downstream-only safety gate below. These commands are read-only with respect to task rows and schema: they intentionally skip the normal Kanban CLI auto-init/migration path so backup and dry-run evidence can be produced before touching a live board.

### All-project backup baseline

The migration deployment must protect **all Kanban projects/boards**, not only Hermes Maintenance. Take a fleet-wide backup first:

```bash
hermes kanban canonical-backup --all-boards --output-dir <artifact-dir>/all-project-backups
```

This writes one subdirectory per discovered board, for example `<artifact-dir>/all-project-backups/hermes-maintenance/kanban-<UTC timestamp>.sqlite3` plus metadata. Boards that have only metadata and no existing `kanban.db` are reported as skipped and are not auto-created. Use `--include-archived` only when the deployment plan explicitly covers archived boards too.

### Per-project evidence loop

For every board that will receive the canonical status deployment, run this loop and keep the artifacts together:

1. Create a deterministic SQLite backup artifact for that board:

   ```bash
   hermes kanban --board <board-slug> canonical-backup --output-dir <artifact-dir>/<board-slug>
   ```

   The command writes `kanban-<UTC timestamp>.sqlite3` plus `kanban-<UTC timestamp>.metadata.json`. The metadata includes the board slug, source DB path, backup path, SHA-256 checksum, artifact size, SQLite/schema metadata, table counts, task status distribution, and restore instructions. Automation/tests may pass `--timestamp YYYYMMDDTHHMMSSZ` for deterministic artifact names.

2. Produce a no-mutation canonical status dry-run report:

   ```bash
   hermes kanban --board <board-slug> canonical-dry-run --output <artifact-dir>/<board-slug>/canonical-dry-run.json
   ```

   The report lists every task row with its legacy storage status, proposed canonical status, proposed compatibility runtime state, reason, and `would_change` flag. It separately summarizes legacy storage aliases, parent-gated descendants that must canonicalize to `waiting`, rows that would change in a future live migration, and `blocked` rows requiring human-only blocker audit. A blocked parent does not make descendants blocked; descendants remain canonical `waiting` unless the descendant itself needs human action.

3. Prove rollback mechanically before live mutation:

   ```bash
   hermes kanban canonical-rollback-proof <artifact-dir>/<board-slug>/kanban-<UTC timestamp>.sqlite3 --temp-dir <artifact-dir>/<board-slug>/restore-proof
   ```

   The proof restores the backup into a temporary DB and verifies SHA-256 equality, `PRAGMA integrity_check`, table counts, task status distribution, and schema checksum. The command exits non-zero if any rollback evidence fails.

4. Restore procedure if rollback is required:

   - Stop all Kanban dispatchers/gateways that might write to the target DB.
   - Verify the backup file checksum matches `backup_sha256` in the metadata JSON.
   - Preserve an emergency copy of the current target `kanban.db`.
   - Copy the selected `kanban-<UTC timestamp>.sqlite3` over the target board's `kanban.db`.
   - Run SQLite `PRAGMA integrity_check` (or rerun `canonical-rollback-proof` against the artifact) before restarting the dispatcher/gateway.

### Deployment everywhere checklist

Apply the deployment consistently everywhere the Kanban board is used:

1. Enumerate boards with `hermes kanban boards` and record the deployment set.
2. Run the all-project backup baseline.
3. For each board in the deployment set, run the per-project evidence loop above.
4. Review every board's dry-run report; `blocked` rows must remain or become `blocked` only when they require human intervention, otherwise they are migration candidates for `waiting`.
5. Deploy the code/config/runtime update everywhere that reads or writes Kanban state: CLI, dispatcher/gateway workers, dashboard/API, profile status scripts, and any project-specific overlays.
6. Restart only the affected services after artifacts are verified, then run read-only smoke checks on every board.
7. Do not run a live schema/data backfill until the all-project backup, per-project dry-runs, and rollback proofs are attached to the review.

### Removing now-irrelevant migration scaffolding

Use this step-by-step cleanup guideline after deployment proves stable:

1. **Wait for proof, not optimism.** Keep backups, dry-run commands, compatibility adapters, and rollback docs until every board in the deployment set has passed smoke checks and no rollback has been needed for the agreed observation window.
2. **Classify each artifact.** For each backup, report, compatibility flag, legacy alias path, task, doc section, and temporary script, mark one of: `retain-for-rollback`, `retain-for-audit`, `replace-with-permanent-doc`, or `remove`.
3. **Never delete the only rollback path.** A backup becomes unnecessary only after a newer verified all-project backup supersedes it or after Yunuen/project policy says rollback to the old state is no longer needed.
4. **Remove in dependency order.** First remove stale docs/checklists, then unused temporary scripts, then compatibility-only CLI flags/help, then legacy adapter code/tests once no deployed writer emits legacy aliases.
5. **Preserve audit records.** Kanban comments, PR links, and concise deployment evidence stay durable even when local temporary artifacts are removed.
6. **Verify after each removal batch.** Run the status/CLI/dashboard smoke checks and targeted tests again; if a removal breaks a board, restore from the relevant artifact and reclassify that item as `retain-for-rollback`.
7. **Do not treat cleanup as a blocker.** Cleanup is `waiting` on automated proof or `working` when being executed. It is `blocked` only if a human decision is required to delete or retain a specific artifact.

This slice still does not perform a live canonical-status schema backfill. It supplies the reviewed all-project backup, dry-run, and rollback proof gate required before a later live migration/backfill can be considered.
