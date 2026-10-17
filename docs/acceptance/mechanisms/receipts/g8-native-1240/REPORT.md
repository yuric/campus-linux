# Fresh G8 native and untimed evidence — direction1240

LINUX-20261016 / card #982 / Office400. Both authenticated GDM tuples completed fresh
native GPU capture, preflight, manually observed environment, diagnostic freeze, untimed
motion proof and proof-bound freeze. **No performance timing, optimization, Electron,
product acceptance or L0 completion is claimed.** The coordinator retains timing admission,
independent review, hosted checks, Council and merge. PR12 stays draft.

Source is accepted Linux `803ab21430aa1cee014d9d0132f35b7087f48a3d`, based on merged
PR11 `37ef5d622da09cd7ba113dc0d1119e62e7378f84`. Fresh [merge records](base-merge.json)
and [Mac producer record](producer-merge.json) are retained. The merged desktop producer is
`3e3d4bcd64fd1504c4546b2f7a063b55e2eea783`, manifest
`7b5fabefd830d3cd3d3577da1c4cb4ba55217de0f7eb5b5bbfc9501443428f09`.
Producer contract provenance remains campus-server `d93b841762183af5ba0d357f3f1c42351aeed9ff`;
no Linux contract import or API compatibility claim follows. Existing installed runtime and
export bytes were reused; no install, dependency/model download, build or Docker operation.

## Actual tuple results

| Observation | Wayland | X11 |
| --- | --- | --- |
| GDM session / leader | 8 /2342 | 12 /4077 |
| Native/preflight | [GPU](wayland-2/gpu.json), [preflight](wayland-2/preflight.json) | [GPU](x11/gpu.json), [preflight](x11/preflight.json) |
| Fresh environment | [Observed values](wayland-2/environment.json) | [Observed values](x11/environment.json) |
| Diagnostic freeze | [Current source](wayland-2/diagnostic-freeze.json) | [Current source](x11/diagnostic-freeze.json) |
| Motion proof | [Raw trace](wayland-2/motion.json) | [Raw trace](x11/motion.json) |
| Proof-bound freeze | [Freeze](wayland-2/timing-freeze.json) | [Freeze](x11/timing-freeze.json) |
| Inputs / checkpoints / performance frames | 1270 /7 /0 | 1363 /7 /0 |
| Errors / invalid foreground events | empty /empty | empty /empty |

Both captures independently passed the unchanged host `verified_motion` checker after
transfer. [Validation and external freeze hashes](independent-motion-validation.json)
record the exact proof/freezes; success is not inferred from host exit0. Both resets reach
absolute zoom1; fresh settled1.5/0.75/1 checks, six-segment traces and gestures are in the
raw proofs. Fixed12projects/48agents/180tasks,1440x900scale1, normal motion, software Mesa,
30s/60s/five processes and nearest-rank p95<=33.3ms remain unchanged. No timed frames
were collected and these proofs cannot establish a valid performance miss or D1 trigger.
Old v7 and all prior receipts retain their original source bindings.

Actual runtime: Ubuntu24.04.5 arm64, kernel6.8.0-142, WebKitGTK2.52.6,
Mesa25.2.8, LLVM20.1.2, native llvmpipe128bits. Both native receipts and live candidate
WebKit llvmpipe threads agree. The masked WebGL API still says Apple GPU, as required by
the existing exact-version source reconciliation. Both requested `on-demand` but reported
effective `ALWAYS`; the freeze's `compositing_policy` names the request, while hash-bound
preflight/motion records retain the effective value. This repeats the existing documented
limitation; changing the request to `always` cannot alone establish an optimization.

## Graphical launch attribution

Both sessions are active local campusqa UID1000, `Service=gdm-password`, seat0, tty2,
with boot ID `6fa7cd03-1b45-4aa7-9416-cab344b8639d`. Normal GDM gear-menu selection and
private password input used the existing QMP/VNC console; no autologin/auth configuration
was changed. The [Xorg menu selection](x11-session-selection.png),
[Wayland Run dialog](wayland-launch-ui.png), and [X11 renderer screen](x11-motion-screen.png)
supplement machine observations. Credentials remained in the private file and local
console input, never argv, output or screenshots during entry.

[Wayland preflight](wayland-2/preflight-launch.json),
[Wayland motion](wayland-2/motion-launch.json),
[X11 preflight](x11/preflight-launch.json) and [X11 motion](x11/motion-launch.json)
record timestamp, boot, real logind session/leader, UID, parent, raw stat/starttime/cgroup,
allowlisted display environment, display configuration and socket-peer identities.
The wrapper was launched by actual GNOME shell through Alt-F2, then spawned the unmodified
GPU/renderer processes. Command receipts bind each actual child PID/start/cgroup and exit.
No SSH-carried display environment launched these probes.

Precise limit: `sd_pid_get_session` returned -61/null for the user-manager application
scopes and GNOME shell; no session value is fabricated. Wayland's socket peer is the same
GNOME-shell PID2521 that directly parented the launch, in its Wayland service. X11's socket
peer is XorgPID4146 in `session-12.scope`, with actual sd_pid_get_session=12; GNOME parent
4321 is in its X11 service. The contemporaneous sole active graphical session, direct parent,
backend and peer observations provide attribution without pretending every user-manager
process belongs to a logind session scope. This is not a general cryptographic attestation.

## Reproduction and preserved failures

The [run plan](../../g8-run-plan.md) specifies external host verification and the manual
stop after preflight. Actual host paths/manifest/verifier hashes are in
[export provenance](export-provenance.json); the verifier's [stdout](export-verification.txt)
was captured before transfer. [Unchanged harness hashes](unchanged-harness-hashes.json)
bind the runtime and original protocol. The additive [graphical wrapper](graphical-probe.py)
records observations/commands and bounds children; it does not alter benchmark source.
The [first wrapper](graphical-probe-first.py) is retained at its executed hash.

Guest root was `/home/campusqa/spike982/g8-native-1240`, with `repo`, `desktop-first` and
fresh output labels `wayland`, `wayland-2`, `x11`. Through the actual GNOME Run dialog:

```text
python3 /home/campusqa/spike982/g8-native-1240/graphical-probe.py wayland preflight wayland-2
[operator inspected fresh receipts and wrote wayland-2/environment.json]
python3 /home/campusqa/spike982/g8-native-1240/graphical-probe.py wayland motion wayland-2
python3 /home/campusqa/spike982/g8-native-1240/graphical-probe.py x11 preflight x11
[operator inspected fresh receipts and wrote x11/environment.json]
python3 /home/campusqa/spike982/g8-native-1240/graphical-probe.py x11 motion x11
```

Each output folder preserves exact argv, stdout/stderr, launch/exit identity and UTCs.
The motion stage sequentially performs diagnosticfreeze → fresh motion → proof-boundfreeze.
Runtime's diagnostic bound remains180s; the wrapper's outer190s bound allows process
startup/exit overhead. No timeout fired. No run-five command was issued.

Preserved failures and corrections:

1. [Initial stopped receipt](host-stopped-before.json) mistakenly filtered `diffdisk` and
   `basedisk`, producing an empty disk list; the following boot proceeded. This was an
   operator accounting failure, also present in prior work and not an acceptable baseline.
   It was immediately stopped normally, before any renderer launch. [Corrected stopped
   baseline](host-stopped-corrected.json) measures actual `disk` before the fresh probe boot.
   The first aborted boot's allocation is unmeasured, not retroactively reconstructed.
2. [First Wayland preflight](wayland/preflight.json) refused viewport1214x731 on the initial
   1280x800 desktop. Its full native/launch/stdout/stderr/exit receipts remain. The
   [display command](display.py) used the existing session's Mutter temporary configuration
   API to select1920x1200scale1, allowing the unchanged Gtk request to produce1440x900.
   [Wayland](display-change-152905.json) and [X11](display-change-153357.json) before/after
   observations are retained. Configuration method1 was temporary, not a persistent
   GDM/auth setting. Graphical logout returned to the ordinary greeter.
3. Host `tar --no-xattrs` still inserted AppleDouble files. The first full inventory audit
   failed with FileNotFoundError for `desktop-first/._Island`; [original inventory](transferred-export.json)
   and [provenance](export-provenance.json) retain all extra paths/hashes and the failed
   equality conclusion. All13 original export files matched bytes/modes throughout;
   extras were outside the manifest and never served. After successful-proof cleanup,
   [cleanup](transfer-metadata-cleanup.json) removed only42 newly added163-byte AppleDouble
   files across this source/export transfer, checking owner/type/magic first. The final
   complete16-entry export inventory matches host bytes and modes. Future host transport
   should use `COPYFILE_DISABLE=1 tar --no-xattrs` to avoid these metadata additions.
   Cleanup changed no manifest-listed file or runtime source, and creates no new runtime proof.
   The failed-preflight process-absence observation was recorded132ms after metadata
   deletion; it does not establish that failed-preflight cleanup was observed beforehand.

No narrow benchmark-source repair was made. Expected strings and thresholds are unchanged.
The existing run plan's manual observation split, host variables/GPU assignment, index
provenance note and Electron desktop-export example were clarified as authorized.

## Cleanup, resource accounting and handoff

[Wayland](wayland-cleanup.json), [failed preflight](wayland-failed-preflight-cleanup.json)
and [X11](x11-cleanup.json) observations confirm all observed renderer/wrapper PIDs and
application scopes absent; no termination signal was needed. Both normal graphical logouts
completed before shutdown. The [login keyring Wayland](wayland-login-keyring-locked.txt)
and [X11](x11-login-keyring-locked.txt) queries each report Locked=true.
[Protected files snapshot](guest-before.json), [after](guest-after.json) and
[comparison](cleanup-verification.json) show identical hashes/UID/GID/modes for GDM config,
polkit rules/action, updater package/helper/verifier/admission/public-key files; coordinator
PhaseB hashes/owners/modes also match. No owned deny rule or polkit mask was introduced.
The first named snapshot is a15:29:49 mid-run observation, not a pre-probe baseline;
earlier protected state relies on coordinator PhaseB evidence. The comparison contains
24 rows covering16 unique protected paths, because eight rules occur twice.
Office377's evidence and processes were not operated on.

Lima was [stopped normally](shutdown.txt), confirmed [15:38:12UTC](host-stopped-after.json),
with no QEMU guest process. UTM was not operated. Corrected stopped disk allocation:
6,870,925,312 →6,890,979,328 bytes, growth20,054,016 bytes; sparse logical size is not the
budget. Final new guest files3,440,640 allocated bytes. Conservative aggregate consumption
169,119,744 of268,435,456 bytes includes retained G4/speech, positive whole-log growth
since the historical baseline and16MiB overhead reserve; remaining99,315,712 bytes.
Whole-log growth is conservative accounting, not attribution of other Offices' writes.
Guest free20,223,381,504 bytes; stopped host free21,560,815,616 bytes, above20GiB.
These are sampled floor observations, not a continuous guarantee; the between-session
host sample records26,928,074,752 free bytes.
The corrected interval includes boot/shutdown disk growth. No old evidence or unrelated
cache was deleted. This is operational accounting, not a filesystem quota.

Host contention remained substantial: [between-session samples](host-between-sessions.json)
show74.66% and76.55% CPU busy. No performance inference or quiet timing window follows.
The64MiB source/export/receipt slice was respected; host return receipts and guest new files
are each under4MiB before final documentation, with actual worktree/temp accounting retained
in the delivery verification. No model/provider account, paid call, release upload, new
runtime or privileged app/update/auth operation occurred.

Explicit human handoff to LINUX-20261016, the active coordinator who issued1240: review
this returned evidence and exact published head, own hosted architecture/admission and
Council, then separately schedule timing when observed shared-host contention permits.
These freezes bind this actual boot/session/source; a later boot/session must reobserve
its conditions and satisfy the run plan rather than relabel these captures. No worker
CI/Council watcher or automatic wakeup is assumed. Full G8, G4/provider, speech/product,
installed-package and downstream acceptance gates remain open; do not mark #982 done.

## Delivery verification

`PATH=/Users/yuri/.pyenv/versions/3.11.15/bin:$PATH python3 -B scripts/verify_repository.py`
passes51 tests, D7, links, legacy132-path parsing and the expanded evidence inventories.
[Independent delivery checks](delivery-verification.json) verify actual session/source/native/
environment/command ordering, wrapper hashes, all469 pre-existing receipt files unchanged
outside the inventory, and the changed-file actual-token/private-key scan. All new screenshots
were inspected. The full returned diff and repository-owned path inventory were reviewed.
The final committed head is rechecked before the single normal push; its SHA and observed
results are recorded on card982 and draftPR12. No local architecture wrapper is retried:
the current no-build direction and35GiB guard leave hosted architecture/admission to root.

The complete worktree allocated22,069,248 bytes and this run's host temporary directory
3,100,672 bytes at delivery verification; guest new files3,440,640 bytes. Even conservatively
counting the entire worktree/temp trees and the20,054,016-byte corrected disk growth together
stays below64MiB. These overlapping quantities are reported separately, not attributed from
global free-space loss. After shutdown, shared-host available space fell below20GiB
(20,625,027,072 bytes at15:42:44UTC). No further guest operation occurred; only review and
publication of already collected evidence continued. The earlier aborted accounting boot
remains outside the measured disk interval and is not concealed by this arithmetic.

Latest human comment10676 separately permits completing this existing source/docs/evidence
publication and focused Python checks under128MiB source budget and18GiB host floor.
The fresh publication free/allocation observation is recorded in the delivery verification;
root independently verified Lima Stopped. This does not authorize another guest boot or
timing run, and does not retroactively change the completed probe accounting.
