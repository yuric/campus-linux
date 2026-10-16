# Task 984 validation receipt

Producer: yuric/campus-server; branch codex/task-984-linux-contracts.
Base at implementation start: 4050498fd4556d1cf1cba9f87a6106b5467283be.
No desktop, provider-login, signed package, deployed SHA or live S1-5 evidence is claimed.

All Rails commands use Ruby 3.4.10 via `PATH="$HOME/.rbenv/shims:$PATH"`.
Tests use disposable databases, observed foreground processes and explicit bounds.
The current-head CI receipt and final broad-suite dispositions are recorded in the PR.

## Red/green observations

- `/tmp/task984-red-platform.log`: 4 runs, 6 assertions, 2 failures, 2 errors, 0 skips
- `/tmp/task984-red-transport.log`: 10 runs, 37 assertions, 5 failures, 1 errors, 0 skips
- `/tmp/task984-red-release.log`: 3 runs, 2 assertions, 2 failures, 1 errors, 0 skips
- `/tmp/task984-native-claim2-red.log`: 5 runs, 39 assertions, 1 failures, 0 errors, 0 skips
- `/tmp/task984-agy-red.log`: 8 runs, 52 assertions, 1 failures, 0 errors, 0 skips
- `/tmp/task984-core-fresh.log`: 194 runs, 10538 assertions, 1 failures, 0 errors, 0 skips
- `/tmp/task984-usage-red.log`: 9 runs, 61 assertions, 1 failures, 0 errors, 0 skips
- `/tmp/task984-final-core.log`: 224 runs, 11002 assertions, 0 failures, 0 errors, 0 skips

The deliberate reds exercise actual HTTP/service seams: Linux root/platform/store readiness,
hosted discovery/import and no-store delivery, Linux admin catalog, Antigravity isolated model
and usage scope, and exact hosted resume after a zero-turn failure. Test-setup errors were
fixed separately and never counted as a demonstrated behavioral failure.

The 194-test run has one deliberately added failing zero-turn hosted-resume assertion;
the subsequent 224-test run passed all 11,002 assertions after the fix. That run also checks
existing Mac native import, model discovery, API shape/route coverage, database tenant
constraints, old stream-loss evidence and persisted login-recovery messages.

Two setup runs timed out before assertions (parallel database preparation at the default
30-second inactivity limit; a separate schema load at 120 seconds). They are blocked evidence.
Subsequent runs use fresh isolated databases. The broad run encountered PostgreSQL shared
lock exhaustion in an existing coordinator test; that exact scenario passed in the 472-test
post-merge rerun. The parallel process later hit its 180-second no-output shutdown timeout
(exit 124); its partial output is not a whole-suite pass. Its disposable database family was
cleaned by the runner. Some broad-run failures reflect classes loaded before subsequent
corrections; every reported failing/error scenario was included in the fresh post-merge run. No database/server settings or CI controls are changed.

## Commands

The broad command below is the actual 84-file request/service/channel regression selection.
Its log is `/tmp/task984-affected-isolated.log`; the timeout and passing targeted reruns are
reported here and on the PR, with no coverage percentage claim (concurrent SimpleCov output is mixed).

```sh
PATH="$HOME/.rbenv/shims:$PATH" DATABASE_URL=postgresql:///campus_test_task984_s1_20261016 api/bin/test --stall-timeout 180 --workers 4 --timeout 1800 test/channels/agent_inbox_channel_test.rb test/channels/agent_output_channel_islands_test.rb test/channels/agent_output_channel_test.rb test/channels/connection_islands_test.rb test/channels/connection_test.rb test/channels/world_channel_islands_test.rb test/channels/world_channel_test.rb test/controllers/workspace_rules_controller_test.rb test/integration/agent_batch_landing_test.rb test/integration/agent_execution_context_test.rb test/integration/agent_restart_test.rb test/integration/agent_resume_test.rb test/integration/assistant_coordinator_queue_contract_test.rb test/integration/assistant_coordinator_sessions_test.rb test/integration/coordinator_user_parity_test.rb test/integration/credential_retry_endpoint_test.rb test/integration/credentials_test.rb test/integration/diagnostics_contract_test.rb test/integration/executor_crash_recovery_test.rb test/integration/executor_credential_bindings_test.rb test/integration/executor_credential_models_test.rb test/integration/executor_execution_plane_test.rb test/integration/executor_model_updates_test.rb test/integration/executors_test.rb test/integration/helper_update_resume_test.rb test/integration/hosted_executor_landing_test.rb test/integration/hosted_native_sessions_test.rb test/integration/linux_executor_contract_test.rb test/integration/linux_releases_test.rb test/integration/mac_run_cap_settings_test.rb test/integration/native_run_claim_ownership_test.rb test/integration/native_sessions_test.rb test/integration/openapi_contract_test.rb test/integration/project_creation_policy_test.rb test/integration/project_overview_contract_test.rb test/integration/rate_limiting_test.rb test/integration/remote_credential_usage_test.rb test/integration/serverless_request_plane_test.rb test/integration/task_run_history_contract_test.rb test/integration/workspace_rule_mac_review_test.rb test/jobs/agent_direction_job_test.rb test/jobs/lease_sweep_agent_status_test.rb test/migrations/blank_retired_usage_message_test.rb test/models/credential_verification_attempt_test.rb test/models/execution_plane_edges_test.rb test/models/execution_start_budget_test.rb test/models/executor_claim_slot_test.rb test/services/agent_batch_landing_test.rb test/services/agent_briefing_test.rb test/services/agent_error_diagnostic_test.rb test/services/agent_landing_test.rb test/services/assistant_coordinator_session_test.rb test/services/assistant_execution_plane_test.rb test/services/assistant_manager_profile_test.rb test/services/auto_assigner_test.rb test/services/campus_manager_conversation_coverage_test.rb test/services/credential_capability_test.rb test/services/credential_diagnostic_test.rb test/services/credential_retry_test.rb test/services/engine_compatibility_test.rb test/services/execution_result_contract_test.rb test/services/executor_broker_contract_test.rb test/services/executor_helper_contract_test.rb test/services/executor_landing_capacity_test.rb test/services/executor_model_updates_test.rb test/services/executor_start_test.rb test/services/git_hub_test.rb test/services/hosted_git_hub_observation_test.rb test/services/hosted_task_run_dispatch_test.rb test/services/landing_capacity_test.rb test/services/manager_sweep_dispatch_alarm_test.rb test/services/manager_sweep_test.rb test/services/model_catalog_coverage_test.rb test/services/model_catalog_test.rb test/services/native_assignment_recovery_test.rb test/services/native_session_import_test.rb test/services/provider_cli_freshness_test.rb test/services/provider_cli_update_contract_test.rb test/services/provider_usage_test.rb test/services/run_directory_test.rb test/services/task_run_history_test.rb test/services/task_transcription_test.rb test/services/visitor_task_projection_test.rb test/services/workspace_rule_review_admission_test.rb
```

Focused core/compatibility rerun (224 tests, 11,002 assertions, zero failures/errors):

```sh
PATH="$HOME/.rbenv/shims:$PATH" api/bin/test --workers 1 --stall-timeout 300 --timeout 900 test/integration/linux_executor_contract_test.rb test/integration/linux_releases_test.rb test/integration/hosted_native_sessions_test.rb test/integration/native_sessions_test.rb test/integration/openapi_contract_test.rb test/integration/executor_credential_models_test.rb test/models/agent_session_island_tenancy_test.rb test/integration/hosted_executor_landing_test.rb:330 test/integration/hosted_executor_landing_test.rb:981 test/integration/hosted_executor_landing_test.rb:1131 test/integration/executor_crash_recovery_test.rb:504 test/services/model_catalog_test.rb:1448 test/services/model_catalog_test.rb:1541 test/integration/workspace_rule_mac_review_test.rb:370 test/integration/workspace_rule_mac_review_test.rb:398 test/integration/workspace_rule_mac_review_test.rb:1062 test/controllers/workspace_rules_controller_test.rb:86 test/integration/project_creation_policy_test.rb:23 test/integration/agent_resume_test.rb:1045 test/services/execution_result_contract_test.rb test/integration/executor_execution_plane_test.rb:682 test/integration/executor_execution_plane_test.rb:704
```

## Cost and remaining proof

New deterministic tests guard unauthorized cross-account import, stale authority, exact
resume versus fresh context, wrong provider scope, unavailable secure storage, unsafe Linux
CLI update eligibility, and immutable package identity. Existing suites did not exercise a
Linux host or hosted native import. Fixtures assert the actual response vocabulary and shape;
no duplicate workflow, recurring notification, source snapshot or paid probe is introduced.
Local suite timeouts are 300–1800 seconds; the core rerun took 190.14 seconds under host load.

LINUX-20261016 owns independent review, different-family review, Council, merge and normal
release deployment. Record merged/deployed SHA and deploy-artifact PR before LINUX-06 live
proof. S2 must export the merged producer, not this branch. See LEDGER.md for exact operations,
capability inventory, Cable revocation gap and required desktop/package receipts.

## Post-merge verification

Merged `origin/main` at `4af90f01d` through merge commit `50cc99907`.
`/tmp/task984-postmerge.log`: 472 tests, 12,479 assertions, zero failures/errors/skips;
157.04 seconds, process exit 0. Includes existing Mac catalog publication/download behavior,
all Linux contracts, existing native import, model/usage bindings, all broad-run failed
scenarios, and the previously lock-exhausted coordinator scenario.

```sh
PATH="$HOME/.rbenv/shims:$PATH" api/bin/test --workers 1 --stall-timeout 300 --timeout 1200 test/integration/linux_executor_contract_test.rb test/integration/hosted_native_sessions_test.rb test/integration/linux_releases_test.rb test/integration/mac_releases_test.rb test/models/mac_release_test.rb test/integration/executor_credential_models_test.rb test/integration/executor_credential_usage_test.rb test/integration/remote_credential_usage_test.rb test/services/provider_usage_test.rb test/integration/openapi_contract_test.rb test/integration/executors_test.rb test/integration/native_sessions_test.rb test/models/agent_session_island_tenancy_test.rb test/controllers/workspace_rules_controller_test.rb:86 test/integration/agent_resume_test.rb:1045 test/integration/assistant_coordinator_sessions_test.rb:3972 test/integration/executor_crash_recovery_test.rb:504 test/integration/executor_execution_plane_test.rb:3534 test/integration/executor_execution_plane_test.rb:3553 test/integration/executor_execution_plane_test.rb:4165 test/integration/executor_execution_plane_test.rb:4430 test/integration/executor_execution_plane_test.rb:4445 test/integration/executor_execution_plane_test.rb:4484 test/integration/hosted_executor_landing_test.rb:1134 test/integration/hosted_executor_landing_test.rb:324 test/integration/hosted_executor_landing_test.rb:981 test/integration/project_creation_policy_test.rb:23 test/integration/serverless_request_plane_test.rb:50 test/integration/workspace_rule_mac_review_test.rb:1062 test/integration/workspace_rule_mac_review_test.rb:370 test/integration/workspace_rule_mac_review_test.rb:398 test/models/execution_plane_edges_test.rb:1032 test/models/execution_plane_edges_test.rb:1119 test/models/execution_plane_edges_test.rb:379 test/models/execution_plane_edges_test.rb:401 test/services/agent_briefing_test.rb:82 test/services/model_catalog_test.rb:1448 test/services/model_catalog_test.rb:1541
```

Self-review corrections: retained old persisted Mac login/stream markers; retained exact
hosted resume after zero-turn failure; used isolated Antigravity model and usage scope;
scoped the Project lookup to the current island; matched claim/disconnect row-lock order
(executor before Office); carried current main disconnect authority forward. Required CI
and coordinator review remain publication gates, not inferred from these local results.

Final lock-order/scope and current-main fleet-copy rerun:

```sh
PATH="$HOME/.rbenv/shims:$PATH" api/bin/test --workers 1 --stall-timeout 180 --timeout 600 test/integration/hosted_native_sessions_test.rb test/integration/executors_test.rb test/integration/openapi_contract_test.rb
```

`/tmp/task984-final-adjustments.log`: 127 tests, 10,077 assertions, zero failures/errors/skips,
17.26 seconds, process exit 0. RuboCop inspected 159 changed Ruby files and identified only
three formatting corrections, applied without behavior changes. Architecture, fragment and
candidate export receipts are recorded on the PR at its exact head. Candidate export is not
a merged-producer or deployment receipt.

## Consolidated review return (comment 10309 / PR comment 6213772592)

Retained base/head: 4af90f01d75ad2ff4f66db13ad8eb4795fdef7a3 /
dae15440af6cceaabc32f09418ecb5c5c03eb56f. No prior commit was replaced or discarded.
The full follow-up diff and affected authority/lease/catalog call sites were self-reviewed;
the original full-diff review and independent review dispositions remain in PR1552.
No speculative delegated-token or advisory-lock change was made.

All five findings first reproduced in `/tmp/task984-review-red.log`: 35 tests,
208 assertions, 9 failures, zero errors, exit 1. The failures prove post-revoke delivery,
locked-store selection/lease exposure, the Mac warning, contradictory parity evidence and
public digest disclosure. A first correction run exposed two compatibility assertions;
the executor null guard was narrowed to serialization and the cookie/native test now
checks identical public identity with separate revocable session authority.

`/tmp/task984-review-final.log`: 306 tests, 10,731 assertions, zero failures/errors/skips,
14.74s assertion execution, process exit 0. Command (fresh owned disposable database):

```sh
PATH="$HOME/.rbenv/shims:$PATH" api/bin/test --workers 1 --stall-timeout 180 --timeout 360 test/channels test/integration/linux_executor_contract_test.rb test/integration/linux_releases_test.rb test/integration/hosted_native_sessions_test.rb test/models/credential_verification_attempt_test.rb test/integration/openapi_contract_test.rb
```

New coverage includes HTTP secret leases, registration rotation, a callback-free revoke
committed on a separate PostgreSQL backend, actual default stream handlers, backfill,
password/role/disabled changes, expiry, idle policy and valid sibling sessions. These are
bounded deterministic regressions at existing boundaries, with synthetic credentials and
no paid probes, recurring workflows or notification changes. Per-payload uncached authority
reads are an intentional security cost. See LEDGER.md for the precise in-flight-frame limit;
this is not production network or desktop acceptance. No coverage-percentage claim is made.

Required CI, fresh independent review, Council and merge belong exclusively to
LINUX-20261016. This continuation does not watch CI, mark ready, merge or arm auto-merge.

Final affected rerun: `/tmp/task984-review-complete.log`, **344 tests / 11,355 assertions,
zero failures/errors/skips, exit 0**, 77.76s assertions under host load. Same command as above
plus `test/integration/credential_verification_attempts_test.rb`, with `--timeout 300`.
It also covers unknown host-version changes between claim and lease and a revoke during
backfill construction. An intermediate targeted run had one test-helper error (missing
Object#stub support), corrected by requiring the existing helper; that run is not a pass.

Final admin-token rotation race and hosted-admin compatibility rerun:
`PATH="$HOME/.rbenv/shims:$PATH" api/bin/test --workers 1 --stall-timeout 180 --timeout 180 test/channels/connection_test.rb`
(`/tmp/task984-review-admin-final.log`): **17 tests / 33 assertions, zero failures/errors/skips,
exit 0**. The retained binding hashes the presented token, so rotation during connect cannot
capture the replacement credential. Assistant authority remains independently restricted.

RuboCop: 18 changed Ruby files, no offenses (`/tmp/task984-review-style-final.log`).
Contract integrity, architecture policy, release-fragment policy and `git diff --check` passed.
No changes to CI, policy controls, deployment, client code or previous commits.

## Second review return: fresh execution credentials after a Linux store lock

The follow-up preserves head `69b38133db9dd5bf21e82b63871dedc7f0753b63` and every
prior commit. It fixes the host-elevated fresh-secret finding at ordinary execution
credential delivery, without changing claim ownership, `/start` receipts or existing-child
reporting. OpenAPI and LEDGER.md describe the serialized current-row check and byte-recall
limit. The controller also gates fresh coordinator MCP bearer creation in the same payload.
The hardened-review lease was inspected: it returns status/cancellation metadata, not
provider secret material. Verification already checks under the executor row lock.

Evidence directory:
`/Users/yuri/.campus/coordinate/linux-20261016/fixes/server-pr1552/fix-evidence/`.
`commands.txt` records exact commands, selected tests, runner-owned database names and
intermediate setup corrections. All tests use Ruby 3.4.10, one worker, fresh disposable
runner-owned databases and explicit bounds; no real credentials or paid provider calls.

- `secret-red.log`: 7 tests / 74 assertions, 7 expected failures, zero errors. Each failure
  is an actual credential response after a store/host transition or stale authentication
  snapshot. The unlocked-path test also proves the post-start lock boundary.
- `secret-green-fixture-correction.log`: 6 refusal cases pass; the seventh reaches an invalid
  terminal-state fixture (`succeeded`). The fixture is corrected to the existing
  `completed`/`provider_completed` contract. This intermediate run is not a pass.
- `secret-focused-path-correction.log`: an incorrect MCP test-file directory stopped that
  invocation before assertions. An earlier unsupported runner `--name` option also stopped
  before execution. Neither is counted as behavioral evidence.
- `secret-focused.log`: the broad 9-file run reached its 480-second absolute limit while
  still emitting progress, exit 124. No failure/error block or complete result was emitted;
  it is not a full-suite pass. The runner stopped it before the fresh final database run.

The final selection reuses the execution-plane suite for all new regressions plus legacy
Mac credential injection, credential revocation/replacement, terminal credential refusal,
start/heartbeat/events/finish, cancellation/reconciliation and executor revocation. It also
runs the complete Linux executor, verification HTTP/model, hosted/local native and OpenAPI
suites. The private selector changes only test selection, not fixtures or application code.
These seven new deterministic regressions prevent observed secret disclosure and protect
already-created-child receipts; they add no paid probes, workflows or notification cost.

Final result: `secret-boundary-final.log`, **218 tests / 11,309 assertions, zero
failures/errors/skips, exit 0**, 99.77 seconds of assertions. Command:

```sh
PATH=/Users/yuri/.rbenv/shims:/Users/yuri/.rbenv/bin:$PATH RBENV_VERSION=3.4.10 RAILS_ENV=test DATABASE_URL=postgres:///campus_test_pr1552_secret_boundary_20261016 api/bin/test --workers 1 --no-verbose --stall-timeout 120 --timeout 180 ../fix-evidence/secret_boundary_compatibility_test.rb test/integration/linux_executor_contract_test.rb test/integration/credential_verification_attempts_test.rb test/models/credential_verification_attempt_test.rb test/integration/hosted_native_sessions_test.rb test/integration/native_sessions_test.rb test/integration/openapi_contract_test.rb
```

RuboCop inspected both changed Ruby files with no offenses. Contract integrity, architecture
policy and `git diff --check` passed. The new diff and surrounding heartbeat/claim/start,
credential verification, coordinator MCP issuance and hardened-review lease paths were
reviewed; the prior complete-candidate independent review remains part of PR1552's record.
No unrelated fixes, policy/CI changes, generated release files or prior commits were changed.
LINUX-20261016 remains sole owner of fresh review, CI, readiness, Council, merge and deploy.

## Third review return: native import and model catalog lock order

This narrow repair retains `7c5c0645dcebc6b939e6dfb6d7f76aa0a0cb6da3` and every prior
commit/fix. `ModelCatalog#issue_local_discovery` and `#ingest_local_observation` now lock
the requested credential before the binding, matching native import and binding verification.
Binding reload, fresh association reads, authorization, generation, expiry and one-time ticket
checks remain inside both locks. No retries, swallowed database exceptions, global lock
redesign, provider I/O or changes to `/start`, credentials, reporting or cancellation were added.

Evidence directory:
`/Users/yuri/.campus/coordinate/linux-20261016/fixes/server-pr1552-lock/fix-evidence/`.
The two committed regressions execute the actual native completion service concurrently with
valid model discovery or ingestion on separate PostgreSQL connections. A per-instance barrier
pauses native completion after its real credential lock; an uncached `pg_stat_activity` read
confirms the catalog backend is waiting for the credential before releasing native completion.
Waiting for the old catalog binding barrier would deadlock the corrected test itself, because
the catalog must now acquire the credential first. The test therefore observes the actual SQL
wait and adds no row locks. Workers use 5-second SQL timeouts, 8-second barrier bounds and
12-second joins with bounded teardown. Both native attachment and catalog success are asserted.

- `lock-red.log`: initial probe, 2 tests / 2 assertions, one genuine discovery deadlock failure
  and one ingestion synchronization timeout. This is not a passing or complete red receipt.
  Repeated observer queries could reuse Rails' query cache; the observer was made uncached.
- `lock-red-uncached.log`: unchanged production code, **2 tests / 4 assertions, 2 actual
  `ActiveRecord::Deadlocked` failures, zero errors/skips**, exit 1, 3.60 seconds of assertions.
  Discovery and ingestion both demonstrate the credential/binding cycle.
- `lock-affected-green.log`: corrected lock order, **432 tests / 12,851 assertions, zero
  failures/errors/skips**, exit 0, 89.36 seconds of assertions. The runner owned and cleaned
  `campus_test_run_tn00kh_xwn_r03ccc70b`; no shared test, development or production DB was used.
- `lock-affected-final.log`: after explicit island scoping and a monotonic observer deadline,
  **432 tests / 12,851 assertions, zero failures/errors/skips**, exit 0, 104.95 seconds of
  assertions. Private database: `campus_test_run_tn00qb_1jin_r641619c4`; all workers exited.

Actual final command (Ruby 3.4.10, existing dependencies, one worker):

```sh
PATH=/Users/yuri/.rbenv/shims:/Users/yuri/.rbenv/bin:$PATH RBENV_VERSION=3.4.10 RAILS_ENV=test DATABASE_URL=postgres:///campus_test_pr1552_lockfix_final_20261016 api/bin/test --workers 1 --no-verbose --stall-timeout 120 --timeout 300 test/services/native_model_lock_order_test.rb test/integration/hosted_native_sessions_test.rb test/integration/native_sessions_test.rb test/services/model_catalog_test.rb test/models/executor_credential_model_catalog_test.rb test/integration/executor_credential_models_test.rb test/integration/executor_credential_bindings_test.rb ../fix-evidence/secret_boundary_compatibility_test.rb test/integration/linux_executor_contract_test.rb test/models/credential_verification_attempt_test.rb test/integration/credential_verification_attempts_test.rb test/integration/openapi_contract_test.rb
```

The retained selector includes the prior seven store/version/stale-authentication credential
regressions, legacy Mac delivery, credential revocation and replacement, terminal guards,
existing-child start/heartbeat/events/finish, cancellation and reconciliation. Full native,
catalog, binding, verification, Linux platform and OpenAPI suites accompany it. The two new
bounded tests guard an independently reproduced server error; no paid probe or new recurring
automation is introduced. RuboCop on both changed Ruby files, contract integrity and whitespace
checks pass. No coverage-percentage, live desktop/provider or deployed-network claim is made.

The nonblocking P3 is documented in OpenAPI and LEDGER.md: #986 hands back an unstarted
secure-store-refused attempt with the advertised `executor_admission_paused` reason and bounded
terminal delivery policy; unlocking helps only while the lease and credential remain usable.
No lease-renewal or refusal policy changed. The previous raw external verdict remains separately
preserved in `reviews/server-pr1552/review-evidence/7c5c0645/anthropic-review.txt`; this local repair
does not relabel that review. LINUX-20261016 owns fresh independent review, canonical CI,
readiness, Council, merge, deployment and the unchanged #984 → #985 → #986 → #988 handoff.


## Native usage and deletion lock repair (LINUX-20261016)

The review of `dcc1f49a` reproduced a native-import/remote-usage deadlock: native held
executor `FOR UPDATE` while usage held the credential and its first executor assignment
needed an implicit foreign-key `KEY SHARE` lock. A second actual-service regression also
reproduced the review's credential-deletion concern: deletion held the credential before
nullifying the Office, opposite native's Office-before-credential order.

Hosted completion now locks executor → credential → Office → Project → bindings, with
`FOR NO KEY UPDATE` on executor and credential. This still excludes registration writes,
revocation, credential edits and deletion, while allowing foreign-key checks from usage
assignment and Office rebinding. The executor-before-Office and credential-before-binding
orders remain intact. Agent execution's advisory lock serializes handoff for the same Office;
claim and disconnect take the executor first. Project observation takes Project before its
binding and its executor foreign-key check is compatible with the new executor lock.
All fresh reloads, current-island selection, registration HMAC, active credential and binding
checks remain inside the locked section. No retry or exception masking was introduced.

`NativeAuthorityLockOrderTest` uses real `RemoteCredentialUsage.request`, credential destroy,
Office update and `HostedNativeSessionTransport.complete` calls. Per-instance barriers pause
only after the real locks; uncached PostgreSQL activity establishes the competing wait before
release. It asserts successful usage/import and rebinding/import, or deletion with the waiting
import reporting the deleted record and creating no session. SQL timeout is 10 seconds,
barrier bounds 8 seconds, joins 12 seconds, and result collection 1 second. Teardown joins
are bounded and restores each connection's timeout.

The evidence directory is
`/Users/yuri/.campus/coordinate/linux-20261016/fixes/usage-evidence`:

- `red.log`: original product code, 2 tests / 5 assertions / 2 failures / 0 errors;
  both failures are actual `PG::TRDeadlockDetected`.
- `credential-fk-red.log`: partial reorder retaining credential `FOR UPDATE`,
  3 tests / 13 assertions / 1 failure / 0 errors. Usage and deletion passed, but the real
  Office rebind foreign-key check deadlocked. This proves why a blind reorder is insufficient.

- `affected-green.log`: complete correction, **460 tests / 13,015 assertions**, zero
  failures/errors/skips, exit 0, 75.35 seconds. Native/model lock races, hosted and local native
  HTTP, catalog/binding/verification, platform, OpenAPI, remote usage and the prior execution
  credential selection passed.
- `root-selected-green.log`: the coordinator's previous 14 authority cases plus these three
  races, **17 tests / 193 assertions**, zero failures/errors/skips, exit 0, 7.51 seconds.
  This also reruns the final bounded result collection. Exact commands are in `commands.txt`.

These bounded regressions prevent observed database errors; they are synthetic service
verification, not live Linux/provider/deployment evidence. D1–D7 and the existing S1-5 live
proof ownership remain unchanged. The coordinator owns independent review, CI and landing.


## Canonical CI follow-up at 600a517 (2026-10-16)

The actual API job in run 38898261458 exposed stale computer-copy assertions, an omitted
islandless release-catalog review entry, two unsupported native operation schemas, a legacy
migration test that discarded a later native-executor foreign key, and a cross-process test
connection that overrode libpq's CI password with an explicit nil. The API job reported
13873 tests, 8 failures, 1 error and branch coverage 26559/26855 (28 short).

Hosted native plans/reports now use additive GET/POST
`/agents/{id}/native_session_transport`, classified `private_protocol`. The original
`agentsNativeSessions` and `agentsNativeSessionAttach` remain invokable with their legacy
Mac HTTP schemas and attach confirmation. Real HTTP tests exercise legacy Coordinator
invocation and confirmed attachment, while the private route cannot be discovered or saved
as an operation request. All signed authority, registration/island/account/binding checks,
lock order, no-store and request redaction remain intact. The gateway manifest and resource
count companion include the one new path resource. No Linux consumer snapshot has shipped.

Focused isolated verification used one worker with a 120-second inactivity bound and
480-second absolute bound; no full local Rails suite or stress run. The 19 affected-file run
completed 486 tests and 13119 assertions with only one new test expectation failure: native
attachment correctly returned 201 rather than the test's expected 200. That assertion was
corrected, then the complete native HTTP, native importer and broker contract files passed
36 tests and 342 assertions with zero failures/errors/skips. The 19-file run otherwise
passed every original CI failure and both native authority lock suites.

An explicit historical-schema regression fails against the previous test cleanup (1 test,
1 assertion, missing native executor FK), then passes with preservation of current foreign
keys. The cross-island native write still raises the database foreign-key exception; no
migration or RLS rule was weakened. Cross-process Cable revocation still commits on a real
second PostgreSQL backend, whose distinct pid is now asserted.

The CI artifact's actual missed branches drove bounded tests for native authority refusal,
malformed host/release evidence, Cable heartbeat/action revocation, account-bound usage,
unsupported native resume, and local-control plans without a selected host. Comparing the
same production source branch keys records 31 formerly uncovered branches exercised (the
controller whose lines moved is excluded). This is targeted behavioral evidence, not a
claim that the full canonical 99% coverage gate has passed.

Contract integrity, architecture snapshot, modified Ruby style, and the focused AWS gateway
resource test pass. AWS dependencies were reused read-only from an existing checkout after
checking versions against this lock; no install or reference-tree edit. All owned isolated
test databases were verified absent after runner teardown. Detailed commands, red/green
logs, coverage deltas and cleanup receipts are in the coordinator's private
`fixes/server-pr1552-ci-evidence/HANDOFF.md`. Canonical CI and root's fresh independent
review remain required before landing. Deferred card #1030 work is unchanged.

## Boundary repair after independent review of `1a0f6c0c`

F1: explicit host observations survive omission under the current executor row lock, including
unknown versions. The platform cannot change on the same installation. Genuine never-explicit
Mac installations retain compatibility. HTTP regressions withhold verification and existing-attempt
secrets after omission or downgrade; a stale authenticated snapshot cannot erase a newer host.

F2: readiness and claim resume policy receive the actual executor. Enqueue and old queued claims
refuse a different imported executor; native capability and the imported Project folder are checked
before delivery. Existing credential binding readiness retains account/scope proof. Tests cover A
selected/imported with B requested (including B missing native capability), an old B queue entry,
claim-time capability loss, changed Project folder, and a successful exact-resume claim.

F4: account deletion returns the model-authored 422 refusal before its audit/delete when an owned
executor retains native conversations. The executor association restricts deletion and never
nullifies native identity. Deletion locks owned executors before deciding, serialized with hosted
import; a real two-connection import/deletion race first returned generic409 and now returns the
specific refusal without deletion or audit. No migration is changed.

Test quality: the queued cancellation fixture now uses a validated continuation plus an actual
Project selection change, with exact `task_ownership_lost` terminal reason and cancel cause.
The limit-reset case has valid workspace identity and asserts `request_selection_changed` and
no cancel cause rather than passing through an unrelated protocol rejection.

All commands use `PATH=/Users/yuri/.rbenv/versions/3.4.10/bin:$PATH RAILS_ENV=test`, default
owned disposable database isolation, `--workers 1`, and explicit timeouts. Logs are retained at
`/Users/yuri/.campus/coordinate/linux-20261016/fixes/server-pr1552-boundary-clean/fix-evidence/`.

- `api/bin/test --workers 1 --timeout 240 test/integration/linux_executor_contract_test.rb test/integration/hosted_native_sessions_test.rb`: initial prevention run, **43 tests / 350 assertions / 7 expected failures**, zero errors. `before.log`. Intermediate runs are retained as non-passes; one exposed the old legacy fixture that explicitly erased a known Linux host, and one exposed the reset fixture's missing workspace identity. Two new no-store error-header assertions were removed because the pre-existing verification refusal contract uses no-cache and carries no secret; this repair does not change that contract.
- `api/bin/test --workers 1 --timeout 300 test/integration/linux_executor_contract_test.rb test/integration/hosted_native_sessions_test.rb test/models/user_deletion_test.rb test/integration/native_sessions_test.rb test/services/native_session_import_test.rb test/integration/credential_verification_attempts_test.rb test/models/credential_verification_attempt_test.rb test/integration/openapi_contract_test.rb`: **238 tests / 11,505 assertions**, zero failures/errors/skips, exit0. `boundary-suite.log`.
- `api/bin/test --workers 1 --timeout 240 test/integration/executor_execution_plane_test.rb:5359:5378:5394:5406:5428:5441:5472:4949:4972:4624 test/integration/agent_resume_test.rb test/integration/marketing_deletion_test.rb`: **84 tests / 1,296 assertions**, zero failures/errors/skips, exit0. `delivery-compatibility.log`.
- `api/bin/test --workers 1 --timeout 180 test/integration/marketing_deletion_concurrency_test.rb`: race prevention before the lock repair, **3 tests / 16 assertions / 1 expected failure**, zero errors. `deletion-race-before.log`.
- `api/bin/test --workers 1 --timeout 240 test/integration/marketing_deletion_concurrency_test.rb test/integration/linux_executor_contract_test.rb test/integration/executors_test.rb test/models/executor_coverage_test.rb`: final validated-fixture, registration and race checks, **48 tests / 353 assertions**, zero failures/errors/skips, exit0. `registration-deletion-final.log`.

These focused deterministic checks prevent observed secret delivery, wrong-host native resume,
identity loss and misleading cancellation evidence. They reuse existing suites and one existing
concurrency harness; no new runner, paid probe, notification, coverage policy or threshold change.
Root LINUX-20261016 owns fresh independent review, canonical CI, Council and merge. This repair
author does not mark ready, merge, deploy, or start a watcher.

### Registration residual after `3c982656`

Independent review found the HTTP registration precheck was judging a new transient executor
before the model restored its persisted host. Same-installation Linux re-registration could
therefore rotate its token with host omitted and the store locked, or host/store both omitted.
The model now validates the effective retained host and incoming store under its existing
user-before-executor locks, before token generation, digest assignment or save. The controller
renders the existing 422 `registration: SecureStoreDiagnostic` envelope from that refusal.
The earlier direct-model test no longer expects locked-store re-registration to succeed.

- Red: `PATH=/Users/yuri/.rbenv/versions/3.4.10/bin:$PATH RAILS_ENV=test api/bin/test --workers 1 --timeout 180 test/integration/linux_executor_contract_test.rb`. **23 tests / 171 assertions / 2 failures / 1 error**, exit1. Both HTTP regressions returned200 instead of422. The direct-model test also raised `NameError: uninitialized constant Executor::RegistrationRefused` because the new refusal type was not implemented yet. Raw log: `fix-evidence/registration-residual-before.log`.
- Green: `PATH=/Users/yuri/.rbenv/versions/3.4.10/bin:$PATH RAILS_ENV=test api/bin/test --workers 1 --timeout 240 test/integration/linux_executor_contract_test.rb test/integration/executors_test.rb test/integration/hosted_native_sessions_test.rb test/integration/openapi_contract_test.rb`. **165 tests / 10,595 assertions**, zero failures/errors/skips, exit0. Raw log: `fix-evidence/registration-residual-final.log`.
- `bundle exec rubocop app/models/executor.rb app/controllers/executors_controller.rb test/integration/linux_executor_contract_test.rb` from `api/`: three files, no offenses. Contract integrity, architecture and whitespace checks pass.

Both regressions assert no returned token, unchanged stored digest and capabilities, continued
validity of the old token after refusal, and successful same-id recovery/rotation when the
incoming store is unlocked. Existing genuine legacy Mac registration and native resume tests
pass. No tokens are logged. The focused tests guard the two observed registration bypasses;
no schema, dependency, version, coverage-policy or unrelated product change is introduced.

### Malformed host recovery after `5f9142ba`

The platform immutability guard previously pinned any explicit host key, including an object
without a platform. That malformed first registration received a token, but a corrected Linux
heartbeat or same-installation registration could never establish a platform. Explicit hosts
now require an object with a nonblank string platform before validation permits persistence or
registration token issuance. Historical malformed rows may recover through an explicit valid
report; their omission remains unsupported. Nonblank string identities, including unsupported
platform names, stay immutable. Unknown contract versions may recover on the same platform.

Evidence is retained in
`/Users/yuri/.campus/coordinate/linux-20261016/fixes/server-pr1552-host-recovery/fix-evidence/`.
Both Rails runs use default owned disposable database isolation and the same Ruby environment.

- Red: `PATH=/Users/yuri/.rbenv/versions/3.4.10/bin:$PATH RAILS_ENV=test api/bin/test --workers 1 --timeout 240 test/integration/linux_executor_contract_test.rb`, **27 tests / 208 assertions / 4 failures / zero errors**, exit1 (`host-recovery-before.log`). Malformed creation persisted an executor; both historical-host cases accepted another malformed retained observation. The fourth failure was an overly broad test assertion: authenticated heartbeats intentionally touch `last_seen_at` before model validation. That assertion now excludes only the authentication timestamp; no heartbeat-authentication behavior changed.
- Green: `PATH=/Users/yuri/.rbenv/versions/3.4.10/bin:$PATH RAILS_ENV=test api/bin/test --workers 1 --timeout 240 test/integration/linux_executor_contract_test.rb test/integration/executors_test.rb test/integration/hosted_native_sessions_test.rb test/integration/openapi_contract_test.rb`, **169 tests / 10,667 assertions**, zero failures/errors/skips, exit0 in 11.03s (`host-recovery-final.log`).
- `bundle exec rubocop app/models/executor.rb test/integration/linux_executor_contract_test.rb` from `api/`: two files, no offenses. `ruby scripts/architecture/contract_check`, `bin/architecture --base e938b618f77fc727df05e022cf0f9b83e1057eb2 --head HEAD`, the release-fragment guard against that base, gitleaks and whitespace checks pass on the final commit.

The HTTP cases cover null/scalar/array hosts, missing/nonstring/blank platforms, refusal with
no row or token, corrected registration using the same installation id, explicit historical
heartbeat and registration recovery, and locked recovery preserving every stored registration
field and the old token. Unknown string platforms cannot be changed or omitted into legacy Mac
eligibility, while an unknown version can recover on its unchanged Linux identity. Existing
omitted-host locked/unknown-store refusal, exact native resume, account-deletion protection and
genuine legacy Mac tests remain green. The prior F1/F2/F4 fixes and D1-D7 remain unchanged.

These deterministic cases prevent permanent registration failure and unsafe identity relaxation
at existing HTTP boundaries, with no new suite, runner, paid probe, recurring check or coverage
change. Both owned test databases were verified absent after teardown. Generated coverage from
this new worktree was removed after runner exit; raw failure evidence is retained. No full-suite
coverage or deployment claim is made. Root LINUX-20261016 remains the sole owner of independent
review, canonical CI, Council, readiness, merge and deployment; this author leaves the PR draft.

### Historical-host revocation return after `01179ebd`

Independent review identified that model-wide host validation also blocked `Executor#revoke!`:
disconnect returned 422, and `User#revoke_sessions_after_security_change` raised during password
rotation. The validator now allows only a persisted active executor becoming revoked with a
cleared token and unchanged capabilities. `revoke!` itself is unchanged, including its row
locks, queued/live work settlement, Office parking/unbinding and transaction. Registration and
heartbeat still validate malformed observations even when the capabilities value is unchanged.

Raw evidence remains in the same `fix-evidence/` directory as the preceding repair:

- Red: `PATH=/Users/yuri/.rbenv/versions/3.4.10/bin:$PATH RAILS_ENV=test api/bin/test --workers 1 --timeout 240 test/integration/linux_executor_contract_test.rb`: **31 tests / 293 assertions / 1 failure / 2 errors**, exit1 (`historical-revocation-before.log`). HTTP disconnect returned 422 instead of 204. The real User security callback and the revoked-registration setup raised the same `ActiveRecord::RecordInvalid` from `Executor#revoke!`; these are the reproduced defect, not environmental failures.
- Green: `PATH=/Users/yuri/.rbenv/versions/3.4.10/bin:$PATH RAILS_ENV=test api/bin/test --workers 1 --timeout 240 test/integration/linux_executor_contract_test.rb test/integration/executors_test.rb test/integration/hosted_native_sessions_test.rb test/integration/openapi_contract_test.rb`: **173 tests / 10,711 assertions**, zero failures/errors/skips, exit0 in 10.32s (`historical-revocation-final.log`).
- RuboCop, two changed Ruby files, no offenses. Actual `bin/architecture --base e938b618f77fc727df05e022cf0f9b83e1057eb2 --head HEAD`, route/spec contract integrity, the release-fragment guard, candidate-range gitleaks and whitespace checks pass on the final commit.

The new HTTP case proves token removal, queued-work settlement, Office unbinding/card parking,
unchanged historical observations and repeated versioned disconnect. Password rotation exercises
the real User callback and clears human sessions plus executor authority. Both active and revoked
historical rows reject same-id registration with either omitted or repeated malformed capabilities,
return no token, and preserve every stored field. These four deterministic cases guard the actual
revocation regression and prevent a capabilities-dirty-only repair from reopening registration.
All F1/F2/F4, malformed-host recovery, platform identity and legacy Mac cases remain green.

The shared host fell below the original 20GiB floor after the red run. The coordinator authorized
one bounded four-file Rails run with at most 512MiB new owned DB/coverage/log allocation and an
18GiB free-space stop, without changing VM/build/download limits. No duplicate test ran. The
resource receipt records 20,875,272,192 free bytes before the run, observed database samples up
to 21,354,163 bytes, generated coverage of 45,284KiB and log growth of 3,072KiB. The database
figures are sampled observations, not a claim of continuous peak measurement. The host remained
above the exception's 18GiB bound in the recorded samples and before/after measurements.
`historical-revocation-resources.txt` retains the measurements. Both owned red/green databases
were absent after teardown; generated coverage was removed and raw logs preserved. No unrelated
data, process, dependency, build or VM was touched. Root remains the sole delivery observer.
