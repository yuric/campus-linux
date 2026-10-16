# #982 renderer, task-link and speech mechanism evidence

This is pre-product evidence for **LINUX-20261016**, not release acceptance. LINUX-16/17
must repeat applicable tests on final deb/AppImage packages in both real GDM sessions.
The bounded real-session observations below do not establish release acceptance.
**G8 remains unaccepted. Corrected untimed X11 v7 and Wayland v7 proofs passed; valid timing series remain held.**
Human coordinator decision **10413**, independently verified by root, supersedes the earlier
10405 investigation: the defect was the harness's initial zoom units, not a producer clamp
or incompatible protocol. Absolute zoom 0.75, 1 and 1.5 are all reachable. The authorized
correction preserves producer bytes, scene, protocol and every threshold. The sole VM owner
must still satisfy the 35 GiB host reserve and human 10420 scheduling hold before further timings.
The latest reported host reserve is 32.7 GiB; the VM owner is stopping Lima normally.

## Producer and premeasurement freeze

Current merged Mac main was read through `gh api repos/yuric/campus-macos/commits/main
--jq .sha` on 2026-10-16: `8e39806c5b1fb2ffeda6e55718a4fd2a4d2890da`.
An isolated `gh repo clone yuric/campus-macos /tmp/campus-982-renderer-git -- --depth 1`
checkout returned the identical HEAD. No reference checkout was modified. Individual
source receipts are in [source-receipt.json](../../../spikes/982/renderer/source-receipt.json).
The Mac contract provenance is `yuric/campus-server@d93b841762183af5ba0d357f3f1c42351aeed9ff`;
this does not replace #985's contract import or #987's desktop producer obligation.

From that clean checkout:

```sh
cd /tmp/campus-982-renderer-git/island
npm run export:ios -- --output /private/tmp/campus-982-renderer-export
npm run verify:ios-export -- --input /private/tmp/campus-982-renderer-export --source 8e39806c5b1fb2ffeda6e55718a4fd2a4d2890da
```

Observed export: success, `iOS Island export verified: 8e39806c5b1fb2ffeda6e55718a4fd2a4d2890da`.
The first export attempt using `/tmp/…` refused its noncanonical parent; using the actual
`/private/tmp/…` parent succeeded. Initial direct SSH clone failed public-key authentication;
`gh repo clone` succeeded using configured GitHub authentication. Neither failure changed
producer source or lowered export checks.

The **provisional** `campus-island-ios-v9` recipe builds the same Island entry as Mac. It is
usable here only for D1 rendering measurement with a synthetic presentation response and
no mutation channel. It is not a desktop export/bridge parity receipt. The generated
[manifest](../../../spikes/982/renderer/producer-manifest.json) is SHA-256
`badcfcde2012ab1aef610f7a955c231b230580730d4d66ccdc6d4c187d6ef120`.
It records Git/Node/npm/Vite, source archive, contract and lockfile hashes and every artifact
byte and runtime license. The 1.1 MiB export includes repository Apache-2.0 LICENSE/NOTICE
and package license inventory; it contains no imported Apple fonts/icons. Its bytes remain
outside the Linux source tree; rebuild using the recorded producer recipe and verify the
manifest digest before transfer. Producer source is never forked into this repository.

[fixture.json](../../../spikes/982/renderer/fixture.json) contains exactly 12 projects,
48 agents and 180 tasks, with synthetic labels, no accounts or secrets. SHA-256:
`16dc931ccaa50a62d350beba44bc64a5a858ed655eb47637f5fda7fedf97d074`.
All 180 tasks are in the synthetic shoreline collection; all 48 agents are synthetic
outdoors characters. Wire identifiers are fixture data copied from the pinned producer
shape, never a Linux product catalog. Seed `98120261016` also initializes the harness's
32-bit Mulberry32 random stream before producer bootstrap. This is the sole primary scene.

The real native [X11 GPU receipt](receipts/webkit-gpu-x11.json), SHA-256
`ddf24313a533aef11ebad7a939cf98fb0057742d2cc842ea529f7ec2269711c0`, reports render-process
`llvmpipe (LLVM 20.1.2, 128 bits)`, vendor Mesa and OpenGL ES 3.2 / Mesa 25.2.8.
This resolves a misleading JavaScript value: exact upstream WebKitGTK 2.52.6
[source](https://github.com/WebKit/WebKit/blob/4fb33923db2f945803df49546f75867980365c08/Source/WebCore/html/canvas/WebGLRenderingContextBase.cpp#L2121)
unconditionally returns `Apple GPU` and `Apple Inc.` for the debug renderer/vendor API.
There is no Linux/ARM platform guard. No harness code replaces these strings.
The native [protocol handler](https://github.com/WebKit/WebKit/blob/4fb33923db2f945803df49546f75867980365c08/Source/WebKit/UIProcess/API/glib/WebKitProtocolHandler.cpp#L105)
obtains actual render-process information; source/tag/file-hash provenance is in
[webkit-source-receipt.json](../../../spikes/982/renderer/webkit-source-receipt.json).

The corrected gate keeps both identities separate. It requires exact reviewed WebKit
runtime, matching native diagnostic/backend (X11 cannot stand in for Wayland), its frozen
SHA-256, software-rendering environment, and live **candidate-descendant WebKit process**
llvmpipe threads before timing and again at capture. It records graphics-only process maps
where readable. An unrelated `glxinfo` result alone cannot pass. Correcting a hardcoded API
observation does not alter the software-rendering requirement, scene or numeric threshold.
The native diagnostic itself is untimed and is not a rendering performance pass.

The fixed numeric criteria remain [visual-protocol.json](../visual-protocol.json): five
separate 60-second runs, each p95 ≤33.3 ms after 30-second warmup, 1440×900 CSS viewport,
scale 1, normal motion, light appearance, 4 CPU/6 GiB/28 GiB Lima Ubuntu 24.04 arm64 and
actual Mesa llvmpipe. Never pool runs, drop stalls or change the scene/scale to pass.

The VM owner must collect exact WebKit/Mesa/LLVM/kernel package versions, actual GL renderer,
architecture, OS and real graphical session before creating an environment JSON with
`webkit`, `mesa`, `llvm`, `kernel`, `architecture`, `os`, `session`, `graphics` strings.
First capture native WebKit GPU diagnostics with `LIBGL_ALWAYS_SOFTWARE=1 python3
spikes/982/renderer/capture-gpu.py > /path/to/gpu.json`. Run the untimed preflight with
that receipt and copy its JavaScript API renderer string into `webgl_api_renderer`;
set `compositing_policy` to `on-demand` for baseline and copy
the complete observed `rendering_env` object. The receipt records both requested and
effective hardware-acceleration policy; an alias/no-op is not an optimization result.
Then, before any candidate measurement:

```sh
LIBGL_ALWAYS_SOFTWARE=1 python3 spikes/982/renderer/run-webkit.py --preflight --native-gpu-receipt /path/to/gpu.json /path/to/export ignored /path/to/preflight.json
python3 spikes/982/renderer/freeze.py --native-gpu-receipt /path/to/gpu.json /path/to/observed-environment.json /path/to/diagnostic-freeze-v3.json
LIBGL_ALWAYS_SOFTWARE=1 python3 spikes/982/renderer/run-webkit.py --motion-proof --native-gpu-receipt /path/to/gpu.json /path/to/export /path/to/diagnostic-freeze-v3.json /path/to/absolute-motion-v3.json
python3 spikes/982/renderer/freeze.py --motion-proof /path/to/absolute-motion-v3.json --native-gpu-receipt /path/to/gpu.json /path/to/observed-environment.json /path/to/frozen.json
python3 spikes/982/renderer/run-five.py --native-gpu-receipt /path/to/gpu.json /path/to/export /path/to/frozen.json /path/to/five-runs
```

Run in the actual GDM user's graphical environment, not an SSH-created compositor. The
host needs Ubuntu `python3-gi` and `gir1.2-webkit2-4.1`. It checks frozen hashes, producer
artifact bytes, actual WebGL llvmpipe, focus, visible canvas, viewport/scale and mounted
lifecycle acknowledgement before timing. The preflight records JavaScript WebGL API vendor/version/renderer
and runtime WebKit; measured runs require that same API identity plus native driver evidence. The unchanged
producer CSP denies connections, remote resources, media, frames and workers. The host
serves only manifest-listed bytes from memory under a custom origin, denies other navigation
and permission requests, and configures an inert loopback proxy as an additional transport
barrier. Custom responses include explicit MIME and CORS headers for the public pinned
module resources. This is bounded probe confinement, not a product security acceptance result. Preserve the freeze digest externally and all
raw outputs. A crash/preflight/timeout receipt has no frame pass. Local Python compilation
and JavaScript syntax checks passed; the v1 successful preflight proved mounting/native driver only, not performance.

`measure.js` v3 drives the six segments from monotonic elapsed time on a 16 ms timer,
independent of animation frame count. It retains requested input poses, actual timer
stamps, every consecutive rAF timestamp, errors, focus/visibility invalidations and lifecycle
messages. One continuous primary drag covers the initial pan segments. Pointer cancellation
ends a gesture without the producer's click/picking action. Wheel events are sent with the
pinned OrbitControls in its idle state; the simultaneous final pan/zoom segment cancels and
reopens the drag around each wheel event. The only pointer-capture bypass is synthetic ID
982. The warmup exercises all six segments in 30 seconds; an acknowledged public lifecycle
and overview focus reset clears pending damping and resets center. Since the producer's
focused overview is about 0.46665 absolute zoom, each reset then sends a production wheel
event to initialize **absolute zoom 1** and waits for its newly rendered, settled main
projection before starting the warmup or measurement clock. Decorative camera yaw remains the producer's normal behavior.
Every repetition launches a fresh host. Both boundary-crossing frame timestamps and long
stalls remain in the raw samples. Nearest-rank p95 must pass individually on all five runs.

The original `c575c71` freeze is **rejected, unmeasured protocol evidence**: review found
that its per-tick pointerdown/move/up could trigger clicks and its first post-warmup rAF
created an input/timing offset. No benchmark was performed against it. The v2 correction fixed those issues but retained a separate zoom-initialization bug.
Both old freezes and their invalid captures remain preserved; v3 requires fresh proof/freeze.

Untimed `--motion-proof` runs the same input sequence with GL draw and camera matrix
instrumentation, emits checkpoints for screenshots, and records no frame-performance
samples. `--lifecycle-proof` loads the separate `lifecycle.js` diagnostic to record actual
normal/reduced-motion/hidden/resumed acknowledgements and draw deltas. These wrappers are
not installed in performance mode. A mounted React scene snapshot must contain all 12
projects, 48 unique agents and 180 unique tasks before a run starts; this checks applied
component data, not merely the supplied HTTP body. It is not an independent object-count
readback of every GPU primitive. The producer's shoreline cap is 2400, above this fixture.
These input commands are **not proof that the camera exactly followed them**: producer
bounds/damping still apply. Inspect real motion checkpoint matrices and screenshots before
accepting timings. Lifecycle draw evidence does not prove reload persistence or complete
animation/visual parity. A preflight failure, invalid focus or failed lifecycle check stays
a failure; no current frame result qualifies.

The retained [v2 motion diagnostic](receipts/motion-proof-x11.json) is **invalid for G8**.
It completed 30,103 ms warmup and 60,141 ms of sequence with seven checkpoints, 1,392
gestures, no pointer-up clicks and no errors/foreground invalidations. Those facts prove
only what that incorrect harness did. The source-correct public `focus(null)` sets zoom
about 0.46665; the harness then incorrectly declared its previous zoom to be 1. Relative
wheel ratios therefore drove overview × 0.75 into the actual floor. The initial
[zoom-clamp analysis](receipts/zoom-clamp-analysis.json) and old screenshot are preserved
unchanged as superseded interpretation, **not evidence of a producer defect**.
[The 10413 correction receipt](receipts/absolute-zoom-correction.json) records this
adjudication and binds the replacement harness hashes. Aborted v2 timings cannot count.

The old numerical observations remain valid in their actual units: source radius 81.9,
internal overview zoom 0.43239197668642054, minimum 0.4064484580852353 and public focused
overview 0.4666505165009651. Actual uploaded `P11` coefficients at 10.01 s / 50.038 s imply
zoom 0.46665051579475403 / 0.406448470428586 (`P11 × 46`), not 1 / 0.75. Comparing their
ratio to protocol 0.75 was the interpretation error. The maximum is 11, so all protocol
**absolute** targets are inside the unchanged producer's bounds. Direct runtime camera
properties were not captured; the numeric camera values are matrix-based inferences.

The v3 correction sends `deltaY = ln(target/current) / (0.015 × ln(0.95))` with pixel mode,
`ctrlKey=false` and no active drag. Overview-to-1 is approximately −990.6098763. A temporary
GL draw observer reads the actual active program's projection after a draw, selecting main
camera depth terms `m10=-0.001818181830458343`, `m14=-0.6363636255264282`; this excludes
shadow cameras and handles Three's cached unchanged uniforms. It waits for three fresh
observations within `1e-5` of absolute zoom 1 (`m5=1/46`), then restores all four original
GL draw methods **before either clock**. The tolerance accounts for Float32 projection
readback; it changes no timing or visual threshold. A failed/timed-out reset fails closed.
The reset interval between the 30-second warmup and 60-second measurement is recorded
separately; the ordinary frame collector retains the boundary-crossing rAF interval.

The untimed v3 proof additionally settles absolute 1.5 → 0.75 → 1 through the same wheel
path before executing the unchanged six-segment diagnostic trace. Timed runs omit these
extra diagnostic steps and the draw/matrix instrumentation. `freeze.py` without
`--motion-proof` now creates an **untimed-only** freeze. A timing freeze must bind a valid
v3 motion proof's digest, matching driver/runner/native/fixture/protocol inputs and both
successful absolute-1 resets. Runners refuse timing against an untimed-only freeze.
Local control-flow simulation passed both modes, including hook restoration and correct
absolute targets; it is not guest evidence. The first real corrected attempts failed before
any wheel was sent: [attempt1](receipts/motion-proof-x11-v3-attempt1.json) had no captured
main projection, and [the bounded diagnostic](receipts/motion-proof-x11-v4.json) recorded
zero observer draws. Source `index.tsx:2470` explains the additional harness defect:
`webglAvailable()` creates and deliberately loses a feature-test context before the real
renderer creates its context. The global observer had latched that first context. The
correction explicitly switches context ownership, restores the feature-test hooks and
attaches to the actual renderer; receipts now carry context IDs and a context-match flag.
A local two-context simulation verifies both original method sets are restored. No
wheel-capping, tolerance or producer workaround was introduced. This corrected observer
has now passed the actual Wayland proof below. Both GTK and Electron runners now return nonzero on failed
probe kinds/errors/foreground/lifecycle checks; a valid slow measurement remains a
measurement whose separate numeric gate fails.

The corrected [Wayland v5 untimed motion receipt](receipts/motion-proof-wayland-v5.json)
(SHA-256 `847b4b7cfbb17ec51f4934b1ac24da2c70cefa2a022979fb08042bb82b2bcdc8`)
passes the current motion checker with no errors or foreground invalidations. Both resets
settled at absolute zoom `1.0000000186264515`; the separate 1.5 → 0.75 → 1 checks settled at
`1.4999999850988388`, `0.7499999925494194`, and `1.0000000186264515`. All are within the
fixed `1e-5` Float32 tolerance. The observer was restored before both clocks. The receipt
retains 1,382 input rows, 1,373 gesture rows and seven motion checkpoints across 30,116 ms
warmup and 60,021 ms diagnostic duration, with a separate 3,630 ms reset interval.
It contains **zero frame-performance samples** and supplies no p95 or G8 timing credit.
Checkpoint projection uniforms can retain stale values from inactive shader programs;
they are diagnostic history, not exact instantaneous camera readback. The fresh active
program readback in each settled zoom check is the evidence for the absolute targets.

Source self-review found and corrected two admission gaps: the motion checker formerly
accepted a receipt stripped of input/gesture/checkpoint traces, and the WebKit freezer
omitted the proof's compositing-policy comparison. The stronger checker now validates
both complete six-segment traces, continuous pan/cancel gestures, seven ordered draw/matrix
checkpoints and the absence of performance samples. The retained v5 receipt passes;
mutated missing/wrong/incomplete traces and a changed-policy candidate fail host checks.
The measured JavaScript and GTK runner bytes are unchanged. The final v7 session freezes/proofs below bind
the revised checker hash; timing still needs its separate freeze and authorized run window.
Old raw receipts are not rewritten. See
[renderer-links-speech-review.md](renderer-links-speech-review.md) for the review and limits.

The next [X11 v6 diagnostic](receipts/motion-proof-x11-v6.json), SHA-256
`c612454102db15b30ec0eb3d6341c1fc1fe594eff09399aa74490764cf9b0242`, reached the host's
115-second wall timeout and remains a failure. The operator's log places the diagnostic
measurement clock at about 55,131 ms of page time: the additional untimed settled-target
checks plus warmup/reset left too little of that overall host budget for the full
60-second trace. This is a diagnostic wall-budget failure, not a measured G8 miss.
GTK and Electron now allow **180 seconds overall only for motion/lifecycle diagnostics**.
Ordinary preflight/performance hosts retain 115 seconds, and the GTK five-run wrapper
retains its 125-second subprocess timeout. The measured JavaScript, 30-second warmup,
60-second measurement and p95 ≤33.3 ms threshold are unchanged. New session proofs must
use fresh freezes recording the revised runner hashes; the failed receipt is preserved.

The final [X11 v7 motion proof](receipts/motion-proof-x11-v7.json), SHA-256
`905c56f786fab5346e2b7bb1e41a735cfb049baebd53d030f321331397b3ff03`, passes the stronger
checker with the revised 180-second diagnostic host. It binds runner
`19111e1b9b374c159333d7174a0986b6761a9cb72fdf60ef3085b89b39ec674d` and checker
`ec3a984d6bb3edbaddff1a3e0ea26fba492e0c8cdd33201aec6e5d00282d9901`, contains 1,292 input
rows and all seven checkpoints, and has no errors/invalidations. Warmup is 30,029 ms and
diagnostic duration is 60,075 ms. Both resets settle at `1.0000000186264515`; diagnostic
1.5/0.75/1 settle at `1.4999999850988388`, `0.7499999925494194`, and
`1.0000000186264515`. This closes the X11 absolute-zoom/trace harness proof, not G8 timing.
The final [Wayland v7 motion proof](receipts/motion-proof-wayland-v7.json), SHA-256
`62288eb7f53450666ae1bf975f441b82812367bac52421b3d60ab9b99f9e2e5d`, also passes the
stronger checker and binds those same final runner/checker hashes. It contains 1,293 inputs
and seven checkpoints, with no errors/invalidations, a 30,098 ms warmup and 60,120 ms
untimed diagnostic duration. Both resets and all three absolute targets settle at the
same Float32 values reported for X11 above. Both session proofs contain zero performance
frames; neither is a G8 timing pass. The final corrected untimed input/reset proof is now
observed in both real graphical sessions.

Exact producer review locations:
[scene.ts:445](https://github.com/yuric/campus-macos/blob/8e39806c5b1fb2ffeda6e55718a4fd2a4d2890da/island/src/world3d/scene.ts#L445)
for overview/floor, `scene.ts:1075` for radius framing, `scene.ts:68` for half-height;
[index.tsx:144](https://github.com/yuric/campus-macos/blob/8e39806c5b1fb2ffeda6e55718a4fd2a4d2890da/island/src/world3d/index.tsx#L144)
and `index.tsx:1201` for null focus;
[contract.ts:493](https://github.com/yuric/campus-macos/blob/8e39806c5b1fb2ffeda6e55718a4fd2a4d2890da/island/src/world3d/contract.ts#L493)
and `contract.ts:538` for fixture radius, `contract.ts:207` for outer radius.
Local preflight functions are `inspect`, `spikePreflight` and asynchronous `spikeStart`
in `spikes/982/renderer/measure.js`, dispatched by `start()` in
`spikes/982/renderer/run-webkit.py`; retained historical receipts are
`renderer-preflight5-x11.json`, `motion-proof-x11.json` and `renderer-freeze-x11-v2.json`.

The real [lifecycle diagnostic](receipts/lifecycle-proof-x11-final.json) reports all six
checks true and zero errors: normal/reduced/hidden/resumed/restored states acknowledge
`applied`; their measured draw deltas are respectively 1494/1411/0/1494/1494 over 2.5-second
observation intervals. This proves hidden draw pause and visible draw resume in the
candidate. Reduced-motion acknowledgement alone does not prove every decorative animation
is motionless; reload persistence and elapsed-animation replay remain unproven. The earlier
[lifecycle attempt](receipts/lifecycle-proof-x11.json) failed because the GTK JS API could
not marshal a Promise result; invocation now explicitly returns void, without changing the
performance path. Earlier motion failures retain null-fixture introspection and real
screen-lock/foreground failures; neither is a pass.

The real [second preflight](receipts/renderer-preflight2.json) reports requested `on-demand`
but effective `ALWAYS`; selecting `always` therefore cannot be presented as a meaningful
optimization. After a measured baseline miss, a separately frozen
`WEBKIT_DISABLE_DMABUF_RENDERER=1` experiment is a conditional runtime candidate, not a
production default. WebKit documents this [buffer-path workaround](https://bugs.webkit.org/show_bug.cgi?id=291332)
and also a [2.52.6 rendering bug in one affected configuration](https://bugs.webkit.org/show_bug.cgi?id=324549).
Keep scene, viewport, render scale, normal motion, software renderer and thresholds
unchanged; record the environment flag and inspect output correctness before using any
performance result. No improvement is asserted. `run-five.py` reads the frozen policy,
requires the observed rendering environment and never switches automatically or drops
slow runs.

Early real-session untimed attempts reported an empty page with no canvas/context; the
original receipt lacked identity detail. The instrument now retains context attempts,
masked/unmasked GL fields, extension availability, producer console errors, resource errors
and page/mount state even on failure. An empty page is a harness/resource failure, not a
measured D1 performance miss. The [first](receipts/renderer-preflight.json) and [second](receipts/renderer-preflight2.json)
failed attempts are retained. A subsequent attempt loaded the module and exposed the
missing synthetic host bridge; the harness now registers the native promise-reply
`campusIslandAPI` channel instead of assigning a temporary JavaScript message-handler
property. That channel returns only the fixed fixture for the exact presentation request.

The separate [Electron fallback harness](../../../spikes/982/renderer/electron/README.md)
pins official Linux arm64 Electron 44.8.0 and the same fixture/driver. Its verified archive
plus extraction is 426,442,476 bytes, below the 500 MB spike bound. Local preparation and
syntax pass; no guest launch or fallback result is asserted. The temporary archive and
extraction were removed during reserve cleanup; they are no longer available at the
reported temporary paths. URLs, versions and digests remain recorded, with no download
or execution performed during this correction. Reproduction remains subject to the
coordinator schedule, reserve and valid-baseline/optimization prerequisites. It preserves the sandbox and
requires actual Mesa llvmpipe; SwiftShader is not silently substituted. See its source
receipt for vendor-download integrity limits.

Outstanding: timing refreeze, valid baseline runs, complete reduced-motion/reload capture, 1×/1.25×/2×
light/dark paired images, renderer-vs-WebKit-process failure recovery, actual package
measurement, permitted-optimization rerun on a miss, then D1's decided Electron fallback
if still missed. A missing result does not select the fallback and does not authorize a
relaxed threshold. #987/#995/#997 need these explicit gaps; unproven D1 blocks production
renderer commitment.

## Task links: observed source and bounded next probe

Pinned Mac `TaskLinkBridge.swift` defines the server-published HTTP grammar
`http://localhost:3979/task-<positive-id>.html?island=<encoded origin>` and a
`campus://task/<id>?island=…` redirect. The separate `campus-task-link` helper binds
127.0.0.1, responds to GET/HEAD and exposes a credential-free health response. Mac rejects
malformed/duplicate island stamps and extra query keys, escapes redirect HTML and uses
an island-aware deep-link parser. This is source evidence, not a Linux behavioral result.
Copy `task_link.href` verbatim; inventing a Linux URL would break existing shared links.

For each disposable package/session, the bounded probe must install a distinct test
`.desktop` entry with `MimeType=x-scheme-handler/campus;` and a fixed executable plus `%u`,
then record `xdg-mime query default x-scheme-handler/campus`, cold activation and a second
activation into the existing window. Preserve the prior association and restore it during
cleanup. Use direct argv dispatch, never a shell. The freedesktop
[Exec specification](https://specifications.freedesktop.org/desktop-entry/latest/exec-variables.html)
defines URL argument expansion; it is not evidence the packaged handler works.

No second Linux listener is installed or approved by this spike. The HTTP href inventory
shows why a narrow loopback-navigation mechanism may be needed; #994 must prove the chosen
OS adapter, singleton and session lifecycle with #989. It must not expose credentials,
process/filesystem access or domain mutations. Required negative cases: foreign Origin and
Host, nonloopback access, invalid/overflow/Unicode IDs, duplicate/unknown query fields,
userinfo/fragment/encoded-separator islands, body/unsupported method, occupied port, app
missing, wrong signed-in island, cold start and active window. A link must never change
API origin, enrollment trust, or account. Keep HTTP navigation evidence separate from
server-authorized task fetch evidence. The separate [task-link probe](task-links.md) records installed deb/mounted AppImage
X11 activation, same-window dispatch and hostile URI rejection. Its exact package/session
receipts supersede this source-only inventory for that seam. Existing HTTP bridge behavior,
real account authorization and final product behavior remain unproven. The linked probe
now includes Wayland deb/AppImage and the passing X11 graphical-terminal deb repeat; its
original SSH-origin focus failure remains preserved.

## Speech: availability and privacy boundary

Pinned Mac `SpeechRecording.swift` uses `SFSpeechRecognizer` and `AVAudioEngine`, requests
both microphone and speech permission, and exposes partial/final editable text. Its primary
request requires on-device recognition when that recognizer reports support; absence of
that support is not an offline guarantee. On-device recovery explicitly requires device
support. `TaskSpeechRecovery.swift` implements Rails recovery v1: memory-only bounded
PCM16 mono 16 kHz capture, server-provided chunk/byte/duration/retention/call/time limits,
authorization/candidate/destination/cost copy and cancellation. Those are existing Mac
contracts, not authorization to activate a Linux cloud transcription path. The legacy
single WAV upload is not selected as a fallback.

Linux Apple Speech availability: **unavailable as a native Linux implementation**. The
actual GTK Web Speech API constructors were **absent in both tested GDM sessions**:
[speech-wayland.json](receipts/speech-wayland.json) and [speech-x11.json](receipts/speech-x11.json) records `SpeechRecognition` and
`webkitSpeechRecognition` as `undefined`, with `mediaDevices` present, `getUserMedia` a
function and secure context true. This is the disposable GTK host on WebKitGTK 2.52.6,
not installed-product evidence. Reproduce with:

```sh
python3 spikes/982/renderer/probe-speech.py
```

This probe reads `SpeechRecognition`, `webkitSpeechRecognition`, `mediaDevices` and secure
context presence without starting recognition, recording audio or making network requests.
A constructor's presence alone cannot prove a backend, offline capability or cost. Its
host denies any unexpected permission request; an empty permission list is not a tested
denial flow. No recorded speech, account credential or owner microphone data is used.

WebKitGTK offers an explicit
[user-media permission request](https://webkitgtk.org/reference/webkit2gtk/2.41.3/class.UserMediaPermissionRequest.html)
and [permission-request signal](https://www.webkitgtk.org/reference/webkit2gtk/stable/signal.WebView.permission-request.html).
These support host-mediated capture decisions; they do not supply a speech recognizer.
Likewise [PipeWire portal integration](https://flatpak.github.io/xdg-desktop-portal/docs/pipewire.html)
is audio/device transport, not transcription. Do not infer that an unsandboxed deb/AppImage
has Flatpak's microphone permission boundary or a universal portal prompt.

A local recognizer such as [whisper.cpp](https://github.com/ggml-org/whisper.cpp) documents
Linux/CPU support, including ARM targets, and can run downloaded models locally. Human
comment **10361** subsequently authorized a bounded offline public-audio mechanism probe;
the actual execution and both-session synthetic audio access/cancel receipts are in
[speech-offline.md](speech-offline.md). That permission does not
select a Linux product recognizer, authorize cloud processing, new spend, or owner audio.
Keep that bounded result separate from this constructor/capture inventory. No product
model distribution, language/quality envelope, runtime/update ownership or privacy wording
is selected here. A remote recognizer would add data destination, credentials and possible
spend and remains unauthorized. LINUX-20261016 must hand observed limits and unresolved
product/privacy decisions to #1030; this client must not invent capability wording.

Current Linux speech evidence dimensions:

| Dimension | Observation / remaining proof |
|---|---|
| Availability | Native Apple API unavailable; GTK speech constructors absent in both sessions; offline English-only candidate runs, current-locale parity unproven |
| Permission/interruption | Native synthetic audio access and cancel pass in both sessions; product prompts/revoke/device removal/suspend/logout remain untested |
| Privacy/data destination | Constructor probe captures none; separate native probe records only public synthetic audio locally and inference is offline; product disclosure/retention unresolved |
| Cost | No paid speech call authorized/performed; bounded offline download/probe tracked separately; no zero-cost cloud claim |
| Offline | Actual public-fixture inference completed with only loopback in its network namespace; no integrated live speech/editor offline proof |
| Limits | Mac contract carries server bounds; Linux duration/byte/chunk/retention enforcement unimplemented |
| Editable result | Mac source exposes text; Linux end-to-end recognized/editable/non-auto-submitted draft unproven |

#1030 receives these observations through LINUX-20261016, then #1031 imports the merged
contract for #994/#996 (and #991's task authoring). These are forward handoffs; #982 does not
acquire reverse dependencies. New capability/copy must merge server-first. Full speech
acceptance remains blocked until real availability, denial/interruption, limits, privacy,
cost/offline behavior and editable results have observed receipts and any changed
product/privacy/spend/trust trade-off has explicit owner disposition. Human 10427 does not
require separate owner approval merely to evaluate a library as an engineering choice.
