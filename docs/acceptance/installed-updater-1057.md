# Installed Tauri updater prototype — #1057

LINUX-20261016 owns acceptance, independent review, Council and merge. This is disposable
D4/G5 evidence for L0, not L0 completion or a production package. The only merged build
dependency is bootstrap #981 at `37ef5d622da09cd7ba113dc0d1119e62e7378f84`.

## Evidence status

Public native runners actually executed the initial lock-preparation
[run 38909633029](https://github.com/yuric/campus-linux/actions/runs/38909633029)
at source `164d7d0dd92fd76dae9abb73a2a34b11af898d5f`. Both jobs completed successfully,
with identical application Cargo locks (`36ce58e103553e14de36c041d245922935d5c59528f325cff2f83cda331d3b34`).
The [run receipt](receipts/installed-updater-1057/lock-preparation/run.json) and architecture
receipts record the real runner, image ID, build dependencies and source archive. This phase
did not compile or install packages. Only the small source/receipt archives (38,769 bytes
amd64; 38,729 bytes arm64) were retrieved locally; no package artifact was downloaded.

The first package [run 38910101310](https://github.com/yuric/campus-linux/actions/runs/38910101310)
at `67ef1123738f7b6c9bde0ec581cb2c5d4747a2b2` built all six real packages per architecture
and recorded 24 passing headless cases on each. Both jobs nevertheless **failed** during
runner cleanup: root-owned exported build directories prevented host `rm`. The
[failure receipt](receipts/installed-updater-1057/first-build/run.json), complete native
[arm64 smoke](receipts/installed-updater-1057/first-build/arm64/installed-smoke.json) and
[amd64 smoke](receipts/installed-updater-1057/first-build/amd64/installed-smoke.json) preserve
that distinction. Those original jobs remain failed even after the cleanup correction.
First-run package ZIP sizes are 257,737,151 bytes arm64 and 262,889,749 bytes amd64.
Only text/source receipt archives were retrieved locally. These sizes inform the later
coordinator download budget, not a VM lease or download authorization.

Review found that the original negative-case validator could accept an unrelated early
failure. The real first-run receipts show the intended requests and rejecting boundaries;
the validator was strengthened independently of those preserved observations.
Negative checks now require the expected request sequence, pinned diagnostic events and
specific rejecting boundary, no downstream installation, and unchanged installed bytes.
Small regression tests reject unrelated GTK/startup failures and zero-request results.
They do not substitute for the subsequent real installed hosted run.

The cleanup [run 38912107928](https://github.com/yuric/campus-linux/actions/runs/38912107928)
at `3de5ab666a84f0a29bb80844219a0c4509ff2238` completed successfully on both native
architectures, with 26 installed cases each. Its [raw receipts](receipts/installed-updater-1057/cleanup-rerun/run.json)
include real caller substitution and signed wrong-architecture AppImage rejection.
All nine negative cases per architecture also pass the later strengthened assertions on
receipt re-audit. The inotify queue records replacement before original reader close on both architectures;
its timestamps are userspace observation times, not kernel operation durations. These
ordered observations fall inside the privileged invocation.
This re-audit does not cover the subsequently added direct privileged signature case.

The final source [run 38913791148](https://github.com/yuric/campus-linux/actions/runs/38913791148)
at `113a53e4eea44b6d80a8ee3edb55d186d11f3ba6` completed **successfully on both native
runners**, with **27 passing cases per architecture**. The
[run/artifact receipt](receipts/installed-updater-1057/verified-run/run.json) binds actual
job conclusions, source, archive digests and sizes. The complete
[arm64 smoke](receipts/installed-updater-1057/verified-run/arm64/installed-smoke.json) and
[amd64 smoke](receipts/installed-updater-1057/verified-run/amd64/installed-smoke.json)
include the tightened negatives and direct privileged signature rejection.

The subsequent evidence/handoff commit leaves every file recorded in those builds'
`fixture-inputs.json` unchanged, including the app, adapter, hosted smoke and dedicated
workflow. The original canonical file-map SHA-256 is
`f775791c6e1080b60297b859e2f029109f5b10965eb928770ba78dadc05585ee`.
This binds the tested implementation while keeping build source and later evidence head
distinct. The later desktop recorder, authority-window helper and runbook are new source
preparation requested by the coordinator and are outside that fingerprint. Phase B below
records their later actual guest execution separately. No claim is made that new receipts
or harnesses existed during their own earlier build.

| Evidence | arm64 | x86_64 | Acceptance scope |
|---|---|---|---|
| Public hosted eligibility and actual execution | Pass | Pass | Both native jobs actually executed and succeeded |
| Ubuntu 22.04 native build; deb and AppImage from one bundler invocation per version | Pass | Pass | v1/v2/v3; exact locks and package hashes retained |
| Ubuntu 24.04 installed deb/full AppImage runtime under virtual display | Pass | Pass | Actual dpkg and read-only FUSE identity; headless only |
| Exact format/architecture target and missing-key refusal | Pass | Pass | Full pinned updater HTTP/check/download/signature path |
| Signed v1 → v2 and higher v3 with reverted fixture behavior | Pass | Pass | AppImage replacement/relaunch and privileged deb verification |
| Lower/same signed deb replay refused at privileged seam | Pass | Pass | App/helper hashes unchanged; live caller substitution also passed |
| Privileged bad signature and signed wrong-architecture AppImage | Pass | Pass | Intended rejecting boundaries; no installation/replacement |
| GDM polkit prompt, cancellation, denial and missing authority | Recorded cancellation tuple manually accepted under10670; first timeout incomplete, denial prerequisite failed, missing not run | Downstream desktop gap | Partial Phase B evidence only; raw `not_certified` retained, no direct PID-session proof |

| Final artifact budget | arm64 | x86_64 |
|---|---:|---:|
| Package/public-bootstrap ZIP bytes | 257,745,483 | 262,893,831 |
| Six package files, uncompressed bytes | 257,074,004 | 262,215,140 |
| Small source/receipt ZIP bytes | 128,142 | 129,992 |
| Largest admitted deb bytes | 4,706,052 | 4,604,616 |
| Largest admitted expanded data bytes | 15,087,544 | 15,868,807 |

All twelve package hashes, sizes, signatures and exact manifest targets are in the final
[arm64 package index](receipts/installed-updater-1057/verified-run/arm64/package-index.json)
and [x86_64 package index](receipts/installed-updater-1057/verified-run/amd64/package-index.json).
Full admission schemas and public keys are retained alongside them and match the root
bootstrap and smoke hashes. Package ZIP retention is seven days. The initial source
handoff downloaded only small receipts. The subsequently authorized phase A retrieved
the exact arm64 package ZIP and reused the coordinator's small receipt ZIP; neither
archive was extracted on the Mac or executed. Later guest extraction uses one output root.

Worker schema review found exactly two control files (`control`, `md5sums`, 611 bytes
total), four payload files (app, inert helper, desktop entry and icon) and ten directories
in each deb. All have root ownership; directories/app are `0755`, other files `0644`.
No scripts, links, special files or adapter/key/verifier/policy paths are admitted.
Admission, package index and extracted payload hashes agree for all three versions on
both architectures. This is review of these exact fixture packages, not a general installer.

Human direction10619 transferred only phase A after Office400's stop/cleanup:
bounded download/byte verification and read-only guest preflight, plus source fixes.
The [phase A record](receipts/installed-updater-1057/phase-a/run.json) binds the actual
[archive inventory](receipts/installed-updater-1057/phase-a/archive-validation.json),
[package/public trust verification](receipts/installed-updater-1057/phase-a/package-verification.json)
and [read-only root observations](receipts/installed-updater-1057/phase-a/root-preflight.json).
The ZIPs match the approved hashes and total 257,873,625 bytes. Expanded member sizes
are 257,742,285 and 826,410 bytes. All six package hashes/signatures and six public
bootstrap files match the admitted source and provisioning receipts. Verification
streamed members without extraction; no artifact was copied into the guest.

The exclusive Lima guest booted normally and was returned to **Stopped** after preflight.
Existing noninteractive root management authentication was used only for read-only
system observations, never for an app update. GDM and polkit were active, but only the
greeter and management SSH sessions existed; `campusqa` UID1000 had no active desktop
or runtime directory. The actual rules directory is root-owned `0750`, so desktop
permission denial must use the explicit root observation rather than imply absence.
Fixture package/trust/rules were absent. The [runtime receipt](receipts/installed-updater-1057/phase-a/runtime-preflight.json)
binds actual pkexec and systemd/D-Bus activation hashes; libfuse2 is absent, leaving any
optional AppImage desktop replay outside this deb authorization preparation.

Guest free space was 20,293,009,408 bytes. The [stopped capacity receipt](receipts/installed-updater-1057/phase-a/capacity-stopped.json)
records host free space 29,213,704,192 bytes and sparse disk allocation 6,819,020,800 bytes.
The initial preboot probe mistakenly looked for `basedisk`/`diffdisk`, missing the actual
`disk` file; no preboot allocation or boot-growth claim is made. The stopped measurement
is the next lease's baseline. Host-wide deltas are not attributed to this task.

The phase A exception permits at most 260 MiB private Mac staging and 1.25 GiB additional
guest allocation, preserving 20 GiB host and 2 GiB guest free. Source work remains bounded
to 128 MiB. No local build, dependency installation, Docker, second VM, package install,
trust bootstrap, graphical login change or authority-window execution occurred.
The concrete [arm64 GDM handoff](../../spikes/1057/installed-updater/probe/DESKTOP.md)
records exact artifacts and extraction/install/storage bounds, graphical PID/session
binding, genuine prompt observation and bounded authority restoration. Returned source
requires reviewed root-owned staging with isolated Python, explicit protected-rule
evidence, post-invocation observer statements and actual authority-window timestamps.
Those phase A prerequisites were subsequently cleared by coordinator comment10643,
which granted the bounded Phase B execution recorded below.
No second VM or x86_64 graphical prerequisite is introduced.

## Phase B: actual desktop attempt and restored blocker

Human comment10643 / direction1233 cleared exact source368809e and downloaded bytes,
then granted the existing Lima guest exclusively. The [Phase B index](receipts/installed-updater-1057/phase-b/run.json)
retains actual operations, failed attempts, raw receipts and their SHA-256s. No new build,
artifact, dependency, AppImage extraction, provider account or administrator authentication
was used. The initial artifact/source transfer streamed 15,391,158 verified bytes; later
driver/preflight/screenshot writes are included in measured allocation. The serving index is
a separately derived copy retaining the three unchanged deb entries; the recorder uses
the original approved index. Root staging was fresh, nonsymlinked, root-owned `0500`
with `0400` files; all seven helper/bootstrap digests were externally checked before
isolated Python. Public fixture trust and exact v1 deb were provisioned initially.
Every actual update used the installed fixed pkexec adapter.

Private ordinary login through the existing QEMU VNC channel produced GDM session `6`,
UID1000, Wayland, `gdm-password`, local `seat0`, leader2367, boot
`fa3b7740-a3be-49b5-8b6a-2e47e9d3b1b0`, DISPLAY `:0` and `wayland-0`.
The driver was launched through a visible GNOME Terminal. The refreshed
[root preflight](receipts/installed-updater-1057/phase-b/root-preflight.json), SHA-256
`50e378acb8ba1f3e0192d0c4992c6046097566e2f8a33f20fcd44c80f6a417ef`,
binds the lease/UID and both effective rule directories: `/etc` explicitly empty and
`/usr/share` with eight distro rules, owners/modes, no hosted allow rule, active GDM/polkit.
The digest was supplied by the worker from the authorized root observation and is now
reported for independent coordinator verification; the recorder's generic
“coordinator-supplied” provenance wording is not evidence of that later review. The keyring
remained locked.

| Attempt | Actual outcome |
|---|---|
| [First cancel](receipts/installed-updater-1057/phase-b/guest/cancel.json) | Genuine prompt captured; 20-second timeout before cancellation completed. Retained **incomplete**; v1 bytes unchanged. `cancel-after.png` belongs to this first attempt. |
| [Cancel retry](receipts/installed-updater-1057/phase-b/guest/cancel-retry.json) | [Actual prompt PNG](receipts/installed-updater-1057/phase-b/guest/cancel-retry.png), Cancel clicked before authentication, exact signed v2 download, pkexec126 `Request dismissed`, no adapter entry, unchanged v1 app/helper; update lasted2.283s. Recorded tuple manually accepted under10670 with the session limitations below. |
| [Deny window](receipts/installed-updater-1057/phase-b/deny-window.json) | Helper ready; polkit reloads nine rules, but required `deny-loaded` marker absent. **Update not invoked.** Exact owned rule restored after35.004s within45s total, retaining10s restoration reserve. |
| Missing authority | **Not run** after the unexpected marker state, obeying the stop instruction. No runtime mask created. |

The cancellation recorder honestly retains `not_certified`: native GNOME Terminal uses
an actual user-manager scope without direct `sd_pid_get_session` association. No SSH
process or environment variable was relabeled. The [polkit journal](receipts/installed-updater-1057/phase-b/guest/authority-journal.json)
independently identifies exact app `3159:start37557`; its session `6` association may be
polkit's UID-display fallback, so it does **not** prove direct PID-session membership.
Human10670 records root and fresh independent Opus5.5 acceptance of exact3697b28 as
partial Phase B evidence, including manual acceptance of genuine GDM cancellation for
this recorded tuple. The combined actual Terminal/session/VNC/empty-password prompt,
signed v2 download, pkexec126 and unchanged v1 app/helper support that bounded finding.
Raw `not_certified` and all receipts remain unchanged. Root retained independent Opus
session `54c2700a-e5b0-4616-9a27-a04ae0b40125` and reported 43 hashes, 125 old raw files,
cleanup checks and
30 repository tests passing; this worker does not extend that review to new helper bytes.

The [authority diagnosis](receipts/installed-updater-1057/phase-b/guest/authority-diagnostic.json)
records real polkit124 Duktape linkage, `--no-debug`, and stdout/stderr pointing to
`/dev/null`. Upstream124's [Duktape logger](https://github.com/polkit-org/polkit/blob/124/src/polkitbackend/polkitbackendduktapeauthority.c#L953)
writes `polkit.log()` to stderr; [no-debug startup](https://github.com/polkit-org/polkit/blob/124/src/polkitbackend/polkitd.c#L181)
redirects it away. Reload messages use [syslog separately](https://github.com/polkit-org/polkit/blob/124/src/polkitbackend/polkitbackendauthority.c#L1412).
This explains the missing marker; a count of loaded rules does not prove the exact rule
or rejecting subject. No service/logging configuration was changed and no marker check
was weakened. Human10665 / direction1242 subsequently authorized the source-only fixture
marker bridge described below; changing timeouts would not address this failure.

[Cleanup](receipts/installed-updater-1057/phase-b/root-cleanup.json) verifies identical rule
inventories, unchanged GDM config/public trust/v1 payload hashes, active original polkit
and bus owner, no fixture rule/allowrule/mask. Owned driver/server exited and no pkexec
remained. Packages, staged public inputs and bounded receipts are retained. Lima is
[Stopped](receipts/installed-updater-1057/phase-b/capacity-stopped.json), unchanged4CPU/6GiB/28GiB:
sparse allocation6,878,593,024bytes, growth59,572,224bytes from the approved stopped baseline;
host free27,593,158,656bytes, guest free before stop20,241,424,384bytes. ZIP staging remains
257,873,625bytes; private Phase B host files total1,093,263bytes at stopped sampling;
guest evidence export428,227bytes. All specified floors/budgets held. UTM was untouched;
CLI status failed with VM-not-found/-1743, so no successful UTM CLI verification is claimed.
Host-wide free-space changes are not attributed to this task.

Next owner is explicitly LINUX-20261016. Under10665 the coordinator viewed the genuine
empty-password prompt and independently verified restored policy/inode absence and
stopped owned processes/Lima. Newer10670 manually accepts the recorded cancellation
tuple with the raw/session limitations above; the first timeout remains incomplete.
Denial's marker prerequisite failed and missing authority remains `not_run`. Remaining
work is review of the new helper bytes, a separately granted execution
lease with the logger preflight below, actual denial/missing-authority cases and final
exact-head checks/Council/merge. D5 x86 desktop and the downstream production/lifecycle
matrix remain open. This attempt is **incomplete**, with clean restoration and an
explicit human/coordinator handoff.

## Source-only marker bridge handoff

Human10665 / direction1242 permits a narrow change to the fixture authority helper on
draft PR13. The bridge invokes fixed `/usr/bin/logger --socket-errors=on --priority
user.notice --tag campus-updater-1057 -- MESSAGE` through `polkit.spawn` as an argument
vector. Lease and subject values are bounded/validated; no shell or server-selected
executable/path is accepted. It preserves the fixture's
action/program, root target, actual user and local/active session scope. The loaded
marker follows successful rule registration; the rejecting marker retains actual
subject PID/user/session diagnostics. The exact loaded and rejecting markers remain
required, and missing/failing logging cannot qualify a case. Rule counts, successful
file creation and source mocks are insufficient. There is no app-authority fallback
or global service/logging/authentication change. Exact owned rule/device/inode/content
cleanup and 45-second total/20-second recorder/10-second restoration reserve remain.
If the rejecting logger invocation throws, the scoped rule still returns `Result.NO`
without an authentication fallback. An absent exact rejecting marker makes the case
failed/incomplete even when pkexec refused; helper `window_elapsed` or restored cleanup
does not qualify the case. The expected argument-vector/throw behavior comes from the
[polkit124 interface](https://github.com/polkit-org/polkit/blob/124/docs/man/polkit.xml),
and explicit local socket-error reporting from the
[util-linux logger interface](https://github.com/util-linux/util-linux/blob/v2.39.3/misc-utils/logger.1.adoc).
Neither source reference proves guest availability or real logging.

The [next-lease logger preflight](../../spikes/1057/installed-updater/probe/DESKTOP.md#required-logger-preflight-for-the-next-lease)
requires actual guest executable availability, canonical path and ancestor inspection,
root ownership/nonwritable modes, no symlink/setid executable, SHA-256, the expected
fixed interface, and a real unique journal message with the execution UID/context
recorded **before any authority window**. It proves only that preflight context. The
later denial window must observe its exact post-registration loaded marker within five
seconds before readiness, inside the unchanged total deadline. Loaded and rejecting
messages require trusted journal provenance: `_SYSTEMD_UNIT=polkit.service`, the actual
`polkitd` `_UID`, `_EXE=/usr/bin/logger`, current `_BOOT_ID` and timestamps within the
recorded window; a tag alone is insufficient. An absent
loaded marker visibly fails the helper and restores its exact owned rule. Source-only
permission does not assert that this executable or interface is present or usable in
the guest, and preflight exit-zero alone cannot establish real delivery or daemon context.

Human10677 / direction1247 records Office400's returned lease and root's Lima Stopped
verification. This permits no guest reads, access or boot; UTM stays stopped. The
existing 128 MiB source budget now has an 18 GiB host free-space floor for small
source/docs/evidence work and focused Python checks only. Record actual free/allocation
and stop new growth below that floor; retain the 20 GiB host reserve for guest work and
35 GiB large-growth guard. No download, build or runtime/timing work is authorized;
dependency, provider and paid operations remain prohibited. The approved
source113a packages and all old receipt/screenshot bytes, including the failed marker
window, remain unchanged. Focused marker invocation, escaping and failure regressions
extend the prior 59-test coverage; they prove only source behavior. LINUX-20261016 is
the explicit next owner for independent helper/evidence review and a separate bounded
lease when resource floors permit it. This consolidated source/docs/test handoff
neither certifies runtime acceptance nor starts a CI/Council watcher, marks ready,
enables auto-merge or completes the card.

Human10678 reports both native jobs in
[run38925541527](https://github.com/yuric/campus-linux/actions/runs/38925541527)
failed at source `5001e412898ffbac9fde7c64f1e6b75eff0d8216` before package output:
the new source test compared floating-point subtraction with exact equality and
observed `44.99999999999999 != 45`. This is a test arithmetic failure, not a measured
authority-window overrun. A mocked monotonic origin of `20.1` reproduces the exact
failure. The correction tests origins `0.0`, `20.1` and `63.9`, retains exact
start/deadline/reserve construction checks, and allows only `1e-12` rounding tolerance
for the elapsed subtraction. The authority helper and its 45/20/10-second bounds are
unchanged. The failed run remains failed; these focused source checks establish no
new installed or guest acceptance. Human10683 records the independent review disposition
and releases the single corrective push, limited to this test fix and documentation.
No helper change or relaxation of trusted marker requirements was requested.

## Fixture and trust boundaries

Source stays under `spikes/1057/installed-updater/`; receipts stay under
`docs/acceptance/receipts/installed-updater-1057/`. The static diagnostic app contains no
Campus API, renderer, provider or executor. Its inert helper identity exists only for byte
comparisons. Fixture versions v1/v2/v3 do not alter production versions or channels.

Use the exact [toolchain lock](../../ci/toolchain-lock.json): Rust 1.99.1, Tauri 2.12.4,
Tauri CLI 2.12.3, tauri-bundler 2.10.3 and updater 2.14.0. Commit transitive Cargo locks;
record package/source checksums and the actual resolved bundler version. The static page
does not require Node or Vite. Build on the pinned Ubuntu 22.04
[release baseline](../../ci/Dockerfile.release-baseline), whose glibc ceiling is 2.35;
run those exact packages on Ubuntu 24.04. Record the derived image ID, installed package
inventory, every regular ELF in each extracted package payload, and per-format runtime/SBOM inventory. A build
on 22.04 alone does not establish installed 22.04 compatibility.
The recorded payload ABI ceiling does not inspect the outer AppImage ELF launcher or
the separately provisioned bootstrap verifier; their bytes are hashed, and their actual
24.04 execution is observed, but their ABI symbol inventories remain outside this receipt.

Generate one disposable signing keypair per hosted build in private ephemeral storage.
Only its public key, signatures and fingerprints may enter uploaded output. Delete private
material on success or failure. Never use owner release-key directories, repository
secrets or a persistent registry. Artifacts have bounded retention and recorded sizes.

The fixture serves a loopback `/stable/linux.json`. This deliberately isolated HTTP
transport is a test-only configuration. Keep four separate entries:
`linux-aarch64-deb`, `linux-aarch64-appimage`, `linux-x86_64-deb` and
`linux-x86_64-appimage`. The selected target comes from the running installed bundle and
native architecture, never a caller-provided format override. Default updater selection
can fall back to a generic target; an explicit exact target avoids that fallback. Dynamic
single-target manifests also need rejection. The updater must require the authenticated
signed version. [Pinned updater implementation](https://github.com/tauri-apps/plugins-workspace/blob/updater-v2.14.0/plugins/updater/src/updater.rs)

AppImage uses the pinned updater's own verify/replace path, followed by a fresh launch of
the same user-owned outer AppImage. Do not fake `APPIMAGE`, rename an archive, or run an
extracted payload and call it installed evidence. Record the runtime-provided outer path,
mount/executable identity and post-relaunch hashes.

Deb uses the updater's download/signature path, then only the fixed polkit adapter.
The pinned stock deb installer can fall back to password collection and terminal sudo;
it must never be called. No app-collected administrator password, `sudo -S` or terminal
sudo belongs in this update path. [Pinned elevation implementation](https://raw.githubusercontent.com/tauri-apps/plugins-workspace/updater-v2.14.0/plugins/updater/src/updater.rs)

The adapter independently authenticates the version and exact root-staged package with
the root-owned disposable public key. It admits only the reviewed fixture package schema,
fixed package identity/architecture and measured byte bounds. It holds the installation
lock while comparing the installed version, verifying staging and invoking fixed `dpkg`
on those same root-owned bytes. Caller paths, environment and manifest claims cannot
select a trust anchor, installed destination or executable. The review must inspect the
real Tauri package's contents; an old tiny-package limit is not evidence for this package.
The hosted source receipts retain byte-for-byte copies of `admission.json` and
`public-key.txt` from the public bootstrap bundle. This permits independent review of the
actual control/data members, ownership, permissions and measured bounds without
downloading the package archive. The admission digest must match the root bootstrap and
installed-smoke receipt.

## Installed execution sequence

The implemented app accepts these diagnostic commands at `/usr/bin/campus-updater-1057`
for deb or at the genuine outer `.AppImage` path:

```sh
campus-updater-1057 --diagnose
campus-updater-1057 --check http://127.0.0.1:17857/stable/linux.json
campus-updater-1057 --download http://127.0.0.1:17857/stable/linux.json
campus-updater-1057 --update http://127.0.0.1:17857/stable/linux.json
```

The [hosted smoke probe](../../spikes/1057/installed-updater/probe/smoke.py) consumes the
build's `receipts/package-index.json`, `packages/` and public-only `bootstrap/` outputs.
The [smoke image](../../spikes/1057/installed-updater/hosted/Dockerfile.smoke) provisions
the fixed fixture as container root, then runs every update as unprivileged `fixture1057`
under Xvfb, a real system D-Bus and real polkit. Its temporary allow rule matches only the
fixture action and user. No terminal sudo is used. The container has no network other
than its internal loopback server and uses bounded resources; FUSE receives the scoped
hosted-runner capability/device required for the actual outer AppImage runtime.

The probe extracts payloads solely to derive independent expected hashes; it never
executes those extracted files. Runtime diagnostics require an actual read-only FUSE
mount for AppImage or a matching installed dpkg record for deb. Each native smoke manifest
contains two real native entries and two deliberately unavailable other-architecture
trap entries. These test selection only; they do not certify a combined four-artifact
publication manifest. A later combined manifest uses both native builds' real receipts.

For the later explicitly leased GDM run, the unprivileged
[standalone server](../../spikes/1057/installed-updater/probe/serve.py) serves only indexed,
checksum-verified packages and logs requests. From the exact source checkout, point it at
the downloaded hosted output:

```sh
python3 -B spikes/1057/installed-updater/probe/serve.py \
  --index /approved/output/receipts/package-index.json \
  --version 2 --port 17857 --log /approved/receipts/requests.jsonl
```

Use `--version 1`, `2` or `3`; restart with
`--missing-target linux-aarch64-deb` (or the actual installed target) to remove that key
while retaining the real opposite-format entry and a generic trap. The server does not
invent packages for absent architectures, elevate privileges, alter environments or
perform installation. This command is a later-lease runbook, not a recorded desktop run.

Run the sequence separately for each architecture and format. Archive each actual command,
exit status, standard output/error and the relevant manifest/server request log. Stop on a
failure and record it; do not relabel a rejected or unavailable operation as success.

1. Verify package/signature/public-key hashes against the hosted build receipt. Record
   `uname`, `/etc/os-release`, package-manager architecture, session/display identity,
   WebKitGTK/runtime versions and exact test command. For desktop runs also capture
   `loginctl show-session` and the coordinator's lease reference.
2. Install genuine deb v1, or place genuine AppImage v1 in the fixture's private user-owned
   directory and execute its outer runtime. Record fixture v1, exact derived target,
   installed executable, helper and outer package hashes. Initial privileged setup is
   separate from the updater and must use the approved fixture bootstrap.
3. Serve v2 with all four format/architecture entries and distinguishable artifact URLs.
   Observe the exact local key and corresponding URL. Remove only that key while retaining
   the generic and opposite-format entries. The installed app must refuse, request no
   alternate artifact and preserve app/helper bytes. Restore the valid manifest.
4. Supply an invalid-signature artifact and wrong-format/architecture artifact through the
   integrated path. Record the rejecting boundary, no successful installer invocation,
   and unchanged app/helper bytes. A manifest claiming a higher version for signed older
   bytes must fail authenticated-version verification.
   Also submit the admitted v2 deb with the genuine v1 signature directly through pkexec;
   require the privileged verifier's signature rejection and unchanged installed bytes.
5. Apply signed v1 → v2 through the installed app. For deb, retain polkit/adapter output,
   root-staged hash, verified version, installed version and installed files. For AppImage,
   retain replacement hash, terminate the old process, execute the same outer path again,
   and require v2 plus expected app/helper behavior and hashes.
6. While v2 is installed, submit correctly signed v1 and v2 directly to the fixed privileged
   deb adapter. Require refusal while holding its installation lock and before `dpkg`;
   record installed version and unchanged executable/helper hashes. Separately check the
   installed updater does not offer lower or same versions. The latter alone does not
   prove privileged replay resistance.
7. Apply signed v3 whose fixture behavior deliberately returns to v1 behavior. Require
   version 3, the specified reverted behavior and expected bytes after relaunch. This is
   forward-version published rollback, distinct from failed-install recovery.
8. In the leased GDM session, record the real deb polkit prompt with the fixed fixture
   action/program identity. Capture cancellation, explicit denial and unavailable authority
   as separate cases, with process/adapter evidence that no fallback ran. Compare installed
   app/helper hashes before and after every refusal. Do not capture a password. Record
   actual prompt wording and screenshot hash, not a fabricated prompt fixture.

For substituted staging, retain a receipt showing the adapter copied the caller package
once into its private root directory, checked that staged digest, and passed that same
fixed staged path to `dpkg`; replacing the caller copy must not change installed bytes.
The hosted `deb/live-caller-substitution` case uses an unprivileged
[inotify watcher](../../spikes/1057/installed-updater/probe/replace-on-open.py) on genuine
caller-owned signed v1 while v2 is installed. It replaces the caller path with invalid
bytes after the adapter opens it. One ordered inotify queue must place the atomic
replacement before the original reader closes; a late wakeup, timeout or overflow fails
the case. The adapter must authenticate the original root-staged v1, refuse its lower
version, never invoke `dpkg`, and preserve installed hashes while the caller-path hash
changes. This proves the copy-once/refusal seam, not an interrupted installation.
[Linux inotify ordering and limitations](https://man7.org/linux/man-pages/man7/inotify.7.html)

The signed AppImage wrong-architecture negative changes only ELF `e_machine` in genuine
v2 bytes and signs that malformed fixture with the disposable key. It is streamed from
the original plus the recorded two-byte patch; it is never installed or described as a
valid cross-architecture artifact. A pass requires full updater signature verification,
refusal before replacement and unchanged installed v1 app/helper/outer hashes.

Keep fixture authority changes isolated to its own polkit action and restore them after
each test. A hosted fixture allow rule only proves headless integration, never a GDM
prompt or authentication interaction.

## Receipt requirements and handoff

Every case binds: source/lock/config hashes; workflow run/job/attempt URL and conclusion;
architecture/format; build image digest/ID; package byte size and SHA-256; public-key
fingerprint and signature hash; actual installed paths; before/after app/helper hashes;
commands/results; and an explicit `passed`, `failed` or `not_run` outcome with reason.
Expected hashes must come from the built package inventory, independently of the later
observed installed files. A missing receipt or skipped hosted job remains missing evidence.

`phase.json` is the build-time snapshot emitted before smoke and therefore says pending;
the actual `installed-smoke.json` and observed GitHub job conclusion record final results.
The strict caller-substitution timing check can fail on a late scheduler wakeup. Hosted
timeout/cancellation can preempt the container ownership cleanup and receipt upload;
such runs remain failed or missing evidence, never inferred passes. Successful runs do
not certify those interrupted hosted paths. These limitations were dispositioned in
[the worker review response](https://github.com/yuric/campus-linux/pull/13#issuecomment-6217429422).

Public hosted jobs use `ubuntu-24.04` / `ubuntu-24.04-arm`, pinned actions, read-only
contents permission, public-visibility guards, timeouts and cancellation. No repository
setting change, private-minute workaround, self-hosted runner or release publication is
authorized. Record native x86_64 build/headless results separately even when failed;
actual x86_64 desktop acceptance remains downstream under D5.

Background only: open [PR #12](https://github.com/yuric/campus-linux/pull/12), observed
head `a975d6747fe0d29932182bb07ad3b7fb01da7e3c`, carries #982's seventeen signature and
sixteen lifecycle fixtures at their stated scope. They are not merged build dependencies,
installed updater proof, or requirements to rerun wholesale here.

Production key custody, final packages, helper lease/outbox/lifecycle behavior,
interrupted-`dpkg` recovery, external package replacement during work and the complete
product/session matrix remain #989/#990/#996/#997/#999. Neither an inert helper nor a
headless updater pass closes those gates.

Worker verification uses `python3 -B scripts/verify_repository.py` (30 policy regressions,
boundary, acceptance inventory, links and legacy OpenAPI), the adapter's ten stdlib
tests, and the probe's 34 source regressions (six smoke, eleven desktop, eight
authority-window and nine marker-bridge tests), for 74 tests total. The earlier
59-test checks at368809e/3697b28 included nineteen probe tests and two authority-window
tests; those historical counts and raw receipts remain unchanged. Current commands:

```sh
python3 -B scripts/verify_repository.py
python3 -B -m unittest discover -s spikes/1057/installed-updater/adapter -p 'test_*.py' -v
python3 -B -m unittest discover -s spikes/1057/installed-updater/probe -p 'test_*.py' -v
git diff --check origin/main...HEAD
```

Python AST and shell syntax checks also pass. Marker tests use existing host Node to
evaluate generated JavaScript with mocked polkit, without a real logger or guest call.
At source113a53e, the live `check-linux-admission.py --pr 13
--head 113a53e4eea44b6d80a8ee3edb55d186d11f3ba6` accepted all six required checks.
The coordinator takes sole CI/Council observation for the later handoff head, as directed
in card comment10584; its outcomes must be read independently rather than inherited.
The desktop helpers also have the actual, incomplete Phase B execution above; source tests
and successful restoration do not establish graphical acceptance.

Deliver one draft PR with `Campus Linux: ` title prefix and `LINUX-20261016`, #1057,
source/build/package hashes, exact-head checks, self-review, failures and remaining evidence
in its body/card. LINUX-20261016 is the next owner and sole CI watcher. Preserve commits
and workspace on failure; name the exact failed operation, actionable error, next step
and actual coordinator watcher or explicit human handoff. Do not mark ready, merge,
enable auto-merge or mark the card done before coordinator acceptance. Follow
[repository verification and admission](verification.md) for unchanged required checks.
