# Architecture: Campus for Linux

**Status: proposed design; no product code exists.** Requirements, parity inventory,
compatibility and delivery gates are in [TODO/PRD.md](TODO/PRD.md).

## Components and authority

```text
Linux desktop UI / pinned Island renderer
                 |
        restricted host bridge
                 |
Linux application host -------- HTTPS / invalidation events -------- Campus Rails API
                 |                                                       |
       authenticated local IPC                                 claims / leases / events
                 |                                                       |
per-user Linux execution service ----------------------------------------+
                 |
      provider CLIs / authorized repository workspaces
```

Remote agents are controlled through authorized API operations, not arbitrary
host-to-host RPC. The Linux service registers with Rails and implements its execution
protocol; it does not host Rails. Local execution continues with the UI closed, within
the user's graphical login session. The last graphical logout ends supervision even
if SSH/TTY sessions remain; graphical login restores installed authorized supervision.
No root service, automatic lingering or unattended pre-login execution is included.

Rails owns capabilities, catalogs, credential domain state, workflow, ordering,
validation, diagnostics, confirmations and wording. Linux owns presentation,
accessibility, drafts and OS adapters. The executor observes/supervises processes;
Rails decides authorized work and interprets normalized results.

## Reuse and repository ownership

- `campus-server`: API/OpenAPI and contract corrections, production deploy.
- `campus-macos`: reference semantics and shared Three.js Island producer.
- `campus-linux`: desktop, native host, per-user service, packaging and tests.
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

## Choices requiring evidence

Desktop shell, executor language, secret-store backend, non-systemd supervision,
package baselines and authenticated update design remain proposals. The
[decision register](TODO/PRD.md#4-proposed-architecture-and-decisions) specifies the
L0 evidence required before implementation. Broad Linux support is verified per
runtime/architecture/desktop combination, not inferred from one Ubuntu build.
