#!/usr/bin/env python3
"""Unprivileged Linux inotify probe: replace a caller path while its reader is open.

The old inode and parent directory share one ordered inotify queue. A pass requires
IN_MOVED_TO for the atomic replacement before IN_CLOSE_NOWRITE on the original inode;
a late scheduler wakeup is recorded as failure, never accepted as a race proof.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import select
import stat
import struct
import sys
import time


IN_OPEN = 0x00000020
IN_CLOSE_NOWRITE = 0x00000010
IN_MOVED_TO = 0x00000080
IN_Q_OVERFLOW = 0x00004000
HEADER = struct.Struct("iIII")


def watch(source, replacement):
    if sys.platform != "linux" or os.geteuid() == 0:
        raise RuntimeError("watcher must be an unprivileged Linux caller")
    for path in (source, replacement):
        info = path.lstat()
        if not path.is_absolute() or not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise RuntimeError("probe paths must be caller-owned regular absolute paths")
    if source.parent != replacement.parent:
        raise RuntimeError("replacement must share the caller's source directory")
    original_inode = source.stat().st_ino
    replacement_inode = replacement.stat().st_ino
    if original_inode == replacement_inode:
        raise RuntimeError("probe requires separate original and replacement inodes")
    libc = ctypes.CDLL(None, use_errno=True)
    libc.inotify_init1.argtypes = [ctypes.c_int]
    libc.inotify_init1.restype = ctypes.c_int
    libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
    libc.inotify_add_watch.restype = ctypes.c_int
    descriptor = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    if descriptor < 0:
        raise OSError(ctypes.get_errno(), "inotify_init1")
    try:
        file_watch = libc.inotify_add_watch(descriptor, os.fsencode(source), IN_OPEN | IN_CLOSE_NOWRITE)
        parent_watch = libc.inotify_add_watch(descriptor, os.fsencode(source.parent), IN_MOVED_TO)
        if min(file_watch, parent_watch) < 0:
            raise OSError(ctypes.get_errno(), "inotify_add_watch")
        print(json.dumps({"event": "watch_ready", "uid": os.getuid(),
                          "monotonic_ns": time.monotonic_ns(), "original_inode": original_inode}), flush=True)
        events, replaced = [], False
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if not select.select([descriptor], [], [], min(1, deadline - time.monotonic()))[0]:
                continue
            block = os.read(descriptor, 65536)
            offset = 0
            while offset < len(block):
                wd, mask, cookie, length = HEADER.unpack_from(block, offset)
                name = os.fsdecode(block[offset + HEADER.size:offset + HEADER.size + length].split(b"\0", 1)[0])
                offset += HEADER.size + length
                if mask & IN_Q_OVERFLOW:
                    raise RuntimeError("inotify queue overflow")
                event = None
                if wd == file_watch and mask & IN_OPEN:
                    event = "original_open"
                elif wd == file_watch and mask & IN_CLOSE_NOWRITE:
                    event = "original_close"
                elif wd == parent_watch and mask & IN_MOVED_TO and name == source.name:
                    event = "replacement_moved_to"
                if event:
                    events.append({"event": event, "monotonic_ns": time.monotonic_ns()})
                if event == "original_open" and not replaced:
                    os.replace(replacement, source)
                    replaced = True
            labels = [event["event"] for event in events]
            if "original_close" in labels and "replacement_moved_to" in labels:
                evidence = {"event": "caller_path_replaced", "uid": os.getuid(), "events": events,
                            "original_inode": original_inode, "replacement_inode": source.stat().st_ino,
                            "replacement_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
                ordered = labels.index("original_open") < labels.index("replacement_moved_to") < labels.index("original_close")
                evidence["replacement_before_original_reader_close"] = ordered
                print(json.dumps(evidence), flush=True)
                if not ordered or source.stat().st_ino != replacement_inode:
                    raise RuntimeError("replacement did not provably occur while original reader was open")
                return
        raise RuntimeError("timed out before ordered open/replacement/close evidence")
    finally:
        os.close(descriptor)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--replacement", required=True, type=Path)
    args = parser.parse_args()
    try:
        watch(args.source, args.replacement)
    except Exception as error:
        print(json.dumps({"event": "watch_failed", "error": str(error), "monotonic_ns": time.monotonic_ns()}), flush=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
