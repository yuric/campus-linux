# Security policy

## Reporting a vulnerability

**Do not open a public issue for a security problem.**

Email **yuri@sparkroad.com** with `SECURITY` in the subject. If GitHub's private
vulnerability reporting is enabled on this repository (**Security → Report a vulnerability**),
that works too and keeps the discussion attached to the code.

Expect an acknowledgement within **3 working days** and an assessment within **10**. If a
report is valid you will be told what the fix is and when it ships; if it is not, you will be
told why rather than left waiting.

## Where the security boundary actually is

This repository is a **client**. It renders decisions made by the Campus API and holds no
authority of its own. That shapes what is worth reporting.

Campus is island-per-user: every project, task, agent, and credential belongs to exactly one
island, and enforcing that is the API's job. A client cannot grant itself access it was not
given. So a report that a client *displays* something is only interesting if the client could
obtain it in the first place.

### Most valuable to report

- **Credential and token exposure.** Provider API keys, session tokens, or executor tokens
  reaching logs, crash reports, analytics, transcripts, process arguments, temporary files,
  or any on-disk location that is not the platform credential store.
- **Local privilege or process escapes.** Anything that lets a task's contents, a provider's
  output, or a repository's files cause code to run outside the intended working directory or
  process boundary.
- **Insecure credential storage** — a secret written somewhere other than the platform's
  credential store, or stored with weaker protection than the platform offers.
- **Transport weaknesses** — certificate validation that can be bypassed, secrets placed in
  URLs or query strings, or tokens sent to a host the user did not configure.
- **Update and distribution integrity**, where the client ships signed builds: anything that
  lets an unsigned, tampered, or downgraded artifact install.
- **Injection through server-authored content.** The client renders strings the API supplies.
  A path where that rendering executes code, escapes its context, or reaches a shell is a
  real bug.

### Out of scope

- Vulnerabilities in the Campus API itself — report those against the API, not here.
- Denial of service through ordinary load, or rate limits working as designed.
- Findings that require an already-compromised local machine. A client that runs coding
  agents against your own checkouts assumes the machine is yours and trusted.
- Missing hardening headers or flags with no demonstrated impact.
- Automated scanner output with no working proof of exploitability.

## A note on what this client is for

Campus runs AI coding agents against real repositories on a real machine, with the user's own
provider credentials. That is the product, not a vulnerability. Reports amounting to "an agent
can modify files in the repository it was pointed at" describe intended behaviour.

What *is* in scope is an agent reaching **beyond** what the user authorised: another island's
data, another project's checkout, a credential it was not leased, or a process outside its own
group.

## Supported versions

Only the current release is supported. There are no maintained release branches; fixes ship
forward.
