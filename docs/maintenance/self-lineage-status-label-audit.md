# Self/Lineage status label audit

Task: `t_bfb00b5e`

Yunuen clarified that user-facing profile/project notifications must use exactly these two canonical status labels:

```text
Self status: WORKING|WAITING|BLOCKED|DORMANT — ...
Lineage status: WORKING|WAITING|BLOCKED|DORMANT — ...
```

Role-specific notification labels such as coordinator-, PA-, responsible-, developer-, researcher-, or master-specific status labels must not be used for active profile notifications, Matrix/Kanban handoffs, skills, prompt templates, watchdog prompts, or profile policy text.

## Patch scope

Updated live profile/policy text under:

- `/home/engs2272/.hermes/profiles/*/SOUL.md`
- `/home/engs2272/.hermes/profiles/*/plans/*.md`
- `/home/engs2272/.hermes/profiles/*/skills/**`
- `/home/engs2272/.hermes/profiles/*/records/**`
- `/home/engs2272/.hermes/coordination/*.md`
- `/home/engs2272/.hermes/coordination/responsible-knowledge/*.md`

Runtime history stores and logs are intentionally excluded from policy enforcement because they preserve past sessions rather than seed new notifications.

## Deterministic check

Added `scripts/hermes_maintenance_status_label_audit.py`, which scans profile/coordination policy-like text and fails on legacy role-specific status labels while skipping runtime history (`state.db`, WAL/SHM, logs, sessions, caches, media, venvs, `.local`).

Passing verification from this worktree:

```text
$ /home/engs2272/.hermes/hermes-agent/venv/bin/python scripts/hermes_maintenance_status_label_audit.py /home/engs2272/.hermes/profiles /home/engs2272/.hermes/coordination
status-label audit passed: scanned 12806 files; no legacy role-specific notification labels found.
```

Targeted tests:

```text
$ PYTHONPATH=$PWD /home/engs2272/.hermes/hermes-agent/venv/bin/python -m pytest tests/test_hermes_maintenance_status_label_audit.py -o 'addopts=' -q
3 passed in 0.07s
```
