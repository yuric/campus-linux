# Client authority boundary policy

[PRD D7](../PRD.md#d7-the-boundary-is-a-failing-build-not-a-principle) defines the rule:
Rails owns domain decisions. Presentation code renders API data. Generated wire types and
trusted executor bindings have narrow, reviewed uses of identifiers; they do not own
capability catalogs, workflow rules or domain messages.

This repository has policy tooling, but no app implementation. The boundary checker uses
Python 3.9 or later and the standard library. The shared regression command also runs
contract-import tests, which use the repository verification environment's existing PyYAML:

```sh
python3 -B -m unittest discover -s scripts/tests -v
scripts/check-client-boundary.sh
```

The Docs and Linux verification workflows run both commands where their public-repository
conditions permit. An empty product tree is reported explicitly. A green policy job is not evidence
of Linux runtime verification.

## What the checker covers

The checker recursively scans `.rs`, `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`, `.mts`
and `.cts` files anywhere in the repository, including `src-tauri` and future source roots.
It excludes directories named `.git`, `.gstack`, `.claude`, `.venv`, `node_modules`,
`target`, `dist` and `build`. These are dependency/output/tool directories, never homes for
maintained product source. Source symlinks fail rather than silently omitting their target.

It rejects exact known domain strings in single/double quotes, JavaScript backticks and
Rust raw strings, including common hex/Unicode escape spellings. It also flags common
error/message/reason/detail substring calls, including calls split across lines, and
assignments of object/array/Map tables to names such as `transitions`,
`workflowTransitions` and `transition_table`. Comments are excluded from code matching.
Diagnostics name the file/line without echoing source payloads.

This is a bounded lexical gate, not a language parser or a proof of semantic authority.
Computed strings, aliases, arbitrary table names, complex template expressions, nested
language constructs and new domain vocabulary can escape it. Review must examine data
flow and decisions; future product contract tests and language-aware checks supplement
this gate. Update the vocabulary/tests when the verified contract changes. Never treat a
pass as permission to add a rule outside Rails.

## Fixture-only line exceptions

A literal in a test/fixture may use a same-line comment with a nonempty explanation:

```ts
const response = { engine: "codex" }; // campus-boundary: allow pinned API response fixture
```

Recognized paths contain a `test`, `tests`, `__tests__`, `fixtures` or `__fixtures__`
component, or use a `.test`/`.spec` JS/TS filename. These files must remain test-only and
must not be imported into production. The comment exempts only its line, not the whole
file. Empty reasons, markers inside string values, preceding-line markers and markers in
production source do not grant exceptions. Review the explanation and fixture use.

## Reviewed production files

The checked-in [policy manifest](../scripts/client-boundary-policy.json) starts empty.
There are no path globs or directory exemptions for generated code or adapters. An entry
must identify one existing source file and contain:

| Field | Requirement |
|---|---|
| `path` | Exact repository-relative file, no traversal or duplicates |
| `kind` | `generated-contract` or `executor-adapter` only |
| `sha256` | SHA-256 of the reviewed file's exact bytes |
| `reason` | Nonempty explanation of why identifiers are necessary |
| `evidence` | Nonempty reference to the provenance/contract and review receipt |

The gate validates the manifest and hash before exempting that file from lexical checks.
Changing a byte invalidates its receipt. Hashes bind reviewed content; they do not prove
that a review was correct or that code was generated. Review the file and manifest
together on every change. The two kinds require different evidence:

- **Generated contract:** verified merged server SHA, snapshot checksum, generator and
  version, exact regeneration command and a clean regeneration diff. Only generated wire
  definitions belong in the file. A future product CI regeneration check must independently
  reproduce it; a hand-edited enum plus an updated hash is insufficient. Do not render
  these enums as a local provider catalog or derive capabilities from them.
- **Executor adapter:** an intentionally small trusted file with a reviewed engine-to-local
  executable/argv binding or OS/credential primitive. Evidence names the server contract,
  allowed local operations and tests for unknown engines, arbitrary executable/path input,
  credential-root/symlink bounds and attempt ownership. Rails supplies authorization and
  opaque scopes, never arbitrary binaries/paths. These files must not carry presentation
  copy, compatibility decisions or workflow logic. File-wide review is required because
  the lexical gate cannot separate a safe binding from an unsafe domain decision inside it.

Malformed/missing policy, stale hashes and invalid metadata fail closed. Changing this
policy, expanding ignored directories or approving an exception requires authority review
in the same PR. Standard-library regression probes cover forbidden syntax/paths, valid
API field access, fixture scope, generated enums, trusted bindings and stale/invalid
receipts; they introduce no application runtime or product dependencies.
