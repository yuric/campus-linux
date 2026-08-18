# PRD — Campus for Linux

**Status: not designed.** This is a placeholder so the repository exists and the name is
claimed. It is not a plan, and nothing here should be built from.

> **The previous stub is superseded.** `clients/linux/PRD_LINUX.md` was three lines
> specifying the "same shared-Tauri strategy as Windows." That strategy no longer exists:
> macOS shipped as a native Swift/SwiftUI application, so there is no shared desktop codebase
> for Linux to join. Tauri remains a live option — but as a decision to be made, not one
> already taken.

## The one thing the stub got right

It identified this repository as "the natural home for headless-server install docs (Campus
on a home server or VPS)." That is a genuinely distinct and possibly more valuable job than a
desktop client, and it is worth separating explicitly:

1. **A Linux desktop client** — the board and the island, for someone working on a Linux
   workstation.
2. **Campus running headless on a Linux server** — no GUI, agents executing against
   checkouts on that machine.

These are different products with different users. The second may matter more, and it is not
a client at all.

## What is already settled, regardless of stack

One thing does not wait for a design. **Rails is authoritative for everything that is not
inherently presentation.** Any Campus client renders; it does not decide.

The API owns which providers, engines, credential kinds and models exist and which
combinations work; credential state and why; allowed workflow transitions, lane identity,
ordering and membership; normalized diagnostic severity, reason, detail and every copy-safe
message; path validation; and the domain vocabulary — what a stage, priority, activity or
session state is *called*.

A client owns layout, navigation, focus, selection, local draft state, native rendering of
server semantics, accessibility behaviour, and transport failures the server could not author
because no response arrived.

**A client must never** duplicate a provider or model catalog, infer domain meaning from an
error substring, or treat HTTP success alone as domain success.

Being late is an advantage here. By the time this client is built, the API should already
author everything — the macOS, web, and CLI clients are having their rules moved server-side
first. **If building this client requires inventing a rule, that is a bug in the API, not a
task for this repository.**

## Reference

The existing clients are the specification in practice:

- [`campus-cli`](https://github.com/yuric/campus-cli) — smallest and most readable; the best
  starting point for understanding the API.
- [`campus-macos`](https://github.com/yuric/campus-macos) — native Swift, and the reference
  for local agent execution.
- [`campus-web`](https://github.com/yuric/campus-web) — React and Three.js; home of the
  island renderer.

`docs/api/openapi.yaml` is the contract itself.

## What has to be decided before this starts

- **Which of the two products above** this repository is for, or whether it is both.
- **The stack**, if a desktop client. Tauri is the leading candidate for the same reason it
  leads on Windows — it reuses the existing web client and island renderer — but it is not
  decided. Tracked alongside the Windows decision in
  [`campus-windows`](https://github.com/yuric/campus-windows).
- **Credential storage.** Neither the macOS Keychain rationale nor the Windows DPAPI question
  transfers. Linux has Secret Service, gnome-keyring, kwallet, and headless machines with
  none of them. A headless server is the hard case and probably the important one.
- **Packaging** — AppImage, deb, flatpak, or some subset. Each carries its own update story.
- **Whether a systemd user unit is in scope**, which is really a question about the headless
  product rather than the desktop one.
