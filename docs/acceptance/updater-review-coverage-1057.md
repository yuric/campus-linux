# Installed updater #1057: supplemental review coverage

LINUX-20261016 / PR13. Reviewed head: `2c4839e9883725d47ba47ced51a9b97d0f637fa9`.
Council base: `e2628c3ebef933a13d20366c1f6998e105258bbd`.
This publishes actual supplemental review evidence and corrects one historical documentation
ambiguity. Executable source and all original runtime receipts remain unchanged.

The standard Council [eight requests](https://github.com/yuric/campus-linux/pull/13#issuecomment-6228368927)
and separate red-team [two requests](https://github.com/yuric/campus-linux/pull/13#issuecomment-6228399239)
reported missing implementation evidence, not demonstrated defects. GitHub omitted the
541-file diff and the Council packet lacked repository context. This review had actual
read-only access to the complete exact-head checkout, including source and images.
Publishing this document does not imply that a future Council run automatically reads
archives, links or material omitted from its packet. Council disposition and the trusted
merge judge remain separate gates.

## Actual reviewer and result

Claude Code, actual model `claude-opus-5-5`, fresh session
`d410016a-cb65-4cd1-aa1a-c9c40178f852`, ran 2026-10-17 02:33:01–02:38:18 UTC with
Read/Grep/Glob tools only. It executed no source, tests, guest commands or Git operations.
It found one P3 historical-documentation ambiguity and no P1/P2 or demonstrated exploit.
This is an **AI review, not human approval or Council clearance**.

Read the [complete verbatim result](receipts/installed-updater-1057/review-supplemental-2c4839/opus-verbatim.md),
[original provider result](receipts/installed-updater-1057/review-supplemental-2c4839/opus-raw.json)
and [model/session/hash proof](receipts/installed-updater-1057/review-supplemental-2c4839/opus-proof.json).
The provider result preserves the reviewer's coverage statement; it is not a complete
serialized tool-call transcript. Its model/session fields are actual output, not an
invented reviewer persona. The [publication index](receipts/installed-updater-1057/review-supplemental-2c4839/index.json)
binds these exact files.

The P3 is addressed in [the acceptance document](installed-updater-1057.md): the docs-only
paragraph now names historical commit `5c1cf8c`, keeps its 110-test result tied to4001,
and distinguishes the later1329 result of108 probe +10 adapter +49 repository tests,
167 total. The earlier paragraph already named4001, so this clarification does not
establish a source bug or invalidate fixture acceptance.

The result's closing CI-gap statement concerns the historical document and the reviewer's
unavailable live CI view. The Council packet itself recorded eight successful conclusions
at2c4839; neither replaces fresh current-head CI/admission. The actual Anthropic review
is different-family from the OpenAI author/coordinator; its generic closing statement
that different-family review remains must not erase this completed consultation.

## Ten evidence requests, independently accounted for

| Request | Actual review evidence and disposition |
|---|---|
| Standard1: source/tests/patch and behavior | Current app, adapter, bootstrap, policy, hosted scripts, workflow, adapter tests, UI and full acceptance text read. Earlier exact-byte lifecycle/test reviews explicitly carried. P3 only. The model did not read the gzip patch; full current source was directly accessible instead. |
| Standard2: acceptance/receipts/images | Startup5 acceptance, independent review, handback and full correlation read; desktop excerpts and identity records read. All38 runtime PNGs inspected. Original failed denial/cancellation attempts remain failed. Detailed raw evidence limits are below. |
| Standard3: implementation/maintainability | Current boundaries inspected and prior1329 review carried only within its lifecycle-delta scope, not represented as a whole-PR approval. No new source finding. |
| Standard4: workflow/cost | Full current workflow, run.sh and prepare script inspected. Added adapter-test discovery is bounded inside existing hosted job limits. No new resource provisioning. Prior timeout/cleanup advisories remain qualified, not silently fixed. |
| Standard5: security source | Current root-staging, admission, signature and privilege-at-use paths inspected with full source available. No exploit identified; no human review claimed. |
| Standard6: confinement/CI/authority | Actual app→pkexec→installer→dpkg and AppImage boundaries traced. Current gated lifecycle carried from byte-matched1329/2928 review. Fixed policy target and isolated CI inputs remain scoped to disposable fixtures. |
| Standard7: privacy | All38 screenshots plus icon visually inspected; regex scan across receipt text. No credentials identified. Host paths and identity-file path remain provenance, not private-key contents. No assertion every text receipt was individually reread. |
| Standard8: UI/recovery/focus | Static page has no JS, buttons or forms; update is CLI-only. No in-app retry/cancel/focus flow exists. OS-polkit frames show limited initial-focus observations, not keyboard testing. No new product interaction requirement inferred. |
| Red-team1: adversarial authority/custody/workflow | Current execution/privileged boundaries inspected, exact lifecycle review carried, and custody evidence considered with stated hash-verification limits. No exploit demonstrated. |
| Red-team2: deeper execution review | Same actual supplemental review addresses this separately numbered request; app/pkexec/installer/dpkg/AppImage traced. No new finding; lifecycle carry is explicit rather than pretending it was reread. |

These are evidence dispositions for coordinator assessment. They do not assert the
formal Council escalations have been cleared or that a summary-only rerun will succeed.

## Immutable source and receipt bindings

The [541-file parent manifest](receipts/installed-updater-1057/review-supplemental-2c4839/parent-files.json)
contains exact lengths, SHA256 values, modes and immutable GitHub links for all source,
configuration, tests and original receipts available at the reviewed head. Availability
does not mean every leaf was individually read. The coordinator independently verified
these bindings; the outside reviewer did not recompute hashes.

The [source carry record](receipts/installed-updater-1057/review-supplemental-2c4839/source-carry.json)
compares current bytes with actual prior full-source review packets. Forty of43 non-receipt
files match earlier complete prompt bytes, directly or through verified line-numbered
full-file manifests. A prompt match proves delivery, not universal approval; previous
findings and their dispositions still govern. The exceptions were the changed acceptance
document, current hosted/run.sh and binary icon. This supplemental review read the current
document/run.sh and visually inspected the icon. Current run.sh differs from113a only by
adding the adapter-test discovery command. No lockfile or executable was changed here.

Useful immutable entry points include the
[workflow](https://github.com/yuric/campus-linux/blob/2c4839e9883725d47ba47ced51a9b97d0f637fa9/.github/workflows/l0-installed-updater.yml),
[installer](https://github.com/yuric/campus-linux/blob/2c4839e9883725d47ba47ced51a9b97d0f637fa9/spikes/1057/installed-updater/adapter/install-deb.py),
[app](https://github.com/yuric/campus-linux/blob/2c4839e9883725d47ba47ced51a9b97d0f637fa9/spikes/1057/installed-updater/src-tauri/src/main.rs),
[static UI](https://github.com/yuric/campus-linux/blob/2c4839e9883725d47ba47ced51a9b97d0f637fa9/spikes/1057/installed-updater/ui/index.html)
and [raw startup5 receipt directory](https://github.com/yuric/campus-linux/tree/2c4839e9883725d47ba47ced51a9b97d0f637fa9/docs/acceptance/receipts/installed-updater-1057/activation-startup5).
The manifest supplies equivalent exact links for every other input.

## Evidence limits retained

The model inspected14 startup5,8 activation10908,7 activation1285,3 authority-continuation
and6 phase-b PNGs, plus the icon. It did not individually reread roughly480 text receipts;
its privacy regex scan is not universal proof of absence. It read raw desktop excerpts
and full correlation, but did not separately read the complete authority/journal files.
It did not read compressed archives/patches or independently recompute hashes. Current
gated source was carried from previous actual reviews, not reread. No OS keyboard/focus,
provider, package installation or guest runtime was executed by this consultation.

Separate root/independent actual review did inspect the raw desktop, authority and journal,
replay the frozen correlation, verify89 original hashes and92 published leaves, and check
protected/package/fixture equality through logout. See the unchanged
[root disposition](receipts/installed-updater-1057/activation-startup5/coordinator-acceptance.json),
[independent actual review](receipts/installed-updater-1057/activation-startup5/independent-review.md)
and [handback](receipts/installed-updater-1057/activation-startup5/final-handback.json).
The raw recorder remains `not_certified`; correlation remains `exact_logind_session=false`.
The accepted scope is controlled arm64 deb denial in observed normal GDM Wayland custody,
correlated through root observations of the user manager. Direct app/logind certification,
production signing, provider authentication and product-wide acceptance are not claimed.
Earlier unclean shutdown remains history; normal later shutdown does not prove filesystem
consistency. All original raw observations remain byte-identical.
