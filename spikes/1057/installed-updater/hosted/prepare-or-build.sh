#!/bin/bash
set -euo pipefail
umask 077
trap 'chmod -R a+rX /output' EXIT
test "${GITHUB_ACTIONS:-}" = true
test "$(getconf GNU_LIBC_VERSION)" = 'glibc 2.35'
test "$(rustc --version | cut -d' ' -f2)" = 1.99.1
test "$(cargo tauri --version)" = 'tauri-cli 2.12.3'
mkdir -p /output/locks /output/receipts
cp /usr/local/share/campus-1057-build-packages.tsv /output/receipts/
cp /usr/local/share/campus-release-baseline-packages.tsv /output/receipts/
cp toolchain/downloads.json /output/receipts/toolchain-downloads.json
if test ! -f src-tauri/Cargo.lock; then
  (cd src-tauri && cargo generate-lockfile)
  cp src-tauri/Cargo.lock /output/locks/Cargo.lock
  printf '%s\n' '{"phase":"lock-preparation","packages_built":false}' > /output/receipts/phase.json
  exit 0
fi
cp src-tauri/Cargo.lock /output/locks/Cargo.lock
mkdir -p /output/packages /output/bootstrap
# The private key and all signer output remain on a private ephemeral tmpfs.
cargo tauri signer generate --ci --password '' --write-keys /private/signing.key > /private/generation.log 2>&1
cp /private/signing.key.pub /output/bootstrap/public-key.txt
export SPIKE_UPDATER_PUBLIC_KEY
SPIKE_UPDATER_PUBLIC_KEY=$(cat /private/signing.key.pub)
export TAURI_SIGNING_PRIVATE_KEY=/private/signing.key
export TAURI_SIGNING_PRIVATE_KEY_PASSWORD=''
# Build helpers may extract themselves in Docker. Installed smoke never sets this.
export APPIMAGE_EXTRACT_AND_RUN=1
export CARGO_BUILD_JOBS=2
for version in 1.0.0 2.0.0 3.0.0; do
  export SPIKE_FIXTURE_BEHAVIOR=v1-baseline
  if test "$version" = 2.0.0; then export SPIKE_FIXTURE_BEHAVIOR=v2-changed; fi
  python3 hosted/set-fixture-version.py "$version" "$SPIKE_FIXTURE_BEHAVIOR"
  # A single bundler invocation produces BOTH formats, from this exact build.
  cargo tauri build --ci --bundles deb,appimage -- --locked
  python3 hosted/collect-packages.py "$version"
done
(cd src-tauri && cargo build --locked --release --features privileged-verifier --bin verify-signature)
cp src-tauri/target/release/verify-signature /output/bootstrap/
python3 adapter/make-admission.py --output /output/bootstrap/admission.json \
  --architecture "$FIXTURE_ARCH" /output/packages/*.deb
cp adapter/install-deb.py adapter/bootstrap.py adapter/dev.projectcampus.updater1057.policy /output/bootstrap/
python3 hosted/inventory.py
printf '%s\n' '{"phase":"packages-built","installed_smoke":"pending"}' > /output/receipts/phase.json
# No private file is part of /output. Container exit destroys /private.
