# Linux S1 contract ledger

Task #984; reserved coordinator **LINUX-20261016**. Producer repository:
`yuric/campus-server`. Implementation starts from merged main
`4050498fd4556d1cf1cba9f87a6106b5467283be`. Source requirements:
`yuric/campus-linux@e496ac2f756a8656575ec2474b771567f2f68e56`, PRD D6 and
`docs/implementation-gates.md` G1–G8. No predecessor producer is assumed from a closed card.

This is code-contract evidence. It is **not deployment or a Linux desktop/provider receipt**.
LINUX-06 (#986) owns the real hosted login/verify/input/cancel and execution round trip.

## Requirements and authority

| Requirement | Rails producer and consumer contract |
|---|---|
| S1-1 | Runtime credential capability/diagnostic, binding, verification-attempt, execution readiness/helper, and CLI freshness/update copy uses computer/helper wording. Compatible engine, mechanism, operation, reason and route identifiers stay unchanged. `TaskTranscription.capability(platform:)` preserves the existing Apple speech contract when absent/macos; Linux/unknown returns unsupported with Rails wording. No provider, spending or privacy fallback is selected. |
| S1-2 | `ExecutorPlatform` reads versioned `capabilities.host`; only installations that have never reported a host retain the legacy Mac root policy. Explicit host observations survive omission; changing platform for the same installation is refused. Linux requires canonical absolute `state_home` and `<state_home>/Campus/production/workspaces`. Claim v2, leases, heartbeat, reports, fixed token injection and the five-device account cap stay intact. `provider_isolation` reports actual provider storage, not merely a cwd/scope echo. Linux Antigravity model discovery and usage (direct and heartbeat-reserved) use credential_isolated and the verified scope; legacy Mac/ambient model discovery remains machine_shared. Compatible agy_cli_mac/codex_app_server_mac source identifiers are retained. Existing Apple-signature CLI updater authorizations are withheld for Linux; manual vendor guidance remains. |
| S1-2 native | Private GET `/agents/{id}/native_session_transport` returns a hosted local-read plan when an owned bound executor is selected. POST `/agents/{id}/native_session_transport` accepts its signed authority and observation. The existing native discovery and attach operations retain their invokable Coordinator and Mac contracts; the additive host protocol is excluded from model tools. Scope is fixed to account/island/executor registration/Office/credential binding revision/Project binding revision/operation/session id, expires after five minutes, and is revalidated before import. Exact Project path is checked against the verified binding. Import records the executor; another computer, missing session, changed credential or unsupported version refuses. Claims retain legacy native fields and add `native_resume` with `failure_policy: refuse`. |
| S1-3 | `Executor.secure_store` supplies separate `secure_store_absent` and `secure_store_locked` warning messages. Linux claims also refuse unknown/unsupported store observations. GET `/executors?platform=linux&secure_store_version=1&secure_store_state=locked` returns the diagnostic before registration. POST registration refuses absent/locked/unknown Linux stores without minting a token. The host must withhold registration and persistent token storage locally when its store is absent/locked; server diagnostics do not authorize a plaintext fallback. |
| S1-4 | Existing administrator-only `/admin/mac_releases` accepts a separate `linux_release` envelope and adds `linux_releases` to listings. `LinuxRelease` preserves immutable stable identity, four package/architecture entries, operator signature/key identity and per-artifact evidence/gaps. No Mac artifact changes, signing keys, uploads or new update channels. `Executor.linux_release` diagnoses catalog/installed identity separately from protocol compatibility and selects the installed package format and architecture. |
| S1-5 | GET/PUT `/executors/{executor_id}/credential_bindings/{credential_id}` already provides hosted login and verification without Rails localhost. `local_control.session_transport` makes local status/input/cancel operations explicit and keeps one login id bound to the credential scope. The local helper owns the PTY and write-only input. Existing `broker_login` routes remain guarded by `local_execution`; they are not hosted fallback. API-key verification retains its one-time executor claim/lease/complete protocol. |

The runtime-copy audit and retained compatibility cases are in [COPY_AUDIT.md](COPY_AUDIT.md).

## Capability and observation inventory

Registration and heartbeat carry the same capabilities object. Versions below are exact
unless the existing service says otherwise. Do not advertise an operation before its Linux
implementation and failure paths exist. Schema gaps below are now explicitly typed in
`ExecutorRegistration.capabilities`; no compatible Mac wire identifier was renamed.

| Wire field / source | Contract and Rails consumer | Linux observation source / obligation |
|---|---|---|
| `host` | v1, `ExecutorPlatformObservation`, `ExecutorPlatform` | Installed host OS, process architecture and resolved XDG state home; no Rails-host inference. |
| `secure_store` | v1, `SecureStoreObservation` and `SecureStoreDiagnostic` | Real Secret Service backend state in the graphical session; absent, locked, unlocked or unknown. |
| `linux_release` | v1 package identity; `LinuxReleaseDiagnostic` | Installed deb/AppImage identity alongside app_version/build and host.arch. |
| `broker` | Boolean; `CredentialVerificationAttempt` | Authenticated running local helper, not its presence on disk. |
| `architectures` | Legacy array, not readiness authority | Existing Mac compatibility only; Linux reports host.arch. |
| `workspace_root` | String; `ExecutionReadiness`, claim `workspace.root` | Canonical host-resolved root, symlink/race confinement enforced locally. |
| `credential_scope_execution` | v1; `ExecutionReadiness` | Local helper accepts scope-only execution and derives storage under its trusted product root. |
| `broker_execution_capacity` | v1; `ExecutorExecutionCapacity` | Actual running helper capacity protocol. Never infer from app version. |
| `resource_observation` | v1 cores/available-memory/time; `ExecutorResourceObservation`, capacity/landing services | Fresh OS CPU and available-memory sample. Unknown memory is omitted, not zero or guessed capacity. |
| `resource_observation_received_at` | Rails timestamp, read-only | Server overwrites it on resource-bearing heartbeat and discards client receipt clocks. |
| `executor_helper` | v1; `ExecutorHelperContract` | Bundled/installed helper digests/builds and bounded install failure from real installation receipts. Running-image identity versus replaced files remains Linux live-proof work. |
| `helper_update_monitor` | v1; `ExecutorHelperContract` | Running helper can observe replacement, stop/report, confirm and hand back before promotion. |
| `cli_versions` | v1 raw engine version lines and path/resolved_path installs | Authenticated adapter resolves approved CLI; Rails parses and judges freshness. |
| `cli_updates` | v1 operations/checks; `ProviderCliUpdateContract` | Existing v1 requires Mac signature verification. Linux cannot earn an update action merely by advertising these names. A future Linux updater is a new server producer before consumer. |
| `credential_verification_attempt` | v1 plus broker=true; `CredentialVerificationAttempt` | API-key one-time claim, lease and normalized completion, no secret replay. |
| `credential_usage_refresh` | v1; `RemoteCredentialUsage` | Fenced credential usage collection and observation. |
| `github_pr_observation_version` | Integer 1; `HostedGitHubObservation` | Bounded authenticated read ticket/report protocol. |
| `workspace_adoption` | v1; `AgentResume` | Verified retained checkout adoption. |
| `workspace_quiescence` | v1 plus adoption v1; `AgentResume` | Proven absence of processes using the retained workspace before automatic handoff. |
| `assistant_coordinator` | v1; `AssistantCoordinatorSession` | Dedicated coordinator work handling. |
| `campus_mcp_v1` | v1 and engines array; `Setting` | Per-engine MCP adapter, fixed attempt credential and declared tool profile. |
| `hardened_review_contract_version` | Existing integer >=1; `HardenedReviewHostContract` | Real hardened review sandbox/report implementation. |
| `manager_tool_free` | Retired v1 observation; ignored by Rails | Do not revive its retired execution semantics. |
| `native_sessions` | v1, new hosted plan/report gate | Credential-isolated provider discovery/read/exact resume. |
| binding `observation.provider_isolation` | v1 `provider_config` plus exact scope | Actual provider token/config isolation. Antigravity is not deemed isolated because a working directory exists. |
| binding `observation.identity` | Existing v1 revision/provenance; `CredentialIdentity` | Provider account/organization facts, hashed and discarded by Rails. Authentication success alone is not identity proof. |
| `work_contract` capability / claim `execution.work` | `ExecutionRequest#work_contract`; Office v1, assistant/coordinator v2 | Honor workspace/tool/output rules verbatim; withhold unknown required versions. |
| heartbeat `delivery` | v1 `ExecutorDeliveryReport` | Durable outbox counters: heartbeat_failures, event_failures, terminal_failures, cancellation_failures, outbox_replays. These are observations, not acknowledgments. |
| claim `delivery_policies`, `terminal_delivery`, `helper_update` | Existing typed claim contracts | Preserve retry/acknowledgment/stop grace/confirmation windows; provider exit is not terminal acknowledgment. |

## Fresh execution credential delivery

GET `/executor/attempts/{id}/credential` rechecks `ExecutorPlatform.refusal` on the
current executor row under its lock, serialized with heartbeat writes. Linux store
locked/absent/unknown (including missing or unsupported observations), and explicit
unsupported host contracts, return 409 without any credential object. The existing `error`
field remains; `reason` and `execution` carry Rails' normalized refusal. This also gates
fresh `campus_mcp` bearer creation in that payload. Host observations absent for the lifetime
of an installation retain legacy Mac compatibility; an attempt can fetch again after unlocking only if its lease and
credential remain usable. Before creating a child, #986 must hand back a secure-store-refused
unstarted attempt with the advertised `executor_admission_paused` refusal and the bounded
terminal delivery policy before lease expiry. That existing transient refusal preserves queued
work without spending startup retries. Do not idle or renew indefinitely, or forward an
unrecognized store reason as though it were a retryable refusal. Consumer acceptance must
exercise a lock between claim and credential delivery, the hand-back, and a later eligible
claim after unlocking; an already-created child still reports its existing `/start` receipt.

This is a fresh-secret boundary, not recall of bytes authorized before the heartbeat
commits. It neither cancels the attempt nor rechecks eligibility at `/start`: that receipt
acknowledges an already-created child. Heartbeat, events, cancellation, terminal reporting
and reconciliation remain available. Claim-time agent credentials keep the existing atomic
claim authority. Verification secrets already recheck under the executor/credential/attempt
locks. Hardened-review claim work contains a claim token and credential id, not a provider
secret; its later lease response contains only status/cancellation metadata.

Native import, executor-local model discovery/ingestion and credential binding verification
all acquire the credential row before its binding row. Catalog authorization, binding reload,
generation and one-time discovery validation remain under both locks. The concurrent service
regression uses separate PostgreSQL connections and bounded waits; it makes no provider call.

## Host Action Cable contract audit

`ApplicationCable::Connection` accepts the native bearer session via Authorization header;
`actioncable-v1-json` is the negotiated protocol. Browser subprotocol token transport exists
for compatibility; the Linux Rust host uses Authorization and never passes credentials to
page JavaScript or a URL. Executor tokens and scoped API tokens are not Cable credentials.
`WorldChannel` derives the island from the authenticated connection, not a client island id;
scopes are world/project:id/task:id/agent:id. `AgentOutputChannel` authorizes session history
and supports bounded after_id backfill. World invalidation slots are already documented under
Realtime; reconnect/foreground must refetch authorized snapshots, preserve drafts, and treat
unknown refresh versions as requiring a safe full refresh, never arbitrary reads from slots.

Human Cable authority is now retained per session and checked without query-cache reuse
before subscriptions, actions, every channel payload (including backfill), and on Cable's
heartbeat worker. Invalid authority stops streams and closes the socket without reconnect.
Explicit deletion, password/role/disabled `delete_all`, expiry and idle timeout all withhold
subsequent payload authorization; validation never touches session activity. Agent identifiers
and valid sibling sessions are preserved. A separate PostgreSQL connection regression proves
committed callback-free revocation is visible to a warmed Cable query cache.

Delivery guarantee: a frame whose authorization read occurs after revocation commits is
withheld. A frame already authorized/queued before that commit cannot be recalled; transport
buffers are not a revocation barrier. Idle socket closure occurs when the heartbeat validation
worker runs, not at a promised wall-clock deadline. The tests exercise actual channel handlers
and database connections, not a deployed WebSocket/network receipt. Deployment and real
Linux/browser transport acceptance remain coordinator/#986 obligations.

## Rollout, fixtures and live-proof handoff

Additive server first; Mac absence fallback is limited to absent host observation and existing
local native import. Explicit unknown objects never use old Linux eligibility. Native executor
binding is nullable for pre-existing history; the new exact-device guard applies to imported
hosted history. Existing contract version/identifiers are retained. No CI/policy controls change.

After review/merge, LINUX-20261016 must record the merged server SHA and deploy it through the
normal release workflow. Record deployment readiness, deployed SHA and any deploy-artifact PR.
Merge alone is not deployment evidence. S2 (#985) exports the merged producer with:

```
node scripts/oss/export-clients.mjs --client linux --ref <merged-server-sha> --dest <isolated-output> --check
```

Verify `contract/.source`, fixture/spec digests and clean re-export before importing consumer
wire types. The local exporter receipt is candidate-only until that merged SHA exists.

LINUX-06 must exercise on isolated authorized data: register/heartbeat with Linux observations;
scoped credential plan → helper PTY login → consent/input/cancel/timeout/redacted snapshots →
verification binding; project observation; enqueue → v2 claim → start/lease/heartbeat/events →
terminal report/ack; native discovery/read/attach/exact resume and each refusal; revoke and
recovery. Record OS/package/architecture/session/graphics and artifact/contract SHAs. No real
provider call or desktop/package claim is made by these offline tests. Later contract gaps are
new server producers, never handwritten Linux contract drift.

## Concrete continuation after this review

#1030 owns mechanism-informed Linux speech and provider CLI update contracts after #982
and #984. #1031 imports that producer after #985 and #1030; #994 and #996 retain that gate.
Manual CLI guidance and unsupported speech do not complete P06/P18 or full parity.
The initial #984 → #985 → #986 → #988 chain remains unchanged. S1-5 remains open until
#986 records its bounded real hosted proof. LINUX-20261016 owns review, CI, merge, deployment
and successor coordination; this Office does not watch CI or change PR readiness.

### Native boundary repair

Readiness judges the actual requested/claim executor as well as the selected executor,
imported credential and Project folder; a different executor or missing native capability
cannot receive the imported conversation. Account deletion refuses imported native bindings
with the existing 422 error envelope (`native_account_deletion_refused.json`); model restriction
also preserves the executor identity. The deletion transaction locks owned executors before
checking, serialized with hosted import. A hosted binding is never nullified into local fallback.

Registration eligibility is evaluated inside the user/executor lock transaction against the
retained host and incoming secure-store report, before token generation or mutation. Omitting
host on an existing Linux installation cannot rotate a token while the store is locked or
unknown; a refusal preserves persisted registration and token identity. An unlocked report
recovers the same installation and rotates the token normally.

An explicit host must be an object with a nonblank string platform before it can be saved or
receive a registration token. Historical malformed host observations remain unsupported through
omission and may recover through an explicit valid heartbeat or registration. A nonblank string
platform is immutable even when unsupported; a known platform with an unknown contract version
may recover by reporting a compatible version of that same platform. Entire capabilities omission
retains the last stored observation and does not constitute a fresh report. These rules preserve
the never-explicit legacy Mac fallback and the locked/unknown Linux registration refusal.

Historical malformed observations cannot prevent disconnect or account-security revocation.
The host-shape validation permits only an existing active executor becoming revoked with its
token cleared and capabilities unchanged. The existing revocation lock, work settlement and
Office parking/unbinding transaction remain in force. This exception never applies to
registration, even when the same malformed capabilities are repeated or omitted entirely.
