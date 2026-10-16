#!/usr/bin/python3 -I
"""Disposable GTK task-link activation; no API, listener, credentials or mutation.
The only accepted island is a synthetic principal, never a user-selected endpoint.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import parse_qsl, urlsplit

PRINCIPAL = 'https://fixture.example.invalid'


def navigation(uri):
    if not isinstance(uri, str) or len(uri) > 2048 or any(ord(c) < 32 or ord(c) == 127 for c in uri):
        raise ValueError('bounded-text')
    parsed = urlsplit(uri)
    if parsed.scheme != 'campus' or parsed.netloc != 'task' or parsed.fragment:
        raise ValueError('shape')
    if not re.fullmatch(r'/[1-9][0-9]{0,18}', parsed.path, flags=re.ASCII):
        raise ValueError('synthetic-id-shape')
    number = int(parsed.path[1:])
    if number > 9223372036854775807:
        raise ValueError('synthetic-id-bound')
    query = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True, max_num_fields=2)
    if query != [('island', PRINCIPAL)]:
        raise ValueError('synthetic-principal-mismatch')
    return number


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--format', choices=('deb', 'appimage'), required=True)
    p.add_argument('--quit', action='store_true')
    p.add_argument('uri', nargs='?')
    initial = p.parse_args()
    assert initial.root.is_absolute() and initial.root.is_dir() and not initial.root.is_symlink()
    assert initial.root.stat().st_uid == os.getuid() and initial.root.stat().st_mode & 0o077 == 0
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gio, GLib, Gtk

    class App(Gtk.Application):
        def __init__(self):
            super().__init__(application_id='dev.projectcampus.Spike982Links.' + initial.format.title(), flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
            self.window = None
            self.label = None
            self.task = None

        def event(self, kind, **fields):
            with (initial.root / 'events.jsonl').open('a') as stream:
                stream.write(json.dumps({'kind': kind, 'pid': os.getpid(), 'monotonic': time.monotonic(), 'format': initial.format, **fields}) + '\n')
                stream.flush()
                os.fsync(stream.fileno())

        def do_activate(self):
            if self.window is None:
                self.window = Gtk.ApplicationWindow(application=self)
                self.window.set_title('Campus #982 disposable ' + initial.format + ' link fixture')
                self.window.set_default_size(640, 240)
                self.label = Gtk.Label()
                self.window.add(self.label)
                self.window.connect('destroy', lambda *_: self.event('window_destroyed'))
                self.event('window_created', mountinfo=[line for line in Path('/proc/self/mountinfo').read_text().splitlines() if str(Path(os.path.realpath(__file__)).parent) in line], script_path=os.path.realpath(__file__), appimage=os.environ.get('APPIMAGE'), architecture=os.uname().machine, session=os.environ.get('XDG_SESSION_TYPE'), principal=PRINCIPAL)
            self.label.set_text('Disposable navigation only\nSynthetic task ' + str(self.task) + '\n' + PRINCIPAL + '\nNo API request, account, credentials or HTTP listener')
            self.window.show_all()
            self.window.present()
            GLib.timeout_add(300, self.active_receipt)

        def active_receipt(self):
            self.event('window_observation', active=self.window.is_active(), visible=self.window.get_visible())
            return False

        def do_command_line(self, cmd):
            try:
                args = p.parse_args(cmd.get_arguments()[1:])
                if args.root != initial.root or args.format != initial.format:
                    raise ValueError('activation-instance-mismatch')
                if args.quit:
                    self.event('quit')
                    if self.window:
                        self.window.destroy()
                    self.quit()
                    return 0
                task = navigation(args.uri)
                self.task = task
                self.event('accepted', task=task)
                self.activate()
                return 0
            except (ValueError, TypeError) as error:
                self.event('rejected', reason='invalid-navigation-or-instance')
                return 2

    return App().run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
