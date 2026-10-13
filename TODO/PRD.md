# PRD: Campus for Linux

**Revision:** 2026-10-13. **Status:** proposed for review; no implementation started.
**Product:** a Linux desktop client and per-user local execution service.

## 1. Owner requirements and outcome

The owner requests macOS feature parity, both local and remote agents, and broad Linux
compatibility. The first user's distribution is Ubuntu. This planning PR does not
authorize implementation, production task import, deployment, credentials or paid services.

A Linux-only user can onboard, connect provider accounts, bind local repositories,
run coding agents on Linux, and manage their island and authorized remote agents.
Rails decides product behavior. The desktop is a thin presentation client; the execution
service is a separate privileged component, not an API wrapper.

Parity means equivalent user outcomes, authorization, confirmations, recovery and data
integrity. **Visual fidelity is also an owner requirement:** the Linux app should look
like the same Campus app, approaching pixel accuracy where practical. Reuse artwork,
Island visuals, colors, layout and interaction patterns; use Linux components where
needed. Do not spend disproportionate effort matching OS chrome or rendering differences.
Preview builds may ship incrementally with an explicit gap list; full parity is the
release target, not a label applied to the first working board.

Not included: hosting Rails/PostgreSQL, a new orchestration engine, new provider integrations,
or a universal guarantee for every Linux system. Connecting to hosted and user-configured
APIs is included. Closing the app window must not terminate execution.

**Owner decision:** match the current Mac lifecycle. Execution is independent of the UI
but tied to the logged-in user session; it can restart on login after reboot. Unattended
execution after logout or before login is outside release 1. Mac evidence:
`ExecutorLaunchAgent.swift` uses `gui/<uid>`, a user LaunchAgent and `RunAtLoad`.

## 2. Evidence and parity baseline

The reference is merged Mac source, not only its older PRD. Source inspection found
features missing from that PRD and Mac-specific executor wording in server code.

| Reference | Immutable baseline | Evidence |
|---|---|---|
| Mac | [3cc71216](https://github.com/yuric/campus-macos/tree/3cc71216e3ca05090e90c5f09a56350b065acdcd) | `CampusApp/Sources/CampusApp`, `CampusKit`, `Sources/CampusBrokerCore`, `island` |
| Server | [d3536154](https://github.com/yuric/campus-server/tree/d35361542b895a4fd73c838b1be3531ceea5d5fd) | `api/docs/openapi.yaml`, execution/task/credential/assistant contracts |
| iOS plan | [companion PRD](https://github.com/yuric/campus-server/blob/d35361542b895a4fd73c838b1be3531ceea5d5fd/TODO/ios-companion-app/PRD.md) | API-driven reads/writes and Island hosting; its reduced scope does not define Linux scope |

This is a source-based inventory, not live Mac UI verification or proof of Linux support.
Paths below are relative to the pinned Mac tree. Before implementation freeze, reconcile
with then-current merged Mac source and record additions explicitly rather than silently
chasing later features. The retired web and CLI clients are not dependencies.

## 3. Feature parity inventory

All rows are **not implemented**. Each needs an owner, exact API operation/schema references,
action-level acceptance cases, source/build identity and passing receipts. L0 expands these
groups into every offered action; this table is not permission to omit unnamed buttons.

| ID | Required outcome | Mac source evidence |
|---|---|---|
| P01 | Sign in/out, registration, password recovery, expiry/revocation, demo/conversion and safe account/island switching | `FirstRunScreen.swift`, `API.swift`, `RootView.swift` |
| P02 | Hosted/configured API, endpoint validation, onboarding/recovery, first-time setup without a Mac | `Configuration.swift`, `BootstrapRecovery.swift`, onboarding stores |
| P03 | Home inbox, waiting-on-you, briefing/digest, recommendations/Pulse, read/resolve receipts | `InboxScreen.swift`, `InboxStore.swift`, `PulsePresentation.swift`, `RecommendationPresentation.swift` |
| P04 | Kanban counts/pagination/filtering, selection/order/staging, batch approval and all offered workflow/assignment/routing actions | `BoardScreen.swift`, `BoardStore.swift`, `LaneFeedStore.swift`, `API.swift` |
| P05 | Task create/edit/comments, dependencies/lineage/PR links, runs/activity, task chat and draft conversation | `TaskDetailView.swift`, `TaskDetailStore.swift`, `TaskWorkspaceScreen.swift`, `NewTaskSheet.swift` |
| P06 | Staged attachment upload, previews/downloads, server limits; microphone/dictation permissions, interruptions and recovery | `API.swift`, `TaskVoiceStore.swift`, `MicrophoneRecording.swift`, `SpeechRecording.swift` |
| P07 | Project create/edit/import/browse, local folder binding, archive/delete, status and workspace rules | `BuildingScreen.swift`, `NewProjectStore.swift`, `ProjectProvisioner.swift`, `WorkspaceRuleStore.swift` |
| P08 | Agent single/batch landing, account/model/executor choice, rename/message/transcript, restart/resume/stop/dismiss/restore/archive when offered | `AgentsScreen.swift`, `LandAgentStore.swift`, `AgentOfficeStore.swift`, `API.swift` |
| P09 | Credential add/rename/remove/reorder, fallback, CLI/browser login/cancel/input/verify, usage/model discovery/refresh | `CredentialsScreen.swift`, `CredentialsStore.swift`, `CredentialCapabilities.swift`, broker login |
| P10 | Assistant/coordinator history/sessions, questions/references/steering, continue/stop, proposals/confirmations, monitors/private interactions | `AssistantStore.swift`, `CoordinatorSessions.swift`, `CoordinatorTurnActions.swift`, `PrivateManagerInteraction.swift` |
| P11 | Delegated authorization scope, grant/refuse consent, expiry/revocation; rendered content cannot grant consent | `DelegatedAuthorization.swift`, `DelegatedAuthorizationConsentSheet.swift` |
| P12 | Shared Island, project/agent selection and offered mutations, navigation, zoom/pan, visibility pause and Reduce Motion | `IslandScreen.swift`, `IslandApprovalStore.swift`, `island/` |
| P13 | Activity/search, shortcuts, deep/task links, external browser/file opening, keyboard focus, screen reader and appearance | `ActivityScreen.swift`, `SearchPalette.swift`, `Navigation.swift`, `DeepLink.swift`, `TaskLinkBridge.swift` |
| P14 | Settings/rules, assistant authority/prompts, GitHub connection, feedback, telemetry preference and profile | `SettingsScreen.swift`, `SettingsStore.swift`, `GithubConnectionStore.swift`, `Telemetry.swift` |
| P15 | Executor register/rename/revoke, project/account binding, readiness, workspace setup/recovery and resource/model observations | `ExecutorRegistrationStore.swift`, `ExecutorSetupStore.swift`, `ExecutorWorkspaceProvisioner.swift` |
| P16 | Local claims/leases, CLI launch, worktree lifecycle, transcripts/tool events, cancellation, result/outbox and crash/reconnect recovery | `ExecutorExecutionStore.swift`, `ExecutorOutbox.swift`, `BrokerExecutionClient.swift`, `Sources/CampusBrokerCore` |
| P17 | Remote executor selection/control, truthful queued/running/offline/revoked states, no accidental local fallback | `HostedAgentExecutionStore.swift`, `ExecutorControlAPI.swift`, `API.swift` |
| P18 | App/helper/provider CLI updates, safe active-run update behavior, prod/dev channel isolation, diagnostics/remedies | `UpdateStore.swift`, `ExecutorHelperUpdate.swift`, `CLIUpdate.swift`, `ProductChannel.swift`, diagnostic stores |

Provider availability comes from Rails plus observed Linux capability. A Mac-only provider
binary is an upstream parity blocker, not invented Linux support or an automatic scope cut.
All applicable rows must pass; unavailable equivalents require explicit owner disposition.
Platform notification, tray/menu and speech equivalents are evaluated in P06/P13/P18;
Apple-specific frameworks are replaced, not assumed portable.

### Visual fidelity acceptance

- Use the pinned Mac `DesignSystem.swift`, `CampusUI` components, screen layouts,
  `CampusApp/Resources` and Island styles/artwork as references. Reuse distributable assets
  with provenance/license checks; do not redraw existing art or copy restricted Apple
  fonts/symbols into Linux packages. Choose licensed equivalents with similar metrics.
- Preserve sidebar/navigation, hierarchy, density, spacing, card shapes, status colors,
  light/dark appearances, icons/illustration identity and main interaction patterns.
  Native Linux file/credential dialogs, decorations, shortcuts and accessibility adapters
  may differ. Accessibility and readable scaling take precedence over matching pixels.
- L0 captures reference Mac screenshots at recorded viewports, scale, appearance and
  seeded data for Home, Board, task detail/chat, agents/landing, credentials, settings,
  onboarding and Island. Compare matching Linux screenshots and review overlays during
  L3–L5; track deliberate platform differences separately from visual regressions.
- Aim for pixel accuracy on reusable artwork and app-controlled geometry where inexpensive.
  Font rasterization and desktop chrome are not universal exact-image gates. Record
  tolerances and remaining discrepancies in the visual QA report. Escalate substantial
  redesigns or a large extra polish budget instead of silently expanding effort.

## 4. Proposed architecture and decisions

A web-based desktop UI hosts the shared React/Three.js renderer. A narrow privileged host
owns session storage, HTTP and OS integration. An independent per-user Linux executor
supervises CLIs. See [ARCHITECTURE.md](../ARCHITECTURE.md) for boundaries.

| Decision | Proposal and evidence required in L0 |
|---|---|
| Desktop shell | Compare Electron/Tauri on Ubuntu, Fedora and KDE for GPU/Island rendering, accessibility, secrets, startup/size and updates. Electron is the initial portability candidate; Tauri remains an option after WebKitGTK checks. Record an ADR before scaffolding. |
| Executor language | Compare portable Mac Swift components with a Linux implementation using identical protocol/recovery fixtures. Select on correctness/maintainability, not copied line count; no execution in renderer JavaScript. |
| Supervision | systemd user service where available and an explicit non-systemd per-user supervisor path, bound to login/logout to match Mac. No root service or automatic lingering changes. Test logout stops supervision; login restores it. |
| Secrets | Proven platform credential-store backend; test missing/locked/revoked stores. No plaintext fallback. Withhold persistent local credentials when secure storage is absent; preserve safe remote/session-only use where possible. |
| Packages | Standalone executor plus desktop artifacts; validate AppImage and native deb/rpm. Choose portable artifacts after GPU/runtime tests. Flatpak is optional and cannot gain unrestricted host access merely to execute CLIs. |
| Updates | Authenticated immutable app/helper artifacts, verified before install, compatible protocol negotiation and interrupted-install recovery. Establish signing/key custody/distribution owner before release; no new release secrets in this planning PR. |

These are engineering proposals, not owner-approved framework choices. L0 resolves them
with evidence before dependencies/product scaffolding. No paid service, repository-setting
change or production execution authorization is implied by this specification.

## 5. API authority and safety requirements

- Rails supplies capabilities/catalogs, wording, workflow/ordering, confirmations,
  validation and normalized failures. Unknown contract/action versions withhold actions;
  do not port Mac's remaining client-rule drift.
- Generate bindings from a verified pinned OpenAPI snapshot. The existing Linux snapshot
  is not assumed current. Missing schemas/operations merge in `campus-server` first.
- Events invalidate authorized snapshots. Reconnect/foreground refresh preserves drafts
  and marks stale data. Writes use server idempotency/confirmation; ambiguous timeouts
  reconcile status rather than replay blindly. Accepted/queued is not running/completed.
- Keep account/executor/provider secrets out of renderer code, URLs, arguments, logs,
  telemetry and crash reports. Restrict host IPC by method, origin, schema and principal;
  serve only pinned bundled assets and open external links in the browser.
- Bind caches/deep links/IPC to account and island. Sign-out clears consent/account data
  and explicitly reconciles active execution without accidental reassignment/termination.
- Executor IPC is authenticated. Use direct argv spawning, executable allowlists, bounded
  workspaces, credential isolation, output redaction and process-group cancellation.
  Local service identity is distinct from account and executor credentials.
- Revalidate lease/attempt ownership, preserve ordered acknowledged outbox delivery,
  and avoid duplicate execution across restart/suspend/partition/revoke. CLI exit alone
  cannot establish domain outcome. Updates cannot replace a running helper unsafely.
- OS adapters report observed facts; Rails interprets readiness/faults. Reject workspace
  symlink escapes and cross-account access; support approved worktrees/Git authentication
  and recovery/cleanup without deleting user modifications.
- Provider OAuth/config artifacts need an audited storage design. If a CLI requires secret
  files, resolve that conflict with the credential-store-only policy before implementation;
  do not quietly weaken the policy or claim all provider credentials are portable.

## 6. Compatibility contract

One source tree is not one binary for every CPU/runtime. Publish exact OS/image, CPU,
desktop/session, GPU/driver and artifact identities. This is a **proposed test matrix**,
not a claim of existing support:

| Tier | Targets and release rule |
|---|---|
| First verified | Ubuntu 24.04 LTS x86_64, GNOME, Wayland and X11. Confirm the friend's actual Ubuntu/hardware in L0 and add that combination if different. |
| Broad desktop | Ubuntu 22.04 compatibility where dependencies allow, Debian stable, current stable Fedora GNOME/KDE and Arch/KDE at a recorded snapshot. Version support is earned by installed-package tests. |
| Architectures | arm64 built/tested separately; release coverage selected after toolchain/provider checks. Untested architectures are never advertised supported. |
| Additional systems | Non-systemd desktops via the supervisor path; musl/Alpine, NixOS and immutable/custom systems require explicit packaging/runtime evidence. |

Cover locked/missing keyring, unavailable WebGL/GPU/software rendering, high DPI/multiple
monitors, suspend/resume, microphone permissions and file chooser behavior. Require complete
keyboard workflows, visible focus, screen reader labels/announcements, scaling/contrast
and reduced motion. Island failure leaves board/task controls usable but does not count
as Island parity. Broader compatibility is designed in, never inferred from one Ubuntu run.

## 7. Delivery sequence and repository ownership

Each milestone has a bounded reviewable outcome, exact checks, owner and handoff containing
repository/commit, contracts, artifacts, results and remaining gaps. No production tasks
have been created by this document.

| Milestone | Dependencies | Outcome and gate |
|---|---|---|
| L0: inventory/spikes | Specification reviewed | Expand P01–P18 into action cases; capture visual references; test shell/Island, credential store and one supervised CLI on Linux; ADRs, approved lifecycle, matrix and revised estimates |
| S1: API prerequisites | L0 inventory | Server-owned Linux platform/capability, paths/login/readiness/diagnostics/updates gaps only where existing contracts do not suffice; merged contract tests and deploy evidence when required |
| M1: renderer export | L0; S1 if needed | Mac-owned platform-neutral host/export changes where needed; exact merged-source artifact/manifest; no renderer fork |
| L1: foundation | L0, required S1 contracts | Snapshot/generator checks, shell, secure sessions, endpoint/channel separation, refresh/unknown-version behavior; P01–P03 |
| L2: execution | L0, required S1 contracts | Per-user service/register/bind/login/workspaces, claim-to-result/cancel/recovery vertical slice; P15–P17; one CLI initially is spike scope, not release scope |
| L3: workflows | L1; L2 for local actions | P04–P11/P13–P14; all supported offered providers/actions, assistant/consent, attachments/speech and shared semantic fixtures |
| L4: Island/integration | L1, M1, L2/L3 actions | P12, restricted host bridge, accessibility and integrated local/remote operation |
| L5: distribution/acceptance | L1–L4 | P18, package/update/recovery/channel checks, advertised matrix, isolated live QA, full parity sign-off and installable artifacts |

Linux owns client/service/packages. Server owns Rails/OpenAPI/deploy. Mac owns renderer
producer changes. Cross-repository work uses separate PRs in contract → producer →
snapshot/consumer order. Dependencies clear on verified merged outcomes, not open PRs.

## 8. Acceptance and release evidence

1. Expand and complete every P01–P18 case against the pinned source. Record expected API
   behavior, observed Linux behavior, test/receipt and exceptions. No missing row is hidden
   by a percentage; exceptions need a recorded owner decision.
2. A new Linux-only user onboards, connects an account, binds a repository, lands an agent,
   creates/approves work, observes actual local edits/result, cancels the process tree,
   closes/reopens the UI and recovers an executor restart without a Mac.
3. Authorized remote control works with local execution unavailable. Offline/queued state
   is truthful, and remote failure cannot cause unauthorized local fallback.
4. Contract fixtures cover unknown versions/withheld actions, confirmations, tenant isolation,
   expiry/revoke, malformed host messages, ambiguous writes, duplicate/out-of-order events,
   stale cursors, attachment errors and redaction. Linux-only adapters get real integration tests.
5. Service tests cover lost lease, provider exit, disk full, interrupted delivery, suspend,
   keyring lock, workspace escape, app/helper mismatch and active-run updates; no captured
   diagnostic/package contains secrets. Account switching cannot leak credentials/data.
6. Paired Mac/Linux screenshots meet the visual fidelity criteria above, with recorded
   platform differences and remaining discrepancies; do not claim pixel perfection without
   evidence. Installed packages pass on every advertised combination, including accessibility,
   graphics/audio, service lifecycle, uninstall and upgrade. Measure startup/board latency,
   Island frame time and idle CPU/RAM on recorded hardware. L0 sets budgets from measured
   reference/user needs rather than invented universal thresholds.
7. Release receipts include source/contract/renderer SHAs, package checksums/signatures,
   build provenance, commands/results, compatibility matrix, known issues and rollback/recovery.
   A merged planning PR or a CI-only build is not a delivered Linux app.
8. Live QA uses an isolated account/island and disposable repositories/agents, never the
   owner's working data. Credentials and release keys use authorized secure channels.

## 9. Estimates and open evidence

Voice estimates were 2–3 working days for specification/parity analysis and 4–8+ weeks
for implementation/verification with agent assistance. They are planning ranges, not
promises, and have not been validated by a Linux spike. This PR proposes the specification;
it does not claim completed portability testing or a complete button-level inventory.
L0 replaces estimates with measured milestone ranges and critical-path risks.

Open evidence: actual Ubuntu/CPU/GPU, Linux test hosts/CI budget,
provider Linux/login support, desktop/executor ADRs, provider-config storage policy,
verified package/update signing route and exact server prerequisite list. Resolve engineering
choices with evidence; ask the owner for unresolved product/spend/credential/trust decisions.
The owner does not need to write another PRD. Implementation/task import is separate work.
