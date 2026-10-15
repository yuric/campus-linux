# PRD: Campus for Linux

**Revision:** 2026-10-15. **Status:** decided; no implementation started.
**Product:** a Linux desktop client and per-user local execution service.

The seven decisions in [section 4](#4-architecture-and-decisions) were made by the owner on
2026-10-15, one at a time, with the trade-offs recorded beside each. They are not proposals.
L0 proves the residual risks each one names; it does not reopen the choices. Implementation
starts only on an explicit owner request after this document merges.

## 1. Owner requirements and outcome

The owner requests macOS feature parity, both local and remote agents, and broad Linux
compatibility. The first user's distribution is Ubuntu. This planning PR does not
authorize implementation, production task import, deployment, credentials or paid services.

A Linux-only user can onboard, connect provider accounts, bind local repositories,
run coding agents on Linux, and manage their island and authorized remote agents.
Rails decides product behavior. The desktop is a thin presentation client; the execution
service is a separate trusted, unprivileged per-user component, not an API wrapper.

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
but tied to the graphical login session; it restarts on graphical login after reboot
when installed and authorized. Unattended
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
| P13 | Activity/search, shortcuts, deep/task links, external browser/file opening, keyboard focus, screen reader, appearance, application menus and reply notifications; tray/status equivalents where Mac provides them | `ActivityScreen.swift`, `SearchPalette.swift`, `Navigation.swift`, `DeepLink.swift`, `TaskLinkBridge.swift`, `AssistantReplyNotification.swift`, `main.swift` |
| P14 | Settings/rules, assistant authority/prompts, GitHub connection, feedback, telemetry preference and profile | `SettingsScreen.swift`, `SettingsStore.swift`, `GithubConnectionStore.swift`, `Telemetry.swift` |
| P15 | Executor register/rename/revoke, project/account binding, readiness, workspace setup/recovery and resource/model observations | `ExecutorRegistrationStore.swift`, `ExecutorSetupStore.swift`, `ExecutorWorkspaceProvisioner.swift` |
| P16 | Local claims/leases, CLI launch, worktree lifecycle, transcripts/tool events, cancellation, result/outbox and crash/reconnect recovery | `ExecutorExecutionStore.swift`, `ExecutorOutbox.swift`, `BrokerExecutionClient.swift`, `Sources/CampusBrokerCore` |
| P17 | Remote executor selection/control, truthful queued/running/offline/revoked states, no accidental local fallback | `HostedAgentExecutionStore.swift`, `ExecutorControlAPI.swift`, `API.swift` |
| P18 | App/helper/provider CLI updates, safe active-run update behavior, single-channel build identity and local-endpoint override isolation, diagnostics/remedies | `UpdateStore.swift`, `ExecutorHelperUpdate.swift`, `CLIUpdate.swift`, `ProductChannel.swift`, diagnostic stores |

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
  onboarding, Island, projects, Activity/search, assistant/coordinator, executor setup and
  delegated consent, application menus and reply notification states. Record native
  notification/chrome differences as platform exceptions. Compare matching Linux screenshots and review overlays during
  L3–L5; track deliberate platform differences separately from visual regressions.
- Aim for pixel accuracy on reusable artwork and app-controlled geometry where inexpensive.
  Font rasterization and desktop chrome are not universal exact-image gates. Record
  tolerances and remaining discrepancies in the visual QA report. Escalate substantial
  redesigns or a large extra polish budget instead of silently expanding effort.

## 4. Architecture and decisions

A Tauri shell hosts a React board and the pinned Three.js Island renderer in WebKitGTK. A
Rust host process owns session storage, HTTP, IPC and OS integration. A separate per-user
Rust executor, built from the same crate, supervises provider CLIs. See
[ARCHITECTURE.md](ARCHITECTURE.md) for the boundaries.

Code sizes at the pinned Mac commit explain the choices below. The island is the only web
code the Mac has; everything else is Swift and does not transfer to a non-Swift stack.

| Mac component | Lines | Reused on Linux |
|---|---|---|
| Island renderer (`island/src`, React and Three.js) | 25,815 | As-is, pinned, in the web view |
| Board screens (`CampusApp/Sources/CampusApp`, SwiftUI) | 26,528 | No; rewritten in React |
| Shared UI (`CampusUI`, SwiftUI) | 4,683 | No; rewritten in React |
| `CampusKit` (models, stores, HTTP, cable, executor) | 72,063 | No; rewritten in Rust and TypeScript against the snapshot |
| `CampusBrokerCore` (CLI supervision) | 7,638 | No; a reference for the Rust executor |

### D1. Desktop shell: Tauri, with the board written in React and TypeScript

**Decided.** Not Electron, not a native toolkit, not Swift on Linux.

- *Why.* The island drops in unchanged and the new board sits beside it in one language and
  one build. Tauri's Rust host is the natural home for the executor (D2), so shell and
  execution share one toolchain. Install size is a few megabytes against Electron's
  80–150 MB, memory is one browser engine lower, startup is faster, and updates are small.
  The same choice leads the Windows PRD, so one board codebase can serve both later.
- *Cost accepted.* Nothing from `CampusKit` transfers; every store and API call is rewritten
  from the OpenAPI snapshot. WebKitGTK is the weakest of the three web views and is supplied
  by the distribution, not bundled, so an old distribution renders with an old engine.
- *Rejected.* Electron: identical features, several times the weight, for a user who runs
  agents and a real browser beside Campus. Swift on Linux with GTK or Qt: reuses `CampusKit`
  but there is no SwiftUI on Linux, so the 31,000 lines of screens are rewritten anyway, on
  a far less travelled packaging path.
- *L0 proves.* The pinned island renders in WebKitGTK on Ubuntu 24.04 under software
  rendering within the budget set in section 8. If it cannot, the fallback is Electron with
  the same React code, so nothing written before the spike is lost.

### D2. Host and executor language: Rust

**Decided.** The Tauri host process and the standalone `campus-linux-executor` binary are
built from one Rust crate.

- *Why.* One language for supervision, HTTP, the outbox and secret handling, written once and
  used by both processes. Rust has first-class Linux primitives for the hard parts: process
  groups, `PR_SET_PDEATHSIG`, cgroups and libsecret. The executor protocol is defined by the
  OpenAPI snapshot, so the Mac broker is a reference to read, not code to port. Execution
  never runs in renderer JavaScript.
- *Cost accepted.* The recovery rules in campus-server's executor recovery drills are
  reimplemented and proven against the same fixtures. Rust is slower to write than Swift or
  TypeScript, and an agent gets fewer first-try compiles.
- *Rejected.* A TypeScript sidecar: faster to write but reintroduces a second runtime beside
  the web view and gives back the weight D1 was chosen for. Ruby: cannot be the Tauri host at
  all, needs a bundled or distribution Ruby for the executor, needs an FFI build for libsecret,
  and makes copying authority code out of campus-server too easy. Ruby's only advantage was
  the owner's familiarity, which matters less for code an agent writes and the owner reviews.

### D3. Secrets: Secret Service for Campus-owned tokens; provider files isolated, not encrypted

**Decided.** This replaces the earlier "no plaintext fallback" sentence, which the Mac client
does not meet either and which blocked local execution. There are two kinds of secret and
Campus controls only one.

| Concern | Mac today | Linux |
|---|---|---|
| Session token and executor token | Login Keychain | Secret Service through libsecret (gnome-keyring, kwallet). No file fallback. |
| Provider OAuth state (Claude, Codex, Gemini, Grok) | Config dir under `~/.campus/credentials/<id>`, bounded by the broker; plain files for every engine except Claude Code, which uses the Keychain on macOS only | Same path, same bound, same `*_CONFIG_DIR`/`*_HOME` variables, mode 0700. Plain files because the provider writes them that way; Campus adds isolation and permissions, not encryption, and says so. |
| API keys | Delivered per attempt by Rails, no-store, environment only | Same. Never on disk. |
| Local IPC secret | 0600 token file | Same |
| Store locked or absent | Broker refuses; Rails authors the message | Session token held in memory for that run only; executor registration withheld with a Rails-authored diagnostic (S1-3). The board still works. |

- *Why.* Rails already owns credential state, readiness, API-key delivery and the rule that a
  config directory sits under the credentials root. Nothing moves to the machine that is not
  on the Mac already; only the store's name changes. A provider CLI rewrites its own file on
  token refresh, so Campus cannot own that file's encryption without racing the provider.
- *Cost accepted.* A desktop with no keyring daemon signs in every launch and cannot run
  agents locally until one is installed. Provider files on an unencrypted home directory are
  readable by any process running as the user, which is true of the provider CLIs without
  Campus too.
- *Rejected.* Encrypting provider directories with a Secret Service key and decrypting to a
  tmpfs per run: possible, but it fights the provider for a file format Campus does not own.

### D4. Packaging and updates: deb and AppImage, Tauri updater, one production channel

**Decided.**

- Two artifacts from one Tauri bundler run: a `.deb` for Ubuntu and Debian, and an AppImage
  for the rest of the matrix. No rpm, snap or Flatpak in release 1. Flatpak's sandbox cannot
  spawn provider CLIs against arbitrary checkouts without defeating itself, so it stays out
  on principle.
- Updates through Tauri's updater with a signing key verified independently of TLS, the
  Sparkle guarantee. One update manifest at `/stable/linux.json` beside the Mac appcast on
  the same host, the same immutable-artifact rule, and rollback by publishing a higher
  version, never a lower one.
- **One channel on Linux: Campus, production.** There is no Campus Dev product for Linux.
  A developer points an unpublished local build at `http://localhost:3001` through a
  build-time flag that cannot be set on a published artifact. Business behaviour never
  branches on it.
- The executor ships inside the app package. The app installs its systemd user unit on first
  authorization, as the Mac app installs its LaunchAgent. There is no separate executor
  download.
- Key custody: one keypair, generated by the owner, private half kept where the Sparkle keys
  live, public half checked into the build configuration. The owner is the release owner.
- *Cost accepted.* In-app update of a deb needs root for `dpkg`, so it prompts through
  polkit; the AppImage updates silently because the user owns the file. An AppImage registers
  its desktop entry itself on first run. WebKitGTK is not bundled in either artifact.
- *Rejected.* An apt repository as the primary update path: Ubuntu-native, but it serves
  only deb users, needs repository signing the Mac does not have, and gives the app no say in
  when an update applies, which the "never replace a running executor unsafely" rule needs.
- *L0 proves.* Which of the two artifacts the current Tauri updater applies in-app, and the
  exact polkit prompt for the deb path.

### D5. Verification: Docker for headless tests, hosted CI on a public repository, a Lima VM for the desktop

**Decided.** An implementer that cannot run its tests on Linux cannot be autonomous, so this
is settled before the first line of code.

1. **Docker, layer 1.** A checked-in `ubuntu:24.04` image builds the Rust crates and the
   React bundle, runs unit and contract tests, and runs WebKitGTK smoke tests under a virtual
   display. The implementing agent runs it on every change, from any host, with no GitHub
   involvement.
2. **Hosted CI, layer 2.** The existing workflow runs the same image and is already gated to
   start the moment the repository is public. **The repository is made public** as part of
   starting implementation; it holds documentation and an API snapshot already public in
   `campus-macos`. Self-hosted runners stay forbidden, for the reason the workflow states.
3. **Lima VM, layer 3.** An Ubuntu 24.04 VM on the owner's Mac, created and driven by the
   agent over `limactl shell`, with a real systemd and a real `loginctl` session,
   gnome-keyring and a Wayland compositor on a virtual display. It installs the deb and
   proves the four things a container cannot: Secret Service prompts, the user unit stopping
   on graphical logout and restarting on login, the polkit update prompt, and the island
   rendering in WebKitGTK. Screenshots for the visual comparison in section 3 come from the
   compositor. No human runs a machine for release acceptance.
4. **GPU frame rate is measured, not gated.** The app's diagnostics screen reports island
   frame time, and real Ubuntu machines report it back. The release gate is the
   software-rendering budget in section 8; hardware numbers are recorded as they arrive.

- *Cost accepted.* The owner's Mac is Apple Silicon, so the VM is arm64. The x86_64 deb and
  AppImage are built and tested headless in CI and never run on a desktop until a real user
  has one; the matrix in section 6 says so. A software-rendering pass is conservative and a
  fail there is not proof of a fail on hardware.
- *Rejected.* Paid hosted minutes on a private repository: works, ends the day the repository
  goes public anyway. An EC2 Ubuntu desktop over RDP: closes the x86_64 gap but costs money
  idle, has no GPU, and is driven through a remote display rather than a shell. Add it only if
  x86_64-specific bugs appear.

### D6. Server prerequisites: S1 is five named campus-server PRs

**Decided.** Each is one PR in `yuric/campus-server` with one card on that building, in this
order, so the client never waits on wording. The executor protocol itself needs no change; a
Linux executor speaks it today. The five-executor cap per account stays.

| # | Item | Why it gates the client |
|---|---|---|
| S1-1 | Platform-neutral copy in the public contract. The spec mentions the Mac 66 times; endpoint summaries say "registered Macs" and "this Mac", and error strings the client renders verbatim say "on this Mac". | The client must not rewrite a single server string. Copy only, so it is first. |
| S1-2 | `platform` and `arch` in the executor registration capability observation, and readiness derived per platform rather than from the Mac engine set. | Rails must know it is judging Linux. The Antigravity account-isolation limit is a Mac-binary fact Rails must not apply blindly. The one guarded change here; it needs a careful review. |
| S1-3 | Two normalized diagnostics: "no secure credential store on this desktop" and "credential store locked", with Rails-authored reason, severity and message. | D3's fallback renders a server sentence, not a client one. |
| S1-4 | A Linux release record, or a platform dimension on the Mac release catalog under the admin endpoints. | Version skew and the supported protocol window are keyed to Mac releases today; without this Rails cannot tell a Linux build it is too old. |
| S1-5 | Confirm the hosted CLI-subscription login path is platform-neutral. The `broker_login` endpoints have Rails call a broker on localhost, which only works when Rails runs on the same machine; hosted Macs sign in through the executor-side binding. | Not verified end to end at this revision. If it leans on the Mac broker, it is real server work and must be known before L2, not found in it. |

### D7. The boundary is a failing build, not a principle

**Decided.** A CI job, `scripts/check-client-boundary.sh`, fails any pull request whose
client source contains a provider, engine, model, stage, priority or credential-kind
literal, matches on an error substring or message prefix, or carries a workflow-transition
table. The vocabulary the API publishes is permitted only as a decoded field, never as a
constant. A test fixture that must spell a provider name carries an explicit
`campus-boundary: allow` comment with a reason. This is the judgement campus-server's client
policy engine applied to the retired web client, brought in-repo so it runs on every Linux
pull request. [ARCHITECTURE.md](ARCHITECTURE.md) carries the authority table the gate
enforces, word for word the same as the Mac and Windows documents.

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
- Bind credentials, caches and IPC to the exact API origin, product channel, account and
  island. An endpoint switch never reuses existing credentials; redirects cannot forward
  secrets across origins. Deep links cannot change the endpoint or its trust policy.
  Sign-out clears consent/account data
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
- Provider OAuth and config files follow D3: provider-owned, isolated under the credentials
  root with the Mac's bounds and permissions, plaintext because the provider writes them so.
  Campus-owned tokens never leave Secret Service. Do not claim all provider credentials are
  portable, and do not add a file fallback for Campus-owned tokens.
- The boundary in this section is enforced by the gate in D7 on every pull request.

## 6. Compatibility contract

One source tree is not one binary for every CPU/runtime. Publish exact OS/image, CPU,
desktop/session, GPU/driver and artifact identities. This is a **test matrix to be earned**,
not a claim of existing support:

| Tier | Targets and release rule |
|---|---|
| First verified | Ubuntu 24.04 LTS x86_64, GNOME, Wayland and X11. Confirm the first user's actual Ubuntu/hardware in L0 and add that combination if different. |
| Broad desktop | Ubuntu 22.04 compatibility where dependencies allow, Debian stable, current stable Fedora GNOME/KDE and Arch/KDE at a recorded snapshot. Version support is earned by installed-package tests. |
| Architectures | x86_64 is the release architecture: built and tested headless in CI (D5 layers 1–2), desktop-verified only once a real x86_64 user reports. arm64 is built and desktop-verified in the Lima VM (D5 layer 3) and released once provider CLIs are confirmed on it. Untested architectures are never advertised supported. |
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
| L0: inventory/spikes | This document merged; owner starts implementation | Expand P01–P18 into action cases; capture visual references; stand up D5 layers 1 and 3; prove the residual risks D1 and D4 name (island in WebKitGTK under software rendering; which artifact the updater applies in-app); one supervised CLI end to end. No ADRs: the decisions are in section 4. |
| S1: API prerequisites | None; opens in parallel with L0 | The five campus-server PRs in D6, merged with contract tests, in order S1-1 to S1-5 |
| M1: renderer export | L0; S1 if needed | Mac-owned platform-neutral host/export changes where needed; exact merged-source artifact/manifest; no renderer fork |
| L1: foundation | L0, required S1 contracts | Snapshot/generator checks, shell, secure sessions, endpoint isolation and the build-time local-endpoint override, refresh/unknown-version behavior; P01–P03 |
| L2: execution | L0, required S1 contracts | Per-user service/register/bind/login/workspaces, claim-to-result/cancel/recovery vertical slice; P15–P17; one CLI initially is spike scope, not release scope |
| L3: workflows | L1; L2 for local actions | P04–P11/P13–P14; all supported offered providers/actions, assistant/consent, attachments/speech and shared semantic fixtures |
| L4: Island/integration | L1, M1, L2/L3 actions | P12, restricted host bridge, accessibility and integrated local/remote operation |
| L5: distribution/acceptance | L1–L4 | P18, deb and AppImage, signed updates, recovery, the single production channel, advertised matrix, isolated live QA in the Lima VM, full parity sign-off and installable artifacts |

Linux owns client/service/packages. Server owns Rails/OpenAPI/deploy. Mac owns renderer
producer changes. Cross-repository work uses separate PRs in contract → producer →
snapshot/consumer order. Dependencies clear on verified merged outcomes, not open PRs.

## 8. Acceptance and release evidence

1. Expand and complete every P01–P18 case against the pinned source. Record expected API
   behavior, observed Linux behavior, test/receipt and exceptions. No missing row is hidden
   by a percentage; exceptions need a recorded owner decision.
2. With an installed authorized helper and secure credential store, a new Linux-only user
   onboards, connects an account, binds a repository, lands an agent,
   creates/approves work, observes actual local edits/result, cancels the process tree,
   closes/reopens the UI and recovers an executor restart without a Mac. Also dispatch work
   from another authorized client to this Linux executor with its UI closed; verify claims,
   real repository edits, event delivery and remote cancellation. Graphical logout ends
   supervision even with an SSH session open, and graphical login restores it safely.
3. Authorized remote control works with local execution unavailable. Offline/queued state
   is truthful, and remote failure cannot cause unauthorized local fallback.
4. The D7 boundary gate passes on every pull request. Contract fixtures cover unknown versions/withheld actions, confirmations, tenant isolation,
   expiry/revoke, malformed host messages, ambiguous writes, duplicate/out-of-order events,
   stale cursors, attachment errors and redaction. Linux-only adapters get real integration tests.
5. Service tests cover lost lease, provider exit, disk full, interrupted delivery, suspend,
   keyring lock, workspace escape, app/helper mismatch and active-run updates; no captured
   diagnostic/package contains secrets. Account switching cannot leak credentials/data.
6. Paired Mac/Linux screenshots meet the visual fidelity criteria above, with recorded
   platform differences and remaining discrepancies; do not claim pixel perfection without
   evidence. Installed packages pass on every advertised combination, including accessibility,
   graphics/audio, service lifecycle, uninstall and upgrade. Measure startup/board latency,
   Island frame time and idle CPU/RAM. The release gate for frame time is set in L0 from the
   Lima VM under software rendering; real-hardware frame time is reported by the diagnostics
   screen and recorded, never gated (D5). Every check in this item except real-hardware
   frame time runs without a human, in D5 layers 1–3.
7. Release receipts include source/contract/renderer SHAs, package checksums/signatures,
   build provenance, commands/results, compatibility matrix, known issues and rollback/recovery.
   A merged planning PR or a CI-only build is not a delivered Linux app.
8. Live QA uses an isolated account/island and disposable repositories/agents, never the
   owner's working data, and runs in the Lima VM. Credentials and release keys use
   authorized secure channels.

## 9. Estimates and open evidence

Voice estimates were 2–3 working days for specification/parity analysis and 4–8+ weeks
for implementation/verification with agent assistance. They are planning ranges, not
promises, and have not been validated by a Linux spike. This PR proposes the specification;
it does not claim completed portability testing or a complete button-level inventory.
L0 replaces estimates with measured milestone ranges and critical-path risks.

Open evidence, after the 2026-10-15 decisions: the first user's actual Ubuntu release, CPU
and GPU; provider CLI availability and login behaviour on Linux and on arm64; the two L0
spikes named in D1 and D4; and the outcome of S1-5. Everything else that was open at the
2026-10-13 revision is decided in section 4. Ask the owner only for product, spend,
credential or trust decisions that those sections do not already answer. Implementation
starts on the owner's explicit request, not on merge.
