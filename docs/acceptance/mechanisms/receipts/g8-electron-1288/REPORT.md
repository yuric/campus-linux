# Direction1288: Electron sandbox prerequisite blocked

LINUX-20261016 / #982. **No Electron native preflight, motion proof, freeze or timing
result was produced. No X11 run occurred. G8 remains unaccepted.** The sole normal
Wayland launch aborted on the vendor sandbox prerequisite. No setup workaround or retry
followed. Lima returned Stopped at17:31:22UTC; UTM was not operated.

The [directions](directions.json) authorize one bounded official archive/extraction after
the prior valid WebKit misses143/187/142/140/174ms and unsupported DMABUF option. They
preserve the original scene,33.3ms/all-five bar and normal sandbox. This outcome neither
invalidates those earlier measurements nor selects a product shell. Later10832, superseded by10834, authorizes
only the [unexecuted installer/rollback source proposal](../../electron-sandbox-proposal.md).

## Provenance and acquisition

Starting draft PR12 head82e88e10b9d38dd56bc4ef3d75d1ed823bb02ccf descends from
merged Linux PR11 [37ef5d6](base-merge.json). All [23 renderer source hashes](source-hashes.json)
match accepted9d7743a byte-for-byte; no benchmark source edit occurred. The existing merged
Mac PR114 [3e3d4bcd](producer-merge.json) export passes its [external verifier](export-verification.txt),
manifest7b5fabefd830d3cd3d3577da1c4cb4ba55217de0f7eb5b5bbfc9501443428f09.
The guest reuses that existing export and existing1268 source tree; no build or dependency
installation occurred. The [guest check](guest-raw/export-verification.json) verifies the11
manifest-listed assets. It is not a new complete mode inventory; the prior accepted complete
export inventory retains that provenance. Producer contract source remains server
d93b841762183af5ba0d357f3f1c42351aeed9ff, not a current Linux API import.

[Stopped baseline](stopped-before.json) at17:23:17 exactly matches root's handed-off disk:
7,424,835,584 allocated bytes, inode944391844. Host32,925,061,120 free minus the full
805,306,368-byte allowance leaves32,119,754,752, above20GiB. The separate immediate
[preboot host sample](host-before-boot.json) records32,296,202,240 free. Guest free was
first freshly observable after boot; [pre-acquisition inventory](protected-before.json)
records19,890,663,424 bytes. No offline guest filesystem was mounted to invent a preboot
free-space observation. Root's prior stopped custody plus fresh postboot checks are distinct.

The [download command](guest-raw/acquisition-command.json) ran once directly inside the
private guest scratch directory,17:24:37–17:24:48. `curl` had the exact124,393,671-byte cap
and180s deadline. Unchanged reviewed `prepare.py` accepted the exact archive SHA256
`502296281cab3c333bd5193e2eaed11c3bb28eabd7a451a49776a3e5a9468f8c`, archive size and
302,048,805 extracted payload bytes; [command](guest-raw/prepare-command.json),
[stdout](guest-raw/prepare.stdout), [full extracted hash inventory](spike-extraction.json).
Executable SHA256 is730d44d5aefb6a969b209cf8ee3e843bd873a06c297bf2c409fbb1cebcb3e6bc.
Both Electron/Chromium license files remain present. This is pinned vendor-download
integrity, not independent release-key or Campus updater verification. No host payload copy
was made; the one archive/extraction remains inside the stopped guest.

## Actual graphical attempt

Private password entry used the existing no-follow0600 input channel and local QMP, after
viewing the [empty password field](password-field.png). No secret value is in argv or receipts.
Fresh [session7](session-before.json.txt) is UID1000, seat0/tty2, `gdm-password`, Wayland,
not autologin. Bootd4cb2166-533b-4911-9ee8-96398f32773e runs kernel6.8.0-147-generic;
observed Mesa25.2.8, LLVM20.1.2, GNOME46 and installed package versions are in
[runtime custody](runtime-custody-before.json). APT jobs were inactive. The observed
usernamespace/AppArmor sysctl values are read-only observations, not causal proof or edits.

Root10821 reviewed the exact [operator wrapper](graphical-probe.py),
[inhibitor](idle-holder.py) and [expanded inventory](protected-snapshot.py). Their hashes
are retained in [transfer](operator-transfer.json) and runtime receipts. The wrapper changes
only orchestration to the accepted Electron commands; accepted23 source files are untouched.
The existing session-only display helper selected1920×1200 to permit the fixed1440×900
content viewport, but Electron never reached viewport validation.

The [inhibitor start](guest-raw/wayland-electron/inhibitor-start.json) records actual
GNOME-parented PID2999/start32132, connection`:1.80`, empty before-list and one owned
flags8 inhibitor. Original idle-delay300 and lock-enabledtrue remain unchanged. It has
1170s normal/1200s absolute bounds. User-manager `sd_pid_get_session=-61/null` is retained;
active logind context is not relabeled as a direct PID session mapping.

The [actual Run-dialog command](gui-launches.jsonl), [UI capture](preflight-launch-ui.png),
and [launch observation](guest-raw/wayland-electron/preflight-launch.json) bind the wrapper's
GNOME parent, actual session leader and display socket peers. `LIBGL_ALWAYS_SOFTWARE=1`
was set and recorded by that wrapper and inherited by its child. There is no separate
post-exec child-environment capture. The exact [child command](guest-raw/wayland-electron/preflight-command.json) was:

```text
/home/campusqa/spike982/g8-electron-1288/electron/electron
/home/campusqa/spike982/g8-timing-1268/repo/spikes/982/renderer/electron/main.cjs
--preflight
/home/campusqa/spike982/g8-timing-1268/desktop-first
ignored
/home/campusqa/spike982/g8-electron-1288/wayland-electron/preflight.json
```

Child3054/start35385 exited with returncode-5 (signal5),17:29:32.051–17:29:32.167.
[Original stderr](guest-raw/wayland-electron/preflight.stderr) is retained byte-exact:

```text
[3054:1016/102932.092554:FATAL:sandbox/linux/suid/client/setuid_sandbox_host.cc:166] The SUID sandbox helper binary was found, but is not configured correctly. Rather than run without sandboxing I'm aborting now. You need to make sure that /home/campusqa/spike982/g8-electron-1288/electron/chrome-sandbox is owned by root and has mode 4755.
```

The [custody record](runtime-custody-before.json) observes that helper as UID1000/GID1001,
0755,17,048 bytes, SHA243acfa0e6bab02b34580c2f426704dcd256c4072f494192c02b2256ea7740bb.
No preflight JSON, complete native GPU data, descendant llvmpipe threads, JavaScript
`process.versions`, mounted scene or motion was observed.44.8.0 is the verified artifact
identity, not an emitted JavaScript runtime-version receipt. The fatal prerequisite does
not establish performance, correctness, software rendering or successful sandbox operation.
No `--no-sandbox`, GPU sandbox disable, SwiftShader substitution or policy workaround ran.

## Cleanup, resources and limits

The [release](guest-raw/wayland-electron/inhibitor-release.json) explicitly uninhibits
after54.8707 seconds; after-list empty. Original [keyring](keyring-locked-after.txt) stays
locked. All observed PIDs2999/3036/3054 are absent and both observed application scopes
2999/3036 are absent. The first [cleanup assertion](cleanup-observation.json) incorrectly
included the shared GNOME parent and failed. The additive [attribution](cleanup-attribution.json)
uses the exact launch parent equality to distinguish that shared cgroup, which was never
signaled. No candidate Electron/sandbox/collector process remained in that scan. Only
metadata of an unrelated pre-existing netplan crash was observed; it was not read or deleted.
Absence is scoped to captured identities and the named process scan, not an exhaustive
historical descendant proof for the116ms process.

All62 protected entries compare exactly equal before acquisition, after preflight and after
normal graphical logout, including bytes/modes/owners/inodes/directory membership:
[preflight comparison](protected-comparison-preflight.json),
[after-logout comparison](protected-comparison-after-logout.json). This includes the newly
staged1057-1285-60dc337b root/helper/user driver paths and keyrings. It is equality over
the observed postboot baseline, not an unobserved whole-boot inventory claim. No updater,
polkit, GDM, keyring, authentication or security-service operation was performed.
[Logout sessions](sessions-after-logout.txt) show greeterc2 and no campusqa session;
[shutdown](shutdown.txt) completed normally. [Stopped readback](stopped-after.json) at
17:31:22 records7,857,307,648 allocated bytes, +432,472,064; host27,135,004,672 free.
Final after-logout guest free19,454,935,040 bytes. No guest access occurred afterward.

Host contention was real: [before preflight](host-before-preflight.json) load18.53/14.53/13.71
and second-sample49.29%idle; [after](host-after-preflight.json)16.96/14.81/13.86 and58.31%idle.
Raw memory, cumulative swap counters and swap usage are retained. This short startup
failure is not a frame benchmark or an uncontended performance estimate. Host free-space
changes are not attributed to this worker. [Preflight accounting](preflight-budget.json)
charges432,406,528 disk growth plus32,518,144 allocated host scopes plus16MiB reserve:
481,701,888 new/1,194,004,480 cumulative bytes, below768MiB/2GiB. Guest files are inside
disk growth and are not added again. [Final accounting](final-allocation.json) includes
the preserved lease highwater and subsequent bounded source allowance. The original
publication floor check failed; direction1318 later grants only the separate8MiB source
exception at16GiB hostfree. No runtime floor is lowered. Floors were sampled, not continuously enforced.

Operational observation failures remain explicit: the task `/activity` suffix returned404
before the correct `/log` route; an initial unprivileged receipt read returned permission
denied and a root read succeeded; UTM CLI said not found and two read-only AppleScript
queries timed out. Root10821 accepted its17:19 nativeStopped handoff and forbade more
retries; none followed. A preboot process-name scan found no QEMU VM process. No UTM
guest operation occurred, and no fresh successful native status is fabricated.

Historical1268 raw bytes remain unchanged. Required10810 prose corrections now distinguish
observed scopes from unresampled3784/3954/4069 and use the actual17:06:17 after-logout
guest-free sample. The rejected10832 move/chown proposal and its four historical validator results are
retained as unactivated history. The replacement10834 fresh-inode proposal has separate
source validation; neither grants installed sandbox or runtime acceptance. Explicit next owner is active human
LINUX-20261016 for independent source/evidence review, future lease and CI/Council/merge.
No worker watcher, automatic wakeup, ready/merge/auto-merge/done or dependency release.
