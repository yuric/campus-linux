# G8 timing attempt — directions1268 and10757

LINUX-20261016 / card #982 / Office400. Accepted runtime source remains
`9d7743a25f4ce15c5fbad4932d3a7c37d9a29617`; no renderer, harness, fixture, scale or
threshold change. This report preserves the failed initial resource window separately
from the coordinator's subsequently authorized continuation. No product/L0 acceptance follows.

## Original allocation failure

The [stopped baseline](host-stopped-before.json) measured the actual Lima `disk` at
6,905,659,392 allocated bytes, inode944391844, before the16:27:03 boot. Host free
26,930,417,664bytes, sampled70.52–73.50%CPU idle and zero sampled swap activity met
human10740's observed-window conditions. The original remaining aggregate allowance was
99,315,712bytes; the64MiB source/export/receipt slice was separate from that disk limit.

Normal private GDM selection/login produced Wayland/session6, boot
`a8d1a18d-ab22-4e8a-8c62-d54b24ec9e9f`. [Native GPU](wayland-base/gpu.json) and
[preflight](wayland-base/preflight.json) succeeded with1440×900scale1,12projects/48agents/
180tasks, normal motion and Mesa llvmpipe. Requested compositing was`on-demand`, effective
policy`ALWAYS`. No diagnostic freeze, motion proof or timing was launched in this boot.
The [later host transcription](wayland-base/environment-observed-after-stop.json) is
explicitly not a premeasurement environment/freeze.

[Graphical launch](wayland-base/preflight-launch.json) records the GNOME-shell parent17956,
matching Wayland socket peer, actual GDM leader7155 and UID1000. The wrapper20889 and its
children were launched through the actual [GNOME Run dialog](wayland-launch-ui.png).
User-manager `sd_pid_get_session=-61/null` remains an attribution limit; logind/session,
parent and display-peer observations are retained without fabricating session ownership.

At16:29:57 the [running disk observation](running-disk-budget.json) found490,340,352bytes
of growth. The worker stopped new probes immediately, exported the small existing receipts,
verified process absence/locked keyring/protected paths, and requested normal shutdown.
The [shutdown](shutdown.txt) completed16:30:22; [stopped readback](host-stopped-after.json)
at16:30:49 records7,388,856,320bytes, a483,196,928-byte increase. Prior aggregate169,119,744
plus this disk increase equals652,316,672bytes, exceeding268,435,456. This is an observed
budget failure, not retrospectively waived by the later allowance. New owned guest files
were only1,556,480bytes; whole-disk growth cannot be attributed from that number or from
global host free-space loss. Host free23,800,487,936bytes and guest19,911,753,728bytes
remained above their respective20GiB/2GiB floors in the final samples.

## Protected-state chronology and cleanup

The [initial postboot snapshot](guest-before.json),16:27:34, and [expanded snapshot](protected-before.json),
16:27:51, differ: `/usr/share/polkit-1/rules.d/systemd-networkd.rules` inode39046 became93103.
Bytes527, SHA256, owner/group and mode remained identical. The [explicit comparison](initial-protected-changes.json)
retains this fact. The expanded25-path/directory snapshot equals the [after snapshot](protected-after.json),
but **whole-boot protected inode equality is false**. [Comparison with updater333](cleanup-verification.json)
also identifies seven coordinator staging/driver/logger paths not resampled in this first
attempt. No full-baseline claim is made from that partial coverage.

[Cleanup](wayland-cleanup.json) confirms all five observed probe PIDs and their one application
scope absent before shutdown, with no signals needed. The [login keyring](keyring-locked.txt)
was Locked=true. Protected updater app/helper/verifier/trust bytes and modes matched; no
owned deny rule or polkit mask appeared. The [transfer inventory](transfer-inventory.json)
records active GDM/polkit and the PolicyKit bus owner before probing; no after-service
identity observation was collected in this first attempt. Shutdown used normal guest poweroff
without a separately observed graphical logout. UTM and other Offices were not operated.

## Verified source and preserved operator failures

Merged Linux base PR11 is`37ef5d622da09cd7ba113dc0d1119e62e7378f84`; [live record](base-merge.json).
Mac PR114 merged at`3e3d4bcd64fd1504c4546b2f7a063b55e2eea783`; [record](producer-merge.json)
and [main ancestry](producer-ancestry.json). Existing desktop export passed the merged
producer verifier with external manifest`7b5fabefd830d3cd3d3577da1c4cb4ba55217de0f7eb5b5bbfc9501443428f09`;
[stdout](export-verification.txt). Producer contract provenance remains campus-server
`d93b841762183af5ba0d357f3f1c42351aeed9ff`; no API import/compatibility claim.

`COPYFILE_DISABLE=1 tar --no-xattrs` transferred the existing source/export with original
modes and no AppleDouble extras. [Verification](transfer-verification.json) checks all source
files and the complete export inventory against host bytes/modes. The first ad hoc audit
incorrectly compared the new guest`repo` container directory's mode with the unrelated host
workspace root and failed; the corrected scoped comparison passed without changing any
transferred byte. [Source hashes](source-hashes.json) bind the unchanged accepted inputs.
The graphical, snapshot and cleanup scripts here are additive observation wrappers.

Other retained operator failures: one QMP `alt-f2` keycode was rejected before input;
`alt+f2` is the correct existing helper syntax. Initial receipt reads without guest sudo
were refused by file permissions; authorized read-only sudo export succeeded. Neither
failure changed the workload or was hidden as a successful command.

## Revised lease and actual package activity

Human10757 authorized a new1GiB total increment from a fresh stopped baseline and2GiB
cumulative accounting, while preserving the first budget failure. [Baseline](resume-stopped-before.json)
at16:34:24 is7,388,856,320 allocated bytes; prior aggregate652,316,672. Host20GiB/guest2GiB
floors remain. Disk growth and new host-owned receipts must be combined without counting
guest files twice inside the disk increase. No install/build/download/cache cleanup was
commanded by this worker.

The [bounded package audit](package-audit-after-resume.json) and [detail](package-audit-detail.json)
identify unattended-upgrade activity during the first boot,09:27:17–09:29:17MST. It upgraded
systemd255.4-1ubuntu8.17→8.18 and installed kernel6.8.0-147; the resumed boot actually runs
that kernel. Dpkg identifies systemd as owner of the replaced networkd rule. This supports
background package activity as the source of the early replacement/allocation, without
attributing every allocated byte: no pre-event per-directory size inventory exists.

After the resumed boot, apt-daily/apt-daily-upgrade were inactive. The sole matching
process was `unattended-upgrade-shutdown --wait-for-signal`, not a package mutation worker.
WebKit2.52.6, Mesa25.2.8, LLVM20.1.2 and GNOME/Mutter/GDM versions remained unchanged.
The protocol requires observed exact kernel versions per receipt; it does not fix142.
No expected-version string was changed to admit147. [Full fresh protected baseline](full-protected-resume-before.json)
adds all previously omitted updater staging/driver/logger paths,32 distinct entries total.

## Preserved idle-lock interruption

Fresh Wayland/session7 in boot`ee95b746-c664-4b55-b133-a94764726e74` completed native/preflight,
manual environment observation, diagnostic freeze, fresh untimed proof and proof-bound
freeze. The [external record](wayland-r2-base/external-freeze-record.json) precedes timing.
The proof has1352inputs,7checkpoints,0performance frames and passes the unchanged checker.
Its resulting original five-process run stopped on run3's focus loss; run4/5 never ran.

| Preserved run | Valid workload | p95 ms | Outcome |
| --- | --- | --- | --- |
|1|yes|179|slow; retained|
|2|yes|127|slow; retained|
|3|no|128|focus loss; excluded from performance acceptance|

[Raw files](wayland-r2-base/five/run-1.json), [run2](wayland-r2-base/five/run-2.json),
[run3](wayland-r2-base/five/run-3.json), [aborted summary](wayland-r2-base/aborted-summary.json),
and [wrapper exit1](wayland-r2-base/five-command.json) are unchanged. At16:45:05 logind
reported IdleHint=yes/LockedHint=yes; [display capture](wayland-idle-lock.png) shows the
inactive display. Existing [idle-delay](wayland-idle-delay.txt) was300seconds and
[lock-enabled](wayland-lock-enabled.txt) true. No OS keepalive or persistent setting was
changed. This incomplete series establishes neither an all-five baseline result nor a D1
fallback trigger. Normal private unlock followed, with no password value in output/argv.

[Cleanup](wayland-base-aborted-cleanup.json) confirms22 observed PIDs and3 application scopes
absent, not the mistaken five-scopes shorthand in task10770. Actual wrapper completion was
16:45:01.134UTC; the earlier task narrative16:44:58 was approximate. Before/after host
load/memory/swap/free-space captures remain separate. Root10768 then held timing for a
bounded other-office server test;10778 issued GO after that work and cleanup completed.

Human10774 specifically authorized a transient GNOME session inhibitor, superseding10773's
unused idle-delay setting option. The installed API was introspected, and official
[GNOME documentation](https://gnome.pages.gitlab.gnome.org/gnome-session/re04.html) defines
flag8 as idle-only and release by Uninhibit/disconnection. Each subsequent candidate uses
one actual graphical holder connection, normal deadline1170seconds and1200second absolute
bound, with before/during/after list and PID/start/session receipts. Logout, switching,
suspend and automount are not inhibited. Both persistent settings remain unchanged.

## Fresh inhibited timing sequences

`idle-holder.py` is an additive environment observer/holder, not a renderer modification.
The final Wayland baseline holder3762/start99735 was launched by GNOME-shell2471 in
actual GDM session7. Its sole connection`:1.103` held flag8; the frozen environment binds
the exact holder-start receipt and source hash. The fresh untimed proof contains1360inputs,
7checkpoints and zero performance frames. Its external proof/freeze digest observation at
16:53:56 preceded the actual graphical timing launch. The old interrupted series contributes
no run to this sequence.

WebKit's JavaScript WebGL strings report Apple GPU/Apple Inc.; these are retained verbatim
as API observations. The independently captured native EGL/GL receipt identifies Mesa
llvmpipe, LLVM20.1.2, with the loaded native evidence and actual display type. The API string
is not substituted for native renderer evidence.

### Complete Wayland baseline

The unchanged runner completed16:54:06.795–17:02:38.409UTC. Task10793's17:02:42
was approximate; the [command receipt](wayland-final-base/five-command.json) is exact.
[Original summary](wayland-final-base/five/summary.json) and
[external verification](wayland-final-base/external-series-verification.json) agree:

| Fresh process | Valid | Frames | p95 ms | Maximum interval ms | Fixed gate |
| --- | --- | --- | --- | --- | --- |
|1|yes|445|143|433|miss|
|2|yes|433|187|357|miss|
|3|yes|455|142|159|miss|
|4|yes|456|140|213|miss|
|5|yes|422|174|227|miss|

Every raw measurement and log is retained under `wayland-final-base/five/`. Each trace
passes the original full30s warmup/60s measurement input/gesture validator with empty
errors/invalid arrays. No frames, stalls or runs were pooled or dropped. Requested
`on-demand` is effective`ALWAYS`; this is a valid slow result in the observed shared-host
window, not a controlled estimate of uncontended machine performance.

[Before-series host](host-wayland-final-base-before-series.json),16:53:56, records
load21.38/18.45/15.73 then20.63/18.35/15.71,52.72–53.88%CPU idle,92Gused/3503–3561Munused,
25,548,312,576bytes free. [After-series](host-wayland-final-base-after-series.json),17:02:46,
records load54.88/38.68/26.68 then52.56/38.47/26.68,22.56–22.70%idle,
94Gused/1464–1651Munused,24,706,244,608bytes free. Both short samples show zero swap
activity, but cumulative swapins rose28 between captures; swap usage stayed3535.44M.
These snapshots show increased contention and do not establish zero swap throughout the
series. No numeric contention cutoff was invented or slow result discarded. The guest
remained above2GiB and host above20GiB in retained samples.

### Coordinator-selected distinct candidate failed admission

Human10789/10795 superseded an unchanged `always` repeat and paused X11 before the D1
assessment. The sole distinct candidate used requested`always` plus
`WEBKIT_DISABLE_DMABUF_RENDERER=1`. The existing accepted renderer source was unchanged.
The [tagged WebKit source](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.6/Source/WebKit/UIProcess/gtk/AcceleratedBackingStore.cpp)
disables transport eligibility before adding shared memory; this is not a proven DMA-BUF
to shared-memory optimization. The [upstream issue](https://bugs.webkit.org/show_bug.cgi?id=324549)
also reports a WebGL presentation hazard with this option. No performance benefit is assumed.

Fresh holder4713/start175730 held the sole idle-only connection. The
[actual graphical invocation](gui-launches.jsonl) prefixes `env WEBKIT_DISABLE_DMABUF_RENDERER=1`
for the complete wrapper, so both native capture and subsequent preflight inherit it.
The [native GPU body](wayland-final-always/gpu.json) reports policy`never` and omits
`Hardware Acceleration Information (Render Process)`. The unchanged native validator
raised `StopIteration`; [stderr](wayland-final-always/preflight.stderr) and
[command](wayland-final-always/preflight-command.json) record exit1 at17:04:22.023UTC.
There is no preflight JSON/rendering_env, scene admission, motion, freeze or timing for this
candidate. No actual environment object was fabricated after process exit; the launch
command/inheritance and raw native result are the available evidence. No candidate host
before-timing sample exists because it never reached timing; the preceding baseline-after
and [candidate-after-preflight](host-wayland-final-always-after-preflight.json) are retained.
This candidate is **invalid/unsupported**, not a numeric performance miss.

The first GUI typing attempt rejected`=` before pressing Return. Escape cancelled it; a
new disposable [typing helper](qmp-type-env.py) adds QMP`equal`, preserving the old helper
and all renderer source. A premature host read of nonexistent preflight JSON failed; this
was inspection failure, not a successful preflight. No fallback weakening or rerun followed.

### Final cleanup and handoff

The baseline [release](wayland-final-base/inhibitor-release.json) at17:02:49 shows an empty
inhibitor list after706seconds. The candidate [release](wayland-final-always/inhibitor-release.json)
at17:04:49 shows an empty list after66seconds. Both are below the1200second bound.
[Settings](idle-delay-after.txt) remain300, [locking](lock-enabled-after.txt) true and
[keyring](keyring-resume-locked.txt) Locked=true; [final inhibitor list](inhibitors-after.txt) empty.

The first [baseline cleanup observer](wayland-final-base/process-cleanup.json) failed because
it incorrectly treated the inherited shared GNOME Shell cgroup as an owned application
scope. All28 captured probe PIDs were already absent. The additive
[attribution-aware observer](cleanup-attribution.py) retains each parent/cgroup relationship:
[baseline](wayland-final-base/cleanup-attribution.json) confirms29 PIDs including holder absent;
[candidate](wayland-final-always/cleanup-attribution.json) confirms4 including holder absent.
Observed application scopes are absent and the scoped renderer/old updater driver scan is empty.
The baseline command scopes `app-gnome-python3-3784`, `app-gnome-python3-3954` and
`app-gnome-python3-4069` were not individually resampled by that collector. All29 observed
PIDs were absent and later Stopped is verified; those facts do not establish individual
scope readback. The original raw collector output is preserved.
The shared GNOME cgroup was never stopped. User-manager session attribution remains limited.
An initial final-snapshot command referenced a guest file that had only been run over stdin;
it failed before observation. The subsequent exact host script over stdin succeeded.

All32 fresh protected entries compare equal before/after and again after graphical logout,
including file bytes, modes, owners, inodes and directory entries:
[comparison](protected-resume-comparison.json), [after logout](full-protected-after-logout.json).
This resumed-boot equality does not erase the first boot's early inode change.
[Services](services-after.json) retain active GDM/polkit, the PolicyKit bus identity, inactive
APT jobs and unchanged measured WebKit/Mesa/GNOME packages. Normal graphical logout is
observed in [sessions](sessions-after-logout.txt) and [greeter](greeter-after-logout.png).
[Shutdown](resume-shutdown.txt) and [stopped readback](resume-stopped-after.json),17:06:46,
record actual disk7,405,699,072bytes, inode944391844, revised-baseline growth16,842,752bytes.
Host free25,448,300,544bytes; final guest sample at17:06:17 after logout was19,910,283,264bytes.
The earlier19,910,086,656byte sample was at17:05:32 before logout. UTM, other Offices,
shared caches, release keys and updater protected content were not operated.

X11 timing was **not run**, per the newer coordinator boundary; historical X11 functional
proofs do not establish current timing acceptance. Electron was neither acquired nor
launched. The D1 fallback need is the existing pinned Electron44.8.0 arm64 archive plus
extraction,426,442,476 logical bytes (124,393,671 archive +302,048,805 extracted),
not a fresh allocated-block measurement, before separately bounded filesystem/evidence/disk overhead; the
[pinned source inventory](../../../../../spikes/982/renderer/electron/source.json) remains the request,
not permission or acceptance. Root LINUX-20261016 owns the D1 decision, next runtime lease,
independent review and exact-head CI/Council. G8 and overall #982 remain unaccepted.

[Final allocation accounting](final-allocation.json) conservatively charges26,365,952 actual
allocated host bytes across owned receipt/source/task-readback scopes, including historical
same-card temporary files, plus16,842,752 stopped-disk growth and16,777,216 explicit publication/
receipt reserve:59,985,920 new charged bytes and712,302,592 cumulative. These are below the
revised1GiB/2GiB limits. The reserve is not represented as measured allocation. Guest files
are not double-counted outside the disk increase. The first allowance failure remains intact.
The raw snapshot `remaining_bytes` field is a superseded guest-internal accounting metric;
the revised whole-disk plus host-growth allowance above governs this lease.
Root10798 independently verified Stopped and took back the guest lease at17:07:36; this worker
performed no guest access after that handoff. Remaining work in this submission is source-only.

[Self-review](self-review.json) rechecks all23 accepted renderer files unchanged, every exported
guest raw byte against its captured original, the fresh motion/freezer linkage and all five
valid slow traces. Repository policy checks establish evidence delivery integrity only.

Staged repository verification passed51 tests, links, legacy132-path parsing, D7 and862
indexed evidence entries. The exact committed head is checked again before publication;
results are recorded on the card/PR. `git diff --check` reports one extra blank line at EOF
in original `wayland-final-base/five.stdout`; it is intentionally retained as raw stdout.
Known credential/private-key scanning of211 staged files passed, and password-field images
were inspected blank. No Docker build or architecture acceptance was run under this lease.
