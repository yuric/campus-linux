# AGENTS.md — Campus for Linux

Instructions for AI coding agents working in this repository. Humans want `README.md` and
`CONTRIBUTING.md`.

## Read this first: there is no code here

This client **has not been started**. There is no source, no build, and no test command. The
stack is not decided.

If you have been asked to implement something here, the correct first move is to stop and
establish the decisions listed in `PRD.md`. Writing an implementation now means inventing
architecture that has not been agreed, in a repository whose whole purpose is to render
decisions made elsewhere.

**Do not** scaffold a project structure, pick a framework, or add dependencies to "get
started". Those are the decisions, not preliminaries to them.

## What you can usefully do

- Answer the open questions in `PRD.md` with evidence — measurements, spikes in a scratch
  directory, links to documentation.
- Improve `PRD.md` itself as answers arrive.
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
you opened. The stage list is currently duplicated across three clients, and two of those
copies do not agree with each other.

A rule in two clients is a rule that will disagree with itself. There is no exception worth
the cost.

## Wire-shape changes

Any change to how this client decodes or encodes an API response requires the corresponding
change to `api/docs/openapi.yaml` in `yuric/campus-server`, merged there first. The
contract comes first, then the client.

## Secrets

Provider keys, session tokens, and executor tokens must never reach logs, transcripts,
process arguments, crash reports, analytics, or any file outside the platform's credential
store. This is not a guideline.

## Source of truth

This repository is the source of truth for Campus on Linux. Work on it has not started; when it
does, development happens here, through pull requests to `main`. Nothing is exported into this
repository except its snapshot of the API spec, which comes from `yuric/campus-server` and is
never edited here by hand. See `CONTRIBUTING.md`.

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

**This may be two products, not one.** A Linux desktop client and a headless Campus server
are different things with different users, and the second may matter more. `PRD.md` treats
them separately. Establish which one you are building before writing anything.

**Credential storage is the hard part and nothing transfers.** Not the macOS Keychain
rationale, not the Windows DPAPI question. Secret Service, gnome-keyring, and kwallet all
exist; a headless server has none of them, and that is probably the important case.

**Packaging choice carries an update story with it.** AppImage, deb, flatpak — each implies a
different answer to how a user gets a fix, and that answer is part of the security boundary,
not packaging trivia.
