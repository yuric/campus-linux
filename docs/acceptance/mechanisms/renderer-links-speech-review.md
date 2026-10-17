# #982 renderer, task-link and speech source self-review

Worker self-review for LINUX-20261016, 2026-10-16. This covers the complete executable
source under `spikes/982/renderer` (including Electron), `spikes/982/links`, and
`spikes/982/speech`, their pin/fixture inputs, and the corresponding mechanism docs/raw
captures. It is neither independent review nor coordinator acceptance. No VM command,
download, owner-provider operation or benchmark was run by this reviewer.


> Historical self-review, superseded where noted below by the evidence corrections
> at `04e0fb1229c808008d8ec61cddcfc8dc9d4f5fae` and direction 1196. The original
> captures and historical file hashes remain intact. Current receipt scope and
> limitations in [renderer-speech.md](renderer-speech.md), [task-links.md](task-links.md)
> and [speech-offline.md](speech-offline.md) govern; this document supplies no extra
> session, timing, cleanup-source or product acceptance.

## Findings and disposition

1. **Motion admission accepted incomplete traces — corrected.**
   `motion_evidence.py` checked settled zoom targets but did not require input, gesture or
   checkpoint rows. Removing all three arrays from the actual v5 receipt still passed the
   old checker. The corrected checker requires both complete ordered six-segment inputs
   with the exact fixed pose formula, continuous down/move/cancel gestures, all seven
   ordered checkpoints with increasing draw counts and finite main/view matrices, and no
   performance samples. It preserves the existing target tolerances and measured driver.
   The actual retained Wayland v5 receipt passes. Deleting each trace array, changing a
   requested zoom, removing a segment, or removing checkpoint draws now fails. This checks
   capture completeness; cached per-program matrices are not instantaneous camera-state
   proof. The separate fresh active-program settled readbacks prove the absolute targets.

2. **Compositing candidate could reuse another policy's motion proof — corrected.**
   `freeze.py` matched native evidence and environment variables but omitted the explicit
   requested policy. It now rejects a different `compositing_policy`. A synthetic copy of
   the real receipt, with only its checker hash updated for the host test, was rejected
   against an otherwise identical opposite-policy environment. That synthetic test was
   temporary and is not guest evidence. Both this fix and the new checker need newly
   identified diagnostic freezes/proofs before timing. Earlier receipts remain untouched.

3. **Task-link restoration could follow a substituted symlink — corrected within the
   disposable scope.** `links/probe.py` formerly hashed by pathname then restored using
   `write_bytes`. It now opens snapshot/read/write descriptors with `O_NOFOLLOW`, rejects
   nonregular files, checks the same descriptor's bytes before restoring through it, and
   creates the test desktop file exclusively. Temporary-file removal verifies inode/device
   before unlink. Host checks passed original byte/mode restoration, changed-byte refusal,
   symlink-target preservation, FIFO refusal without blocking, and new-file removal.
   The operation is still cooperative snapshot restoration: there is no atomic guarantee
   against malicious same-UID writes, renames, or parent-directory substitution. It must
   remain in the owned disposable guest, never be applied to owner defaults, and never be
   represented as the product workspace race-safety mechanism. Historical session captures
   predate the cleanup change. Current `links-{x11,wayland}-{deb,appimage}-nofollow-*`
   reruns now pass all twelve cases, active/visible observations, UI stop and restoration
   in all four tuples, bound to the new probe hash.

## Historical fixed bytes and host verification

These are hashes at the initial review, not current-source identities. Later
corrections below supersede these bytes. Current `run-webkit.py` SHA-256 is
`19111e1b9b374c159333d7174a0986b6761a9cb72fdf60ef3085b89b39ec674d`;
the [direction 1200 freeze](repair-1200.md) records later timing-source identities.
Historical producing hashes remain unchanged.

| File | SHA-256 at the initial historical review |
| --- | --- |
| `measure.js` — unchanged | `0b252839b5c6b6f485cf5c735aa4bcee1e662f6ac2a423032bc8c36d223c86e0` |
| `run-webkit.py` — historical, before diagnostic-timeout correction | `543548f2d362e3307fa62636ef666d6a9ee71e5206e62b62bf6cff040e8db352` |
| `motion_evidence.py` | `ec3a984d6bb3edbaddff1a3e0ea26fba492e0c8cdd33201aec6e5d00282d9901` |
| `freeze.py` | `37e99c8b3494be361e4991a8b6a916b997c1075db93328249a6dfe9445ddf0ad` |
| `links/probe.py` | `a59d69833f46b76106d67036ab5ffc30bdf04b80a3ab336098d6bfa8024f6cd1` |

Commands: `node --check spikes/982/renderer/measure.js`; Python `compile()` over every
`.py` below the three reviewed folders; `git diff --check`. All pass. The targeted host
checks above imported `verified_motion`, `snapshot`, and `restore_default` directly and
used only temporary files. No original capture, MIME association or VM state was changed.
To repeat positive motion admission:

```sh
PYTHONPATH=spikes/982/renderer python3 -c 'from motion_evidence import verified_motion; print(verified_motion("docs/acceptance/mechanisms/receipts/motion-proof-wayland-v5.json")[1])'
```

Expected/observed digest:
`847b4b7cfbb17ec51f4934b1ac24da2c70cefa2a022979fb08042bb82b2bcdc8`.
Negative copies must be made in a fresh temporary directory, never by editing that raw
receipt. Removing `inputs`, `gestures`, or `checkpoints` must raise `ValueError`.

## Remaining evidence and operating limits

The actual Wayland v5 proof has no errors/invalidations and settles both initial zooms at
1 and diagnostic targets 1.5/0.75/1 within `1e-5`. It has zero performance-frame samples.
G8 stays unaccepted: five valid separate 60-second runs after 30-second warmups have not
been captured. Human 10420's scheduling hold and the 35 GiB reserve govern further work.
The numeric summarizer computes intervals and nearest-rank p95; it is not an independent
provenance checker. Use the five-run wrapper and review distinct raw captures/freezes,
session/native evidence and the returned `gate_pass`. A zero subprocess exit alone is
not a numerical performance pass. No fallback or optimization result has been observed.

The review found no additional demonstrated escape from the bounded synthetic speech
source: the recorder names the unique monitor explicitly, verifies its device name and
sets `PA_STREAM_DONT_MOVE`; orchestration stops streams before source unload. Same-user
audio access is explicitly not an isolation boundary. Offline inference returns a success
status for inference availability; reviewers must separately inspect cancellation and
invalid-audio rows rather than interpreting that status as whole speech acceptance.
The actual receipts contain successful cancellation and bound rejection, but only English
synthetic batch audio, mutable backend files and native synthetic capture were tested.
Locale, real permission UI/revoke, quality, streaming, recovery and product-editor parity
remain unproven. No library adoption approval or new service/spend/privacy choice is inferred.

Electron's pinned archive/extraction were deleted for reserve recovery. The prepared
sandboxed fallback host has no real guest launch/GPU/sandbox/performance proof. Task links
cover synthetic deep-link activation, not the shipped localhost HTTP bridge or real account
authorization. All final package cases repeat under LINUX-16/17. LINUX-20261016 owns the
remaining runs, independent review and #1030 → #1031 handoff; this review does not complete
dependencies or authorize production commitment.

## Diagnostic timeout follow-up

**Superseded attribution:** the precise operator-clock value and causal explanation
in the following historical paragraph were not retained as reproducible evidence.
They are withdrawn as proof; the actual v6 timeout remains a failure. See the
current [timeout qualification](renderer-speech.md) and unchanged diagnostic/timing
limits. Direction 1196 only repairs floating-point duration equality with the
existing `1e-6` tolerance; it adds no cadence/max-gap metric or performance bar.


The subsequent X11 v6 untimed probe timed out at the original 115-second host budget.
Its operator log showed the 60-second diagnostic clock starting around 55,131 ms after
extra settled-target checks, warmup and reset. The failed raw receipt remains
`motion-proof-x11-v6.json`, SHA-256
`c612454102db15b30ec0eb3d6341c1fc1fe594eff09399aa74490764cf9b0242`.
Only motion/lifecycle diagnostics now receive a 180-second total host timeout. Timed
hosts retain 115 seconds and the GTK five-run subprocess retains 125 seconds; all G8
clocks, thresholds and measured JavaScript are unchanged. This is an identified harness
timeout correction requiring fresh runner-bound freezes, never performance acceptance.

Updated `run-webkit.py` SHA-256:
`19111e1b9b374c159333d7174a0986b6761a9cb72fdf60ef3085b89b39ec674d`.
Updated `electron/main.cjs` SHA-256:
`c5d9bb3dda1b4c6045c5848cb5090ac000afd3cb78b2ff18cc137e0754f76aee`.
Python compilation, `node --check spikes/982/renderer/electron/main.cjs`, and
`git diff --check` pass. No guest run was performed by this reviewer.

## Current final session evidence

X11 v7 motion SHA-256
`905c56f786fab5346e2b7bb1e41a735cfb049baebd53d030f321331397b3ff03` passes the stronger
checker against the revised runner, with 1,292 inputs, seven checkpoints and no errors or
invalidations. Its two absolute-1 resets and 1.5/0.75/1 checks settle within `1e-5`; it
contains no performance frames. The final Wayland v7 repeat also passes: SHA-256
`62288eb7f53450666ae1bf975f441b82812367bac52421b3d60ab9b99f9e2e5d`, 1,293 inputs,
seven checkpoints, no errors/invalidations, and zero performance frames. It binds the
same final runner `19111e1b9b374c159333d7174a0986b6761a9cb72fdf60ef3085b89b39ec674d`
and checker `ec3a984d6bb3edbaddff1a3e0ea26fba492e0c8cdd33201aec6e5d00282d9901` as
X11. Both final captures pass the checker locally. Their absolute-target proof does not
establish G8 timing acceptance; the full five-run timing series remains held.

All four final task-link `-nofollow-` result/cleanup receipts use probe
`a59d69833f46b76106d67036ab5ffc30bdf04b80a3ab336098d6bfa8024f6cd1` and pass. The precise
links/PIDs are in [task-links.md](task-links.md). This closes execution of the bounded
cleanup correction in both formats/sessions; it does not establish adversarial same-user
race safety, HTTP bridge behavior or final-product acceptance. Earlier failures remain.

## Producing-source and cleanup limitation, direction 1196

The historical host-check statements above are unretained operator checks, not
source-bound runtime receipts. Final task-link results name the probe hash, but
that does not separately bind every outer host orchestration/cleanup command at
execution. Retain their observed restoration results within the stated cooperative
scope; do not infer hostile same-user race safety, complete graphical-session
provenance or a separately verified producing-source chain. Historical provider
and speech orchestration source remains unbound as documented at 04e0fb12.
The new Apport pair binds its actual host runner, guest runner, launcher, inherited
filter and cleanup-function source at execution; this does not retrofit those
bindings into any old capture.
