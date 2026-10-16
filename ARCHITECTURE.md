# Architecture: Campus for Linux

**Status: decided design; no product code exists.** Requirements, parity inventory,
compatibility, delivery gates and the seven decisions behind this page are in
[PRD.md](PRD.md). Detailed contract handoffs and required future receipts are in
[the implementation gates](docs/implementation-gates.md).

## Components and authority

```text
React board + verified Island export, in WebKitGTK
                 |
        restricted Tauri IPC bridge
                 |
Rust Tauri host ---------------- HTTPS / invalidation events -------- Campus Rails API
                 |                                                       |
       authenticated local IPC                                 claims / leases / events
                 |                                                       |
campus-linux-executor (Rust, systemd user unit) -------------------------+
                 |
      provider CLIs / authorized repository workspaces
```

Remote agents are controlled through authorized API operations, not arbitrary
host-to-host RPC. The Linux service registers with Rails and implements its execution
protocol; it does not host Rails. Local execution continues with the UI closed, within
the user's graphical login session. The last graphical logout ends supervision even
if SSH/TTY sessions remain; graphical login restores installed authorized supervision.
No root service, automatic lingering or unattended pre-login execution is included.
Both package formats install a verified, versioned helper copy in a stable per-user
location; the unit never targets an AppImage's temporary mount. D4 specifies singleton
ownership, staged promotion, active-attempt/outbox recovery and uninstall behavior.

### Where the authority line sits

| The API decides | A client decides |
|---|---|
| Which providers, engines, models, and credential kinds exist | Layout, navigation order, focus, selection |
| Which combinations can work | How a `destructive` intent looks as a button |
| Credential state — unverified, active, expired, exhausted — and why | Which native colour renders `error` vs `warning` |
| Allowed workflow transitions and their labels | Local draft and interaction state |
| Board lane identity, ordering, membership | Accessibility behaviour |
| Diagnostic severity, reason, detail, safe message | Transport failures where no response arrived |
| Workspace eligibility and authorized opaque credential scopes | Trusted executor derives local paths and enforces filesystem confinement |
| Domain vocabulary — what a stage is *called* | — |

A client that infers domain meaning from an error substring, a message prefix, or HTTP status
alone is broken, even when it happens to produce the right answer. The D7
[boundary policy](docs/client-boundary.md) checks known syntax and reviewed exceptions;
semantic review and contract tests establish the full authority boundary.

The executor observes and supervises processes; Rails decides authorized work and interprets
normalized results.
Generated transport enums reproduce a verified pinned server contract. Trusted adapters
map engine identifiers to locally allowed binaries and enforce workspace/credential bounds;
they cannot accept arbitrary server-supplied binaries or paths. Those narrow files require
content-bound review receipts and provenance. Presentation code still has no catalogs,
compatibility logic or workflow tables.

### Freshness: events are hints, not patches

Real-time updates say *that* something changed. The client re-reads the snapshot it already
knows how to render. There is no patch application and no reconciliation, so a dropped socket
costs one extra fetch rather than corrupt state.

### Versioning and failing closed

Server contracts are versioned. A client that receives a version it does not understand
**withholds the action** rather than falling back to an older client-side decision. Silent
degradation is how two clients start disagreeing.

## Reuse and repository ownership

- `campus-server`: API/OpenAPI and contract corrections, production deploy.
- `campus-macos`: reference semantics and shared Three.js Island producer.
- `campus-linux`: the Tauri shell, the React board, the Rust host and executor, packaging
  and tests.
- Retired `campus-web` and `campus-cli` are not product dependencies.

Generate API bindings from a verified server snapshot. Import renderer artifacts from
an exact merged producer commit with manifest/byte verification. Shared renderer
changes land at the producer first; no second renderer or hand-maintained API schema.
S2 imports a merged post-S1 contract bundle with the server exporter and migrates all
snapshot references/checks together. L1 consumes that verified import. M1 defines a
desktop renderer export and the presentation/mutation/lifecycle bridge; the existing
iOS recipe's read-only mobile surface is not desktop parity.

## Boundaries and recovery

Session storage and HTTP belong to the trusted unprivileged per-user host, not renderer JavaScript.
IPC has narrow authenticated methods and schema/origin/principal validation. Bundled
content cannot invoke arbitrary programs or approve delegated authorization. External
links use the browser. Credentials and caches are scoped to exact API origin, channel,
account and island. Endpoint changes never reuse credentials; redirects cannot forward
secrets across origins and deep links cannot switch the endpoint/trust policy. Unknown
server contract versions withhold affected actions.

The executor uses distinct identity, bounded workspaces, direct argv spawning,
executable allowlists, credential isolation, redacted events and process-group
cancellation. Durable delivery, lease reconciliation and restart recovery preserve
attempt ownership and prevent duplicate work. Sign-out and updates explicitly
reconcile active work. Campus-owned token file fallback is excluded; D3's provider-owned
OAuth files and local IPC token retain their explicit isolation/permissions rules.
The local executor maps an opaque scope to `<root>/scopes/<base64url(scope)>`; Rails
does not choose its credential directory. Antigravity's Linux isolation remains evidence
for Rails readiness, not an assumed config-directory feature.

G3 ties updates and lifecycle to the existing helper-update handback and authorization
generation contracts. G4 requires evidence for IPC peer identity, per-attempt token
scope, child context, process termination and crash capture. Secret Service does not
establish isolation from hostile code running as the same user. G5 requires verification
at the privileged deb installation boundary; this introduces no root execution service.
G6/G7 cover PTY login, link/speech adapters, CSP and whole-webview recovery.

Events signal re-fetches, not client-authored patches. Writes reconcile ambiguous
delivery instead of replaying blindly. Queued, running and completed remain distinct.

## Decisions

Tauri with a React board (D1); Rust for the host and the executor (D2); Secret Service for
Campus-owned tokens and provider files isolated but plaintext (D3); deb and AppImage with
Tauri's signed updater and one production channel (D4); Docker, public hosted CI and a Lima
VM for verification (D5); five named campus-server prerequisites (D6); the boundary gate
(D7). Each is recorded with its trade-offs in [PRD.md section 4](PRD.md#4-architecture-and-decisions).
Broad Linux support is verified per runtime, architecture and desktop combination, not
inferred from one Ubuntu build.
The existing workflow checks docs and boundary tooling only. D5's Docker/product CI and
Lima verification are L0 work after implementation is authorized. Section 8 labels
x86_64 headless-tested previews separately from desktop-verified combinations, without
adding a product channel or weakening the P01–P18 parity target.
