# Matched Apport activation control, direction 1196

**The matched SIGQUIT collector-activation pair passed; no full crash-report or
marker-persistence proof is claimed.** This follows task comments 10512/10517 under
LINUX-20261016. It does not close G4, provider Crashpad handling, same-user secrecy,
G8 or final-product acceptance. No provider credentials or model calls were used.

## Current authority and admission

Comment 10512 corrects the prior plan to host **20 GiB** and guest **2 GiB** free,
64 MiB explicit output inside 256 MiB operational owned growth, with the separate
35 GiB reserve for large work unchanged. Both arms use `PrivateNetwork=no` and
measure their mount/PID namespaces against PID 1; the prior claim that private
networking preserved the mount namespace was false on this system. This is a
synthetic collector control, not a provider network policy. The existing sleep
binary performs no networking and receives only LANG, PATH and a public marker.

The later comment 10517 removes exact Ubuntu register-note source retrieval as an
admission requirement. Upstream 6.8 layout plus actual runtime facts can support
practical one-shot budgeting; 14 MiB is an estimate, not a formal distribution
bound or acceptance threshold. Earlier source-unavailable language in raw runner
records describes the earlier direction and is superseded here. The **original
metadata preflight failed**, so the explicitly permitted SIGQUIT fallback
was used. No global Apport/kernel/service settings, dependencies or VM sizes changed.

## Results and source binding

The host [runner receipt](receipts/apport-activation-1196/run2/host-runner.json)
records exact commands, per-operation host free space and producing-source hashes.
[Guest hash readback](receipts/apport-activation-1196/run2/guest-source-hashes.txt)
verifies transferred bytes before execution. Source is the
[host runner](../../../spikes/982/security/run-apport-activation.py),
[guest runner](../../../spikes/982/security/apport-activation-pair.py),
[launcher](../../../spikes/982/security/apport-activation-launch.py) and unchanged
[sentinel filter](../../../spikes/982/security/core-sentinel-probe.py).
The guest receipts also bind the cleanup function's exact source hash at execution.
These bindings do not retroactively bind older host orchestration or cleanup.

The [identity](receipts/apport-activation-1196/run2/identity.json) retains installed
kernel/package identities and verifies handler/report-module hashes and package
MD5 records. Installed package metadata is not an independent publisher signature.
Kernel is Ubuntu 6.8.0-142-generic, arm64; Apport is 2.28.3-0ubuntu0.1.
The package-owned sleep SHA256 is
`5b814cc93d7f2110d40c936f5f86a6135de783ae2a28afe25eabac4ecc25bf10`.
These are system-manager transient units with `User=campusqa`, not user-manager units.

| Arm | Actual observation |
| --- | --- |
| [Positive](receipts/apport-activation-1196/run2/positive.json) | Sleep PID 2429/start tick 17744; core 0/0, no seccomp filter. Apport PID 2433/start tick 17750 observed with exact crash argv. Its log says global PID 2429, signal 3, core limit 0, dump mode 1. |
| [Negative](receipts/apport-activation-1196/run2/negative.json) | Sleep PID 2442/start tick 18071; core 1/1 plus existing inherited filter. Kernel says `Process 2442(sleep) has RLIMIT_CORE set to 1`; no matching collector, collector log delta or owned report observed. |

Both use identical launcher, executable, environment, signal and profile except
core limit/filter. Each has 8 MiB AS, 2,322,432 mapped bytes, 16 VMAs, one thread,
NoNewPrivileges=1, coredump_filter=1, exact 76-byte allowlisted environment, fixed
argv and only standard FDs. Both mount and PID namespaces match PID 1 immediately
before signaling the stopped process through its retained pidfd. Both cgroups
are absent after cleanup. Boot ID is `d915aa24-3314-474a-aadf-4ee4fa6f2bf8`.

Observation ended after fixture exit, absence of an active matching collector,
and a three-second quiet interval (3.088/3.024 seconds total respectively), within
the 60-second deadline. Fast collector sampling alone is not absence proof; the
positive has its exact collector log, and the negative has the exact-PID kernel
sentinel diagnostic. No timeout or collector-termination path was exercised.
No `.crash`, `.upload` or `.uploaded` path existed before or after either arm.

The exact handler's SIGQUIT branch calls the zero-limit user-core path and returns
before report construction. Zero returns before opening a raw-core destination
or ambient cleanup. Therefore this establishes real collector activation for the
positive and kernel suppression for the matched negative, **not** report creation,
a decoded marker match or absence of all possible userspace secret persistence.

## Retained failures and remaining full-report proof

The [metadata attempt](receipts/apport-activation-1196/run2/metadata.json) passed
all stopped-ELF/namespace/size predicates, then raised `ValueError: not accessible`
while collecting metadata with effective UID 1000 but the wrong effective GID
1000 (the stopped target and actual handler used GID 1001). The earlier
[run1 metadata failure](receipts/apport-activation-1196/run1/metadata.json) is also
retained. There is no serialized metadata byte count, and no claim that the
proposed 1 MiB metadata check passed. The exact failing internal metadata method
was not captured. These were **non-equivalent harness failures**: supplementary
groups were retained, the proc descriptor was not pre-opened as root, and
ExecutablePath was not established before the drop. These mismatches are proven,
but no single one is established as the sole cause. Both old failures remain
unchanged. The separately authorized [direction 1200 repair](repair-1200.md)
subsequently passed non-crashing metadata collection; it grants no full-report
or SIGABRT admission.

The [first activation attempt](receipts/apport-activation-1196/run1/host-runner.json)
failed to return its final JSON because cleanup tried to stop an already collected
unit. [The traceback](receipts/apport-activation-1196/run1/failed-command.txt) and
[unit recovery capture](receipts/apport-activation-1196/run1/unit-recovery.txt) show
SIGQUIT and subsequent unit removal; it is not counted as a complete positive.
Its actual host/guest/launcher source snapshots are retained under `run1/sources/`.
The corrected complete matched run is `run2`; no old raw capture was overwritten.
Commit `26f6909f0e491145e383b666c913bdc92cab7c46` and its prior namespace/floor
failures are preserved through [the original preflight](apport-positive-preflight.md).

A future full matched SIGABRT pair still needs separately authorized collector-stop
proof and repeated bounded metadata collection plus all runtime/source/ownership predicates, attributed collector
and report monitoring with the existing 60-second/output budgets, a complete
exact-owned report, measured encoded/decoded sizes, capped streaming decoded
CoreDump marker/hash verification without saving raw core, identity-checked own
report/sidecar cleanup, then the matching filtered SIGABRT negative. Exact Ubuntu
note source remains a provenance limitation, not a blocker under 10517. An
estimate miss must be recorded, never converted into a silent threshold change.

## Accounting, shutdown and review

Guest free space was 20,403,519,488 bytes in both matched arms, above 2 GiB. The
positive added 113 log bytes; negative added zero. Whole `/var/log` allocated size
was unchanged at 119,664,640 bytes across each matched arm; this includes preexisting
logs and is a conservative observation, not attributed growth. Host free space is
recorded before/after each runner operation and remained above 20 GiB. Small public
source/receipt writes are the only explicit outputs; no core/report export exists.
[Final host accounting](receipts/apport-activation-1196/host-final.json) records their
sizes. This is operational accounting, not a kernel aggregate quota: sparse VM
allocation/journal changes are not independently attributed from global free-space
deltas. No broad full-report growth guarantee is inferred from activation-only work.

[Normal shutdown](receipts/apport-activation-1196/stop.txt) completed at 13:20:28 UTC;
Lima is stopped. UTM was not operated. No cache or unrelated file was deleted.
The current runner refuses an existing guest output directory; reproduction needs
an explicitly new owned directory and new receipt name, not overwriting run2.

Self-review covered the additive source and all output/failure paths: fixed guest
identity/UID guards, source readback, clean post-exec context, exact pidfd signaling,
namespace predicates, bounded command/log reads, PID/start identity observation,
absence-only report inspection, explicit cleanup and retained failure receipts.
No negative result is promoted to full-report acceptance. The runner's timeout
failure path has no exercised collector kill receipt; future full-report work must
implement and prove that attributed budget-stop path before crash admission.
