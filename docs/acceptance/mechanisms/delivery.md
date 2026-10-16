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
  provider receipts retain their original source revision; new refusal paths are
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

These gaps block their dependent production mechanisms. Only the coordinator routes
provider/speech observations to #1030, then the merged-contract import #1031 for
#994/#996. No reverse dependency was added. LINUX-16/17 (#996/#997) must repeat every
applicable case against final actual deb/AppImage artifacts and both real GDM tuples.

## Verification and delivery receipt

Repository policy checks do not establish product runtime or desktop acceptance.
Exact committed head, local architecture commands/results, hosted checks, PR URL and
remaining coordinator action are recorded on card #982 and in the draft PR. Historical
mechanism receipts bind their own script/artifact hashes; a later source fix never
retroactively changes those captures. Preserve all failed/aborted runs.

Raw terminal/vendor captures retain their original whitespace and line endings, including
serial-console control sequences. Consequently the full `git diff --check` reports
whitespace in raw receipts; those findings are deliberately retained to preserve capture
hashes. The source/document check excluding `docs/acceptance/mechanisms/receipts/**`
passes. This is not a claim that the full whitespace check passed.
