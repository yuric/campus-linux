# Project alarm request previews

Each existing `ProjectSnapshot.alarms[]` gains `request` version 1. All legacy fields,
alarm membership, ordering, and aggregate `attention` semantics stay unchanged. In particular,
a question on a task without an alarm does not add an alarm, and quota reset waits remain
excluded. No new polling endpoint is introduced.

The kind and label distinguish an assistant failure or blocked error, a review in the
Project's bound repository, the newest unresolved agent question on the alarm's live task,
and an ordinary input block, in that precedence order. Unknown blocked kinds use `unknown`
and withhold actions. A missing blocked kind retains the legacy needs-input meaning.

`preview` is plain display text, never markup or instructions. Rails applies `DisplaySafeText`
and `CopySafeDetail.redact_human_text` before shortening to 240 characters, including ellipsis.
`preview_truncated` reports shortening or an input too large to inspect safely. Inputs over
32,000 characters are withheld entirely. No original body, prompt, description, diagnostic
payload, credential, or hidden tail is included in `request`. The redactor's documented
ordinary-word residual applies: arbitrary secrets encoded as unlabelled prose cannot be
recognized. Task actions only navigate; fetch the task's current contract before responding.

Clients render `label`, `preview` and `action.label` verbatim and preserve array order. The
action's `kind: task` opens `task_id`. Unknown versions or kinds withhold actions; they never
fall back to client classification. Older servers omit `request`, in which case clients may
keep the existing generic task-opening presentation. Older clients ignore this additive field.

`requests.json` is pinned against Rails responses with task IDs normalized to 42. Import it
only from the merged campus-server main commit; this API-only card does not update clients.
