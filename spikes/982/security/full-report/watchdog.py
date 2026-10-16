"""Bounded pidfd monitor for the serialized disposable Apport experiment."""
import os
from pathlib import Path
import select
import signal
import time


def read(path, cap=8192):
    with open(path, 'rb', buffering=0) as stream:
        data = stream.read(cap + 1)
    if len(data) > cap:
        raise RuntimeError('bounded proc read exceeded')
    return data


def identity(pid):
    p = Path('/proc') / str(pid)
    stat = read(p/'stat').rsplit(b')', 1)[1].split()
    return dict(pid=pid, start_ticks=int(stat[19]), ppid=int(stat[1]),
                argv=read(p/'cmdline').rstrip(b'\0').split(b'\0'))


class Watchdog:
    def __init__(self, deadline, guard):
        self.deadline = time.monotonic() + deadline
        self.guard = guard
        self.owned = {}
        self.events = []

    def retain(self, pid, expected=None, parent=None):
        before = identity(pid)
        if expected is not None and before != expected:
            raise RuntimeError('identity changed before pidfd acquisition')
        if parent is not None and (before['ppid'] != parent or parent not in self.owned):
            raise RuntimeError('unattributed child')
        fd = os.pidfd_open(pid)
        try:
            if before != identity(pid):
                raise RuntimeError('identity changed during pidfd acquisition')
            old = self.owned.get(pid)
            if old:
                if old['identity'] != before:
                    raise RuntimeError('retained PID reused')
                os.close(fd)
                return
            self.owned[pid] = dict(fd=fd, identity=before, parent=parent)
        except BaseException:
            os.close(fd)
            raise

    def live(self, pid):
        return not select.select([self.owned[pid]['fd']], [], [], 0)[0]

    def descendants(self):
        # /proc children is read only for retained, still-live identities.
        for parent in list(self.owned):
            if not self.live(parent):
                continue
            try:
                children = read(Path('/proc')/str(parent)/'task'/str(parent)/'children').split()
            except (FileNotFoundError, ProcessLookupError):
                # A retained process can exit between pidfd polling and this read.
                # Continue cleaning the other retained identities.
                continue
            for child in children:
                pid = int(child)
                if pid not in self.owned:
                    try:
                        self.retain(pid, parent=parent)
                    except (FileNotFoundError, ProcessLookupError):
                        pass
        if len(self.owned) > 32:
            raise RuntimeError('owned descendant bound')

    def tick(self):
        self.descendants()
        self.guard()
        if time.monotonic() >= self.deadline:
            raise TimeoutError('guest watchdog deadline')

    def send(self, pid, sig):
        try:
            signal.pidfd_send_signal(self.owned[pid]['fd'], sig)
        except ProcessLookupError:
            pass

    def stop(self):
        end = time.monotonic() + 5
        # Freeze observed parents before discovering further direct children.
        stable = 0
        while time.monotonic() < end and stable < 3:
            before = len(self.owned)
            for pid in self.owned:
                self.send(pid, signal.SIGSTOP)
            self.descendants()
            stable = stable + 1 if len(self.owned) == before else 0
            time.sleep(.02)
        for pid in reversed(list(self.owned)):
            self.send(pid, signal.SIGKILL)
        while time.monotonic() < end and any(self.live(pid) for pid in self.owned):
            time.sleep(.02)
        return stable >= 3 and all(not self.live(pid) for pid in self.owned)

    def receipt(self):
        return [dict(pid=p, start_ticks=v['identity']['start_ticks'],
                     parent=v['parent'], exited=not self.live(p)) for p,v in self.owned.items()]

    def close(self):
        for entry in self.owned.values():
            os.close(entry['fd'])
