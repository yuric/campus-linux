#!/usr/bin/env python3
"""Fixed one-shot GUI driver. Start manually from the selected normal GDM Terminal.

Waits for a separately authorized root controller; never starts that controller,
acquires privilege, changes policy, accepts arbitrary commands or retries.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

import gated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('gate-directory', 'hints', 'index', 'inventory', 'receipt', 'root-preflight'):
        parser.add_argument('--' + name, required=True, type=Path)
    for name in ('lease-reference', 'authority-reference', 'source-head', 'root-preflight-sha256', 'observer'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    gated.require(os.getuid() == os.geteuid() != 0, 'normal unprivileged GUI user required')
    gated.require(args.hints.stat().st_uid == os.getuid(), 'own hint directory required')
    print(json.dumps({'event': 'gui_driver_waiting', 'pid': os.getpid()}), flush=True)
    until = time.monotonic() + 60
    while time.monotonic() < until:
        try:
            config = gated.config_read(args.gate_directory)
            break
        except FileNotFoundError:
            time.sleep(0.05)
    else:
        raise RuntimeError('root preparation timeout')
    gated.require(config['driver_pid'] == os.getpid() and config['lease'] == args.lease_reference
                  and config['hints'] == str(args.hints) and config['uid'] == os.getuid(), 'root scope differs')
    source = Path(__file__).parent
    log = args.hints / 'server.jsonl'
    server = subprocess.Popen(['/usr/bin/python3', '-B', str(source / 'serve.py'), '--index', str(args.index),
                               '--version', '2', '--gate-directory', str(args.gate_directory), '--log', str(log)],
                              stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    child = None
    try:
        ready_until = min(time.monotonic() + 3, config['prepare_deadline_ns'] / 1e9)
        while time.monotonic() < ready_until:
            gated.require(server.poll() is None, 'gated server exited')
            if log.exists() and any(json.loads(line).get('event') == 'serving' for line in log.read_text().splitlines()):
                break
            time.sleep(0.02)
        else:
            raise RuntimeError('gated server startup timeout')
        argv = ['/usr/bin/python3', '-B', str(source / 'desktop.py'), '--case', 'deny', '--timeout', '20',
                '--gate-directory', str(args.gate_directory), '--gate-server-pid', str(server.pid),
                '--planned-observation', 'One root-correlated normal GUI null-session denial; no administrator input']
        for name in ('index', 'inventory', 'receipt', 'root-preflight', 'lease-reference', 'authority-reference',
                     'source-head', 'root-preflight-sha256', 'observer'):
            argv.extend(['--' + name, str(getattr(args, name.replace('-', '_')))])
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL)
        return child.wait(timeout=58)
    except Exception as error:
        if not (args.hints / 'abort.json').exists():
            gated.hint_write(args.hints / 'abort.json', {'error': str(error)[:1024]})
        raise
    finally:
        # Desktop itself retains its app until root restoration. Keep the server
        # and this ancestry alive until it returns; no early poll of the app.
        if child is not None and child.poll() is None:
            child.terminate()
            child.wait(timeout=2)
        server.terminate()
        try:
            server.wait(timeout=2)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=1)
        server.stderr.close()


if __name__ == '__main__':
    raise SystemExit(main())
