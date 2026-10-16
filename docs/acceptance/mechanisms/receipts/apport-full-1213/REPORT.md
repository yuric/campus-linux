# Bounded full-report control — #982, directions 10577 / 1213

LINUX-20261016 assigned one matched SIGABRT pair, with a non-crashing watchdog
drill first. This report records that pair, including its failed initial inspection
and recovery of the **same** report. No repeated positive crash occurred. It proves
this synthetic kernel/Apport capture-and-inspection mechanism, not full G4, provider
isolation, product support export or L0 acceptance. The older SIGQUIT pair and every
historical failure remain unchanged.

Linux source base is merged PR11/#981, `37ef5d622da09cd7ba113dc0d1119e62e7378f84`,
reverified through GitHub's merge record. This additive batch starts at published
PR12 head `4042a4d784b9e23e9e45f7e84730956b12b3e41a`. It imports no server contract
or renderer artifact. Existing renderer captures retain their original producer.

## Admission and controls

The [non-crashing drill](drill.stdout) exercised the common guest deadline against
an owned Python parent and its sleep child. Both retained pidfds became exited;
cleanup passed. The drill was SSH-attached with a no-op guard: heartbeat loss,
STOP-file and storage-failure paths were not exercised. This is an exercised
watchdog deadline, **not** a forced timeout of an actual Apport collector. The
[metadata preflight](metadata.stdout) reproduced
3,559 serialized bytes using UID1000/GID1001, empty supplementary groups, a proc
fd opened as root and ExecutablePath established as root. All seven required proc
fields were present, nonempty and not `Error:` values; no error-valued field existed.
Its unit cgroup was absent after cleanup. [Installed identities](apport-positive-preflight.stdout)
match the recorded Apport 2.28.3 handler/report/serialization hashes and package-file
checks; kernel is Ubuntu 6.8.0-142.142 arm64. That inherited identity receipt still
reports an obsolete guest-20-GiB predicate false: the assigned guest floor is 2 GiB.

Both actual arms used the unchanged packaged `/usr/bin/sleep`, fixed `sleep 90`
argv and the same public synthetic environment/marker. Each recorded 8 MiB AS,
2,322,432 mapped bytes, one thread, 16 VMAs, 369 pathname bytes, core filter1,
NoNewPrivileges1, standard descriptors and PID/mount namespaces equal to PID1.
PrivateNetwork=no is the approved synthetic-control setting. Per-arm metadata was
3,556 bytes with all required fields readable; the working-directory string is three
bytes shorter than the separate 3,559-byte preflight's directory. This is observed
metadata size, not an exact kernel-note/report quota.

The runner checks the exact `.crash`, `.upload`, `.uploaded` and PID-specific
`.hanging` names before signaling. It retains `/var/crash` through a directory fd.
Collector attribution requires the complete expected argv, including both target
PID options, signal/core/dump mode, UID/GID, encoded sleep path and the known empty
`-F`, plus the resolved interpreter path, installed handler source identity and a new
start identity. The interpreter hash was recorded, not independently package-verified;
the handler/report/serialization package-file checks are separate evidence.
It acquires/rechecks pidfds and tracks directly observed children. The guest monitor
runs independently of SSH, checks the host heartbeat, and owns the 60-second crash
observation deadline and bounded cleanup. Host space/image sampling continues during
each arm. An unexplained identity/sidecar or unconfirmed cleanup withholds the next arm.

## Positive, failure, same-report recovery, negative

1. [Positive raw receipt](positive.json): at 14:26:02 UTC, target2445 invoked actual
   Apport2465. Complete argv and boot/start/namespace identities were captured;
   both pidfds exited and the three-second quiet interval completed. The report was
   19,026 logical bytes /20,480 allocated bytes, UID1000, inode92386/device64769.
   The receipt remains **failed**: the binding parser did not skip the leading empty
   line in RFC822 multiline ProcStatus. It also treated `systemctl stop` of an already
   collected unit as an error, despite cgroup absence. No report was deleted and the
   host refused the negative arm. [Original pair source](source-pair1/pair.py) and
   [host result](host-pair.json) preserve this failure; it is not rewritten as a pass.
2. [Same-report reinspection](reinspection.json): no process/crash/collector was
   launched. Recovery computed and recorded the original receipt hash; it required the
   same boot, exited retained identities, absent cgroup and exact captured report
   inode/owner/type/mode. Before launching the negative arm, `resume_negative.py`
   required that recorded hash to match the original host receipt and required
   byte-identical guest receipt content. Corrected
   multiline parsing bound ExecutablePath, ProcCmdline, ProcStatus PID/UID, Signal6
   and `_HooksRun=no` to the fixture and exact collector log. Streaming RFC822/base64/
   gzip inspection decoded **393,216 bytes**, SHA256
   `e8dd95b035d527558befeed8636c96c87fffb79609e4f6b6b456f51f300decd0`;
   the public marker appeared once, at offset393163. Gzip completion/integrity passed.
   The report itself hashed
   `6ac2648f4b04efcd039a4a06e47cb75afbcdf498d14f954ebbb2278be74a4135`.
   Only after renewed device/inode/owner/type/size/mtime checks was that report unlinked.
   Neither a raw core nor a second full report copy was written/exported.
3. [Negative raw receipt](negative.json): after confirmed positive cleanup, the one
   matched negative SIGABRT targeted2610 with core(1,1) and the inherited sentinel
   filter. The kernel recorded `Process 2610(sleep) has RLIMIT_CORE set to 1`.
   No collector, matching Apport line or exact report/sidecar appeared; the retained
   target exited, quiet interval completed and cgroup was absent. The corrected pair
   skips stopping an already absent unit. [Resume record](host-negative.json) binds
   the prior recovery and the exact corrected source.

[Collection](collection.json) rechecks all three retained identities, both fixture
and monitor cgroups and exact report/sidecar names as absent. Bounded attributable
log lines and the three synthetic support-receipt files contained zero public-marker
occurrences. These JSON files are this experiment's support bundle; an unimplemented
production exporter is not tested. Collector-open report-fd/inode correlation was not
retained as a successful observation; report binding uses the captured inode,
report fields, exact target/collector identity and collector log. Forced stopping of
a live actual Apport process was not exercised; do not claim otherwise.

## Resource accounting and shutdown

[Admission accounting](allocation-baseline.json) measured prior G4/speech directories,
positive growth from the historical `/var/log` allocation baseline, and a 16 MiB
source/host reserve:126,476,288 bytes consumed,141,959,168 remaining inside256 MiB.
The explicit new-file reservation was64 MiB. Polling thresholds were32 MiB report,
48 MiB explicit,192 MiB aggregate, host20 GiB and guest2 GiB. Whole-log growth is a
conservative, unattributed upper bound. Positive deltas are used; shrinkage does not
hide another file's growth. This is operational accounting, not a filesystem quota
or proof that a fast writer cannot overshoot between samples. Each arm used a fresh
log baseline with the prior consumed baseline reused: positive/inter-arm log growth
was not carried into the next guard. The inter-arm increment was not separately
measured, so this is not an exact cumulative per-file ledger. The recorded final
allocation/image measurements remain observations; improved cumulative accounting
is future reuse hardening, not a new gate for the completed pair.

Peak captured guest explicit allocation during the positive was118,784 bytes;
final retained guest files allocated151,552 bytes. The report was removed only after
its producers exited and its binding was verified. Host arm samples stayed above
33 billion free bytes; guest collection free was20,298,649,600 bytes. The final
[stopped readback](host-after.json) records host33,420,546,048 free bytes and327,680
bytes of image allocation growth from the corrected postboot baseline. Image growth
is a separate observation, not added again to contained files. No unrelated global
host-free delta is attributed to the experiment.

The first preboot accounting command used nonexistent `diffdisk`; the shell continued
to the normal Lima start. [Corrected baseline](host-before.json) uses `disk` and is
postboot; boot allocation growth was not measured. This ordering failure is disclosed,
not represented as a successful preboot check. All crash admission accounting was
refreshed before the pair. No install/download/build/model change occurred. Lima was
[stopped normally](stop.txt); its lease is returned to LINUX-20261016. UTM was untouched.

## Source history, validation and remaining limits

Sources are under [full-report](../../../../../spikes/982/security/full-report).
The deployed watchdog used by the drill and both arms is preserved byte-for-byte in
[source-pair1/watchdog.py](source-pair1/watchdog.py). Post-run review found a possible
exit-between-pidfd-poll-and-proc-read race: the current source now tolerates the expected
vanished proc path and continues stopping other retained identities. A deterministic
regression exercises this race in the existing repository unittest suite. That source
improvement was **not** rerun in the guest and grants no additional runtime credit.
Direction1223 additionally repairs cleanup when discovery or individual signaling
operations fail: every retained pidfd still receives a SIGKILL attempt, errors are
recorded in `watchdog_cleanup_errors`, and cleanup remains unconfirmed on any error.
Handles stay open through all attempts; normal attribution errors still propagate.
Mock-only regressions cover discovery RuntimeError after STOP (including a newly
retained third identity), STOP/KILL refusal without skipping other handles, and
normal attribution failure. This repair was not run in the guest. The executed
negative [pair](source-pair2/pair.py) and [drill](source-pair1/drill.py) are preserved
before adding error-receipt plumbing to their current sources. Other review P3
suggestions remain future reuse hardening, not requirements for this experiment.

The original four scanner tests cover cross-chunk marker detection, decompression
bounds, corrupt/truncated gzip and input bounds; they also run in the normal suite.
The scanner caps report input at32 MiB, each line at1 MiB, metadata at1 MiB, per-call
inflation at64 KiB and decoded core at9 MiB. An exceedance fails rather than expanding
limits. Source hashes in receipts map to current files or explicitly retained historical
files in this directory; [index](index.json) uses the existing repository checker.

Direct-child observation does not prove containment of an unseen detached double-fork
or hostile same-user process. Actual forced collector stop, provider userspace crash
reporters, host/product policy, real support export and final packages remain separate
obligations. No global collector policy or owner credential changed. G8 timing,
provider-account/isolation and final-product gates remain open. All523 product cases
remain unimplemented. Keep PR12 draft; the explicit next owner is the active human
LINUX-20261016 (comments10577/10582) for exact-head review, hosted CI/admission, Council
and merge disposition. No worker wakeup, readiness or dependency completion is assumed.
