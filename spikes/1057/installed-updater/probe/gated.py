"""Optional controlled-guest manifest barrier. No privilege acquisition or acceptance.

Root observations correlate a normal GUI user-manager process; they never establish
an exact direct logind session. All input from the desktop is a hint until sampled.
"""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import threading
import time

MODE = 'root-correlated-user-manager'
APP = '/usr/bin/campus-updater-1057'
LIMIT = 32768
GATE_NS = 8_000_000_000
APP_NS = 20_000_000_000


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def file_identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def root_read(path):
    """Walk anchored dirfds: no symlink traversal, bounded immutable root file."""
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute canonical root path required')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
            info = os.fstat(fd)
            require(info.st_uid == 0 and not info.st_mode & 0o022, 'untrusted root path ancestor')
        require(not os.fstat(fd).st_mode & 0o222, 'gate directory must be nonwritable')
        leaf = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            info = os.fstat(leaf)
            require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o222
                    and info.st_size <= LIMIT, 'untrusted or oversized root record')
            raw = os.read(leaf, LIMIT + 1)
            require(len(raw) == info.st_size and file_identity(os.fstat(leaf)) == file_identity(info), 'root record changed')
            value = json.loads(raw, object_pairs_hook=unique_object)
            require(type(value) is dict, 'root record must be an object')
            return value
        finally:
            os.close(leaf)
    finally:
        os.close(fd)


def publish(directory, name, value):
    require(os.geteuid() == 0 and name in ('config.json', 'binding.json', 'release.json', 'restored.json'),
            'only root may publish fixed gate records')
    raw = encode(value)
    require(len(raw) <= LIMIT, 'gate record too large')
    # Directory is precreated by the root controller, never writable by the user.
    # Root alone can create in its mode-0555 directory; no chmod window is needed.
    pending = Path(directory) / ('.' + name + '.pending')
    fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o444)
    try:
        os.fchmod(fd, 0o444)
        require(os.write(fd, raw) == len(raw), 'short gate record write')
        os.fsync(fd)
    finally:
        os.close(fd)
    # Link exposes only the complete fsynced buffer, and refuses an existing name.
    os.link(pending, Path(directory) / name, follow_symlinks=False)
    # Retain the owned pending hardlink until post-export cleanup; no metadata
    # changes race readers of the newly published immutable record.
    require(root_read(Path(directory) / name) == value, 'published gate record mismatch')


def hint_read(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_size <= LIMIT, 'unbounded hint')
        raw = os.read(fd, LIMIT + 1)
        require(len(raw) <= LIMIT, 'unbounded hint')
        return json.loads(raw)
    finally:
        os.close(fd)


def hint_write(path, value):
    raw = encode(value)
    require(len(raw) <= LIMIT, 'unbounded hint')
    pending = Path(path).with_name('.' + Path(path).name + '.pending')
    fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        require(os.write(fd, raw) == len(raw), 'short hint write')
        os.fsync(fd)
    finally:
        os.close(fd)

    os.link(pending, path, follow_symlinks=False)
    # Keep the private pending link until lease cleanup; no post-publication race.


def config_read(directory):
    value = root_read(Path(directory) / 'config.json')
    require(value.get('mode') == MODE and value.get('schema') == 1, 'wrong gate mode/schema')
    require(type(value.get('lease')) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', value['lease']), 'invalid lease')
    require(type(value.get('nonce')) is str and re.fullmatch(r'[0-9a-f]{32}', value['nonce']), 'invalid nonce')
    require(type(value.get('prepared_ns')) is int and type(value.get('prepare_deadline_ns')) is int
            and 0 < value['prepare_deadline_ns'] - value['prepared_ns'] <= 60_000_000_000,
            'invalid preparation deadline')
    require(value.get('boot_id') == boot_id(), 'gate boot changed')
    return value


def boot_id():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip().replace('-', '')


def kernel_process(pid, zombie=False):
    require(type(pid) is int and 1 < pid <= 2147483647, 'invalid actual PID')
    proc = Path('/proc') / str(pid)
    before = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    require(before[0] != 'Z' or zombie, 'process already exited')
    status = dict(line.split(':', 1) for line in (proc / 'status').read_text().splitlines() if ':' in line)
    row = {'pid': pid, 'ppid': int(before[1]), 'starttime': before[19],
           'uids': status['Uid'].split(), 'gids': status['Gid'].split(),
           'cgroup': (proc / 'cgroup').read_text()}
    if before[0] != 'Z':
        try:
            row['exe'] = os.readlink(proc / 'exe')
            info = (proc / 'exe').stat()
            row['exe_identity'] = [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns]
        except FileNotFoundError:
            if not zombie:
                raise
            # exit_mm may remove exe before exit_notify publishes Z. Resample
            # only this same lifetime, at most 20ms; all other drift still fails.
            for attempt in range(5):
                after = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
                require(before[19] == after[19] and before[1] == after[1], 'process changed during exit sampling')
                if after[0] == 'Z':
                    row.pop('exe', None)
                    row.pop('exe_identity', None)
                    break
                if attempt == 4:
                    raise
                time.sleep(0.005)
    after = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    require(before[19] == after[19] and before[1] == after[1], 'process changed during sampling')
    require(after[0] != 'Z' or zombie, 'process exited during sampling')
    if after[0] == 'Z':
        row.pop('exe', None)
        row.pop('exe_identity', None)
    row['state'] = after[0]
    return row


def logind(pid):
    lib, libc = ctypes.CDLL('libsystemd.so.0'), ctypes.CDLL(None)
    lib.sd_pid_get_session.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)]
    lib.sd_pid_get_session.restype = ctypes.c_int
    lib.sd_pid_get_owner_uid.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_uint)]
    lib.sd_pid_get_owner_uid.restype = ctypes.c_int
    libc.free.argtypes = [ctypes.c_void_p]
    pointer, owner = ctypes.c_void_p(), ctypes.c_uint()
    result = lib.sd_pid_get_session(pid, ctypes.byref(pointer))
    try:
        session = ctypes.string_at(pointer).decode() if result >= 0 else None
    finally:
        if pointer:
            libc.free(pointer)
    owner_result = lib.sd_pid_get_owner_uid(pid, ctypes.byref(owner))
    return {'session': session, 'session_result': result,
            'owner_uid': owner.value if owner_result >= 0 else None, 'owner_result': owner_result}


def properties(kind, ident, deadline):
    remaining = (deadline - time.monotonic_ns()) / 1e9
    require(remaining > 0, 'root sampling deadline')
    result = subprocess.run(['/usr/bin/loginctl', 'show-' + kind, str(ident), '--no-pager'],
                            capture_output=True, text=True, timeout=min(1, remaining), check=True)
    require(len(result.stdout) <= LIMIT, 'unbounded logind properties')
    values = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    keys = ('Id', 'User', 'Leader', 'Type', 'Class', 'Service', 'Remote', 'Active', 'State', 'Scope', 'Seat') if kind == 'session' else ('Sessions', 'Display', 'RuntimePath')
    return {key: values.get(key) for key in keys}


def custody(config, deadline):
    uid = config['uid']
    user = properties('user', uid, deadline)
    sessions = (user.get('Sessions') or '').split()
    require(0 < len(sessions) <= 8, 'unbounded or absent user sessions')
    rows = [properties('session', sid, deadline) for sid in sessions]
    active = [row for row in rows if row['User'] == str(uid) and row['Type'] in ('wayland', 'x11')
              and row['Class'] == 'user' and (row['Service'] or '').startswith('gdm-')
              and row['Remote'] == 'no' and row['Active'] == 'yes' and row['State'] == 'active']
    require(len(active) == 1 and active[0]['Id'] == config['session_id'] and active[0]['Seat'],
            'requires unique selected active local GDM session')
    session = active[0]
    leader = kernel_process(int(session['Leader']))
    direct = logind(leader['pid'])
    require(direct['session'] == session['Id'], 'GDM leader lacks direct session')
    return {'session': session, 'leader': stable(leader), 'leader_logind': direct, 'user': user}


def source_process(pid, expected, uid):
    row = kernel_process(pid)
    require(row['uids'] == [str(uid)] * 4 and len(set(row['gids'])) == 1, 'source process credentials differ')
    path = Path(expected['path'])
    require(path.is_absolute() and path.resolve(strict=True) == path, 'noncanonical source path')
    # Executed scripts are root staged, immutable, and independently hash-bound.
    data = root_read_source(path)
    require(sha(data) == expected['sha256'], 'executed source hash differs')
    argv = (Path('/proc') / str(pid) / 'cmdline').read_bytes().split(b'\0')
    require(len(argv) <= 128 and len(b'\0'.join(argv)) <= LIMIT and str(path).encode() in argv[1:4],
            'kernel command line does not name reviewed script')
    return row


def root_read_source(path):
    # Same anchored metadata policy as records; scripts need not be JSON.
    require(path.is_absolute() and path.resolve(strict=True) == path, 'symlinked source')
    for parent in (path.parent, *path.parent.parents):
        info = parent.stat()
        require(info.st_uid == 0 and not info.st_mode & 0o022, 'source ancestor not root controlled')
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o222
            and not path.parent.stat().st_mode & 0o222 and info.st_size <= 128 * 1024,
            'source not bounded immutable root file')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        raw = os.read(fd, 128 * 1024 + 1)
        require(file_identity(os.fstat(fd)) == file_identity(info) and len(raw) == info.st_size, 'source changed')
        return raw
    finally:
        os.close(fd)


def no_pkexec(pid):
    tasks = list((Path('/proc') / str(pid) / 'task').iterdir())
    require(len(tasks) <= 64, 'unbounded app tasks')
    children = set()
    for task in tasks:
        raw = (task / 'children').read_text()
        require(len(raw) <= 4096, 'unbounded app child list')
        children.update(map(int, raw.split()))
    require(len(children) <= 64, 'unbounded app children')
    for child in children:
        try:
            row = kernel_process(child)
        except FileNotFoundError:
            continue
        require(row['exe'] != '/usr/bin/pkexec', 'authorization child appeared before gate release')


def actual_binding(config, hint, request):
    """Root samples live kernel state. Hints select PIDs, never attest identity."""
    require(os.geteuid() == 0, 'actual binding requires independent root')
    now = time.monotonic_ns()
    require(now < config['prepare_deadline_ns'] and boot_id() == config['boot_id'], 'expired preparation or boot')
    require(hint.get('lease') == request.get('lease') == config['lease']
            and hint.get('nonce') == request.get('nonce') == config['nonce'], 'hint lease/nonce mismatch')
    start = hint['monotonic_started_ns']
    require(type(start) is int and type(request.get('waiting_ns')) is int
            and start <= request['waiting_ns'] <= now < start + GATE_NS, 'gate ordering/8-second ceiling')
    deadline = min(start + GATE_NS, request['waiting_ns'] + GATE_NS)
    app = kernel_process(hint['app_pid'])
    kernel_start = int(app['starttime']) * 1_000_000_000 // os.sysconf('SC_CLK_TCK')
    require(abs(kernel_start - start) <= 1_000_000_000, 'app start hint differs from kernel lifetime')
    # The earlier clock controls: hints cannot extend the real invocation budget.
    start = min(start, kernel_start)
    deadline = min(deadline, start + GATE_NS)
    uid = config['uid']
    require(app['uids'] == [str(uid)] * 4 and len(set(app['gids'])) == 1
            and app['exe'] == APP, 'wrong app executable or credentials')
    require(sha((Path('/proc') / str(app['pid']) / 'exe').read_bytes()) == config['app_sha256'], 'actual app hash differs')
    disk = Path(APP).stat()
    require(disk.st_uid == 0 and not disk.st_mode & 0o022
            and app['exe_identity'] == [disk.st_dev, disk.st_ino, disk.st_size, disk.st_mtime_ns], 'app file identity differs')
    recorder = source_process(app['ppid'], config['sources']['desktop.py'], uid)
    driver = source_process(recorder['ppid'], config['sources']['gated-driver.py'], uid)
    require(driver['pid'] == config['driver_pid'], 'recorder is not the independently selected GUI driver')
    server = source_process(hint['server_pid'], config['sources']['serve.py'], uid)
    require(server['ppid'] == driver['pid'], 'server is not a child of GUI driver')
    terminal = kernel_process(config['terminal_pid'])
    require(stable(terminal) == stable(config['terminal']) and terminal['uids'] == [str(uid)] * 4, 'GUI terminal lifetime changed')
    # Walk the actual parents, not a cgroup-prefix-only assertion.
    chain, current = [], driver
    for _ in range(8):
        if current['pid'] == terminal['pid']:
            break
        current = kernel_process(current['ppid'])
        require(current['uids'] == [str(uid)] * 4, 'GUI ancestry crossed user boundary')
        chain.append(current)
    require(current['pid'] == terminal['pid'], 'driver not descended from selected GUI terminal')
    prefix = '0::/user.slice/user-' + str(uid) + '.slice/user@' + str(uid) + '.service/app.slice/app-org.gnome.Terminal.slice/'
    require(terminal['exe'] == '/usr/libexec/gnome-terminal-server'
            and terminal['cgroup'].rstrip('\n') == prefix + 'gnome-terminal-server.service',
            'selected terminal is not the normal GNOME Terminal service')
    group = driver['cgroup']
    require(re.fullmatch(re.escape(prefix) + r'vte-spawn-[0-9a-f-]{36}\.scope\n?', group),
            'driver lacks actual GNOME Terminal VTE scope')
    require(all(row['cgroup'] == group for row in [app, recorder, driver, server, *chain[:-1]]),
            'app/recorder/driver GUI scope differs')
    direct = logind(app['pid'])
    require(direct['session'] is None and direct['session_result'] < 0 and direct['owner_uid'] == uid,
            'new mode requires actual null direct session and correct owner UID')
    no_pkexec(app['pid'])
    selected = custody(config, deadline)
    require(selected == config['custody'], 'selected GDM custody changed')
    require(time.monotonic_ns() < deadline, 'binding exceeded gate ceiling')
    return {'mode': MODE, 'lease': config['lease'], 'nonce': config['nonce'], 'boot_id': config['boot_id'],
            'app': app, 'recorder': recorder, 'driver': driver, 'server': server, 'ancestry': chain,
            'terminal': terminal, 'custody': selected, 'direct_logind': direct,
            'app_started_ns': start, 'app_deadline_ns': start + APP_NS, 'gate_deadline_ns': deadline,
            'request': request, 'bound_ns': time.monotonic_ns(), 'bound_unix_ns': time.time_ns(),
            'app_sha256': config['app_sha256'], 'sources': config['sources']}


def stable(row):
    return {key: value for key, value in row.items() if key != 'state'}


def recheck(binding, config, deadline, allow_zombie=False):
    require(boot_id() == binding['boot_id'], 'boot changed')
    for key in ('recorder', 'driver', 'server', 'terminal'):
        require(stable(kernel_process(binding[key]['pid'])) == stable(binding[key]), key + ' lifetime/custody changed')
    for old in binding['ancestry']:
        require(stable(kernel_process(old['pid'])) == stable(old), 'GUI ancestor changed')
    current = kernel_process(binding['app']['pid'], zombie=allow_zombie)
    old = dict(binding['app'])
    if current['state'] == 'Z':
        old.pop('exe', None)
        old.pop('exe_identity', None)
    require(stable(current) == stable(old), 'actual app lifetime/credentials/executable changed or early reaped')
    require(custody(config, deadline) == binding['custody'], 'GDM custody changed')
    require(time.monotonic_ns() < deadline, 'root recheck deadline')
    return current


class ManifestGate:
    """One manifest, one indexed deb. Any error permanently closes delivery."""
    def __init__(self, directory, record):
        self.directory, self.record = Path(directory), record
        self.config = config_read(directory)
        self.lock = threading.Lock()
        self.state = 'closed'
        self.package_used = False
        self.binding = None

    def fail(self, reason):
        with self.lock:
            self.state = 'failed'
        self.record({'event': 'gate_failed', 'reason': str(reason), 'monotonic_ns': time.monotonic_ns()})

    def manifest(self, connection):
        with self.lock:
            require(self.state == 'closed', 'duplicate manifest request')
            self.state = 'waiting'
        started = time.monotonic_ns()
        request = {'lease': self.config['lease'], 'nonce': self.config['nonce'],
                   'waiting_ns': started, 'waiting_unix_ns': time.time_ns()}
        hint_write(Path(self.config['hints']) / 'request.json', request)
        self.record({'event': 'manifest_waiting', **request})
        try:
            until = min(started + GATE_NS, self.config['prepare_deadline_ns'])
            while time.monotonic_ns() < until:
                require(self.state == 'waiting', 'gate invalidated')
                # A disconnected request cannot consume a later release.
                import select
                if select.select([connection], [], [], 0)[0]:
                    require(connection.recv(1, socket.MSG_PEEK | socket.MSG_DONTWAIT), 'manifest client disconnected')
                    raise RuntimeError('unexpected pipelined request')
                try:
                    release = root_read(self.directory / 'release.json')
                except FileNotFoundError:
                    time.sleep(0.02)
                    continue
                binding = root_read(self.directory / 'binding.json')
                self.validate_release(release, binding, request)
                with self.lock:
                    require(self.state == 'waiting', 'gate invalidated before release')
                    self.state, self.binding, self.release = 'released', binding, release
                self.record({'event': 'manifest_released', 'monotonic_ns': time.monotonic_ns(),
                             'binding_sha256': sha(encode(binding)), 'release': release})
                return
            raise RuntimeError('manifest gate expired')
        except Exception as error:
            self.fail(error)
            raise

    def validate_release(self, release, binding, request):
        require(binding.get('mode') == MODE and binding.get('request') == request, 'wrong root binding/request')
        expected = {'schema': 1, 'lease': self.config['lease'], 'nonce': self.config['nonce'],
                    'boot_id': self.config['boot_id'], 'app_pid': binding['app']['pid'],
                    'app_starttime': binding['app']['starttime'], 'binding_sha256': sha(encode(binding))}
        require(all(release.get(key) == value for key, value in expected.items()), 'wrong release binding')
        require(binding.get('lease') == expected['lease'] and binding.get('nonce') == expected['nonce']
                and binding.get('boot_id') == expected['boot_id'], 'root binding scope differs')
        times = [binding['app_started_ns'], request['waiting_ns'], binding['bound_ns'],
                 release['window_started_ns'], release['loaded_ns'], release['rechecked_ns'], release['released_ns']]
        require(all(type(t) is int and t > 0 for t in times) and times == sorted(times), 'invalid gated timing order')
        require(release['loaded_ns'] - release['window_started_ns'] <= 5_000_000_000
                and time.monotonic_ns() < binding['gate_deadline_ns'] <= binding['app_started_ns'] + GATE_NS
                and binding['app_deadline_ns'] == binding['app_started_ns'] + APP_NS
                and release['released_ns'] <= time.monotonic_ns(), 'release deadline exceeded')

    def deliver(self, write):
        with self.lock:
            try:
                require(self.state == 'released', 'manifest invalidated before delivery')
                write()
                self.record({'event': 'manifest_delivered', 'monotonic_ns': time.monotonic_ns()})
                self.state = 'delivered'
            except Exception:
                self.state = 'failed'
                raise

    def package(self, artifact):
        with self.lock:
            require(self.state == 'delivered' and not self.package_used and self.binding is not None,
                    'package forbidden before one manifest release or duplicate package')
            require(artifact['format'] == 'deb' and artifact['architecture'] == 'arm64'
                    and artifact['version'] == '2.0.0' and time.monotonic_ns() < self.binding['app_deadline_ns'],
                    'only fixed signed arm64 deb v2 operation is gated')
            require(not (self.directory / 'restored.json').exists(), 'authority already restored')
            require(root_read(self.directory / 'release.json') == self.release, 'release no longer valid')
            self.package_used = True


def child_exit(child):
    """Return observed status without consuming the zombie or freeing its PID."""
    result = os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    if result is None:
        return None
    require(result.si_pid == child.pid, 'waitid returned another child')
    require(result.si_code in (os.CLD_EXITED, os.CLD_KILLED, os.CLD_DUMPED), 'unexpected child state')
    return result.si_status if result.si_code == os.CLD_EXITED else -result.si_status


def correlate(desktop, authority, rows, validate_rows, derive_rule):
    """Separate root-correlation report; never changes raw null-session status.

    Independent root baseline, GUI observation, complete export and review remain
    mandatory. This report is neither direct-session proof nor automatic acceptance.
    """
    result = {'status': 'incomplete', 'acceptance': 'pending_coordinator_review',
              'correlation': MODE, 'exact_logind_session': False, 'journal_rows': rows}
    try:
        require(desktop.get('gated_mode') == MODE and desktop.get('case') == 'deny'
                and desktop.get('status') == 'not_certified'
                and desktop.get('session_binding') == 'coordinator_review_required', 'not a completed raw null-session observation')
        b = authority['user_manager_binding']
        require(authority.get('status') == 'app_completed_pending_coordinator_review'
                and authority.get('cleanup') == 'restored' and authority.get('deadline_exceeded') is False
                and authority.get('service_identity_valid') is True, 'unclean or incomplete authority window')
        require(desktop.get('lease_reference') == authority.get('lease') == b['lease']
                and desktop.get('boot_id') == desktop.get('boot_id_after') == authority.get('boot_id') == b['boot_id'],
                'lease or boot differs')
        service = authority['service_binding']
        require(all(authority.get(key) == service for key in ('service_binding_before_ready',
                'service_binding_before_restore', 'service_binding_after_restore')), 'polkit service changed')
        rule = derive_rule(authority['user'], b['lease'], b['app']['pid'], authority['subject_session'],
                           nonce=b['nonce'], null_binding=b)
        require(sha(rule) == authority.get('rule_sha256')
                and authority.get('owned_path') == '/etc/polkit-1/rules.d/00-campus-updater-1057-deny.rules'
                and len(authority.get('owned_device_inode', [])) == 2, 'rule identity/hash differs')
        updates = [row for row in desktop['commands'] if row.get('argv', [])[:2] == [APP, '--update']]
        require(len(updates) == 1, 'requires one app invocation')
        update = updates[0]
        p = update['process']
        require(p['pid'] == b['app']['pid'] and str(p['starttime_ticks']) == b['app']['starttime']
                and p['session'] is None and p['uids'] == list(map(int, b['app']['uids']))
                and p['cgroup'] == b['app']['cgroup'] and p['ppid'] == b['recorder']['pid'], 'app lifetime differs')
        release, restoration = authority['gate_release'], authority['gate_restoration']
        require(release['binding_sha256'] == sha(encode(b)) and update.get('root_restoration') == restoration
                and restoration.get('rule_absent') is True, 'gate release/restoration binding differs')
        times = [b['app_started_ns'], update['monotonic_started_ns'], b['request']['waiting_ns'], b['bound_ns'],
                 release['window_started_ns'], release['loaded_ns'], release['rechecked_ns'], release['released_ns'],
                 update['monotonic_finished_ns'], restoration['restored_ns'], update['reaped_monotonic_ns']]
        require(all(type(t) is int and t > 0 for t in times) and times == sorted(times), 'gated temporal ordering differs')
        require(times[8] - times[1] <= APP_NS and times[7] <= b['gate_deadline_ns'] <= times[0] + GATE_NS
                and times[5] - times[4] <= 5_000_000_000
                and authority['elapsed_seconds_including_cleanup'] <= 45
                and restoration['restored_ns'] - authority['restore_started_monotonic_ns'] <= 10_000_000_000,
                'original timing limits exceeded')
        require(desktop['session'] == desktop['session_after'] or all(
            desktop['session'].get(k) == desktop['session_after'].get(k) for k in b['custody']['session']), 'session changed')
        require(all(desktop['session'].get(k) == v for k, v in b['custody']['session'].items()), 'root GDM custody differs')
        samples = authority['lifetime_observations']
        require(0 < len(samples) <= 128 and samples[-1]['app']['state'] == 'Z', 'missing retained app completion')
        for sample in samples:
            old = dict(b['app'])
            if sample['app']['state'] == 'Z':
                old.pop('exe'); old.pop('exe_identity')
            require(stable(sample['app']) == stable(old), 'root sampled app lifetime changed')
        transport = authority['gate_transport']['rows']
        require(not any(row.get('event') == 'gate_failed' for row in transport), 'transport gate failed')
        waiting = [row for row in transport if row.get('event') == 'manifest_waiting']
        delivered = [row for row in transport if row.get('event') == 'manifest_delivered']
        released = [row for row in transport if row.get('event') == 'manifest_released']
        requests = [row for row in transport if row.get('event') == 'request']
        require(len(waiting) == len(released) == len(delivered) == 1
                and waiting[0]['waiting_ns'] == b['request']['waiting_ns']
                and released[0]['release'] == release
                and release['released_ns'] <= released[0]['monotonic_ns'] <= delivered[0]['monotonic_ns'] <= times[8]
                and len(requests) == 2 and all(row.get('status') == 200 for row in requests)
                and requests[0]['path'] == '/stable/linux.json'
                and requests[1]['path'].startswith('/packages/'), 'missing one-shot manifest/package delivery evidence')
        events = desktop['updater_events']
        require([e.get('event') for e in events] == ['installed_identity', 'selected', 'verified_download',
                'polkit_adapter_result', 'refusal_bytes', 'refused'] and type(update['returncode']) is int
                and update['returncode'] != 0 and events[3].get('success') is False
                and events[3].get('stdout', '').strip() == '' and events[4].get('app_unchanged') is True
                and events[4].get('helper_unchanged') is True and desktop['before'] == desktop['after'] == events[0]
                and events[5].get('error') == 'polkit adapter did not install the fixture; inspect its receipt',
                'not the actual refusal/unchanged-byte path')
        require(0 < len(rows) <= 64, 'incomplete bounded journal union')
        common = {'nonce': b['nonce'], 'lease': b['lease'], 'binding': service, 'boot_id': b['boot_id']}
        def journal_time(row, lower, upper):
            value = row.get('__MONOTONIC_TIMESTAMP')
            require(type(value) is str and re.fullmatch(r'[0-9]{1,20}', value), 'missing journal monotonic time')
            stamp = int(value)
            # journald stores microseconds; compare at that recorded precision.
            require(lower // 1000 <= stamp <= upper // 1000, 'journal callback outside released window')
            return stamp

        loaded_message = 'campus1057-deny-loaded lease=' + b['lease'] + ' nonce=' + b['nonce']
        rejecting_message = 'campus1057-deny lease=' + b['lease'] + ' nonce=' + b['nonce'] + ' pid=' + str(b['app']['pid']) + ' user=' + authority['user'] + ' session=null active=true mode=' + MODE + ' binding=' + sha(encode(b))
        groups = {'loaded': [], 'rejecting': [], 'candidate': []}
        for row in rows:
            message = row.get('MESSAGE', '') if isinstance(row, dict) else ''
            if b['nonce'] not in json.dumps(row):
                continue
            if message == loaded_message:
                journal_time(row, release['window_started_ns'], release['loaded_ns'])
                groups['loaded'].append(row)
            elif message == rejecting_message:
                journal_time(row, delivered[0]['monotonic_ns'], update['monotonic_finished_ns'])
                groups['rejecting'].append(row)
            elif message.startswith('campus1057-deny-candidate lease=' + b['lease'] + ' nonce=' + b['nonce'] + ' '):
                journal_time(row, delivered[0]['monotonic_ns'], update['monotonic_finished_ns'])
                payload = json.loads(message.split(' ', 3)[3])
                require(payload.get('status') == 'observed' and payload.get('subject_session') == {'present': True, 'type': 'null'}
                        and payload.get('subject_pid', {}).get('value') == b['app']['pid'], 'candidate contradicts literal null/PID')
                checked = validate_rows([row], message, start_ns=update['started_ns'], end_ns=update['finished_ns'], **common)
                require(checked['accepted'] and not checked['anomalies'], 'untrusted candidate')
                groups['candidate'].append(row)
            else:
                raise RuntimeError('unknown or contradictory current-nonce journal row')
        for name, message, start, end in (
                ('loaded', loaded_message, authority['window_started_unix_ns'], authority['loaded_marker_observed_unix_ns']),
                ('rejecting', rejecting_message, update['started_ns'], update['finished_ns'])):
            checked = validate_rows(groups[name], message, start_ns=start, end_ns=end, **common)
            require(checked['accepted'] and not checked['anomalies'], 'missing or untrusted ' + name)
            result[name] = checked
        require(groups['candidate'], 'actual literal-null callback diagnostic absent')
        require(max(int(row['__MONOTONIC_TIMESTAMP']) for row in groups['candidate']) <=
                min(int(row['__MONOTONIC_TIMESTAMP']) for row in groups['rejecting']),
                'candidate follows rejecting callback')
        result['status'] = 'root_correlated_user_manager_pending_coordinator_review'
        result['remaining_review'] = 'Independent full protected baseline, source/export hashes, GUI custody and package/trust restoration; raw observation remains not_certified.'
    except (RuntimeError, KeyError, TypeError, ValueError) as error:
        result['error'] = str(error)
    return result


def transport_log(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_size <= LIMIT, 'unbounded transport log')
        raw = os.read(fd, LIMIT + 1)
        require(len(raw) <= LIMIT, 'transport log grew beyond bound')
        rows = [json.loads(line, object_pairs_hook=unique_object) for line in raw.splitlines()]
        require(len(rows) <= 32, 'too many transport events')
        return {'sha256': sha(raw), 'bytes': len(raw), 'rows': rows}
    finally:
        os.close(fd)
