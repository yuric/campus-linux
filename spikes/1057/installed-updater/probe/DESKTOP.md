# Arm64 GDM lease handoff — #1057

Current direction1269 / human10741 authorizes source and mocked tests only, from
`333d59b`, with at most 32 MiB new allocation and 18 GiB host reserve. Office400 owns
Lima; neither VM may be accessed for this source task. The actual333 attempt remains
failed before readiness: two daemon rows carried UID/GID 989, kernel sender PIDs 3263
and 3274, syslog transport, current boot and journal timestamps, but lacked `_EXE`
and `_SYSTEMD_UNIT`. Those observed numeric IDs are historical, never future inputs.
No updater invocation occurred. Missing authority remains independently unproven;
the next separately granted lease runs that case first after its own checks. It does
not depend on denial logger readiness. Changed helper bytes require fresh hashes and
coordinator/different-family source review before execution.

Phase B direction1233 / human10643 authorized exact368809e execution with approved113a
packages. The [actual attempt](../../../../docs/acceptance/receipts/installed-updater-1057/phase-b/run.json)
is incomplete and Lima was returned stopped. Human10665 / direction1242 records that
LINUX-20261016 viewed the genuine empty-password prompt and independently verified
restored policy/inode absence and stopped owned processes. The first cancellation
timeout remains incomplete; `cancel-after.png` belongs to that first attempt.
Human10670 records root and fresh independent Opus5.5 acceptance of exact3697b28 as
partial Phase B evidence: genuine GDM cancellation for the recorded tuple is manually
accepted while raw `not_certified` remains unchanged. The journal identifies exact
app `3159:start37557`, but session `6` may be polkit's UID-display fallback and is not direct
PID-session proof. Combined Terminal/session/VNC/empty-password prompt evidence,
signed v2 download, pkexec126 and unchanged v1 bytes support only that bounded finding.
The deny loaded-marker prerequisite failed, no denial update
was invoked, and missing authority remains `not_run`. None becomes a pass through a
source correction.

Direction1242 authorizes only the narrow fixture marker bridge and source regressions
on draft PR13. Actual Duktape polkit124 runs `--no-debug` with stderr at `/dev/null`,
where `polkit.log()` writes; the bridge instead uses a fixed `/usr/bin/logger` argv
through `polkit.spawn`. Availability and delivery were unverified at that source
handoff; the later333 root-context preflight delivered, while actual daemon readiness
failed as recorded above.
Human10677 / direction1247 records Office400's returned Lima lease and root's Stopped
verification; this grants no guest read, access or boot. UTM stays stopped. Small
source/docs/evidence work and focused Python checks may use the existing 128 MiB
source budget with an 18 GiB host free-space floor. Record actual free/allocation and
stop new growth below that floor. The 20 GiB host reserve for guest work and 35 GiB
large-growth guard remain; no download, build or runtime/timing work is authorized.
Dependency, provider and paid operations remain prohibited. Preserve the exact
approved 113a artifacts and every prior receipt/screenshot, including the failed
marker window. LINUX-20261016 reviews the new helper bytes and remaining evidence,
then separately grants any bounded execution lease when resource floors permit it.
The coordinator owns CI/Council and merge; this source handoff starts no watcher.

The historical procedure below describes source preparation. Lease10643 scoped execution
to three refusal scenarios only, with20-second recorder timeout,45-second total windows
and10-second restoration reserve. Its private ordinary-login permission did not authorize
administrator authentication or the fourth successful-prompt case described below.

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
| Root-owned helper/bootstrap staging | 65 MiB |
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

Phase A read-only inspection found active GDM with only its greeter (`c1`, UID110)
and the SSH management session (`4`, UID501); existing `campusqa` UID1000 had no
active session/runtime. Neither greeter nor SSH is the required user desktop.
The later execution lease must include an existing private graphical login, then
bind that actual new session. No login or configuration change was made in phase A.
`/etc/polkit-1/rules.d` was root-owned `0750` (GID989), explaining desktop read denial;
`/run/systemd/system` was root-owned `0755`. Polkit was active/running without masks
or drop-ins, owned its system-bus name and supported systemd activation. Preserve
those constraints. `libfuse2t64` was absent; optional AppImage desktop replay remains
separate from these deb authorization cases and does not authorize installation.

Record the lease reference, approved directories and byte budget, actual Ubuntu/arm64
identity, active local GDM session, user/UID, session leader, Wayland/X11 display,
runtime directory and relevant polkit/D-Bus/GTK versions. Preserve existing session
and service state. Reject a pre-existing `campus-updater-1057` package, trust directory
or fixture polkit rule rather than overwriting it. No headless allow rule may be present.
The existing private root context must inspect the actual rules-directory owner/mode
and effective policy files when the desktop user cannot read them. Export a bounded
JSON preflight receipt and bind its SHA-256 in the coordinator handoff. Preserve the
observed directory restrictions; do not relax them to make an unprivileged read work.
After later provisioning, refresh that root inventory before running desktop cases:
the phase A baseline cannot certify subsequently changed authority state.

### Required logger preflight for the next lease

The next explicit execution lease must satisfy all of these before a **denial**
window. Missing authority has its own independent mask/activation/readiness checks
and runs first under the next lease. Source tests cannot satisfy guest prerequisites.

1. From the separately authorized root observation, inspect the actual guest
   `/usr/bin/logger`: record its literal and resolved canonical paths, symlink status,
   regular-file/executable status, UID/GID, mode and SHA-256. Inspect every ancestor's
   owner/mode and resolution. Require the fixed executable and resolved ancestors to
   be root-controlled and nonwritable by group/other; reject a symlink, setuid/setgid
   executable, writable path, missing executable or identity mismatch. Bind the
   accepted path and digest to the reviewed helper and current lease, then recheck before use. Do not
   install a logger, choose a substitute path or alter permissions to pass preflight.
2. Record the installed logger implementation/version and its `--help` interface;
   verify support for the exact fixed argv:
   `[/usr/bin/logger, --socket-errors=on, --priority, user.notice, --tag,
   campus-updater-1057, --, MESSAGE]`. Keep the message a single argument after the
   option terminator; no shell, interpolated command string, server-selected
   executable/path or broadened logging configuration is permitted.
3. Verify **real journal delivery** of a unique bounded preflight marker using those
   same executable/options from the authorized preflight context. Record argv,
   execution UID/context, timestamp, exit status and the actual exact journal message
   with trusted metadata. Exit zero without the observed message is insufficient.
   This preflight changes no service, logging, authentication or policy configuration
   and grants no app authority. Its result establishes only that recorded context:
   it does not assert successful execution by the polkit daemon.

The denial helper binds the actual active `polkit.service` MainPID, starttime,
executable, cgroup and real UID/GID before mutation. It cross-checks the dedicated
`polkitd` NSS account, requires a different fixture UID and rejects unexplained
same-UID processes. Record and recheck the complete identity before readiness and
restoration; missing reliable fields or context changes invalidate correlation.
The helper generates a fresh 128-bit OS-random nonce, stores it in the root receipt
before creating the rule, and embeds it with the bounded lease in both marker events.
The nonce correlates the attempt; it is not a secret or an authentication credential.

After successful rule registration, the helper waits at most five seconds within the
unchanged 45-second total. Each loaded/rejecting row must contain the exact event,
lease, nonce and payload, the expected tag, verified service `_UID` and `_GID`, a
valid kernel sender `_PID`, `_TRANSPORT=syslog`, current `_BOOT_ID` and trusted
journal reception time inside the relevant window. Preserve monotonic timestamps
when available. The rejecting payload binds the actual app PID, user, session and active state;
correlate the separately observed app starttime and session with the invocation. The logger sender PID is not the
app subject PID; loaded and rejecting logger invocations may have different PIDs.

`_EXE` and `_SYSTEMD_UNIT` are optional journal process metadata. If present they
must be exactly `/usr/bin/logger` and `polkit.service`; empty, array-valued,
malformed or contradictory values fail visibly. Absence is permitted only under
the complete credential/nonce/context contract and is explicitly recorded. Preserve
full accepted and rejected rows; a bad current-nonce candidate cannot be hidden by
a later good row. Message, tag, `_COMM` or `SYSLOG_PID` alone never qualifies.
No separate marker-only rule, sleep to manufacture metadata, alternate transport,
fake PID or widened authority window is permitted.

This evidence attributes an exact fresh marker to the verified dedicated polkit
service account and owned rule in this controlled guest. When process metadata is
absent it does not directly prove the sender executable, parent service or cgroup.
The trusted dedicated-account assumption excludes malicious root and same-account
compromise; before/after inventories cannot exclude a transient hostile process.
If that assumption cannot be established, fail closed. Loaded evidence permits
readiness only; exact rejecting evidence, unchanged bytes, no adapter entry, actual
app/session/time correlation and clean restoration remain independently required.

If the executable/interface or real preflight logging check fails, record the
failure visibly and stop before an authority window. No observed marker means no
logging qualification, even when a command returned zero. Preserve bounded diagnostics
and all failed evidence; return the blocker to LINUX-20261016 for disposition. This
runbook defines a later-lease prerequisite, not permission to probe Office400's guest.

### Staged provisioning and recorder

Use only the coordinator's existing private guest authentication for root provisioning.
Do not collect an administrator password, put it in arguments/logs, use `sudo -S`,
terminal sudo, or build an alternate escalation path. The remaining provisioning
commands require the later execution lease, not phase A.

Before either privileged Python program runs, stage its exact reviewed bytes from
that independent root context into a fresh root-owned directory under `/root`, with
root-controlled nonsymlinked ancestors. Use `0700` while copying, then `0500` for the
staging directory and `0400` for every staged file. Never execute a helper directly
from the desktop user's checkout or extracted bundle. Independently compare the
staged authority helper SHA-256 to the reviewed source head; compare the staged
`bootstrap.py` to source113a53e's `fixture-inputs.json`. Also stage and independently
compare all bootstrap inputs to the admitted provisioning receipts:
`install-deb.py`, `verify-signature`, `public-key.txt`, `admission.json` and
`dev.projectcampus.updater1057.policy`. This matters because bootstrap explicitly
imports its bundled adapter. Keep all six bootstrap files in the same staged
`bootstrap` subdirectory; make that directory `0500` too. A hash generated from the
new copy alone is not verification against the admitted bytes.

Authority-helper staging command shape, only in the later root execution lease:

```sh
umask 077
stage_root=$(/usr/bin/mktemp -d /root/campus1057-reviewed.XXXXXXXX)
authority_sha256='REVIEWED_AUTHORITY_HELPER_SHA256'
/usr/bin/install -m 0400 /approved/source/authority-window.py "$stage_root/authority-window.py"
/usr/bin/chmod 0500 "$stage_root"
printf '%s  %s\n' "$authority_sha256" "$stage_root/authority-window.py" | /usr/bin/sha256sum --check --strict
```

Record the actual staging paths, owners, modes, expected and observed SHA-256s in
the lease receipt, and stop if any comparison fails. Prepare the bootstrap staging
directory by the same copy/compare/lock procedure. Execute the verified staged copy
in an explicit subshell, then install the exact v1 deb as initial provisioning:

```sh
(umask 022; /usr/bin/python3 -I -B /root/ACTUAL_STAGE/bootstrap/bootstrap.py \
  --bundle /root/ACTUAL_STAGE/bootstrap)
```

The subshell leaves private staging's `umask 077` intact. Bootstrap's exact directory
mode checks remain unchanged: unexpected existing permissions still refuse. Do not
chmod shared or pre-existing system directories to make provisioning pass.
Both root Python invocations use `-I -B`: this excludes user-controlled module paths
(including a neighboring or working-directory `json.py`) and avoids bytecode writes.
Initial `dpkg --install` is separate from the updater; every update invokes the real
fixed pkexec adapter.

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
  --root-preflight /approved/evidence/root-policy-preflight.json \
  --root-preflight-sha256 'COORDINATOR_VERIFIED_PREFLIGHT_SHA256' \
  --observer 'ACTUAL_OBSERVER' --planned-observation 'Observe the prompt and select cancel' \
  --receipt /approved/evidence/cancel.json \
  --screenshot /approved/evidence/cancel.png --timeout 20
```

Use `deny`, `missing-authority` or `prompt` for the other cases. The prompt/cancel
screenshot must be captured during the invocation, before any password is entered.
For deny/missing-authority, supply the actual bounded-window receipt reference.
The initial command records the intended interaction only. After the process exits,
the actual observer records what happened, including unexpected or absent prompts:

```sh
python3 -B spikes/1057/installed-updater/probe/desktop.py \
  --record-outcome /approved/evidence/cancel.json \
  --observer 'ACTUAL_OBSERVER' --observation 'ACTUAL_GUI_OUTCOME'
```

The separately timed observation does not replace the technical result or independently
prove the prompt; both remain for coordinator review. An unprivileged process may be
denied `/proc/PID/exe` access for setuid pkexec. Preserve `name_only`/unavailable evidence
honestly; do not call a process-name sample proof of the executable path. Correlate
that sample with the exact app child PID, polkit subject/session and the fixed invoked
`/usr/bin/pkexec` path; root may inspect that exact PID if the execution lease allows.

From the already-authorized independent root context, with an existing root-owned
`0700` receipt directory, prepare a window using the actual GDM UID and session ID
from verified logind binding. Use the staged helper and the SHA-256 verified above:

```sh
/usr/bin/python3 -I -B "$stage_root/authority-window.py" deny \
  --lease COORDINATOR_LEASE_ID --uid ACTUAL_GDM_UID --duration-seconds 45 \
  --session-id ACTUAL_GDM_SESSION_ID --source-sha256 "$authority_sha256" \
  --receipt /approved/root-private/deny-window.json
```

For the missing-authority case use positional mode `missing` and add
`--allow-shared-authority-window` only when that window is in the actual lease.
The helper prints readiness; the root operator then starts the pre-staged GDM
recorder promptly. Up to ten seconds of the requested 15–45 second duration is
reserved for restoration, so use `--timeout 20` for the refusal recorder. For denial,
also require the matching `campus1057-deny-loaded` and actual `campus1057-deny` journal
markers: rule-file creation is not proof of denial. Preserve the bounded current-window
candidate rows, including wrong-PID/event/identity contradictions. Do not filter those
out by the expected subject PID. Use a 65-row sentinel and refuse an export with 65
or more rows; silently retaining only a tail could hide a contradictory candidate.
Do not capture an unrelated session log dump.
The fixture bridge emits the loaded marker only after successful `polkit.addRule`
registration. Its fixed executable/options use `polkit.spawn` argument vectors with
validated bounded lease/user/session/PID values; no shell or app-authority fallback
is involved. A missing/failing logger or absent exact marker prevents qualification
and must be retained as a failure, never replaced by rule-count evidence. Keep the
loaded marker's exact lease identity, the action/user/session scope in the owned hashed
rule and the rejecting marker's actual PID/user/session/active diagnostic fields, and
correlate them with the invocation. The rule also requires a local subject.
If the rejecting logger invocation throws, the rule retains its scoped `Result.NO`;
it never falls through to authentication. Missing the exact rejecting marker still
makes the case failed/incomplete, even when pkexec refused. The helper's
`window_elapsed` status or successful cleanup reports window operation, not case success.
The 45-second total authority bound and 20-second recorder timeout stay unchanged.
Afterward, the reviewer must compare the actual update invocation's start/end times
with `ready_unix_ns` and `restore_started_unix_ns` in the authority receipt: the whole
invocation must fall within that interval. Window creation/readiness alone is not
proof that the update occurred while denial or missing authority was effective.
For denial, also establish that the matching loaded marker preceded that invocation.
Do not prefilter the rule by a PID that does not exist yet; bind the actual session
and correlate the logged rejecting subject PID to the observed app child afterward.

After restoration, export the final root authority receipt and full bounded journal
JSONL rows through the existing authorized control channel. The coordinator binds
their SHA-256s and the completed desktop receipt's SHA-256. Preserve the full rows,
including contradictions and missing optional fields; never export only the rows
that appear to pass. Run the unprivileged post-run validator with the exact reviewed
`authority-window.py` adjacent to `desktop.py`:

```sh
/usr/bin/python3 -I -B /approved/source/desktop.py \
  --validate-denial /approved/evidence/deny.json \
  --desktop-receipt-sha256 'COORDINATOR_VERIFIED_DESKTOP_SHA256' \
  --authority-receipt /approved/evidence/final-deny-window.json \
  --authority-receipt-sha256 'COORDINATOR_VERIFIED_AUTHORITY_SHA256' \
  --journal /approved/evidence/deny-journal.jsonl \
  --journal-sha256 'COORDINATOR_VERIFIED_JOURNAL_SHA256' \
  --authority-helper-sha256 'REVIEWED_AUTHORITY_HELPER_SHA256' \
  --validation-receipt /approved/evidence/denial-correlation.json
```

This writes a new private correlation receipt and never modifies the original
observations. The reviewed helper source is hash-checked before its pure validator
is loaded; no authority operation runs during validation. Both loaded readiness and
actual rejection use the same marker predicate. Incomplete or ambiguous app session
binding, changed service identity, missing reliable fields, a contradictory current
nonce or failed restoration yields `incomplete`. A successful correlation remains
`correlated_pending_coordinator_review`, never final acceptance. Prior failures and
missing-authority evidence cannot be promoted by this denial-only validator.

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
   username and actual session ID, and logs the rejecting PID.
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

The marker bridge follows the [polkit124 interface](https://github.com/polkit-org/polkit/blob/124/docs/man/polkit.xml):
`polkit.spawn` takes an argument vector and throws on unsuccessful execution. The
[util-linux logger interface](https://github.com/util-linux/util-linux/blob/v2.39.3/misc-utils/logger.1.adoc)
documents `--socket-errors=on` to surface local socket delivery errors. These interface
references justify the expected invocation; they do not prove the guest's executable,
supported options, service context or actual journal delivery.
