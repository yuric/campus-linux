# Reviewed Electron installation and rollback; rendering not started

LINUX-20261016 / card #982 / human10963, direction1337 / Office382.
Source is published PR12 head `e74edf542ef1f8cec879a1fef4bf09dd46d6f37b`,
retained clean from Office400. The coordinator activated the reviewed1329 runbook
with holder382 substituted. No operator or renderer changes were made.

The exact operator installed the pinned72-file Electron44.8.0 arm64 payload into
fresh root-owned inodes and completed normal rollback. A conservative host-space
guard stopped this attempt before graphical login. This proves the observed normal
install/remove path only: no sandbox launch, native GPU evidence, preflight, motion,
freeze, timing, X11, installed product or release acceptance is claimed.

## Source custody and execution

[Preboot](host-preboot.json) confirms stopped disk7,871,332,352 bytes/inode944391844,
4 CPUs/6GiB, host23,953,465,344 free and23,416,594,432 after reserving512MiB.
The unchanged existing Lima guest booted successfully; no download or build ran.
The package verification command emitted no differences for Python packages.
[Interpreter/mount observations](interpreter-and-mounts.txt) recorded root-owned
ancestry and ordinary ACLs. The three apparent writable stdlib entries were
package-managed symlinks; read-only namei inspection resolved them to root-owned,
non-writable files. No interpreter or system-policy change was made.

[Fresh staging](fresh-source-custody.stdout) copied reviewed source as data into
exclusive root-created regular inodes, closed writers and set0444 under root0500
or public root0555 parents. The staging routine checked ancestry/ACLs and used
external `/usr/bin/sha256sum` before any operator execution. Operator digest is
`91e983738a53e2d28c798ec80a748b29ee0a57cf94b415a7565feb3a3fd6ab84`.
The retained inode1102291, device64769, size22,821, nlink1 and digest were sampled
again [before install](pre-install-custody.stdout) and [before rollback](pre-rollback-custody.stdout).
Both calls used the exact reviewed argv, isolated `/usr/bin/python3 -I -B`,
empty environment except trusted PATH, and closed stdin; see [install command](install.json)
and [rollback command](rollback.json). Self-hash was not used as initial authorization.

[Install output](install.stdout) records target inode1102314, pinned manifest,
helper identity and `installed-not-launched`. It returned0 after the reviewed
operator's complete tree verification and helper4755-last sequence. There was no
separate post-install helper stat; the success receipt comes from the reviewed
operator, not an independent sandbox execution. All23 accepted guest harness/protocol
files [matched](guest-accepted-23.stdout). Producer export bytes were not separately
verified before the capacity stop, so they confer no fresh runtime admission.

## Capacity stop and cleanup

[Before login](host-before-login.json), host free was21,915,172,864 bytes. The
worker conservatively subtracted the **entire**536,870,912-byte lease again, leaving
21,378,301,952, which failed the20GiB floor21,474,836,480 by96,534,528 bytes.
The authorization required the **remaining** reserve. Thus this conservative
worker guard does not establish that correctly reduced remaining-reserve admission
would have failed. No threshold was lowered or retry attempted; the worker stopped
and returned the lease for coordinator disposition.

No campusqa login or holder/renderer process started, so no graphical logout or
inhibitor release was applicable. [Cleanup](cleanup-observation.stdout) records
loginctl output supporting no logged-in/lingering user1000 and active polkit.
Its semicolon-separated shell tests retain no individual test statuses; the final
polkit exit0 does not independently prove prior predicates or the no-UID1000-process
assertion. [Rollback](rollback.stdout) returned0 with
`removed; external ownership receipt retained`, supporting target removal through
the reviewed normal operator path. The later actual LimaStopped observation is
separate evidence. Raw commands and outputs remain unchanged (human10987).
The normal path clears the helper's privilege before complete verification/removal;
earlier identity/link/content refusal remains an untested recovery limitation.
No generic chmod/rm sweep or security-policy workaround ran.

All62 original protected entries and22 additional Office39110908 entries compare
equal after install and rollback, including bytes, identities, modes and directory
membership: [comparison](protected-comparisons.json). This is a postboot baseline,
not a claim of whole-boot immutability. Only the authorized root source directory,
public operator directory and external installation ledger remain; the new runtime
is gone. The guest evidence base was never created. Historical archive/extraction,
keyrings and1057 paths are preserved.

[Stopped readback](stopped.json) at18:28:45UTC records7,890,403,328 allocated bytes,
same disk inode, host24,314,380,288 free. Peak observed disk allocation was
8,193,835,008 (+322,502,656); final growth19,070,976 does not lower that highwater.
The full512MiB new allowance plus prior corrected1,262,161,920 reserve totals
1,799,032,832, below2GiB. Final source/receipt/Git accounting is recorded separately.
Floors and peaks are sampled; no continuous resource enforcement claim is made.

## Observation limits and handoff

UTM `utmctl list` failed with macOS Automation OSStatus-1743. Read-only process/open-file
inspection found only the UTM application, no QEMU guest, and Docker's unrelated
Virtualization process. No UTM operation or settings change ran; no fresh successful
native UTM status is claimed. A preboot disk lookup initially used nonexistent
`diffdisk`; the actual `disk` path was then verified before boot. A local orchestration
import typo failed before guest work and was corrected via runpy. Raw guest command
stdout/stderr and exact argv are retained, including the expected loginctl absence
message after rollback. The failed capacity assertion is retained in its JSON sample.

The two accepted10944 P3 fixes identify the intended archive rejection guards and
correct historical1288 final-versus-highwater wording without altering raw receipts.
Next owner is active human LINUX-20261016 under10963, for independent review,
exact-head CI/Council and any separately authorized runtime window. No worker watcher,
automatic wakeup, readiness, merge, task completion or dependency completion is implied.

## Source-only publication under direction1341

Human10979 authorized this source-only continuation after runtime10963 closed.
[Accounting](source-publication-accounting.json) preserves peak guest growth
322,502,656 + host receipts274,432 + the full16MiB source/Git/temp reservation
=339,554,304 bytes. Final guest shrinkage does not reduce this charge. The original
18:31:04 publication failure remains recorded:21,380,030,464 host available minus
197,316,608 remaining runtime reserve =21,182,713,856, below21,474,836,480.
The new source-only step has no remaining512MiB runtime reservation. Its fresh
admission subtracts the conservatively unconsumed full16MiB from host available
and requires at least19,327,352,832 bytes. No guest boot, login, installer, retry,
build or download is authorized here; proposed retry namespace sources are excluded.

[source-verification.txt](source-verification.txt) is the preserved **precommit**
58-test check output from10976, not the final exact-head verification receipt.
The final exact-head command/result and publication SHA are recorded in the card/PR
handoff. Root LINUX-20261016 owns review, CI/Council and any next runtime activation.
