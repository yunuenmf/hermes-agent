# Research: repeated Hermes compaction/context-overload solutions

Date: 2026-06-04
Task: t_b3e12465
Branch/worktree: researcher/compaction-solutions-hermes-lcm at /home/engs2272/.hermes/hermes-agent/.worktrees/t_b3e12465

## Executive recommendation

Do not build more custom compaction machinery yet.

Run a small, reversible experiment with hermes-lcm on one non-production or low-risk profile first, while keeping the existing built-in compression and context-fragmentation process as the safe fallback. Hermes-lcm is the most directly relevant available solution because it is designed as a Hermes context-engine plugin that stores the full conversation locally, summarizes old material into a searchable tree, and gives the agent tools to recover exact old details. It is not a magic fix: it adds a local SQLite database, has open performance/host-integration issues, and changes the privacy/storage risk profile because more raw conversation content is deliberately preserved.

In lay language: built-in compression is like turning the earlier part of the chat into one note. Hermes-lcm is more like putting the chat into a filing cabinet, writing index cards for old drawers, and giving the agent tools to open the drawer again when it needs the exact old text. That should help when compaction makes the agent forget details, but it may not help if the real problem is too many always-on instructions, too many active roles in one profile, or noisy gateway/Kanban/Matrix traffic.

## Internet access and search evidence

Internet access was verified from the task worktree with live GitHub/API and docs fetches on 2026-06-04:

- GitHub repository search for `hermes-lcm` returned stephenschoettler/hermes-lcm as the top result, described as “Lossless Context Management plugin for Hermes Agent — DAG-based context engine that never loses a message.”
- GitHub issue search in NousResearch/hermes-agent returned active LCM/context-engine items, including PR #6464 and issues #20316, #23140, #27633.
- Raw README fetch succeeded from https://raw.githubusercontent.com/stephenschoettler/hermes-lcm/main/README.md.
- Official Hermes docs fetch succeeded from https://hermes-agent.nousresearch.com/docs/developer-guide/context-engine-plugin and https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching.
- Prior-art fetch succeeded from https://raw.githubusercontent.com/martian-engineering/lossless-claw/main/README.md and the LCM paper URL https://papers.voltropy.com/LCM.

Exact local command evidence is in this run’s transcript; local repository handles are listed in “Local evidence handles” below.

## What hermes-lcm is

Hermes-lcm is a third-party Hermes Agent plugin by stephenschoettler. Its README describes it as “Lossless Context Management plugin for Hermes Agent,” with the slogan “Bounded context, unbounded memory. Nothing is ever lost.” It is based on the LCM paper by Ehrlich & Blackman and inspired by lossless-claw for OpenClaw.

Core behavior from the README:

- It stores raw messages in a local SQLite message store before compaction.
- It compacts older context into a hierarchical summary DAG.
- It exposes recovery tools such as `lcm_grep`, `lcm_describe`, `lcm_expand`, `lcm_expand_query`, `lcm_status`, and `lcm_doctor`.
- It supports source-aware retrieval, session filters, optional large payload externalization, optional sensitive-pattern redaction, and diagnostics.
- It positions itself as different from Hermes built-in compression because recall is part of the active context engine, not only a separate host-level history search.

Important wording from its README: Hermes core may still persist original conversation history in `state.db`, and `session_search` can recover earlier history; hermes-lcm should not be sold as “Hermes has no history.” The difference is that LCM gives the active agent a purpose-built drill-down mechanism during/after compaction.

Sources:
- https://github.com/stephenschoettler/hermes-lcm
- https://raw.githubusercontent.com/stephenschoettler/hermes-lcm/main/README.md
- https://papers.voltropy.com/LCM
- https://github.com/martian-engineering/lossless-claw

## How hermes-lcm integrates with Hermes

Hermes now has a pluggable context-engine slot. Local docs and code confirm this:

- `agent/context_engine.py` defines the ContextEngine interface. Engines decide when compaction fires, perform compaction, track token usage, and may expose tools.
- `website/docs/developer-guide/context-engine-plugin.md` says only one context engine can be active at a time and selection is config-driven via `context.engine`.
- `website/docs/developer-guide/context-compression-and-caching.md` says the built-in compressor is default, plugin engines are never auto-activated, and selection uses `context.engine`.
- `agent/agent_init.py:1262-1337` reads `context.engine`, tries `plugins/context_engine/<name>`, then the general plugin system, and falls back to the built-in compressor if not found.
- `agent/agent_init.py:1352-1377` injects context-engine tool schemas into the agent’s tool list.
- `hermes_cli/plugins.py:499-527` supports `ctx.register_context_engine(engine)` for general plugins.

Hermes-lcm’s own README says it has two names:

- plugin manifest name: `hermes-lcm`
- runtime context engine name: `lcm`

The documented activation shape is:

```yaml
plugins:
  enabled:
    - hermes-lcm

context:
  engine: lcm
```

The README says to restart Hermes after changing plugin or context-engine config.

## Install/config steps, not executed

No install or production config mutation was performed for this task.

The hermes-lcm README gives these install paths:

1. General user plugin:

```bash
git clone https://github.com/stephenschoettler/hermes-lcm ~/.hermes/plugins/hermes-lcm
```

2. Profile-specific plugin:

```bash
git clone https://github.com/stephenschoettler/hermes-lcm ~/.hermes/profiles/myprofile/plugins/hermes-lcm
```

3. Symlink from an existing checkout:

```bash
./scripts/install.sh
HERMES_PROFILE=myprofile ./scripts/install.sh
```

Then enable both the plugin and the context engine in config, restart Hermes, and verify with `hermes plugins`. Expected signals in the README are: plugin list includes `hermes-lcm`, selected context engine is `lcm`, and tools include `lcm_grep`, `lcm_load_session`, `lcm_describe`, `lcm_expand`, `lcm_expand_query`, `lcm_status`, and `lcm_doctor`.

Important local caveat: in the local downstream checkout, `plugins/context_engine/__init__.py` still says it scans bundled `plugins/context_engine/<name>/`. `agent_init.py` also falls back to the general plugin system. There is an open upstream Hermes PR #30761 to support user-installed context engine plugins via `$HERMES_HOME/plugins/`, which means plugin placement/discovery should be tested carefully before assuming the README’s user-plugin path works in this exact downstream branch.

Sources:
- https://raw.githubusercontent.com/stephenschoettler/hermes-lcm/main/README.md
- https://github.com/NousResearch/hermes-agent/pull/30761
- Local: `plugins/context_engine/__init__.py:1-220`
- Local: `agent/agent_init.py:1262-1377`
- Local: `hermes_cli/plugins.py:499-527`

## Known limitations and open issues

### hermes-lcm repository issues

Open issue #235 reports slow startup from unconditional full SQLite FTS5 integrity-check on every launch. The issue reports a long-lived `lcm.db` of 328MB / about 54.6k messages where startup stalled around 90 seconds, with FTS5 integrity-check taking about 81 seconds before a rebuild. This matters for profiles with long histories and lots of tool output.

Open issue #168 asks to make preflight compression messaging context-engine aware. The symptom is user-facing wording like “Preflight compression...” even when LCM is the active engine and healthy. That is mostly UX/status clarity, not necessarily data loss.

Sources:
- https://github.com/stephenschoettler/hermes-lcm/issues/235
- https://github.com/stephenschoettler/hermes-lcm/issues/168

### Hermes host integration issues/PRs around LCM

Open items in NousResearch/hermes-agent search results show that LCM and context-engine integration is still active work:

- PR #6464: “feat(lcm): Lossless Context Management as ContextEngine plugin” is open and describes a Hermes LCM implementation with DAG store, tools, and tests.
- PR #5700: “feat: pluggable context engine slot” is closed/unmerged but documents the architectural motivation: LCM and future context engines need to control what stays in the active window.
- Issue #20316: says `run_agent.py` never calls `should_compress_preflight()`, so LCM deferred maintenance may not fire.
- Issue #23140: says gateway mode does not invoke pre/post LLM hooks, causing LCM/context plugins to fail silently in platform sessions.
- Issue #27633: says a compression boundary drops the platform kwarg, causing source lineage to become `unknown` after compression.
- PR #30761: proposes user-installed context-engine plugin discovery via `$HERMES_HOME/plugins/`.

These are not proof that the local branch has every defect. They are evidence that we must test CLI and gateway/Matrix behavior separately before rolling LCM into production coordinator profiles.

Sources:
- https://github.com/NousResearch/hermes-agent/pull/6464
- https://github.com/NousResearch/hermes-agent/pull/5700
- https://github.com/NousResearch/hermes-agent/issues/20316
- https://github.com/NousResearch/hermes-agent/issues/23140
- https://github.com/NousResearch/hermes-agent/issues/27633
- https://github.com/NousResearch/hermes-agent/pull/30761

## Other alternatives / prior art

### A. Built-in Hermes compression

Hermes has a built-in ContextCompressor and gateway session hygiene. The local docs describe a dual system:

- gateway hygiene at about 85% of model context as a safety net before agent processing;
- agent compression at the configurable `compression.threshold`, documented default 50%;
- `compression.target_ratio` and protected head/tail messages control what remains after compaction;
- old tool results can be pruned cheaply before summarization;
- the summary model must have a large enough context window, otherwise summary generation can fail and context quality can degrade.

This option is already present and lower-risk. It can reduce compaction frequency by tuning thresholds and summary behavior, but it remains summary-based: exact old details may still require `session_search` or other history tools.

Sources:
- https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching
- Local: `website/docs/developer-guide/context-compression-and-caching.md:37-208`
- Local: `agent/context_compressor.py`

### B. Context fragmentation / responsible profiles

The loaded local `context-fragmentation` skill is a process solution, not a retrieval engine. It says that when auto-compaction still leaves high pressure, the system should split durable knowledge and duties into bounded responsible profiles or project-scoped owners. In lay language: if one person/profile is carrying too many notebooks in their backpack, give separate notebooks to separate people instead of buying a bigger backpack.

This helps when compaction is frequent because a profile’s always-on prompt/memory/role is too large. It does not by itself preserve every old chat detail; it reduces the need to carry everything in one active context.

Local source:
- Installed skill: `/home/engs2272/.hermes/profiles/researcher_hermes_maintenance/skills/devops/context-fragmentation/SKILL.md`
- Rollout note: `/home/engs2272/.hermes/profiles/researcher_hermes_maintenance/skills/devops/context-fragmentation/references/deterministic-compaction-monitor-rollout.md`
- Local test: `tests/agent/test_compression_post_compaction_monitor.py`

### C. Deterministic post-compaction monitor

The local context-fragmentation rollout notes recommend a deterministic warning at the compaction boundary: measure before/after pressure, warn only when pressure remains high, and do not run a recurring cron as the normal mechanism. The local test `tests/agent/test_compression_post_compaction_monitor.py` confirms the current local code expects warnings like “Compression pressure remains high” when a compressed result still exceeds the threshold.

This is a visibility/safety solution: it tells Yunuen when compaction did not really solve the pressure problem. It does not replace compression or LCM.

### D. Session reset / transcript pruning patterns

Hermes already has `/new`, `/reset`, manual `/compress`, session history, and `session_search`. Session reset is the simplest pressure relief: start a fresh active session and rely on durable records/Kanban/session search for old work. Transcript pruning/noise filters are useful when gateway alerts, cron output, or repeated tool blobs are filling context.

The tradeoff is continuity: resets and pruning are safe only if important project state is in Kanban, repo docs, Matrix, or records. They are poor if the active chat is the only place where decisions exist.

Sources:
- Hermes skill/CLI reference loaded in this session: `/new`, `/reset`, `/compress`, `session_search`.
- Local docs: `website/docs/developer-guide/context-compression-and-caching.md`.

### E. Vector/RAG/context-store approaches

Vector/RAG tools are a family of solutions that put old information into a searchable store and retrieve likely-relevant chunks. They can help with broad recall over docs, sessions, and project records. Hermes already has host-level `session_search`; plugins/memory providers can add other memory backends. The tradeoff is that vector retrieval may find “similar” material but not always the exact old turn, and it can hide mistakes if the wrong chunk is retrieved confidently.

Hermes-lcm is closer to a structured current-session archive than generic RAG: it stores raw messages plus summaries with source lineage and provides bounded expand/search tools.

Sources:
- Local: `website/docs/developer-guide/context-engine-plugin.md:101-126` for context-engine tools.
- Local: Hermes `session_search` tool behavior in active tool instructions.
- hermes-lcm README retrieval contract.

## Comparison in lay language

| Option | Plain-language picture | What it helps | Main tradeoff | Fit for constant compaction |
|---|---|---|---|---|
| Adopt hermes-lcm experimentally | Filing cabinet plus index cards for old chat | Recover exact old details after compaction; less “forgotten after summary” risk | New plugin, local DB growth, open performance/integration issues, privacy/storage review | Best candidate if compaction loses important details |
| Keep built-in compression but tune it | Better automatic note-taking | Lower risk; already built in; knobs exist | Still summary-based; repeated summaries can lose detail or churn | Good first-line baseline and fallback |
| Context fragmentation / responsible profiles | Split one overloaded job into smaller jobs | Reduces always-on prompt/memory load and role overload | Requires architecture/ownership choices and Matrix/Kanban routing discipline | Best if the profile is carrying too many duties |
| Session reset + records/Kanban discipline | Start a fresh notebook and file old decisions properly | Simple, safe, cheap | Requires disciplined handoffs; active chat continuity drops | Good operational hygiene; not enough alone for long live chats |
| Generic RAG/vector/session search | Searchable library | Broad recall over old material | Retrieval may be approximate; not necessarily current-session-aware | Useful supplement, not a direct compaction replacement |
| Hybrid | Filing cabinet + smaller jobs + better warnings | Addresses multiple causes at once | More moving pieces; needs staged rollout | Most realistic production path |

## Does hermes-lcm address “constant compaction” symptoms?

Partly.

It should help when the symptom is: “after compaction, the agent no longer has exact details and must rediscover them.” LCM keeps exact old messages recoverable and gives the model tools to search/expand them.

It may not help when the symptom is: “the profile reaches high context immediately because the system prompt, memory, skills, Matrix/Kanban state, and role duties are too large before any user conversation starts.” In that case, LCM can store history, but it cannot make the always-on prompt smaller. Context fragmentation and memory/prompt cleanup are the better tools for that cause.

It may make some pressure worse if not tuned: LCM adds its own status/tools/summary structures and stores more data locally. Open issue #235 shows large `lcm.db` startup performance can become a real operational concern.

## Recommended small experiment plan

Do this only after Yunuen chooses the architecture/privacy/cost risk level. Do not enable it on production coordinator/admin profiles first.

### Experiment profile

Use one test profile or a low-risk cloned coordinator-like profile. Prefer a fresh profile-local plugin/config so rollback is deleting/renaming that profile/plugin and restoring config.

### Baseline before enabling LCM

For 3-5 representative sessions, record:

- number of compactions per session/hour;
- prompt pressure before compaction and after compaction;
- whether the agent loses key details after compaction;
- number of times it needs `session_search` or manual recap;
- Matrix/Kanban continuity: task IDs, room identity, parent/child task handoff still correct;
- startup latency and profile responsiveness.

### Enable and verify in test only

1. Install hermes-lcm in the test profile or a disposable plugin path.
2. Set `plugins.enabled: [hermes-lcm]` and `context.engine: lcm` only in that profile.
3. Restart Hermes.
4. Verify `hermes plugins` shows plugin `hermes-lcm`, selected context engine `lcm`, and the LCM tools.
5. Send one normal message, then check `lcm_status`/`lcm_doctor` if tools are available.
6. Run one CLI session and one gateway/Matrix-like session because upstream issues indicate gateway hooks/source lineage can differ from CLI.

### Success metrics

Call the experiment successful only if all of these improve or stay safe:

- Compaction frequency: fewer emergency/forced compactions, or compactions become less disruptive.
- After-compaction pressure: prompt pressure after compaction is lower and stays below the warning threshold for longer.
- Recall: the agent can recover exact old details through LCM tools without asking Yunuen to repeat them.
- Continuity: Matrix/Kanban task identity, task comments, parent/child links, and project-room routing do not regress.
- Latency: startup and first response do not become noticeably slow; specifically watch for the open FTS5 integrity-check issue on larger DBs.
- Storage/privacy: local `lcm.db` size and externalized payload directory stay acceptable; sensitive-pattern redaction policy is understood.
- Rollback: disabling `context.engine: lcm` and removing the plugin returns the profile to the built-in compressor without data corruption.

### Stop conditions

Stop or rollback if:

- gateway/Matrix sessions silently bypass LCM or lose source lineage;
- startup stalls grow materially as `lcm.db` grows;
- LCM tools are missing after activation;
- compaction messages become confusing enough to impair operations;
- sensitive raw messages are stored against Yunuen’s privacy preference;
- Matrix/Kanban continuity breaks.

## Decision Yunuen should make before enabling anything

Please choose one of these risk levels before implementation:

1. Conservative: no LCM yet; tune built-in compression and continue context fragmentation/responsible-profile cleanup.
2. Pilot: enable hermes-lcm only on a disposable/test profile and measure for a few sessions.
3. Targeted production pilot: enable hermes-lcm on one lower-risk working profile after a backup and rollback checklist.
4. Broad rollout: not recommended yet because upstream/local evidence shows active integration and performance issues.

My recommendation is option 2 first.

## Local evidence handles

Local worktree inspected: `/home/engs2272/.hermes/hermes-agent/.worktrees/t_b3e12465`

Files/evidence:

- `agent/context_engine.py:1-211` — ContextEngine ABC, lifecycle, tool hooks, token fields.
- `website/docs/developer-guide/context-engine-plugin.md:7-168` — docs for plugin selection, one active engine, config, tools, lifecycle.
- `website/docs/developer-guide/context-compression-and-caching.md:10-35` — pluggable context engine docs; plugin engines are never auto-activated.
- `website/docs/developer-guide/context-compression-and-caching.md:37-208` — dual compression system, thresholds, algorithm, summary-model risk.
- `agent/agent_init.py:1262-1377` — local config selection and tool schema injection for context engines.
- `plugins/context_engine/__init__.py:1-220` — local bundled context-engine discovery path.
- `hermes_cli/plugins.py:499-527` — general plugin `register_context_engine` support.
- `tests/agent/test_compression_post_compaction_monitor.py:43-97` — local tests for post-compaction high-pressure warning.
- Installed skill: `/home/engs2272/.hermes/profiles/researcher_hermes_maintenance/skills/devops/context-fragmentation/SKILL.md` — fragmentation workflow and thresholds.
- Installed skill reference: `/home/engs2272/.hermes/profiles/researcher_hermes_maintenance/skills/devops/context-fragmentation/references/deterministic-compaction-monitor-rollout.md` — compaction-boundary monitor pattern.

## Source list

- https://github.com/stephenschoettler/hermes-lcm — primary repository for hermes-lcm; confirms project identity, description, active updates.
- https://raw.githubusercontent.com/stephenschoettler/hermes-lcm/main/README.md — primary install/config/behavior docs for hermes-lcm.
- https://github.com/stephenschoettler/hermes-lcm/issues/235 — open performance issue about large `lcm.db` startup/FTS5 checks.
- https://github.com/stephenschoettler/hermes-lcm/issues/168 — open UX/status issue for context-engine-aware preflight messaging.
- https://papers.voltropy.com/LCM — cited underlying LCM paper; useful for conceptual prior art.
- https://github.com/martian-engineering/lossless-claw — OpenClaw prior art that inspired hermes-lcm.
- https://raw.githubusercontent.com/martian-engineering/lossless-claw/main/README.md — lossless-claw behavior: replaces sliding-window compaction with DAG summarization while preserving messages.
- https://hermes-agent.nousresearch.com/docs/developer-guide/context-engine-plugin — official Hermes context-engine plugin docs.
- https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching — official Hermes compression/context-engine docs.
- https://github.com/NousResearch/hermes-agent/pull/6464 — open Hermes LCM/context-engine implementation PR.
- https://github.com/NousResearch/hermes-agent/pull/5700 — architectural PR/proposal for the pluggable context-engine slot.
- https://github.com/NousResearch/hermes-agent/issues/20316 — open host issue: preflight hook not called, impacting LCM deferred maintenance.
- https://github.com/NousResearch/hermes-agent/issues/23140 — open host issue: gateway mode hook invocation gap for context plugins.
- https://github.com/NousResearch/hermes-agent/issues/27633 — open host issue: platform/source lineage dropped after compression boundary.
- https://github.com/NousResearch/hermes-agent/pull/30761 — open host PR for user-installed context-engine plugin discovery.
