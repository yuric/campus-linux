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
