# Speech recovery v1 consumer handoff (task #836)

Snapshot only after the API PR merges; use its **merged main SHA** in the Mac's
`contract/.source`. Mac task #837 implements the consumer; release verification is #838.
The server PR's draft/head is not a valid snapshot source.

`capability.json` is served under `recovery` by `GET /task_transcription?recovery_version=1`.
Absent/unknown recovery versions must withhold recovery upload. The default capability
and existing Apple text/WAV contracts remain unchanged. `plan-request.json` represents
Stop with no final text despite earlier partials, with all five minutes retained.

1. Keep at most 300 seconds of mono 16 kHz signed little-endian PCM16 in memory
   (9,600,000 bytes); never a temporary recording file, database field, log or attachment.
   Discard on successful transcript, explicit cancel, draft dismissal or 900 seconds
   after Stop. Expiry never deletes the user's text. Lost memory means honest manual recovery.
2. Send normalized facts, not error prose. Empty final and finalization timeout are not
   proof of no speech. `had_partial_text` never asks Rails to manufacture a final transcript.
   Capture failure / no retained audio gets manual recovery; no provider can fix a missing mic.
3. Prefer the returned `replay_on_device` action with **requires-on-device** recognition.
   It must not silently use Apple's network recognizer. Replay once; if unavailable/failed,
   replan with `on_device_available=false`. Ordinary successful Apple text costs no account.
4. Show Rails' consent copy plus selected account labels, model and Google destination.
   Only an explicit decision may POST the offered subset and disclosure version to authorize.
   Both `tasks:write` and `credentials:write` are required for cloud use. Same island alone
   is insufficient. Scoped clients without account authority receive manual/local recovery.
5. Split all samples into sequential, nonoverlapping 30-second chunks (480,000 samples),
   with the exact remainder last; at most ten. Construct canonical 44-byte WAV headers,
   no extra chunks. Each decoded chunk is at most 960,044 bytes; base64 at most 1,280,060.
   Send bounded JSON with **Content-Length**, no multipart or Transfer-Encoding, at most
   1,300,000 request bytes. Dispatch the advertised `upload_chunk` action one at a time.
6. Preserve the recording UUID and chunk bytes for retries. Duplicate delivery never spends
   again; changed content under the same identity is refused. Poll after transport loss,
   no faster than every two seconds. Do not create new UUIDs to bypass an uncertain operation.
   Provider timeout 20 seconds, attempt deadline 25 seconds, maximum three accounts and
   twelve provider calls. Each HTTP request makes at most one provider call to fit hosted
   runtime limits. On a candidate failure, follow the returned upload action (same chunk,
   incremented `attempt` query) with identical bytes; earlier attempt replays only read state.
   Failed accounts are not retried elsewhere in the same recording.
7. Only `state=succeeded` carries one canonical validated transcript. Render it once, for
   the still-active draft and matching UUID. Other states preserve the partial/manual draft.
   Cancellation prevents subsequent dispatch when observed and discards late results; an
   already-dispatched call may still finish and incur its charge. Cancel on dismissal.

The only cloud adapter in this slice is Google Gemini 2.5 Flash `generateContent` inline
`audio/wav`, with API-key credentials. Supported base language tags: en, es, fr, de, it,
pt, ja, ko, zh, ru; other languages retain local/manual recovery. No CLI login, text-only
model or Coordinator assignment is treated as audio capability. Both fallback switches,
exclusions, exhaustion and the shared usage gate are honored. Consent pins secret revision.

Adapter evidence: `task_transcription_provider_test.rb` verifies the exact host, key, model,
inline WAV bytes, bounded response and failure normalization using fake HTTP. The recovery
integration tests exercise actual Rails routes with synthetic WAV and fake providers.
`transcription_memory_transport_test.rb` uses a local Puma socket and prohibits Tempfile
creation to prove that accepted audio stays in memory and oversized/chunked requests fail
before spooling. No paid or live provider call is part of verification.

Provider protocol reference: https://ai.google.dev/gemini-api/docs/audio (checked 2026-10-09).
This is a rollout contract, not a claim that the current Mac already retains or recovers audio.

Server text retention is distinct from client audio retention. Transcript reads expire 900
seconds after plan creation, including successful results. Failure, cancellation, and an
expired read clear server text immediately. The existing local/hosted minute tick clears up
to 500 expired text rows per island/pass and deletes up to 500 expired replay identities after a
24-hour grace period. Physical cleanup may lag during maintenance outages or backlog; expired
text is never returned. Client draft text remains the client's draft and is not erased.

An empty successful provider chunk advances without account fallback, including a silent
trailing remainder. Only an entirely empty combined final transcript reports `empty_result`.
The authorization and succeeded fixtures are compared against real HTTP responses in tests.

The opt-in local check `python3 api/script/check_transcription_lambda_transport.py` runs the
Dockerfile's actual Lambda Web Adapter against a synthetic local runtime and HTTP listener.
It verifies both API Gateway body envelope forms arrive intact with Content-Length and without
Transfer-Encoding. It needs local Docker and the public adapter image; it is not scheduled or
part of ordinary CI, and makes no AWS or provider invocation.

Verified 2026-10-10 with adapter 1.0.0 (image manifest digest
`sha256:b4da35991627bdac98a81c377d0cc28e6989687359576dfda9f0b64be835d648`):
both envelopes forwarded 1,280,094 bytes intact with Content-Length and no Transfer-Encoding.
This is local adapter evidence, not a production deployment smoke test; #838 owns that check.
