# Contributing

Thank you for looking. Before you spend time on a change, there are two things about this
repository that are unusual and worth knowing up front.

## 1. Pull requests merge here, but start with an issue

This repository is the source of truth for Campus on Linux, and pull requests are merged here,
into `main`. API snapshots come from `yuric/campus-server`; a change to the API starts
there. Planned Island renderer artifacts come from pinned merged `campus-macos` source;
renderer changes remain producer-owned rather than maintained as a Linux fork.

The product specification is [PRD.md](PRD.md). Its section 4 holds the owner's decisions;
implementation was explicitly authorized on 2026-10-16 under LINUX-20261016.

Open an issue first for substantial unsolicited work. An explicit owner-requested
planning PR can proceed directly; it does not authorize implementation or task import.

## 2. This client does not decide anything

**The Campus API decides; this client renders.**

The client holds no provider catalog, no credential compatibility table, no workflow
transition table, no ordering rule, no validation rule, and no interpretation of what a
failure means. It asks the server and renders the answer.

Verified generated wire enums and trusted executor/OS safety bindings follow the narrow
reviewed exceptions in [the boundary policy](docs/client-boundary.md). They do not authorize
presentation code to own catalogs or rules.

This is the single rule most likely to get a change sent back. If your patch adds a line like
`if provider == "anthropic"`, or hardcodes a list of stages, or turns an error string into a
user-facing explanation, that logic belongs in the API instead.

The reason is concrete rather than theoretical. Campus has several clients, and a rule
compiled into two of them drifts. It has already happened: the macOS and web clients
disagreed about whether xAI supported CLI login, so Campus gave two different answers
depending on which one you opened.

If a change genuinely needs new product behaviour, the work starts with an API contract. Say
so in the issue and it can be routed properly.

## Getting set up

There is no application build or runtime test suite yet. This repository defines
a desktop client and local execution service, with macOS feature parity and remote control.
It does not host Rails. Read [PRD.md](PRD.md) for the parity baseline, the decided stack
and the L0 gates before adding a dependency.

Feature PRDs belong at `TODO/<feature-name>/PRD.md`; follow [TODO/README.md](TODO/README.md).
The root placeholder PRD has been replaced. Shared renderer changes belong in
`campus-macos`; API changes belong in `campus-server`, merged before Linux consumers.
The [implementation gates](docs/implementation-gates.md) record the remaining evidence
required during implementation. The post-S1 snapshot lives in `contract/`;
[the import receipt](docs/acceptance/contract-import.md) records its merged server source,
export command and verification. Refresh it with the server-owned exporter and update
all affected documentation and CI in the same PR; never hand-edit the bundle.

Documentation changes are checked for internal links and OpenAPI snapshot parsing by
`.github/workflows/docs.yml` where its repository-visibility condition permits. The same
workflow runs `scripts/check-client-boundary.sh` and the shared repository regression suite
(the contract checks use the existing PyYAML verification dependency):
`python3 -B -m unittest discover -s scripts/tests -v`. The gate checks the syntax and
reviewed exceptions described in [the boundary policy](docs/client-boundary.md); it is not
a semantic proof. These are repository checks, not Docker/app builds or runtime parity
tests. Owner-requested policy maintenance does not start app implementation. Do not
bootstrap a product test framework for a docs PR.

## Making a change

- **Match the surrounding code.** Naming, comment density, and structure are more consistent
  in this codebase than any style guide would capture. Read the neighbours first.
- **Tests are not optional** for behaviour changes. A new test that does not run is worse than
  no test — check that the total count actually went up.
- **Never log a secret.** Provider keys, session tokens, and executor tokens must not reach
  logs, transcripts, process arguments or crash reports. Persistent Campus-owned tokens
  use Secret Service; D3 separately defines provider-owned OAuth files and the local IPC
  token. Per-attempt API keys never go on disk.
- **Comments should say why, not what.** The code already says what.

## Commit messages

Write the subject as what the change does, in the imperative. The body is for the reasoning —
what was wrong before, what you considered, why this way. If a comment in the diff would go
stale, the commit message is the better home for it.

## Reporting bugs and security problems

Bugs: use the issue templates. Security vulnerabilities: **do not open an issue** — see
[SECURITY.md](SECURITY.md).

## Code of conduct

Participation is covered by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — Contributor
Covenant 3.0.

## Licensing

By contributing you agree that your contribution is licensed under the Apache License 2.0,
the same terms as this repository. See [LICENSE](LICENSE).

## Linux implementation delivery

Follow [AGENTS.md](AGENTS.md) for draft-only worker handoff and coordinator review/merge.
[Verification](docs/acceptance/verification.md) names the bounded Docker commands, required
checks and fail-closed admission; [inventory](docs/acceptance/inventory.md) tracks action gaps.
