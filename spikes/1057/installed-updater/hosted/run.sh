#!/bin/bash
set -euo pipefail
test "${GITHUB_ACTIONS:-}" = true
test "$(git rev-parse HEAD)" = "$EXACT_HEAD"
spike=spikes/1057/installed-updater
python3 -B -m unittest discover -s "$spike/adapter" -p 'test_*.py' -v
python3 -B -m unittest discover -s "$spike/probe" -p 'test_*.py' -v
mkdir -p updater-output/receipts
work=$(mktemp -d "$RUNNER_TEMP/updater1057.XXXXXX")
container="campus-1057-build-${FIXTURE_ARCH}"
export FIXTURE_OWNER="$(id -u):$(id -g)"
trap 'docker rm -f "$container" >/dev/null 2>&1 || true; rm -rf "$work"' EXIT
git archive HEAD > "$work/source.tar"
tar xf "$work/source.tar" -C "$work"
export SOURCE_ARCHIVE_SHA256
SOURCE_ARCHIVE_SHA256=$(sha256sum "$work/source.tar" | cut -d' ' -f1)
rm "$work/source.tar"
python3 - <<'PY'
import hashlib, json, os, pathlib, subprocess
paths = ['ci/Dockerfile.release-baseline', 'ci/toolchain-lock.json',
         'spikes/1057/installed-updater/hosted/Dockerfile.build']
receipt = {'source_head': os.environ['EXACT_HEAD'], 'source_archive_sha256': os.environ['SOURCE_ARCHIVE_SHA256'],
           'architecture': os.environ['FIXTURE_ARCH'], 'runner': os.environ.get('RUNNER_NAME'),
           'run_id': os.environ['GITHUB_RUN_ID'], 'run_attempt': os.environ['GITHUB_RUN_ATTEMPT'],
           'baseline': json.loads(pathlib.Path('ci/toolchain-lock.json').read_text())['release_base'],
           'recipe_sha256': {p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in paths},
           'commands': ['docker build ci/Dockerfile.release-baseline', 'docker build hosted/Dockerfile.build',
                        'hosted/prepare-or-build.sh'], 'result': 'started'}
fixture_paths = subprocess.check_output(['git', 'ls-files', '-z', '--',
    'spikes/1057/installed-updater', '.github/workflows/l0-installed-updater.yml'], text=True).split('\0')
fixture_files = {p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in sorted(fixture_paths) if p}
fixture_hash = hashlib.sha256(json.dumps(fixture_files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
receipt['fixture_tree_sha256'] = fixture_hash
pathlib.Path('updater-output/receipts/fixture-inputs.json').write_text(json.dumps(fixture_files, indent=2)+'\n')
pathlib.Path('updater-output/receipts/build.json').write_text(json.dumps(receipt, indent=2)+'\n')
PY
docker build --progress=plain -f ci/Dockerfile.release-baseline -t campus-1057-release-baseline .
docker build --progress=plain -f "$spike/hosted/Dockerfile.build" -t campus-1057-builder .
docker image inspect campus-1057-builder --format '{{.Id}}' > updater-output/receipts/build-image-id.txt
timeout 2400 docker run --rm --name "$container" --cpus 2 --memory 6g --pids-limit 1024 \
  --tmpfs /private:rw,noexec,nosuid,size=4m,mode=0700 \
  -e GITHUB_ACTIONS=true -e FIXTURE_ARCH -e EXACT_HEAD -e FIXTURE_OWNER \
  -v "$work:/work" -v "$PWD/updater-output:/output" \
  campus-1057-builder bash hosted/prepare-or-build.sh
if test ! -d updater-output/packages; then
  echo 'Lock preparation only; no build or installed evidence yet.'
  exit 0
fi
test -e /dev/fuse || { echo 'Actual AppImage runtime blocked: hosted /dev/fuse absent'; exit 1; }
docker build --progress=plain -f "$spike/hosted/Dockerfile.smoke" -t campus-1057-smoke .
docker image inspect campus-1057-smoke --format '{{.Id}}' > updater-output/receipts/smoke-image-id.txt
timeout 900 docker run --rm --network none --cpus 2 --memory 4g --pids-limit 512 \
  --device /dev/fuse --cap-add SYS_ADMIN --security-opt apparmor=unconfined \
  -v "$PWD/updater-output:/input:ro" -v "$PWD/updater-output/receipts:/receipts" \
  campus-1057-smoke
