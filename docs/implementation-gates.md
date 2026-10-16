# Linux implementation gates

These are required evidence for [the PRD](../PRD.md), not completed tests. Implementation was explicitly authorized on 2026-10-16. D1–D7, P01–P18, the five S1 prerequisites and D5's accepted x86_64
desktop-evidence gap remain in force. L0 may investigate mechanisms after the owner starts
implementation; later milestones must supply passing receipts before claiming the outcome.

Each receipt records the responsible repository/milestone, source and contract SHAs,
artifact digest, exact command/scenario, expected and observed result, and unresolved
dependencies. Desktop receipts also identify architecture, package, OS, session and
graphics mode. A proposed mechanism is not an acceptance result.

## G1. Server contracts and snapshot handoff

**Owners:** campus-server S1-1–S1-5; Linux S2/L1/L2. Build a contract ledger before L2:

| Area | Existing evidence and required closure |
|---|---|
| Claim readiness | [Pinned readiness](https://github.com/yuric/campus-server/blob/d35361542b895a4fd73c838b1be3531ceea5d5fd/api/app/services/execution_readiness.rb#L24) accepts Mac-shaped `/Users/.../workspaces` roots. S1-2 must define Linux workspace observations and platform-aware validation, with Mac compatibility tests. A Linux executor must demonstrate a real claim, not just successful registration. |
| Capability observations | The [registration schema](https://github.com/yuric/campus-server/blob/d35361542b895a4fd73c838b1be3531ceea5d5fd/api/docs/openapi.yaml#L28071) already describes `broker_execution_capacity`, resources, credential scope and helper updates. Map every advertised key to its schema/version and Linux observation source; cover workspace adoption/quiescence, work contracts, coordinator/MCP work and delivery counters. Record genuinely missing schemas under S1-2; do not rename existing fields simply to remove Mac terminology. |
| Native conversations | [NativeSessionImport](https://github.com/yuric/campus-server/blob/d35361542b895a4fd73c838b1be3531ceea5d5fd/api/app/services/native_session_import.rb#L25) calls MacBroker for discovery/read. S1-2 must establish an authorized executor-side path for hosted Linux and type the native-resume claim fields where absent. Test discovery, attach, exact resume, account mismatch, missing session and unsupported versions. Never replace a failed native resume with a fresh conversation. |
| Copy and platform behavior | S1-1 covers runtime copy as well as OpenAPI prose, including CLI freshness/update and speech. S1-2 handles platform eligibility and any necessary wire-shape changes with compatible migration. A Mac-named wire value is not itself permission to rename it; clients must not rewrite server messages. |
| Secure store and release identity | S1-3 maps absent and locked store observations to its two diagnostics. S1-4 retains Linux release/catalog identity and diagnostics; protocol-version rejection already exists independently. |
| Hosted login | S1-5 requires a real hosted Rails → Linux executor → provider login/verify round trip, including cancellation and redaction. Source inspection identifies the path but does not close the gate. |

S2 is a Linux-owned contract-import PR from a recorded merged server SHA containing the
S1 changes required by its consumers. Use the server-owned
[exporter](https://github.com/yuric/campus-server/blob/d35361542b895a4fd73c838b1be3531ceea5d5fd/scripts/oss/export-clients.mjs#L48),
which replaces `docs/api/openapi.yaml` and `docs/api/.source` with a `contract/` bundle
(including `contract/api/docs/openapi.yaml`, fixtures and `contract/.source`). Move every
documentation, generator and CI reference in that same PR; prove external fixture links,
provenance and clean re-export. If the exporter needs a correction, merge it in the server
first. This PR leaves the old snapshot untouched and makes no current-contract claim.

L1 pins the generator/version/command, commits generated wire types and runs
regenerate-and-diff. Test additive fields and unknown enums without crashing unrelated
presentation data; withhold affected actions on unknown required contracts. Missing or
malformed required authorization fields fail closed. Preserve server-authored refusal
copy; decoding must not manufacture an explanation. Sensitive schema fields, including
`x-campus-sensitive`, require redacting types/formatters and log/crash serialization tests.

The Rust host owns authenticated Action Cable transport, keeping credentials out of page
JavaScript and URLs. The spec's [Realtime description](https://github.com/yuric/campus-server/blob/d35361542b895a4fd73c838b1be3531ceea5d5fd/api/docs/openapi.yaml#L330)
already defines invalidation slots; S1-2 records any remaining connection/subscription
contract gaps against the [server connection](https://github.com/yuric/campus-server/blob/d35361542b895a4fd73c838b1be3531ceea5d5fd/api/app/channels/application_cable/connection.rb)
and channel code. Verify authentication, island authorization, revoke/disconnect,
reconnect/refetch and unknown refresh versions; never infer reads from unknown slots.

## G2. Credential scope and provider evidence

**Owners:** Linux L0/L2; server S1-2/S1-3/S1-5. Mirror the pinned
[CredentialScope](https://github.com/yuric/campus-macos/blob/3cc71216e3ca05090e90c5f09a56350b065acdcd/Sources/CampusBrokerCore/CredentialScope.swift)
algorithm: UTF-8 scope bytes, nonempty, at most 160 bytes, no NUL; unpadded base64url;
`<trusted-root>/scopes/<encoded-scope>`. Use shared input/output vectors, including Unicode.
The exact derived path bytes reach the CLI. The root is selected locally and isolated by
the configured product/API identity, never by a server-provided path.

Prove strict-descendant bounds, permissions, malicious scope input, symlink substitution,
rename/race and mount-boundary behavior without deleting user data. L0 chooses a safe
descriptor-relative filesystem strategy; string-prefix checks alone are insufficient.
Do not require all user repositories to reside on one filesystem merely to simplify a test.

Record CLI version, engine, login method, actual token store, config-variable behavior,
refresh, cancellation and account-isolation results. Claude Code, Codex and Grok have
isolated-directory mechanisms in the Mac reference; those are not proof of Linux behavior.
The pinned [engine bindings](https://github.com/yuric/campus-macos/blob/3cc71216e3ca05090e90c5f09a56350b065acdcd/Sources/CampusBrokerCore/Engine.swift)
give Antigravity no config-dir variable. Its Linux storage and identity scope remain
unproven and feed Rails readiness through S1-2. Do not label it account-isolated because a
working directory exists. Gemini's API-key path is tested separately from subscription login.

Prove D3's absent/locked/unlocked Secret Service behavior on the selected backend, including
memory-only board access and withheld executor registration. No file fallback for persistent
Campus tokens. G4 covers same-user exposure and per-attempt credentials separately.

## G3. Supervision, recovery and live updates

**Owners:** Linux L0/L2/L5. L0 records the proposed unit, executable path, restart policy,
stop timeout and graphical-session integration for the actual D5 desktop. Use a real
display-manager-managed login session in Lima; a compositor launched over SSH alone does
not prove graphical login/logout. Keep the standalone Rust helper from D2; do not copy a
Mac-only app launch flag as a Linux requirement.

Prove SSH-only login cannot start supervision, closing the UI does not stop it, and last
graphical logout stops it even with SSH open. Preserve D4's stable helper installation.
Specify a retryable helper exit (the Mac uses 75) separately from intentional stop/revoke
(success must stay down). Repeated retryable exits must have a tested bounded-backoff and
recovery path, not silently exhaust a restart limit forever. Do not treat retry as success.
Stop timing must accommodate the Rails claim's stop grace and durable delivery protocol.

Use a cross-process singleton lock and durable authorization generation. Preserve an
already-authorized epoch on ordinary UI relaunch, same-account sign-in and repair;
invalidate it on sign-out/revoke. Establish local sign-out precedence, fence/stop work and
disable automatic restart before remote revocation; failures must not let a concurrent
installer reactivate the service. Retain enough local state to reconcile an uncertain stop.
The [Mac lifecycle implementation](https://github.com/yuric/campus-macos/blob/3cc71216e3ca05090e90c5f09a56350b065acdcd/CampusApp/Sources/CampusKit/ExecutorLaunchAgent.swift#L490)
is evidence for these invariants, not a portable unit-file recipe.

Wire D4 promotion to the existing [claim's helper-update contract](https://github.com/yuric/campus-server/blob/d35361542b895a4fd73c838b1be3531ceea5d5fd/api/app/controllers/executor_claims_controller.rb#L154):
report, confirmation window and stop grace. Advertise `helper_update_monitor` only when supported; report truthful
`executor_helper` bundled/installed digests and distinguish running-image identity from
files replaced on disk. L0 defines those identities for the stable extracted helper and
each outer package. Announce, stop, prove termination and report handback before replacement;
Rails owns resume. A failed confirmation must not be reported as a successful stop.

Create Linux tests for the four [recovery-drill boundaries](https://github.com/yuric/campus-server/blob/d35361542b895a4fd73c838b1be3531ceea5d5fd/docs/EXECUTOR_RECOVERY_DRILLS.md#the-four-boundaries):
claim/start acknowledgement, mid-stream, provider exit before terminal acknowledgement,
and cancellation. L2 records the outbox location/schema under private XDG state, scoped to
origin/channel/account/executor, and proves durability, replay order and no secret payloads.
Add crash loops, sign-out mid-run, re-sign-in during work, concurrent update/start, keyring
lock and package replacement while UI-closed to D4's existing transition matrix.

## G4. Host and executor trust boundaries

**Owners:** Linux L0/L1/L2; server S1-2 for any missing token-authority contracts.
[GNOME Keyring](https://wiki.gnome.org/Projects/GnomeKeyring/SecurityPhilosophy) does not
promise isolation from arbitrary code in the same user session. State what is protected
against a different UID, a compromised renderer and a provider process running as the user.
Environment filtering, IPC tokens and process groups do not create a same-user sandbox.
Do not claim parity with Mac application ACLs without evidence. Any required expansion of
token authority or acceptance of an unresolved trust gap requires an explicit owner
decision; preserve D3's selected store and file policy.

L0 must demonstrate these boundaries with synthetic secrets and disposable processes:

- **IPC:** authenticate the peer before sending a credential or privileged request. Evaluate
  an AF_UNIX pathname socket under the private runtime directory with peer-UID checks and
  D3's distinct token; verify both ends, stale endpoints, another UID and wrong-principal
  requests. A loopback port and bearer token alone are not proof of server identity. An
  alternative transport must meet the same cases; no broad unauthenticated executor RPC.
- **Child context:** define allowed environment/descriptor inheritance per run and login
  profile. No ambient Campus tokens, unrelated provider keys, SSH agent, display or session
  bus access by default; prove any provider-specific exception without transferring wider
  authority. Close unintended descriptors and test Git/login workflows still work.
- **Attempt credentials:** separately test the [claim's runtime credential](https://github.com/yuric/campus-server/blob/d35361542b895a4fd73c838b1be3531ceea5d5fd/api/app/controllers/executor_claims_controller.rb#L166)
  (`campus_agent_token`/`CAMPUS_API_TOKEN`) and [attempt MCP credential](https://github.com/yuric/campus-server/blob/d35361542b895a4fd73c838b1be3531ceea5d5fd/api/app/controllers/executor_attempts_controller.rb#L42)
  (`CAMPUS_MCP_TOKEN`) contracts: fixed injection, bounded authority, expiry/revoke,
  no renderer/argv/log/outbox persistence and no reuse by another attempt. These do not
  authorize giving the child a session or executor token.
- **Termination:** test grandchildren, `setsid`, fork races and PID reuse. Validate a delegated
  per-attempt cgroup/user scope plus stable process identities where available; verify the
  whole descendant population, not just the leader. [cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)
  is a lifecycle mechanism, not automatic containment of hostile same-user processes.
  Missing delegation or uncertain termination must report unconfirmed state to Rails and
  withhold unsafe reassignment, never manufacture a successful cancellation.
- **Crash capture:** establish core-dump/dumpability policy for secret-bearing host and child
  processes and test the desktop's actual crash collector, including after exec. Inspect
  logs, dumps and support bundles with synthetic markers. A setting on the parent alone
  does not establish that children cannot persist secrets.

## G5. Signed updates and package selection

**Owners:** Linux L0/L5; campus-server release tooling under S1-4's handoff. Keep one
production manifest. Record four distinct URL/signature entries for the two formats and
architectures, using the pinned updater's bundle-aware keys (for example,
`linux-x86_64-deb`, `linux-x86_64-appimage`, `linux-aarch64-deb`,
`linux-aarch64-appimage`). Verify selection from each installed artifact; no generic key
may route a deb installation to AppImage bytes. [Updater source](https://github.com/tauri-apps/plugins-workspace/blob/v2/plugins/updater/src/updater.rs)
supports bundle-aware selection, but the released version and manifest must be pinned/tested.

For deb, verify the exact bytes installed by the privileged process, not only the earlier
download in user space. L0 must prove a polkit-authorized installer that validates against
a trusted key and prevents substitution between verification and `dpkg`, with narrowly
bounded inputs. This is a privileged installation step, not a root execution service.
Audit the pinned updater's elevation behavior: do not collect administrator passwords in
Campus or silently fall back to a GUI password → `sudo -S` path. Missing/denied polkit must
leave the installed app/helper intact and expose a safe update remedy; it is not a pass
for in-app deb updates. Escalate an unachievable D4 path instead of changing packaging.

Test wrong package/architecture, bad signature, substituted staged file, denied elevation,
interrupted install and an external package-manager replacement while work is active.
The helper must observe/reconcile replacement even if Campus did not initiate it; D4's
rejection of apt as the primary update channel is not an assumption that it never happens.
Keep per-format SBOM/WebKitGTK receipts and an owner for bundled-runtime security updates.

## G6. Login, task links and speech

**Owners:** Linux L0/L2/L3/L5; server S1-1/S1-2/S1-5 as applicable.

| Mechanism | Acceptance evidence |
|---|---|
| Provider login | Use a PTY for interactive login and a write-only input relay with bounded, redacted snapshots. Test consent URL discovery, input, cancel, timeout, token-like output and refresh. Non-interactive execution/verification retains its declared pipe protocol. The [Mac PTY](https://github.com/yuric/campus-macos/blob/3cc71216e3ca05090e90c5f09a56350b065acdcd/Sources/CampusBrokerCore/PTYProcess.swift#L3) explains why the paths differ. |
| Task links | Test Rails-provided `task_link.href`, `campus://` desktop association, cold start and existing-window activation for both packages. Inventory the [Mac task-link bridge](https://github.com/yuric/campus-macos/blob/3cc71216e3ca05090e90c5f09a56350b065acdcd/CampusApp/Sources/CampusKit/TaskLinkBridge.swift) before selecting a Linux mechanism. If parity needs a credential-free loopback activation listener, bound it to validated navigation only: no tokens, file/process access or domain mutations; test hostile origins, malformed IDs and unavailable app. This does not authorize a second service by assumption. |
| Speech | The pinned [transcription capability](https://github.com/yuric/campus-server/blob/d35361542b895a4fd73c838b1be3531ceea5d5fd/api/app/services/task_transcription.rb#L41) advertises Apple platform speech. L0 identifies a Linux mechanism and its availability, permissions, privacy, cost and offline limits. Do not treat the legacy WAV path as a durable fallback. Any new API capability/copy merges in S1 first; any changed product/privacy/spend trade-off needs owner disposition. P06 remains a gap until permission denial, interruption, duration/size limits and editable results pass. |

## G7. Renderer export, bridge and webview recovery

**Owners:** campus-macos M1; Linux L0/L1/L4. Import a built renderer artifact from an exact
merged producer SHA, with an externally recorded manifest digest and verified byte/license
inventory. The existing [iOS export recipe](https://github.com/yuric/campus-macos/blob/3cc71216e3ca05090e90c5f09a56350b065acdcd/island/IOS_EXPORT.md)
is evidence to adapt at the producer; its mobile read-only surface is not desktop parity.
Exclude tests, development harnesses and retired client API/rules modules. Do not hide
the artifact from D7 to make a copied client catalog pass.

M1 names the desktop recipe and bridge schema. L4 maps the renderer's `campusIslandAPI`
presentation requests, authorized `campusHost` mutations and `window.campusIsland`
lifecycle acknowledgements to restricted host methods. Check main-frame/exact-origin,
method, schema, principal and server confirmation on every authority-bearing request.
No generic eval/HTTP/filesystem/process bridge; no tokens in JavaScript. L0 may use a stub
for rendering performance, but stubbed actions are not functional parity receipts.

Explicitly configure and test [Tauri CSP](https://v2.tauri.app/security/csp/) and per-window
capabilities against the final bundled artifact. Replay hostile labels, iframe/foreign
origin messages, navigation and remote-subresource attempts. Prove reduced-motion and
visibility changes are applied/acknowledged rather than merely sent.

Separate an Island-renderer failure from an entire WebKit/GPU-process failure. The first
must preserve board controls; the second needs a host recovery path that does not depend
on the failed page. Test software rendering and compositing-related failures on D5's VM.
Any workaround flags must be conditional, tested and visible in diagnostics. Record real
GPU results when available without adding a hardware gate that D5 rejected.

## G8. Reproducible L0 and acceptance receipts

**Owner:** Linux L0, with Mac-owned reference capture changes at M1 when needed. Before
running comparisons, record the seed/reference server, viewport, scale factors, appearance,
scene, licensed font/icon mapping, capture method, visual tolerances and motion/visibility
conditions. Use isolated data and the existing authorized credential channel. Select a
provider already supported by the contract for the first CLI proof; one working provider
does not reduce the P09/P15/P16 release inventory.

Before the first renderer benchmark, record a numeric p95 frame-time limit and the test
protocol: a fixed 60-second pan/zoom sequence, warmup, viewport/render scale, reference
scene, VM resources and software renderer/version. Do not derive the passing limit from
the candidate's measured result. Record raw measurements and repeats; a changed scale or
scene is a separately identified run. A missing threshold is an unresolved L0 gate.
On a verified miss, apply D1's existing fallback after testing permitted optimizations;
relaxing the target or changing the agreed scope requires owner disposition.

The L0 handoff must include a reproducible Lima configuration and automation for real
graphical login/logout, keyring unlock/lock and polkit interaction, with disposable guest
credentials supplied securely rather than committed. Test each D5 session/package tuple.
Failures and unavailable mechanisms remain explicit; the x86_64 preview does not inherit
arm64 desktop results. Implementation is authorized; these receipts remain required.
