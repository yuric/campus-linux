# Arm64 GDM lease handoff — #1057

Prepared source only. No desktop case has run. LINUX-20261016 owns the explicit
download/VM lease after Office400's stopped/cleanup handoff, private existing guest
authentication, independent review, CI/Council and merge. The worker must not start
Lima, access the guest or retrieve package archives before that lease.

## Exact inputs and bounded allocation

Use successful native source `113a53e4eea44b6d80a8ee3edb55d186d11f3ba6`,
[run 38913791148](https://github.com/yuric/campus-linux/actions/runs/38913791148).
Keep its disposable key/schema/packages together; another run generates another key.

| Arm64 artifact | GitHub artifact ID | ZIP bytes | ZIP SHA-256 |
|---|---:|---:|---|
| Packages/public bootstrap | 12051463614 | 257745483 | `6a7fe78c15105644067cf373e417949f0bb45138972bc9bf9396ba390164f419` |
| Source receipts | 12051777955 | 128142 | `df4efdf7f4dc79f8ccc6869b94ab1cb79c678cbacc02eb943203a5c54fdbf878` |

The archives total **257,873,625 bytes**. If downloaded through the Mac, reserve at
most **260 MiB** for these two ZIPs and transfer overhead; do not extract there.
The coordinator must explicitly allocate this download and any guest disk growth.
Prefer a direct approved guest download when its existing authentication supports it.
No new VM, dependency install, build, registry or signing key is needed.

Before extracting, verify both SHA-256s, reject ZIP traversal, absolute names, links
and duplicate members, and require all members to be ordinary files/directories under
`packages/`, `bootstrap/`, `receipts/` or `locks/`. Check central-directory expanded sizes
before any write: package ZIP at most **300 MiB**, receipt ZIP at most **4 MiB**.
Extract both into one newly created, private, lease-specific guest directory. Verify
every package against `receipts/package-index.json` and the installed trust inputs
against the recorded provisioning hashes in `receipts/installed-smoke.json`. Verify
`bootstrap.py` itself against the source113a53e file hash in `fixture-inputs.json`.
No package is executed until coordinator verification of these exact bytes.

| Guest allocation component | Upper bound |
|---|---:|
| Both retained ZIPs | 257873625 bytes |
| Expanded public bundle and source receipts | 304 MiB |
| Working AppImage plus two temporary/replacement copies | 242966040 bytes |
| Caller and root-staged deb copies | 9412104 bytes |
| Old/new installed deb payload allowance | 30175088 bytes |
| Separately provisioned public trust/verifier | 64 MiB |
| Desktop receipts/screenshots | 64 MiB |
| Filesystem/package-manager overhead reserve | 128 MiB |

Total reservation: **1.25 GiB additional guest disk**; stop before exceeding it.
The measured six package files total 257,074,004 bytes. Largest AppImage is
80,988,680 bytes; largest admitted deb is 4,706,052 bytes; largest expanded deb
data is 15,087,544 bytes. Do not extract AppImages in the guest: use hosted payload
hash receipts and the genuine FUSE runtime. Existing GDM/system packages must already
be available; a missing dependency is a coordinator resource decision, not permission
to install or change Office400's environment. Limit diagnostic commands to one active
fixture process, a loopback server and the bounded authority window.

## Preflight and initial provisioning

Record the lease reference, approved directories and byte budget, actual Ubuntu/arm64
identity, active local GDM session, user/UID, session leader, Wayland/X11 display,
runtime directory and relevant polkit/D-Bus/GTK versions. Preserve existing session
and service state. Reject a pre-existing `campus-updater-1057` package, trust directory
or fixture polkit rule rather than overwriting it. No headless allow rule may be present.

Use only the coordinator's existing private guest authentication for root provisioning.
Do not collect an administrator password, put it in arguments/logs, use `sudo -S`,
terminal sudo, or build an alternate escalation path. In that already-authorized root
context, run the reviewed `bootstrap/bootstrap.py --bundle ABSOLUTE_BUNDLE_PATH`,
then install the exact v1 deb as initial provisioning. Initial `dpkg --install` is
separate from the updater; every update invokes the real fixed pkexec adapter.

Launch `serve.py` as the actual GDM user with the final package index, `--version 2`,
`--port 17857` and a lease-specific request log. Launch the desktop recorder from the
actual graphical session. It records the recorder/app PIDs and logind/process/display
evidence. A user-manager process may have no direct logind session association; the
recorder must retain that limitation for coordinator review, never relabel an SSH
process with an inherited `XDG_SESSION_ID` and call it a graphical binding.

Recorder command shape (substitute actual lease, observer and approved paths):

```sh
python3 -B spikes/1057/installed-updater/probe/desktop.py \
  --case cancel --lease-reference 'COORDINATOR_LEASE_REFERENCE' \
  --authority-reference 'ordinary restored polkit; no temporary fixture rule' \
  --source-head 113a53e4eea44b6d80a8ee3edb55d186d11f3ba6 \
  --index /approved/output/receipts/package-index.json \
  --inventory /approved/output/receipts/payload-inventory.json \
  --observer 'ACTUAL_OBSERVER' --observation 'ACTUAL_GUI_OUTCOME' \
  --receipt /approved/evidence/cancel.json \
  --screenshot /approved/evidence/cancel.png --timeout 40
```

Use `deny`, `missing-authority` or `prompt` for the other cases. The prompt/cancel
screenshot must be captured during the invocation, before any password is entered.
For deny/missing-authority, supply the actual bounded-window receipt reference.

From the already-authorized independent root context, with an existing root-owned
`0700` receipt directory, prepare a window using the actual GDM UID:

```sh
python3 -B spikes/1057/installed-updater/probe/authority-window.py deny \
  --lease COORDINATOR_LEASE_ID --uid ACTUAL_GDM_UID --duration-seconds 45 \
  --receipt /approved/root-private/deny-window.json
```

For the missing-authority case use positional mode `missing` and add
`--allow-shared-authority-window` only when that window is in the actual lease.
The helper prints readiness; the root operator then starts the pre-staged GDM
recorder promptly. Up to ten seconds of the requested 15–45 second duration is
reserved for restoration, so use `--timeout 20` for the refusal recorder. For denial,
also require the matching `campus1057-deny-loaded` and actual `campus1057-deny` journal
markers: rule-file creation is not proof of denial. Preserve journal lines only for
this lease's marker and subject PID, not an unrelated session log dump.

Elapsed overruns or failed restoration remain failures even if the command eventually
restores authority. An abrupt process kill can prevent in-process restoration; the
independent root operator must remain present and apply the recovery procedure below.

## Ordered real desktop cases

Run refusals while v1 is installed, then the successful prompt last. Compare the
installed app/helper to hosted v1 expected hashes before each refusal and afterward.
Keep the exact manifest requests, selected artifact, verified-download hash and
pkexec result. A network/startup failure is not an authority refusal.

1. **Prompt cancellation.** With ordinary fixture policy, invoke the real installed
   `--update` path. Observe the actual GDM polkit prompt, its action/program identity
   and the associated app/pkexec PIDs. Capture one fresh screenshot before any secret
   entry, then select the genuine cancel action. Record the observer, action and
   screenshot hash; require no adapter entry and unchanged v1 app/helper bytes.
2. **Explicit denial.** In the private root context use the bounded `deny` authority
   window. Its temporary rule matches only this fixture action and the actual GDM
   username, optionally the observed subject/session, and logs the rejecting PID.
   Invoke the same installed update; correlate the polkit log and invocation/session.
   Require no adapter entry and unchanged bytes. Remove only the exact rule created
   by this window and verify the original authority still operates.
3. **Missing authority.** Requires the lease to explicitly include a short system-wide
   polkit-unavailability window in the otherwise exclusive disposable VM. Do not use
   a private-bus environment override: pkexec clears `DBUS_SYSTEM_BUS_ADDRESS` before
   acquiring authority. The bounded root window verifies systemd D-Bus activation,
   records active original service state and absence of pre-existing masks, creates
   only a runtime mask for `polkit.service`, stops it, and verifies both absent bus
   ownership and blocked activation. Invoke the same GDM app within that window.
   Require no adapter entry and unchanged bytes. Remove only the created runtime
   mask, restart the originally active service and verify bus ownership. If the lease
   excludes this shared-service window, leave this case `not_run`; do not fake it.
4. **Prompt accepted.** With original authority restored and no temporary rule, invoke
   the same installed update. Capture the real prompt before entering any secret;
   the approved operator completes existing guest authentication privately. The
   assistant never collects or records the password. Require the real adapter's
   authenticated v2 install receipt and the hosted v2 app/helper hashes afterward.
   This also validates the positive desktop path, separate from headless evidence.

The screenshot/observer record is evidence for independent review, not automatic proof
of prompt contents or user interaction. Do not record passwords, keystrokes or a video
of authentication. Keep only the bounded diagnostic output and pre-entry prompt image.

Use the previously prepared real outer AppImage commands for any arm64 desktop replay
requested by the lease; exact target, signed upgrade/relaunch and reverted v3 behavior
already have installed native headless evidence. No x86_64 graphical prerequisite or
expanded lifecycle/interrupted-dpkg matrix is added here.

## Recovery and handoff

Keep the independent private root session available throughout authority testing.
The authority helper restores its own changes on normal exit and handled signals.
If it is killed abruptly or the guest stops, LINUX-20261016 must inspect its recorded
owned paths, remove only its exact runtime mask/rule, restart the previously active
polkit service and verify bus ownership before ending the lease. Never run a broad
rule deletion, global policy reset, VM reset or cleanup in Office400 directories.

Retain commands, stdout/stderr, request logs, actual session/PID evidence, public trust
hashes, before/after app/helper hashes, prompt screenshot hashes, observer outcomes,
authority state and restoration results. Mark each case observed, failed or not_run;
LINUX-20261016 independently decides acceptance. Preserve the source/build distinction:
desktop harness additions have not executed merely because hosted source113a53e passed.
Remove only this lease's temporary files/rules/package if the coordinator authorizes
cleanup, and retain its receipts in the dedicated #1057 directory. No done/ready/merge.

Primary implementation references: [pkexec124 source](https://github.com/polkit-org/polkit/blob/124/src/programs/pkexec.c),
[polkit D-Bus activation](https://github.com/polkit-org/polkit/blob/124/data/org.freedesktop.PolicyKit1.service.in),
[polkit systemd unit](https://github.com/polkit-org/polkit/blob/124/data/polkit.service.in),
[systemd255 mask semantics](https://github.com/systemd/systemd/blob/v255/man/systemctl.xml).
