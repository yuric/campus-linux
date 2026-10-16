# S1-1 runtime and contract copy audit

Audit source: campus-server main 4050498fd4556d1cf1cba9f87a6106b5467283be,
then the complete candidate diff. Ruby lexer inspection covered actual string literals in
api/app, including interpolated fragments, rather than treating comments or occurrence
counts as runtime evidence. OpenAPI descriptions and exported fixture messages were
reviewed alongside their producers.

| Surface | Disposition |
|---|---|
| Credential catalog, broker login/setup, verification attempts, binding/readiness, login recovery and identity guidance | Generic computer/helper wording. Preserve provider commands such as `claude setup-token`, consent, encrypted storage and account recovery guidance. |
| Provider model discovery, CLI freshness/install classification/update guidance, quota collection | Generic computer wording. Mac CLI source identifiers remain unchanged. Apple Team ID update authorization is unavailable on Linux. Linux provider storage must be observed before isolated-account eligibility. |
| Executor registration, five-device account cap, reachability, capacity/resource/helper messages | Generic computer wording; no limit or admission-policy relaxation. Unknown Linux platform/store observations fail closed. |
| Landing, workflow execution, coordinator/MCP, delivery/recovery, retained work and Rule reviews | Generic computer wording because these messages also reach Linux. Named executors, including an actual device named `This Mac`, retain their names. |
| Speech | Absent platform/macos retains Apple speech wording and behavior. Linux/unknown platform receives Rails-authored unsupported state; no fallback provider is selected. |
| Local Rails MacBroker installation remedies, macOS media/library integrations, Mac signed release and updater mechanics | Retained where the path is inherently Mac-specific. Hosted login uses the executor binding contract, not this local path. |
| Wire compatibility | Do not rename `agy_cli_mac`, `codex_app_server_mac`, `grok_cli_mac`, `max_concurrent_runs_per_mac`, Mac-named reason codes, schema/class identifiers, or existing route names. |
| Legacy prose used as protocol evidence | Retain recognition of the pinned Mac stream-ended input and both persisted Mac login-recovery park messages. New outbound copy is neutral; old input/persisted evidence must still normalize and recover. |

Review found and corrected two important non-cosmetic cases: the stream-ended string is
an adapter input, and login wait messages identify existing parked work. Their existing
request/service tests exercise those boundaries with literal pre-rollout values. Do not
replace their fixtures with new copy just to make a snapshot pass.

Existing expectation updates follow the Rails messages. New tests cover observable
platform/refusal/transport behavior; this audit adds no source-string or prose snapshot CI.

Current-main carry-forward also audits `ExecutorFleetContract`: disconnect labels, confirmation, result and parked-card messages now say computer. Device names and the persisted Mac disconnect actor identifier retain their identity.
