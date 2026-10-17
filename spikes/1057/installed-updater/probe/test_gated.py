"""Source/mocked controls only. No guest, root mutation or installed acceptance."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import gated
import desktop
from test_marker_bridge import NODE_HARNESS

spec = importlib.util.spec_from_file_location('gated_authority_test', Path(__file__).with_name('authority-window.py'))
authority = importlib.util.module_from_spec(spec)
spec.loader.exec_module(authority)


def binding():
    process = {'pid': 123, 'ppid': 122, 'starttime': '10', 'exe': gated.APP,
               'exe_identity': [1, 2, 3, 4], 'uids': ['1000'] * 4, 'gids': ['1000'] * 4,
               'cgroup': 'gui', 'state': 'S'}
    session = {'Id': '6', 'User': '1000', 'Active': 'yes', 'Remote': 'no', 'State': 'active',
               'Class': 'user', 'Type': 'wayland', 'Service': 'gdm-password', 'Seat': 'seat0'}
    return {'mode': gated.MODE, 'lease': 'lease1', 'nonce': 'a' * 32, 'boot_id': 'b' * 32,
            'app': process, 'recorder': {**process, 'pid': 122}, 'driver': {**process, 'pid': 121},
            'server': {**process, 'pid': 125}, 'terminal': {**process, 'pid': 120},
            'ancestry': [{**process, 'pid': 120}],
            'custody': {'session': session, 'leader_logind': {'session': '6'}},
            'direct_logind': {'session': None, 'session_result': -61, 'owner_uid': 1000},
            'sources': {'desktop.py': {'path': '/fixture/desktop.py', 'sha256': 'c' * 64}},
            'app_sha256': 'd' * 64, 'app_started_ns': 100, 'app_deadline_ns': 100 + gated.APP_NS,
            'gate_deadline_ns': 100 + gated.GATE_NS, 'request': {'waiting_ns': 200}, 'bound_ns': 300}


def release(b):
    return {'schema': 1, 'lease': b['lease'], 'nonce': b['nonce'], 'boot_id': b['boot_id'],
            'app_pid': b['app']['pid'], 'app_starttime': b['app']['starttime'],
            'binding_sha256': gated.sha(gated.encode(b)), 'window_started_ns': 400,
            'loaded_ns': 500, 'rechecked_ns': 600, 'released_ns': 700}


class NullRuleTests(unittest.TestCase):
    def source(self, value=None):
        return authority.deny_rule('campusqa', 'lease1', 123, '6', nonce='a' * 32,
                                   null_binding=binding() if value is None else value).decode()

    def execute(self, subject, action=None, **options):
        payload = {'source': self.source(), 'subject': subject,
                   'configuredUser': 'campusqa', 'configuredSession': '6', 'configuredPid': 123,
                   'action': action or {'id': authority.ACTION, 'program': authority.PROGRAM, 'user': 'root'}, **options}
        result = subprocess.run([shutil.which('node'), '-e', NODE_HARNESS], input=json.dumps(payload),
                                text=True, capture_output=True, check=True, timeout=5)
        return json.loads(result.stdout)

    def subject(self):
        return {'user': 'campusqa', 'pid': 123, 'local': True, 'active': True, 'session': None}

    def test_actual_js_literal_null_only_and_exact_binding_marker(self):
        out = self.execute(self.subject())
        self.assertEqual(out['answer'], 'NO')
        marker = [row[-1] for row in out['delivered'] if row[-1].startswith('campus1057-deny lease=')]
        self.assertEqual(len(marker), 1)
        self.assertIn('pid=123 user=campusqa session=null active=true mode=' + gated.MODE, marker[0])
        self.assertTrue(marker[0].endswith('binding=' + gated.sha(gated.encode(binding()))))
        for value in (False, '', 'null', '6', 'other', 0, {}, []):
            s = self.subject(); s['session'] = value
            with self.subTest(value=value): self.assertIsNone(self.execute(s)['answer'])
        for mode in ('absent', 'undefined'):
            with self.subTest(mode=mode):
                self.assertIsNone(self.execute(self.subject(), runtimeField=['session', mode])['answer'])

    def test_actual_js_wrong_scope_never_denies(self):
        for field, value in (('pid', 124), ('pid', '123'), ('user', 'other'), ('local', False),
                             ('active', False), ('local', 1), ('active', 'true')):
            s = self.subject(); s[field] = value
            with self.subTest(field=field, value=value): self.assertIsNone(self.execute(s)['answer'])
        for field in ('id', 'program', 'user'):
            a = {'id': authority.ACTION, 'program': authority.PROGRAM, 'user': 'root'}; a[field] = 'wrong'
            self.assertIsNone(self.execute(self.subject(), action=a)['answer'])

    def test_no_boolean_or_incomplete_binding_can_enable_branch(self):
        for value in (True, {}, {'mode': gated.MODE}):
            with self.subTest(value=value), self.assertRaises(RuntimeError): self.source(value)
        for key in binding():
            b = binding(); del b[key]
            # bound_unix_ns isn't in this synthetic fixture; every field here is required.
            with self.subTest(key=key), self.assertRaises((RuntimeError, KeyError, TypeError)):
                self.source(b)

    def test_direct_generated_rule_is_byte_identical_to_inherited_source(self):
        # Golden generated bytes from inherited 81cd32e; no Git history needed
        # in the hosted shallow checkout.
        expected = {'None': '2cc6d5eef2d904592bf82b103c6339d07136b3dfa17269fe8b08c9c4c7bbe2e1', '123': '2212d33b6e439fe0df3511343025ca785a5de9e738893d78927b28ba7fb8962a'}
        for pid in (None, 123):
            self.assertEqual(gated.sha(authority.deny_rule('campusqa', 'lease1', pid, '6', nonce='a' * 32)),
                             expected[str(pid)])



class GateTests(unittest.TestCase):
    def gate(self):
        g = gated.ManifestGate.__new__(gated.ManifestGate)
        import threading
        g.directory, g.record = Path('/root-gate'), Mock()
        b = binding()
        g.config = {'lease': b['lease'], 'nonce': b['nonce'], 'boot_id': b['boot_id'],
                    'prepare_deadline_ns': 100 + 60_000_000_000, 'hints': '/hints'}
        g.lock, g.state, g.package_used, g.binding = threading.Lock(), 'closed', False, None
        return g

    def test_release_requires_all_scope_fields_lifetime_digest_and_order(self):
        g, b = self.gate(), binding()
        with patch.object(gated.time, 'monotonic_ns', return_value=1000):
            g.validate_release(release(b), b, b['request'])
            for field in release(b):
                value = release(b); value[field] = 'wrong'
                with self.subTest(field=field), self.assertRaises((RuntimeError, TypeError)):
                    g.validate_release(value, b, b['request'])
            for field, value in (('gate_deadline_ns', 999), ('app_deadline_ns', 999),
                                 ('mode', 'direct'), ('request', {})):
                changed = copy.deepcopy(b); changed[field] = value
                with self.subTest(field=field), self.assertRaises((RuntimeError, TypeError, KeyError)):
                    g.validate_release(release(changed), changed, b['request'])

    def test_manifest_expiry_stays_closed(self):
        g = self.gate()
        clock = [100]
        def sleep(seconds): clock[0] += int(seconds * 1e9)
        with patch.object(gated.time, 'monotonic_ns', side_effect=lambda: clock[0]), \
                patch.object(gated.time, 'sleep', side_effect=sleep), patch.object(gated, 'hint_write'), \
                patch.object(gated, 'root_read', side_effect=FileNotFoundError), patch('select.select', return_value=([], [], [])):
            with self.assertRaisesRegex(RuntimeError, 'expired'): g.manifest(Mock())
        self.assertEqual(g.state, 'failed')
        self.assertLessEqual(clock[0], 100 + gated.GATE_NS)

    def test_disconnect_never_releases(self):
        g, connection = self.gate(), Mock()
        connection.recv.return_value = b''
        with patch.object(gated, 'hint_write'), patch.object(gated.time, 'monotonic_ns', return_value=1000), \
                patch('select.select', return_value=([connection], [], [])):
            with self.assertRaisesRegex(RuntimeError, 'disconnected'): g.manifest(connection)
        self.assertEqual(g.state, 'failed')

    def test_package_requires_delivered_manifest_and_only_one_fixed_artifact(self):
        g, b = self.gate(), binding()
        artifact = {'format': 'deb', 'architecture': 'arm64', 'version': '2.0.0'}
        for state in ('closed', 'waiting', 'released', 'failed'):
            g.state = state
            with self.subTest(state=state), self.assertRaises(RuntimeError): g.package(artifact)
        g.state, g.binding, g.release = 'delivered', b, release(b)
        with patch.object(gated.time, 'monotonic_ns', return_value=1000), \
                patch.object(gated.Path, 'exists', return_value=False), patch.object(gated, 'root_read', return_value=g.release):
            for key in artifact:
                bad = dict(artifact); bad[key] = 'wrong'
                with self.subTest(key=key), self.assertRaises(RuntimeError): g.package(bad)
            g.package(artifact)
            with self.assertRaises(RuntimeError): g.package(artifact)

    def test_unknown_or_duplicate_manifest_is_not_released(self):
        g = self.gate()
        for state in ('waiting', 'released', 'delivered', 'failed'):
            g.state = state
            with self.assertRaisesRegex(RuntimeError, 'duplicate'): g.manifest(Mock())

    def test_json_duplicate_keys_refused(self):
        with self.assertRaises(RuntimeError): json.loads('{"nonce":1,"nonce":2}', object_pairs_hook=gated.unique_object)

    def test_root_record_owner_modes_bounds_and_nofollow(self):
        def info(uid=0, mode=stat.S_IFREG | 0o444, size=2):
            return SimpleNamespace(st_uid=uid, st_gid=0, st_mode=mode, st_size=size, st_dev=1, st_ino=2,
                                   st_mtime_ns=1, st_ctime_ns=1)
        parent = info(mode=stat.S_IFDIR | 0o555)
        for leaf in (info(), info(uid=1000), info(mode=stat.S_IFREG | 0o644),
                     info(mode=stat.S_IFLNK | 0o777), info(size=gated.LIMIT + 1)):
            with patch.object(gated.os, 'open', side_effect=[3, 4, 5]) as opened, \
                    patch.object(gated.os, 'close'), patch.object(gated.os, 'read', return_value=b'{}'), \
                    patch.object(gated.os, 'fstat', side_effect=[parent, parent, leaf, leaf]):
                if leaf is not None and leaf.st_uid == 0 and leaf.st_mode == stat.S_IFREG | 0o444 and leaf.st_size == 2:
                    self.assertEqual(gated.root_read('/gate/release.json'), {})
                else:
                    with self.assertRaises(RuntimeError): gated.root_read('/gate/release.json')
                for call in opened.call_args_list[1:]: self.assertTrue(call.args[1] & os.O_NOFOLLOW)


class LifetimeTests(unittest.TestCase):
    def test_waitid_observes_without_reap(self):
        child = Mock(pid=123)
        for result, expected in ((None, None), (SimpleNamespace(si_pid=123, si_code=os.CLD_EXITED, si_status=7), 7),
                                 (SimpleNamespace(si_pid=123, si_code=os.CLD_KILLED, si_status=9), -9)):
            with patch.object(gated.os, 'waitid', return_value=result, create=True) as wait:
                self.assertEqual(gated.child_exit(child), expected)
                self.assertTrue(wait.call_args.args[2] & os.WNOWAIT)
                child.poll.assert_not_called(); child.wait.assert_not_called(); child.communicate.assert_not_called()

    def test_recheck_rejects_parent_loss_boot_lifetime_exe_cgroup_and_custody_drift(self):
        b = binding()
        processes = {b[k]['pid']: b[k] for k in ('app', 'recorder', 'driver', 'server', 'terminal')}
        def check(mutator):
            values = copy.deepcopy(processes); mutator(values)
            with patch.object(gated, 'boot_id', return_value=b['boot_id']), \
                    patch.object(gated, 'kernel_process', side_effect=lambda pid, **kw: values[pid]), \
                    patch.object(gated, 'custody', return_value=b['custody']), \
                    patch.object(gated.time, 'monotonic_ns', return_value=1000):
                return gated.recheck(b, {}, 2000, allow_zombie=True)
        check(lambda values: None)
        for key, value in (('starttime', '11'), ('ppid', 1), ('exe', '/other'), ('cgroup', 'other'), ('uids', ['0'] * 4)):
            for pid in (123, 122):
                with self.subTest(key=key, pid=pid), self.assertRaises(RuntimeError):
                    check(lambda values: values[pid].update({key: value}))
        with self.assertRaises(KeyError): check(lambda values: values.pop(122))
        def zombie(values):
            values[123]['state'] = 'Z'; values[123].pop('exe'); values[123].pop('exe_identity')
        self.assertEqual(check(zombie)['state'], 'Z')
        with patch.object(gated, 'boot_id', return_value='wrong'), self.assertRaises(RuntimeError):
            gated.recheck(b, {}, 2000)

    def test_strict_validator_never_upgrades_null_history(self):
        result = desktop.validate_denial_evidence({'schema': 1, 'case': 'deny', 'status': 'not_certified',
                    'session_binding': 'coordinator_review_required'}, {}, [], Mock(), Mock())
        self.assertEqual(result['status'], 'incomplete')


class RecorderRetentionTests(unittest.TestCase):
    def test_completed_app_is_never_polled_or_reaped_before_root_restoration(self):
        recorder = desktop.Recorder.__new__(desktop.Recorder)
        recorder.args = SimpleNamespace(gate_directory=Path('/gate'), case='deny', timeout=20,
                                        lease_reference='lease1', gate_server_pid=125)
        recorder.receipt, recorder.save, recorder.sample_children = {'commands': []}, Mock(), Mock()
        config = {'lease': 'lease1', 'nonce': 'a' * 32, 'boot_id': 'b' * 32, 'hints': '/hints', 'prepare_deadline_ns': 60_000_000_000}
        clock, restored = [1000], [False]
        def tick():
            clock[0] += 100
            return clock[0]
        acknowledgment = {**{k: config[k] for k in ('lease', 'nonce', 'boot_id')},
                          'rule_absent': True, 'restored_ns': 1500}
        def root_read(path):
            restored[0] = True
            return acknowledgment
        child = Mock(pid=123)
        child.wait.side_effect = lambda **kw: 7 if restored[0] else self.fail('early reap')
        child.poll.side_effect = AssertionError('poll would reap')
        child.communicate.side_effect = AssertionError('communicate would reap')
        selector = Mock()
        selector.get_map.side_effect = [True, False]
        selector.select.return_value = []
        with patch.object(desktop.gated, 'config_read', return_value=config), \
                patch.object(desktop.gated, 'hint_write'), patch.object(desktop.gated, 'root_read', side_effect=root_read), \
                patch.object(desktop.gated, 'child_exit', return_value=7), \
                patch.object(desktop.time, 'monotonic_ns', side_effect=tick), \
                patch.object(desktop.subprocess, 'Popen', return_value=child), \
                patch.object(desktop, 'logind_process', return_value={'session': None}), \
                patch.object(desktop.os, 'set_blocking'), patch.object(desktop.selectors, 'DefaultSelector', return_value=selector):
            result = recorder.gated_command([desktop.APP, '--update', 'http://127.0.0.1:17857/stable/linux.json'])
        child.poll.assert_not_called(); child.communicate.assert_not_called(); child.wait.assert_called_once()
        self.assertLess(result['monotonic_finished_ns'], result['reaped_monotonic_ns'])
        self.assertEqual(result['returncode'], 7)
        self.assertEqual(recorder._unreaped, [])

    def test_new_correlation_never_accepts_history_or_partial_root_binding(self):
        for raw in ({}, {'gated_mode': gated.MODE, 'case': 'deny', 'status': 'not_certified',
                         'session_binding': 'coordinator_review_required'}):
            result = gated.correlate(raw, {}, [], Mock(), Mock())
            self.assertEqual(result['status'], 'incomplete')
            self.assertFalse(result['exact_logind_session'])


class ActualBindingTests(unittest.TestCase):
    def environment(self, mutate=None, direct=None, custody_changed=False):
        from contextlib import ExitStack
        stack = ExitStack()
        group = '0::/user.slice/user-1000.slice/user@1000.service/app.slice/app-org.gnome.Terminal.slice/'
        def process(pid, ppid, exe, cgroup):
            return {'pid': pid, 'ppid': ppid, 'exe': exe, 'exe_identity': [1, 2, 3, 4],
                    'uids': ['1000'] * 4, 'gids': ['1000'] * 4, 'starttime': '10', 'state': 'S', 'cgroup': cgroup}
        vte = group + 'vte-spawn-12345678-1234-1234-1234-123456789abc.scope\n'
        processes = {123: process(123, 122, gated.APP, vte), 122: process(122, 121, '/usr/bin/python3.12', vte),
                     121: process(121, 119, '/usr/bin/python3.12', vte), 125: process(125, 121, '/usr/bin/python3.12', vte),
                     119: process(119, 120, '/usr/bin/bash', vte),
                     120: process(120, 118, '/usr/libexec/gnome-terminal-server', group + 'gnome-terminal-server.service\n')}
        config = {'uid': 1000, 'driver_pid': 121, 'terminal_pid': 120, 'terminal': copy.deepcopy(processes[120]),
                  'prepare_deadline_ns': 60_000_000_000, 'boot_id': 'b' * 32, 'lease': 'lease1', 'nonce': 'a' * 32,
                  'app_sha256': gated.sha(b'app'), 'custody': {'session': {'Id': '6'}},
                  'sources': {name: {} for name in ('desktop.py', 'gated-driver.py', 'serve.py')}}
        hint = {'lease': 'lease1', 'nonce': 'a' * 32, 'app_pid': 123, 'server_pid': 125, 'monotonic_started_ns': 100_000_000}
        request = {'lease': 'lease1', 'nonce': 'a' * 32, 'waiting_ns': 200_000_000}
        if mutate: mutate(processes, config, hint, request)
        for target, name, kw in (
            (gated.os, 'geteuid', {'return_value': 0}), (gated.os, 'sysconf', {'return_value': 100}),
            (gated, 'boot_id', {'return_value': 'b' * 32}), (gated.time, 'monotonic_ns', {'return_value': 1_000_000_000}),
            (gated, 'kernel_process', {'side_effect': lambda pid, **kwargs: processes[pid]}),
            (gated, 'source_process', {'side_effect': lambda pid, *args: processes[pid]}),
            (gated.Path, 'read_bytes', {'return_value': b'app'}),
            (gated.Path, 'stat', {'return_value': SimpleNamespace(st_uid=0, st_mode=0o755, st_dev=1, st_ino=2, st_size=3, st_mtime_ns=4)}),
            (gated, 'no_pkexec', {}),
            (gated, 'logind', {'return_value': direct or {'session': None, 'session_result': -61, 'owner_uid': 1000}}),
            (gated, 'custody', {'return_value': {} if custody_changed else config['custody']})):
            stack.enter_context(patch.object(target, name, **kw))
        return stack, config, hint, request

    def run_binding(self, **kwargs):
        stack, config, hint, request = self.environment(**kwargs)
        with stack: return gated.actual_binding(config, hint, request)

    def test_actual_normal_terminal_service_and_vte_ancestry_bind(self):
        b = self.run_binding()
        self.assertEqual(b['app']['pid'], 123)
        self.assertEqual([row['pid'] for row in b['ancestry']], [119, 120])
        self.assertEqual(b['direct_logind']['session'], None)

    def test_wrong_kernel_identity_ancestry_uid_hash_and_expiry_refuse(self):
        mutations = [lambda p,c,h,r: p[123].update(uids=['0'] * 4),
                     lambda p,c,h,r: p[123].update(exe='/other'),
                     lambda p,c,h,r: p[123].update(starttime='9999'),
                     lambda p,c,h,r: p[123].update(cgroup='unrelated'),
                     lambda p,c,h,r: p[121].update(ppid=118),
                     lambda p,c,h,r: c.update(app_sha256='0' * 64),
                     lambda p,c,h,r: c.update(prepare_deadline_ns=1),
                     lambda p,c,h,r: h.update(nonce='wrong'),
                     lambda p,c,h,r: r.update(waiting_ns=1),
                     lambda p,c,h,r: p[120].update(starttime='11')]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises((RuntimeError, KeyError)):
                self.run_binding(mutate=mutate)
        with self.assertRaises(RuntimeError): self.run_binding(custody_changed=True)
        for direct in ({'session': '6', 'session_result': 0, 'owner_uid': 1000},
                       {'session': None, 'session_result': -61, 'owner_uid': 1001}):
            with self.assertRaises(RuntimeError): self.run_binding(direct=direct)


class CorrelationTests(unittest.TestCase):
    def fixture(self):
        from test_authority_window import BINDING
        b = binding()
        for key in ('app_started_ns', 'bound_ns'):
            b[key] *= 1000
        b['request']['waiting_ns'] *= 1000
        b['app_deadline_ns'] = b['app_started_ns'] + gated.APP_NS
        b['gate_deadline_ns'] = b['app_started_ns'] + gated.GATE_NS
        rel = release(b)
        for key in ('window_started_ns', 'loaded_ns', 'rechecked_ns', 'released_ns'):
            rel[key] *= 1000
        service = copy.deepcopy(BINDING); service['boot_id'] = b['boot_id']
        restored = {'lease': b['lease'], 'nonce': b['nonce'], 'boot_id': b['boot_id'], 'rule_absent': True, 'restored_ns': 1000000}
        update = {'argv': [gated.APP, '--update'], 'process': {'pid': 123, 'starttime_ticks': 10, 'session': None,
                  'uids': [1000] * 4, 'cgroup': 'gui', 'ppid': 122}, 'monotonic_started_ns': 100000,
                  'monotonic_finished_ns': 900000, 'reaped_monotonic_ns': 1100000, 'started_ns': 1_000_100_000,
                  'finished_ns': 1_000_900_000, 'returncode': 1, 'root_restoration': restored}
        identity = {'event': 'installed_identity'}
        d = {'gated_mode': gated.MODE, 'case': 'deny', 'status': 'not_certified',
             'session_binding': 'coordinator_review_required', 'lease_reference': b['lease'],
             'boot_id': b['boot_id'], 'boot_id_after': b['boot_id'], 'commands': [update],
             'session': b['custody']['session'], 'session_after': b['custody']['session'],
             'before': identity, 'after': identity, 'updater_events': [identity, {'event': 'selected'},
             {'event': 'verified_download'}, {'event': 'polkit_adapter_result', 'success': False, 'stdout': ''},
             {'event': 'refusal_bytes', 'app_unchanged': True, 'helper_unchanged': True},
             {'event': 'refused', 'error': 'polkit adapter did not install the fixture; inspect its receipt'}]}
        zombie = {k: v for k, v in b['app'].items() if k not in ('exe', 'exe_identity')}; zombie['state'] = 'Z'
        a = {'user_manager_binding': b, 'status': 'app_completed_pending_coordinator_review', 'cleanup': 'restored',
             'deadline_exceeded': False, 'service_identity_valid': True, 'lease': b['lease'], 'boot_id': b['boot_id'],
             'service_binding': service, 'user': 'campusqa', 'subject_session': '6',
             'rule_sha256': gated.sha(authority.deny_rule('campusqa', 'lease1', 123, '6', nonce=b['nonce'], null_binding=b)),
             'owned_path': str(authority.RULE), 'owned_device_inode': [1,2], 'gate_release': rel, 'gate_restoration': restored,
             'elapsed_seconds_including_cleanup': 1, 'restore_started_monotonic_ns': 950000,
             'window_started_unix_ns': 1_000_400_000, 'loaded_marker_observed_unix_ns': 1_000_500_000,
             'lifetime_observations': [{'app': zombie}], 'gate_transport': {'rows': [
                {'event': 'manifest_waiting', 'waiting_ns': 200000},
                {'event': 'manifest_released', 'release': rel, 'monotonic_ns': 710000},
                {'event': 'manifest_delivered', 'monotonic_ns': 800000},
                {'event': 'request', 'path': '/stable/linux.json', 'status': 200},
                {'event': 'request', 'path': '/packages/fixture.deb', 'status': 200}]}}
        for key in ('service_binding_before_ready', 'service_binding_before_restore', 'service_binding_after_restore'): a[key] = service
        prefix = ' lease=lease1 nonce=' + b['nonce']
        messages = [('campus1057-deny-loaded' + prefix, 1000450),
                    ('campus1057-deny' + prefix + ' pid=123 user=campusqa session=null active=true mode=' + gated.MODE + ' binding=' + gated.sha(gated.encode(b)), 1000850),
                    ('campus1057-deny-candidate' + prefix + ' ' + json.dumps({'status': 'observed', 'subject_session': {'present': True, 'type': 'null'}, 'subject_pid': {'value': 123}}), 1000840)]
        rows = [{'MESSAGE': message, 'SYSLOG_IDENTIFIER': authority.LOGGER_TAG, '_UID': service['uid'], '_GID': service['gid'],
                 '_PID': '999', '_TRANSPORT': 'syslog', '_BOOT_ID': b['boot_id'], '__REALTIME_TIMESTAMP': str(t), '__MONOTONIC_TIMESTAMP': str(t - 1000000)} for message,t in messages]
        return d, a, rows

    def test_complete_separate_correlation_and_temporal_mutations(self):
        d, a, rows = self.fixture()
        update = d['commands'][0]
        def check(): return gated.correlate(d, a, rows, authority.validate_marker_rows, authority.deny_rule)
        result = check()
        self.assertEqual(result['status'], 'root_correlated_user_manager_pending_coordinator_review', result)
        self.assertFalse(result['exact_logind_session'])
        for field, value in (('reaped_monotonic_ns', 850), ('monotonic_finished_ns', 21_000_000_100)):
            saved = update[field]; update[field] = value
            self.assertEqual(check()['status'], 'incomplete'); update[field] = saved
        for index in (1, 2):
            for value in (None, '200', '799', '901', 'bad', -1):
                saved = rows[index].pop('__MONOTONIC_TIMESTAMP')
                if value is not None:
                    rows[index]['__MONOTONIC_TIMESTAMP'] = value
                with self.subTest(row=index, value=value):
                    self.assertEqual(check()['status'], 'incomplete')
                rows[index]['__MONOTONIC_TIMESTAMP'] = saved
        # A wall-clock rollback cannot substitute for monotonic chronology.
        rows[2]['__REALTIME_TIMESTAMP'] = '1000200'
        self.assertEqual(check()['status'], 'root_correlated_user_manager_pending_coordinator_review')
        rows[2]['__MONOTONIC_TIMESTAMP'] = '200'
        self.assertEqual(check()['status'], 'incomplete')
        rows[2]['__MONOTONIC_TIMESTAMP'] = '840'
        rows[2]['__REALTIME_TIMESTAMP'] = '1000840'
        a['gate_transport']['rows'].append({'event': 'gate_failed'})
        self.assertEqual(check()['status'], 'incomplete')


if __name__ == '__main__':
    unittest.main()
