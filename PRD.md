# PRD: Campus for Linux

**Revision:** 2026-10-16. **Status:** implementation authorized 2026-10-16; bootstrap in progress.
**Product:** a Linux desktop client and per-user local execution service.

The seven decisions in [section 4](#4-architecture-and-decisions) were made by the owner on
2026-10-15, one at a time, with the trade-offs recorded beside each. They are not proposals.
L0 proves the residual risks each one names; it does not reopen the choices. The owner explicitly started implementation on 2026-10-16, coordinated by LINUX-20261016.
Engineering clarifications below preserve D1–D7; repository policy tooling is not app
implementation. No runtime, app scaffold or product build is introduced by this revision.
The [implementation gates](docs/implementation-gates.md) define the remaining contract
and acceptance evidence. They refine execution of these decisions without reopening them.

## 1. Owner requirements and outcome

The owner requests macOS feature parity, both local and remote agents, and broad Linux
compatibility. The first user's distribution is Ubuntu. The owner authorized implementation and cards #981–#999. Credentials, paid services and
release publication remain subject to the specific authority recorded on those cards.

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

The local `docs/api/.source` records `campus@ab114c50b2cc881c9b3b65315355e2d469751dd0`;
its snapshot has 132 paths, versus 292 in the pinned server above. These counts establish
drift, not compatibility. S2 in section 7 owns the verified post-S1 import and its path
migration before L1 generates bindings. This documentation revision does not refresh it.

## 3. Feature parity inventory

All rows are **not implemented**. The action-level [acceptance inventory](docs/acceptance/inventory.md)
and [fixed visual/renderer protocol](docs/acceptance/visual-protocol.md) track bootstrap evidence. Each needs an owner, exact API operation/schema references,
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

The [implementation gates](docs/implementation-gates.md) make the non-portable mechanisms
explicit: P08/P16 native-session discovery, attach and exact resume; P09 PTY login;
P06 Linux speech; P13 task-link activation; P12 the verified renderer export and bridge;
and P18 the helper-update handback protocol. A failed native resume must never silently
start a fresh conversation. Missing Linux mechanisms remain parity gaps until proven or
explicitly dispositioned by the owner.

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
| Island renderer (`island/src`, React and Three.js) | 25,815 | Verified built renderer export from the pinned producer; no wholesale source-directory import |
| Board screens (`CampusApp/Sources/CampusApp`, SwiftUI) | 26,528 | No; rewritten in React |
| Shared UI (`CampusUI`, SwiftUI) | 4,683 | No; rewritten in React |
| `CampusKit` (models, stores, HTTP, cable, executor) | 72,063 | No; rewritten in Rust and TypeScript against the snapshot |
| `CampusBrokerCore` (CLI supervision) | 7,638 | No; a reference for the Rust executor |

### D1. Desktop shell: Tauri, with the board written in React and TypeScript

**Decided.** Not Electron, not a native toolkit, not Swift on Linux.

- *Why.* The shared island renderer is reused through M1's verified export and host bridge;
  the new board sits beside it in one language and one build. Tauri's Rust host is the
  natural home for the executor (D2), so shell and
  execution share one toolchain. Avoiding a bundled Chromium runtime is the weight
  rationale; package size, installed size, memory and startup are measurements for L0,
  not a few-megabyte promise for both formats.
  The same choice leads the Windows PRD, so one board codebase can serve both later.
- *Cost accepted.* Nothing from `CampusKit` transfers; every store and API call is rewritten
  from the OpenAPI snapshot. WebKitGTK compatibility must be proven with the pinned island.
  The deb uses distribution WebKitGTK; the AppImage bundles WebKitGTK and other runtime
  dependencies and is materially larger. It still depends on the host kernel, glibc and
  graphics stack. See [Tauri's AppImage guidance](https://v2.tauri.app/distribute/appimage/).
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
- *Cost accepted.* The four crash boundaries in campus-server's executor recovery drills
  are reproduced in Linux tests; no ready-made cross-platform fixture suite is assumed.
  Interactive provider login uses a PTY; ordinary execution keeps its non-interactive pipe
  protocol. Rust is slower to write than Swift or TypeScript, and an agent gets fewer
  first-try compiles.
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
| Isolated provider OAuth state (Claude Code, Codex, Grok) | The broker derives `<root>/scopes/<base64url(credential_scope)>`; Claude Code namespaces its Mac Keychain item by the config-path bytes, while other provider state is file-backed | Derive the same relative scope encoding locally under the trusted credentials root; preserve exact path bytes in the engine's config/home variable, mode 0700. Provider-owned files remain plaintext; verify each Linux CLI's actual storage in L0. No server-supplied directory. |
| Antigravity (`agy`) subscription/ambient login | No config-directory variable; the pinned CLI uses the login Keychain on macOS and cannot isolate accounts through that directory | Linux storage and identity scope require L0 evidence. Report observations for S1-2 readiness; do not invent per-account isolation or a Linux Keychain equivalent. Gemini is the API-key engine in the pinned server mapping, not this OAuth path. |
| API keys | Delivered per attempt by Rails, no-store, environment only | Same. Never on disk. |
| Per-run Campus credentials | Claim `campus_agent_token` and the attempt MCP credential have fixed environment injection contracts | Memory and the authorized child's fixed environment only; no durable outbox, argv, renderer or diagnostics. Honor authority, expiry/revoke and attempt scope from the contract. |
| Local IPC secret | 0600 token file | Retain a distinct 0600 local token; this does not select loopback TCP. L0 must prove peer authentication before secret transmission and principal-scoped IPC. |
| Store locked or absent | Broker refuses; Rails authors the message | Session token held in memory for that run only; executor registration withheld with a Rails-authored diagnostic (S1-3). The board still works. |

- *Why.* Rails owns credential state, readiness, API-key delivery and opaque scope issuance.
  The trusted executor derives and confines local paths, as the pinned Mac broker does.
  The default root is `~/.campus/credentials`, with a trusted local
  `CAMPUS_CREDENTIALS_ROOT` override; scopes must be strict descendants both lexically and
  after symlink resolution. A scope is never interpreted as a path. A provider CLI rewrites
  its own file on token refresh, so Campus cannot own that file's encryption without racing
  the provider.
- *Cost accepted.* A desktop with no keyring daemon signs in every launch and cannot run
  agents locally until one is installed. Provider files on an unencrypted home directory are
  readable by any process running as the user, which is true of the provider CLIs without
  Campus too.
- *Security boundary.* Secret Service protects persistent Campus-owned tokens; it is not a
  per-application sandbox against arbitrary processes running as the same user. L0 must
  document and test that exposure, child environment/descriptor handling and crash capture
  under [G4](docs/implementation-gates.md#g4-host-and-executor-trust-boundaries).
  This correction does not authorize broader token access or claim full Mac ACL parity.
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
  download. The durable installation and update contract below applies to both formats.
- Key custody: one keypair, generated by the owner, private half kept where the Sparkle keys
  live, public half checked into the build configuration. The owner is the release owner.
- *Cost accepted.* In-app update of a deb needs root for `dpkg`, so it prompts through
  polkit; the AppImage updates silently because the user owns the file. An AppImage registers
  its desktop entry itself on first run. The deb declares distribution WebKitGTK packages;
  the distribution supplies their security updates. The AppImage carries its WebKitGTK
  runtime; Campus must rebuild and sign a new AppImage to deliver fixes to bundled
  dependencies. Release receipts record actual runtime versions and an SBOM per format.
- *Rejected.* An apt repository as the primary update path: Ubuntu-native, but it serves
  only deb users, needs repository signing the Mac does not have, and gives the app no say in
  when an update applies, which the "never replace a running executor unsafely" rule needs.
- *L0 proves.* Which of the two artifacts the current Tauri updater applies in-app, and the
  exact polkit prompt for the deb path. Pin Tauri/bundler/updater versions and verify each
  artifact end to end; updater behavior is version-dependent (see the
  [updater changelog](https://github.com/tauri-apps/plugins-workspace/blob/v2/plugins/updater/CHANGELOG.md)).
  [G5](docs/implementation-gates.md#g5-signed-updates-and-package-selection) requires
  package-specific manifest entries, privileged verification of the installed deb bytes,
  and no application-collected administrator password. One manifest still serves both
  formats and architectures on the single production channel.

#### Bundled helper installation and update contract

An AppImage runs from a temporary mount that is cleaned up when its payload exits
([AppImage runtime](https://docs.appimage.org/introduction/software-overview.html#runtime)).
The systemd unit must never point into that mount or depend on the UI keeping it alive.

- On first authorization, extract the bundled helper and its required runtime files from
  the verified package into a private, versioned installation under the user's XDG data
  directory, owned by that user with mode 0700 and no writable path components owned by
  another user. A manifest records package signature/checksum, helper bytes, architecture and
  protocol version. Use the same installation contract for deb and AppImage. This is a
  local copy from the app bundle, not a second download or an independently updated product.
- The user unit launches the selected installed helper by a stable absolute path. It is
  bound to the graphical session, not merely the longer-lived systemd user manager; last
  graphical logout stops supervision even while SSH/TTY sessions remain. Do not enable
  lingering. Graphical login restores the authorized service without opening the UI;
  missing or locked Secret Service withholds claims under D3/S1-3.
- Before promotion, stage and verify the new helper, check app/helper/protocol and durable
  state compatibility, and fence new claims. Drain active attempts or use the existing
  lease-safe cancellation/reconciliation protocol; never start a replacement claimant
  while the old process or its children still own an attempt. Preserve and reconcile the
  durable outbox, including unacknowledged events and its acknowledgement cursor, and
  attempt ownership across the switch. Enforce one supervisor per
  user, including concurrent UI launches and simultaneous old/new app packages.
- Atomically promote the installed version only after a successful quiesce. Retain the last
  compatible helper until startup, lease reconciliation and outbox recovery succeed.
  A crash at any staging/promotion step must recover to one compatible supervisor, without
  duplicate execution or lost events. If state cannot safely roll back, withhold claims
  and recover forward. Local failed-install recovery does not change D4's rule that a
  published rollback is a new, higher signed version.
- Moving, replacing or deleting the outer AppImage must not strand an authorized service;
  its installed copy remains usable until explicitly disabled or uninstalled. Removing
  the deb likewise must not leave a unit targeting removed package files. Both formats
  document a per-user uninstall path available without the UI: stop/fence/reconcile work,
  disable/remove the unit and installed helper versions, and clear Campus registration
  credentials. Do not silently delete provider-owned credentials or user repositories.
- L0 specifies and L2/L5 prove these transitions for each installed format: UI closed and
  remote dispatch; move/delete the outer package; logout with SSH open; reboot/login without
  UI launch; locked keyring; concurrent starts; update during active work; interruption at
  every promotion boundary; incompatible state; rollback; uninstall. Receipts must show
  unit paths, helper identity, process/lease ownership and outbox continuity, with secrets
  redacted. This is an acceptance contract, not a service implementation in this PRD.

The Linux lifecycle must also implement the existing helper-update report/confirmation
contract, with claim-supplied grace periods and truthful `executor_helper` and
`helper_update_monitor` observations. [G3](docs/implementation-gates.md#g3-supervision-recovery-and-live-updates)
defines retry versus intentional-stop exits, sign-out precedence, authorized epoch
preservation, singleton locking and crash-recovery receipts. A package replacement or UI
relaunch must not directly restart a busy helper.

### D5. Verification: Docker for headless tests, hosted CI on a public repository, a Lima VM for the desktop

**Decided.** An implementer that cannot run its tests on Linux cannot be autonomous, so this
is settled before the first line of code.

1. **Docker, layer 1 (planned).** A checked-in `ubuntu:24.04` verification image builds the
   Rust crates and React bundle, runs unit and contract tests, and runs WebKitGTK smoke
   tests under a virtual display. The implementing agent runs it on every change, from any
   host, with no GitHub involvement. L0 pins the image digest/toolchains and separates verification from the
   release build baseline below. #981 supplies the repository-policy image/commands; real
   product builds/tests are added at their owning seams, not claimed by bootstrap CI.
2. **Hosted CI, layer 2 (planned).** Today `.github/workflows/docs.yml` checks Markdown links,
   OpenAPI parsing and the boundary policy (including its regression tests), gated on public
   visibility. #981 adds `.github/workflows/linux-verification.yml` with architecture and
   receipt admission jobs for repository policy; a Linux app test is still pending. L0
   extends required hosted jobs to run the same checked-in
   image/commands as layer 1 for x86_64 and arm64, record image digest, source SHA,
   architecture, commands/results and artifact checksums, and fail on a skipped required
   job or missing receipt. Record the required check names and branch-protection setup in
   that implementation PR. **The repository is made public** as part of
   starting implementation; it holds documentation and an API snapshot already public in
   `campus-macos`. Self-hosted runners stay forbidden, for the reason the workflow states.
3. **Lima VM, layer 3.** An Ubuntu 24.04 VM on the owner's Mac, created and driven by the
   agent over `limactl shell`, with a real systemd and a real `loginctl` session,
   gnome-keyring and a Wayland compositor on a virtual display, plus an X11 test session.
   It installs both deb and AppImage separately and proves the desktop integrations:
   Secret Service prompts, the user unit stopping
   on graphical logout and restarting on login, the polkit update prompt, and the island
   rendering in WebKitGTK, as well as D4's durable helper/update scenarios. Screenshots for
   the visual comparison in section 3 come from the compositor. No human runs a machine
   for prerelease acceptance.
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

**Release build baseline.** Ubuntu 24.04 remains the local/hosted verification environment.
It is not evidence that binaries built there run on Ubuntu 22.04. L0 selects and pins the
oldest compatible release build image/toolchain that provides the required WebKitGTK ABI
(22.04 if it is included), builds both formats from it per architecture, and runs those
exact artifacts through the 24.04 verification layers. Record glibc/ABI minimums and
bundled versus host libraries; test installation/startup on every older distribution
before advertising it. A 24.04-produced binary is not silently relabeled compatible.
If the baseline cannot cover a target, record it as unverified/blocking evidence under
section 6, not as a new owner decision to drop that target. This follows
[Tauri's oldest-base guidance](https://v2.tauri.app/distribute/appimage/).

**Evidence tiers.** The accepted x86_64 desktop gap does not block an explicitly labeled
headless-tested preview. It does block calling that artifact desktop-verified or full
parity. arm64 desktop receipts apply only to the exact Lima image, session and package
tested, with provider CLI availability proven before release. Preview/full-parity are
maturity labels on the single production channel, not a second product or update feed.
Section 8 defines which evidence each label requires; it adds no paid infrastructure or
human-run prerelease QA requirement.

### D6. Server prerequisites: five requirements, consolidated delivery

**Decided; owner consolidation approved 2026-10-16.** Keep S1-1–S1-5 and their
internal review order in one server product PR (#984); policy/export/release tooling stays
in a separate server PR (#983). The real hosted round trip remains #986, after #985 imports
the merged contract. Consolidating PRs does not waive any requirement or evidence. Retain execution protocol v2 and the existing
claim/lease/heartbeat/report flow; Linux readiness is not proven by registration alone.
The pinned server requires Mac-shaped workspace roots and some paths call a local Mac
broker. S1 must close those platform gaps before L2. Existing capability fields such as
`broker_execution_capacity` and `helper_update_monitor` are already in the pinned server
schema; preserve compatible wire names rather than renaming them for appearance.
The five workstreams below, their order and the five-executor cap per account stay.

| # | Item | Why it gates the client |
|---|---|---|
| S1-1 | Platform-neutral copy in the public contract and runtime diagnostics, including credential/login, CLI-update and speech messages. Audit the pinned source rather than relying on an occurrence count. | The client must not rewrite a server string. Copy only, so it is first; a wire identifier is not renamed as a copy edit. |
| S1-2 | `platform` and `arch` observations; platform-aware workspace-root/readiness, provider identity scope and CLI-update eligibility; explicit native-session and capability contracts required by Linux. | Rails must judge Linux facts rather than Mac-only paths or engine assumptions. G1 inventories existing fields versus genuine gaps, including hosted native-session transport; schema/behavior changes preserve existing Mac consumers. |
| S1-3 | Two normalized diagnostics: "no secure credential store on this desktop" and "credential store locked", with Rails-authored reason, severity and message. | D3's fallback renders a server sentence, not a client one. |
| S1-4 | A Linux release record, or a platform dimension on the Mac release catalog under the admin endpoints. | Gates Linux release identity and P18 diagnostics/catalog integration. Protocol v2 compatibility already has a platform-neutral check; a release record is not what makes that check possible. |
| S1-5 | Confirm the hosted CLI-subscription login path is platform-neutral. The `broker_login` endpoints have Rails call a broker on localhost, which only works when Rails runs on the same machine; hosted Macs sign in through the executor-side binding. | Not verified end to end at this revision. If it leans on the Mac broker, it is real server work and must be known before L2, not found in it. |

The [G1 contract ledger](docs/implementation-gates.md#g1-server-contracts-and-snapshot-handoff)
maps detailed evidence into these five prerequisites. S1-5 remains open until its
end-to-end proof passes. S2 is the Linux-owned snapshot handoff. The coordinator created the native dependency graph; a Ready card does not waive evidence.

### D7. The boundary is a failing build, not a principle

**Decided.** Rails owns domain decisions. Presentation code consumes API fields, not local
provider/model catalogs, compatibility or workflow tables, or interpretations of error
text. Two narrowly reviewed uses of identifiers do not transfer authority to the client:

- Generated transport types may contain enum literals copied from a verified pinned server
  contract. Record the server SHA, snapshot hash, generator/version and regeneration check;
  generated enums are wire types, not locally maintained capability or display catalogs.
- Trusted executor/OS adapters may bind a server engine identifier to a locally approved
  executable, argv protocol and isolated credential location. They enforce local process
  and filesystem safety and report facts; Rails still decides availability, compatibility,
  readiness, wording and authorized work. A server payload cannot supply an arbitrary
  executable, shell command or credential path. Unknown bindings withhold execution and
  report an observation for Rails to interpret. The pinned server already expects this
  separation in its [executor broker contract](https://github.com/yuric/campus-server/blob/d35361542b895a4fd73c838b1be3531ceea5d5fd/api/app/services/executor_broker_contract.rb).

`scripts/check-client-boundary.sh` enforces the bounded lexical checks documented in
[the boundary policy](docs/client-boundary.md), across Rust/JS/TS including `src-tauri`.
It checks known quoted literals, common error-substring calls and named transition tables.
Fixture-only, same-line allow comments require a nonempty reason. Production exceptions
require an exact reviewed file/hash with provenance; there is no directory-wide exemption.
The manifest starts empty. Regression probes run even before product source exists.
This is not a port of campus-server's semantic policy engine or proof of every business
rule: aliases, computed expressions and new vocabulary still require authority review,
contract tests and future language-aware enforcement. The authority table remains in
[ARCHITECTURE.md](ARCHITECTURE.md).

## 5. API authority and safety requirements

- Rails supplies capabilities/catalogs, wording, workflow/ordering, confirmations,
  validation and normalized failures. Unknown contract/action versions withhold actions;
  do not port Mac's remaining client-rule drift.
- Generate bindings from a verified pinned OpenAPI snapshot. The existing Linux snapshot
  is not assumed current. Missing schemas/operations merge in `campus-server` first.
  S2 records the merged post-S1 SHA and exporter layout; G1 requires regeneration checks,
  scoped unknown-value handling, sensitive-field redaction and the host-owned Cable contract.
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
  D7's reviewed adapters own the local bindings and enforce bounds on server-issued opaque
  credential scopes; presentation code cannot choose binaries or construct credential paths.
  Local service identity is distinct from account and executor credentials.
- Revalidate lease/attempt ownership, preserve ordered acknowledged outbox delivery,
  and avoid duplicate execution across restart/suspend/partition/revoke. CLI exit alone
  cannot establish domain outcome. Updates cannot replace a running helper unsafely.
- OS adapters report observed facts; Rails interprets readiness/faults. Reject workspace
  symlink escapes and cross-account access; support approved worktrees/Git authentication
  and recovery/cleanup without deleting user modifications.
- Provider OAuth and config files follow D3: provider-owned, isolated under the credentials
  root where that provider supports isolation, plaintext because the provider writes them so.
  Persistent Campus-owned session/executor tokens use Secret Service; D3 separately defines
  memory-only runs and per-attempt credentials. Do not claim all provider credentials are
  portable, and do not add a file fallback for Campus-owned tokens.
- D7's gate checks the documented syntax on every eligible pull request; review and contract
  tests must establish the semantic boundary this section requires.

[G2–G7](docs/implementation-gates.md) supply the required credential, recovery, IPC/process,
privileged update, PTY/speech/link and webview acceptance cases. They are future test
obligations, not evidence that an implementation or security guarantee already exists.

## 6. Compatibility contract

One source tree is not one binary for every CPU/runtime. Publish exact OS/image, CPU,
desktop/session, GPU/driver and artifact identities. This is a **test matrix to be earned**,
not a claim of existing support:

| Tier | Targets and release rule |
|---|---|
| First desktop target | Ubuntu 24.04 LTS, GNOME, Wayland and X11. x86_64 desktop evidence remains outstanding under D5; arm64 Lima evidence covers only its recorded configuration. Confirm the first user's actual Ubuntu/hardware in L0 and add that combination if different. |
| Broad desktop | Ubuntu 22.04 compatibility where dependencies allow, Debian stable, current stable Fedora GNOME/KDE and Arch/KDE at a recorded snapshot. Version support is earned by installed-package tests. |
| Architectures | x86_64 is the primary release architecture: deb and AppImage built/tested headless in CI (D5 layers 1–2), labeled preview with desktop unverified until real x86_64 evidence arrives. arm64 runs both formats in the Lima VM (D5 layer 3) and is released once provider CLIs are confirmed on it. Section 8's evidence labels apply per artifact, architecture and session. Untested combinations are never advertised supported. |
| Additional systems | Non-systemd desktops require a designed and verified equivalent graphical-session supervisor; no alternate supervisor exists yet. They, musl/Alpine, NixOS and immutable/custom systems require explicit packaging/runtime evidence before a support claim. |

Cover locked/missing keyring, unavailable WebGL/GPU/software rendering, high DPI/multiple
monitors, suspend/resume, microphone permissions and file chooser behavior. Require complete
keyboard workflows, visible focus, screen reader labels/announcements, scaling/contrast
and reduced motion. Island failure leaves board/task controls usable but does not count
as Island parity. Broader compatibility is designed in, never inferred from one Ubuntu run.

## 7. Delivery sequence and repository ownership

Each milestone has a bounded reviewable outcome, exact checks, owner and handoff containing
repository/commit, contracts, artifacts, results and remaining gaps. LINUX-20261016 created
cards #981–#999 with native dependencies after the owner authorized implementation.

| Milestone | Dependencies | Outcome and gate |
|---|---|---|
| L0: inventory/spikes | Document merged; owner start authorized 2026-10-16 | Expand P01–P18 and G1–G8 into action cases; fix G8's performance/visual criteria before measuring; capture references; wire D5 layers 1–3; pin the release build baseline; prove D1/D4 risks and G2–G7 platform mechanisms. One supervised CLI end to end after its S1 dependencies merge. No ADRs: the decisions are in section 4. |
| S1: API prerequisites | None; opens in parallel with L0 | The consolidated D6 product PR (#984), separate policy PR (#983), and hosted proof (#986), preserving S1-1–S1-5 |
| S2: verified contract import | Required S1 changes merged | Linux-owned export PR from a recorded merged server SHA containing those changes; verify provenance/fixtures and move snapshot references/checks with the export layout. G1 defines receipts; no handwritten schema edits. |
| M1: renderer export | L0; S1 if needed | Mac-owned platform-neutral host/export changes where needed; exact merged-source artifact/manifest; no renderer fork |
| L1: foundation | L0, S2 for required S1 contracts | Snapshot/generator checks, shell, secure sessions, endpoint isolation and the build-time local-endpoint override, refresh/unknown-version behavior; P01–P03 |
| L2: execution | L0, S2 for required S1 contracts | Per-user service/register/bind/PTY login/workspaces, claim-to-result/cancel/recovery and native-session attach/exact resume; P15–P17; one CLI initially is spike scope, not release scope |
| L3: workflows | L1; L2 for local actions | P04–P11/P13–P14; all supported offered providers/actions, assistant/consent, attachments/speech and shared semantic fixtures |
| L4: Island/integration | L1, M1, L2/L3 actions | P12, G7's restricted presentation/mutation/lifecycle bridge and CSP, accessibility and integrated local/remote operation |
| L5: distribution/acceptance | L1–L4 | P18, deb and AppImage, signed updates, recovery, the single production channel, advertised matrix and isolated live QA in the Lima VM. Publish installable artifacts with section 8's earned evidence labels; full parity sign-off requires all P01–P18 evidence, with D5's x86_64 desktop gap explicit until closed. |

Linux owns client/service/packages. Server owns Rails/OpenAPI/deploy. Mac owns renderer
producer changes. Cross-repository work uses separate PRs in contract → producer →
snapshot/consumer order. Dependencies clear on verified merged outcomes, not open PRs.

## 8. Acceptance and release evidence

These are full-parity requirements. D5 permits preview publication before all desktop
evidence exists; it does not turn missing evidence into a pass or remove a P01–P18 case.
Record status and receipts separately for each `(package format, architecture, OS image,
desktop/session)` tuple. Wayland success is not an X11 pass, and deb success is not an
AppImage pass. No combination has passed today.

| Publication label | Required evidence | Outstanding evidence/claim limit |
|---|---|---|
| Headless-tested preview (x86_64 under D5) | Layers 1–2: unit/contract/boundary checks, build/package/signature/provenance, dependency/ABI checks, virtual-display WebKitGTK smoke, and headless executor recovery tests for each artifact | Desktop login/keyring/polkit, graphics/audio/accessibility, installed lifecycle and visual parity remain explicitly unverified. Publish a gap list; do not advertise desktop support or full parity. |
| Desktop-verified preview (initially arm64 Lima) | The headless checks plus layer 3's installed deb and AppImage runs, each on recorded Wayland and X11 sessions; D4 helper lifecycle/update/uninstall, Secret Service, provider CLI/login evidence and desktop cases below | Receipts apply only to tested VM/session/package combinations. List incomplete P01–P18 cases and broader distributions as gaps; real-GPU frame rate remains informational. |
| Full parity for a declared combination | Every applicable P01–P18 case and items 1–8 below passes with receipts, or has an explicit owner disposition; installed desktop evidence for that exact combination | An x86_64 artifact cannot inherit arm64 VM desktop results. D5 accepts waiting for real-user evidence; until it arrives, x86_64 keeps the preview label. |

Release pages and receipts carry these labels/gaps per download. They do not introduce a
new update channel. Retaining `stable/linux.json` does not itself certify parity.

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
4. The D7 boundary gate and its regression suite pass on every eligible pull request;
   generated bindings pass provenance/regeneration checks and reviewed adapters pass
   contract and safety tests. Contract fixtures cover unknown versions/withheld actions,
   confirmations, tenant isolation,
   expiry/revoke, malformed host messages, ambiguous writes, duplicate/out-of-order events,
   stale cursors, attachment errors and redaction. Linux-only adapters get real integration tests.
5. Service tests cover lost lease, provider exit, disk full, interrupted delivery, suspend,
   keyring lock, workspace escape, app/helper mismatch and all D4 install/update/recovery
   transitions for both package formats; no captured
   diagnostic/package contains secrets. Account switching cannot leak credentials/data.
6. Paired Mac/Linux screenshots meet the visual fidelity criteria above, with recorded
   platform differences and remaining discrepancies; do not claim pixel perfection without
   evidence. Installed packages pass on every advertised combination, including accessibility,
   graphics/audio, service lifecycle, uninstall and upgrade. Measure startup/board latency,
   Island frame time and idle CPU/RAM. Fix the numeric frame-time budget and G8's repeatable
   Lima/software-rendering protocol before the first candidate measurement; a result cannot
   set its own passing threshold. D1's fallback remains unchanged. Real-hardware frame time
   is reported by the diagnostics screen and recorded, never gated (D5). Every check in this item except real-hardware
   frame time is automated for the D5 Lima combinations, in layers 1–3. D5 supplies no
   x86_64 desktop environment; those cases remain unverified for its preview, and future
   real-user receipts must identify the exact package/system and checks performed.
7. Release receipts include source/contract/renderer SHAs, package checksums/signatures,
   build provenance, per-format SBOM/runtime versions and patch ownership, release build
   baseline/ABI minimums, commands/results, evidence labels, compatibility matrix, known
   issues and rollback/recovery. Missing/skipped required checks cannot count as passes.
   A merged planning PR or a CI-only build is not a delivered Linux app.
8. Live QA uses an isolated account/island and disposable repositories/agents, never the
   owner's working data, and runs in the Lima VM. Credentials and release keys use
   authorized secure channels.

G1–G8 receipts in [the implementation gates](docs/implementation-gates.md) accompany these
items. A blocked mechanism has a named dependent milestone and an explicit unresolved
receipt; a documentation or policy-tooling pass does not establish installed-app behavior.

## 9. Estimates and open evidence

Voice estimates were 2–3 working days for specification/parity analysis and 4–8+ weeks
for implementation/verification with agent assistance. They are planning ranges, not
promises, and have not been validated by a Linux spike. This PR proposes the specification;
it does not claim completed portability testing or a complete button-level inventory.
L0 replaces estimates with measured milestone ranges and critical-path risks.

Open evidence, after the 2026-10-15 decisions: the first user's actual Ubuntu release, CPU
and GPU; provider CLI availability and login behaviour on Linux and on arm64; D1/D4's L0
spikes including helper persistence/update recovery for both formats; the compatible
release build baseline/runtime receipts; D5's future CI wiring and per-combination desktop
evidence; Antigravity storage/identity scope, Linux speech and G1–G8's other platform proofs;
and the outcome of S1-5. These are engineering proofs of the chosen design, not
new product decisions. Everything else that was open at the
2026-10-13 revision is decided in section 4. Ask the owner only for product, spend,
credential or trust decisions that those sections do not already answer. Implementation is now authorized; unresolved evidence still gates dependent work.
