# AGENTS.md — Campus for Linux

Instructions for AI coding agents working in this repository. Humans want `README.md` and
`CONTRIBUTING.md`.

## Read this first: there is no code here

This client **has not been started**. There is no source, no build, and no test command. The
stack is not decided. The proposed requirements are in [TODO/PRD.md](TODO/PRD.md).

If you have been asked to implement something here, the correct first move is to stop and
establish the decisions listed in `TODO/PRD.md`. Writing an implementation now means inventing
architecture that has not been agreed, in a repository whose whole purpose is to render
decisions made elsewhere.

**Do not** scaffold a project structure, pick a framework, or add dependencies to "get
started". Those are the decisions, not preliminaries to them.

## Repository routing

Campus spans several repositories. A change lands in the repository that owns the files it
edits, whatever building the card sits on and whatever folder your shell started in.

| Repository | Owns | Never goes here |
|---|---|---|
| `yuric/campus-server` | Rails API (`api/`), the OpenAPI spec and `contracts/`, deploy and release (`deploy/`, `changes/`, `VERSION`), AWS (`infrastructure/`), CI and policy (`.github/`, `scripts/`, `config/`), Campus skills (`.agents/skills`, `api/app/skills`) | Swift, the Mac app, the island renderer, any client UI |
| `yuric/campus-macos` | The Mac app (`CampusApp/`, `Sources/`, `Package.swift`), the island renderer (`island/`), the contract snapshot (`contract/`, moved only by a snapshot PR) | Rails, migrations, OpenAPI edits, deploy and release, client pins |
| `yuric/campus-ios`, `campus-android`, `campus-linux`, `campus-windows` | Scaffolds: PRDs and docs, until the owner starts the client | Product code, frameworks, dependencies |
| `yuric/campus-cli`, `yuric/campus-web` | Retired on 2026-10-05 (`campus-web` is archived) | Any new work |
| `yuric/campus` | The umbrella: submodule pointers and its own scaffold docs | Product code of any kind |
| `yuric/campus-marketing-page` | The public marketing site | API or client code |

- **Business rules go to Rails even when the card is about a client.** If the Mac change needs
  a new rule, message, or field, that part is a campus-server PR first; the client PR only
  renders it. The order is the contract order in campus-server's `AGENTS.md`.
- **A change that spans repositories is one PR per repository**, and one card per repository,
  each card on the building bound to that repository.
- **Check before you open a PR.** `git diff --name-only origin/main...HEAD` must list only
  paths this repository owns. Anything else moves to its own PR in the owning repository.
- **CI enforces it.** campus-server's Architecture policy rule `repository-boundary` fails on
  client files in campus-server and, at the client pin gate, on server files in the pinned
  campus-macos commit; campus-macos CI runs the same check on its own pull requests.

### In this repository

- You are in a scaffold. Nothing but PRDs and docs changes here until the owner starts
  this client; product or API work goes to the repository the table names.

## What you can usefully do

- Answer the open questions in `TODO/PRD.md` with evidence — measurements, spikes in a scratch
  directory, links to documentation.
- Improve `TODO/PRD.md` itself as answers arrive.
- Point out where the plan contradicts what the shipped clients actually do.

## The shipped client is the specification

- [`campus-macos`](https://github.com/yuric/campus-macos) — native Swift; the reference for
  local agent execution, and home of the island renderer.

`docs/api/openapi.yaml` is the contract itself.

## The rule that overrides everything else

**Rails is authoritative. This client renders.**

Do not add to this repository:

- provider, engine, model, or credential-kind catalogs;
- compatibility tables (which provider works with which credential kind);
- workflow or stage transition tables;
- ordering, ranking, or lane-membership rules;
- path, name, or filesystem validation rules;
- interpretation of what a failure means — no matching on error substrings, message
  prefixes, or exit codes;
- user-facing domain wording: what a stage, priority, activity, or session state is *called*.

All of that comes from the API. Ask it, render the answer verbatim.

**Unknown versioned server fields fail closed.** If the API sends a contract version this
client does not understand, withhold the action — never substitute an older client-side
decision.

**HTTP success is not domain success.** A 200 means the request was accepted, nothing more.

### Why this is enforced so hard

The macOS and web clients each compiled their own copy of which providers support CLI login.
They drifted. Campus answered "can I sign in with xAI?" differently depending on which client
you opened. Historical duplication also caused stage lists to disagree. The retired clients are
not dependencies of this implementation.

A rule in two clients is a rule that will disagree with itself. There is no exception worth
the cost.

## Wire-shape changes

Consume existing responses from a verified pinned OpenAPI snapshot. New or changed wire
shapes require the corresponding change to `api/docs/openapi.yaml` in
`yuric/campus-server`, merged there first. A Linux implementation of an existing contract
does not itself require an API change. The contract comes first, then the client.

## Secrets

Provider keys, session tokens, and executor tokens must never reach logs, transcripts,
process arguments, crash reports, analytics, or any file outside the platform's credential
store. This is not a guideline.

## Source of truth

This repository is the source of truth for Campus on Linux. Work on it has not started; when it
does, development happens here, through pull requests to `main`. API snapshots come from `yuric/campus-server` and are never edited here by hand.
The planned renderer artifact comes from a pinned merged `campus-macos` producer;
its implementation remains producer-owned. See `CONTRIBUTING.md`.

## Repository name cutover

This repository is not renamed. The upstream monorepo referenced elsewhere in this file (for
example in Wire-shape changes) becomes `yuric/campus-server`; this repository's own `origin`
is unaffected and needs no change here. If you separately hold a checkout of that monorepo, identify it by its stable GitHub repository
id, never by name: `gh api repos/yuric/campus --jq '.id, .full_name'` printing `1311891398` and
`yuric/campus-server` means renamed, so repoint; `1311891398` still at `yuric/campus` means not yet,
do nothing; any other id, a 404, or an auth or API error means the name may have been reused or
the state is unknown, so stop before any fetch or push and escalate. When repointing, preserve the
transport the checkout already uses: `git remote set-url origin git@github.com:yuric/campus-server.git`
for SSH, `git remote set-url origin https://github.com/yuric/campus-server.git` for HTTPS, and never
print a URL that carries credentials. Run it once in any of its worktrees, since they share the
parent checkout's `origin`; the monorepo's `.claude/skills/repo-cutover-continue/SKILL.md` has the
full procedure.

## Linux-specific notes for whoever starts this

**Scope is specified.** The owner requested desktop macOS feature parity, local execution
and remote control. Hosting Rails is outside scope. Match the Mac login-session lifecycle:
execution can continue with the window closed, but unattended pre-login/after-logout work
is not release 1. See `TODO/PRD.md`; framework choices still require L0 evidence.

**PRD location.** Overall requirements live at `TODO/PRD.md`. Future feature PRDs belong
at `TODO/<feature-name>/PRD.md`, following `TODO/README.md`. Do not restore a root PRD.

**Credential storage is the hard part and nothing transfers.** Not the macOS Keychain
rationale, not the Windows DPAPI question. Secret Service, gnome-keyring, and kwallet all
exist; a headless server may have none of them. Do not add a plaintext fallback or expand
the approved logged-in desktop scope to solve headless deployment.

**Packaging choice carries an update story with it.** AppImage, deb, flatpak — each implies a
different answer to how a user gets a fix, and that answer is part of the security boundary,
not packaging trivia.
