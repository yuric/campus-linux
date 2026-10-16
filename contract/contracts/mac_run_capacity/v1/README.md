# Per-Mac Office run cap

`settings.json` is the additive subset of GET/PATCH `/settings` for the human-owned cap.
The integer accepts 1 through 200 and defaults to 76. The label and help are Rails-authored.
`setting_bound.json` is a LandingCapacity v1 response for 96 GiB available, 28 processors,
cap 10 and three running Offices. Rails tests compare both fixtures to served values.

The same `governing_bound` field accompanies `ExecutionCapacity.max_concurrent_runs` on
claims and heartbeats, and the capacity inside `executor_bulk_landing`. Values are
`setting`, `memory`, `processors`, or null. Ties prefer setting, then memory, then processors.
Null covers fallback governed by the safe default, unsupported/paused capacity and broker
serial execution. Unknown local resources offer min(11, setting); executor admission still
pauses for unreadable observations. Clients render the explanation rather than parsing it.

This is additive in v1. Older clients can ignore the new fields and continue enforcing the
sent maximum. Missing broker capacity v1 support still pauses parallel admission. Lowering
the setting only withholds new claims; running attempts are never stopped by this setting.
