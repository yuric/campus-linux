# `change_check.json` notes

`change_check.json` is the `GET /tasks/kanban/revision` answer (task 719), frozen as data for
the Mac client (card 743). `revision` and `revalidate_at` are per-request values; every other
field is what Rails serves, and `BoardChangeCheckContractFixtureTest` fails when they drift.

## `refresh_rule: every_read_agrees`

A scope's refresh group is every read of that scope the client currently renders: for `board`,
the task lists, the Kanban and its lane pages, and an open task panel (`GET /tasks/{id}`); for
`fleet`, `GET /agents`. Each of those reads returns the scope's token in the scope's `header`.

1. Store the scope's token only when every read in the group carried the same header token.
2. While any two disagree, store none. The scope is dirty, and the next check refetches the
   whole group, whatever token it answers.
3. When the check answers the stored token, fetch nothing.
4. Take tokens from the reads' headers, never from the check itself.

Never store the token of whichever read came last. A task renamed after the list was read,
followed by opening that task's panel, gives the panel the new token while the list on screen
still shows the old title; storing the panel's token would make the next check match and leave
the stale list up until `revalidate_at`. `BoardChangeCheckContractTest` pins this two-read case.

A client that does not recognize the `version` or a scope's `refresh_rule` must not use the
check for that scope and keeps its previous full-refresh polling.
