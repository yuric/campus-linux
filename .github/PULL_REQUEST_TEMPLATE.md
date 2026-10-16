## What this changes

<!-- One or two sentences. What behaviour is different after this lands? -->

## Why

<!-- The problem. Link an issue if there is one. -->

## How it was verified

<!-- Commands run, tests added, what you checked by hand. "It builds" is not verification. -->

---

### Checklist

- [ ] No product decision was added to this client — no provider catalog, credential
      compatibility table, workflow transition table, ordering rule, validation rule, or
      interpretation of what a failure means. Those belong to the Campus API.
- [ ] Tests cover the new behaviour, and the observed test count went up.
- [ ] No secret, token, or credential is written to a log, a transcript, a process argument,
      or anywhere outside the platform credential store.
- [ ] Documentation updated if behaviour or setup changed.

> **Heads up:** pull requests here are merged into `main`, with Linux implementation authorized under LINUX-20261016.
> Workers hand off draft PRs to that coordinator; unsolicited substantial work starts with an issue. API changes start in
> `yuric/campus-server`, not here; see [CONTRIBUTING.md](../CONTRIBUTING.md).
