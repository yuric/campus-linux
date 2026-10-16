# #982 review and handoff

Reserved next owner: **LINUX-20261016**. This is a draft mechanism-evidence delivery,
not dependency completion. The coordinator independently verifies, obtains a
different-family review, observes Council and all required exact-head checks, and
owns admission. The worker does not mark ready, merge, enable auto-merge or mark done.

## Source and scope review

The worker reviewed the complete Linux-owned source/document/receipt diff against
merged base `37ef5d622da09cd7ba113dc0d1119e62e7378f84`. All added implementation is
explicitly disposable instrumentation under `spikes/982`; no product architecture,
contract, renderer producer, server rule, release key or public release upload changes.
The provisional producer is merged Mac `8e39806c5b1fb2ffeda6e55718a4fd2a4d2890da`.
There is no current server contract imported or authenticated product claim in this PR.

Self-review corrected actual defects rather than interpreting failed receipts as passes:

- Serial console authentication initially matched an echoed prompt marker; the
  disposable password was rotated and its local log exposure remediated. See
  [credential receipt](receipts/credential-remediation.json).
- The renderer initially used relative zoom, then observed the producer's discarded
  feature-test context. Absolute zoom, context ownership, full trace admission and
  diagnostic timeout were corrected; original failures remain attached.
- Package fixtures now bound decompressor output before buffering, validate exact
  archive member ownership/type/mode/presence, verify removal before cleanup, and
  fail when an applicable format is missing.
- IPC now authenticates both peers before sending synthetic authority; aggregate
  process and store results require the claimed checks and verified cleanup.
- Task-link cleanup uses no-follow file descriptors. It is cooperative disposable
  cleanup, not protection against an adversarial process under the same UID.
- Provider wrappers now distinguish completed observations from successful mechanisms,
  enforce failure exit status and validate installed bytes before execution. Historical
  provider receipts lack an executed-script digest and are source-unbound; new refusal paths are
  separately identified as source-reviewed rather than recaptured observations.

The [renderer/link/speech review](renderer-links-speech-review.md) records focused
negative checks and source hashes. These worker/helper reviews are **not** the
coordinator's required different-family review or Council approval.

## Outstanding evidence that must not disappear at handoff

1. G8 has no accepted five-run timing series. Coordinator directions 10420/10448/10450
   defer it while competing CI runs on the same Mac. Preserve the fixed fixture,
   absolute zoom, 30-second warmup, 60-second trace, 33.3 ms p95 and all-five-run bar.
   A measured miss requires the permitted separately frozen optimization and then
   D1's decided Electron fallback. The fallback is prepared but has not run.
2. Real provider login, refresh, cancellation, two-account isolation and active model
   run/update concurrency require the coordinator's authorized isolated-account plan.
   Owner provider homes must not be copied. Antigravity isolation remains unproven;
   Gemini API-key is a separate path. Trust and fixed update/rollback gaps are listed
   per actual CLI/layout in [providers](providers.md), without a trust downgrade.
3. Offline speech demonstrated synthetic English inference and native synthetic
   audio-server access. It does not establish current-locale language parity, physical
   microphone/portal consent, streaming or interruption recovery. No cloud fallback,
   new spend or English-only product choice is adopted.
4. Stock Tauri's deb installer is unsuitable because of its password/sudo fallback.
   The disposable privileged verifier proves a constrained alternative mechanism,
   not the full installed updater, actual release trust anchor or final package route.
   All remaining D4 cases stay explicit in [the transition matrix](packages.md).
5. The original login keyring remains intact and locked after the disposable Unix
   password rotation. There is no PAM auto-unlock recovery claim. The shared private
   credential file now matches Lima; stopped UTM was not changed. The coordinator's
   environment owner must reconcile UTM through its existing private control channel.

6. Allow-rule installer and process checks establish session-independent mechanisms.
   Historical wayland/x11 filenames do not bind graphical session identity; prompt
   receipts also lack run-bound graphical metadata. No per-tuple acceptance follows
   from those captures. Future session evidence must capture observed identity with
   boot/timestamp/source/artifact linkage; no historical metadata is backfilled.
7. Authenticated-version presence is proven, but signed replay/downgrade enforcement
   is not: the fixture accepts signed v1 over v2. The historical misleading test name
   is preserved in raw JSON and corrected only for future source output. D4's published
   higher-version rollback remains unimplemented.
8. Historical crash probes observed no dump with both dumpability/core-limit zero in
   three seconds, without an isolated positive collector control. The separate
   [G4 follow-up](core-sentinel-followup.md) leaves its positive control inconclusive;
   closed-source after-exec crash policy remains a live gap.

These gaps block their dependent production mechanisms. Only the coordinator routes
provider/speech observations to #1030, then the merged-contract import #1031 for
#994/#996. No reverse dependency was added. LINUX-16/17 (#996/#997) must repeat every
applicable case against final actual deb/AppImage artifacts and both real GDM tuples.

## Verification and delivery receipt

Repository policy checks do not establish product runtime or desktop acceptance.
Exact committed head, local architecture commands/results, hosted checks, PR URL and
remaining coordinator action are recorded on card #982 and in the draft PR. Historical
mechanism receipts retain the script/artifact hashes they actually captured; missing
script bindings remain explicitly unproven. A later source fix never
retroactively changes those captures. Preserve all failed/aborted runs.

Raw terminal/vendor captures retain their original whitespace and line endings, including
serial-console control sequences. Consequently the full `git diff --check` reports
whitespace in raw receipts; those findings are deliberately retained to preserve capture
hashes. The source/document check excluding `docs/acceptance/mechanisms/receipts/**`
passes. This is not a claim that the full whitespace check passed.


## Consolidated review repair (directions 10480/10485/10494)

The nine indexed raw logs were recovered from their retained guest originals, secret
reviewed and added with exact historical hashes. Tracked manifest membership plus
size/hash checks now run in repository verification. The timed summarizer requires
complete finite ordered warmup/measurement segment and gesture traces before applying
the unchanged 33.3 ms/all-five bar; the coordinator's five stalled counterexamples
reject. Untimed v7 driver/checker bytes are unchanged. A fresh timing freeze is required
for the changed summarizer before the deferred timed series.

Historical provider/speech receipts without an executed probe hash are explicitly
execution-source-unbound. Unreceipted host/mock tests receive no runtime credit.
The lifecycle model's pointer recovery is observed; fence survival and actual claim
withholding are not asserted by that harness and remain untested. The already retained
process run that could not connect to the user bus is now linked explicitly as failed.
The absolute-zoom correction's public author email was replaced with a task-authority
reference and its original digest recorded; no test observation was changed.

The separate core-sentinel follow-up records bounded synthetic kernel/filter results,
its failed harness observations and the inconclusive positive collector control. It
does not close G4 or authorize provider, privacy or release behavior. Coordinator
review and exact-head hosted checks remain required; no earlier-head green result is
reused for the repair.

Native finding 4 is narrowed: the installer predicate requires both the expected
exit status and expected installed digest; successful unexpected installation fails.
Finding 11 is narrowed: after-promote writes the candidate pointer before crashing,
and after-accept persists acceptance before crashing, so a no-op recovery fails the
former. Earlier pre-write interruption rows have deliberately limited scope. Fence
assertions remain absent. These explanations preserve the original findings for
coordinator disposition rather than claiming all lifecycle behavior is proven.
