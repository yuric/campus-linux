# #982 review and handoff

Reserved next owner: **LINUX-20261016**. This is a draft mechanism-evidence delivery,
not dependency completion. The coordinator independently verifies, obtains a
different-family review, observes Council and all required exact-head checks, and
owns admission. The worker does not mark ready, merge, enable auto-merge or mark done.

The historical English-only and direction1196 status below is superseded by the
[current speech report](receipts/speech-next-1203/REPORT.md) (forced en/es, prefix/final
and cancellation observations, with errors and unknown actual locale) and the
[current G4 report](receipts/apport-full-1213/REPORT.md) (one bounded SIGABRT pair,
failed initial inspection and same-report recovery). Neither closes product speech,
full G4 or L0; historical receipts and failed outcomes remain unchanged.

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
  provider receipts listed in the historical binding limit lack an executed-script digest
  and are source-unbound; Gemini has historical digests but unavailable producing revisions. New refusal paths are
  separately identified as source-reviewed rather than recaptured observations.

The aborted X11 timing history is retained explicitly:
[first-series disposition](receipts/renderer-x11-baseline-aborted/disposition.json)
and [completed run 1](receipts/renderer-x11-baseline-aborted/run-1.json);
[second-series disposition](receipts/renderer-x11-baseline-final-aborted/disposition.json),
[completed run 1](receipts/renderer-x11-baseline-final-aborted/run-1.json) and
[completed run 2](receipts/renderer-x11-baseline-final-aborted/run-2.json).
The first series stopped for disposable credential remediation; the second stopped
under the coordinator resource/timing hold with the superseded relative-zoom harness
and an incomplete series. These historical traces are not accepted or compared as a
G8 baseline, valid performance miss, optimization result or D1 fallback trigger.
No slow run was removed to obtain a pass, and the fixed 30-second warmup,
60-second trace, 33.3 ms p95 and all-five-run bar is unchanged. No missing tail result
is inferred from the incomplete logs. Existing aborted-v2 disclosures remain valid;
these direct links improve discoverability without changing any raw receipt.

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
   Historical store and GTK speech-capability pairs are also session-unbound; their
   byte-identical output does not establish two independent graphical tuples. Recorded
   operations/cleanup remain observations, and distinct task-link result/event records
   retain their own PID/session binding.
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


## Direction 1196 consolidated evidence

The [matched Apport SIGQUIT pair](apport-activation.md) now establishes activation
and kernel suppression for a bounded synthetic ELF only. Full-report metadata
preflight failed; SIGABRT/report creation and decoded-marker proof remain open.
The historical positive-control limitations above remain accurate for those older
captures. No original raw capture or commit was rewritten.

The duration-equality repair uses the existing `1e-6` numerical tolerance and a
valid fractional-start regression. It preserves the 60-second protocol, p95 bar,
all-five-run rule and absence of a cadence/max-gap threshold. A fresh timing freeze
is still required. Historical self-review timing/cleanup-source claims are annotated
as superseded by current receipt limits.

Mac PR114 is now verified **MERGED** at
`3e3d4bcd64fd1504c4546b2f7a063b55e2eea783`; see the
[GitHub readback](receipts/apport-activation-1196/mac-pr114-merged.json).
The existing v7 captures remain bound to their original `8e39806` producer;
no new export import, benchmark or parity credit is inferred from the later merge.
Root reports final-export verification and owns its subsequent consumer handoff.

The published branch remains `campus-linux/982-mechanism-proofs`, draft PR12.
This batch preserves recovered commit `26f6909` and adds one consolidated repair
commit. All registered evidence manifests participate in the normal repository check;
checks count committed membership/bytes/hashes, not product acceptance. The active
human coordinator LINUX-20261016 (comments10512/10517) is the explicit next owner
for exact-head independent review, CI/admission, Council and remaining probes.
No worker wakeup, readiness, merge or task completion is assumed.

## Direction1240 native handback

[Fresh G8 functional evidence and cleanup](receipts/g8-native-1240/REPORT.md) records actual
GDM Wayland/X11 native preflight, unchanged-harness untimed proofs and proof-bound freezes.
No timing, optimization, Electron or final acceptance is claimed. Lima is stopped; root
LINUX-20261016 owns independent review and separate observed timing scheduling.

## Direction1268 consolidated timing return

The [complete evidence and exact allocation](receipts/g8-timing-1268/REPORT.md) preserves
an initial allocation overrun, early protected inode replacement during unattended upgrades,
and a later idle-lock interruption. None is promoted to success. After the revised lease,
a fresh idle-inhibited Wayland series completed all five valid processes: p95
143/187/142/140/174ms, all misses. Shared-host contention increased and is recorded.
The coordinator-selected distinct transport-option candidate failed native admission;
no candidate timing was attempted and no numeric miss is inferred from that failure.

Exact accepted source9d7743a and merged Mac3e3d4bcd export stayed unchanged. Newer
human10789/10795 paused X11 and Electron before the D1 decision. Both inhibitors were
released; all captured owned PIDs/scopes are absent, with shared GNOME attribution limits
explicit. The resumed boot's32 protected entries match exactly through graphical logout.
Lima returned Stopped at17:06:46 observation, actual disk7,405,699,072bytes. Root
LINUX-20261016 owns review, CI/Council, D1 decision and the next observed lease. This is
one consolidated evidence push to draft PR12, not readiness or task completion.
