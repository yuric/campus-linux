# Fixed visual and renderer criteria

Recorded on 2026-10-16 before candidate measurements. The executable-data specification is
[visual-protocol.json](visual-protocol.json). **Every one of five 60-second runs must have
p95 frame interval ≤33.3 ms**, with zero renderer crashes, after a 30-second warmup per run.
Use nearest-rank p95 on all consecutive `requestAnimationFrame` timestamps during each
foreground sequence, including stalls; retain raw timestamps and input trace. Do not pool
runs, discard slow runs or subtract stalls. Record frame count, p50/p95/max and missed-frame
count. A run with focus/visibility loss is invalid, retained and repeated with its reason.
This gate measures the actual WebKitGTK renderer, not the input driver's timing.

#982 freezes the synthetic fixture bytes/hash, producer SHA/manifest digest, exact WebKit,
Mesa/LLVM/kernel versions and the time-driven input automation before first measurement.
Seed 98120261016; 12 projects, 48 agents, 180 tasks; 1440×900 CSS viewport, device/render
scale 1; light appearance; 4 vCPU/6 GiB/28 GiB Lima Ubuntu 24.04 arm64. Use software Mesa
llvmpipe, set `LIBGL_ALWAYS_SOFTWARE=1`, and prove the actual renderer string. Environment support observed WebKitGTK 2.52.6-0ubuntu0.24.04.1 and
Mesa 25.2.8-0ubuntu0.24.04.4 in the named guest on 2026-10-16, with GNOME
46.0-0ubuntu6~24.04.16 and systemd 255.4-1ubuntu8.17. LLVM/kernel and the actual
llvmpipe renderer remain unobserved by this worker; revalidate these exact versions
under #982 before measurement. These observations are not a renderer pass. No benchmark may begin with these
receipt fields blank. Warm up the same scene/sequence for 30 seconds. Run the six linear
10-second segments in the JSON using elapsed monotonic time, not a frame-count-dependent
input rate. Fix the seed and initial camera before every repeat; no live account changes.

Normal visible motion is the performance gate. Separately test reduced-motion visible,
hidden/paused and visible/resumed acknowledgement, with raw lifecycle messages and
screenshots. Hidden animation must stop, resume must not replay elapsed animation, and
reduced motion must survive navigation/reload. Repeat visual cases in light/dark at
1×, 1.25× and 2× scale; these are separately labeled, not substituted for the performance
run. If the limit is missed, #982 records permitted optimizations and repeats unchanged
criteria; D1's decided fallback applies after a verified miss. Do not relax the bar.

## Paired capture arrangement

#987 owns reproducible Mac reference capture at the pinned producer and its licensed
asset manifest; #982 arranges disposable seeded data/capture transport; the listed Linux
owner supplies the matched capture; #997 reviews overlays and all remaining gaps.
This is an explicit capture request/handoff, **no screenshots have been captured yet**.
Every row needs Mac and Linux image SHA-256, repo/build/contract/renderer SHAs, fixture
hash, screen/state, viewport/scale, appearance, capture timestamp/method and license
manifest. Mac uses window-content capture (record macOS/build); Linux uses the actual
Lima compositor. Secret-bearing fields are synthetic and excluded from capture.

| Screen/state pair (each state independently captured) | Linux owner | Current receipt |
|---|---:|---|
| Home inbox, waiting, credential grid, briefing/digest, Pulse/recommendation | #988 | Missing both |
| Board empty/populated, filter, pagination, multi-select, confirmation | #991 | Missing both |
| Task detail, editing, comments, dependencies/PR/runs, chat and draft | #991 | Missing both |
| Agents list, landing single/batch, office/transcript and recovery | #992 | Missing both |
| Credentials list/add, login/input/cancel, verification, usage tier/recheck | #992 | Missing both |
| Settings rules/authority/prompts, profile, telemetry, GitHub, feedback | #988 | Missing both |
| Onboarding sign-in/register/recovery, demo/conversion and endpoint | #988 | Missing both |
| Island normal/reduced motion, selected project/agent, hidden/resumed | #995 | Missing both |
| Projects create/edit/import/browse/binding/archive/delete | #991 | Missing both |
| Activity/filter and search palette/results/empty | #994 | Missing both |
| Assistant/coordinator sessions, references/steering, proposals/private interactions | #993 | Missing both |
| Executor setup/readiness/recovery and helper diagnostics | #989 | Missing both |
| Delegated consent principal/scope, grant/refusal/expired | #993 | Missing both |
| Application menus, shortcut focus, tray/status equivalents | #994 | Missing both |
| Reply notification delivered/denied/activated | #994 | Missing both |

## Visual tolerances and assets

App-controlled geometry: maximum 2 CSS px displacement in edges, spacing and baselines at
1×, scaled proportionally. Reusable artwork: at most 1% changed pixels with any RGBA
channel delta >8/255 inside the artwork ROI. Compare matching settled frames; record
motion-phase/time for animated captures. Text must preserve visible content, line count,
focus outline and actionable labels without clipping. Mask only glyph rasterization
interiors and platform chrome, never entire panels. Keep masks and overlay diffs as artifacts.
Native Linux dialogs, decorations, key symbols and notifications are reviewed platform
exceptions with explicit screenshots, not blanket exclusions. Accessibility/readable scaling
wins over pixel matching; each exception has an owner and disposition, not a percentage score.

Font choice: Inter (SIL OFL 1.1), with a pinned font-file hash and license copied by #988
before packaging; use system sans only for native dialogs. Icon choice: Lucide (ISC),
with pinned package/individual asset hashes and attribution by #994. These are chosen
licensed equivalents, not a claim that those bytes already exist here. Font metrics and
individual SF Symbol replacements require per-screen comparison. Never redistribute
SF Pro, SF Symbols or other restricted Apple assets. Campus/Island art is eligible only
when #987's per-file license/provenance manifest allows redistribution; unknown art remains
blocked. #995 verifies every imported byte against that manifest, with no D7 directory exemption.

Sources: [Inter license](https://github.com/rsms/inter/blob/master/LICENSE.txt),
[Lucide license](https://github.com/lucide-icons/lucide/blob/main/LICENSE).

First user's Ubuntu point release, CPU and GPU: **unresolved observation**. Only “Ubuntu”
is recorded. The coordinator host is Apple Silicon/96 GiB, not evidence about that user's
Linux hardware. Do not infer a GPU or widen the support matrix from the host or VM.
