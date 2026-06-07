# Internal profile communication toolbox

Hermes profiles should discuss with each other through direct/internal channels. Kanban is the durable coordination ledger, not a chat transport.

## Rule

Do not create Kanban contact tasks merely to ask, notify, ping, or refine with another profile. Use Kanban for durable work items, dependencies, blockers, evidence, review handoffs, and post-discussion outcomes.

## Direct profile runner path

Use the named profile directly when you need a quick internal answer or instruction:

```bash
hermes -p <profile> chat -q '<question or instruction>' --toolsets safe
```

Notes:

- This starts the target profile directly and does not create a Kanban task.
- Add `--skills <skill-name>` when the target must load a specific policy or domain skill.
- Use a bounded prompt and ask for a concise response so the interaction remains discussion, not a durable work assignment.

## Structured internal message path

When a validated private profile room/channel exists, send a structured message instead of creating a contact task:

```bash
printf '%s\n' '<structured note>' | hermes send --to <target> --file - --subject '[internal:<profile>]'
```

Agents with the messaging tool can use:

```python
send_message(
    target='<target>',
    message='[internal:<profile>]\nContext: ...\nQuestion: ...\nNeeded by: ...',
)
```

Use `hermes send --list` or `send_message(action='list')` before sending to a specific person/channel when the target is ambiguous.

## Matrix escalation and guards

- Human-facing Matrix participation is for decisions or actions that genuinely require Yunuen or another human.
- Before contacting a human from a dedicated Matrix room, validate profile room isolation and gateway activation with the coordination validators.
- If a Matrix profile-room send is blocked, unvalidated, or unavailable, do not create a Kanban contact task as a workaround. Use the direct profile runner path, or block only when a concrete human action is required.

## What to record on Kanban

After direct discussion, write a Kanban comment or follow-up task only for durable outcomes: decisions, evidence, dependencies, blocker status, review feedback, or concrete work that should survive restarts and be audited.

## Blocker-to-coordinator review path

Blocked-task comments are never executable dispatch. When a blocker, review-required handoff, crash/timeout circuit-breaker, or active-PR respawn guard needs coordination, Kanban creates a dedicated `coordinator_review` holder task assigned to the board coordinator profile. That holder is a spawnable review lane with `kanban-orchestrator` loaded; it is distinct from human `blocked` and non-human waiting/parent-dependency holds.

Coordinator outcomes are deterministic:

1. solve trivial admin/routing issues directly;
2. delegate non-trivial implementation to the appropriate responsible/profile;
3. create a deployment/restart/review cluster when the blocker is a deployment or PR authority gate;
4. re-dispatch the source task when automated recovery is enough;
5. preserve a human blocker only when deployment approval, secrets/credentials, destructive action, new scope, or another concrete human decision is required.
