"""Finite stderr capture for the diagnostic wrapper; no rendering policy changes."""
import os
import selectors
import signal
import subprocess
import time

LIMIT = 256 * 1024
MARKER = b'\n[campus GPU diagnostic stderr truncated; remaining bytes drained]\n'


def capture(args, *, stdout, stderr, cwd, limit, launched=lambda child: None):
    """Own an unreaped session leader until EOF/deadline, then reap exactly once.

    Keep at most LIMIT bytes, including the single overflow marker. A descendant
    holding stderr open cannot extend the existing outer deadline. Never signal
    a group after Popen has reaped its leader, including hidden KeyboardInterrupt
    reaping inside stdlib wait(). stdout retains the caller's existing policy.
    """
    deadline = time.monotonic() + limit
    total = kept = 0
    child = None
    failure = None
    cleanup = []
    overflow = timed_out = False
    try:
        child = subprocess.Popen(args, stdout=stdout, stderr=subprocess.PIPE,
                                 cwd=cwd, start_new_session=True)
        launched(child)
        os.set_blocking(child.stderr.fileno(), False)
        with selectors.DefaultSelector() as selector:
            selector.register(child.stderr, selectors.EVENT_READ)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(args, limit)
                for key, _ in selector.select(remaining):
                    chunk = os.read(key.fd, 16384)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    total += len(chunk)
                    take = min(len(chunk), LIMIT - len(MARKER) - kept)
                    if take:
                        stderr.write(chunk[:take])
                        kept += take
                    if take < len(chunk) and not overflow:
                        stderr.write(MARKER)
                        overflow = True
            child.wait(timeout=max(.001, deadline - time.monotonic()))
    except BaseException as error:
        failure = type(error).__name__ + ': ' + str(error)[:512]
        timed_out = isinstance(error, subprocess.TimeoutExpired)
        # A signal error must not prevent a bounded reap attempt or erase cause.
        if child is not None and child.returncode is None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except BaseException as signal_error:
                cleanup.append({'operation': 'killpg', 'error': type(signal_error).__name__ + ': ' + str(signal_error)[:256]})
            try:
                child.wait(timeout=10)
            except BaseException as wait_error:
                cleanup.append({'operation': 'wait', 'error': type(wait_error).__name__ + ': ' + str(wait_error)[:256]})
    finally:
        if child is not None and child.stderr is not None:
            try:
                child.stderr.close()
            except BaseException as close_error:
                cleanup.append({'operation': 'stderr-close', 'error': type(close_error).__name__ + ': ' + str(close_error)[:256]})
    reaped = child is not None and child.returncode is not None
    status = child.returncode if child is not None else None
    return {'returncode': status, 'timeout': timed_out, 'failure': failure,
            'cleanup': cleanup, 'child_pid': child.pid if child is not None else None,
            'child_reaped': reaped,
            'usable': failure is None and not cleanup and not overflow and reaped and status == 0,
            'stderr_bytes_observed': total, 'stderr_bytes_retained': kept + (len(MARKER) if overflow else 0),
            'stderr_overflow': overflow, 'stderr_limit_bytes': LIMIT}
