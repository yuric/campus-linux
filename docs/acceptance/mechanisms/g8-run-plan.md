# G8 source preparation and next authorized run

LINUX-20261016 / #982. Direction1229 prepared this plan. Direction1240 subsequently
returned the existing Lima lease to Office400 for native preflight, fresh untimed motion
proof and proof-bound freeze only. **Timing, optimization and Electron remain withheld.**
The current slice allows64MiB new allocated source/export/receipts inside the earlier
256MiB aggregate guest budget, with20GiB host and2GiB guest free. No install, build,
download, provider/account use or CI/Council watcher is authorized. The separate35GiB
large-growth guard remains. See the [returned evidence](receipts/g8-native-1240/REPORT.md).

## Inputs and reconciliation

The active WebKit freezer/runner and Electron runner now use
[desktop-producer-manifest.json](../../../spikes/982/renderer/desktop-producer-manifest.json),
SHA256 `7b5fabefd830d3cd3d3577da1c4cb4ba55217de0f7eb5b5bbfc9501443428f09`.
Producer [Mac PR114](https://github.com/yuric/campus-macos/pull/114) merged at
`3e3d4bcd64fd1504c4546b2f7a063b55e2eea783`. Live GitHub comparison confirms it is an
ancestor of main. Recipe `campus-island-desktop-v1`; archive SHA256
`30872d807a5750769e12631841ef5ba7cded56911bd5b90333f006f9ea642654`;
bridge schema SHA256 `4d73eea8fb118df341bd98600ee0c06aba4f33018cc0f01ab586918a8e0fa91c`.
The producer's contract provenance remains `yuric/campus-server@d93b841762183af5ba0d357f3f1c42351aeed9ff`;
this is not a Linux API snapshot import or current API compatibility claim.

Existing coordinator artifacts are `reviews/macos-pr114-final-exports/desktop-first` and
`desktop-second`, relative to the existing Linux coordinator directory. Both complete
exports pass the merged producer's verifier with these external expected pins. Reuse those
bytes, including schema/licenses/modes, without rebuilding. The JavaScript payload is
`Island/assets/island-B3jZU801.js`, SHA256
`1a409b8e7bb93bd3bed44b430b347708518010a03f00ae56f99c89448ebeefcf`.
The [source receipt](receipts/g8-sourceprep-1229/source-receipt.json) records inspected
producer source and preserved prior harness bytes; the [source inventory](receipts/g8-sourceprep-1229/source-hashes.json)
binds this prepared candidate. Neither file is a timing freeze.

The merged producer retains the same `{kind:"presentation"}` request and
`{reachable:true,status:200,body}` transport stub, `Island/island.html`, public
focus/lifecycle methods and camera geometry. `scene.ts` is byte-identical to the prior
producer. The desktop bridge is opt-in. This rendering-only probe deliberately continues
without `campusDesktopHost` or `campusHost`: actions remain unavailable and the fixture is
unchanged. It tests the merged renderer payload, not desktop bridge behavior or functional
parity. Producer-owned bridge/native-host acceptance remains downstream.

Fixed inputs remain12projects/48agents/180tasks, fixture SHA256
`16dc931ccaa50a62d350beba44bc64a5a858ed655eb47637f5fda7fedf97d074`, seed98120261016,
4CPU/6GiB/28GiB Ubuntu24.04 arm64,1440x900 CSS viewport, device/render scale1,
light normal motion, Mesa llvmpipe. Preserve the [protocol](../visual-protocol.json):
30s warmup covering all six segments, then60s six-segment measurement, nearest-rank
p95<=33.3ms **in each of five fresh-process runs**. No pooling, discarded stalls,
minimum-frame-count or new maximum-gap bar.

## What must be fresh

For **each real GDM X11 and Wayland session**, and again for a changed compositing candidate:

1. Observe boot/session/PID identity and current OS/kernel/package/backend/rendering settings,
   VM resources, viewport/scale and host contention. Launch from the actual authenticated
   graphical session; do not substitute an SSH compositor or copied environment alone.
   Preserve the launch PID/start/cgroup-to-session evidence beside the captures.
2. Capture native `webkit://gpu` and successful renderer preflight with the new export.
   Native version/backend/llvmpipe and live candidate descendant software threads must agree.
   A changed WebKit version fails closed pending source reconciliation; do not edit its
   expected string to pass. Observe environment values afresh, never copy historical JSON.
3. Make a diagnostic-only freeze with current source hashes; run a fresh **untimed** motion
   proof. Require both settled absolute1 resets and1.5/0.75/1 targets within1e-5 through
   normal wheel input, actual main projection, complete finite ordered warmup/measurement
   six-segment inputs/gestures and seven checkpoints, foreground/visibility and no errors.
   Both clock resets restore projection observation; motion proof has zero performance frames.
4. Freeze that proof's hash, exact native/environment evidence and current source bytes
   before timing. Run-five/summarizer hashes must be current as well. Record the resulting
   freeze digest externally. Stop on any mismatch; no hand-editing old proof/freeze hashes.

The old v7 proofs bind producer8e39806, runner19111e1b and checker ec3a984d. The current
checker changed to9f369d17 and the driver to0d87b9cd during the source repairs; this update
also changes producer manifest and runner. Thus neither old v7 nor the repair1200
source-only inventory admits timing. A summarizer-only edit would require refreezing the
current summarizer/run-five inputs; the present motion/driver/producer changes additionally
require the actual fresh untimed proof above. New unrelated G4/speech source is not a reason
to repeat renderer proofs. Historical failed/aborted traces remain immutable and excluded.

## Executable sequence for the later guest window

Set `REPO`, `EXPORT`, `OUT`, and `ENVIRONMENT` to absolute owned guest paths.
`GPU` is generated below under the fresh `OUT`; it is not an existing host input.
`EXPORT` must be a mode-preserving transfer of the already verified complete desktop export;
`OUT` must be new for this session/candidate. `ENVIRONMENT` is a newly observed JSON with
`webkit`, `mesa`, `llvm`, `kernel`, `architecture`, `os`, `session`, `graphics`,
`webgl_api_renderer`, `rendering_env`, `compositing_policy`. Retain raw `loginctl`,
`/proc/PID/{stat,cgroup}`, boot ID, `uname`, `dpkg-query`, VM resource and display observations
alongside it. Copy only `rendering_env` and `webgl_api_renderer` from this run's preflight.
These observations are prerequisites, not values to infer from the example historical files.

On the host, before transfer, use the existing clean merged producer checkout's verifier
(no export/build/install command):

```sh
PRODUCER=/Users/yuri/.campus/coordinate/linux-20261016/fixes/macos-pr114
EXISTING_EXPORT=/Users/yuri/.campus/coordinate/linux-20261016/reviews/macos-pr114-final-exports/desktop-first
node "$PRODUCER/island/scripts/verify-desktop-export.mjs" \
  --input "$EXISTING_EXPORT" \
  --source 3e3d4bcd64fd1504c4546b2f7a063b55e2eea783 \
  --contract-source yuric/campus-server@d93b841762183af5ba0d357f3f1c42351aeed9ff \
  --manifest-sha256 7b5fabefd830d3cd3d3577da1c4cb4ba55217de0f7eb5b5bbfc9501443428f09
```

In the authorized actual GDM session, with the observed environment and unchanged installed
runtime, run each command only after its predecessor succeeds. Preserve stdout/stderr and
failed outputs; never reuse an output path. `POLICY=on-demand` for baseline.

```sh
set -eu
cd "$REPO"
mkdir "$OUT"
R=spikes/982/renderer
export LIBGL_ALWAYS_SOFTWARE=1
POLICY=on-demand
GPU="$OUT/gpu.json"
python3 -B "$R/capture-gpu.py" > "$GPU"
python3 -B "$R/run-webkit.py" --preflight --compositing-policy "$POLICY" \
  --native-gpu-receipt "$GPU" "$EXPORT" ignored "$OUT/preflight.json"
```

**Stop here.** Inspect the successful preflight and fresh session/package/display/native
observations, then write `ENVIRONMENT` with those actual values. This is a manual observation
step; a shell comment does not collect evidence. A viewport refusal requires preserving
that output and a fresh preflight at1440x900scale1, not changing the expected dimensions.
Only after this step, in the same authenticated graphical session:

```sh
python3 -B "$R/freeze.py" --native-gpu-receipt "$GPU" \
  "$ENVIRONMENT" "$OUT/diagnostic-freeze.json"
python3 -B "$R/run-webkit.py" --motion-proof --compositing-policy "$POLICY" \
  --native-gpu-receipt "$GPU" "$EXPORT" "$OUT/diagnostic-freeze.json" "$OUT/motion.json"
python3 -B "$R/freeze.py" --native-gpu-receipt "$GPU" --motion-proof "$OUT/motion.json" \
  "$ENVIRONMENT" "$OUT/timing-freeze.json"
sha256sum "$OUT/timing-freeze.json"
```

Stop here unless the coordinator's separately observed timing window is active and all
session/resource/contention predicates still hold. Diagnostics can take180s overall;
normal hosts retain115s and the five-run wrapper125s per subprocess. The durations above
are not new performance thresholds. Then:

```sh
python3 -B "$R/run-five.py" --native-gpu-receipt "$GPU" \
  "$EXPORT" "$OUT/timing-freeze.json" "$OUT/baseline-five"
```

Capture host load before/after from the host (`date -u`, `uptime`, `vm_stat`, `df -k`),
without operating another Office's processes. An interruption/invalid workload aborts that
series and preserves its outputs; a valid slow run stays in its five-run series. Preserve
all raw JSON/logs and summary, hash/index them, and report each p95 plus all-five result.
An exit0 from the host is not a numeric pass. No old aborted run becomes a baseline miss.

On a verified miss, test the existing allowed `always` compositing candidate using a new
output directory, `POLICY=always`, newly observed effective policy/environment, new native
capture/preflight/motion/freeze, and another complete five-run series. No scene/scale/
producer/threshold change or renderer optimization fork. If it still misses, follow D1's
[Electron fallback sequence](../../../spikes/982/renderer/electron/README.md) with the same
new desktop pin and fixed scene/bars. Its44.8.0 archive/extraction is currently absent;
426,442,476bytes must be separately budgeted/scheduled by root before acquisition.
Neither direction1229 nor1240 authorizes that allocation/download or any fallback launch.

Remaining next owner: explicit human handoff to LINUX-20261016 for returned-evidence review,
exact-head hosted checks/admission/Council and separately observed guest/timing scheduling.
No worker wakeup is assumed. G8 and all downstream product/package gates stay open.
