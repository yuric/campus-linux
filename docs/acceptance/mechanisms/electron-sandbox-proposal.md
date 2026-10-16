# Unexecuted fresh-inode Electron sandbox proposal

LINUX-20261016 / #982 / human10834 and direction1318. **Source review only;
installation, rollback and runtime remain unexecuted. No guest lease is active.**
The [1288 failure](receipts/g8-electron-1288/REPORT.md) is a sandbox prerequisite
failure, not a benchmark miss. Root and independent review must accept the exact
source before a separately activated, freshly budgeted guest window.

The [fixed-fixture operator](../../../spikes/982/environment/electron-sandbox-operator.py)
supersedes the [rejected move/chown source](receipts/g8-electron-1288/rejected-move-operator.py.txt).
Moving and changing ownership cannot revoke already-open writable descriptors.
Process absence scans are not a substitute for creating new root-owned inodes.
The rejected source was never activated; its [four historical validator results](receipts/g8-electron-1288/operator-input-tests.txt)
do not validate this revision.

## Exact proposed custody

The only input is the existing guest archive, 124,393,671 bytes, SHA256
`502296281cab3c333bd5193e2eaed11c3bb28eabd7a451a49776a3e5a9468f8c`.
Read it once through a bounded no-follow regular-file descriptor. Verify that same
immutable byte buffer before parsing and extracting it; never reopen the pathname
to extract, copy the archive to disk, or consume the old user-writable extraction.

The source pins the complete 72-file hash map from the retained
[verified extraction receipt](receipts/g8-electron-1288/spike-extraction.json).
Validate exact membership, 302,048,805 total bytes, canonical relative paths,
duplicates, directory/file collisions, types, ordinary modes, and individual
sizes/digests. Reject links, special files, encrypted entries and privileged modes.
Preserve both license files. The preparer's generated spike-extraction.json is
not a vendor member and is not copied into the new runtime.

The new exclusive target is:

```text
/opt/campus-linux-spike982/electron-44.8.0-730d44d5aefb6a969b209cf8ee3e843bd873a06c297bf2c409fbb1cebcb3e6bc
```

Require root:root, non-user-writable ancestry through /opt. Refuse an existing
target or ledger, including dangling symlinks. Create target0700 and runtime/files
exclusively, using O_EXCL/O_NOFOLLOW for leaves. These are fresh inodes, never
hardlinks, moves or chowns of the old tree. Stream each entry from the same verified
buffer into a root0600 file, rechecking its length/hash, then set its ordinary
vendor mode. Revalidate complete root ownership, modes, membership, mount/device
and all content while the target is still private.

Only the retained descriptor for the fresh helper may receive4755, after the full
tree passes. Its exact size is17,048 bytes and SHA256 is
`243acfa0e6bab02b34580c2f426704dcd256c4072f494192c02b2256ea7740bb`.
The runtime executable remains SHA256
`730d44d5aefb6a969b209cf8ee3e843bd873a06c297bf2c409fbb1cebcb3e6bc`.
Verify the tree again before exposing target0755. All leaves/parents remain
root-owned and non-user-writable. The root-only external ledger records target
and helper device/inode, manifest, source digest and state; it survives rollback.

## Resource and activation boundary

This proposal would allocate a SECOND approximately302MB extraction plus filesystem
overhead. It preserves the original archive/extraction and all failure receipts.
It is not authorized by1318's8MiB source exception. Root must verify the remaining
original768MiB and cumulative2GiB budgets against a fresh stopped baseline and
reserve the full extraction/overhead before granting any activation. Host20GiB
after reservation and guest2GiB floors remain; do not allocate if it cannot fit.

Both actions require root, the exact disposable Lima hostname, externally supplied
reviewed source digest and explicit --execute-under-new-lease. This argument alone
does not grant authorization. No download/build, Electron launch, OS policy,
AppArmor, usernamespace, sysctl, authentication or service change is implemented.
All23 accepted renderer files remain unchanged.

A later reviewed launcher adaptation would change only the absolute executable
path and fresh output label. Any later benchmark still requires fresh normal GDM
session/native preflight/untimed motion/proof-bound freeze and all five original
30s/60s runs at33.3ms. Nothing here proves sandbox operation or selects a product.

## Rollback and interruption limits

Normal rollback checks the root-only ledger and target/helper device/inode/content.
It clears4755 through a retained matching helper descriptor BEFORE full-tree
validation/removal, validates the pinned manifest and exact target membership,
and refuses live fixture-user processes or observed runtime FD/mapping references.
Only then may descriptor-safe rmtree remove this unique target. The external ledger,
original archive/extraction, shared parent and every historical receipt remain.

An install exception after opening the verified helper attempts privilege clearing
through that retained descriptor. A failure to clear propagates; it is not labeled
successful cleanup. Incomplete extraction or interruption can leave an inaccessible
root tree, incomplete ledger, or an installed helper after the final privilege step.
Normal rollback may refuse an incomplete tree. Root must inspect retained identities
and review a specific recovery. There is no transactional or crash-recovery claim.

No installer, extraction, chmod, rollback or filesystem-failure branch has been
executed. Current source validation is separately recorded in
[source-validation.json](receipts/g8-electron-1288/source-validation.json).
Historical four-test results belong only to the rejected proposal. Full repository
checks and publication status must be taken from the current handoff, not inherited
from the older green PR head.
