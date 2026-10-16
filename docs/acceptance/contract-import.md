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
  non-regular entries and compares the complete leaf set, Git executable modes and bytes.
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
Repository suite: **42 tests pass** (12 contract regression cases plus existing policy and
admission tests). D7 policy passes with no product source or exceptions added. Acceptance
inventory retains 523 unimplemented cases and 590 dispositioned census locations.
Markdown link and spec checks pass. Diff ownership is Linux contract/docs/repository tooling.

The acceptance ledger's source/hash now identify this imported spec. Structural revalidation
of **431 operation mappings and 1,275 JSON pointers** passed using:

```sh
python3 - <<'PY'
import json, pathlib, yaml
spec = yaml.safe_load(pathlib.Path('contract/api/docs/openapi.yaml').read_text())
ledger = json.loads(pathlib.Path('docs/acceptance/actions.json').read_text())
operations = pointers = 0
for row in ledger['actions']:
    for op in row['operations']:
        for pointer in [op['schema_pointer'], *op['schema_refs']]:
            node = spec
            for key in pointer[2:].split('/'):
                node = node[key.replace('~1', '/').replace('~0', '~')]
            pointers += 1
        assert spec['paths'][op['path']][op['method'].lower()]['operationId'] == op['operation_id']
        operations += 1
print(operations, pointers)
PY
```

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
