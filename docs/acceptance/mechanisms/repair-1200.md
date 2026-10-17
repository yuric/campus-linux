# Direction 1200: bounded review repairs for PR 12

LINUX-20261016 / card #982. This batch repairs the four findings against
`a975d6747fe0d29932182bb07ad3b7fb01da7e3c`. It preserves all historical captures,
including both original metadata failures and the valid matched SIGQUIT
activation/suppression result. No full G4, G8 or product acceptance follows.

## Non-crashing metadata result

The corrected [guest preflight](../../../spikes/982/security/apport-metadata-preflight.py)
reads the stopped target's real UID/GID and asserts all four UID/GID slots against
the disposable account. It opens the proc directory and establishes ExecutablePath
as root, clears supplementary groups, then sets and verifies effective UID/GID,
matching the installed Apport 2.28.3 metadata access sequence. It passes that open
descriptor to `add_proc_info`. It records the named failure stage on exceptions,
retains pidfd signaling and start identity checks, restores controller credentials,
and checks the owned unit's removal. Only SIGSTOP and SIGKILL are sent.

The [run2 metadata receipt](receipts/apport-metadata-1200-run2/metadata.json)
passed with target/effective UID **1000**, GID **1001**, groups `[]`, all original
stopped-ELF/namespace predicates, and **3,559 serialized non-core metadata bytes**.
PID 2374/start tick 12118 was cleaned; its cgroup is absent. The exact handler and
report module SHA256 values and installed package MD5 records passed in the
[identity capture](receipts/apport-metadata-1200-run2/identity.json). Package database
checks are not independent publisher authentication. No core/report was generated,
no collector was invoked, and no decoded marker or collector-stop proof was attempted.
Changing all identified context mismatches together does not establish a sole cause
for the old `ValueError: not accessible` failures.

[The host runner](../../../spikes/982/security/run-apport-metadata.py) binds transferred
sources and checks guest hash readback before execution. It refuses existing output
directories and checks host >=20 GiB, guest >=2 GiB, exact installed source hashes,
and absent prospective report paths. The first execution collected successful
metadata but failed JSON parsing because a benign dpkg warning was merged into
stdout. Its [raw output](receipts/apport-metadata-1200-run1/metadata-output.txt),
[failed host receipt](receipts/apport-metadata-1200-run1/host-runner.json), and producing
sources remain unchanged. Run2 separates and retains
[stderr](receipts/apport-metadata-1200-run2/stderr-6.txt); it does not suppress the warning.
The historical identity helper still reports its superseded guest-20-GiB predicate;
this runner enforces the authorized **2 GiB** guest floor.

The [normal stop log](receipts/repair-1200/stop.txt) and
[accounting](receipts/repair-1200/shutdown-accounting.json) confirm Lima stopped and
its sole lease returned to LINUX-20261016. Each new guest source directory occupied
24 KiB. Output is small public source/metadata, within the 64 MiB explicit allowance
and 256 MiB operational owned-growth allowance. No large build/download, global
collector change, unrelated cleanup, Office377 path, UTM operation, real credential,
speech download or G8 timing occurred. Global free-space deltas do not attribute
sparse VM/journal growth or establish a kernel-enforced aggregate quota.

## Timing and arithmetic repairs

The driver now records `sampled_at`, the actual `performance.now()` used to compute
logical seconds, separately from post-dispatch `at`, and records `warmup_start_ms`.
The validator requires prior dispatch <= next sample <= current dispatch, and checks
seconds against the phase origin at **500 ms** per logical warmup second and
**1000 ms** per measurement second. Initial samples use the phase origin; the final
explicit pose is clamped to 60 after the stop predicate. There is no maximum dispatch
delay, input cadence, maximum frame gap or minimum-frame rule.

Both `summarize.py` and `motion_evidence.py` apply the existing **1e-6 ms** arithmetic
tolerance to input-span subtraction. Regression coverage includes the fractional
49374.001 first input / 109374.00099999999 final input boundary, both phase spans,
complete logical poses with inconsistent clocks, wrong/nonfinite sample clocks,
and an admitted four-second synchronous dispatch delay. Existing missing-segment,
fixed p95 and all-five tests remain. Test fixtures are explicitly synthetic; adding
sample clocks in memory never upgrades a historical browser receipt.

The new [source freeze](receipts/repair-1200/renderer-source-freeze.json) records the
producing/checking bytes for future work. It is **not timing admission**. A new
coordinator-authorized untimed motion proof and `freeze.py` environment/source binding
are required before future timing; old v7 captures retain their original hashes and
cannot bind this changed driver. Historical source copies are under
`receipts/repair-1200/historical-a975/`. The 30-second warmup, 60-second measurement,
p95 <=33.3 ms and all-five-run rule are unchanged.

## Private input and review handoff

The dedicated `.gitignore` entry covers `spikes/982/environment/private/`.
[The static check](receipts/repair-1200/private-input-static-check.json) confirms the
password path is ignored and no private path is tracked. No credential was opened,
created or used as a test payload. The helper's owner/mode/regular-file/nofollow/stdin
protections are unchanged; this finding does not imply credential rotation.

Self-review covers the complete repair diff, source/receipt bindings, both retained
host runs, phase-clock boundaries and the original full-PR scope documented in
[delivery.md](delivery.md). Required local repository checks and both architecture
commands are recorded on the card for the committed head; unavailable capacity is
reported as blocked, never a pass. Coordinator LINUX-20261016 owns independent
exact-head review, hosted CI, Council and merge. PR 12 remains draft; no ready,
auto-merge, done or downstream release action is authorized by this repair.
