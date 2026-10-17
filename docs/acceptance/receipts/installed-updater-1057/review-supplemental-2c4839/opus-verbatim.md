I read the actual files and found no P1 or P2 problem. There is one P3 accuracy fix in the acceptance document. This is a supplemental, read-only consultation, not Council, human approval or merge authorization. I executed nothing and did not use Git, so hashes were not recomputed and the gzipped patch and archive were not read.

## A. Verdict

**One [P3] finding, no [P1]/[P2].**

**[P3] Stale "docs-only" claim with no commit attached**
- **Where:** `docs/acceptance/installed-updater-1057.md:1109-1112`, next to the "110 tests total / Current commands" block at `:1091-1107`.
- **What it says:** "The docs-only follow-up under direction1316 changes no source, helper, validator or raw receipt bytes. The 110-test result above belongs to source4001; those tests were not rerun for the documentation-only head."
- **Why it's wrong now:** The current head sits on branch `…/1057-docs-1316` and contains source commits after 4001: `7ecfc68` (the gate), `2928729` and `1329e15`. The same document says so itself: 108 probe tests at 1329 (`:82-111`) and source-only work from `81cd32e` (`:133-160`).
- **Consequence:** Someone reviewing 2c4839 could conclude that no source changed since 4001 and that 110 is the current count. This is an evidence-accuracy defect, not a code defect.
- **Fix:** Name the commit that sentence describes, and point the "current" pointer at the 1329 result (108 probe + 10 adapter + 49 repository = 167 tests).

### Checked and not raised as findings
- **`hosted/run.sh`.** The only change since 113a, per the packet (I could not check this without Git), is `:6`, which runs the 10 adapter tests before the probe tests.
  - `test_adapter.py` loads `install-deb.py` by file path, needs no root, network or Node, and works on Linux. Nothing has to be installed.
  - Its cost is seconds, inside the existing limits: 60-minute job, 2400 s build and 900 s smoke timeouts, `--cpus/--memory/--pids` caps, smoke run with `--network none`.
- **Token isolation holds.** The workflow uses `pull_request` (not `_target`) with `contents: read`. Actions are pinned by SHA, `persist-credentials: false` is set, and there are public-only guards. The container gets a `git archive` copy with no `.git`, only the `GITHUB_ACTIONS`/`FIXTURE_*`/`EXACT_HEAD` environment variables, and no secrets. The private key stays on a `noexec` tmpfs at `/private` (`prepare-or-build.sh:21-27`).
- **Smoke container privileges.** `SYS_ADMIN` plus `/dev/fuse` widen nothing beyond what PR code already has on an ephemeral hosted runner.
- **Prior advisories are not reopened.** These are `timeout` without `--init`/`-k`, the unnamed smoke container, the path filters, and the 60 vs 40+15 minute budget. All are dispositioned in the 164d/113a records.
- **Authorization at the moment of use holds** (`install-deb.py:290-344`):
  - It requires root plus a decimal `PKEXEC_UID` above 0, and a root-only trust path at the moment of use.
  - Caller-owned files are opened with `O_NOFOLLOW` and copied once into a root `0700` staging directory.
  - The package hash is checked against the admission list before any parsing; then the signature is verified and the signed version must equal the package version.
  - The forward-version check runs under its own lock plus the dpkg frontend lock, and dpkg installs only the staged path.
  - The polkit policy is `auth_admin` for active sessions only, with a fixed `exec.path`. `main.rs:200-202` uses `--disable-internal-agent`, so there is no terminal fallback.
  - The AppImage replay concern was rebutted earlier with pinned upstream evidence. There is no new evidence, so it stays closed.

## B. Obligation dispositions (S1–S8, R1–R2)

| ID | Disposition |
|---|---|
| **S1** | I read the full current `run.sh`, workflow, prepare script, `main.rs`, `install-deb.py`, `bootstrap.py`, the policy, `test_adapter.py`, `ui/index.html` and the full acceptance document. The other 40 unchanged files are carried by byte identity (from prior-full-byte-coverage.json) together with the 1329/113a/164d verdicts, within those verdicts' own scope. **The patch file was not read** (gzip). Result: P3 above only. |
| **S2** | I inspected all 38 receipt PNGs and the icon, and read the startup5 disposition, review, handback, correlation and desktop receipts. Startup5 claims match the raw data: exit 127 with "Not authorized", `status: not_certified`, `session_binding: coordinator_review_required`, `exact_logind_session: false`, `screenshot: null`. Monotonic order holds: candidate → reject (462977169 µs) → app finish (463041489045 ns) → restore (463183756779 ns) → reap. The 1285/10908 denials remain failed; the first Phase B cancel remains incomplete. Not laundered. |
| **S3** | No new code defect. The 1329 NO_FINDINGS is carried only within its lifecycle-delta scope and is not counted as a whole-PR clearance. |
| **S4** | Bounds and cost are acceptable; see A. No new resource is provisioned. |
| **S5** | Security source reviewed as in A. No exploit path found. |
| **S6** | Staging, admission, signature, package and privilege-at-use are intact. CI privilege boundary unchanged. No production-key prerequisite added. |
| **S7** | Privacy: all 38 frames show only the disposable `campusqa` account, empty password fields and no credentials; the QMP canary is synthetic text. A regex scan of all receipt text found no private keys, tokens, emails or password hashes. Getent output shows only disposable accounts. Remaining low-risk exposure: host paths under `/Users/yuri/...`, the Lima ssh port, the VNC display and the identity-file *path* (not its content) appear in public receipts (`final-handback.json`, `root-correlation.json`, about 20 files). This is not a secret; owner discretion. |
| **S8** | `ui/index.html` is static, with no JS, buttons or form. The window opens only when there are no arguments (`main.rs:265-267`), and updating is CLI-only (`:248-264`). **No in-app cancel, retry or keyboard flow exists**, so none was tested. The Phase B "cancel retry" was a re-run of the driver, not an app retry. The app gives cancel, deny and missing authority the same generic refusal; per `desktop-final.json:901` the case labels are operator observations. Frames show the prompt wording matching the policy `<message>` exactly, and the password entry highlighted with a caret (one frame each in cancel, cancel-retry and 10908). That is a single-frame observation of initial focus, **not a keyboard or focus test**. This is a bounded gap, not a product requirement. |
| **R1** | Adversarial check of authorization at use, fixture confinement, evidence custody and the CI privilege boundary. No exploit. Custody hashes and inodes are recorded; I did not recompute them. |
| **R2** | The same review, recorded separately. I traced the execution path through the app (`main.rs`), pkexec, the adapter and dpkg, plus the AppImage branch. No new finding. The gated lifecycle (`gated*.py`, `desktop.py`, `authority-window.py`) was **not re-read**; it is carried from the 1329/2928 packets. |

## C. What I read, inspected and carried

- **Packet:** COVERAGE.md, prior-full-byte-coverage.json, and the 1329 verdict, adjudication and report; the 113a verdict and report; the 164d verdict and report.
- **Checkout:** the files listed in S1, plus
  - `test_marker_bridge.py:90-104`;
  - grep over probe tests for platform/Node dependencies (Node is required; paths use `resolve()`);
  - startup5 `coordinator-acceptance.json`, `independent-review.md`, `final-handback.json`, `root-correlation.json` (full), `desktop-final.json:120-160` and `:830-902`, `fresh-identity-space.json`, and part of `fresh-nss-data.json`;
  - privacy and secret regexes across all receipt text.
- **Images:** the Read tool rendered the pixels, so this is genuine visual inspection.
  - **startup5 (14):** attempt-visible-a, outcome-before-return, driver-waiting, driver-complete-before-return, driver-segment-a through e, gui-presence, qmp-canary, qmp-cleared, logout-observed, logout-gdm.
  - **activation-10908 (8):** all 8 frames listed for that run.
  - **activation-1285 (7):** all 7 frames listed for that run.
  - **authority-continuation (3):** all 3 frames listed for that run.
  - **phase-b (6):** all 6 frames, including guest/cancel and guest/cancel-retry.
  - **Icon:** `32x32.png`.
- **Not read or not verified:**
  - base-to-head.patch.gz, the archive, source-complete.txt, exact-head-files.json, PACKET-MANIFEST.json, actual-review-provenance.json, and prior records other than 1329/113a/164d.
  - The `run.json` indexes, `authority-final.json`, `journal-final.jsonl` (its rows were seen embedded in the correlation), and the other ~480 text receipts beyond the regex scans.
  - All SHA-256 values: none were recomputed.
- **Evidence still missing, which normal CI and Council must supply:**
  - The doc records no hosted Linux run at any head that has the current 108-test probe suite or `run.sh:6`. The last recorded run, at 5001e41, failed.
  - Exact-head CI on 2c4839, Council, and a different-family review remain with LINUX-20261016.