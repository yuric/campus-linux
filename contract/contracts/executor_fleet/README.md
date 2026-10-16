# Mac fleet contract, version 1

Server card #453; Mac companion #966. Snapshot this directory and OpenAPI from the
merged server main SHA before implementing the client. The orchestrator records that
SHA on #966 at merge; this branch is not yet a snapshot source.

Render staleness label/message and disconnect confirmation as plain text, verbatim.
Seven days is Rails policy, never a client timer or an assignment rule. Stale does
not mean no live work. Existing picker membership and readiness stay authoritative.
Old clients ignore additive fields; absent/null/unknown-version disconnect contracts
offer no new action. Dispatch the exact request only after explicit confirmation.

The existing DELETE endpoint retains 204 for legacy callers; the published
disconnect_version=1 request returns a current executor and disconnect_result.
Unknown request versions fail without mutation. It is safe to repeat disconnect.
The response does not claim that remote provider processes stopped. A heartbeat or
claim between display and disconnect can change activity; revocation settles current
work under the same executor lock used by claims. Every in-progress card held by an
Office it unbinds moves to Blocked (`blocked_kind: needs_input`) with a Rails-authored
`blocked_reason`, and its claim ends, so neither the lease sweep nor another Office
restarts it; a person reviews the workspace kept on that computer and moves it to Ready.
Project folder links survive and return if the same installation registers again;
Offices stay unbound.

Staleness `state` is the seven-day observation. `label` for a fresh Mac names its
reachability (`Online` or `Offline`), so "Fresh" never sits beside an offline Mac, and
`message` says how long ago in words Rails computed; `last_seen_at` stays the timestamp.

Fixtures cover observed states, owner confirmation/request and revoked result.
They are compared against the Rails service by ExecutorsTest.
