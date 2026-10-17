# Bounded crash-collector follow-up, direction 10470

This is **worker evidence for LINUX-20261016's consolidated repair batch**. The
probe started with PR #12 frozen at `d784405d34437cd68cb8349efef588d7d5ae2470`;
later direction 10480 authorized one consolidated repair push. Both directions
arrived during the delayed speech-direction #1163 follow-up.
No release, provider-account, speech-product or renderer acceptance is conferred.

## Result and remaining blocker

The actual Ubuntu arm64 kernel rejected core collection after exec with
`RLIMIT_CORE=(1,1)`, including a filtered child and a fork/exec/setsid grandchild.
The narrow inherited filter denied core-limit mutations while allowing queries and
non-core operations. Failure controls withheld the synthetic credential and exec.
This establishes the tested launch mechanism, **not full G4 closure**.

Case A, a normal collector positive control, is **inconclusive and was not run**.
The installed Apport handler bounds its core input by three quarters of usable RAM;
that does not establish the requested 16 MiB bound on the complete report from this
Python fixture. No normal zero-limit interpreter dump was launched. A safe fixed
fixture plus a demonstrated complete core/report footprint bound remains necessary.
Missing reports alone cannot establish that an otherwise working collector was
blocked. Here, separate exact-PID kernel diagnostics establish the sentinel branch.

Provider binary compatibility and provider-owned crash/reporting paths remain
unproven. No arbitrary same-user or root isolation, user-space reporter suppression,
x86_64 compatibility, installed-product acceptance or future-kernel guarantee is
claimed. In particular another same-UID process is outside this inherited filter;
all authorized launch routes would need the trusted launch stage.

## Inputs and reproduction

The coordinator supplied the source investigation with task #982 direction 10470.
Primary sources include [Linux 6.8 core collection](https://github.com/torvalds/linux/blob/v6.8/fs/coredump.c),
[resource limits](https://github.com/torvalds/linux/blob/v6.8/kernel/sys.c), and
[seccomp inheritance](https://docs.kernel.org/userspace-api/seccomp_filter.html).
The installed guest, rather than the report's reference Apport release, was measured:

- Linux `6.8.0-142-generic`, package `6.8.0-142.142`, `arm64`.
- Apport `2.28.3-0ubuntu0.1`, enabled; handler SHA-256
  `1b8b5e2c53e8970dd2f47c9a0892030d1ebad57cae1f7242c43a6252f1f6dff2`.
- systemd `255.4-1ubuntu8.17`.
- Kernel pipe pattern uses `/usr/share/apport/apport`, `core_pipe_limit=10`.
  Neither setting nor Apport configuration was changed.

The [launcher](../../../spikes/982/security/core-sentinel-probe.py) uses existing
Python/ctypes and a fixed aarch64 little-endian BPF program: architecture mismatch
kills; `setrlimit` core mutations and `prlimit64` core mutations with nonnull new-limit
pointers return EPERM. Resource comparison uses its low unsigned 32 bits; pointer
comparison covers both 32-bit halves. Unsupported host ABIs refuse before install.
No compilation, dependency installation, public download or real credential is used.
It sets/verifies the limit and filter before placing a public synthetic marker in
the child environment. It never applies child `PR_SET_DUMPABLE=0`.

On an already running, exclusively owned named guest, copy the launcher to
`/home/campusqa/spike982/core-sentinel-10470/probe.py` and run from this repository:

```sh
python3 spikes/982/security/run-core-sentinel.py /path/to/fresh-output-directory
```

The [runner](../../../spikes/982/security/run-core-sentinel.py) refuses existing
output directories and checks host free space before each case. Every case uses a
unique transient **system-manager unit with User=campusqa**, not a user-manager unit:
there was no `/run/user/1000/bus` at the greeter. This difference is explicit; no
graphical-session/user-manager lifecycle proof is claimed. Commands and observed
process cgroups are captured. Units set private networking, 64 MiB memory, no swap,
eight tasks, 100% CPU quota, 20-second runtime and two-second stop grace. The
launcher needs an initial hard core limit permitting `(1,1)`; failure is refusal.

## Observed cases

Authoritative captures are in [final3](receipts/core-sentinel-10470-final3/identity.json).
The final launcher SHA-256 is
`3aca30e49471b4c12cbcd5c6abcccf9a9f1006262beb4eaedb3e36e03d3ba22d`.
All nine runner assertions passed. Each case finished in less than 30 seconds,
including its three-second bounded observation. The output manifest binds exact
source and receipt bytes; previous runs are retained separately.

| Case | Observed result |
| --- | --- |
| Bare sentinel, no crash | Post-exec dumpability 1, core `(1,1)`; lowering soft limit to zero succeeds. This is the bare-limit weakness. |
| Narrow filter | Raw setrlimit/prlimit64 mutations to 0, 1 and unlimited return EPERM; high-word resource aliases and a nonnull pointer with zero low word are also denied. Read-only core query and same-value non-core setters succeed. |
| Descendants, no crash | Fork/exec child and setsid/re-exec grandchild each retain `(1,1)`, dumpability 1 and filter; mutation checks pass at every depth. |
| Limit installation failure | Actual hard-limit-zero condition prevents raising to one; exit 23 before marker admission or fixture exec. |
| Filter installation failure | Empty BPF program is rejected with EINVAL; exit 23 before marker admission or fixture exec. |
| Foreign-ABI branch | Intentionally mismatched expected audit architecture kills native test process 3114 with SIGSYS before marker admission. This exercises refusal, not a real x86/compat ABI. |
| Sentinel abort | PID 3141, dumpability 1/core `(1,1)`, SIGABRT; kernel reports its exact PID has RLIMIT_CORE set to 1 and `Aborting core`. |
| Filtered abort | PID 3168 passes mutation checks, then SIGABRT with dumpability 1/core `(1,1)`; same exact-PID kernel sentinel refusal. |
| Descendant abort | Designated setsid/re-exec grandchild PID 3197 passes inherited checks and aborts; same kernel refusal. Parents reap descendants and exit successfully. |

Each recorded PID has boot ID, start ticks, cgroup and before/after-exec state.
The three-second poll found no matched collector process, no original PID remaining,
and no remaining unit cgroup. Sampling can miss a short process; it is not offered as
standalone proof of no invocation. Kernel sentinel messages supply the stronger
positive observation. Actual unit-manager exit information records SIGABRT/SIGSYS.

Before/after metadata was identical in `/var/crash`, the installed Apport storage
`/var/lib/apport/coredump`, `/var/lib/systemd/coredump`, and the fixture working
directory. The pre-existing netplan crash file was not opened or modified. The
Apport log had no growth. Own unit journals contained no synthetic marker. No new
attributed core/report or compressed payload existed to scan; no support bundle
was generated. These bounded observations do not cover arbitrary retention paths.

## Failed harness evidence and budget

The initial six-case [run](receipts/core-sentinel-10470/filtered.json) binds the saved
`launcher-v1.py`. Its syscall results remain historical. The first full
[run](receipts/core-sentinel-10470-final/sentinel-abort.json) used an ISO timestamp
with comma fractional seconds that journalctl rejected (exit 1): its empty kernel
arrays are **failed observations**, never absence passes. The saved `runner-v1.py`
preserves that source. The [second full run](receipts/core-sentinel-10470-final2/sentinel-abort.json)
fixed timestamps and captured kernel rejection, but omitted Apport's actual core
directory from snapshots. `runner-v2.py` preserves that limit. Final3 adds the
installed storage path and fileutils digest; it does not rewrite either earlier run.

No positive dump or new crash output was retained. The 16 MiB crash-output cap was
not approached. The conservative allocation receipt counts **all** current guest
`/var/log` files (about 104 MiB, including pre-existing logs), plus this probe's
files, rather than attributing global host-free-space changes to this run. This
upper bound plus the prior recorded 96.57 MiB allocation and the small new local
sources/receipts is below the 256 MiB allowance. Every case separately records
more than 20 GiB host free. No unrelated workload or UTM guest was changed.

UTM CLI status returned not-found and list returned OSStatus -1743. A read-only
host process inventory found no QEMU guest before Lima startup. This does not
repair UTM automation; its earlier credential/setup handoff remains separate.

## Speech direction and publication repair

Direction #1163 was explicitly acknowledged for attempt
`c4cb4d3a-a39a-4cf8-af07-03e8ceed92fe`. Its earlier implementation is already in
[the offline speech report](speech-offline.md): whisper.cpp v1.9.5 plus tiny.en,
offline synthetic inference, resource measurements, native synthetic audio capture,
cancellation and editable plaintext. Recommend continuing the measured local
whisper.cpp route, with locale/quality/streaming/recovery and actual microphone
consent evidence before any product adoption. Tiny.en is only a small English
mechanism fixture; it cannot narrow the Mac current-locale requirement. No cloud
fallback, paid call or owner-login copy was enabled. Later direction 10427 clarifies
that a library name alone does not need new owner approval; concrete changed
product/privacy/spend/trust trade-offs do.

Fresh checkout validation found nine raw logs indexed at d784405 but excluded from
the commit by `*.log`. All nine were recovered read-only from their original guest
locations, with exact recorded byte lengths and SHA-256 values. The consolidated
repair includes those original logs using `git add -f`. Original capture hashes
are unchanged; current source inventory hashes are refreshed for the reviewed
source changes. Historical source remains available at d784405 and each original
receipt keeps its own source identity. The new repository check requires tracked
membership plus exact size/hash, with regressions for ignored logs, missing files
and changed bytes. This corrects the earlier overbroad published-delivery claim.

LINUX-20261016 is the explicit coordinator handoff owner. Root owns
the repair batch, independent review, Council, CI and merge. Next steps are the
bounded positive collector fixture, provider compatibility/reporting inventory and
all previously retained G8/account/update/final-package evidence. No future worker
wakeup is assumed. Direction 10480 permits this single consolidated push; ready,
merge and task completion remain coordinator-owned.
