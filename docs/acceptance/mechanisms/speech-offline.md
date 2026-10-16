# Offline speech candidate — #982

Human direction 10361 authorized this bounded local/offline mechanism test using
public synthetic audio. It did not choose a product backend, authorize a cloud
service or paid inference, or waive permissions/privacy acceptance. The actual
Linux arm64 CPU candidate ran successfully with network interfaces restricted to
loopback. This supplements the WebKit availability observations in
[renderer-speech.md](renderer-speech.md); it is not installed-product speech parity.

## Pinned inputs and reproduction

[Source/model pins](../../../spikes/982/speech/pins.json) bind
[whisper.cpp v1.9.5](https://github.com/ggml-org/whisper.cpp/tree/d1be6fde11ac6e0407606b4e42fe72d34add8037)
to commit `d1be6fde11ac6e0407606b4e42fe72d34add8037` and the converted `tiny.en`
model to [Hugging Face revision 5359861c739e955e79d9a303bcbc70fb988958b1](https://huggingface.co/ggerganov/whisper.cpp/tree/5359861c739e955e79d9a303bcbc70fb988958b1).
The source SHA256 is `645445da884df6dbd52b30f82d7be7c01d1767c938714e477e786b88d529e9f4`;
the model SHA256 is `921e4cf8686fdd993dcd081a5da5b6c365bfde1162e72b08d75ac75289920b1f`.
The downloader enforces exact hashes and sizes (87,336,171 bytes total).
These are pinned public HTTPS artifacts, not proof of an independently signed
speech release or an approved product supply chain. whisper.cpp is MIT;
[OpenAI Whisper code and model weights](https://github.com/openai/whisper#license)
are MIT. Ubuntu eSpeak NG generates the test fixture locally; it is a test-only
prerequisite, not an adopted product dependency. The original test sentence is
CC0-dedicated and contains no user data.

Run only in the owned disposable Ubuntu 24.04 arm64 guest. The parent operator
owns guest access and provisioning. Prerequisites are `python3`, `libespeak-ng1`,
`cmake`, `g++`, and **`make`**. The first attempt omitted make and failed CMake
configuration; [its failed receipt](receipts/speech-offline-attempt1/receipt.json)
and logs remain evidence of that failure, not a pass. Ubuntu package resolution
was not an immutable dependency closure: the actual receipt records cmake
`3.28.3-1build7`, g++ `4:13.2.0-7ubuntu1`, and libespeak-ng1
`1.51+dfsg-12build1`, all arm64. The successful run predates the script's addition
of make version capture; do not infer a recorded make version or synthesizer
library digest from it.

With scripts and adjacent pins copied to the guest:

```sh
sudo runuser -u campusqa -- python3 /path/probe.py download /home/campusqa/spike982/speech-offline
sudo unshare --net runuser -u campusqa -- python3 /path/probe.py offline /home/campusqa/spike982/speech-offline
```

The observed successful run used `speech-offline2` with verified input files
hardlinked from the first attempt. A future failed run can use `offline <same-dir>
--resume`; this requires matching pins and a failed receipt, preserves its old
captures, verifies inputs again, and reuses the build directory. Never overwrite a
successful receipt. The [probe](../../../spikes/982/speech/probe.py) configures a
CPU-only build with GPU, curl, SDL, server, external FetchContent, native CPU tuning
and OpenMP disabled. Exact configure/build/transcription arguments, executable
SHA256, environment, source license digest, stdout/stderr and outputs are in the
[captures](receipts/speech-offline/receipt.json). No audio-device API is used by
fixture synthesis or transcription.

## Observed local inference

The actual guest was `lima-campus-linux-d5-noble-arm64`, Linux
`6.8.0-142-generic`, `aarch64`, UID 1000. The inference namespace had only `lo`.
The binary SHA256 was
`50712621452d3ab5f0d7b2a2c5dbaad5100c8d9b86538da1e1a192074b3ec2a2`.
The fixture was 6.1608125 seconds of mono PCM16 at 16 kHz, 197,190 bytes, SHA256
`5652875067982ca45b0aba111e247a186168f89a03a4ec80680ae2ed7bb688a2`.

| Actual operation | Wall time | Child CPU time | Sampled maximum RSS | Result |
| --- | ---: | ---: | ---: | --- |
| First inference after build | 2.454 s | 3.402 s | 177,404 KiB | Exit 0; nonempty transcript |
| Second inference | 1.408 s | 2.557 s | 177,380 KiB | Exit 0; nonempty transcript |
| Third inference | 1.538 s | 2.793 s | 177,360 KiB | Exit 0; nonempty transcript |
| Cancel 50-second synthetic fixture | 0.517 s total | 0.918 s | 152,136 KiB | Running process terminated by SIGTERM; 0.01398 s from cancellation to observed stop |

“First” does not mean a cold kernel file cache: source, model and binary had just
been read/built. RSS is sampled from `/proc`, not a certified peak. The file-size
sum after the probe was 145,560,225 bytes, not a filesystem allocation measurement.
These are three short CPU-only mechanism observations, not a statistical latency
or battery benchmark, accuracy score, G8 renderer result or general audio-quality
acceptance.

The [transcript](receipts/speech-offline/cold.txt) was:

> The Blue Notebook is beside the window. This is a synthetic speech test.
> Please edit the words before saving.

The probe copied the text into an [editable draft](receipts/speech-offline/editable-draft.txt)
and wrote an [edited draft](receipts/speech-offline/edited-draft.txt); both hashes
are recorded and differ. This proves a mutable plaintext backend result only.
No product editor, submit action or automatic transmission was tested. Empty
and 61-second WAVs were withheld before inference under this test's explicit
60-second/10-MiB/mono-PCM16-16-kHz bounds. Those are disposable probe bounds,
not server rules or chosen product limits. English synthetic speech alone was
exercised; accents, noise, multilingual audio and real microphone accuracy remain
unproven.

## Locale, quality, streaming and recovery limits

Human coordinator follow-up **10427** preserves the shipped Mac's language scope. At the
pinned producer SHA `8e39806c5b1fb2ffeda6e55718a4fd2a4d2890da`,
[SpeechRecording.swift:274](https://github.com/yuric/campus-macos/blob/8e39806c5b1fb2ffeda6e55718a4fd2a4d2890da/CampusApp/Sources/CampusKit/SpeechRecording.swift#L274)
constructs `SFSpeechRecognizer(locale: .current)`; `SystemTaskSpeechDevice.language`
at line 537 returns `Locale.current.language.languageCode.identifier`. The Mac does not
hardcode English. Its live-partial setting comes from Rails; its replay path at line 549
uses the current locale and requires an available on-device recognizer.

This probe deliberately selected `tiny.en` and passed `-l en` for each recorded CLI
invocation. The model is English-only, and the guest/user locale was not recorded in
this inference receipt. It proves neither locale discovery/mapping nor supported-language
coverage, language switching or locale-specific failure behavior. No English-only product
parity claim or silent narrowing of the Mac requirement is authorized.

| Dimension | Observed evidence | Remaining parity proof |
| --- | --- | --- |
| Locale | One forced-English synthetic sentence with `tiny.en` | Current-locale handling and language coverage matching the shipped behavior; unsupported locales represented through Rails capability/wording |
| Quality | Three nonempty transcripts of the same clean synthesized sentence | Representative accents, languages, noise, silence, hallucination/error behavior and editable-result fidelity; no accuracy metric or threshold was measured |
| Streaming | Batch WAV-to-text CLI completion; capture and inference tested separately | Live partials, rolling/segment boundaries, time to first text, final-text reconciliation, latency and cancel during a real streaming pipeline |
| Recovery | Offline inference cancellation and mutable text files | Rails recovery-v1 availability/planning, bounded retained audio, locale-aware local replay, interruption/retry, retention expiry, cancellation races and stale-result prevention |
| Product limits | Disposable 60-second/10-MiB bounds and one 6.16-second fixture | Consume and enforce verified server duration/byte/chunk/retention limits; the probe constants cannot become product policy |

Recommendation: retain the measured offline candidate as useful engineering evidence and
continue the authorized mechanism work against the locale/quality/streaming/recovery gaps.
A library by itself is an engineering choice under PRD section 9; this record does **not**
create a separate owner-approval requirement for its name. Escalate a concrete change to
product scope, privacy, spend or trust—for example an English-only limitation or a cloud
fallback—before adopting that change. No such change, paid call or library adoption is
asserted here. Any additional large model download needs a budget/reserve check first;
this documentation update downloaded nothing.

## Privacy, permissions, interruption and cost

Inference was actually offline, so no audio or transcript could be sent to a cloud
endpoint through the isolated namespace. Public initial source/model downloads
contact GitHub and Hugging Face and disclose ordinary network request metadata;
they contain no audio or credentials. The probe uses local CPU, RAM and storage,
with no inference API fee. This is a measured candidate, not authorization to add
those hosts to a product download flow. Audio/transcripts remain in disposable
guest directories with a private umask; product retention, deletion and disclosure
policy still require disposition. No host microphone was accessed.

The separate [synthetic audio-server probe](../../../spikes/982/speech/microphone_synthetic.py)
requires `pulseaudio-utils` (`pactl`, `paplay`), `libpulse0`, the adjacent
[bounded recorder](../../../spikes/982/speech/synthetic_recorder.py), and the existing real GDM
user's PulseAudio/PipeWire socket. After inference created the public fixture,
run in each real session:

```sh
sudo python3 /path/microphone_synthetic.py /home/campusqa/spike982/speech-offline2 --label wayland
sudo python3 /path/microphone_synthetic.py /home/campusqa/spike982/speech-offline2 --label x11
```

The script validates the requested active local `gdm-password` user session,
records same-user enabled and separate-UID denied access to the actual session
audio socket, creates a uniquely named null sink/monitor, records only that
explicit synthetic monitor and cancels its recorder. It stops all streams before
unloading the synthetic source; unloading a live source could cause audio-server
fallback onto a default device. The recorder additionally sets libpulse's
[`PA_STREAM_DONT_MOVE`](https://github.com/pulseaudio/pulseaudio/blob/v16.1/src/pulse/def.h)
flag, validates the exact device name before each read, and bounds recording below
1 MiB/10 seconds; it cannot silently move to a default source. It never
opens a default/hardware microphone. Captures are separate per session and fail
rather than overwrite. The root orchestrator rejects any host other than the named
owned guest; it records script hashes and returns nonzero unless both UID checks,
nonzero bounded samples, active-recorder cancellation below two seconds and cleanup
all pass.

The actual [X11 capture](receipts/speech-microphone-x11.json) and
[Wayland capture](receipts/speech-microphone-wayland.json) both pass these narrow native
audio-server checks on PipeWire 1.0.5's PulseAudio server. Both are active, local
`gdm-password` sessions: X11 session 6 and Wayland session 11. In each, UID 65534 is refused
access while UID 1000 connects, the dedicated synthetic monitor yields nonzero bounded
samples, the running recorder is stopped by SIGTERM, and the temporary module is unloaded.

| Session | Synthetic capture | SHA-256 | Cancellation to observed stop |
| --- | ---: | --- | ---: |
| X11 | 49,152 bytes | `b887f8618ed4472c52a61c9bebfca8bf3dd609e63fd26846ea4c47b127f06d8d` | 0.001681 s |
| Wayland | 53,248 bytes | `ce68a2f4a406fd594f7a196043f13f2e0afd721d71c7d16dd78b1759b6c6da41` | 0.001203 s |

Both receipts bind the recorder/probe hashes and original public fixture, with
`checks_passed`, `completed` and source-cleanup true. Neither uses the default or hardware
microphone. The two sessions establish this bounded audio-socket access/cancel mechanism;
recording and offline inference are still separate probes, not an integrated live
speech-to-editor product flow.

Even successful native audio-server access would not prove product/browser
microphone permission prompts, portal grant/denial, permission revocation,
physical-device interruption, source selection UX or consent enforcement.
Those remain explicit acceptance gaps. Same-UID PulseAudio access also does not
establish protection against another process running as the user. The measured
inference cancellation above proves process interruption, not recording permission
revocation.

LINUX-20261016 must disposition any changed product/privacy/spend/trust trade-off and coordinate the
speech observations into #1030, then #1031 for #994/#996 as applicable. Functional
integration and all applicable final-package permission, cancellation, offline,
retention and editable-result cases remain for LINUX-16/17. This candidate does
not unblock those gates on its own.


## Historical execution-source binding limit

The successful `speech-offline/receipt.json` omits `probe_sha256`. Its executable,
source/model and output hashes identify those artifacts, but they do not identify the
exact Python orchestration script executed. The current committed probe has later
changes, so **execution-source binding is unproven**. The recorded timings/cancellation
remain historical observations, not current-probe or product acceptance. The original
raw logs have now been restored with their indexed hashes; this repairs delivery, not
the missing script binding. A future bounded recapture must record that binding.
