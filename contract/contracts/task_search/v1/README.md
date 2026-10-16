# Task search version 1

Task #1001 adds `GET /tasks/search`. Existing task list, Kanban, lane-page and
desktop contracts are unchanged. This directory is the server contract handoff;
it does not implement a client consumer.

The orchestrator must record the full **merged campus-server main SHA** containing
this contract in the downstream task/handoff after merge. No unmerged feature
branch SHA is a valid contract snapshot source. The client snapshot PR comes
before a client rendering PR; this API change does not require a simultaneous
client release. A consumer that does not understand `version: 1` must withhold
this projection rather than infer its semantics.

The contract was revised before merge/snapshot in response to the owner's
2026-10-16 review. Snapshot task #1005 must import this final contract; consumer
task #1006 must honor explicit scan progress, including partial pages with no hits.

## Fixtures

- `empty.json`: a query omitted or empty after stripping returns no tasks, no
  continuation and no unfiltered history scan.
- `project_hit.json`: one project-filtered task with its server-authored project
  label, board lane and detail destination. Identity and timestamp values are
  fixed fixture examples; the integration contract test compares actual Rails
  responses after substituting the test records' ids and timestamp.
- `partial_empty.json`: 100 candidates were examined without a match, but the
  remaining traversal is unknown. `has_more` is true and `scan.state` is partial.
  The example cursor is a placeholder, never a usable signed token; request tests
  normalize the generated cursor to this value for fixture comparison.
- `oversized_partial_empty.json`: one oversized candidate was examined alone without
  a match. Its actual `examined_bytes` exceeds the normal `max_bytes` budget, and the
  continuation still reaches older project candidates. The request test normalizes
  the project id and generated cursor before comparing this fixture.

The authoritative schemas and parameter/error contracts are `TaskSearch`,
`TaskSearchRow`, `TaskSearchError` and `TaskSearchUnavailable` in
`api/docs/openapi.yaml`.

## Matching, scope and bounds

`q` is optional and capped before normalization at 200 characters and 800 UTF-8
bytes; invalid text encoding and NUL characters are refused. Rails applies Ruby
`String#strip` only: internal whitespace, case and Unicode normalization are
preserved in `query.text`. PostgreSQL `ILIKE` matches
a literal substring against title **or** description, using the database
collation's case comparison and no accent folding, tokenization, stemming or
fuzzy ranking. `%`, `_` and `\` are literal characters. Empty normalized queries
return the empty projection. Duplicate titles are independent rows keyed by id.

All supported task stages and board lanes participate, including approval and
Done/Closed history. Results are scoped to the authenticated principal's current
island. A positive `project_id` optionally narrows that scope; absent and
inaccessible projects have the same 404 response. Every page checks authorization
again. The endpoint requires `tasks:read` and refuses visitor agents.

`page_size` defaults to 25 and must be a whole number from 1 through 50. Before
matching text, Rails selects at most 100 ordered candidates in the island/project
scope. Comparing full title/description text is limited to a prefix whose combined
UTF-8 title/description size is at most 1 MiB (1,048,576 bytes), except that an
oversized first candidate is always examined alone under the same 500 ms statement
timeout. This permits progress past large tasks without skipping their matches or
permanently blocking older tasks. No total count is computed. Reaching the
candidate/text budget returns explicit partial progress with a continuation;
it never silently drops a candidate. If a statement times out, Rails returns a
retryable 503 instead of an empty success. Search rows contain
at most 280 title characters and 280 description characters, with separate
`title_truncated` and `description_truncated` flags and no added ellipsis. They
contain no task association collections; use `detail.href` for the full task.
Matching uses full titles/descriptions, so a match can be beyond a returned prefix.

## Paging and client cache completeness

Rank is always `id_desc`, not relevance. Use only the opaque `next_cursor` returned
by Rails and preserve normalized query, project and page size. Signed cursors are
at most 4096 bytes, bind the principal and island, and expire after 15
minutes. An invalid/expired/rebound cursor returns 422 with
`code: task_search_invalid_cursor` and version-1 `pagination_recovery` whose action
is `restart_without_cursor`. Parameter errors do not carry recovery.

The first page anchors the highest candidate id. If a window contains more
matches than `page_size`, continuation reads strictly below the last returned
match; extra matches are reconsidered rather than skipped. Otherwise it reads
below the last examined candidate, even when the page returned zero matches.
Returned ids cannot repeat, and deleting an earlier row does not shift remaining
pages. Higher ids require a new search. This is a **live** read: changed tasks may stop matching, deleted tasks
are omitted, current descriptions/project labels are returned, and newly matching
or late-committed lower ids may appear while their range remains ahead of the
cursor. An already passed id is never revisited within that traversal.

`scan.state: partial` and `page.has_more: true` mean exhaustion has not yet been
established: another range or undelivered matches may remain. They do not promise
that the next page contains a match. Continue
with `next_cursor` even when `tasks` is empty or shorter than `page_size`. A full
100-candidate window may require one final empty page before Rails can report
exhaustion. Consumers must never label a partial empty page as "no matches."

`scan.examined_count` and `scan.examined_bytes` describe this request's text-matching
candidate work, capped at `max_candidates: 100`. `max_bytes: 1048576` is the normal
byte budget; `examined_bytes` may exceed it only when an oversized first candidate
is examined alone (`examined_count: 1`). Byte counts include full title and
description text, with null descriptions counting as zero; they exclude project
labels and response metadata. They are not
cumulative: output overflow can cause candidates to be considered again on the
next request. Never sum them into a complete-result count or coverage claim.

`scan.state: exhausted` agrees with `has_more: false` and `next_cursor: null`.
It ends this traversal at the current read but does not certify a complete current
island search index, even after every page was loaded.
`consistency` therefore always says `mode: live_keyset`, `cache: display_only` and
`complete_snapshot: false`. Responses carry `Cache-Control: no-store`.

Any transient client display cache must remain tied to its exact principal,
island, query and project scope and be replaced when that scope changes. It must
not answer new searches locally, claim authoritative absence, or claim full
coverage from an exhausted traversal. Start without a cursor to refresh; use the
API's current task detail when opening a result. Render project labels, board
lanes and detail destinations from Rails verbatim.
