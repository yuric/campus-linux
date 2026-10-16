# S2 contract import receipt

Owner: #985; coordinator and next owner: **LINUX-20261016**. This receipt covers the
contract snapshot and repository checks, not product types, API deployment, live Linux
behavior, server client-pin admission or release publication.

## Immutable inputs and output

- Linux merged base: `37ef5d622da09cd7ba113dc0d1119e62e7378f84`.
- Server repository ID: `1311891398`, verified as `yuric/campus-server` through both
  `gh api repositories/1311891398` and `gh api repos/yuric/campus-server`.
  The old `yuric/campus` name now identifies umbrella ID `1403754490`; no old-name
  fetch or remote repoint was used. Linux repository ID is `1337851940`.
  Canonical GitHub identity checks preceded the isolated clone. The coordinator later
  clarified that the executable cutover guard receipt was also required; it ran after
  source bootstrap, exited 0 without mutation, and before any further server Git network
  operation (none was needed). This timing distinction is retained for coordinator review.
- Server source: `a7e0abceb23f874e5a8c01ba043679a844e6d287`, the actual
  [merged PR #1552](https://github.com/yuric/campus-server/pull/1552) for prerequisite #984.
  GitHub reported merged at `2026-10-16T17:22:09Z`, from head
  `a7a665696600bf17ff4150b2577a374e845704cd`. Server main was identical to the merge
  when inspected; `git merge-base --is-ancestor` also passed in the isolated clone.
- Exporter SHA-256: `f6fc22f04acda6493cc97e9c8fb230e6d694781f9a3166100d08112457c3f4f1`.
  Both exporter and its regression suite came from that exact server commit.
- [Provenance](../../contract/.source): `yuric/campus-server@a7e0abceb23f874e5a8c01ba043679a844e6d287`.
- [Spec](../../contract/api/docs/openapi.yaml) SHA-256:
  `e5b10521076db00ad02c8d7e064abffa67b1c303a6136ec6cd3df4effb61bc88`.
- Bundle: **166 regular files**, **301 API paths**, **44 distinct externalValue targets**.
  Every `contracts/` leaf is included, including fixtures not referenced by the spec.
- Tree SHA-256: `a2702b2e3ccba9e78fc77b6ce7fa51bc7d48b91dadfa648f2cb41f2162360aec`.
  [The verifier](../../scripts/check_contract.py) hashes compact ASCII JSON of sorted
  `[relative_path, git_mode, content_sha256]` records, including `.source`. It rejects
  non-regular entries. The ordinary offline check compares this complete-tree digest with
  the reviewed [external pin](contract-tree.sha256). Explicit `--server` and `--reexport`
  modes additionally compare the complete leaf set, Git executable modes and bytes against
  upstream Git objects and a fresh export, respectively. The editable pin detects local
  drift; agreement alone does not authenticate upstream or prove main ancestry. A pin
  refresh requires reviewed merged-source equality and clean re-export evidence.
  This digest is distinct from a Git tree OID.

The Linux snapshot commit and draft PR are recorded on card #985 and its PR handoff;
embedding a commit's own SHA in this file would change that SHA. Coordinator acceptance
must pin the eventual merged Linux commit as well as the source and digest above.

The server-owned cutover guard was read from the pinned commit via GitHub's contents API
and run with `bash /tmp/campus-985-8684049b/repo-cutover-continue` from the isolated server
checkout. Exact output (exit 0):

```text
repo-cutover-continue: origin route inventory (userinfo redacted)
  configured fetch (remote.origin.url): https://github.com/yuric/campus-server.git [destination]
  effective fetch  (git remote get-url --all): https://github.com/yuric/campus-server.git [destination]
  effective push   (git remote get-url --push --all): https://github.com/yuric/campus-server.git [destination]
repo-cutover-continue: destination identity confirmed: id 1311891398, yuric/campus-server
repo-cutover-continue: continue. Every configured and effective route is yuric/campus-server
with confirmed id 1311891398. Fetch and push are safe.
```

## Reproduction and observed results

Source scratch: `/tmp/campus-985-8684049b/server`, an isolated sparse clone, detached at
the recorded merge. No reference worktree files were copied. Host tools: Node `v22.23.1`,
Python `3.11.15`, PyYAML `6.0.3`, Gitleaks `8.30.1`. These are source-check tools, not a
change to the pinned product toolchain. No dependencies were installed and no Docker,
VM, package, renderer, provider or deployment workload was run.

Commands below use the original disposable paths. Start export commands from the server
repository directory, as in the producer's documented invocation:

```sh
git merge-base --is-ancestor a7e0abceb23f874e5a8c01ba043679a844e6d287 origin/main
shasum -a 256 scripts/oss/export-clients.mjs
mkdir -p /tmp/campus-985-8684049b/import/campus-linux
node scripts/oss/export-clients.mjs --dest /tmp/campus-985-8684049b/import --client linux --ref a7e0abceb23f874e5a8c01ba043679a844e6d287 --report /tmp/campus-985-8684049b/export.json
node scripts/oss/export-clients.mjs --dest /tmp/campus-985-8684049b/reexport --client linux --check --ref a7e0abceb23f874e5a8c01ba043679a844e6d287 --report /tmp/campus-985-8684049b/reexport.json
node --test scripts/oss/export-clients.test.mjs
git status --short
```

Observed: both exports exit 0, 166 files each, producer secret scans clean; all **10**
exporter tests pass, including planted-secret rejection and repeated Linux migration.
Source checkout remains clean. The import directory's `contract/` was copied without
editing its contents; both legacy snapshot files were removed. An initial absolute
invocation through macOS's `/tmp` symlink produced no output because the producer's CLI
entry-point guard compares file URLs. That no-op was detected before import; the documented
source-relative commands above produced the actual checked bundles. No exporter was patched.

Run from the Linux repository:

```sh
python3 -B scripts/check_contract.py --server /tmp/campus-985-8684049b/server --reexport /tmp/campus-985-8684049b/reexport/.stage-campus-linux/contract
python3 -B -m unittest discover -s scripts/tests -v
scripts/check-client-boundary.sh
python3 -B scripts/check_acceptance.py
python3 -B scripts/verify_repository.py
git diff --check
git diff --name-only origin/main...HEAD
```

Observed source comparison: every exported leaf path/type/mode/byte equals the pinned
server Git object; independent parsed-YAML traversal resolves every externalValue; all
JSON fixtures parse; provenance matches; fresh re-export, including `.source`, is identical.
Original import head `142a3751c9cfba4dcf0c5066e1b330d42ae8e24e` repository suite: **42 tests pass** (12 contract regression cases plus existing policy and
admission tests). D7 policy passes with no product source or exceptions added. Acceptance
inventory retains 523 unimplemented cases and 590 dispositioned census locations.
Markdown link and spec checks pass. Diff ownership is Linux contract/docs/repository tooling.

The acceptance ledger's source/hash identify this imported spec. The original receipt's
one-off walk resolved **431 operation mappings and 1,275 JSON pointers**. That walk now runs
in ordinary `python3 -B scripts/check_acceptance.py` verification: it checks source/hash
equality, operationId presence/equality, exact operation-pointer/path/method agreement and
resolution of every schema reference. The in-memory mutation regressions in
[test_contract_offline.py](../../scripts/tests/test_contract_offline.py) exercise stale
bindings and fixture add/delete/edit/mode changes without copying the bundle.

This does not upgrade any action to runtime acceptance or erase the historical Mac
reconciliation source recorded in [the inventory](inventory.md).

## Secret scan and remaining admission

```sh
gitleaks dir contract --redact --no-banner --report-format json --report-path /tmp/campus-985-8684049b/gitleaks-contract.json
```

The additional unmodified Gitleaks scan exits **1**, with exactly one `generic-api-key`
finding: `contract/contracts/workspace_rules/v1/transition_hold.json:5`, a fixture UUID in
`request_key`. The imported `WorkspaceRuleTransitionHold.properties.request_key` schema
explicitly marks it `x-campus-output: identifier`; it is a request identifier, not an
API credential. This is a reviewed false positive, not a claim of a clean Gitleaks exit.
No ignore, baseline, rule change or fixture edit was applied. Both producer secret scans
pass. The coordinator must independently confirm the disposition during review.

LINUX-20261016 is the explicitly assigned sole CI/review/merge observer. Hosted architecture
checks and exact-head admission remain for that owner; the worker does not start another
watcher or run the Docker commands under the source-only budget. Required CI is not claimed
green here. The coordinator obtains different-family review, observes Council and records
merged snapshot evidence before unblocking consumers. All L0/product/release gates remain.

## Offline-verification repair validation

The #10869 repair keeps all 166 imported leaves and the action/census/reconciliation JSON
unchanged. Direction #1317 permits at most 8 MiB additional source/receipt/Git writes with
a freshly measured 16 GiB host floor. It permits Python `-B` read-only/mocked validators;
the 18 GiB targeted-test and higher build/guest floors still apply. No dependencies were
installed and no full-tree copies, builds, guests, database or coverage allocations ran.

Repair checks (source revision is recorded on card #985):

- `python3 -B -m unittest discover -s scripts/tests -p test_contract_offline.py -v`:
  **7 passed**, including in-memory fixture add/delete/edit/mode and stale ledger mutations.
- `python3 -B scripts/check_acceptance.py`: **PASS**, 431 operation mappings, 1,275
  pointers, 523 unimplemented cases and 590 dispositioned census locations.
- `python3 -B -c "import sys; sys.path.insert(0, 'scripts'); import verify_repository; verify_repository.documents()"`:
  **PASS**, Markdown links plus default offline contract checks.
- `python3 -B scripts/check_client_boundary.py --root .`: **PASS**, no product source.
- `python3 -B scripts/check_contract.py --server /tmp/campus-985-8684049b/server --reexport /tmp/campus-985-8684049b/reexport/.stage-campus-linux/contract`:
  **PASS**, using the already-preserved server objects and fresh-export output; no new export
  or server Git network operation was run in this repair.
- `git diff --check`: **PASS**. The original 42-test full suite, full
  `verify_repository.py`, exporter tests and hosted checks were **not rerun for this repair**
  under the below-18-GiB resource condition. Their old-head results do not certify this head.

A first D7 invocation mistakenly used the nonexistent hyphenated Python filename and exited
2; the corrected underscored command above passed. LINUX-20261016 owns the remaining full
suite/CI, fresh different-family delta review, Council and merge. The draft is not completion.
