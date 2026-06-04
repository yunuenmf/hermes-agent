# Hermes Maintenance Profile Expertise Directory

> Generated from `docs/hermes-maintenance/profile-expertise-directory.yaml`. Keep the YAML canonical and regenerate this view after edits.

- Schema version: 1
- Visibility: internal_public_safe
- Canonical owner: responsible_project_autonomy
- Update cadence: on profile create/rename/retire and during monthly Hermes Maintenance review

## Investigation and enquiry decision rule

### Proceed locally when
- The task is small, reversible, repo-local, already covered by current docs/tests, and does not introduce a new external dependency or policy choice.
- A local verification command can prove the answer without current internet facts or another profile's private project context.

### Research internet/prior art when
- The task is unfamiliar, non-trivial, externally dependent, security/privacy/licensing/cost sensitive, or asks whether existing tools or prior attempts already solve it.
- The answer depends on current versions, public APIs, standards, incidents, pricing, model capabilities, or third-party documentation.

### Consult another profile when
- The directory shows a strong owner or expertise match and the question crosses that profile's project or milestone boundary.
- The profile likely has non-public project context, recent implementation memory, or a narrower skill set that materially improves the answer.
- Use lookup -> score -> narrowcast -> summarize: ask the smallest relevant audience, normally one best-fit profile first.

### Ask Yunuen when
- The choice changes architecture, project boundaries, privacy, secret exposure, Matrix/contact topology, user-facing behavior, cost, legal/licensing posture, or irreversible operations.
- The directory has no safe owner for a high-impact decision and proceeding would create hidden policy.

## Privacy rules

- Do not expose private Matrix room IDs, invite links, tokens, API keys, credential paths, personal phone numbers, or private chat identifiers.
- Use contact route abstractions such as direct_profile_command or validated_internal_room instead of raw room IDs.
- Mark entries restricted when a profile's existence, project boundary, or contact route is not safe for broad internal discovery.

## Profile tree

- pa_yunuen → default
- pa_yunuen
- coordinator_master
- pa_yunuen → coordinator_hermes_maintenance
- pa_yunuen → coordinator_hermes_maintenance → responsible_project_autonomy
- pa_yunuen → coordinator_hermes_maintenance → responsible_board_safety
- pa_yunuen → coordinator_hermes_maintenance → responsible_kanban_semantics
- pa_yunuen → coordinator_hermes_maintenance → responsible_memory_rollout
- pa_yunuen → coordinator_hermes_maintenance → responsible_matrix_hardening
- pa_yunuen → coordinator_hermes_maintenance → researcher_hermes_maintenance
- pa_yunuen → coordinator_hermes_maintenance → developer_hermes_maintenance
- pa_yunuen → pa_master
- coordinator_master → responsible_master
- coordinator_master → researcher_master
- coordinator_master → developer_master
- pa_yunuen → coordinator_hermes_migration_system
- pa_yunuen → coordinator_hermes_migration_system → researcher_hermes_migration_system
- pa_yunuen → coordinator_hermes_migration_system → developer_hermes_migration_system
- pa_yunuen → coordinator_qwen_image_layered
- pa_yunuen → coordinator_qwen_image_layered → researcher_qwen_image_layered

## Directory

| Profile | Type | Project | Status | Expertise | Consult on | Contact |
| --- | --- | --- | --- | --- | --- | --- |
| default | personal_assistant | global | active | default_profile, general | general_default_profile_questions | hermes -p default chat --toolsets safe |
| pa_yunuen | personal_assistant | global | active | project_admin, delegation, human_interface | human_facing_project_decisions, project_creation_or_destruction | hermes -p pa_yunuen chat --toolsets safe |
| coordinator_master | template | global | template | template, coordinator_pattern | coordinator_template_policy | template only |
| coordinator_hermes_maintenance | coordinator | hermes-maintenance | active | hermes_maintenance, kanban, matrix, watchdogs, architecture | cross_milestone_coordination, project_priority, board_level_dependencies | hermes -p coordinator_hermes_maintenance chat --toolsets safe |
| responsible_project_autonomy | responsible | hermes-maintenance | active | project_autonomy, dispatch_owner, project_boundaries, watchdog_split, profile_directory | project_boundaries, profile_tree_policy, dispatcher_owner_metadata, project_watchdog_split | hermes -p responsible_project_autonomy chat --toolsets safe |
| responsible_board_safety | responsible | hermes-maintenance | active | board_safety, kanban_db_repair, backup_first, blocker_audit | kanban_db_sanitation, backup_first_board_repair, board_safety_rollout | hermes -p responsible_board_safety chat --toolsets safe |
| responsible_kanban_semantics | responsible | hermes-maintenance | active | kanban_semantics, statuses, blocked_waiting, live_state | status_vocabulary, blocked_vs_waiting_policy, kanban_state_mapping | hermes -p responsible_kanban_semantics chat --toolsets safe |
| responsible_memory_rollout | responsible | hermes-maintenance | active | memory, skills, profile_hygiene, rollout | memory_policy, reusable_skill_capture, profile_memory_hygiene, directory_to_memory_mirroring | hermes -p responsible_memory_rollout chat --toolsets safe |
| responsible_matrix_hardening | responsible | hermes-maintenance | active | matrix, gateway, room_isolation, encryption, profile_contact | matrix_route_exposure, profile_room_isolation, gateway_activation, encryption_choice | hermes -p responsible_matrix_hardening chat --toolsets safe |
| researcher_hermes_maintenance | researcher | hermes-maintenance | active | research, prior_art, architecture, external_docs, evidence | prior_art, public_tooling_research, cited_decision_briefs, external_docs | hermes -p researcher_hermes_maintenance chat --toolsets safe,web |
| developer_hermes_maintenance | developer | hermes-maintenance | active | implementation, tests, git_worktree, pr | implementation_feasibility, test_strategy, repo_local_code_paths | hermes -p developer_hermes_maintenance chat --toolsets safe |
| pa_master | template | global | template | template, personal_assistant_pattern, project_admin | personal_assistant_template_policy | template only |
| responsible_master | template | global | template | template, milestone_owner_pattern | responsible_template_policy | template only |
| researcher_master | template | global | template | template, research_pattern | researcher_template_policy | template only |
| developer_master | template | global | template | template, developer_pattern | developer_template_policy | template only |
| coordinator_hermes_migration_system | coordinator | hermes-migration-system | active | migration_system, coordinator | migration_system_project_boundary | hermes -p coordinator_hermes_migration_system chat --toolsets safe |
| researcher_hermes_migration_system | researcher | hermes-migration-system | active | migration_system, research | migration_system_research | hermes -p researcher_hermes_migration_system chat --toolsets safe,web |
| developer_hermes_migration_system | developer | hermes-migration-system | active | migration_system, implementation | migration_system_implementation | hermes -p developer_hermes_migration_system chat --toolsets safe |
| coordinator_qwen_image_layered | coordinator | qwen-image-layered | active | qwen_image_layered, coordinator, local_inference | qwen_image_layered_project_boundary | hermes -p coordinator_qwen_image_layered chat --toolsets safe |
| researcher_qwen_image_layered | researcher | qwen-image-layered | active | qwen_image_layered, local_inference, cuda, pytorch, huggingface | qwen_image_layered_model_research, cuda_pytorch_feasibility | hermes -p researcher_qwen_image_layered chat --toolsets safe,web |

## Maintenance workflow

1. On profile creation, `hermes profile create --description` or `hermes profile describe` seeds `profile.yaml`; the owning coordinator/responsible adds a public-safe directory entry before assigning durable work.
2. On profile rename, project move, or retirement, update the YAML in the same PR/commit as the operational change.
3. During monthly Hermes Maintenance review, the canonical owner checks `hermes profile list`, refreshes `last_verified`, and marks missing or inactive profiles as `stale` or `retired` rather than deleting history.
4. Profiles discover expertise by reading this rendered doc, loading the YAML, or asking the coordinator for the best-fit owner. Consultation uses direct profile commands or validated internal rooms; Kanban remains for durable work, not chat.

