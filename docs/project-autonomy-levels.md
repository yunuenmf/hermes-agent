# Project autonomy levels

Kanban boards store a durable project-wide `autonomy_level` in each board's `board.json`. The allowed values are exactly `Low`, `Medium`, `High`, and `Full`. Existing boards that do not yet have the field are treated as `Medium`, which matches the previous Hermes project-operation baseline. v1 intentionally uses one project-wide level per board; per-lane/card overrides are out of scope.

The level is visible and editable in the Kanban Web UI board switcher. It can also be set from the CLI:

```bash
hermes kanban boards create <slug> --autonomy-level High
hermes kanban boards set-autonomy <slug> Full
hermes kanban --board <slug> boards show
hermes kanban boards list --json
```

## Levels

### Low

Granular human-reviewed mode. Agents and coordinators may inspect, draft, test, and prepare proposals, but should stop for human review before medium-risk or externally visible state changes such as GitHub push/PR approval/merge, deployment, destructive DB/runtime actions, or user-facing policy changes.

### Medium

Current/default Hermes baseline. Agents proceed with routine scoped implementation, tests, documentation, local DB changes, and Kanban execution. They stop for decisions previously treated as medium-risk approval prompts, deployments, merges/approvals where policy requires Yunuen, credential/key/access issues, destructive production/runtime actions, or material plan changes.

### High

Auto-approves routine `Medium` approval prompts Yunuen normally accepts. GitHub pull/push/PR approval/merge may proceed automatically when CI and required review evidence pass, provided no red flags are present. Deployment remains human-approval gated. Hard stops remain credentials/keys/secrets/access, unsafe destructive operations, external impossibility, and major scope/safety changes.

### Full

After a strong initial plan, agents/coordinators proceed according to their recommendation and evidence without routine review stops. Routine GitHub and board work is automatic. Deployment may proceed only when deployment is explicitly part of the approved plan; if not, agents should recommend deployment at completion rather than perform it. Contact Yunuen only for hard stops: credentials/keys/secrets/access, external impossibility, legally/security-dangerous action, deployment not covered by the approved plan, or truly dramatic plan changes that invalidate the initial plan.

## API shape

`GET /api/plugins/kanban/boards` includes:

```json
{
  "slug": "hermes-maintenance",
  "autonomy_level": "High",
  "autonomy": {
    "summary": "Auto-approve routine Medium approvals and GitHub merge when CI and required review evidence pass; deployment remains gated.",
    "requires_strong_initial_plan": true,
    "routine_review_required": false,
    "auto_approves_medium_prompts": true,
    "github_push_pull_merge_automatic": true,
    "deployment_requires_approval": true,
    "contact_yunuen_for": ["..."]
  }
}
```

Create/update endpoints accept `autonomy_level` and reject unknown values with HTTP 400.
