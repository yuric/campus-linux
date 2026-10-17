# Owned Lima mechanism environment

This directory preserves the authorized support configuration and adds probe automation.
Use only `campus-linux-d5-noble-arm64`; do not provision duplicate guests or change UTM.
The independent UTM guest remains outside these tests. One desktop VM at a time; host
free disk must stay at least 35 GiB for large downloads/builds/VM growth. Coordinator
direction 10448 permits short functional probes with a separate 20 GiB host guard and
256 MiB maximum actual additional owned allocation; it does not waive timing holds or
acceptance bars. No host mounts or agent forwarding are configured.

The image is Ubuntu 24.04 arm64 at the exact digest in
`campus-linux-d5-noble-arm64.yaml`. Lima 2.2.1 and QEMU 11.1.2 were observed on the host.
The upstream environment handoff lives outside Git at
`/Users/yuri/.campus/coordinate/linux-20261016/environment/`; only its allowlisted YAML,
session selector and password-setting source were copied. No private support directory,
seed ISO, disk, signing private key or guest password is included.

## Start and recover

```sh
df -h /Users/yuri
limactl list
limactl start --tty=false campus-linux-d5-noble-arm64
```

UTM CLI status returned macOS Automation OSStatus -1743 in this worker context. The
QEMUHelper had no guest disk/network descriptors and no UTM QEMU process was present;
UTM was not launched or modified. This observation does not grant Automation permission.

The prepared Lima guest failed its first unchanged cold start: netplan inherited a global
`NetworkManager` renderer, but that service was absent; eth0 stayed DOWN and networkd
wait-online timed out. The local serial console allowed authenticated recovery using the
disposable `campusqa` account. First per-interface recovery restored SSH but `netplan apply`
still reported absent NetworkManager; setting the global renderer to networkd resolved
that error. The checked-in YAML now sets both explicitly after desktop provisioning.
No online-check service was disabled. Preserve the failed and recovered receipts.

`serial-admin.py` is a guest setup recovery utility, never an updater. It checks login
and sudo prompts before sending private input; it prints only public command output.
Source self-review found that the earlier sudo marker also occurred in the TTY-echoed
command, so matching it could precede sudo disabling echo. The corrected command splits
the shell literal and asserts that its echoed bytes do not contain the contiguous marker;
only the actual sudo prompt supplies that marker. The parent's private scan found three
occurrences of the old disposable password in the local Lima serial capture, with none in
published receipts or the parent's operation log. The parent redacted that local capture,
restricted it to mode0600, and rotated the disposable account password through PAM.
The [remediation receipt](../../../docs/acceptance/mechanisms/receipts/credential-remediation.json)
records outcomes without password values.
The subsequent cold login showed that this PAM password change did not rekey the existing
login collection. Its locked data is preserved. A new unaliased disposable collection can
exercise the Secret Service mechanism, but cannot establish login auto-unlock or repair
the original collection. The [X11 disposable collection run](../../../docs/acceptance/mechanisms/receipts/store-x11-disposable.jsonl)
completed its item/collection deletion and preserved original aliases and collection paths.
The product updater probe exclusively uses polkit and has no sudo/password fallback.

## Authenticated graphical sessions

```sh
python3 spikes/982/environment/select-authenticated-session.py wayland
python3 spikes/982/environment/qmp-console.py capture /tmp/greeter.png
# Inspect the actual greeter, select campusqa:
python3 spikes/982/environment/qmp-console.py key ret
python3 spikes/982/environment/qmp-console.py capture /tmp/password-field.png
# Inspect the actual password field before this operation:
python3 spikes/982/environment/qmp-console.py password /PRIVATE/PATH/campusqa.password
limactl shell campus-linux-d5-noble-arm64 loginctl list-sessions
limactl shell campus-linux-d5-noble-arm64 loginctl show-session SESSION_ID \
  -p Name -p Service -p Type -p Class -p Seat -p Remote -p Active
```

Repeat with `x11`. The expected receipt is `Service=gdm-password`, actual session type,
`Class=user`, `Seat=seat0`, `Remote=no`, `Active=yes`. The copied legacy
`lima-select-setup-session.py` deliberately uses autologin and is **not** used for these
authenticated acceptance observations. It remains labeled setup-only.

QMP is the documented local QEMU input/capture protocol. Password files require current
owner, no group/other access and no symlink. Values remain in memory and the local socket;
never pass passwords as arguments, print them or capture the field during entry. Public
screenshots are taken before secret entry and after the dialog closes. The QMP helper
never prints secret keycodes or raw QMP errors, but it cannot verify the focused widget:
wrong focus could type plaintext into a terminal or another unmasked field. Confirm the
actual focused password field immediately before entry; this is an operator precondition,
not an unconditional guest-console secrecy guarantee. `set-disposable-password.py`
expects a private sibling credential file supplied through the existing secure channel;
it does not generate or publish credentials. The prepared guest already has that password.
For a new keyring dialog with two password fields, use `password --no-enter PATH` for
the first field, then inspect/move focus to its confirmation field before the second
entry. Wait for the next prompt before issuing another key; blindly queued Tab/Return
caused a preserved dismissed-unlock attempt during this run.

`in-session.py` runs inside this exact guest as root, drops to campusqa and whitelists the
actual graphical manager's display environment. Copy it to `/tmp/campus-982-in-session.py`.
Use this launcher for GTK/Secret Service probes; polkit authentication must be launched
through `gnome-terminal --wait -- ...` in the active session. A process merely carrying
display variables from SSH was correctly refused by the active-session polkit policy.

## Additional probe dependencies

The provisioned guest already supplied Python3, GI, WebKitGTK4.1, D-Bus, libsecret,
GNOME Keyring, polkit, OpenSSL, GnuPG and squashfs-tools. This run installed distribution
`rustc` (1.75, solely to compile the extracted updater-selection method) and `xdg-utils`.
This does not change the product Rust pin or add application dependencies.

```sh
limactl shell campus-linux-d5-noble-arm64 sudo env DEBIAN_FRONTEND=noninteractive \
  apt-get install -y --no-install-recommends rustc xdg-utils
```

For source transport use `tar --no-xattrs`; never include private fixture signing keys or
provider state in return archives. Return receipts via explicit filename allowlists.
Normal shutdown is `limactl stop --tty=false campus-linux-d5-noble-arm64`.

Sources: [QEMU QMP](https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html),
[netplan renderer](https://netplan.readthedocs.io/en/stable/netplan-yaml/).
