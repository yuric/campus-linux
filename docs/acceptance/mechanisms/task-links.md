# Disposable task-link desktop activation probe

This is #982 mechanism work, with next owner LINUX-20261016. The pinned Mac bridge
inventory is in [renderer-speech.md](renderer-speech.md#task-links-observed-source-and-bounded-next-probe).
The shipped HTTP `task_link.href` remains authoritative and must be copied verbatim.
The following probe covers only the `campus://` desktop activation seam. It does not
invent a replacement href or make an API request. No local HTTP listener or extra
background service is installed by this experiment.

The [fixture builder](../../../spikes/982/links/build-fixtures.py) produces a separate,
unsigned `campus-982-links-disposable` deb and AppImage. Both contain the identical
[GTK handler](../../../spikes/982/links/handler.py), whose only principal is the synthetic
`https://fixture.example.invalid`. It uses GTK3 and Python already available in the guest,
not a product framework choice. The AppImage uses the same hash-pinned type-2 runtime as
the [package probe](packages.md); all generated artifact/handler hashes are recorded.
There is no updater/release trust claim for these unsigned fixtures.

The first URI creates a window and D-Bus-registered `Gtk.Application`. A second URI reaches
the existing application/window, requests presentation and records its PID and actual
window active/visible observations. The application exits when the window closes or the
cleanup command asks its existing D-Bus instance to quit. This is a single UI process,
not an installed second service. Same-user D-Bus access is not an account-authentication
boundary; the principal restriction is explicitly synthetic. Actual signed-in island
and account authorization remain server/product work.

Run the following only in the owned disposable guest. The explicit root `dpkg` command
is fixture provisioning, not the in-app update path or a polkit fallback. The deb has no
maintainer scripts and owns only its distinct handler directory.

```sh
python3 spikes/982/links/build-fixtures.py --output /tmp/campus-982-link-packages \
  --runtime /tmp/campus-982-appimage-runtime-aarch64
sudo dpkg --install /tmp/campus-982-link-packages/campus-982-links-disposable.deb
```

Run each tuple under the actual display-manager session's graphical environment and user
bus. Use a fresh root for each tuple. The executable passed below is a fixed local package
path; a URI is always a separate argument, never shell syntax.

```sh
python3 spikes/982/links/probe.py --format deb \
  --executable /usr/lib/campus-982-links-disposable/handler.py \
  --root /tmp/campus-982-links-wayland-deb
# Capture the visible window before cleanup.
python3 spikes/982/links/probe.py --root /tmp/campus-982-links-wayland-deb --cleanup
python3 spikes/982/links/probe.py --format appimage \
  --executable /tmp/campus-982-link-packages/campus-982-links-disposable.AppImage \
  --root /tmp/campus-982-links-wayland-appimage
# Capture the visible window before cleanup.
python3 spikes/982/links/probe.py --root /tmp/campus-982-links-wayland-appimage --cleanup
```

Repeat both commands in GDM X11 using distinct `...-x11-...` roots. Preserve `result.json`,
`events.jsonl`, `cleanup.json`, the package artifact manifest and screenshots alongside the
actual loginctl/graphics receipt. Do not publish `state.json`: it holds private backups of
the user's MIME configuration solely for restoration. It contains no Campus credentials.
After all tuples, remove only `campus-982-links-disposable` with `sudo dpkg --remove` and
remove only the freshly created caller-owned fixture directories.

The [probe](../../../spikes/982/links/probe.py) registers a unique test `.desktop` with
`MimeType=x-scheme-handler/campus` and a direct `Exec` plus `%u`. It records the prior
association and exact affected MIME-file bytes/modes, checks the new `xdg-mime` default,
then runs real `xdg-open` calls. An xdg-open exit is insufficient: each case needs an
actual accepted/rejected handler receipt. Cleanup restores the previous bytes/default
and removes the test desktop entry. Cooperative snapshot checks refuse changed bytes
and require explicit reconciliation. No-follow file descriptors reject final-component
symlinks and nonregular files; this is not atomic protection against adversarial same-user
mutation or parent-directory replacement. Use only the owned disposable guest.

Cases: cold start; second activation in the same PID/window; empty, Unicode, overflow or
encoded-separator ID; foreign/userinfo island; fragment; duplicate or unknown query
fields; missing island. The test parser accepts only the pinned URI shape with an ASCII
positive signed-64-bit fixture ID and exact synthetic origin. It never changes an API
origin or enrollment policy. This grammar is a bounded adapter experiment, not a new
client-owned catalog or business rule. Rejected URLs are not copied to event logs.

For AppImage, `window_created` must contain the actual runtime's `APPIMAGE` and matching
`/proc/self/mountinfo` entry for the bundled handler. Extraction-only execution fails this
specific probe. This distinguishes a genuinely mounted package UI from the earlier
filesystem-only helper model. The final Tauri product still needs its own desktop-entry,
mount/runtime, task fetch, navigation/focus and account-lifecycle tests.

The current real-session receipts cover all four arm64 package/session tuples. Each
records twelve passing navigation cases: cold start, same-window reuse and ten hostile
URI/principal rejections. The paired window observations are active and visible, and
cleanup restores the original empty MIME default, removes the test desktop entry and
stops the test UI. The latest deb/Wayland runs originated in the real session's graphical
terminal; an SSH-origin launch is a distinct activation context.

| Tuple | Navigation/focus evidence | Cleanup evidence |
| --- | --- | --- |
| X11 installed deb | [Current no-follow result](receipts/links-x11-deb-nofollow-result.json), [timed events](receipts/links-x11-deb-nofollow-events.jsonl): PID 5378, two active/visible observations, twelve cases pass | [PASS](receipts/links-x11-deb-nofollow-cleanup.json), UI stop exit 0 |
| X11 mounted AppImage | [Current no-follow result](receipts/links-x11-appimage-nofollow-result.json), [timed events](receipts/links-x11-appimage-nofollow-events.jsonl): PID 5870, two active/visible observations, twelve cases pass | [PASS](receipts/links-x11-appimage-nofollow-cleanup.json), UI stop exit 0 |
| Wayland installed deb | [Current no-follow result](receipts/links-wayland-deb-nofollow-result.json), [timed events](receipts/links-wayland-deb-nofollow-events.jsonl): PID 8240, two active/visible observations, twelve cases pass | [PASS](receipts/links-wayland-deb-nofollow-cleanup.json), UI stop exit 0 |
| Wayland mounted AppImage | [Current no-follow result](receipts/links-wayland-appimage-nofollow-result.json), [timed events](receipts/links-wayland-appimage-nofollow-events.jsonl): PID 8758, two active/visible observations, twelve cases pass | [PASS](receipts/links-wayland-appimage-nofollow-cleanup.json), UI stop exit 0 |

All four current result/cleanup receipts bind updated probe hash
`a59d69833f46b76106d67036ab5ffc30bdf04b80a3ab336098d6bfa8024f6cd1`.
The preceding terminal deb/Wayland runs remain preserved with probe hash
`3793a864cf9e8388831b9e1bcfc661359f76e4f0524846e9696973f3ea37c3cc`.
The actual AppImage receipts include its read-only FUSE mount, executable path inside
that mount and `APPIMAGE`; these are mounted-package observations.
[Artifact hashes](receipts/link-artifacts.json) bind the separate unsigned spike packages.
The [Wayland deb screenshot](receipts/links-wayland-deb.png) was taken after terminal/UI
exit and shows the desktop only. It **does not prove activation or focus**; the timed
handler events above supply that evidence. Earlier X11 screenshots remain supplemental
captures of their particular attempts, not substitutes for current timed events.

Preserve the original [SSH-origin deb focus failure](receipts/links-x11-deb-final-result.json):
its twelve navigation cases passed, but both windows were visible and inactive, reported
as **FAIL_OR_UNOBSERVED**. The later graphical-terminal run passes that same narrow focus
check; it does not erase the failure or establish that every launch origin can focus a
window. Product/browser activation and compositor policies still require final-package
coverage. The corrected driver returns nonzero after preserving a failed focus or UI-stop
cleanup receipt. Earlier positive [deb](receipts/links-x11-deb-result.json) and
[AppImage](receipts/links-x11-appimage-result.json) attempts remain in the record.

In particular this experiment does not
prove the existing `http://localhost:3979/task-...html?island=...` path, occupied port,
Host/Origin/method/body restrictions, nonloopback rejection, missing-app HTTP handling,
or a Linux loopback bridge lifecycle. Those remain explicit #994/#989 gaps for
LINUX-20261016; no permanent listener is selected by this spike. Final product repetition
belongs to #997/#998 after #994/#996.

The cleanup receipts prove restoration in those isolated runs only. Source review found
that the original read-by-path hash check followed by `write_bytes` could follow a same-user
symlink substitution. The corrected probe uses `O_NOFOLLOW` regular-file descriptors for
snapshot verification and restoration, including the actual write; desktop creation is
exclusive. Host regression checks prove changed-byte/symlink/FIFO refusal, target
preservation, original mode/byte restoration and temporary-file removal. The updated
probe hash is `a59d69833f46b76106d67036ab5ffc30bdf04b80a3ab336098d6bfa8024f6cd1`;
the table above now records reruns of these exact bytes in all four tuples.
Earlier terminal/X11 AppImage and Wayland receipts remain unchanged, including their
original driver hashes. No adversarial same-user atomicity or owner-data safety guarantee
is claimed. Review disposition and scope are recorded in [renderer-links-speech-review.md](renderer-links-speech-review.md).
