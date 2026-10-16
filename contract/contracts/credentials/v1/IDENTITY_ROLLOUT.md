# Account identity rollout (tasks 927 and 928)

Rails is authoritative. Ship this API and snapshot its merged main SHA in campus-macos
before implementing the consumer, then run the server candidate and pin bump sequence.

- GET the owned executor's credential binding. `identity_context` names version 1,
  the opaque isolated scope, and the comparison revision. The same context is included
  in native usage plans, auth rechecks, and executor usage refresh offers.
- Collect inside that scope. Report `binding.observation.identity` version 1 with the
  context revision, provenance, account and organization IDs, and optional email. A
  generation success does not prove identity. `local_metadata` is never `live_provider`.
  Unknown provenance, omitted identity or inconsistent local evidence cannot confirm it.
  Rails stores only island-keyed hashes of provider IDs and historical email attribution.
- Include identity evidence on every binding PUT, including failed generation reports, when
  the independent identity read succeeded. Omission explicitly makes identity unknown/stale.
  Evidence expires after 24 hours; all non-revoked bound Macs must agree before a credential-wide
  shared-capacity warning is possible. Verifying only one Mac cannot clear conflicting or
  stale evidence on another non-revoked Mac. Refresh the existing owned bindings, without forced relogin.
  Revoked Macs retain their historical binding records but do not participate in current
  identity, shared-capacity decisions or warning fingerprints.
- Expired binding identity retains the latest known email, provenance and observation time
  in `identity.history`; the single-binding credential diagnostic renders the same history.
  Untouched legacy bindings retain their identifier with `legacy` provenance and a null
  observation time, including after the first identity-less observation. That write seeds
  history from the binding identifier before the credential-wide email; existing versioned
  evidence retains precedence. History never restores current `account_email` or shared-capacity proof.
- The legacy database email is retained for existing admission/review behavior when new
  identity is missing. Public attribution and shared warnings never treat that column as
  current proof. This change does not redesign those existing admission rules.
- The revision advances for each accepted binding observation. Fetch the resulting context
  before usage. Echo its revision in `observation.identity_revision`. To receive `current`
  attribution, also send `observation.identity` from the same live usage collection;
  its account/organization must match the accepted identity. A different identity or old
  revision receives 409 and leaves the snapshot unchanged. Refetch and recollect; never
  re-stamp an old result. The helper must check scope/account before and after collection.
- Legacy collectors can continue with `partial` usage attribution until their binding first
  accepts versioned identity evidence. After upgrade, missing revisions are refused, even
  after later identity-less verification. A legacy Mac cannot replace a snapshot already
  carrying current attribution. No global rollout flag or indefinite downgrade fallback.
- Render `account_diagnostic` and usage `attribution` verbatim. Unknown versions withhold
  the corresponding identity/warning/actions rather than falling back to email grouping.
  Existing `shared_account` and catalog `shared_accounts` remain but only represent fresh
  confirmed Anthropic account-and-organization matches. The legacy display email may be
  empty when live identity provides no email. Email-only historical matches are suppressed.
- Dismiss only the warning fingerprint, per signed-in Campus user. Fingerprints exclude
  timestamps, revision counters and quota percentages. Shared-capacity fingerprints include
  sorted sibling credential IDs, so a new sibling re-raises a dismissed warning. No dismissal changes Rails state,
  authorization, credential selection or quota enforcement.

## Traced boundary and verification limits

Inspected campus-macos pin `5812c612dc3883a14f9b4844704afa663fae55ce` read-only:
`CredentialsStore.swift` forwards `result.accountIdentifier` from the broker. The broker's
`VerifyService.accountEmail` in `Sources/CampusBrokerCore/Services.swift` first reads a
Claude status-response email, then tries isolated local login metadata. Both can yield nil.
That is a verified omission path, not proof of why the specific production observation
omitted identity. Local metadata for the two affected credentials is not live provider
confirmation, and quota differences establish neither identity nor independent capacity.

After the API and successor collector ship, reverify credentials 34 and 18 through their
existing owned Mac binding flows. Compare normalized provenance/state and shared-capacity
results, then collect usage with the returned revision. Do not overwrite email manually,
delete credentials, force relogin, or copy tokens/config/provider IDs into evidence. Confirm
that correcting distinct live identities clears the warning and that a later identity-less
failure keeps it cleared. If live identity cannot be obtained, report unknown/stale honestly.
Production reconciliation is release/successor verification; this API PR does not claim it
has run or that either current provider identity has been confirmed.
