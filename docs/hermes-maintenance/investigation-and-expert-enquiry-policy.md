# Systematic Investigation and Expert Enquiry Policy

This is the downstream Hermes Maintenance policy for embedding investigation,
prior-art research, and relevant profile-to-profile enquiry into normal profile
behavior without creating noisy consultation requirements.

## Goal

For non-trivial work, every profile should pause long enough to ask:

- What has already been tried in this project?
- What public tools, APIs, patterns, or prior art already exist?
- Which Hermes profile owns or knows this area?
- Is this a local reversible choice, a specialist consultation, or a Yunuen decision?

This is a habit, not a bureaucracy. Tiny, reversible, repo-local fixes should not
page other profiles or trigger internet research by default.

## Grounding inspected for this policy

- Current live profiles were inspected with `hermes profile list` on 2026-06-04.
- Current profile descriptions were inspected with `hermes profile describe <profile>`.
- Existing profile documentation already records `profile.yaml` descriptions for
  orchestrator routing and `hermes profile describe` as the maintained metadata
  surface.
- Existing Kanban/orchestrator guidance already says to discover real profiles,
  use direct profile communication for discussion, and keep Kanban for durable
  work/evidence rather than chat.
- Researcher consultation identified public analogues: Kubernetes SIG/OWNERS,
  GitHub CODEOWNERS, Backstage Software Catalog, PagerDuty escalation policies,
  AutoGen/CrewAI role-based agents, and Slack-style narrowcast etiquette.

## Decision rule

Use this rule at the start of non-trivial work and whenever new facts change the
risk profile.

### Proceed locally

Proceed locally when all of these are true:

1. The task is low-risk and reversible.
2. The answer is repo-local or already covered by current project docs, tests, or
   parent-task handoffs.
3. No new external dependency, API, cost, license, privacy, architecture, Matrix,
   or user-facing behavior decision is being introduced.
4. A local verification command can prove the result.

Examples: fix a typo, run an existing test, inspect a local config, update a doc
section that is already explicitly specced.

### Research internet/prior art

Research public sources when any of these are true:

1. The task is unfamiliar, externally dependent, or asks "what already exists?"
2. The answer depends on current versions, public APIs, model capabilities,
   standards, security advisories, incidents, pricing, or license terms.
3. The choice could avoid reinventing an existing tool/pattern.
4. The project would benefit from cited evidence rather than intuition.

Research output should be concise: sources read, what mattered, confidence, and
how it changes the local plan.

### Consult another profile

Consult another profile when the profile expertise directory shows a strong match
and at least one of these is true:

1. The work crosses that profile's project, milestone, or ownership boundary.
2. The profile likely has recent project context or private implementation memory
   that public research will not reveal.
3. The decision would be materially better with a specialist's answer.
4. The profile owns a route, policy, or subsystem you would otherwise change.

Anti-spam rule: lookup -> score -> narrowcast -> summarize.

- Lookup: inspect the directory and current profile list; do not invent names.
- Score: prefer owner match, expertise-tag match, project match, freshness, and
  safe contact route.
- Narrowcast: ask one best-fit profile first unless multiple owners are truly
  required.
- Summarize: record only durable outcomes/evidence on Kanban or in git; do not
  turn Kanban into chat.

### Ask Yunuen

Ask Yunuen when the choice changes or risks any of these:

- architecture or project boundaries,
- privacy, secrets, private contact routes, or Matrix topology,
- user-facing behavior or notifications,
- cost, legal/licensing posture, or irreversible operations,
- cross-project defaults or profile hierarchy,
- a high-impact decision with no safe owner in the directory.

If the issue is simply waiting for CI, a worker, a dependency, or automated
verification, mark it `waiting`, not `blocked`.

## Profile expertise directory design

Canonical machine-readable source:

- `docs/hermes-maintenance/profile-expertise-directory.yaml`

Generated human-readable view:

- `docs/hermes-maintenance/profile-expertise-directory.md`

Renderer:

- `scripts/render_profile_expertise_directory.py`

Tests:

- `tests/test_profile_expertise_directory.py`

The YAML is canonical because profiles, dashboards, future CLI commands, or
Kanban helpers can consume it without scraping prose. The Markdown is generated
for humans and PR review.

### Minimum entry fields

- `profile_id`: exact profile name from `hermes profile list`.
- `display_name`: readable label.
- `profile_type`: personal_assistant, coordinator, responsible, researcher,
  developer, or template.
- `project`: project boundary, such as `hermes-maintenance`.
- `tree_path`: structure from top-level profile to this profile.
- `role_summary`: one public-safe sentence.
- `expertise_tags`: searchable routing tags.
- `owned_domains`: what the profile owns.
- `consult_on`: when it is useful to ask this profile.
- `do_not_consult_for`: explicit anti-spam boundaries.
- `contact`: abstract route and escalation, not raw secrets or private room IDs.
- `privacy_level`: public_safe, internal_only, or restricted.
- `status`: active, template, stale, or retired.
- `owner`: profile or human responsible for freshness.
- `last_verified`: date of last profile-list/description check.

## Privacy and publication boundary

The directory may expose profile names, roles, public-safe expertise, ownership,
project boundary, and abstract contact methods. It must not expose:

- Matrix room IDs or invite links,
- bot tokens, API keys, credentials, auth files, or home-channel IDs,
- private user identifiers beyond agreed profile names,
- unreviewed personal details from profile memory,
- sensitive project names unless explicitly classified safe.

Use `validated_internal_room` only as an abstract method until Matrix hardening
has approved a public-safe route representation.

## Maintenance workflow

1. New profile: creator supplies `--description` or runs `hermes profile describe`;
   owning coordinator/responsible adds a directory entry before assigning durable
   cross-profile work.
2. Rename/project move: update the YAML in the same branch/PR as the operational
   rename/move.
3. Retirement: mark `status: retired` first. Delete only after review if history
   is no longer useful.
4. Staleness: during monthly Hermes Maintenance review, run `hermes profile list`,
   compare against the directory, refresh `last_verified`, and mark missing or
   inactive profiles as `stale`.
5. Discovery: profiles read the generated Markdown for human orientation or the
   YAML for routing. Future CLI/Kanban helpers should consume the YAML.

## Implementation slices

1. Land this non-invasive policy, YAML directory, renderer, generated Markdown,
   and tests.
2. Add a CLI helper such as `hermes profile directory render/check` or a Kanban
   utility that validates the YAML against live `hermes profile list`.
3. Extend `hermes profile create`, `profile describe`, or profile distributions to
   prompt for directory fields and warn when a profile has no directory entry.
4. Teach orchestrator prompts/skills to apply the decision rule before routing
   non-trivial work.
5. Ask `responsible_memory_rollout` to mirror the rule into reusable skills and
   memory hygiene after this policy lands.
6. Ask `responsible_matrix_hardening` to define which Matrix contact abstractions,
   if any, are safe to expose in the directory.
7. Add project-watchdog checks for stale/missing directory entries only after the
   directory has one maintenance cycle of real use.

## Acceptance checks for this slice

- The directory contains only real profiles observed from `hermes profile list`.
- Public-safe route abstractions are used instead of private room IDs or secrets.
- The decision rule prevents both under-research and noisy profile spam.
- The renderer produces a readable Markdown directory from the YAML.
- Tests validate required safety fields and rendered sections.
