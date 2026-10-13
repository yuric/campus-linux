# Contributing

Thank you for looking. Before you spend time on a change, there are two things about this
repository that are unusual and worth knowing up front.

## 1. Pull requests merge here, but start with an issue

This repository is the source of truth for Campus on Linux, and pull requests are merged here,
into `main`. API snapshots come from `yuric/campus-server`; a change to the API starts
there. Planned Island renderer artifacts come from pinned merged `campus-macos` source;
renderer changes remain producer-owned rather than maintained as a Linux fork.

The proposed product specification is [TODO/PRD.md](TODO/PRD.md). Implementation has not
started; design review must distinguish proposed choices from accepted decisions.

Open an issue first for substantial unsolicited work. An explicit owner-requested
planning PR can proceed directly; it does not authorize implementation or task import.

## 2. This client does not decide anything

**The Campus API decides; this client renders.**

The client holds no provider catalog, no credential compatibility table, no workflow
transition table, no ordering rule, no validation rule, and no interpretation of what a
failure means. It asks the server and renders the answer.

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

There is no application build or runtime test suite yet. This planning repository defines
a desktop client and local execution service, with macOS feature parity and remote control.
It does not host Rails. Read [TODO/PRD.md](TODO/PRD.md) for the parity baseline and L0
portability gates before adding frameworks or dependencies.

Feature PRDs belong at `TODO/<feature-name>/PRD.md`; follow [TODO/README.md](TODO/README.md).
The root placeholder PRD has been replaced. Shared renderer changes belong in
`campus-macos`; API changes belong in `campus-server`, merged before Linux consumers.

Documentation changes are checked for internal links and OpenAPI snapshot parsing by
`.github/workflows/docs.yml` where its repository-visibility condition permits. Those
checks do not prove runtime parity. Do not bootstrap a product test framework for a docs PR.

## Making a change

- **Match the surrounding code.** Naming, comment density, and structure are more consistent
  in this codebase than any style guide would capture. Read the neighbours first.
- **Tests are not optional** for behaviour changes. A new test that does not run is worse than
  no test — check that the total count actually went up.
- **Never log a secret.** Provider keys, session tokens, and executor tokens must not reach
  logs, transcripts, process arguments, crash reports, or any file outside the platform
  credential store.
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
