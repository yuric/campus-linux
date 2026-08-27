# Campus for Linux

The Linux client for [Campus](https://projectcampus.dev) — a local-first task board that lands
AI coding agents on your own machine and gives them somewhere to work.

> **Status: not started.** This repository exists to claim the name and hold the design as it
> forms. There is no source here, and [PRD.md](PRD.md) is an honest placeholder rather than a
> plan — the earlier stub it replaces rested on assumptions that were never tested.

## Where this sits

Three Campus clients exist today:

| Client | State |
|---|---|
| [`campus-cli`](https://github.com/yuric/campus-cli) | Shipped — dependency-free TypeScript, the most readable reference |
| [`campus-macos`](https://github.com/yuric/campus-macos) | Shipped — native Swift, reference for local agent execution |
| [`campus-web`](https://github.com/yuric/campus-web) | Shipped — React and Three.js, home of the island renderer |

This would be the fourth. Unlike the others, it may not be a client at all — see below.

## The one rule that already applies

**The API decides; this client renders.**

No provider catalog, no credential compatibility table, no workflow transition table, no
ordering rule, no local interpretation of what an error means. Ask the server, render the
answer.

This is why a late client is tractable: it is a rendering job, not a reimplementation of the
product. If building it requires inventing a rule, that is a bug in the API.

## API documentation

`docs/api/openapi.yaml` describes the server every Campus client talks to. Combined with the
three shipped clients, that is everything needed to build this one.

## Two products, not one

The earlier stub quietly contained two different things, and they are worth separating:

1. **A Linux desktop client** — the board and the island for a Linux workstation.
2. **Campus running headless on a Linux server** — no GUI, agents executing against
   checkouts on that machine.

Different users, different products. The second may well matter more, and it is not a client.
[PRD.md](PRD.md) treats them separately.

## Contributing

Campus is developed in a private monorepo and mirrored here, which has one consequence worth
stating plainly: **a pull request opened against this repository cannot be merged here**,
because the next export would overwrite it. Contributions are back-ported by hand and arrive
in a later export.

Because this client has not been started, design discussion in issues is worth far more right
now than code.

## Project documents

| File | What it covers |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | The system this client will sit in, and the boundary it must respect |
| [PRD.md](PRD.md) | What is known, and every decision still open |
| [CONTRIBUTING.md](CONTRIBUTING.md) | What is actually useful to contribute right now |
| [AGENTS.md](AGENTS.md) | Instructions for AI coding agents — read before writing any code here |
| [SECURITY.md](SECURITY.md) | What to report, and how to report it privately |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Contributor Covenant 3.0 |

## License

Apache-2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).

Copyright is held by **Yuri Costa (YCStudios Inc)**. The company name is provisional
pending final incorporation; if it changes, it is a one-line update in `LICENSE` and
`NOTICE`.
