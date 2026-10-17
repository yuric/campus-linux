# Disposable D1 Electron fallback probe

Human coordinator10413 authorizes correction of the harness's absolute-zoom initialization;
producer/protocol/thresholds remain unchanged. The commands below are reproduction
instructions. The sole VM owner must verify reserve, corrected untimed motion proof and
a valid measured WebKit baseline miss plus permitted optimization before fallback timing.
This is the decided fallback **mechanism candidate**, not a new product implementation,
renderer fork, security acceptance or final-package parity. Keep the same G8 inputs,
thresholds and normal-motion software-rendering requirement. No network or account action
is implemented. The worker controlling the real GDM guest must run these commands there.

Official Linux arm64 Electron 44.8.0 archive is pinned in `source.json`; the worker already
verified the host download at `/tmp/campus-982-electron-v44.8.0-linux-arm64.zip` against
vendor HTTPS SHASUMS256. That temporary archive and its extracted directory were later
removed as regenerable worker-owned data to protect the host 35 GiB free-space reserve.
They are **not present**; retained source URLs/digests permit a future explicitly authorized
reproduction. No download or guest launch was performed during this harness correction.
Combined archive and extraction was 426,442,476 bytes (<500 MB).
The archive preserves Electron/Chromium licenses. This digest is vendor-download integrity,
not independent release-key verification or Campus updater trust evidence.

Once the coordinator schedules this candidate and the host reserve remains at least
35 GiB **after** the bounded 426 MB allocation, the official archive can be reproduced with
this size-limited command. `prepare.py` verifies the recorded SHA-256 before extraction;
no checksum or sandbox downgrade is permitted.

The example export below is the verified merged desktop export from MacPR114
`3e3d4bcd64fd1504c4546b2f7a063b55e2eea783`, manifest
`7b5fabefd830d3cd3d3577da1c4cb4ba55217de0f7eb5b5bbfc9501443428f09`.
Verify it externally as in the [G8 plan](../../../../docs/acceptance/mechanisms/g8-run-plan.md)
and preserve its modes. Direction1240 authorizes no Electron launch or allocation.

```sh
curl -fL --max-time 180 --max-filesize 124393671 \
  --output /path/to/electron-v44.8.0-linux-arm64.zip \
  https://github.com/electron/electron/releases/download/v44.8.0/electron-v44.8.0-linux-arm64.zip
python3 spikes/982/renderer/electron/prepare.py /path/to/electron-v44.8.0-linux-arm64.zip /path/to/new-disposable-electron
LIBGL_ALWAYS_SOFTWARE=1 /path/to/new-disposable-electron/electron spikes/982/renderer/electron/main.cjs --preflight /path/to/verified-desktop-export ignored /path/to/electron-preflight.json
python3 spikes/982/renderer/electron/freeze.py /path/to/electron-preflight.json /path/to/observed-environment.json /path/to/electron-freeze.json
LIBGL_ALWAYS_SOFTWARE=1 /path/to/new-disposable-electron/electron spikes/982/renderer/electron/main.cjs --motion-proof /path/to/verified-desktop-export /path/to/electron-freeze.json /path/to/electron-motion.json
python3 spikes/982/renderer/electron/freeze.py --motion-proof /path/to/electron-motion.json /path/to/electron-preflight.json /path/to/observed-environment.json /path/to/electron-timing-freeze.json
python3 spikes/982/renderer/electron/run-five.py /path/to/new-disposable-electron/electron /path/to/verified-desktop-export /path/to/electron-timing-freeze.json /path/to/new-five-runs
```

The environment file records actual kernel/architecture/OS/session/Mesa/LLVM/graphics,
from the same real session. Preflight must succeed before freezing; freeze refuses changed
bytes. The host also verifies actual Electron version, executable digest, unchanged producer
manifest/assets, fixture and driver hashes, viewport, unique mounted fixture counts,
WebGL-reported llvmpipe, native complete GPU information and own-descendant llvmpipe threads.
Both clock resets first verify settled absolute zoom1 with a temporary draw observer,
then restore the original methods. The normal timed mode has no draw/matrix diagnostics.
The first freeze is diagnostic-only; the second must bind a successful corrected motion
proof before timing is admitted. The optional
`--lifecycle-proof` flag is separate and untimed, like WebKit. Keep every failure capture.

The renderer is sandboxed with context isolation and no Node, receives only the fixed
presentation response, and can send bounded probe receipts. No general IPC channel or host
mutation bridge is exposed. It loads only manifest-listed resources in an ephemeral custom
session. Browser requests outside the custom origin are cancelled, permissions denied and
an inert loopback proxy is configured. GPU access uses `use-gl=angle`, `use-angle=gl` over
`LIBGL_ALWAYS_SOFTWARE=1`; actual Mesa llvmpipe must be observed. SwiftShader is not accepted
as a substitute for the frozen Mesa protocol. `disableHardwareAcceleration()` is deliberately
not used because it could remove WebGL or substitute a different software implementation.
No production security claim follows from this bounded harness.

A sandbox startup refusal is a blocked test. Do not add `--no-sandbox` or disable the GPU
sandbox. The guest owner can resolve an ordinary disposable distribution sandbox prerequisite
under existing guest setup authorization; preserve that setup command and error. No host
installation is modified. `app.getGPUInfo('complete')` and Chromium DevTools injection are
only diagnostic APIs, with no remote debugging port opened. Official API references:
[GPU information](https://www.electronjs.org/docs/latest/api/app#appgetgpuinfoinfotype),
[Debugger](https://www.electronjs.org/docs/latest/api/debugger),
[custom protocols](https://www.electronjs.org/docs/latest/api/protocol).

Status at preparation: archive/size/digest and local syntax verified; no Linux Electron
launch, native driver, sandbox, frame result or fallback success observed yet. Earlier v2
relative-zoom captures were invalid harness evidence: the unchanged producer supports all
absolute0.75/1/1.5 targets. The shared v3 driver corrects its initial condition and requires
actual settled main projections. Do not claim the corrected guest path passes until those
receipts exist. No protocol reinterpretation is authorized or needed.


## Startup deadline repair after the 0240 preflight timeout

The normal GDM Wayland attempt on 2026-10-17 started preflight at02:55:00 UTC and
hit the unchanged125-second outer wrapper timeout at02:57:05. It returned-9;
The absent `preflight.json` and empty stdout/stderr are retained operator
observations, not measurements recorded in the two published receipts below. The preserved
[command receipt](../../../../docs/acceptance/mechanisms/receipts/g8-preflight-0240/preflight-command.json)
and [launch receipt](../../../../docs/acceptance/mechanisms/receipts/g8-preflight-0240/preflight-launch.json)
bind the argv path, current boot and actual session observation, not the main.cjs
source digest. Raw
`sd_pid_get_session={returncode:-61,session:null}` remains qualified; it is not an
exact logind session claim. No nativeGPU, environment publication, motion proof or
performance timing passed in that attempt. No bare retry was made.

That attempt used main.cjs SHA256
`70cd2f44e6dcf8f91c30a438ac829e2b26fa0fc32ad2e99a83eeb6fd8cd10d84`.
That digest comes from the retained operator receipt
`environment/g8-retry1835-0240/accepted-source-export.json` in the coordinator
evidence directory, not either published raw receipt linked above.
The exact stalled operation remains unknown. Source review demonstrated that the
internal timeout began only after awaited startup/loadURL, and terminal receipt
writing could itself wait forever for GPU enrichment. These are repairable source
defects, not proof of which operation stalled in the guest.

The successor arms the existing115-second normal/180-second diagnostic deadline
before asynchronous startup. The full fixed30-second warmup and60-second measurement
must fit within that115-second total together with startup; a slow startup fails
rather than shortening either measurement period. A proposed10-second nativeGPU
query bound applies in all modes, including diagnostic; it is a new bound, not a
threshold or sandbox relaxation. Terminal writing never
awaits GPU: unknown stays null and fails the existing native evidence gates.
For failures before GPU evidence exists, that fail-closed gate rewrites `kind` to
`preflight_failure`; the original error text and phase diagnostics remain available.
Timestamped fixed phase records go synchronously to stderr, and failures record the
last phase. Successful receipt schema and native llvmpipe plus own-descendant-thread
requirements are unchanged. Late startup completion cannot resume after termination.
A blocked JavaScript event loop or synchronous native/file operation still requires
the unchanged outer wrapper deadline; missing output is never a passing result.

Portable offline regression command, using Node's built-in test runner only:

```sh
node --check spikes/982/renderer/electron/main.cjs
node --test spikes/982/renderer/electron/test-deadline.cjs
```

The tests mock Electron, filesystem, processes and timers. They inject stalled and
rejected readiness/proxy/debugger/load/GPU calls, check one nonzero terminal receipt,
unknownGPU handling, late completion, successful schema, and native evidence failures.
They do not launch Electron or prove guest performance. The bootstrap policy image
has no Node runtime, so its existing policy checks do not run this supplemental suite;
record this exact standalone command alongside source review before admission.

The current artifact index binds the successor source and tests; historical receipt
hashes remain unchanged. Any future guest must use a newly reviewed exact source map
and fresh preflight. Source acceptance is not runtime permission or G8 completion.


## Empty-target bootstrap after the debugger-enable stall

The next single preflight on 2026-10-17 returned1 after about115 seconds, with an
internal failure receipt rather than another outer kill. The preserved
[phase stderr](../../../../docs/acceptance/mechanisms/receipts/g8-preflight-deadline-r1/raw-preflight.stderr)
ends startup at `debugger-enable`; the
[native receipt](../../../../docs/acceptance/mechanisms/receipts/g8-preflight-deadline-r1/raw-preflight.json)
binds main.cjs `7725df63d064728c3dffd131e52af8e87f76ac40983a6ea4574d4b59744b4d62`,
records that last phase, null nativeGPU and no loaded resources. The
[command receipt](../../../../docs/acceptance/mechanisms/receipts/g8-preflight-deadline-r1/raw-preflight-command.json)
records start04:09:15.684624 UTC, finish04:11:11.055494 and return1. Its null
`sd_pid_get_session` remains a null observation. This is failed preflight evidence,
not native GPU, motion, timing, or G8 acceptance. Missing GPU data does not establish
a GPU cause: that query was never reached.

[Electron documents](https://www.electronjs.org/docs/latest/api/debugger#debuggersendcommandmethod-commandparams-sessionid)
that a debugger command issued before navigation may remain unresolved until a
navigation occurs. Awaiting Page.enable before the only loadURL creates that wait
cycle. The successor first awaits a fixed empty `about:blank` navigation and checks
its URL, then attaches/enables the debugger and registers the unchanged new-document
instrumentation before the producer's first navigation. The benchmark load callback
is installed only after the blank navigation completes. The blank page neither starts
measurement nor supplies accepted renderer evidence; IPC still requires the exact
producer frame. Network restrictions and sandbox settings are unchanged. A rejected
blank navigation fails closed without an alternate URL or broader allowlist.

The same115/180-second overall deadlines include bootstrap; the full30-second warmup,
60-second measurement, 10-second GPU bound and all native evidence gates remain.
Portable tests model commands waiting for navigation, reproduce the original stall,
verify bootstrap/registration/producer ordering, and cover pending, rejected, late
and unexpected-URL bootstrap outcomes. Existing19 regression cases remain. These
mocks do not establish that the pinned Linux runtime now passes; a new reviewed
source map and separately admitted preflight are still required.

### GPU startup diagnostics after the bootstrap repair

The one normal Wayland preflight of published `a9d7c50b` reached bootstrap,
CDP enablement, producer navigation and the native GPU query. Its
[receipt](../../../../docs/acceptance/mechanisms/receipts/g8-preflight-bootstrap-r1/raw-preflight.json),
[stderr](../../../../docs/acceptance/mechanisms/receipts/g8-preflight-bootstrap-r1/raw-preflight.stderr)
and [command result](../../../../docs/acceptance/mechanisms/receipts/g8-preflight-bootstrap-r1/raw-preflight-command.json)
are verbatim failed evidence. WebGL was blocklisted and the native query rejected
GPU access due to frequent crashes. The first GPU crash cause is not present in
those logs. No renderer acceptance or performance result follows from this failure.

The proposed `--gpu-diagnostic` preflight records at most16 GPU-only
`child-process-gone` events with fixed UTC/type/reason/exitCode fields, followed by
one overflow marker. It adds error-level Chromium stderr logging; ordinary
preflight, motion and timing do not enable that logging. The
[Electron event contract](https://www.electronjs.org/docs/latest/api/app#event-child-process-gone)
provides crash, OOM and launch-failure distinctions;
[logging switches](https://www.electronjs.org/docs/latest/api/command-line-switches#--enable-loggingfile)
provide diagnostics without changing rendering or sandbox policy.

This option must run through the reviewed diagnostic wrapper using
`bounded_stderr.py`: its stderr file contains at most256KiB including one truncation
marker, excess bytes are drained, and inherited pipes cannot extend the existing
125-second outer deadline. The helper retains process ownership until reap and
never signals a known reaped leader. Signal failures still allow a bounded reap
attempt; the command receipt retains the original failure and cleanup errors.
Timeout, overflow or unknown reap fails the wrapper even if the leader exited0.
Its launch callback and stdout policy come
from the wrapper. The proposed wrapper remains outside this repository pending
separate source-map and runtime admission; direct invocation without a bounded
stderr sink is not the admitted diagnostic procedure.

Diagnostic receipts carry `diagnostic_only: gpu-startup`, and `freeze.py` rejects
them even if native checks succeed. Ordinary success schema, rendering flags,
sandbox, native llvmpipe evidence,115/180-second inner deadlines,10-second GPU
query,30-second warmup and60-second measurement are unchanged. This patch has
only offline verification; it does not establish a GPU root cause or a runtime pass.

Offline commands:

```sh
node --test spikes/982/renderer/electron/test-deadline.cjs
python3 -B -m unittest discover -s spikes/982/renderer/electron -p 'test_bounded_stderr.py'
```
