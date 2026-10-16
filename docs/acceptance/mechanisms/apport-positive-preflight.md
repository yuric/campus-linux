# Apport positive-control preflight, direction 10500

The full matched crash experiment was **not run**. Two preconditions failed before
any crash signal: the supplied plan's guest storage floor, and the unchanged unit
profile's mount namespace. The failed preflight is retained. It gives no collector
positive, G4 closure, provider compatibility or product acceptance.

This follow-up began on published draft PR #12 head
`04e0fb1229c808008d8ec61cddcfc8dc9d4f5fae`. Direction 1169 was acknowledged for its
exact delivered attempt; the later task comment 10500 governs the bounded probe.
The published head stays frozen while LINUX-20261016 reviews it. This evidence is
held locally for the coordinator's next batch, with no push or acceptance action.

## Superseding direction 1196 (task comment 10512)

The historical observations below and commit `26f6909f0e491145e383b666c913bdc92cab7c46`
are preserved. The coordinator resolved both experiment settings: **host 20 GiB,
guest 2 GiB**, with 64 MiB explicit files inside 256 MiB operational owned growth;
the separate 35 GiB large-work reserve remains. Both new synthetic arms use
`PrivateNetwork=no` and verify mount/PID namespaces against PID 1. The supplied
plan's assertion that `PrivateNetwork=yes` preserved the mount namespace was
incorrect on this installed systemd configuration. These are experiment settings,
not production provider network policy. See [the activation result](apport-activation.md).

## Observations

The [identity capture](receipts/apport-positive-preflight-10500/identity.json)
binds the [read-only source](../../../spikes/982/security/apport-positive-preflight.py)
and exact invocation. The actual Ubuntu arm64 kernel is 6.8.0-142-generic,
package 6.8.0-142.142. Apport 2.28.3-0ubuntu0.1's handler, `report.py` and
`problem_report.py` all match the coordinator's primary-source hashes. The four
checked files, including `/usr/bin/sleep` from coreutils 9.4-3ubuntu6.3, also match
the installed package database's MD5 entries. These local package checks do not
independently authenticate a publisher. The exact proposed sleep `.crash`,
`.upload` and `.uploaded` paths were absent and were not read or created.

The plan's execution step 1 requires at least 20 GiB free on **host and guest**.
Guest free space was 20,410,814,464 bytes (19.01 GiB), so that predicate fails.
The host had 27,372,023,808 bytes before startup (25.49 GiB), above the separately
authorized 20 GiB small-probe floor and below the unchanged 35 GiB large-work
reserve. No download, build, model, image or large export was started. No cleanup
was performed: final artifacts and diagnostic evidence were retained.

The separate [non-crashing ELF preflight](receipts/apport-positive-preflight-10500/sleep-preflight.json)
binds [its source](../../../spikes/982/security/apport-sleep-preflight.py).
It ran the existing distro sleep in a transient **system-manager** unit with
`User=campusqa`, `NoNewPrivileges=yes`, `PrivateNetwork=yes`, 64 MiB memory,
no swap, eight tasks, 100% CPU, a 20-second runtime and two-second stop grace.
The launcher prepared the exec arguments/environment before setting its 8 MiB
address-space limit; no interpreter startup under that small limit was assumed.
The child received only the documented public synthetic marker, LANG and PATH.

At PID 2316, boot `c5e3e5df-c86c-4413-af92-336a7ba87c76`, the stopped ELF had:

| Predicate | Observation |
| --- | --- |
| Address-space soft/hard limit | 8,388,608 / 8,388,608 bytes |
| Mapped ranges / VMA count | 2,322,432 bytes / 16 |
| Mapped pathname bytes | 369 |
| Environment | Exact allowlist, 75 bytes |
| Threads | One |
| Core soft/hard limit | 0 / 0 |
| Per-process coredump filter | 00000001 |
| NoNewPrivileges | 1 |
| PID namespace versus PID 1 | Same |
| Mount namespace versus PID 1 | **Different: preflight failed** |

The fixed command line contained no marker. This preflight sent only SIGSTOP
and SIGKILL through its owned pidfd; no SIGABRT or SIGQUIT was sent. Its cgroup
was absent after cleanup. Report metadata sizing was deliberately not reached
after the namespace predicate failed. No core stream or report was produced.

The exact [Apport handler](https://github.com/canonical/apport/blob/2.28.3/data/apport#L778)
checks mount and PID namespaces before its normal collection path. With the
observed different-mount/same-PID combination it returns after logging that it
ignored the crash. Therefore retaining this profile for a positive crash would
not establish the intended report/marker control. The prior assumption that the
private network profile leaves the mount namespace unchanged is disproved for
this installed systemd configuration. This does not invalidate the prior
exact-PID kernel sentinel diagnostics; those never established a collector positive.

## Coordinator handoff

Task questions 10505 and 10506 report the exact blockers to the active human
coordinator LINUX-20261016. Recommended adjustments for a later matched pair:

- Clarify the additional guest 20 GiB requirement, while preserving both host
  floors and the 64 MiB explicit-file / 256 MiB owned-growth limits.
- Permit `PrivateNetwork=no` for both synthetic arms so a fresh measured
  same-mount/PID preflight can pass. The fixed sleep fixture has no network work;
  no provider payload or account is involved. This change has not been applied.
- Verify the actual Ubuntu kernel's relevant note producers before admitting
  the proposed 14 MiB report bound. Installed headers exist, but complete
  `arch/arm64/kernel/ptrace.c` is not present there. Upstream v6.8 source alone
  does not establish an exact distribution-kernel bound.

After those prerequisites, a new source-bound preflight must verify metadata size,
descriptor inheritance, final process identity, all bounds and ownership before
the matched signals. No old failed receipt should be rewritten. A complete
positive must still include the actual collector trace and synthetic marker in
stream-decoded CoreDump, followed by the matched filtered negative.

Lima shut down normally at 13:10:04 UTC. UTM was not operated. Its CLI status
lookup reported not found; a read-only QEMU process check found no guest before
Lima startup. This does not repair or certify UTM. No global core, sysctl, Apport,
credential, unrelated workspace or Docker/CI setting was changed.

Only small source/JSON records were written on the host. The identity capture
records an intentionally conservative whole `/var/log` allocation upper bound
(114,270,208 allocated bytes), including preexisting logs; it is not attributed
growth. Global free-space differences are not treated as this probe's allocation.
No full crash-pair aggregate-storage claim is made.
