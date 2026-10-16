# Disposable security and session observations (#982)

These are bounded OS experiments on the owned Lima Ubuntu 24.04 arm64 guest,
not product authorization, API compatibility or release acceptance. Linux base:
`37ef5d622da09cd7ba113dc0d1119e62e7378f84` (merged #981/PR11).
No current server contract was imported, no live account credential was injected,
and no server lease, registration or outbox success is claimed.

## Observed boundaries

| Mechanism | Observation | Limit |
|---|---|---|
| Scope encoding | Shared-rule vectors include ASCII, Japanese, accented Unicode, empty, NUL, 160-byte boundary and oversized Unicode; unpadded base64url | Safety binding only; no presentation or server validation rule |
| Descriptor-relative access | `openat2(RESOLVE_BENEATH | RESOLVE_NO_SYMLINKS)` rejects symlink/absolute/parent escapes; 3,000 concurrent rename/symlink attempts never opened the external sentinel | Kernel FD pins the inode, not immutable lexical ancestry; hostile same-UID relocation still requires fencing before CLI launch |
| Cross-filesystem workspaces | Independent authorized directory descriptor on `/dev/shm` works while credentials remain on the home filesystem | Does not impose a global `RESOLVE_NO_XDEV` restriction; product adoption/reconciliation remains required |
| IPC | AF_UNIX kernel peer identities obtained before token read; actual nobody UID rejected; final Wayland/X11 clients authenticated root server UID/PID/start ticks and withheld token for a wrong expected server identity; stale socket/principal/attempt negatives also observed | This root-server fixture is not the final same-UID executor design. Same UID is not application identity; synthetic principal tests do not establish Rails token authority, expiry or revocation |
| Child inheritance | Explicit allowlist contains only basic runtime fields plus synthetic attempt runtime/MCP variables; no unintended FD survives `close_fds` | Git/SSH/provider-login exceptions still require dedicated evidence; no general session bus/display/SSH-agent inheritance |
| Attempt termination | Real systemd user service contains leader and `setsid` grandchild in the same attempt cgroup; final X11/Wayland runs terminated both TERM-ignoring processes in 2.185s/2.206s with pidfd exit readiness | Probe timeout is not a production claim stop grace. Fork races, hostile cgroup escape and full protocol handback remain unproven |
| Identity | Boot ID, PID, start ticks, cgroup and actual pidfd exit readiness recorded | PID reuse not forced; final code must retain handles and never trust PID alone |
| Crash policy | Normal exec resets parent-set dumpability to 1. Setting it inside the executed synthetic child prevents an observed Apport dump after SIGABRT | This exposes a production gap: closed-source provider executables have not been shown to apply child-side policy; a parent prctl/core limit alone is insufficient |
| Secret Service | Final Wayland/X11 unaliased disposable collections completed create/read/lock/refusal/graphical unlock, verified item deletion and verified collection deletion while preserving default/login aliases and preexisting collections | Original login collection remains locked after password rotation. This is not PAM auto-unlock; historical default-store cleanup was unverified. No product memory-only/registration withholding behavior exists yet |
| Same-user exposure | Separate same-UID process read the synthetic Secret Service item | Secret Service is not a per-application sandbox; no Mac application ACL parity claim |
| Absent store | Private D-Bus with no service activation has no secret-service owner; no fallback file created by the probe | This is an isolated bus absence test, not uninstalling the guest's backend or testing a product |
| Privileged package update | Final Tauri-signature fixture passed seventeen cases per session, actual Wayland/X11 password prompts, and Wayland cancellation/missing-authority cases with intact helper bytes | Exact source-extracted signature verification with disposable keys; stock updater fallback still fails G5 and full product integration remains unproven |

Raw observations: [OS probes](receipts/security-os.json),
[final X11 process/cgroup/crash](receipts/process-x11-final.json),
[final Wayland process/cgroup/crash](receipts/process-wayland-final.json),
[final X11 disposable store](receipts/store-x11-disposable.jsonl),
[final Wayland disposable store](receipts/store-wayland-disposable.jsonl),
[historical Wayland store](receipts/store-wayland.jsonl), [absent bus](receipts/store-absent.json),
[graphical keyring prompt](receipts/keyring-wayland-prompt.png).
The corrected store probe resolves any deletion prompt and verifies that the item is
absent from `SearchItems`; it now requires those observations and a successful separate
process read before returning success. After the disposable Unix password rotation,
cold graphical login left the existing login collection locked: PAM password change did
not rekey it. Preserve that failed default-store observation and the original collection;
do not delete/reset it to obtain a passing result. Historical pre-rotation unlocked-store
observations retain their original scope. Both final Wayland/X11 disposable-collection runs passed
with script SHA `4e0eb5d7723d070a367f0c815a0fcdff37e5f350fb0ad8095f04ede6cef62f04`.
Its [earlier creation timeout](receipts/store-x11-disposable-timeout.jsonl) and
[dismissed unlock](receipts/store-x11-disposable-dismissed.jsonl) remain failures, not
passes. The operator attributed dismissal to Tab/Return racing the next prompt; the
failed run still deleted its own collection and preserved existing collections/aliases.
The [default-store attempt](receipts/store-x11-final.jsonl) contains only a pending prompt,
not a completed cycle. Neither final disposable-collection pass repairs or proves
auto-unlock of that original login collection.

Both final Wayland/X11 process runs passed with script SHA
`1a7edac20f39131aefbcf8764d447be7fbd713f994c07ab28c844f5b2d4b5578`.
Each checked equal cgroups, all three reciprocal IPC cases and aggregate exit status;
both wrong-server cases recorded `token_sent=false`. Historical process receipts prove
their recorded server-side checks, not this newly added client check. The crash result
remains limited to the recorded Apport configuration and three-second observation window.
Package details and hashes are in [the package matrix](packages.md) and
[signature proof](tauri-signatures.md), with final
[Wayland](receipts/tauri-install-wayland-schema.json)/[X11](receipts/tauri-install-x11-schema.json)
suite receipts and [missing-authority preservation](receipts/tauri-install-wayland-schema-polkit-missing.json).
The operator restored polkit afterward. This is not evidence for a separately missing
desktop agent or for owner-held release-key custody.
Sources: [openat2 ABI](https://kernel.googlesource.com/pub/scm/docs/man-pages/man-pages/+/refs/tags/man-pages-6.12/man/man2/openat2.2),
[cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html),
[Secret Service API](https://specifications.freedesktop.org/secret-service-spec/latest/),
[GNOME Keyring limits](https://wiki.gnome.org/Projects/GnomeKeyring/SecurityPhilosophy).

## Reproduce

Copy the checked-in `spikes/982` directory to the guest without private host material.
`in-session.py` derives only the actual display/bus environment from the graphical user's
manager. It is a test launcher, not a provider-child environment policy.

```sh
limactl shell campus-linux-d5-noble-arm64 sudo -u campusqa python3 - \
  < spikes/982/security/os-probes.py
limactl shell campus-linux-d5-noble-arm64 sudo python3 /tmp/campus-982-process-probes.py
limactl shell campus-linux-d5-noble-arm64 sudo python3 /tmp/campus-982-in-session.py \
  python3 /tmp/campus-982-store-probe.py cycle
# To preserve a locked existing login collection, use a new unaliased test collection:
limactl shell campus-linux-d5-noble-arm64 sudo python3 /tmp/campus-982-in-session.py \
  python3 /tmp/campus-982-store-probe.py cycle --disposable-collection
```

The optional mode uses standard `CreateCollection` with an empty alias and the label
`Campus 982 disposable synthetic collection`. The actual desktop prompts choose a
disposable collection password and later unlock it; no password enters this script's
arguments or files. Its item has unique synthetic attributes and the separate reader
targets that exact item. Cleanup may delete only the collection newly returned in this
run, never a preexisting collection or a current default/login alias. Final success
requires item removal, collection removal, preserved default/login aliases and preserved
preexisting collection paths. A canceled prompt, unknown collection identity or failed
cleanup returns failure. Host mocked API checks exercise immediate/prompted creation,
preexisting-path rejection and canceled deletion; they are not actual Secret Service
or graphical prompt evidence.

Inspect the actual password field before invoking `qmp-console.py password` with the
private support credential file path. No password is passed in an argument, printed,
captured or committed. The Secret Service payloads are synthetic. Retain output and the
exact script hashes; do not replace a failing capture with a passing claim.
For a new collection's first password field, `qmp-console.py password --no-enter PATH`
types without submitting; move to the confirmation field and inspect focus before the
second entry. Wait for the resulting dialog transition before sending further keys.
The [credential remediation receipt](receipts/credential-remediation.json) records the
earlier serial-prompt echo defect, private scan, three redacted local serial-log occurrences
and Unix password rotation. No checked-in receipt contained the password; rotation did
not rekey the original login collection and must not be presented as doing so.

## Real graphical supervision

`session-service.py` installs only `campus-982-session-spike.service` and a hashed helper
under `~/.local/share/campus-982-spike/session/versions`. Its stable `current` pointer lives
outside AppImage mounts. `Requisite`, `After` and `PartOf` bind it to
`graphical-session.target`; lingering remains disabled. The fixture uses cleared environment,
whole-cgroup stop and a two-second synthetic grace. Its restart delay starts at 250ms,
increases over three steps to a two-second cap, and does not permanently exhaust a start
limit. Three intentional exit-75 failures recovered; intentional exit zero stayed stopped.

Actual Wayland logout through `gnome-session-quit --logout --no-prompt` stopped the unit
and graphical target while a **same-user SSH session remained open**. An explicit start
at the greeter was refused by the target prerequisite. The SSH session uses a disposable
restricted key with a fixed sleep command, never the owner's provider credentials.

Receipts: [retry timing](receipts/session-wayland-retries.json),
[intentional stop](receipts/session-wayland-intentional-stop.json),
[logout with SSH](receipts/session-wayland-logout-ssh-open.json),
[greeter refusal](receipts/session-greeter-start-refused.json).
The [cold-start/login receipt](receipts/session-cold-login-no-ui.json) also records the
stable helper admitted without a UI on a new boot ID
`4bd8ede4-223b-40ab-a4d2-32b6534e20b7`, retaining synthetic epoch4 from the preceding boot.
The user unit and graphical target were active. This establishes the fixture's cold-login
restart observation; it is not pre-login execution or recovery of actual Rails leases.
Synthetic durable epochs illustrate local revocation fencing; ordinary relaunch keeps the
epoch and explicit reset changes it. This is not implementation of server revocation,
lease reconciliation or the four recovery-drill boundaries. L2/#989–#990 must bind those
to merged contracts and actual Rust helper processes. LINUX-16/17 (#996/#997) must repeat
every applicable case with final installed product packages.

## Final disposable cleanup

The [cleanup receipt](receipts/cleanup-final.json) verifies removal of the test root
installers, polkit actions/rules, packages, session unit and synthetic private signing
keys. [Package-manager output](receipts/package-cleanup.txt) and the
[unit cleanup](receipts/session-cleanup.json) are preserved. The restricted disposable
SSH key was removed while preserving other authorized-key bytes; its host temporary
key directory was also removed. Polkit was restored, idle delay restored to300 seconds,
and user/provider data plus the original locked login keyring were preserved.
