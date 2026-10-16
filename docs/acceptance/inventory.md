# Linux action acceptance inventory

Task #981, next owner **LINUX-20261016**. All **450** product action cases are **unimplemented**;
356 have concrete API operation/delegate mappings. The rest are explicit local steps or
producer-blocked bridge cases, not uncounted omissions.
[actions.json](actions.json) is the action ledger: one independently named test case and
receipt per action, owning card, expected behavior, source location and exact API path /
method / operationId / schema JSON pointer where the source maps to a concrete operation.
A row is an acceptance obligation, not a product test or a passing receipt. No percentage
summarizes missing actions. The [Mac control census](mac-control-census.json) records every
Swift Button/Menu/Toggle/Picker/TextField/submit/tap location found in non-test source,
with file hashes, as a cross-check against omitted local controls. It is not a semantic
parser or a replacement for reviewing server-offered action arrays.

## Pins and reconciliation

- Linux base: `yuric/campus-linux@e496ac2f756a8656575ec2474b771567f2f68e56` (merged main).
- PRD Mac: `yuric/campus-macos@3cc71216e3ca05090e90c5f09a56350b065acdcd`.
- Reconciled Mac: `yuric/campus-macos@8e39806c5b1fb2ffeda6e55718a4fd2a4d2890da`,
  merged main observed 2026-10-16; 44 commits ahead. Read from an isolated GitHub archive,
  never a dirty reference worktree. [Compare the pins](https://github.com/yuric/campus-macos/compare/3cc71216e3ca05090e90c5f09a56350b065acdcd...8e39806c5b1fb2ffeda6e55718a4fd2a4d2890da).
- PRD server: `yuric/campus-server@d35361542b895a4fd73c838b1be3531ceea5d5fd`.
- Reconciled Mac contract provenance: `yuric/campus-server@d93b841762183af5ba0d357f3f1c42351aeed9ff`.
  Exact bytes/hash are recorded in the JSON ledger; references point into
  `api/docs/openapi.yaml` at that server SHA. This is source evidence, **not** a Linux
  snapshot import. #985 must verify/export the merged post-S1 contract and rebind these
  pointers before product generation. The existing 132-path snapshot stays untouched.

Explicit additions since the PRD pin: endpoint enrollment verification and account-session
retirement; Home waiting/credential grid and usage tiers; credential-auth recheck reservations
and executor usage refresh; speech interruption/recovery planning, authorization and chunk
transport; coordinator autocomplete/completion, session search and saved-operation review;
helper repair deadlines, root migration/path observations, diagnostic report submission and
CLI update observations. They appear as separate action cases and remain required, including
server-driven retries and refusals. #997 must re-read then-current merged Mac main at freeze,
compare it to this exact pin, append every new offered action, and record its disposition.
Freeze is not asserted by this bootstrap. Later additions cannot disappear into a coverage score.

## How each action becomes acceptance

For a concrete API row, the `schema_pointer` names the whole operation, including request,
parameters, response and inline schemas; `schema_refs` additionally lists named types.
For descriptor downloads/uploads, the storage request uses only the descriptor's permitted
method/URL/headers, without the Campus bearer. For dynamic actions, replay only the
server-offered request after version, principal, origin and confirmation checks. Never turn
this planning inventory into a client catalog of allowed actions or domain labels.

Every case exercises the named successful outcome and refusal/interruption at its real
seam. Mutation receipts include before/request/response/refetched state, confirmation and
idempotency/uncertain-write behavior. Read receipts include empty/populated, pagination,
unknown/additive fields and authorization isolation. Executor cases add lease/generation,
process/outbox identities and each crash boundary. OS-only presentation cases have no API
operation; their exact OS adapter, observed request (if any) and implementation command are
filled by the owning card. The ledger deliberately names missing implementations rather
than installing `true` tests or fake passing packages.

**Remaining contract gates:** the existing execution/verdict replay union is explicitly
mapped from `HTTP.swift`: create/cancel execution, resend message and retry saved direction.
#990/#992 must revalidate every offered variant against #985's merged fixtures at freeze.
#987 still owes the exact desktop bridge schema; P12 is explicitly blocked on that producer.
Existing native-session routes are mapped, but their hosted Linux transport/readiness
contracts remain S1/G1 work, not proof that MacBroker calls work remotely. Local-only
navigation/OS/process steps explicitly have no API operation; their resulting mutations
use separately mapped API delegates. #984 owns genuinely missing server schemas.
Receipt filename is the ledger's `receipt`, stored in a review-linked artifact set, with
repo/head, server/snapshot/renderer SHA, artifact/hash, test-case ID, exact command,
expected/observed result and gaps. Desktop receipts add architecture/package/OS/session/
graphics and screenshot hashes. `blocked`, `skipped`, `not-run` and absent receipts fail
release acceptance. Planned test IDs do not imply commands already exist.

## Owners and real test seams

| Group | Owning card | Seam and critical cases |
|---|---:|---|
| P01 | #988 | Session host/Secret Service; sign-in/out, enrollment/recovery, demo/conversion, expiry and account/island isolation |
| P02 | #988 | Endpoint/bootstrap host; exact origin, onboarding/recovery, no Mac dependency |
| P03 | #988 | Home reads/action receipts; waiting, credential grid/recheck, digest, Pulse/recommendations |
| P04 | #991 | Board request/store/UI; all offered workflow/assignment/routing actions, counts/cursors, staging/order/batch |
| P05 | #991 | Task detail/chat/draft; edit/comments, dependencies/lineage/PR/runs and review retries |
| P06 | #994 | Storage descriptor and audio adapter; staged upload, preview/download, permissions/interruptions/recovery |
| P07 | #991 | Project/binding/rule requests and trusted filesystem adapter; preview/confirm, archive/delete/history |
| P08 | #992 | Landing/office/session UI; single/batch, account/model/executor, exact native resume and all offered lifecycle actions |
| P09 | #992 | Credential UI plus #989 PTY/scope adapter; input/cancel/verify, recheck, usage/model refresh and fallback |
| P10 | #993 | Assistant/coordinator/private request scopes; history/search/reference/steering, continuation and confirmations |
| P11 | #993 | Trusted native delegated consent; principal/scope, grant/refuse, expire/revoke, renderer denial |
| P12 | #995 | #987 artifact import and restricted bridge; selection/mutations, camera, motion/visibility and crash recovery |
| P13 | #994 | Desktop navigation/a11y/link/menu/notification adapters; cold/warm activation and hostile inputs |
| P14 | #988 | Settings/profile/GitHub/feedback/telemetry request and retry seams |
| P15 | #989 | Registration/bindings and Linux observations; absent/locked store, readiness/root/capacity |
| P16 | #990 | Claims/leases/CLI/worktrees/events/outbox/cancellation; all four crash boundaries, no secret persistence |
| P17 | #990 | Remote request control; exact executor, truthful states, no local fallback |
| P18 | #996 | Signed package/update and helper promotion; format/arch, privileged-byte verification, lifecycle/diagnostics |

#982 proves mechanisms, #986 proves hosted login/claim, #987 produces the renderer, #997
runs the final matrix, #998 hands off UTM, and #999 owns authorized publication. None of
those cards is fulfilled by the inventory. [Visual capture obligations](visual-protocol.md)
cover every PRD §3 screen. [Verification](verification.md) covers bootstrap CI and its limits.
