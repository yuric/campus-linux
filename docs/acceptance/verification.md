# Linux bootstrap verification and admission

Owner #981; next owner LINUX-20261016. Public visibility was verified through GitHub on
2026-10-16 after the coordinator's authorization/secret scan. Workers never change repository
settings, attach self-hosted runners or spend private hosted minutes.

## Commands and boundaries

Run from a clean committed head (the wrapper exports `git archive HEAD`, so uncommitted
changes are deliberately not tested). Both hosted architectures run exactly these commands:

```sh
python3 -B -m unittest discover -s scripts/tests -v
scripts/check-client-boundary.sh
python3 -B scripts/check_acceptance.py
python3 -B scripts/verify_repository.py
python3 scripts/verify-linux.py --arch arm64 --output /tmp/campus-linux-receipts
python3 scripts/verify-linux.py --arch amd64 --output /tmp/campus-linux-receipts
```

`verify_repository.py` also checks Markdown relative links and parses the legacy OpenAPI.
The Docker wrapper builds [Dockerfile.verify](../../ci/Dockerfile.verify), exports only
committed files, and mounts that export read-only with no credentials, network or Docker
socket in the test container. Limits: build timeout 900s, run timeout 600s, 2 CPU/2 GiB,
128 PIDs, 256 MiB temporary filesystem, dropped capabilities/no-new-privileges. Builds only
install repository-check dependencies; they do not compile a nonexistent product. Run
one local architecture at a time, keep the coordinator's 35 GiB free disk floor, and never
resize/prune/stop unrelated Docker workloads. A timeout/failure yields no success receipt.

Each receipt binds source head/archive hash, base digest, actual built image ID,
Dockerfile hash, architecture, exact command, result, log and installed-package hashes.
APT security updates can change the derived image ID; base digest plus recipe is fixed,
and the complete installed package versions are retained. Local/hosted receipts therefore
compare recipe/base/source and record actual image IDs rather than claiming bit-identical
APT rebuilds. No image is pushed to a public registry. Runtime libraries and product
lockfiles are not smuggled into the policy image.

The [toolchain lock](../../ci/toolchain-lock.json) selects Rust 1.99.1, Node 24.22.0 LTS,
Tauri 2.12.4, Tauri CLI 2.12.3, tauri-bundler 2.10.3, updater 2.14.0 and Vite 8.3.4,
verified against upstream release/package metadata on 2026-10-16. These exact versions
are inputs for #982/#988/#996, not a claim they were compiled together. Product owners
must use exact Cargo/npm versions, commit transitive lockfiles and checksum manifests,
and demonstrate compatibility before adding product commands to this lock. No `latest`,
caret dependency or auto-updated bundler binary is acceptable in a release receipt.

Upstream pin evidence: [Rust release manifest](https://static.rust-lang.org/dist/2026-10-15/channel-rust-stable.toml),
[Node 24.22.0 checksums](https://nodejs.org/dist/v24.22.0/SHASUMS256.txt),
[Tauri](https://crates.io/crates/tauri/2.12.4),
[Tauri CLI](https://crates.io/crates/tauri-cli/2.12.3),
[bundler](https://crates.io/crates/tauri-bundler/2.10.3),
[updater](https://crates.io/crates/tauri-plugin-updater/2.14.0),
[Vite](https://www.npmjs.com/package/vite/v/8.3.4).

## Required checks and skip rejection

Required exact names, including the existing checks:

- `Internal links resolve`
- `OpenAPI spec parses`
- `Client renders, API decides`
- `Linux policy x86_64`
- `Linux policy arm64`
- `Linux verification admission`

The new jobs use standard public `ubuntu-24.04` and `ubuntu-24.04-arm` runners, 20-minute
job timeouts, read-only contents permission, full-SHA actions and no path filters. They
check out the PR's exact head, not just an incidental merge commit. Admission runs with
`always()` when public, requires both job results to be `success`, downloads both receipts,
and checks their head/arch/base/image/recipe/source and artifact hashes. Missing downloads
fail too. Existing Docs jobs remain required; policy regressions still run on every
eligible PR, with the unchanged exact-file/hash D7 manifest.

A private repository schedules **no** hosted job, including admission, so it cannot incur
paid minutes. GitHub can consider a skipped required job successful for merge purposes;
therefore the coordinator's external read-only gate is mandatory even with branch
protection:

```sh
python3 scripts/check-linux-admission.py --pr PR_NUMBER --head FULL_HEAD_SHA
python3 scripts/check_acceptance.py --receipts RECEIPT_DIRECTORY --head FULL_HEAD_SHA \
  --results '{"verify_amd64":"success","verify_arm64":"success"}'
```

The first reads live GitHub visibility/head/check conclusions and rejects skipped, neutral,
cancelled, failed, pending or absent checks. The second verifies downloaded bytes; its
results argument must come from the observed run, never invented. The workflow supplies
that argument directly from `needs`. Neither command approves review/Council or merges.
The coordinator must configure/verify all six required names and prevent bypass under the
repository's review policy. This worker does not mutate branch protection. On 2026-10-16, `GET /repos/yuric/campus-linux/branches/main/protection` returned
404 “Branch not protected”, and `GET /repos/yuric/campus-linux/rules/branches/main`
returned `[]`. Enforcement is therefore an observed coordinator blocker, not assumed active.
An earlier REST rate-limit failure cleared on retry. Settings or GitHub availability
failures are explicit coordinator blockers, not reasons to bypass CI.
See [GitHub runner documentation](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

## Release-build baseline and ABI inventory

Verification: pinned `ubuntu:24.04` multiarch index, glibc 2.39. Release builds: distinct
pinned `ubuntu:22.04` index, glibc 2.35, native x86_64 and arm64, from
[Dockerfile.release-baseline](../../ci/Dockerfile.release-baseline). It installs actual
build dependencies and writes their package inventory; it does not manufacture a package.
22.04 is the selected oldest candidate with Tauri v2 WebKitGTK 4.1 in standard repositories,
following [Tauri's oldest-base requirement](https://v2.tauri.app/distribute/appimage/).
The arm64 dependency image was actually built successfully; its
[receipt](receipts/release-baseline-arm64.json) and
[full installed package inventory](receipts/release-baseline-arm64-packages.tsv) record
glibc 2.35, WebKitGTK 4.1 and the actual library versions. This is not a product build.
Compatibility remains unproven until #982/#996 build and inspect actual artifacts.

| Library/ABI | deb | AppImage | Required observation |
|---|---|---|---|
| glibc / dynamic loader | Host; maximum required GLIBC_2.35 | Host, never bundle glibc | `readelf --version-info` for every ELF; loader/NEEDED inventory |
| libstdc++ / libgcc | Baseline host dependency unless explicitly bundled | Inventory actual bundled/host choice | GLIBCXX/CXXABI maximum symbols from every ELF |
| WebKitGTK 4.1 / JavaScriptCore 4.1, libsoup 3 | Distribution packages | Bundled per D1, exact versions/SBOM | `pkg-config --modversion webkit2gtk-4.1`; inspect final package |
| GTK3 / GLib / GObject / GIO | Distribution packages | Inventory bundled closure | `dpkg-query`, `readelf -d`, dependency resolution in clean VM |
| Secret Service/libsecret, D-Bus | Host session/service; library package | Inventory library; service remains host | Absent/locked/unlocked real graphical session |
| Ayatana indicator / librsvg / SSL | Explicit package dependencies | Inventory actual bundled closure | No assumption based only on build headers |
| EGL/GL/Mesa/DRM, Wayland/X11 | Host graphics/session | Host interface; inventory any bundled shim | Actual renderer and loader paths; software gate |
| FUSE / AppImage runtime / linuxdeploy helpers | Not applicable | Exact runtime/helper hashes and host FUSE requirement | #996 must pin downloaded helper bytes; bundler version alone is insufficient |
| GStreamer/audio codecs | Actual audio feature dependencies | Bundle only needed licensed plugins | Permission/codec/SBOM/license proof; no unreviewed codec pack |

Build both formats on 22.04 and install those **same checksummed bytes** on 24.04. Before
advertising older-distro support, run the exact packages there too. #996 must record actual
ELF symbol ceilings, full library inventory, linuxdeploy/AppImage runtime hashes and
WebKit security-patch ownership. These are explicit unresolved artifact fields, not a
claim that every library listed above is already bundled. No release key is created here.

## Deferred real seams and handoff

`product_commands` is empty because the product does not exist. #988 adds actual host/API
and board build/tests; #989/#990 executor/CLI/IPC/outbox tests; #991–#994 UI/action/OS tests;
#995 real WebKit/bridge smoke tests under a virtual display; #996 package/update tests.
They extend this same image/command path with reviewed dependencies and executable seams.
A repository-policy receipt never substitutes for those tests or #982/#997 Lima receipts.

Environment support owns the named D5 Lima and UTM machines; the coordinator's
`planning/environment-plan.md` (outside this repo) is the provisioning authority. #982
must check in the proven Lima configuration/automation and actual software identities;
this bootstrap does not create another VM. [Visual criteria](visual-protocol.md) fix the
premeasurement bar and arrange every reference screen. First-user Ubuntu/CPU/GPU, paired
captures, producer/contract merges, ABI compatibility, product test commands and desktop
behavior remain explicitly unresolved. Public visibility is currently satisfied; required
branch-protection enforcement must be verified by LINUX-20261016 at merge.
