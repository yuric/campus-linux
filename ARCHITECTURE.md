# Architecture: Campus for Linux

**Status: decided design; no product code exists.** Requirements, parity inventory,
compatibility, delivery gates and the seven decisions behind this page are in
[PRD.md](PRD.md).

## Components and authority

```text
React board + pinned Island renderer, in WebKitGTK
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

### Where the authority line sits

| The API decides | A client decides |
|---|---|
| Which providers, engines, models, and credential kinds exist | Layout, navigation order, focus, selection |
| Which combinations can work | How a `destructive` intent looks as a button |
| Credential state — unverified, active, expired, exhausted — and why | Which native colour renders `error` vs `warning` |
| Allowed workflow transitions and their labels | Local draft and interaction state |
| Board lane identity, ordering, membership | Accessibility behaviour |
| Diagnostic severity, reason, detail, safe message | Transport failures where no response arrived |
| Path and filesystem validation | Terminal, window, or view composition |
| Domain vocabulary — what a stage is *called* | — |

A client that infers domain meaning from an error substring, a message prefix, or HTTP status
alone is broken, even when it happens to produce the right answer. This table is the same one
the Mac and Windows documents carry, and `scripts/check-client-boundary.sh` fails a pull
request that crosses it (PRD D7).

The executor observes and supervises processes; Rails decides authorized work and interprets
normalized results.

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
reconcile active work. Plaintext credential fallback is excluded.

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
