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
preparation requested by the coordinator; they have not run in a guest and are outside
that fingerprint. No claim is made that new receipts or harnesses existed during their
own earlier build.

| Evidence | arm64 | x86_64 | Acceptance scope |
|---|---|---|---|
| Public hosted eligibility and actual execution | Pass | Pass | Both native jobs actually executed and succeeded |
| Ubuntu 22.04 native build; deb and AppImage from one bundler invocation per version | Pass | Pass | v1/v2/v3; exact locks and package hashes retained |
| Ubuntu 24.04 installed deb/full AppImage runtime under virtual display | Pass | Pass | Actual dpkg and read-only FUSE identity; headless only |
| Exact format/architecture target and missing-key refusal | Pass | Pass | Full pinned updater HTTP/check/download/signature path |
| Signed v1 → v2 and higher v3 with reverted fixture behavior | Pass | Pass | AppImage replacement/relaunch and privileged deb verification |
| Lower/same signed deb replay refused at privileged seam | Pass | Pass | App/helper hashes unchanged; live caller substitution also passed |
| Privileged bad signature and signed wrong-architecture AppImage | Pass | Pass | Intended rejecting boundaries; no installation/replacement |
| GDM polkit prompt, cancellation, denial and missing authority | Awaiting explicit VM lease | Downstream desktop gap | Hosted allow rules cannot satisfy graphical acceptance |

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
bootstrap and smoke hashes. Package ZIP retention is seven days. Only the two small
source/receipt ZIPs were downloaded locally. A later approved download needs both the
package ZIP and its small receipt ZIP, extracted into the same output root.

Worker schema review found exactly two control files (`control`, `md5sums`, 611 bytes
total), four payload files (app, inert helper, desktop entry and icon) and ten directories
in each deb. All have root ownership; directories/app are `0755`, other files `0644`.
No scripts, links, special files or adapter/key/verifier/policy paths are admitted.
Admission, package index and extracted payload hashes agree for all three versions on
both architectures. This is review of these exact fixture packages, not a general installer.

The worker has no VM lease. Office400/#982 exclusively owns Lima until LINUX-20261016
explicitly transfers it. Do not boot, install, change sessions or run guest probes before
that transfer. The host is below the 35 GiB large-allocation floor: no local build,
dependency installation, Docker startup or artifact download. Small source/lock/docs
preparation is bounded to 128 MiB new allocation while preserving 20 GiB free. Before the
later arm64 download, report exact hosted artifact bytes and obtain the coordinator's
resource allocation. No second VM or x86_64 graphical prerequisite is introduced.
The concrete [arm64 GDM handoff](../../spikes/1057/installed-updater/probe/DESKTOP.md)
records exact artifacts and extraction/install/storage bounds, graphical PID/session
binding, genuine prompt observation and bounded authority restoration. It reserves
1.25 GiB additional guest storage and, only if the coordinator chooses Mac staging,
260 MiB for ZIP transfer. Neither allocation nor guest access has been granted here.

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
tests, the smoke validator's six regression tests, Python AST and shell syntax checks,
and `git diff --check`. At source113a53e, the live `check-linux-admission.py --pr 13
--head 113a53e4eea44b6d80a8ee3edb55d186d11f3ba6` accepted all six required checks.
The coordinator takes sole CI/Council observation for the later handoff head, as directed
in card comment10584; its outcomes must be read independently rather than inherited.
The new desktop helpers have source/mocked validation only, never a graphical pass.

Deliver one draft PR with `Campus Linux: ` title prefix and `LINUX-20261016`, #1057,
source/build/package hashes, exact-head checks, self-review, failures and remaining evidence
in its body/card. LINUX-20261016 is the next owner and sole CI watcher. Preserve commits
and workspace on failure; name the exact failed operation, actionable error, next step
and actual coordinator watcher or explicit human handoff. Do not mark ready, merge,
enable auto-merge or mark the card done before coordinator acceptance. Follow
[repository verification and admission](verification.md) for unchanged required checks.
