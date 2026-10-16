# Provider mechanism observations — #982

These are bounded pre-product observations for LINUX-20261016, G2/G6 and P18,
not a provider catalog, capability contract, product adapter or release acceptance.
No provider account was signed in, no model request was sent, no owner's installation
was changed, and no paid execution is authorized by this receipt. LINUX-16/17 must
repeat applicable cases with final product packages. Coordinator hands observations
forward to #1030 → #1031 → #994/#996; those cards are not dependencies of this spike.

## Provenance and differences from the reference

The reference is merged Mac SHA
[`3cc71216e3ca05090e90c5f09a56350b065acdcd`](https://github.com/yuric/campus-macos/tree/3cc71216e3ca05090e90c5f09a56350b065acdcd),
`Sources/CampusBrokerCore/Engine.swift` and `CLIUpdate.swift`. Read via `gh api
repos/yuric/campus-macos/contents/<path>?ref=<sha>` on 2026-10-16. These files
bind Claude, Codex, Gemini, agy and Grok Build. Grok Build is xAI's CLI; the
similarly named third-party `superagent-ai/grok-cli` is not this reference.

The updater accepts operations for Claude, Codex, Grok and agy, not Gemini.
Its verification is `/usr/bin/codesign` with Apple team identity and its sandbox
is Seatbelt. Neither proves Linux authenticity or isolation. Linux must not reuse
`expected_team_id` as evidence. The reference recognizes native version directories
for Claude, a Grok downloads symlink, in-place agy, and the Codex npm tree. It
coordinates updater/install leases and copies a previous install for restoration;
those are source facts, not measured Linux behavior.

[Probe pins](../../../spikes/982/providers/pins.json) capture exact package versions,
URLs, metadata digests, archive SRI, registry signature fields and the agy manifest.
Registry/manifest versions observed on 2026-10-16 are Claude 2.1.301, Codex
0.163.0, Grok 1.0.60, agy 1.4.0 and Gemini 0.64.0. The four native binaries
were subsequently executed in the guest as recorded below; the separate pinned
Gemini npm install also completed offline version/help execution as detailed below.
Pin presence alone is not executable availability evidence.

## Available integrity mechanisms

Claude's [official setup documentation](https://code.claude.com/docs/en/setup)
publishes signed release manifests and signing fingerprint
`31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE`. In a fresh private GPG directory,
we checked that fingerprint and verified the 2.1.301 manifest signature successfully.
The [raw verification receipt](../../../spikes/982/providers/claude-signature-receipt.json)
records source digests, command and GPG output. Reproduce with
`python3 spikes/982/providers/verify_claude_signature.py`. Its Linux arm64 binary SHA256 is
`1e119036a802d359ba5f9886428e031586e8796f7a858d5a8ee179ac7b8604f0`;
the downloader enforces that hash in addition to npm SRI. This verifies a public
vendor signature; no private release key was generated. The native installer URL
returned HTTP 403 from this host; it was not executed.

For Codex/Grok packages, npm's per-version metadata supplied SRI and registry
signature fields. We record those signatures but have not verified them or
publisher provenance. Registry TLS plus SRI detects corruption relative to that
metadata; it does not alone establish independent publisher identity. For agy,
the fetched installer verifies SHA512 from its HTTPS manifest. An independently
signed manifest/key was not found in that observed installer. No trust downgrade
is approved; these paths remain blocked for a production updater.

Downloaded installer source observations (not executed):

| Source | SHA256 | Observation |
| --- | --- | --- |
| `https://x.ai/cli/install.sh` | `7fd6fdc75d9418b2e58356726fcbf1ae849416f773925da07d0ccc7a60d3e791` | Exact version argument; `linux-aarch64`; `.grok/downloads/grok-linux-aarch64` plus `.grok/bin/grok` link; temporary payload/version check then rename; no checksum/signature verification in the captured installer. |
| `https://antigravity.google/cli/install.sh` | `62966c07365423bd4dc209355060744058fb30d60f5323e2d360e39de64e5042` | `linux_arm64` manifest; SHA512; archive member `antigravity`; target `.local/bin/agy`; background updates advertised. |

## Update and credential evidence matrix

Every row below distinguishes an observed source mechanism from an actual completed
Linux test. Manual instructions do not constitute a delivered update action.

| Reference path | Fixed vendor operation / recovery candidate | Remaining required observations |
| --- | --- | --- |
| Claude native | Actual vendor `install 2.1.300` → `install 2.1.301` → `install 2.1.300` and two concurrent fixed 2.1.301 installs completed with signed binary hashes verified at every stage. | Active-model-run/install races, corruption and mid-promotion interruption remain unproven; Linux token file/keyring behavior, refresh/cancel and two-account isolation remain open. |
| Codex npm | Version 0.163.0 actually exposes `codex update` with update-specific help. Exact npm version installation is a separate candidate for restoring a complete previous dependency tree. | Help proves command recognition, not successful update. Complete npm layout, provenance, old/new dependency closure, concurrency and recovery remain untested. |
| Grok native | Observed 1.0.60 help exposes `grok update --version <VERSION>`, `--force-reinstall` and `--check --json`. Save entire resolved install plus launcher before mutation. | Help proves version-selectable syntax. Artifact authenticity, actual selection/install, running-image/launcher replacement, previous-version recovery and concurrent update/active-run safety remain unproven. |
| agy native | `agy update` is documented. Installer manifest provides a versioned payload URL. | Version selection/rollback support, authenticity beyond same-origin checksum, update/background-update races, Linux storage, refresh/cancel and account identity scope. |
| Gemini API-key | No update action in the pinned Mac adapter. Pinned 0.64.0 npm bundle installed offline with Node24.22.0 arm64; version/help returned0 with optional native addons omitted. | Actual API-key handling/deletion, cancellation, native addon behavior and authentication remain unproven. Scoped project-temp-file creation does not prove OAuth isolation. Never count agy OAuth evidence as Gemini API-key evidence. |

[Official Codex authentication documentation](https://developers.openai.com/codex/auth)
states `CODEX_HOME` scopes file credentials; storage mode can be file, keyring,
auto or ephemeral. Auto can fall back to a file. This concerns provider-owned
credentials, not Campus tokens. Refresh is documented but not exercised here.
[Official CLI guidance](https://developers.openai.com/codex/cli) describes Linux
installation and updating; the reference's npm layout must be verified separately.

[Antigravity installation/authentication](https://antigravity.google/docs/install?tab=cli)
describes Linux keyring and SSH-dependent login behavior. It does not prove two
accounts are isolated. The pinned Mac binding has **no config-dir variable**;
a separate working directory remains insufficient evidence. This spike must not
claim isolation until actual Linux stores and account switching are observed.

[Grok enterprise documentation](https://docs.x.ai/build/enterprise) distinguishes
native updater download hosts from its npm distribution. Neither proves rollback
or concurrent-install safety. [Gemini installation](https://geminicli.com/docs/get-started/installation/)
and [authentication](https://geminicli.com/docs/get-started/authentication/) provide
its own runtime and API-key paths. The separate offline runtime probe below does
not establish authentication or optional native addon behavior.

## Actual arm64 execution receipt

[Captured command receipt](receipts/providers/captures/receipt.json) records Linux
`6.8.0-142-generic`, `aarch64`, host `lima-campus-linux-d5-noble-arm64`, UID 1000,
and a network namespace containing only loopback. These are extracted binary
probes under `/home/campusqa/spike982/provider-binaries`, not installed vendor
package or Campus package acceptance. The environment excluded session bus,
SSH forwarding and all inherited credentials. No command timed out or had its
capture truncated in this run.

| Binary | Actual observation | Limit |
| --- | --- | --- |
| Claude | [`--version`](receipts/providers/captures/claude/command-00.txt) printed `2.1.301 (Claude Code)`. [`auth status`](receipts/providers/captures/claude/command-02.txt) returned structured `loggedIn: false`, `authMethod: none`, and the exact supplied `CLAUDE_CONFIG_DIR` path. | Observes logged-out state and config-directory selection. No valid OAuth token store, refresh or two-account isolation was exercised. |
| Codex | [`--version`](receipts/providers/captures/codex/command-00.txt) printed `codex-cli 0.163.0`. The deliberately invalid synthetic key supplied on stdin was accepted by local `login --with-api-key`; `login status` then reported an API-key login. | Network was absent, so this was local cache behavior, not provider authentication. Exit 0 and positive status cannot establish a working account. |
| Grok Build | [`--version`](receipts/providers/captures/grok/command-00.txt) printed `grok 1.0.60 (01a8e1c591c0)`. Login help exposed device and OAuth options; update help exposed exact version selection. | No login, token store, refresh or two-account isolation was exercised. |
| agy | [`--version`](receipts/providers/captures/agy/command-00.txt) printed `1.4.0`. Update help printed `Usage of update:`. | No keyring/OAuth identity or isolation claim. |

Codex's [local login output](receipts/providers/captures/codex/command-03.txt),
[status output](receipts/providers/captures/codex/command-04.txt) and
[logout output](receipts/providers/captures/codex/command-05.txt) must be read
together: they used an intentionally invalid synthetic credential, and logout
reported local deletion. The final [file inventory](receipts/providers/captures/codex/filesystem.json)
contains `scope/config.toml` and a `scope/log/codex-login.log`, with no `auth.json`.
The probe did not capture the intermediate auth file, so it does not prove its
contents or permissions. Status exposed masked key fragments even for this fake
key; production must not forward provider auth output to logs or transcripts.
The CLI also refused to create helper aliases because the test set `TMPDIR` to
the private test home. This is a known constraint of this receipt, not a product
installation result.

The dedicated [Codex update help](receipts/providers/captures/codex/command-06.txt)
explicitly identifies `Usage: codex update [OPTIONS]`; it is not generic prompt
help. [Grok update help](receipts/providers/captures/grok/command-03.txt) establishes
accepted exact-version syntax only. agy 1.4.0's [general help](receipts/providers/captures/agy/command-01.txt)
now advertises `json`/`stream-json` output, unlike the older pinned Mac source's
prose-only commentary. This observed delta needs producer/contract reconciliation;
it does not authorize silently changing the Linux binding.

Per-binary archive/member/digest receipts are retained for
[Claude](receipts/providers/claude/artifact.json),
[Codex](receipts/providers/codex/artifact.json),
[Grok](receipts/providers/grok/artifact.json), and
[agy](receipts/providers/agy/artifact.json). Grok's official npm payload was
`package/bin/grok.br`, decoded through the guest's existing Brotli library after
archive-integrity verification.

### Bounded actual updater-failure follow-up

`spikes/982/providers/update_failures.py` copies these verified binaries into
fresh, explicitly synthetic native-shaped layouts, then invokes two actual
vendor updater commands concurrently with networking removed. The original
extracted binaries and a synthetic user-data sentinel are hashed before/after.
It invokes Claude/Codex/agy `update`, and Grok `update --version 1.0.59` to
observe the failure of an older-version request without network access. Command
output, timeout, exit value, launcher resolution and hashes are receipts; exit
values are not interpreted as provider success.

```sh
sudo unshare --net runuser -u campusqa -- python3 /absolute/path/update_failures.py /home/campusqa/spike982/provider-binaries
```

The actual [offline failure receipt](receipts/providers/update-failures/receipt.json)
contains two concurrent commands per binary. Claude returned 1 after 2.405/2.623
seconds, Codex returned 1 after 0.030/0.025 seconds, agy returned 1 after
0.425/0.422 seconds, and both Grok commands exceeded the 20-second bound and were
killed (return -9). All four launchers still resolved inside their disposable
layouts; executable, original source and synthetic user-data hashes were unchanged.
Claude's capture reports failed DNS/version fetch after recording its native
installation method; agy's capture reports an unreachable manifest endpoint.
Codex's capture says it could not detect the installation method and directs
manual updating, so its failure does not exercise an npm update transaction.
Grok's timeout is an observed bounded failure, not a completed updater or rollback.
These runs cannot establish successful update, actual previous-version recovery,
active-provider-run safety or a vendor-created install. Codex's reference
npm installation is explicitly not reproduced by the standalone layout. No
manual file promotion is substituted for a delivered, authenticated vendor action.

### Online signed Claude fixed-version follow-up

`spikes/982/providers/claude_transitions.py` and its
`claude-transition-pins.json` define a bounded actual vendor-command experiment:
verify both 2.1.300/2.1.301 manifest signatures against the same published
Anthropic public-key fingerprint, run `claude install 2.1.300`, then fixed-version
2.1.301 upgrade and 2.1.300 recovery, followed by concurrent 2.1.301 installs.
Every completed stage checks installed bytes against the signed manifest, exact
reported version, launcher containment and synthetic user-data preservation.

The new 2.1.300 arm64 binary is 266,264,568 bytes. To respect the incremental
500 MB guest-storage limit, the probe reuses the already verified 2.1.301 binary
through a hardlink into its fresh version cache. It records this explicitly;
the 2.1.301 stages prove the vendor's fixed-version selection/promotion of cached
bytes, not a second network download. An allocation guard aborts above 450 MB,
leaving a 50 MB margin; individual file growth is kernel-limited to 300 MB.
Public metadata/network failures stop the experiment without a trust downgrade.
The parent separately checks the host's 35 GiB free-space floor.

The first actual attempt validated both signatures, then was deliberately killed
by the 450 MB allocation guard after 5.245 seconds, with observed allocation
461,590,528 bytes and installer return code -9. This is a failed/aborted install,
not a pass. The accounting already excluded the existing 2.1.301 inode; there is
no evidence that the extra allocation was simply that hardlink counted twice.
The coordinator subsequently authorized up to 1 GiB incremental space on the same
guest with host space observed at 43 GiB. Safe resume preserves the first receipt
and logs under `history/`, charges existing partial-download files against the
same total, and emits per-inode allocation inventories. It also conservatively
charges filesystem free-space loss to catch unlinked but still-open staging files.
The 1 GiB option stops at 960 MiB, retaining a 64 MiB margin. No threshold is
silently relaxed, and no prior failure becomes a successful transition.

The [first aborted receipt](receipts/providers/claude-transitions/history/receipt-1792149423032141106.json)
and [installer capture](receipts/providers/claude-transitions/history/1792149423032141106-install-2.1.300-0.txt)
are attached, with hashes verified against the resumed receipt. The
[before](receipts/providers/claude-transitions/allocation-before.json) and
[after](receipts/providers/claude-transitions/allocation-after.json) allocation inventories
are also attached. These list disposable paths and inode allocation; provider homes and
credential contents were not copied.

```sh
python3 claude_transitions.py /home/campusqa/spike982/provider-binaries \
  --resume --incremental-budget-bytes 1073741824
```


```sh
# Online public artifact download is authorized; no login or model request.
python3 claude_transitions.py /home/campusqa/spike982/provider-binaries
```

The [resumed actual receipt](receipts/providers/claude-transitions/receipt.json)
completed all four stages: initial 2.1.300 install (10.715 seconds), 2.1.301
upgrade (5.446 seconds), 2.1.300 recovery (6.2 seconds), and two concurrent
2.1.301 installs (5.6 seconds observed for the pair). Every stage resolved the
launcher to the expected version directory, matched the signed manifest hash,
reported the requested version, and preserved both the synthetic sentinel and
original bootstrap binary. Observed peak charge was 994,177,024 bytes; final
charge was 727,924,736 bytes. These fit the explicitly increased 1 GiB budget.
The prior aborted attempt remains preserved in the receipt's `prior_attempt_preserved`
paths; it is not overwritten as a pass. This proves this bounded vendor-native
fixed-version installation/recovery mechanism and concurrent installers only,
not active-model execution during update or a delivered Campus update action.

The command runs as `campusqa` with fresh HOME/config and an allowlisted
credential-free child environment. Its output is
`claude-transitions/receipt.json` and raw installer output. The attached receipt establishes these measured stages; it does not establish
product-package release acceptance. Active model execution during update, credential
refresh, other installer layouts and a delivered Campus update action remain
separate evidence even if all transitions succeed.

## Reproducible bounded execution

### Separate Gemini API-key CLI availability follow-up

[gemini_probe.py](../../../spikes/982/providers/gemini_probe.py) and its adjacent
[package input](../../../spikes/982/providers/gemini-package.json) and
[npm lock](../../../spikes/982/providers/gemini-package-lock.json) prepare an
isolated Gemini 0.64.0 availability test, distinct from agy. Host disk pressure
initially paused payload downloads. The first guest download later verified
Node's signature and exact archive checksum, then stopped at a defect in the
probe's npm key-fingerprint calculation before downloading Gemini. It retained
30,963,083 bytes and did not establish Gemini runtime availability.
Its two phases verify Node 24.22.0 Linux arm64 against the Node project's signed
checksum manifest and signer fingerprint
`C82FA3AE1CBEDC6BE46B9360C43CEC45C17AB93C`, then Gemini's pinned SHA512 SRI and
npm registry ECDSA signature. The [Node release-key procedure](https://github.com/nodejs/release-keys)
and [npm signature format](https://docs.npmjs.com/about-registry-signatures/)
are the verification sources. An npm registry signature is not independent
Google publisher provenance. Verification failures stop the probe; no trust
downgrade or product updater acceptance is implied.

The [key-encoding diagnosis](../../../spikes/982/providers/gemini-keyid-receipt.json)
shows the same published P-256 key has DER SHA256
`fb190a462123443500cbcdb6519623e7179e9f38d84ad4e9362b72d2b68b62c1`, while its
SSH public-key wire encoding yields npm's published key ID
`SHA256:DhQ8wR5APBvFHLF/+Tc+AYvPOdTpcIDqOhxsBHRwC7U`. Hashing DER directly as
the key ID was the probe error. The corrected script pins the complete DER
digest and verifies its SSH fingerprint before verifying the ECDSA signature.
An independent metadata-only OpenSSL check returned `Verified OK` for the pinned
Gemini package signature. This is a verifier correction, not a bypass; it still
does not verify Google publisher provenance. `download <same-dir> --resume`
preserves the failed receipt, rehashes reusable downloads and repeats signature
verification. The corrected guest download subsequently passed verification.
The first offline attempt ran Node but stopped at `npm --version`: assigning
both user and global config to `/dev/null` made npm reject loading the same
config file twice. This is a second probe failure, not Gemini availability.
The corrected offline resume preserves that capture and creates distinct empty
0600 npm configuration files in a new private HOME, with fresh install/cache/scope
directories. Before reusing Node it compares every regular file and symlink plus
the entire extracted inventory against the verified signed archive; altered or
additional files fail closed.

The [corrected offline resume](receipts/providers/gemini/captures-offline/receipt.json)
completed all six commands with exit 0: Node version
(0.163 seconds), npm version (0.152 seconds), local tarball cache import
(3.921 seconds), `npm ci` (2.770 seconds), Gemini version (1.067 seconds) and help
(1.057 seconds). It ran as UID1000 on the named arm64 guest with only loopback.
All 4,797 regular files and three symlinks in the reused Node extraction matched
the signed archive before execution. Node binary SHA256 was
`719a43d185f3b6a59d8fcbba1ff06b93c75f76fb0bb9916f81d33921615d4cb5`; the installed
Gemini entry SHA256 was
`ab113d84c8f1692fd6c95081366718897876d8664328c7bf0ccf9437d688145f`.
The final/peak observed file-size sum was 371,098,036 bytes, below the 600 MB
probe budget. This establishes bounded executable availability for this isolated
bundle/layout, not a working provider account. Exact captured output was
[`v24.22.0`](receipts/providers/gemini/captures-offline/node-version.stdout),
[`11.19.1`](receipts/providers/gemini/captures-offline/npm-version.stdout), and
[`0.64.0`](receipts/providers/gemini/captures-offline/gemini-version.stdout) for
Node, npm and Gemini respectively. npm reported one added package; all six
successful command stderr files were empty. Gemini's
[actual help](receipts/providers/gemini/captures-offline/gemini-help.stdout)
exposes text/json/stream-json output and its normal launch options, with no
dedicated updater command listed. Help recognition is not feature execution.

The supplied `GEMINI_CLI_HOME` received four `.gemini/projects.json.<UUID>.tmp`
filenames during version/help; the receipt lists their names only. Those are not
observed token files, proof of secure token storage or account isolation. No
credential was supplied, and no project-file contents or HOME/scope/cache files
are handed off. The 34 allowlisted files comprise successful download/offline
captures and the two failed-attempt capture directories; no entire provider home
is part of the evidence transfer. The
[successful download](receipts/providers/gemini/captures-download/receipt.json),
[registry signature verification](receipts/providers/gemini/captures-download/registry-signature.stdout),
[original fingerprint failure](receipts/providers/gemini/captures-download-failed-1792151308937335563/receipt.json)
and [original npm configuration failure](receipts/providers/gemini/captures-offline-failed-1792151496029361731/receipt.json)
remain separate receipts.

The local lock was resolved with npm 10.9.8 using `--package-lock-only
--ignore-scripts --omit=optional --no-audit --no-fund` in an isolated temporary
directory. It contains 13 entries, including optional addons that the actual
install omitted. Gemini's pinned package bundles its JavaScript and declares
no mandatory external dependency. The guest phase uses the pinned Node runtime,
an empty HOME, private npm cache, offline `npm ci --ignore-scripts --omit=optional`,
and only `--version`/`--help` execution inside a network namespace with loopback.
Native keytar and terminal addons are deliberately omitted: this test cannot
prove OAuth/keyring storage or full interactive execution. Neither phase supplies
a credential or calls a model. The combined download/expanded/cache file-size
budget is 600 MB with a 10 MB stop margin; the parent separately maintains the
host's 35 GiB floor before authorizing any download.

```sh
# Run only after parent resource-floor authorization; fresh owned guest directory.
python3 gemini_probe.py download /home/campusqa/spike982/gemini-api-key
sudo unshare --net runuser -u campusqa -- python3 /path/gemini_probe.py offline /home/campusqa/spike982/gemini-api-key
```

The [vendor installation page](https://geminicli.com/docs/get-started/installation/)
documents npm installation. Exact package selection through npm and restoration
of a prior complete lock are candidates, not measured updater/recovery actions.
Gemini has no update action in the pinned Mac adapter. This probe adds no offered
update path or product dependency and establishes no previous-version recovery,
active-run/install concurrency, API-key authentication, refresh or two-account
isolation. The existing archive/cache contains only version 0.64.0; it cannot
establish an old→new→old transition without a separately verified second version.
Reinstalling those same bytes could test same-version repair only and must not be
called previous-version rollback. No such repair probe has been run. The two
preserved failed attempts remain distinct from the successful
availability run; none is an update/rollback or authentication acceptance receipt.

### Native extracted binary probe

Copy `spikes/982/providers/{probe.py,pins.json}` into the disposable guest. Download
as the disposable user into a new directory, then run with network removed:

```sh
python3 probe.py download /var/tmp/campus-982-provider-binaries
sudo unshare --net runuser -u campusqa -- python3 /absolute/path/probe.py offline /var/tmp/campus-982-provider-binaries
```

The download directory must belong to `campusqa`, and the script/pins must be
readable by it. `download` verifies existing receipts/hashes on resume, rejects nonempty unreceipted
partial directories, and decodes Grok’s regular `package/bin/grok.br` member using
the guest’s existing `libbrotlidec`; a missing decoder is a blocked probe. It does
not execute payloads and can instead run in host
staging before transfer. `offline` refuses root, non-Linux/non-arm64 and network
namespaces containing anything except loopback. It starts fresh private homes,
an allowlisted environment, closed inherited FDs and bounded commands. It runs
version/help, empty Claude auth status and a deliberately invalid synthetic Codex
API key passed over stdin, then logout. No real OAuth flow or inference is started.
Captures preserve exit values as raw observations without interpreting domain
success. The fake API-key file operation is **not** subscription login, token
refresh, account isolation, a successful provider request or production acceptance.

`captures/receipt.json`, bounded command text, file-name/mode inventories and
per-artifact receipts are the output. Retain source/head and tuple metadata when
copying them into the coordinator's capture bundle. The probe intentionally uses
an extracted binary layout and does not pretend that layout is a vendor install.

Before marking any offered update action proven: install two exact vendor-supported
versions into a disposable guest layout; authenticate both old/new artifact bytes;
record initial hash/layout; hold a synthetic process against the old image; race
update/update and update/launch; interrupt download/staging/promotion; corrupt the
payload and manifest; deny writes/run out of space; recover the old version; prove
credentials and repository sentinels remain unchanged. Record absence of a
trustworthy mechanism as blocking, not a manual workaround. Real refresh and
account-isolation probes need separately authorized disposable accounts and must
not copy owner credentials into these homes or logs.

## Post-capture source and receipt review

The provider harness self-review found and corrected two Claude transition-script
defects: a failed receipt could still yield shell status 0, and version inspection
executed the installed binary before rejecting a signed-manifest hash mismatch.
The current script rejects mismatched bytes before execution, returns nonzero for
failed completion, and lets final preservation/allocation checks fail completion.
The recorded successful stages all independently contain matching signed hashes,
exact versions and intact source/sentinel; the first allocation abort was already
recorded as `completed: false` and remains a failure regardless of its old wrapper
exit status. These corrections were source-reviewed and syntax-checked after the
captures; the old captures do not test the new refusal branches.

The native offline harness now labels observation completion separately from
provider authentication/update success and fails its wrapper on timeout or
truncation. The updater-failure harness explicitly records that no update/rollback
was proven, and fails its wrapper if source/install/sentinel preservation fails.
Nonzero vendor outcomes in these deliberately negative probes are raw observations,
never domain-success mappings. Runtime harnesses now enforce the exact owned guest
hostname; Gemini additionally checks exact version strings and expected help entry
text. The native captures, Claude transitions and updater-failure receipts named in
the historical binding limit below lack a probe/script source digest. Gemini receipts
do contain historical digests, but the producing revisions are unavailable; neither
set proves execution against the current corrected harness bytes.

Receipt consistency review verified all four completed Claude transition records,
their final preservation/allocation checks, all four offline updater preservation
records, all 18 native captures without timeout/truncation, and Gemini's six
successful commands and exact printed versions. No valid account credential or
model call appears in this test scope. The deliberately invalid Codex key's local
cache acceptance and masked output remain explicitly synthetic, not authentication
proof. Core dumps are disabled for future native observation children as an
additional bounded-probe safeguard; arbitrary provider crash-collector behavior
remains governed by the separate security evidence and is not proved here.

## Additive coordinator review, 2026-10-16 12:23 UTC

Card comment 10452 records an independent public-only review and coordinator reproduction:
all four recorded Codex/Grok npm registry signatures verified under the already pinned
npm key, with wrong-version controls rejected. The report and raw verification are coordinator-held evidence referenced by comment
10452, not independently reproducible files delivered in this PR.
This supplements the historical captures; they are not rewritten. It establishes registry
authenticity, not publisher identity or fresh archive-byte verification. Codex metadata
contains a matching Sigstore provenance bundle, but full verification was still pending
at this handoff. Grok has no observed attestation and agy has only a checksum. No trust
downgrade, account proof, update acceptance or release acceptance follows from this review.


## Historical execution-source binding limit

The historical `providers/captures/receipt.json`, `claude-transitions/receipt.json`
and `update-failures/receipt.json` do not record `probe_sha256`. The current committed
probe is a reproduction candidate, not a proven byte-identical execution source for
those runs. Their recorded tool/artifact/output hashes remain observations, but the
execution-source binding is **unproven**; later source fixes cannot retroactively bind
them. These receipts must not be admitted as current-source mechanism proof. Future
recapture must bind the actual executed script and inputs. No historical source hash
is invented and the raw receipts are preserved.

Gemini's retained download/offline receipts record historical `probe_sha256` digests,
but those producing source revisions are not retained in this repository and differ
from the current committed `gemini_probe.py`. Their output/artifact observations
remain; execution against the current committed probe is unproven. This is unavailable
producing source, not an absent digest. No historical hash is backfilled or replaced.

`spikes/982/providers/pins.json` is the historical 10:53 UTC inventory; its Gemini
“not installed” status predates the later Gemini install receipts described above.
Its Claude “independently verified” wording means cryptographic manifest verification
with a vendor HTTPS bootstrapped key, not independently authenticated publisher identity.
