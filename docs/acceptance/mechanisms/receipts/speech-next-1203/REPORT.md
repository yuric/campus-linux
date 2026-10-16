# Bounded speech observations — direction 1203, card 982

LINUX-20261016 authorized this independent speech slice after the four-repair
commit `0e7c6b57aa88340b22ad49e4cdf6966a03f37e25`. All changes are new speech
source/receipt paths. Historical evidence, updater paths and prior commits are unchanged.
Merged Linux base remains `37ef5d622da09cd7ba113dc0d1119e62e7378f84` (PR11/#981).
No API snapshot or renderer producer changed; this experiment consumes neither.

The [final receipt](receipt.json) records two real capture-prefix hypotheses before
Stop, a final inference, and cancellation of active capture/playback/inference.
This is **prefix-batch output, not native streaming**. No quality/latency threshold,
product backend adoption, full L0 pass or installed-package acceptance follows.

## Locale and launch boundary

The [observer](session.json) actually ran from GNOME's Run dialog through
`gnome-terminal`, in authenticated GDM Wayland session 7, UID1000, Class=user,
Remote=no, Active=yes. Only LANG, LC_ALL, LC_MESSAGES and LC_CTYPE were collected.
Inherited LANG and effective LC_MESSAGES/LC_CTYPE were `C.UTF-8`: language is
**unknown**, never English by default. The probe designates effective LC_MESSAGES
as its language input, strips region/encoding when present, and maps C/POSIX to null.
No current-locale recognition quality is claimed. Separate process-local initialization
of `en_US.UTF-8` succeeded; `es_ES.UTF-8` failed `unsupported locale setting`.
No locale file/user setting changed or locale package was installed.

The [supervisor](launch.json) launched inference as a separate unprivileged system
service, copying only the observer's allowlisted locale values. This is a disclosed
variation from the brief's single inherited graphical-runner process: locale discovery
is verified in the graphical observer, **the inference process is not a graphical
session child**. An unprivileged network-namespace attempt failed before this route.
The system service's existing PrivateNetwork mechanism provided only `lo`; its exact
namespace, unit argv, memory.max=536870912 and memory.swap.max=0 were read back.
No controller installation/reconfiguration occurred. The existing audio server remains
outside the bounded runner tree; its preexisting process is not covered by that cgroup.

## Actual text and time

Public CC0 reference sentences, exact eSpeak voices, package/library hashes,
PCM sample counts, linear resampling and WAV hashes are in `fixtures` in the receipt.
The model is multilingual tiny at revision `5359861c739e955e79d9a303bcbc70fb988958b1`:
77,691,713 bytes, SHA256
`be07e048e1e599ad46341c8d2a135645097a538221678b7acdd1b1919c6e1b21`.
It was downloaded once directly into the guest, with no host/model cache, rebuild,
install or second model. Existing whisper-cli SHA256 is
`50712621452d3ab5f0d7b2a2c5dbaad5100c8d9b86538da1e1a192074b3ec2a2`;
its previously pinned source is whisper.cpp `d1be6fde11ac6e0407606b4e42fe72d34add8037`.

| Observation | Input | Wall seconds | Child CPU seconds | Sampled RSS KiB |
|---|---|---:|---:|---:|
| Forced en | 64,074 samples / 4.004625 s | 0.977293 | 1.798517 | 177040 |
| Forced es | 70,915 samples / 4.4321875 s | 1.352919 | 2.491194 | 177156 |
| Prefix 1 | [0,48000), 3 s | 0.942199 | 1.747701 | 176920 |
| Prefix 2 | [0,96000), 6 s | 1.044154 | 1.942810 | 177264 |
| Final | [0,112640), 7.04 s | 1.123797 | 2.090762 | 177436 |

The exact argv uses `-f - -t 2 -ng -l en|es -nt -otxt -of -`, with translation off.
Each complete WAV snapshot goes through stdin followed by EOF, with one inference
child at a time and no obsolete queue. Times include child startup/input and polling;
provisional times are when completed child output was collected, not first-token times.
RUSAGE_CHILDREN is a child-accounting delta; cancellation includes reaped audio children.

English reference: “The blue notebook is beside the window. Please keep these words as a draft.”
Actual [English output](observation-en.stdout):

> If you know book is beside the window, please keep these words never draft.

Spanish reference: “El cuaderno azul está junto a la ventana. Guarda estas palabras como borrador.”
Actual [Spanish output](observation-es.stdout):

> el cuané en la turista junto a la ventana, o a la estaspalá en la scoma o la mód.

These transcription errors are observations, not a quality pass. The capture uses
repeated English public synthetic PCM, independent of unknown current locale.
[Prefix 1](prefix1.stdout) ends “please keep the”; [prefix 2](prefix2.stdout) changes
the beginning to “The new notebook” and extends the text. [Final output](final.stdout):

> The blue notebook is beside the window. Please keep these words and a draft. The blue notebook is beside the window. Please keep these

Capture began at monotonic500.240321111. Prefixes were collected at504.249127616
and507.299730479 while the recorder remained active. Stop was507.299742436;
input was sealed507.300954461, final collected508.425334979. “Complete capture”
here means the bounded PCM delivered to the runner before Stop: pending audio-server
or pipe bytes are not drained after termination. The sample range and PCM hash are
recorded; this is not a product retention/flush guarantee.

The exact dedicated module-null-sink/monitor was verified by module ID, sink name,
null-audio factory and monitor class. PA_STREAM_DONT_MOVE and repeated exact-device
checks prevent recorder fallback. No default or physical microphone was selected.
A second capture fed an inference before cancellation: all three owned children were
observed running at511.698523166, and reaped by511.703175986 (4.644362 ms).
Recorder/inference returned-15, playback0; zero late transcript bytes were discarded.
These actual timings impose no performance bar. All workers were reaped before
unloading the synthetic source, which was verified absent. All six owned cgroups
were absent during [collection](collection.json).

## Resource accounting and failures

The final kernel cgroup memory.peak readback was198,529,024 bytes (189.332 MiB),
swap peak0, with no max/oom/oom_kill event. This is a pre-receipt-write tree peak,
not RSS. systemd-run's summary printed256KiB, inconsistent with the kernel peak;
we retain both and use the direct cgroup readback, not the smaller summary.

Preflight counted163,840 bytes in prior G4 directories plus growth from the recorded
114,270,208-byte /var/log baseline, and conservatively reserved another16MiB for
prior source/host overhead:42,614,784 bytes consumed,225,820,672 bytes remaining
within256MiB. This is operational attribution, not a filesystem quota.
Guest speech directory allocated79,134,720 bytes including the single model and all
four attempts; non-model files allocated1,441,792 bytes. Host receipts/source are
under1MiB. Image allocated growth from corrected pre-download baseline to normal
shutdown was83,689,472 bytes. Image growth includes guest overhead and is not added
again to its contained files. Both the128MiB slice and4MiB fixture/output limits held.
Initial image-name filtering failed; corrected baseline is after normal boot, so boot
image growth is unmeasured. No claim attributes global host free-space changes to this
probe. Host free at shutdown22,763,724,800 bytes; guest free at collection20,303,396,864.
The35GiB large-work guard remains unchanged.

Failures are preserved with exact producing source snapshots:

- [Attempt 1](attempt1/receipt.json): stdin output flag missing, so both inference
  stdout files were empty; blanket RLIMIT_FSIZE caused PulseAudio shared-memory
  `ftruncate` failure and pactl SIGXFSZ. No capture started. Removed that blanket
  restriction while retaining the hard memory tree limit and measured output bounds.
- [Attempt 2](attempt2/receipt.json): correct text output, then source identity check
  assumed native PulseAudio driver string; actual server is PipeWire. Source unloaded.
- [Attempt 3](attempt3/receipt.json): module enumeration incorrectly assumed `index`
  in every module row; KeyError before capture. Source unloaded. This published receipt
  is a declared derived copy excluding unrelated public upstream author metadata;
  original remains in the guest with its original SHA in collection.json.
- [Final run](receipt.json): selected the exact null sink using observed PipeWire
  identity and module arguments; completed capture/prefix/Stop/final/cancellation.
- [Early operator failures](operator-observations.json): boot-time SSH refusal,
  absent remote-tracking ref, unprivileged namespace refusal and image-name correction.

No failed receipt is relabeled as a pass or silently replaced. Raw guest failures
remain in `speech-next-1203/attempt1`, `attempt2`, `attempt3`. Model/audio bytes were
not exported; exact fixture hashes and generating sources are retained. No private
audio, credentials, crash report, cloud destination or paid API call was involved.

## Reproduction, review and handoff

Use only the named existing owned guest and an explicitly granted lease/resource
exception. The five [guest sources](../../../../../spikes/982/speech-next/runner.py)
are a disposable mechanism harness, not product code. `prepare.py` fails rather than
overwriting an existing model and checks the pinned binary/budget/tree mechanism.
Run `session.py` from the real graphical desktop, then `sudo python3 launch.py`
through the guest management channel. Every attempt's launch.json binds all source
hashes before execution. The [collector](../../../../../spikes/982/speech-next/collect.py)
exports only allowlisted text/source files and audio hashes, never the model/audio.
Sources ran uncommitted atop0e7c6b57; execution hash receipts bind their actual bytes,
not a falsely claimed later Git HEAD.

Full prior PR changes remain preserved; reviewed delta is additive speech-only files.
Self-review checked device identity/no-fallback, single inference ownership, bounded
PCM, actual cancellation, cgroup/network limits, unknown locale, source hashes and
failure disclosure. The inherited-graphical-runner and post-Stop drain limitations
above remain explicit; this is not full compliance with a single-process locale runner.
No source was amended after its final runtime receipt. Exact-head repository and
speech-integrity verification results are recorded in the task handoff.

Normal [shutdown](stop.txt) completed at14:03:36UTC; [status](host-after.json) is Stopped.
Exclusive Lima lease returned to active human LINUX-20261016, direction1203/comment10552.
Root owns exact-head independent review, CI/admission, Council and merge. Keep PR12
draft; no ready/merge/auto-merge/done or dependency completion. No future worker wake
is assumed. Native triage10558 concerns an earlier head and is left to root's
consolidation, outside this speech-only assignment.

Downstream #994/#1030/#1031 still own product editor/server round trips, stale-draft
handling, retention, permissions/revocation/device loss and final deb/AppImage tests.
G4 full reports, G8 timed series, provider accounts and installed updater remain open.
