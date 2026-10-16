# #982 disposable package and helper mechanisms

Owner: #982; admission/next owner: LINUX-20261016. These probes are deliberately
bounded pre-product experiments. They do not implement Campus or establish LINUX-16/17
release acceptance. #996 must build the final Tauri deb/AppImage and #997/#998 must
repeat every applicable case against those exact signed installed product bytes.
All results below distinguish source inspection, synthetic mechanism execution and
installed-product evidence. Missing or blocked observations are not passes.

## Pinned updater: a concrete G5 failure

The release baseline selects tauri-plugin-updater **2.14.0**. Its published crate was
retrieved from [static.crates.io](https://static.crates.io/crates/tauri-plugin-updater/tauri-plugin-updater-2.14.0.crate)
and its source matches the [tagged updater source](https://github.com/tauri-apps/plugins-workspace/blob/updater-v2.14.0/plugins/updater/src/updater.rs).
The crate records producer commit `44293a5722efcaf27060504e63b17aeba721b40f`.

| Object | SHA-256 |
| --- | --- |
| Published 2.14.0 crate | `7259989d4fe11b2bf51f7d671642249b1837c4ae2da1430dc713ae38f98ceeec` |
| `src/updater.rs` in crate and matching tag | `79ed11ecdb3d22410f71d7adb9f7bcbcab00f888cd8892e2268639085df044ce` |

The crates.io metadata API returned HTTP 403 during this audit. The above are observed
artifact hashes, corroborated by the matching tag source; this is not a claim of
independent registry signature verification. The reproducible audit refuses changed bytes.

`get_urls` first tries the bundle-aware `{os}-{arch}-{installer}` key and then the generic
`{os}-{arch}` key. An explicit updater target uses only that exact key. Therefore final
Campus integration must select the exact trusted local format/architecture target and
reject generic entries/missing format targets; merely supplying four entries does not
prove fail-closed behavior if one disappears. Required keys are `linux-aarch64-deb`,
`linux-aarch64-appimage`, `linux-x86_64-deb`, and `linux-x86_64-appimage`.

**Stock deb installation fails G5.** `try_install_with_privileges` tries `pkexec`, then
collects an administrator password using zenity/kdialog and feeds it to `sudo -S`,
then tries terminal sudo. Its privileged operation runs `dpkg -i` on the caller-owned
staged package without independently verifying those installed bytes against the trust
anchor. Do not call that installer from Campus. A denied/missing polkit action cannot
be converted into this fallback. #996 needs a reviewed bounded privileged installer,
with actual Tauri/minisign verification against the owner-held release public key, while
retaining the decided single manifest, Tauri updater and deb/AppImage formats.

[The audit script](../../../spikes/982/packages/audit-updater.py) downloads only the pinned
crate or accepts an already downloaded copy. It extracts the exact `get_urls` Rust method
into a standalone test with stub metadata, architecture and installer objects. With an
existing rustc it executes four distinct URL/signature selections, demonstrates the
generic cross-format fallback and checks that explicit targeting rejects that fallback.
This tests upstream method logic; bundle detection from each installed artifact and the
full Tauri updater remain separate unproven requirements. Host source audit completed; the [guest audit receipt](receipts/updater-source-audit.json)
records all six source-extracted cases passing with rustc 1.75.0. This is a disposable
logic probe, not the pinned Rust 1.99.1 product build or installed artifact routing.

```sh
python3 spikes/982/packages/audit-updater.py --output /tmp/campus-982-updater-audit
```

## Bounded fixtures and execution

[build-fixture.py](../../../spikes/982/packages/build-fixture.py) creates only
`campus-982-disposable-spike`, versions `0.982.1`/`0.982.2`, plus intentionally wrong
name/architecture test packages. The payload is a synthetic Python process with a file
lock and identity receipt. It contains no webview, provider CLI, API execution or secret.
The disposable OpenSSL Ed25519 key is generated in a mode-0700 fixture directory inside
the guest. It is **not** a release key, a Tauri signature or an approved production trust
format. No generated private key belongs in the repository or captures.

An optional real arm64 AppImage combines a pinned upstream type-2 runtime with a small
squashfs payload. It is unsigned and does not bundle WebKitGTK. Runtime upstream commit:
`8f39b89e2ac31e1640b3d3f7e9a5108e6ce805fa`; GitHub release ID `398504756`, asset ID
`596077442`; SHA-256 `b4ff0030242d0c3bb12ce40541828303cf167493f4793456f0436edd6255c39d`.
The [runtime download](https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-aarch64)
is mutable, so the builder requires this exact checksum and fails if it changes. This
records available upstream integrity metadata, not independent release-key authenticity.
The payload and runtime provenance must not be promoted into a product dependency choice.

Run as the disposable graphical guest user, with existing openssl, dpkg-deb and (for
AppImage) mksquashfs. Parent #982 owns guest execution; these scripts never install tools,
start another VM, alter owner CLI installations or use a provider account.

```sh
python3 spikes/982/packages/build-fixture.py \
  --output /tmp/campus-982-package-fixture \
  --runtime /tmp/campus-982-appimage-runtime-aarch64
python3 spikes/982/packages/build-negative-fixtures.py \
  --fixture /tmp/campus-982-package-fixture
```

The negative-fixture builder signs harmless test packages containing a maintainer script,
a symlink payload, an unrelated file, a setuid mode, a compressed 256KiB payload,
unprivileged ownership or a writable helper. All seven must be rejected despite valid
signatures; installed-helper digests must remain
intact. Missing fixture files are recorded as blocked cases. To add only the bounded
expansion case to an existing fixture, run the builder with `--only-expansion`; it reuses
existing disposable OpenSSL/minisign keys without replacing them.
`--only-metadata` adds only the two ownership/mode negatives to that existing fixture.

The root setup command below is explicit fixture provisioning in the named owned guest,
**not** an application password or installer fallback. It refuses other hostnames and
installs only test-namespaced root paths. The helper accepts no argv, no caller path and
no executable name. It accepts at most 4 MiB on stdin, copies package/signature bytes into
root-owned mode-0700 staging, verifies with the root-owned disposable public key, checks
package name/version/native architecture, and invokes fixed `/usr/bin/dpkg --install`.
Its exact archive schema requires root UID/GID 0, directory mode 0755, control mode 0644,
helper mode 0755, each required path exactly once and no extra PAX metadata. Wrong types,
missing/duplicate members, links, maintainer scripts and unrelated payload paths fail.
The verified package remains root-owned/read-only through the actual install. A deliberate
one-second pause after verification allows substitution of the original untrusted file.
No user-controlled pathname is reopened by dpkg. Root attackers are outside this boundary.
The current verifier caps subprocess output at 128KiB while reading and kills/reaps the
private process group on overflow/timeout. Earlier receipts checked the expanded size
only after buffering it; they do not establish this new resource bound. Host checks cover
the exact 128KiB limit and rejection at 128KiB+1 and 256KiB. The
[X11 bounded OpenSSL run](receipts/install-x11-bounded.json) passed ten cases and the
[X11 bounded Tauri run](receipts/tauri-install-x11-bounded.json) passed fifteen, including
the signed expansion rejection with installed helper intact. The later
[exact-schema X11](receipts/tauri-install-x11-schema.json) and
[exact-schema Wayland](receipts/tauri-install-wayland-schema.json) Tauri runs each passed
all seventeen cases, including wrong-owner and writable-helper rejection. The
[final OpenSSL X11 run](receipts/install-x11-schema.json) passed its twelve cases.

```sh
sudo python3 spikes/982/packages/prepare-guest.py --user campusqa \
  --fixture /tmp/campus-982-package-fixture --mode allow
python3 spikes/982/packages/test-install.py --fixture /tmp/campus-982-package-fixture \
  --output /tmp/campus-982-polkit-allow.json
sudo python3 spikes/982/packages/prepare-guest.py --user campusqa \
  --fixture /tmp/campus-982-package-fixture --mode deny
python3 spikes/982/packages/test-install.py --fixture /tmp/campus-982-package-fixture \
  --output /tmp/campus-982-polkit-deny.json --denied
```

The temporary allow rule proves action routing/root byte verification only. It does not
prove a polkit authentication dialog. `--mode prompt` removes that rule and requires an
actual active-session administrator prompt. Record the prompt on each Wayland/X11 tuple
and cancellation/denial with installed/helper digests intact. The rule must never remain
installed after the disposable run. The test client uses `pkexec --disable-internal-agent`
and has no alternative elevation path. Missing pkexec is an execution failure, not success.

```sh
sudo python3 spikes/982/packages/prepare-guest.py --user campusqa \
  --fixture /tmp/campus-982-package-fixture --mode prompt
python3 spikes/982/packages/test-install.py --fixture /tmp/campus-982-package-fixture \
  --output /tmp/campus-982-polkit-prompt.json --prompt
python3 spikes/982/packages/test-helper-lifecycle.py \
  --fixture /tmp/campus-982-package-fixture --output /tmp/campus-982-helper-lifecycle.json
sudo python3 spikes/982/packages/prepare-guest.py --user campusqa \
  --fixture /tmp/campus-982-package-fixture --cleanup
```

Cleanup now requires successful `dpkg --remove`, an uninstalled/config-files-only package
state and absent installed helper before removing the action/rule/helper/root staging.
If removal fails, it preserves the fixture rather than printing a successful cleanup.
The failure path passed a host mock; actual cleanup remains a guest observation. Remove the
caller-owned fresh fixture directory explicitly after preserving safe captures, deleting
the disposable private key. No provider-owned credential or repository is targeted.
Keep artifact digests, public-key fingerprint, command logs, actual session tuple and
result JSON; never collect the private key or real passwords in the receipt.

## Observed disposable guest results

The parent executed these probes in the owned Ubuntu 24.04 arm64 guest. The
[session identity](receipts/lima-wayland-identity.txt) records a real active local
`gdm-password` Wayland login, polkit 124 and systemd 255. These are mechanism receipts,
not an installed Tauri application or a trusted release artifact.

- [Nine allow-rule cases](receipts/install-wayland-allow-final.json) passed: native install;
  bad signature, wrong package, wrong architecture, signed maintainer script, symlink,
  unrelated path and setuid payload rejection; replacement of the original download
  after privileged verification still installed the verified bytes.
- [Explicit policy denial](receipts/install-wayland-denied.json) preserved the installed
  helper digest. [Real prompt authentication](receipts/install-wayland-prompt.json)
  installed the verified version `0.982.2`; the [prompt capture](receipts/polkit-wayland-prompt.png)
  records the desktop authorization UI. [Prompt dismissal](receipts/install-wayland-cancel.json)
  returned pkexec 126 with `Request dismissed` and an unchanged installed helper digest.
  These fixture prompts use the synthetic Ed25519 trust anchor, not Tauri signatures.
- [Sixteen lifecycle cases on the final probe revision](receipts/helper-lifecycle-final.json) passed across deb extraction
  and AppImage extraction: stable copy/singleton/move-delete/busy fence/promotion, five
  interruption boundaries, incompatible synthetic state, and sibling-data preservation.
  Raw process identities and measured termination times are retained. Synthetic outbox
  preservation is not Rails lease/event delivery or production supervisor timing evidence.

The original fixture also passed [X11 prompt authentication](receipts/install-x11-prompt.json)
and [X11 dismissal](receipts/install-x11-cancel.json), with the actual
[X11 prompt](receipts/polkit-x11-prompt.png) and [GDM identity](receipts/lima-x11-identity.txt).
[Missing polkit](receipts/install-polkit-missing.json) returned 127 with its authority
service masked and preserved the installed helper digest; there was no alternate elevation.

The historical OpenSSL driver checked exit zero for positive installs and recorded the
installed digest, but only its substitution case compared that digest to the expected
fixture helper. Its earlier positive rows are not independent expected-byte assertions.
Missing negative fixtures were labeled `BLOCKED` without forcing that driver's exit
status to fail; the recorded nine-case run contains all fixtures. Preserve those bounded
receipts. The corrected Tauri driver separately checks expected helper bytes on every
accepted install, records its own source hash, and exits
nonzero for a missing or failed case. The
[stronger Wayland rerun](receipts/tauri-install-wayland-allow-final.json) and
[stronger X11 rerun](receipts/tauri-install-x11-allow-final.json) each passed all fourteen
cases, including expected helper digest assertions, on their recorded driver SHA. The
original X11 receipt without the `-final` suffix retains its earlier assertion scope.
The latest source adds the signed expansion and two archive-metadata negatives and
requires seventeen cases; the [X11 exact-schema run](receipts/tauri-install-x11-schema.json)
and [Wayland exact-schema run](receipts/tauri-install-wayland-schema.json) both passed on
current driver SHA `15ce813245922d7668522a0d80fad3a7d34d121102c9c03cb5a3f637f8a2c9fd`.
The current root-helper source hashes are OpenSSL
`7f76fd8b4b3fb0f0c63da62425ad62683e2e3e670aefe09b37896513270cd441`
and Tauri `f59d75f3e67e47285c31f7689a90311a575050f06cd187c17df3adad99d57111`.
The lifecycle driver also now returns failure when
AppImage is missing rather than exiting zero with a `BLOCKED` row. Its existing
sixteen-case receipt includes both formats and is unaffected by that historical exit bug.
The [current lifecycle rerun](receipts/helper-lifecycle-bounded.json) also passed all sixteen
cases and records aggregate success with its matching source SHA.

The separate [Tauri minisign experiment](tauri-signatures.md) now has seventeen passing
privileged cases in each graphical session, including exact upstream signature/version
verification and no OpenSSL-format fallback. Actual product
formats, four installed updater targets, production integration/custody, interrupted dpkg
and external package replacement remain separate obligations. A positive fixture receipt
does not remove any of those gates.

The final driver also passed real password authentication on
[Wayland](receipts/tauri-install-wayland-schema-prompt.json) and
[X11](receipts/tauri-install-x11-schema-prompt.json),
[Wayland prompt cancellation with intact installation](receipts/tauri-install-wayland-schema-cancel.json),
and [missing runtime polkit authority with intact installation](receipts/tauri-install-wayland-schema-polkit-missing.json).
The operator unmasked/restarted the authority after this bounded failure probe. No
password-to-sudo fallback was used. These are still the separate test-key privileged
installer, not the full installed Tauri product updater.

## Separate real session and process observations

These supplement the filesystem/package model; they do not turn it into an integrated
product supervisor. The [session fixture](../../../spikes/982/security/session-service.py)
uses `campus-982-session-spike.service`, a stable private XDG `current/helper.py` path,
`Requisite`/`PartOf=graphical-session.target`, control-group kill, `Restart=on-failure`,
250 ms initial delay, three backoff steps capped at two seconds, no restart-limit lockout,
and a two-second **synthetic** stop timeout. The final stop timeout must derive from Rails
stop grace/outbox requirements, not this fixture value.

[Wayland retry receipts](receipts/session-wayland-retries.json) observed three exit-75
failures followed by recovery; [intentional zero](receipts/session-wayland-intentional-stop.json)
stayed down. [Last graphical logout](receipts/session-wayland-logout-ssh-open.json) stopped
the unit while SSH sessions remained; [manual SSH/greeter start](receipts/session-greeter-start-refused.json)
was refused. [Real X11 login without UI](receipts/session-x11-login-no-ui.json) restored
the same synthetic epoch. [Local synthetic revoke](receipts/session-revoke.json) stopped
the helper and [subsequent start](receipts/session-revoked-start-withheld.json) withheld it.
The [cold login without UI](receipts/session-cold-login-no-ui.json) additionally observed
the stable helper on a changed boot ID, retaining synthetic epoch4 with the graphical
target active. These are not real account/lease or production reboot-recovery receipts.

Separate [Wayland](receipts/process-wayland.json) and [X11](receipts/process-x11.json)
process probes observed a detached grandchild remain in the attempt cgroup and die with
its parent in 2.145 s / 2.218 s. Both receipts record boot ID/start ticks/pidfd exit,
cross-UID peer/token bounds, same-UID access limits and synthetic-secret crash handling
under the actual Apport collector. The [strengthened final X11 run](receipts/process-x11-final.json)
passed reciprocal server authentication before token send, rejected a wrong expected
server identity without sending the token, verified equal attempt cgroups, and stopped
both children in 2.185s. The [strengthened Wayland run](receipts/process-wayland-final.json)
passed the same checks and stopped both children in 2.206s. This does not prove every crash collector or real
provider lifecycle. The [scope/workspace receipt](receipts/security-os.json) supplements
path-safety and user-data preservation; those results never substitute for final package
and Rails protocol tests.

## Stable helper and complete D4 transition plan

The lifecycle probe extracts the actual fixture deb/AppImage, copies the payload into
private versioned directories, and uses a stable `current/helper` path. The parent
directory and versions are mode 0700. A manifest records helper hash, package hash,
architecture and synthetic state schema. The AppImage path is exercised with
`--appimage-extract`; it does **not** prove FUSE mounts or Tauri UI lifecycle. The new
helper candidate comes from the second deb fixture in both model runs; there is no
second AppImage/update transaction, and this is not per-format updater acceptance.

Promotion is explicitly a local model: a synthetic active-attempt marker fences changes,
old process termination precedes replacement, a durable atomic pointer selects the helper,
and a journal retains previous/candidate versions. Interrupted unaccepted promotion selects
the previous compatible helper; accepted promotion retains the new helper. Recovery leaves
claims fenced until external reconciliation. An unchanged synthetic outbox digest proves
only file preservation, not Rails acknowledgements, delivery order or lease recovery.
The model never advertises `helper_update_monitor` or acquires a real claim.

For the product, `current/helper` must be an absolute stable unit target beneath verified
XDG data, outside any AppImage mount and deb-owned package path. #989 defines the standalone
Rust helper, user-session unit and retry/stop policy; #996 coordinates promotion. Package
signature/checksum and helper/protocol/runtime identities belong in the manifest. Durable
state belongs under private XDG state with origin/channel/account/executor scoping. A
compatible old helper remains until startup, Rails lease reconciliation and durable outbox
recovery succeed. State incompatibility withholds claims and recovers forward. Published
rollback always uses a new higher signed version; local failed-promotion recovery is separate.

The following table is the required case matrix for **each** installed format and **each**
Wayland/X11 tuple. Script existence is not an observed pass. Raw run receipts, when present,
are the authority for fixture results; all actual product cases remain unproven.

| D4/G3/G5 case | Disposable mechanism coverage | Required final observation / owner |
| --- | --- | --- |
| First authorization / stable helper | Extract-copy, private versioned paths, byte manifest | Actual package signature, runtime closure, protocol and safe path components; #989/#996 |
| UI closed, remote dispatch | No UI or server in fixture | Same authorized epoch, no duplicate claim; #989/#997 |
| Move/replace/delete outer AppImage | Fixture move/delete after helper launch | Running image survives unmount/replacement; #996/#997 |
| Remove deb while UI closed | Test package cleanup only | Helper survives package removal, registration and uninstall route remain available; #996/#997 |
| SSH-only login | [Actual greeter/SSH-only start refused](receipts/session-greeter-start-refused.json) by separate session fixture | Cannot start supervisor; #989/#997 |
| Last graphical logout with SSH open | [Actual Wayland logout stopped fixture; SSH remained](receipts/session-wayland-logout-ssh-open.json) | Supervisor/children stop, no lingering; #989/#997 |
| Reboot/login without UI | [Cold login](receipts/session-cold-login-no-ui.json) admitted stable helper on a new boot ID with unchanged synthetic epoch4 and active graphical target; no real lease/outbox recovery | Authorized generation restored by real display-manager session; #989/#997 |
| Missing/locked/unlocked keyring | [Absent bus](receipts/store-absent.json) and final [Wayland](receipts/store-wayland-disposable.jsonl)/[X11](receipts/store-x11-disposable.jsonl) disposable collection cycles; item/collection cleanup verified; original login collection remains locked after rotation | Claims withheld/recovered without file fallback in actual product; #989/#997 |
| Concurrent UI and old/new packages | File-lock duplicate process rejection | One supervisor/lease owner during concurrent installer/start; #989/#996 |
| Busy update / grace and confirmation | Synthetic active marker refuses promotion | Report, confirm, fence, drain/cancel, prove termination, handback; Rails owns resume; #989/#996 |
| Stage interrupted | Crash after verified staging | Old compatible helper, no partial execution; #996 |
| Fence interrupted | Crash after durable fence | Claims remain withheld until ownership reconciliation; #989/#996 |
| Before atomic promotion | Crash after journal before pointer switch | Previous helper retained, outbox/ack cursor intact; #996 |
| After atomic promotion | Crash after pointer switch before acceptance | Compatible previous helper or safe forward recovery, no duplicate work; #996 |
| After acceptance / cleanup | Crash after accepted journal | New helper retained, old version cleanup safe; #996 |
| Incompatible app/helper/protocol/state | Synthetic state-schema rejection | Withhold claims; recover forward if rollback unsafe; #989/#996 |
| Failed startup / local recovery | Pointer-journal recovery only | Startup, lease reconciliation and outbox recovery determine safe version; #989/#996 |
| Signed higher-version rollback | Not implemented | Higher version/signature verified, no downgrade channel; #996 |
| External package-manager replacement during work | Not implemented | Detect file-vs-running-image digest, report, reconcile without direct restart; #989/#996 |
| Claim/start acknowledgement interruption | No real claim | Recovery drill at server boundary, no duplicate execution; #989/#997 |
| Mid-stream interruption | Synthetic outbox preservation only | Durable ordered replay and acknowledgement cursor; #989/#997 |
| Provider exit before terminal acknowledgement | No real provider | Ownership retained and terminal event replayed exactly; #989/#997 |
| Cancellation interruption | No real cancellation | Lease-safe cancellation and reconciliation; #989/#997 |
| Crash loop / retry backoff | Separate [three retry exits/backoff/recovery](receipts/session-wayland-retries.json), [intentional zero stayed down](receipts/session-wayland-intentional-stop.json) | Retry exit distinct from intentional stop; bounded backoff and recoverability; #989/#997 |
| Sign-out/revoke mid-run | [Synthetic epoch revoke stopped fixture](receipts/session-revoke.json), [later start withheld](receipts/session-revoked-start-withheld.json); no real account/lease | Local precedence, fence/disable before remote revoke; concurrent installer cannot reactivate; #989/#997 |
| Same-account sign-in / repair / relaunch | No account in fixture | Preserve authorized epoch, no busy helper restart; #989/#997 |
| New sign-in during work | No account in fixture | Account/principal isolation and ownership reconciliation; #989/#997 |
| Four manifest keys | Exact upstream method harness | Actual format detection and URL/signature from each installed architecture; #996 |
| Wrong package/architecture/signature/metadata | Final [OpenSSL twelve cases](receipts/install-x11-schema.json) and Tauri seventeen cases on [Wayland](receipts/tauri-install-wayland-schema.json)/[X11](receipts/tauri-install-x11-schema.json), including expected-helper digests and bounded expansion/owner/mode rejection | Exact installed bytes verified with owner release public key; #996 |
| Source substitution after verification | Both signature suites passed original-file replacement after root verification | Audited privileged installer across complete TOCTOU boundaries; #996 |
| Missing/denied polkit | Final Tauri password prompts passed on [Wayland](receipts/tauri-install-wayland-schema-prompt.json)/[X11](receipts/tauri-install-x11-schema-prompt.json); final Wayland [cancel](receipts/tauri-install-wayland-schema-cancel.json)/[masked authority](receipts/tauri-install-wayland-schema-polkit-missing.json) preserved helper; earlier X11 dismissal and denied-rule fixture also observed | Actual product missing-agent/authority, denied and cancelled prompts; no sudo/password fallback; #996/#997 |
| Interrupted dpkg transaction | Not tested | Distribution database and helper recovery without extra claimant; #996 |
| Offline per-user uninstall | Fixture cleanup preserves sibling sentinel | Fence/reconcile, disable unit, remove owned helper/registration credentials, preserve provider files/repos; #989/#996 |
| SBOM / actual WebKitGTK runtime | No webview bundled | deb distro version; AppImage bundled runtime/SBOM, rebuild owner #996; #998 release repetition |

## Additional signature-compatibility probe

[The separate Tauri-signature probe](tauri-signatures.md) compiled the exact pinned updater
verification functions against its locked minisign/base64/semver crates. It uses a new
disposable key/action namespace and requires authenticated version binding. It preserves
all OpenSSL receipts above; seventeen privileged cases passed in each session with the exact upstream
verification functions. This resolves the synthetic-key format/verification mechanism gap,
while actual product integration and owner key custody remain unproven. It is not a full
installed Tauri updater test.

## Admission impact

Do not admit dependent production package/update work on stock updater behavior: the
pinned source proves a forbidden deb fallback and lacks privileged verification. The
fixture offers a bounded path to investigate replacement of that install step; it now
demonstrates Tauri-signature compatibility with synthetic keys and actual interactive
polkit/session primitives in separate fixtures. It does not resolve four installed
format/architecture selections, integrated product lifecycle or production crash recovery.
LINUX-20261016 must disposition these gaps explicitly. #1030 receives observations through
the coordinator only, then #1031 imports approved contracts for #994/#996. No reverse
dependency on those cards is required for these independent mechanism probes.

## Final disposable cleanup

The [cleanup receipt](receipts/cleanup-final.json) verifies removal of the test root
installers, polkit actions/rules, packages, session unit and synthetic private signing
keys. [Package-manager output](receipts/package-cleanup.txt) and the
[unit cleanup](receipts/session-cleanup.json) are preserved. The restricted disposable
SSH key was removed while preserving other authorized-key bytes; its host temporary
key directory was also removed. Polkit was restored, idle delay restored to300 seconds,
and user/provider data plus the original locked login keyring were preserved.
