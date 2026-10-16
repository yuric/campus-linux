# Disposable privileged fixture adapter

This is a narrow #1057 experiment, not a production installer. Its fixed package is
`campus-updater-1057`; admitted versions are exactly `1.0.0`, `2.0.0`, and `3.0.0`.
The verifier and public key are provisioned independently of the deb payload.

`make-admission.py --architecture arm64 --output admission.json v1.deb v2.deb v3.deb`
measures the actual Tauri packages. It records exact package hashes and sizes, control
and data member names, types, modes, owners, sizes and file hashes. The copy and expanded
data bounds equal the largest measured fixtures, with separate defensive absolute ceilings.
The reviewed data layout permits only the app, inert helper, desktop entry, PNG icons and
their parent directories. Scripts, links, devices, unreviewed control members and
package relation fields capable of replacing another package are refused. An unfamiliar
real bundler layout fails generation; it requires a reviewed source change, not a relaxed
root installer. The generated admission must be reviewed with the hosted receipt before
provisioning. This deliberate exact-hash restriction is appropriate only to a disposable
three-release experiment.

In an explicitly authorized disposable Linux root provisioning session, run:

```sh
python3 adapter/bootstrap.py --bundle /absolute/hosted-output/bootstrap
```

The bundle contains `install-deb.py`, `verify-signature`, `public-key.txt`,
`admission.json`, and `dev.projectcampus.updater1057.policy`. Verify its hosted artifact
receipt first. Bootstrap installs only these fixed trusted files and the private state
directory. It refuses existing trust, accepts no app elevation, performs no deb
installation, and does not acquire root. Initial v1 installation belongs to disposable
environment provisioning, after comparison with its exact admitted bytes. There is no
production key, persistent registry, general package admission, or updater fallback.

An installed unprivileged app invokes exactly:

```sh
/usr/bin/pkexec --disable-internal-agent \
  /usr/lib/campus-updater-1057/install-deb.py /absolute/package.deb /absolute/package.sig
```

Both source files must be regular files owned by polkit's authenticated caller. Final
symlinks are refused. The adapter copies them with bounds into a fresh private root
directory before verification. It uses the root-owned verifier and public key to
authenticate those staged bytes, checks the signed trusted-comment version against the
exact package control version/schema, and checks that the installed app/helper match the
previous admitted fixture. No unsigned caller version is accepted. It holds its own lock
and dpkg's frontend lock across version comparison and installation. Its dpkg child uses
the [documented frontend lock protocol](https://manpages.debian.org/trixie/dpkg/dpkg.1.en.html#DPKG_FRONTEND_LOCKED),
a fixed environment and `--no-triggers --install` on that same root-staged path. Same/lower
signed versions are refused; signed higher v3 can carry deliberately reverted behavior.
The trusted installer, verifier, key, policy and admission paths are forbidden in package
payloads. A caller cannot configure these paths or substitute another executable.

The adapter emits structured receipts containing the stage, result, authenticated version,
package hash/size and installed app/helper hashes before and after the operation. A dpkg
failure is explicitly incomplete recovery evidence; it is not described as an atomic
installation. Full interrupted-dpkg handling remains downstream. The polkit action uses
active-session `auth_admin`, never retained authorization, and refuses inactive/other
sessions. `--disable-internal-agent` prohibits a terminal authentication fallback.

Run the unprivileged stdlib boundary tests with:

```sh
python3 -B -m unittest discover -s spikes/1057/installed-updater/adapter -p 'test_*.py' -v
```

These tests exercise copy confinement, measured bounds, schema rejection and authentication
ordering with synthetic archives and injected verifier/comparison results. They are not
installed-artifact, cryptographic, polkit or desktop evidence. Hosted actual packages and
the later leased GDM session must supply those separate receipts.
