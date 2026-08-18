# Architecture — Campus for Linux

**This client has not been built, so it has no internal architecture yet.** What follows is
the part that is already settled: the system this client will sit in, and the boundary it
must respect. The decisions still open are in `PRD.md`.

## The system this client sits in

Campus is a Rails API with several clients. The API is authoritative for every product
decision; a client renders those decisions and adds platform-native interaction.

```
                    ┌──────────────────────────────┐
                    │        Campus API            │
                    │  Rails + PostgreSQL/Aurora   │
                    │                              │
                    │  · workflow and capability   │
                    │    decisions                 │
                    │  · normalized state          │
                    │  · diagnostic severity       │
                    │  · domain vocabulary         │
                    └──────┬────────────────┬──────┘
                           │                │
                    HTTPS  │                │  Action Cable
                    REST   │                │  (change hints)
                           │                │
        ┌──────────────────┴────────────────┴──────────────────┐
        │                  │                │                  │
   ┌────┴────┐      ┌──────┴─────┐    ┌─────┴────┐      ┌──────┴─────┐
   │ campus- │      │  campus-   │    │ campus-  │      │  future    │
   │  macos  │      │    web     │    │   cli    │      │  clients   │
   └────┬────┘      └────────────┘    └──────────┘      └────────────┘
        │
        │ localhost, authenticated
   ┌────┴──────────────────┐
   │  campus-mac-broker    │  provider CLIs, local repository access
   └───────────────────────┘
```

### Where the authority line sits

| The API decides | A client decides |
|---|---|
| Which providers, engines, models, and credential kinds exist | Layout, navigation order, focus, selection |
| Which combinations can work | How a `destructive` intent looks as a button |
| Credential state — unverified, active, expired, exhausted — and why | Which native colour renders `error` vs `warning` |
| Allowed workflow transitions and their labels | Local draft and interaction state |
| Board lane identity, ordering, membership | Accessibility behaviour |
| Diagnostic severity, reason, detail, safe message | Transport failures where no response arrived |
| Path and filesystem validation | Terminal, window, or view composition |
| Domain vocabulary — what a stage is *called* | — |

A client that infers domain meaning from an error substring, a message prefix, or HTTP status
alone is broken, even when it happens to produce the right answer.

### Freshness: events are hints, not patches

Real-time updates say *that* something changed. The client re-reads the snapshot it already
knows how to render. There is no patch application and no reconciliation, so a dropped socket
costs one extra fetch rather than corrupt state.

### Versioning and failing closed

Server contracts are versioned. A client that receives a version it does not understand
**withholds the action** rather than falling back to an older client-side decision. Silent
degradation is how two clients start disagreeing.

## What is undecided

Whether this repository is even a client. See `PRD.md`.

## The fork that has to be resolved first

An early stub quietly contained two products:

1. **A Linux desktop client** — the board and the island, fitting the diagram above exactly.
2. **Campus running headless on a Linux server** — no GUI, agents executing against checkouts
   on that machine. This does not fit the diagram above at all: it is closer to the *broker*
   box than to a client box, or possibly to the API box itself.

These have different users, different threat models, and different update stories. The second
may well matter more.

## Credential storage transfers from nowhere

Not the macOS Keychain rationale, not the Windows DPAPI question. Secret Service,
gnome-keyring, and kwallet all exist on desktops; a headless server has none of them. If the
headless product is the real one, credential storage is an open design problem rather than a
platform API call.
