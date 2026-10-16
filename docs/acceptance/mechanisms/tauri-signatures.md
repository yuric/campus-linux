# #982 second signature probe: actual Tauri minisign verification

This separately named disposable experiment addresses the signature-format gap in the
[earlier package experiment](packages.md). It does not replace the earlier OpenSSL
signature scheme, keys, scripts or receipts. It creates no owner/release key and does not
change product dependencies. Guest execution belongs to the parent #982 operator;
LINUX-20261016 owns admission and the handoff to #996.

The [builder](../../../spikes/982/packages/build-tauri-verifier.py) fetches the same pinned
2.14.0 updater crate and extracts its exact `verify_signature`, `verify_signed_version`,
`signed_version` and `base64_to_string` functions. It compiles them with rustc against the
three versions/checksums recorded by that crate's `Cargo.lock`, without a registry resolver:

| Source | Version | Crate SHA-256 |
| --- | --- | --- |
| tauri-plugin-updater | 2.14.0 | `7259989d4fe11b2bf51f7d671642249b1837c4ae2da1430dc713ae38f98ceeec` |
| minisign-verify | 0.3.0 | `871285dc19d8d0ebe0eef3d0e99a205f2a71363b122632cbbfa4a6c370a960ce` |
| base64 | 0.22.1 | `72b3254f16251a8381aa12e40e3c4d2f0199f8c6508fbecb9d91f575e0fbb8c6` |
| semver | 1.0.28 | `8a7852d02fc848982e0c167ef163aaff9cd91dc640ba85e263cb1ce46fae51cd` |

The crate sources and licensing remain in guest scratch. The checked-in builder pins
all downloaded bytes and writes compiler commands, compiler version, extracted function
hash, wrapper hash and executable hash to `verifier-build.json`. These are actual updater
verification functions, not a reimplementation of Ed25519 or the minisign envelope.
The enclosing Tauri app/plugin, bundle detection and installed-artifact routing are **not**
compiled by this experiment.

[Minisign's documented format](https://jedisct1.github.io/minisign/) includes an authenticated
trusted comment as well as the artifact signature. The [signer](../../../spikes/982/packages/sign-tauri-fixtures.py)
creates an unencrypted **test-only** key in a new private `tauri-minisign` fixture directory,
never in the owner key location. It signs the existing disposable deb bytes and wraps the
entire minisign signature/public-key text in standard base64, exactly as the pinned Tauri
functions decode them. A signed `version:0.982.1` or `version:0.982.2` field uses the actual
tab-separated trusted-comment convention. The original OpenSSL signatures/key stay intact.

The wrapper always sets `require_signed_version=true`. A valid signature without a signed
version must fail, as must a response announcing a different version. The upstream verifier
checks the global signature before reading this comment. Its legacy-minisign compatibility
flag is preserved exactly; this is not permission to accept an arbitrary raw OpenSSL
signature, unsigned version or alternate key. No negotiation, TLS-only mode or weaker
signature fallback is implemented.

[The second privileged helper](../../../spikes/982/packages/privileged-tauri-install.py)
uses only `/var/lib/campus-982-tauri-spike/public-key.b64` and a root-owned fixed verifier
binary. Its action, executable, marker, staging directory and polkit rule have separate
test names. It accepts bounded byte/signature/version JSON, stages exact package bytes in
root-owned private storage, invokes the actual Tauri verifier, compares package metadata to
the authenticated announced version, checks the same narrow package/archive bounds, and
runs fixed dpkg on those root-owned bytes. The caller never supplies a privileged input
path, key path or executable. A deliberate test pause exercises substitution of the original
user download after verification. There is no sudo or application-collected password fallback.

Commands below are fixture provisioning inside the owned guest. `EXISTING_FIXTURE` must
refer to the earlier built packages and negative fixtures. Use a new verifier output path.

```sh
sudo apt-get install --no-install-recommends minisign
python3 spikes/982/packages/build-tauri-verifier.py --output /tmp/campus-982-tauri-verifier
python3 spikes/982/packages/sign-tauri-fixtures.py --fixture EXISTING_FIXTURE
sudo python3 spikes/982/packages/prepare-tauri-guest.py --user campusqa \
  --fixture EXISTING_FIXTURE --verifier /tmp/campus-982-tauri-verifier/tauri-signature-verify \
  --mode allow
python3 spikes/982/packages/test-tauri-install.py --fixture EXISTING_FIXTURE \
  --output /tmp/campus-982-tauri-allow.json
```

The allow rule measures signature/root-byte mechanisms only. Repeat the root setup with
`--mode prompt`, then run the test with `--prompt` under each real GDM session to observe
actual administrator authentication. `--mode deny` plus test `--denied` records intact
installation on refusal. With prompt mode, cancellation can also be observed by invoking
`--denied` and dismissing the real dialog. Capture no password/private-key bytes.

```sh
sudo python3 spikes/982/packages/prepare-tauri-guest.py --user campusqa \
  --fixture EXISTING_FIXTURE --cleanup
```

Cleanup removes only this action/rule/root trust anchor/verifier/helper and the disposable
package. It does not remove or change the older OpenSSL action. Delete synthetic private
keys in the caller-owned fixture after preserving public-key fingerprints, signature/source
artifact hashes, commands and safe result captures. Never publish a generated private key.

The test suite includes a valid signed-version install; package byte tamper; wrong key;
cryptographically valid but unversioned signature; signed/announced-version mismatch;
trusted-comment tamper; raw OpenSSL signature format rejection; wrong package/architecture;
signed maintainer script, symlink, unrelated path, setuid, oversized expanded archive,
wrong-owner and writable-helper rejection; and original
file substitution after privileged verification. Missing negative fixtures are recorded as
blocked and force a nonzero aggregate result. Result JSON is saved even if a case fails.
The current driver compares each positive install with the expected fixture helper
digest, requires all seventeen cases, and records its own source hash. Before the bounded
expansion negative was added, the
[strengthened Wayland run](receipts/tauri-install-wayland-allow-final.json) and
[strengthened X11 run](receipts/tauri-install-x11-allow-final.json) each passed all
fourteen cases with script SHA
`3c220e73d12fff6375ca9c04b0787c5d055cc5e127e9f810148f3d875bce2538`.
The historical X11 run below, without the `-final` suffix, used its earlier assertions.
The current seventeen-case runs on [X11](receipts/tauri-install-x11-schema.json) and
[Wayland](receipts/tauri-install-wayland-schema.json) passed the streaming subprocess-output
bound and exact archive schema with driver SHA
`15ce813245922d7668522a0d80fad3a7d34d121102c9c03cb5a3f637f8a2c9fd`.
Both preserve installed helper bytes on all three new signed negatives. The installed
root helper's corresponding source SHA is
`f59d75f3e67e47285c31f7689a90311a575050f06cd187c17df3adad99d57111`.
The added expansion payload is only 256KiB before
compression; ownership/mode negatives are tiny copies. No large resource probe is
needed. The exact schema requires root-owned directories 0755, control 0644 and helper 0755,
all required paths once and no extra metadata. Host checks reject incorrect types,
duplicates, missing entries, UID/GID, modes and PAX extensions. Historical fourteen-case
results retain their exact recorded scope.

The [guest build receipt](receipts/tauri-verifier-build.json) records successful compilation
with Ubuntu rustc 1.75.0 and verifier SHA-256
`203431af56bea2b4624c2f17f6179fbb0a95978c8012c80a870f4bc46f838471`. This is a source-extracted
verification experiment, not the Rust 1.99.1 product build. The
[X11 privileged run](receipts/tauri-install-x11-allow.json) passed all **fourteen** cases.
The exact source-function block hash is
`116d93fcf08a6a3d8cb6d9a70e8f3dd9d9ff860d8de219de79d34e8e58db572b`.
This run used the test-specific polkit allow rule. Separate
[real X11 prompt authentication](receipts/tauri-install-x11-prompt.json) and
[expected X11 prompt dismissal](receipts/tauri-install-x11-cancel-expected.json) were then
observed in this second namespace. The earlier
[dismissed positive expectation](receipts/tauri-install-x11-cancel.json) correctly failed
after deliberate Escape and remains as a failed observation, not a passing cancellation
test.

The final exact-schema driver passed actual password prompts on
[Wayland](receipts/tauri-install-wayland-schema-prompt.json) and
[X11](receipts/tauri-install-x11-schema-prompt.json), plus Wayland
[expected dismissal](receipts/tauri-install-wayland-schema-cancel.json) and
[missing polkit authority](receipts/tauri-install-wayland-schema-polkit-missing.json).
Each positive case checks the installed helper against the expected v2 fixture digest;
both negative cases record unchanged helper bytes. The authority was temporarily masked
at runtime and the operator unmasked/restarted it afterward. This proves absence handling
for the authority, not a separate missing desktop-agent case. No alternate elevation path
was invoked.

Even a successful run is limited to these test keys, package bytes and exact extracted
verification functions. The final product must integrate the trust anchor under owner
custody, prove the same protected install step, handle interrupted dpkg and external package
replacement, and select all four manifest targets from real installed packages. Stock
updater deb elevation still contains the prohibited fallback. This probe neither accepts
that behavior nor makes a production/release admission claim.

## Final disposable cleanup

The [cleanup receipt](receipts/cleanup-final.json) verifies removal of the test root
installers, polkit actions/rules, packages, session unit and synthetic private signing
keys. [Package-manager output](receipts/package-cleanup.txt) and the
[unit cleanup](receipts/session-cleanup.json) are preserved. The restricted disposable
SSH key was removed while preserving other authorized-key bytes; its host temporary
key directory was also removed. Polkit was restored, idle delay restored to300 seconds,
and user/provider data plus the original locked login keyring were preserved.
