# Contributing

Thank you for looking. Before you spend time on a change, there are two things about this
repository that are unusual and worth knowing up front.

## 1. Pull requests cannot be merged here

Campus is developed in a private monorepo and published to this repository by an automated
export. A commit pushed here would be overwritten by the next export.

That does **not** mean contributions are unwelcome — it means the mechanics are different:

1. Open an issue or a pull request here. Either is fine; a PR is often the clearest way to
   show what you mean.
2. The change is reviewed here, in the open.
3. If accepted, it is applied upstream in the monorepo with your authorship preserved.
4. It arrives back in this repository in the next export, and the PR is closed with a link
   to the commit that carries it.

Round trips are slower than a normal merge. Issues are cheap; large unsolicited pull requests
are the thing most likely to be wasted effort, so open an issue first for anything
substantial.

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

This client has not been started, and it may turn out to be two
different things — a Linux desktop client, and Campus running headless on a server. See
[PRD.md](PRD.md).

**The most useful contribution right now is not code.** The open questions are:

- Which of those two products this repository is for.
- Credential storage. Neither the macOS Keychain design nor the Windows DPAPI question
  transfers. Secret Service, gnome-keyring, kwallet, and headless machines with none of them
  are all real cases, and headless is probably the important one.
- Packaging: AppImage, deb, flatpak, or some subset — each with its own update story.

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
